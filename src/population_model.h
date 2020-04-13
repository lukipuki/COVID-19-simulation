#pragma once

#include <array>
#include <cassert>
#include <cmath>
#include <random>
#include <vector>

// Population of Slovakia
constexpr uint32_t kPopulationSize = 5450000;
// Death probabilities by decade of life
constexpr uint32_t kDecadesCount = 9;
constexpr std::array<double, kDecadesCount> kPopulationAge = {0.11, 0.10, 0.12, 0.16, 0.15,
                                                              0.13, 0.13, 0.07, 0.03};
constexpr std::array<double, kDecadesCount> kDeathProbabilities = {
    0.002, 0.002, 0.002, 0.002, 0.004, 0.013, 0.036, 0.08, 0.148};
constexpr double kDeathThreshold = 0.5;
constexpr uint32_t kSymptomsLength = 28;
constexpr uint32_t kFactorialLength = 5000;

// Class containing all the logic for generating people and their symptoms. Each person:
// * is generated according to population age distribution
// * has symptoms' severity generated based on their age
// * has disease length generated based on symptoms severity
class PopulationModel {
 public:
  PopulationModel() : log_factorials_(kFactorialLength), random_generator_(std::random_device{}()) {
    log_factorials_[0] = 0;
    for (uint32_t i = 1; i < kFactorialLength; i++) {
      log_factorials_[i] = log_factorials_[i - 1] + std::log(i);
    }

    const double kLog2 = std::log(2);
    for (int i = 0; i < kDecadesCount; i++) {
      b_[i] = -std::log(kDeathProbabilities[i]) / kLog2;
    }
  }

  // Logarithm of the distance function. More details in Rado Harman's COR01.pdf.
  auto LogDistance(uint32_t z, uint32_t c) -> double {
    if (z + c == 0) {
      return 0;
    }
    assert(z >= 0 && c >= 0);
    uint32_t max = std::max(z, c) + 1;
    for (uint32_t i = log_factorials_.size(); i < max; ++i) {
      log_factorials_.push_back(log_factorials_.back() + std::log(i));
    }
    double positive = (z + c) * std::log((z + c) / 2.);
    double negative = z + c + log_factorials_[z] + log_factorials_[c];
    return positive - negative;
  }

  // Generates age decade according to Slovak population age distribution
  auto GenerateAgeDecade() -> uint32_t {
    std::uniform_real_distribution<> distribution(0.0, 1.0);
    double generated = distribution(random_generator_);
    double sum = 0;
    uint32_t res = 0;
    for (; sum + kPopulationAge[res] <= generated; ++res) {
      sum += kPopulationAge[res];
    }
    assert(res < kDecadesCount);
    return res;
  }

  // Generates symptoms based on age decage. More details in Rado Harman's COR01.pdf.
  auto GenerateSymptoms(uint32_t age_decade) -> double {
    return BetaDistribution(1, b_[age_decade]);
  }

  // Generates disease length based on symptoms. More details in Rado Harman's COR01.pdf.
  auto DiseaseLength(double symptoms) -> uint32_t {
    std::uniform_int_distribution<> uniform(0, 14);
    return std::ceil(symptoms * kSymptomsLength + uniform(random_generator_));
  }

  // Poisson distribution.
  auto PoissonDistribution(double mean) -> double {
    std::poisson_distribution<> poisson(mean);
    return poisson(random_generator_);
  }

  // Generates the number of infected based on deltas. See Rado Harman's COR01.pdf for the
  // definition of delta_t.
  auto GenerateInfected(const std::vector<double>& deltas)
      -> std::vector<uint32_t> {
    assert(count <= deltas.size());
    std::vector<uint32_t> infected;
    for (double mean : deltas) {
      infected.push_back(PoissonDistribution(mean));
    }
    return infected;
  }

  // Calculates threshold for testing, when we are testing 'tested_count' people, given 'b0' (see
  // Rado Harman's COR01.pdf for the definition of b0).
  static auto CalculateThreshold(uint32_t b0, uint32_t tested_count) -> double {
    double quantile = 1 - static_cast<double>(tested_count) / kPopulationSize;
    return BetaQuantile(b0, quantile);
  }

 private:
  auto BetaDistribution(double alpha, double beta) -> double {
    std::gamma_distribution<> X(alpha, 1), Y(beta, 1);
    double x = X(random_generator_), y = Y(random_generator_);
    return x / (x + y);
  }

  // Quantile function of beta distribution B(1, b).
  static auto BetaQuantile(double b, double quantile) -> double {
    return 1 - pow(1 - quantile, 1.0 / b);
  }

  std::vector<double> log_factorials_;
  // For each decade of life 'i', calculate 'b_[i]', such that
  // 'Pr[B(1, b_[i]) > 0.5] = kDeathProbabilities[i]'. 'B()' is the beta distribution.
  std::array<double, kDecadesCount> b_;

  std::mt19937 random_generator_;
};
