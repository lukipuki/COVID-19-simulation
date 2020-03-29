#pragma once

#include <cmath>
#include <random>
#include <vector>

// Population of Slovakia
constexpr uint32_t kPopulationSize = 5450000;
// Death probabilities by decade of life
constexpr double kDeathProbabilities[] = {0.002, 0.002, 0.002, 0.002, 0.004, 0.013, 0.036, 0.08, 0.148};
constexpr uint32_t kDecadesCount = 9;
constexpr double kPopulationAge[] = {0.11, 0.10, 0.12, 0.16, 0.15, 0.13, 0.13, 0.07, 0.03};
const double kLog2 = std::log(2);

auto beta_distribution(double alpha, double beta, std::mt19937* gen) -> double {
  std::gamma_distribution<> X(alpha, 1), Y(beta, 1);
  double x = X(*gen), y = Y(*gen);
  return x / (x + y);
}

auto calculate_b(double d) -> double {
  assert(d < 1);
  assert(d >= 0);
  return -std::log(d) / kLog2;
}

auto qbeta(double b, double q) -> double { return 1 - pow(1 - q, 1.0 / b); }

auto generate_age(std::mt19937* generator) -> uint32_t {
  std::uniform_real_distribution<> dis(0.0, 1.0);
  double generated = dis(*generator);
  double sum = 0;
  uint32_t res = 0;
  for (; sum + kPopulationAge[res] <= generated; ++res) {
    sum += kPopulationAge[res];
  }
  return res;
}
