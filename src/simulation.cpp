#include <algorithm>
#include <cassert>
#include <fstream>
#include <iomanip>
#include <iostream>

#include "yaml-cpp/yaml.h"

#include "generators.h"
#include "person.h"
#include "result.h"
#include "stats.h"

constexpr uint32_t kExtraDays = 10;       // Extra simulated days of infections
// constexpr uint32_t kRestrictionDay = 11;  // 0-indexed March 12th
constexpr uint32_t kRestrictionDay = 8;  // For polynomial growth
constexpr double kGamma1 = 1.25;
constexpr double kGamma2 = 1.04;
constexpr double kPolynomialDegree = 1.25;
constexpr uint32_t kSymptomsLength = 28;

// Only serialize good parameters, scoring below kScoreThreshold
constexpr double kScoreThreshold = 250;


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

  auto Simulate(double beta0, const GeneratorInterface& generator) -> SimulationResult {
    constexpr double gamma1 = 1.25, gamma2 = 1.04;
    std::vector<uint32_t> infected = GenerateInfected(generator);
    std::vector<Person> persons;
    std::uniform_int_distribution<> uniform(0, 14);

    SimulationResult result(infected);
    result.error = 0;
    int32_t cumulative_positive = 0;
    for (uint32_t day = 0; day < positive_.size(); ++day) {
      for (uint32_t i = 0; i < infected[day]; ++i) {
        auto age = generate_age(&random_generator_);
        auto symptoms = beta_distribution(1, bs[age], &random_generator_);
        persons.emplace_back(
            symptoms, std::ceil(symptoms * kSymptomsLength + uniform(random_generator_)), day);
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
      if (cumulative_positive + positive_[day] > 0) {
        result.error -= log_distance_probability(cumulative_positive, positive_[day]);
        // std::cout << day << " " << cumulative_positive << " " << positive_[day] << " "
        //           << log_distance_probability(cumulative_positive, positive_[day])
        //           << std::endl;
      }

      persons.resize(iter - persons.begin());
    }

    return result;
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

  // auto generator = ExponentialGenerator(kGamma1, kGamma2);
  auto generator = PolynomialGenerator(kGamma1, kPolynomialDegree);
  constexpr uint32_t kIterations = 200;
  const uint32_t kEarlyStop = std::ceil(std::sqrt(kIterations));
  std::cout << "prefix_length optimal_b0 dead_count best_error" << std::endl;
  std::vector<YAML::Node> nodes;
#pragma omp parallel for shared(positive, tested)
  for (uint32_t prefix_length = 2; prefix_length < 20; ++prefix_length) {
    Simulator simulator(prefix_length, positive, tested);
    uint32_t optimal_b0 = -1, optimal_dead_count;
    double best = 1e10;
    for (uint32_t b0 = 30; b0 <= 200; b0 += 3) {
      YAML::Node node;
      node["params"]["prefix_length"] = prefix_length;
      node["params"]["b0"] = b0;
      // node["params"]["gamma2"] = kGamma2;
      node["params"]["alpha"] = kPolynomialDegree;
      node["params"]["deltas"] = generator.CreateDeltas(prefix_length + kRestrictionDay,
                                                        prefix_length + tested.size() + kExtraDays);
      double sum_error = 0, dead_count = 0;
      int iterations = 0;
      std::vector<SimulationResult> results;
      for (uint32_t i = 0; i < kIterations; ++i) {
        auto result = simulator.Simulate(b0, generator);
        sum_error += result.error;
        dead_count += std::accumulate(result.dead_count.begin(), result.dead_count.end(), 0);
        results.push_back(result);
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

      if (sum_error < kScoreThreshold) {
        for (const auto& result : results) {
          node["results"].push_back(result.Serialize());
        }
      } else {
        node["result_abbrev"]["error"] = sum_error;
        node["result_abbrev"]["dead_count"] = dead_count;
      }
      nodes.push_back(node);
    }

    std::cout << std::setw(2) << prefix_length << std::setw(4) << optimal_b0 << std::setw(4)
              << optimal_dead_count << std::setw(9) << best << std::endl;
  }

  YAML::Emitter yaml_out;
  yaml_out << YAML::BeginSeq;
  for (const auto& node : nodes) {
    yaml_out << YAML::Flow << node;
  }
  yaml_out << YAML::EndSeq;

  std::ofstream results_yaml("results.yaml");
  results_yaml << yaml_out.c_str() << std::endl;
}
