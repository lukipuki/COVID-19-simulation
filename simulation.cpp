#include <algorithm>
#include <cassert>
#include <iostream>

#include "person.h"
#include "stats.h"

std::vector<double> bs;
const std::vector<uint32_t> tested = {37,  32,  38,  50,  49,  64,  72,  69,  116, 99,
                                      35,  118, 197, 228, 148, 293, 217, 283, 354, 399,
                                      235, 432, 464, 325, 912, 747, 720, 401, 688};
const std::vector<uint32_t> positive = {0,  0,  0, 0,  1,  2,  2, 2,  0,  3,  11, 11, 12, 17,
                                        11, 25, 8, 19, 13, 41, 7, 19, 12, 10, 43, 23, 22, 22, 27};
constexpr uint32_t kRestrictionDay = 11;  // 0-indexed March 12th
// constexpr uint32_t kRestrictionDay = 10;  // For power law
constexpr double kGamma2 = 1.04;
constexpr double kPowerLawExponent = 1.30;
constexpr double kPowerLawDecay = 35;
constexpr uint32_t kSymptomsLength = 28;

struct SimulationResult {
  SimulationResult() : cases{}, error{0}, dead_count{} {}
  std::vector<uint32_t> cases;
  std::vector<uint32_t> dead_count;
  double error;
};

class ExponentialGrowth {
 public:
  static auto GenerateNewValues(double last, uint32_t count) -> std::vector<double> {
    std::vector<double> result{last * kGamma2};
    for (int i = 1; i < count; ++i) {
      result.push_back(result.back() * kGamma2);
    }
    return result;
  }
};

class PowerLawGrowth {
 public:
  static auto GenerateNewValues(double last, uint32_t count) -> std::vector<double> {
    std::vector<double> values;
    for (int i = 1; i <= count + 1; ++i) {
      double val = std::pow(i, kPowerLawExponent) * exp(-i / kPowerLawDecay);
      values.push_back(val);
    }
    std::vector<double> result;
    for (int i = 1; i <= count; ++i) {
      result.push_back(last * (values[i] - values[i - 1]));
    }
    return result;
  }
};

template <typename Growth>
class Simulator {
 public:
  Simulator(uint32_t tmax)
      : tmax_{tmax},
        tested_(static_cast<uint32_t>(tmax - tested.size() + 1), 0),
        positive_(tested_.size(), 0),
        t0_{static_cast<uint32_t>(kRestrictionDay + tmax - positive.size())},
        rd_{},
        gen_(rd_()) {
    std::copy(tested.begin(), tested.end(), std::back_inserter(tested_));
    std::copy(positive.begin(), positive.end(), std::back_inserter(positive_));
    std::partial_sum(positive_.begin(), positive_.end(), positive_.begin());
  }

  auto Simulate(double beta0) -> SimulationResult {
    constexpr double gamma1 = 1.25, gamma2 = 1.04;
    std::vector<uint32_t> infected = GenerateInfected(gamma1, gamma2);
    std::vector<Person> persons;
    std::uniform_int_distribution<> uniform(0, 14);
    SimulationResult result;
    result.error = 0;
    int32_t cumulative_positive = 0;
    for (uint32_t day = 0; day < infected.size(); ++day) {
      for (uint32_t i = 0; i < infected[day]; ++i) {
        auto age = generate_age(&gen_);
        auto symptoms = beta_distribution(1, bs[age], &gen_);
        persons.emplace_back(symptoms, std::ceil(symptoms * kSymptomsLength + uniform(gen_)), day);
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

      cumulative_positive += persons.end() - iter;
      result.cases.push_back(cumulative_positive);
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
  auto GenerateInfected(double gamma1, double gamma2) -> std::vector<uint32_t> {
    std::vector<double> deltas = {1.0};
    for (uint32_t i = 0; i < t0_; ++i) {
      deltas.push_back(deltas.back() * gamma1);
    }
    double base = deltas.back();
    std::vector<double> next_part = Growth::GenerateNewValues(base, tmax_ - t0_);
    std::copy(next_part.begin(), next_part.end(), std::back_inserter(deltas));

    std::vector<uint32_t> infected;
    for (uint32_t i = 0; i < deltas.size(); ++i) {
      std::poisson_distribution<> possion(deltas[i]);
      infected.push_back(possion(gen_));
    }
    return infected;
  }

  uint32_t tmax_;
  uint32_t t0_;

  std::vector<uint32_t> tested_;
  // Cumulative sum of positive cases for each day
  std::vector<uint32_t> positive_;

  std::random_device rd_;
  std::mt19937 gen_;
};

int main() {
  std::transform(kDeathProbabilities, kDeathProbabilities + kDecadesCount, std::back_inserter(bs),
                 calculate_b);
  assert(tested.size() == positive.size());

  constexpr uint32_t kIterations = 50;
  std::cout << "prefix_length optimal_b0 dead_count best_error" << std::endl;
#pragma omp parallel for shared(positive, tested, bs)
  for (uint32_t prefix_length = 2; prefix_length < 9; ++prefix_length) {
    Simulator<ExponentialGrowth> simulator(positive.size() + prefix_length);
    // Simulator<PowerLawGrowth> simulator(positive.size() + prefix_length);
    uint32_t optimal_b0 = -1, optimal_dead_count;
    double best = 1e10;
    for (uint32_t b0 = 60; b0 <= 200; b0 += 3) {
      double sum_error = 0, dead_count = 0;
      for (uint32_t i = 0; i < kIterations; ++i) {
        auto result = simulator.Simulate(b0);
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
    std::cout << prefix_length << " " << optimal_b0 << " " << optimal_dead_count << " " << best << std::endl;
  }
}
