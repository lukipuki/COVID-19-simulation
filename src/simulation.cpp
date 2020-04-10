#include <algorithm>
#include <cassert>
#include <fstream>
#include <iomanip>
#include <iostream>

#include "yaml-cpp/yaml.h"

#include "generators.h"
#include "person.h"
#include "simulation_results.pb.h"
#include "stats.h"


// #define EXPONENTIAL_GROWTH
// constexpr bool kExponentialGrowth = true;
constexpr bool kExponentialGrowth = false;

constexpr uint32_t kRestrictionDay = 8 + static_cast<int>(kExponentialGrowth) * 3;
constexpr double kGamma1 = 1.25;
constexpr uint32_t kSymptomsLength = 28;
constexpr uint32_t kExtraDays = 10;  // Extra simulated days of infections

// Only serialize good parameters, scoring below kScoreThreshold
constexpr double kScoreThreshold = 280;

class Simulator {
 public:
  Simulator(uint32_t prefix_length, const std::vector<uint32_t>& positive,
            const std::vector<uint32_t>& tested)
      : tested_(prefix_length, 0),
        positive_(prefix_length, 0),
        t0_{kRestrictionDay + prefix_length},
        rd_{},
        random_generator_(rd_()) {
    std::copy(tested.begin(), tested.end(), std::back_inserter(tested_));
    std::copy(positive.begin(), positive.end(), std::back_inserter(positive_));
    std::partial_sum(positive_.begin(), positive_.end(), positive_.begin());
  }

  auto Simulate(double beta0, const GeneratorInterface& generator) -> SimulationResult::OneRun {
    std::vector<uint32_t> infected = GenerateInfected(generator);
    std::vector<Person> persons;
    std::uniform_int_distribution<> uniform(0, 14);

    SimulationResult::OneRun run;
    *run.mutable_daily_infected() = {infected.begin(), infected.end()};
    int32_t cumulative_positive = 0;
    double error = 0;
    std::vector<uint32_t> dead_count;
    for (uint32_t day = 0; day < positive_.size(); ++day) {
      for (uint32_t i = 0; i < infected[day]; ++i) {
        auto age = generate_age(&random_generator_);
        auto symptoms = beta_distribution(1, bs[age], &random_generator_);
        persons.emplace_back(
            symptoms, std::ceil(symptoms * kSymptomsLength + uniform(random_generator_)), day);
        if (persons.back().DateOfDeath().has_value()) {
          uint32_t date = *persons.back().DateOfDeath();
          if (dead_count.size() <= date) {
            dead_count.resize(date + 1);
          }
          ++dead_count[date];
        }
      }

      assert(day < tested_.size());
      double quantile = 1 - static_cast<double>(tested_[day]) / kPopulationSize;
      double threshold = qbeta(beta0, quantile);

      auto iter = std::partition(
          persons.begin(), persons.end(),
          [day, threshold](const Person& ca) { return ca.CurrentSymptoms(day) < threshold; });

      run.add_daily_positive(persons.end() - iter);
      cumulative_positive += persons.end() - iter;
      if (cumulative_positive + positive_[day] > 0) {
        error -= log_distance_probability(cumulative_positive, positive_[day]);
      }

      persons.resize(iter - persons.begin());
    }
    run.set_error(error);
    *run.mutable_daily_dead() = {dead_count.begin(), dead_count.end()};

    return run;
  }

 private:
  auto GenerateInfected(const GeneratorInterface& generator) -> std::vector<uint32_t> {
    std::vector<uint32_t> infected;
    for (double mean : generator.CreateDeltas(t0_, tested_.size() + kExtraDays)) {
      std::poisson_distribution<> poisson(mean);
      infected.push_back(poisson(random_generator_));
    }
    return infected;
  }

  uint32_t t0_;

  std::vector<uint32_t> tested_;
  // Cumulative sum of positive cases for each day
  std::vector<uint32_t> positive_;

  std::random_device rd_;
  std::mt19937 random_generator_;
};

int main(int argc, char* argv[]) {
  if (argc <= 1) {
    std::cout << "You need to supply a YAML file with data" << std::endl;
    exit(1);
  }

  std::vector<uint32_t> tested;
  std::vector<uint32_t> positive;
  for (const auto& node : YAML::LoadFile(argv[1])) {
    positive.push_back(node["positive"].as<uint32_t>());
    tested.push_back(node["tested"].as<uint32_t>());
  }
  assert(tested.size() == positive.size());

  constexpr uint32_t kIterations = 200;
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
    for (uint32_t prefix_length = 1; prefix_length < 10; ++prefix_length) {
      Simulator simulator(prefix_length, positive, tested);
      uint32_t optimal_b0 = -1, optimal_dead_count;
      double best = 1e10;
      for (uint32_t b0 = 20; b0 <= 250; b0 += 3) {
        SimulationResult result;
        result.set_prefix_length(prefix_length);
        result.set_b0(b0);
        std::vector<double> deltas = generator.CreateDeltas(
            prefix_length + kRestrictionDay, prefix_length + tested.size() + kExtraDays);
        *result.mutable_deltas() = {deltas.begin(), deltas.end()};

        if constexpr (kExponentialGrowth) {
          result.set_gamma2(param);
        } else {
          result.set_alpha(param);
        }
        double sum_error = 0, dead_count = 0;
        int iterations = 0;
        for (uint32_t i = 0; i < kIterations; ++i) {
          auto run = simulator.Simulate(b0, generator);
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
        if (sum_error < best) {
          best = sum_error;
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
        *results.add_results() = result;
      }

      std::cout << std::setw(2) << prefix_length << std::setw(4) << optimal_b0 << std::setw(4)
                << optimal_dead_count << std::setw(9) << best << std::endl;
    }
  }

  std::fstream output("results.pb", std::ios::out | std::ios::trunc | std::ios::binary);
  if (!results.SerializeToOstream(&output)) {
    std::cerr << "Failed to write results" << std::endl;
  }
}
