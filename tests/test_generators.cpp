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

TEST(Generators, PowerLaw) {
  constexpr double kGamma1 = 1.25, kPowerLawExponent = 1.2;
  auto generator = PowerLawGenerator(kGamma1, kPowerLawExponent);
  std::vector<double> deltas = generator.CreateDeltas(1, 4);

  double second_step = std::pow(kGamma1, 1);
  std::vector<double> power_law_sequence = {
      // second_step * (std::pow(2, kPowerLawExponent) * std::exp(-2 / kPowerLawDecay) -
      //                std::pow(1, kPowerLawExponent) * std::exp(-1 / kPowerLawDecay)),
      // second_step * (std::pow(3, kPowerLawExponent) * std::exp(-3 / kPowerLawDecay) -
      //                std::pow(2, kPowerLawExponent) * std::exp(-2 / kPowerLawDecay))
      second_step * (std::pow(2, kPowerLawExponent) - std::pow(1, kPowerLawExponent)),
      second_step * (std::pow(3, kPowerLawExponent) - std::pow(2, kPowerLawExponent))
  };

  EXPECT_THAT(deltas, ElementsAre(DoubleNear(1.0, kEps), DoubleNear(kGamma1, kEps),
                                  DoubleNear(power_law_sequence[0], kEps),
                                  DoubleNear(power_law_sequence[1], kEps)));
}
