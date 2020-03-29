#include <algorithm>
#include <cassert>
#include <iostream>

#include "stats.h"

auto generate_infected(double gamma1, double gamma2, uint32_t tmax, std::mt19937* gen)
    -> std::vector<uint32_t> {
  uint32_t t0 = tmax - 16;
  std::vector<double> deltas = {1.0};
  for (uint32_t i = 0; i < t0; ++i) {
    deltas.push_back(deltas.back() * gamma1);
  }
  for (uint32_t i = t0; i < tmax; ++i) {
    deltas.push_back(deltas.back() * gamma2);
  }

  std::vector<uint32_t> infected(1);
  for (uint32_t i = 0; i < tmax; ++i) {
    std::poisson_distribution<> possion(deltas[i]);
    infected.push_back(possion(*gen));
  }
  return infected;
}

int main() {
  std::random_device rd;
  std::mt19937 gen(rd());

  std::vector<uint32_t> tested = {37,  32,  38,  50,  49,  64,  72,  69,  116,
                                  99,  35,  118, 197, 228, 148, 293, 217, 283,
                                  354, 399, 235, 432, 464, 325, 912, 747, 720};
  std::vector<uint32_t> positive = {0,  0,  0, 0,  1,  2,  2, 2,  0,  3,  11, 11, 12, 17,
                                    11, 25, 8, 19, 13, 41, 7, 19, 12, 10, 43, 23, 22};
  assert(tested.size() == positive.size());

  double gamma1 = 1.25, gamma2 = 1.05;
  uint32_t tmax = positive.size();
  std::vector<uint32_t> infected = generate_infected(gamma1, gamma2, tmax, &gen);

  std::vector<double> bs;
  std::transform(kDeathProbabilities, kDeathProbabilities + kDecadesCount, std::back_inserter(bs),
                 calculate_b);

  for (uint32_t day = 0; day < infected.size(); ++day) {
    for (uint32_t i = 0; i < tmax; ++i) {
      auto age = generate_age(&gen);
      auto symptoms = beta_distribution(1, bs[age], &gen);
    }

    double quantile = 1 - static_cast<double>(tested[day]) / kPopulationSize;
    // To be continued ...
  }
}
