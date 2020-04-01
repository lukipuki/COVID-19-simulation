#include <algorithm>
#include <cassert>
#include <iostream>

#include "yaml-cpp/yaml.h"

#include "generators.h"
#include "person.h"
#include "stats.h"

std::vector<double> bs;
constexpr uint32_t kRestrictionDay = 11;  // 0-indexed March 12th
// constexpr uint32_t kRestrictionDay = 10;  // For power law
constexpr double kGamma1 = 1.25;
constexpr double kGamma2 = 1.04;
constexpr double kPowerLawExponent = 1.30;
constexpr uint32_t kSymptomsLength = 28;

struct SimulationResult {
  explicit SimulationResult(const std::vector<uint32_t>& infected)
      : daily_positive{}, daily_infected{infected}, error{0}, dead_count{} {}
  std::vector<uint32_t> daily_positive;
  std::vector<uint32_t> daily_infected;
  std::vector<uint32_t> dead_count;
  double error;
};

class Simulator {
 public:
  Simulator(uint32_t prefix_length, const std::vector<uint32_t>& positive,
            const std::vector<uint32_t>& tested)
      : tmax_{prefix_length + static_cast<uint32_t>(positive.size())},
        tested_(prefix_length + 1, 0),
        positive_(prefix_length + 1, 0),
        t0_{kRestrictionDay + prefix_length + 1},
        rd_{},
        random_generator_(rd_()) {
    std::copy(tested.begin(), tested.end(), std::back_inserter(tested_));
    std::copy(positive.begin(), positive.end(), std::back_inserter(positive_));
    std::partial_sum(positive_.begin(), positive_.end(), positive_.begin());
  }

  auto Simulate(double beta0, const GeneratorInterface& generator) -> SimulationResult {
    constexpr double gamma1 = 1.25, gamma2 = 1.04;
    std::vector<uint32_t> infected = GenerateInfected(generator);
    std::vector<Person> persons;
    std::uniform_int_distribution<> uniform(0, 14);

    SimulationResult result(infected);
    result.error = 0;
    int32_t cumulative_positive = 0;
    for (uint32_t day = 0; day < infected.size(); ++day) {
      for (uint32_t i = 0; i < infected[day]; ++i) {
        auto age = generate_age(&random_generator_);
        auto symptoms = beta_distribution(1, bs[age], &random_generator_);
        persons.emplace_back(symptoms, std::ceil(symptoms * kSymptomsLength + uniform(random_generator_)), day);
        if (persons.back().DateOfDeath().has_value()) {
          uint32_t date = *persons.back().DateOfDeath();
          if (result.dead_count.size() <= date) result.dead_count.resize(date + 1);
          ++result.dead_count[date];
        }
      }

      assert(day < tested_.size());
      double quantile = 1 - static_cast<double>(tested_[day]) / kPopulationSize;
      double threshold = qbeta(beta0, quantile);

      auto iter = std::partition(
          persons.begin(), persons.end(),
          [day, threshold](const Person& ca) { return ca.CurrentSymptoms(day) < threshold; });

      result.daily_positive.push_back(persons.end() - iter);
      cumulative_positive += persons.end() - iter;
      if (positive_[day] > 0) {
        result.error += std::pow(cumulative_positive - static_cast<int32_t>(positive_[day]), 2) /
                        positive_[day];

        // std::cout << day << " " << cumulative_positive << " " << positive_[day] << " "
        //           << std::pow(cumulative_positive - static_cast<int32_t>(positive_[day]), 2) /
        //                  positive_[day]
        //           << std::endl;
      }

      persons.resize(iter - persons.begin());
    }

    return result;
  }

 private:
  auto GenerateInfected(const GeneratorInterface& generator) -> std::vector<uint32_t> {
    std::vector<uint32_t> infected;
    for (double mean : generator.CreateDeltas(t0_, tested_.size())) {
      std::poisson_distribution<> possion(mean);
      infected.push_back(possion(random_generator_));
    }
    return infected;
  }

  uint32_t tmax_;
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

  std::transform(kDeathProbabilities, kDeathProbabilities + kDecadesCount, std::back_inserter(bs),
                 calculate_b);
  assert(tested.size() == positive.size());

  auto generator = ExponentialGenerator(kGamma1, kGamma2);
  constexpr uint32_t kIterations = 4;
  std::cout << "prefix_length optimal_b0 dead_count best_error" << std::endl;
#pragma omp parallel for shared(positive, tested, bs)
  for (uint32_t prefix_length = 2; prefix_length < 9; ++prefix_length) {
    Simulator simulator(prefix_length, positive, tested);
    // Simulator simulator(prefix_length, positive, tested);
    uint32_t optimal_b0 = -1, optimal_dead_count;
    double best = 1e10;
    for (uint32_t b0 = 60; b0 <= 200; b0 += 3) {
      double sum_error = 0, dead_count = 0;
      for (uint32_t i = 0; i < kIterations; ++i) {
        auto result = simulator.Simulate(b0, generator);
        sum_error += result.error;
        dead_count += std::accumulate(result.dead_count.begin(), result.dead_count.end(), 0);
      }
      sum_error /= kIterations;
      dead_count /= kIterations;
      if (sum_error < best) {
        best = sum_error;
        optimal_b0 = b0;
        optimal_dead_count = dead_count;
      }
    }
    std::cout << prefix_length << " " << optimal_b0 << " " << optimal_dead_count << " " << best
              << std::endl;
  }
}
