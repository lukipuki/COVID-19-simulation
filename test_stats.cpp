#include "gtest/gtest.h"

#include <random>
#include <vector>

#include "stats.h"

TEST(Stats, CalculatesB) {
  std::random_device rd;
  std::mt19937 gen(rd());

  std::vector<double> ds = {0.02, 0.1, 0.3};
  constexpr uint32_t kIterations = 1 << 16;
  for (double d : ds) {
    double b = calculate_b(d);
    double sum = 0;
    for (uint32_t i = 0; i < kIterations; ++i) {
      sum += static_cast<double>(beta_distribution(1, b, &gen) > 0.5);
    }
    double result = sum / kIterations;
    EXPECT_NEAR(d, result, 0.05);
  }
}

TEST(Stats, CalculatesQuantiles) {
  std::random_device rd;
  std::mt19937 gen(rd());
  constexpr uint32_t kIterations = 1 << 20;

  double quantile = 0.999;  // 99.9-th percentile of population
  constexpr double kBeta = 80;
  double value = qbeta(kBeta, quantile);
  double sum = 0;
  for (uint32_t i = 0; i < kIterations; ++i) {
    sum += static_cast<double>(beta_distribution(1, kBeta, &gen) < value);
  }

  sum /= kIterations;
  EXPECT_NEAR(sum, quantile, 0.001);
}

TEST(Stats, GeneratesAgeAccordingToPopulation) {
  std::random_device rd;
  std::mt19937 gen(rd());
  constexpr uint32_t kIterations = 1 << 20;
  std::vector<double> occurences(population_age.size(), 0.0);
  for (uint32_t i = 0; i < kIterations; ++i) {
    occurences[generate_age(&gen)] += 1;
  }
  for (auto& occurence : occurences) occurence /= kIterations;
  for (uint32_t i = 0; i < population_age.size(); ++i) {
    EXPECT_NEAR(occurences[i], population_age[i], 0.001);
  }
}

