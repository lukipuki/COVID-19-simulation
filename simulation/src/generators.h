#pragma once

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <vector>

constexpr double kPolynomialDecay = 35;

class GeneratorInterface {
 public:
  auto ExponentialPrefix(double gamma1, uint32_t count) const -> std::vector<double> {
    std::vector<double> deltas = {1.0};
    for (uint32_t i = 0; i < count; ++i) {
      deltas.push_back(deltas.back() * gamma1);
    }
    return deltas;
  }

  [[nodiscard]] virtual auto CreateDeltas(uint32_t t0, uint32_t count) const
      -> std::vector<double> = 0;
  virtual ~GeneratorInterface() = default;
};

class ExponentialGenerator : public GeneratorInterface {
 public:
  ExponentialGenerator(double gamma1, double gamma2) : gamma1_(gamma1), gamma2_(gamma2) {}
  // Creates deltas as defined in COR01.pdf.
  [[nodiscard]] auto CreateDeltas(uint32_t t0, uint32_t count) const
      -> std::vector<double> override {
    t0 = std::min(t0, count - 1);
    std::vector<double> result = ExponentialPrefix(gamma1_, t0);
    while (result.size() < count) {
      result.push_back(result.back() * gamma2_);
    }
    return result;
  }
  ~ExponentialGenerator() override = default;

 private:
  double gamma1_;
  double gamma2_;
};

class PolynomialGenerator : public GeneratorInterface {
 public:
  PolynomialGenerator(double gamma1, double polynomial_exponent)
      : gamma1_(gamma1), polynomial_exponent_(polynomial_exponent) {}
  // Creates deltas with polynomial growth after t0.
  [[nodiscard]] auto CreateDeltas(uint32_t t0, uint32_t count) const
      -> std::vector<double> override {
    t0 = std::min(t0, count - 1);
    std::vector<double> values;
    for (int i = 1; i <= count + 1; ++i) {
      // double val = std::pow(i, polynomial_exponent_) * exp(-i / kPolynomialDecay);
      double val = std::pow(i, polynomial_exponent_);
      values.push_back(val);
    }
    std::vector<double> result = ExponentialPrefix(gamma1_, t0);
    double base = result.back();
    for (int i = 1; i + t0 < count; ++i) {
      result.push_back(base * (values[i] - values[i - 1]));
    }
    assert(result.size() == count);
    return result;
  }
  ~PolynomialGenerator() override = default;

 private:
  double gamma1_;
  double polynomial_exponent_;
};
