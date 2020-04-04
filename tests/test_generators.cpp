#include "gmock/gmock.h"
#include "gtest/gtest.h"

#include <vector>

#include "generators.h"

using testing::DoubleNear;
using testing::ElementsAre;

constexpr double kEps = 1e-9;

TEST(Generators, Exponential) {
  constexpr double kGamma1 = 1.25, kGamma2 = 1.05;
  auto generator = ExponentialGenerator(kGamma1, kGamma2);
  std::vector<double> deltas = generator.CreateDeltas(3, 6);

  EXPECT_THAT(deltas, ElementsAre(DoubleNear(1.0, kEps), DoubleNear(kGamma1, kEps),
                                  DoubleNear(std::pow(kGamma1, 2), kEps),
                                  DoubleNear(std::pow(kGamma1, 3), kEps),
                                  DoubleNear(std::pow(kGamma1, 3) * kGamma2, kEps),
                                  DoubleNear(std::pow(kGamma1, 3) * kGamma2 * kGamma2, kEps)));
}

TEST(Generators, ExponentialNoSecondPhase) {
  constexpr double kGamma1 = 1.25, kGamma2 = 1.05;
  auto generator = ExponentialGenerator(kGamma1, kGamma2);
  std::vector<double> deltas = generator.CreateDeltas(3, 3);

  EXPECT_THAT(deltas, ElementsAre(DoubleNear(1.0, kEps), DoubleNear(kGamma1, kEps),
                                  DoubleNear(std::pow(kGamma1, 2), kEps)));
}

TEST(Generators, Polynomial) {
  constexpr double kGamma1 = 1.25, kPolynomialDegree = 1.2;
  auto generator = PolynomialGenerator(kGamma1, kPolynomialDegree);
  std::vector<double> deltas = generator.CreateDeltas(1, 4);

  double second_step = std::pow(kGamma1, 1);
  std::vector<double> power_law_sequence = {
      // second_step * (std::pow(2, kPolynomialDegree) * std::exp(-2 / kPolynomialDecay) -
      //                std::pow(1, kPolynomialDegree) * std::exp(-1 / kPolynomialDecay)),
      // second_step * (std::pow(3, kPolynomialDegree) * std::exp(-3 / kPolynomialDecay) -
      //                std::pow(2, kPolynomialDegree) * std::exp(-2 / kPolynomialDecay))
      second_step * (std::pow(2, kPolynomialDegree) - std::pow(1, kPolynomialDegree)),
      second_step * (std::pow(3, kPolynomialDegree) - std::pow(2, kPolynomialDegree))
  };

  EXPECT_THAT(deltas, ElementsAre(DoubleNear(1.0, kEps), DoubleNear(kGamma1, kEps),
                                  DoubleNear(power_law_sequence[0], kEps),
                                  DoubleNear(power_law_sequence[1], kEps)));
}
