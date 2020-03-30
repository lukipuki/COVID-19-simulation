#include <algorithm>
#include <cassert>
#include <iostream>

#include "person.h"
#include "stats.h"

std::vector<double> bs;
const std::vector<uint32_t> tested = {37,  32,  38,  50,  49,  64,  72,  69,  116,
                                      99,  35,  118, 197, 228, 148, 293, 217, 283,
                                      354, 399, 235, 432, 464, 325, 912, 747, 720};
const std::vector<uint32_t> positive = {0,  0,  0, 0,  1,  2,  2, 2,  0,  3,  11, 11, 12, 17,
                                        11, 25, 8, 19, 13, 41, 7, 19, 12, 10, 43, 23, 22};
constexpr uint32_t kRestrictionDay = 11;  // 0-indexed March 12th

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
  }

  auto Simulate(double beta0)
      -> std::vector<uint32_t> {
    constexpr double gamma1 = 1.25, gamma2 = 1.04;
    std::vector<uint32_t> infected = GenerateInfected(gamma1, gamma2);
    std::vector<Person> cases;
    std::uniform_int_distribution<> uniform(0, 14);
    std::vector<uint32_t> result;
    for (uint32_t day = 0; day < infected.size(); ++day) {
      for (uint32_t i = 0; i < infected[day]; ++i) {
        auto age = generate_age(&gen_);
        auto symptoms = beta_distribution(1, bs[age], &gen_);
        cases.emplace_back(symptoms, std::ceil(symptoms * 28 + uniform(gen_)), day);
      }

      assert(day < tested_.size());
      double quantile = 1 - static_cast<double>(tested_[day]) / kPopulationSize;
      double threshold = qbeta(beta0, quantile);

      auto iter = std::partition(cases.begin(), cases.end(), [day, threshold](const Person& ca) {
        return ca.CurrentSymptoms(day) < threshold;
      });
      uint32_t positive_cases = cases.end() - iter;
      result.push_back(positive_cases);
      cases.resize(iter - cases.begin());
      std::cout << day << " " << positive_[day] << " " << positive_cases << std::endl;
    }
    return result;
  }

 private:
  auto GenerateInfected(double gamma1, double gamma2)
      -> std::vector<uint32_t> {
    std::vector<double> deltas = {1.0};
    for (uint32_t i = 0; i < t0_; ++i) {
      deltas.push_back(deltas.back() * gamma1);
    }
    for (uint32_t i = t0_; i < tmax_; ++i) {
      deltas.push_back(deltas.back() * gamma2);
    }

    std::vector<uint32_t> infected = {1};
    // TODO: The i+1 is here, because the day numbering goes too far, I think
    for (uint32_t i = 0; i + 1 < deltas.size(); ++i) {
      std::poisson_distribution<> possion(deltas[i]);
      infected.push_back(possion(gen_));
    }
    return infected;
  }

  uint32_t tmax_;
  uint32_t t0_;

  std::vector<uint32_t> tested_;
  std::vector<uint32_t> positive_;

  std::random_device rd_;
  std::mt19937 gen_;
};

int main() {
  std::transform(kDeathProbabilities, kDeathProbabilities + kDecadesCount, std::back_inserter(bs),
                 calculate_b);
  assert(tested.size() == positive.size());

  Simulator simulator(positive.size() + 6);
  for (int i = 0; i < 1; ++i) {
    simulator.Simulate(150);
  }
}
