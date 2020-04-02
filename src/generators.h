#pragma once

#include <cstdint>
#include <cmath>
#include <vector>

class GeneratorInterface {
 public:
  auto ExponentialPrefix(double gamma1, uint32_t count) const -> std::vector<double> {
    std::vector<double> deltas = {1.0};
    for (uint32_t i = 0; i < count; ++i) {
      deltas.push_back(deltas.back() * gamma1);
    }
    return deltas;
  }

  virtual auto CreateDeltas(uint32_t t0, uint32_t count) const -> std::vector<double> = 0;
  virtual ~GeneratorInterface() = default;
};

class ExponentialGenerator : public GeneratorInterface {
 public:
  ExponentialGenerator(double gamma1, double gamma2)
      : gamma1_(gamma1), gamma2_(gamma2) {}
  auto CreateDeltas(uint32_t t0, uint32_t count) const -> std::vector<double> override {
    std::vector<double> result = ExponentialPrefix(gamma1_, t0);
    for (int i = 0; i + t0 + 1 < count; ++i) {
      result.push_back(result.back() * gamma2_);
    }
    return result;
  }
  ~ExponentialGenerator() override = default;

 private:
  double gamma1_;
  double gamma2_;
};

constexpr double kPowerLawDecay = 35;

class PowerLawGenerator : public GeneratorInterface {
 public:
  PowerLawGenerator(double gamma1, double power_law_exponent)
      : gamma1_(gamma1), power_law_exponent_(power_law_exponent) {}
  auto CreateDeltas(uint32_t t0, uint32_t count) const -> std::vector<double> override {
    std::vector<double> values;
    for (int i = 1; i <= count + 1; ++i) {
      double val = std::pow(i, power_law_exponent_) * exp(-i / kPowerLawDecay);
      values.push_back(val);
    }
    std::vector<double> result = ExponentialPrefix(gamma1_, t0);
    for (int i = 1; i + t0 < count; ++i) {
      result.push_back(result.back() * (values[i] - values[i - 1]));
    }
    return result;
  }
  ~PowerLawGenerator() override = default;

 private:
  double gamma1_;
  double power_law_exponent_;
};
