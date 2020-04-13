#include <algorithm>
#include <cassert>
#include <fstream>
#include <iomanip>
#include <iostream>

#include <google/protobuf/io/zero_copy_stream_impl.h>
#include <google/protobuf/text_format.h>

#include "country_data.pb.h"
#include "generators.h"
#include "person.h"
#include "simulation_results.pb.h"
#include "stats.h"

// #define EXPONENTIAL_GROWTH
// constexpr bool kExponentialGrowth = true;
constexpr bool kExponentialGrowth = false;

constexpr uint32_t kRestrictionDay = 8 + static_cast<int>(kExponentialGrowth) * 3;
constexpr double kGamma1 = 1.25;
constexpr uint32_t kExtraDays = 10;  // Extra simulated days of infections

// Only serialize good parameters, scoring below kScoreThreshold
constexpr double kScoreThreshold = 300;

class Simulator {
 public:
  Simulator(uint32_t prefix_length, const std::vector<uint32_t>& positive,
            const std::vector<uint32_t>& tested, const GeneratorInterface& generator)
      : tested_(prefix_length, 0),
        positive_(prefix_length, 0),
        t0_{kRestrictionDay + prefix_length},
        deltas_{generator.CreateDeltas(t0_, positive.size() + prefix_length + kExtraDays)} {
    std::copy(tested.begin(), tested.end(), std::back_inserter(tested_));
    std::copy(positive.begin(), positive.end(), std::back_inserter(positive_));
    std::partial_sum(positive_.begin(), positive_.end(), positive_.begin());
  }

  // Simulates the model for the configuration (b0, prefix_length, deltas).
  // Note that deltas could be generated as an exponential sequence or a polynomial sequence.
  auto Simulate(double beta0) -> SimulationResult::OneRun {
    std::vector<uint32_t> infected = stats_.GenerateInfected(deltas_, positive_.size());
    SimulationResult::OneRun run;
    *run.mutable_daily_infected() = {infected.begin(), infected.end()};

    std::vector<Person> persons;
    int32_t cumulative_positive = 0;
    double error = 0;
    std::vector<uint32_t> dead_count;
    uint32_t days = positive_.size();
    for (uint32_t day = 0; day < days; ++day) {
      for (uint32_t i = 0; i < infected[day]; ++i) {
        persons.emplace_back(&stats_, day);
        if (persons.back().DateOfDeath().has_value()) {
          uint32_t date = *persons.back().DateOfDeath();
          if (dead_count.size() <= date) {
            dead_count.resize(date + 1);
          }
          ++dead_count[date];
        }
      }

      assert(day < tested_.size());

      double threshold = Stats::CalculateThreshold(beta0, tested_[day]);
      auto iter = std::partition(
          persons.begin(), persons.end(),
          [day, threshold](const Person& ca) { return ca.CurrentSymptoms(day) < threshold; });

      run.add_daily_positive(persons.end() - iter);
      cumulative_positive += persons.end() - iter;
      error -= stats_.LogDistance(cumulative_positive, positive_[day]);

      persons.resize(iter - persons.begin());
    }
    run.set_error(error);
    *run.mutable_daily_dead() = {dead_count.begin(), dead_count.end()};

    return run;
  }

  auto get_deltas() -> std::vector<double> { return deltas_; }

 private:
  uint32_t t0_;

  // Daily count of tested people.
  std::vector<uint32_t> tested_;
  // Cumulative sum of positive cases for each day
  std::vector<uint32_t> positive_;
  // See Rado Harman's COR01.pdf for the definition of delta_t.
  std::vector<double> deltas_;

  Stats stats_;
};

int main(int argc, char* argv[]) {
  if (argc <= 1) {
    std::cerr << "You need to supply a proto file with country data" << std::endl;
    exit(1);
  }

  std::vector<uint32_t> tested;
  std::vector<uint32_t> positive;

  CountryData country_data;
  std::ifstream country_file(argv[1]);
  google::protobuf::io::IstreamInputStream input_stream(&country_file);
  if (!google::protobuf::TextFormat::Parse(&input_stream, &country_data)) {
    std::cerr << "Failed to parse data" << std::endl;
  }
  for (const auto& day : country_data.stats()) {
    positive.push_back(day.positive());
    tested.push_back(day.tested());
  }

  constexpr uint32_t kIterations = 100;
  const uint32_t kEarlyStop = std::ceil(std::sqrt(kIterations));
  SimulationResults results;
  std::cout << "prefix_length optimal_b0 dead_count best_error" << std::endl;
#pragma omp parallel for shared(positive, tested)
#ifdef EXPONENTIAL_GROWTH
  // Yes, it's #ifdef, because 'if constexpr' sucks
  for (uint32_t g = 96; g <= 106; g += 2) {
    auto generator = ExponentialGenerator(kGamma1, g / 100.0);
#else
  for (uint32_t g = 122; g <= 130; g += 2) {
    auto generator = PolynomialGenerator(kGamma1, g / 100.0);
#endif
    double param = g / 100.0;
    for (uint32_t prefix_length = 1; prefix_length < 19; ++prefix_length) {
      Simulator simulator(prefix_length, positive, tested, generator);
      uint32_t optimal_b0 = -1, optimal_dead_count;
      double best_error = 1e10;
      for (uint32_t b0 = 20; b0 <= 250; b0 += 3) {
        SimulationResult result;
        result.set_prefix_length(prefix_length);
        result.set_b0(b0);
        std::vector<double> deltas = simulator.get_deltas();
        *result.mutable_deltas() = {deltas.begin(), deltas.end()};

        if constexpr (kExponentialGrowth) {
          result.set_gamma2(param);
        } else {
          result.set_alpha(param);
        }
        double sum_error = 0, dead_count = 0;
        int iterations = 0;
        for (uint32_t i = 0; i < kIterations; ++i) {
          auto run = simulator.Simulate(b0);
          sum_error += run.error();
          for (auto count : run.daily_dead()) {
            dead_count += count;
          }
          *result.add_runs() = run;
          ++iterations;
          if (i == kEarlyStop && sum_error / iterations > 1.5 * kScoreThreshold) {
            break;
          }
        }

        sum_error /= iterations;
        dead_count /= iterations;
        if (sum_error < best_error) {
          best_error = sum_error;
          optimal_b0 = b0;
          optimal_dead_count = dead_count;
        }

        SimulationResult::Summary summary;
        summary.set_error(sum_error);
        summary.set_dead_count(dead_count);
        *result.mutable_summary() = summary;
        if (sum_error > kScoreThreshold) {
          result.mutable_deltas()->Clear();
          result.mutable_runs()->Clear();
        }
#pragma omp critical
        *results.add_results() = result;
      }

      std::cout << std::setw(2) << prefix_length << std::setw(4) << optimal_b0 << std::setw(5)
                << optimal_dead_count << std::setw(9) << best_error << std::endl;
    }
  }

  std::fstream output("results.pb", std::ios::out | std::ios::trunc | std::ios::binary);
  if (!results.SerializeToOstream(&output)) {
    std::cerr << "Failed to write results" << std::endl;
  }
}
