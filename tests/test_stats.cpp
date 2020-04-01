#include "gtest/gtest.h"

#include <random>
#include <vector>

#include "stats.h"

TEST(Stats, CalculatesB) {
  std::random_device rd;
  std::mt19937 gen(rd());

  std::array<double, 9> kDeathProbabilities = {0.002, 0.002, 0.002, 0.002, 0.004,
                                               0.013, 0.036, 0.08,  0.148};
  constexpr uint32_t kIterations = 1 << 16;
  for (uint32_t index : {1, 5, 8}) {
    double b = bs[index];
    double sum = 0;
    for (uint32_t i = 0; i < kIterations; ++i) {
      sum += static_cast<double>(beta_distribution(1, b, &gen) > 0.5);
    }
    double result = sum / kIterations;
    EXPECT_NEAR(kDeathProbabilities[index], result, 0.05);
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
  std::vector<double> occurences(kDecadesCount, 0.0);
  for (uint32_t i = 0; i < kIterations; ++i) {
    occurences[generate_age(&gen)] += 1;
  }
  for (auto& occurence : occurences) occurence /= kIterations;
  for (uint32_t i = 0; i < kDecadesCount; ++i) {
    EXPECT_NEAR(occurences[i], kPopulationAge[i], 0.001);
  }
}

TEST(Stats, GeneratesAccordingToPoisson) {
  std::random_device rd;
  std::mt19937 gen(rd());

  constexpr uint32_t kIterations = 1 << 23;
  constexpr uint32_t kSentinel = 1 << 20;
  std::vector<uint32_t> occurences(kSentinel, 0);
  constexpr uint32_t kPairSum = 22;
  for (uint32_t i = 0; i < kIterations; ++i) {
    std::poisson_distribution<> poisson(kPairSum / 2.0);
    uint32_t generated = poisson(gen);
    if (generated < kSentinel) {
      ++occurences[generated];
    }
  }

  std::vector<double> probabilities(kSentinel, 0);
  for (uint32_t i = 0; i < kSentinel; ++i) {
    probabilities[i] = occurences[i] / static_cast<double>(kIterations);
  }

  for (uint32_t z = 0; z <= kPairSum; ++z) {
    EXPECT_NEAR(std::exp(log_distance_probability(z, kPairSum - z)),
                probabilities[z] * probabilities[kPairSum - z], 0.0001);
  }
}
