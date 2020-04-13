#pragma once

#include <cmath>
#include <optional>
#include <vector>

#include "stats.h"

class Person {
 public:
  Person() = default;
  Person(Stats* stats, uint32_t start_date) : start_date_{start_date}, date_of_death_{} {
    auto age_decade = stats->GenerateAgeDecade();
    auto symptoms_max = stats->GenerateSymptoms(age_decade);
    auto disease_length = stats->DiseaseLength(symptoms_max);

    double step = symptoms_max / disease_length;
    for (uint32_t i = 0; i <= disease_length; ++i) {
      symptoms_.push_back(i * step);
    }
    for (int32_t i = static_cast<int32_t>(disease_length) - 1; i >= 0; --i) {
      symptoms_.push_back(symptoms_[i]);
    }
    if (symptoms_max > kDeathThreshold) {
      date_of_death_ = std::ceil(disease_length * kDeathThreshold / symptoms_max) + start_date;
    }
  }

  // Returns the severity of symptoms on 'date'.
  auto CurrentSymptoms(uint32_t date) const -> double {
    // TODO(lukas): Instead of using 'symptoms_', try calculating them on the fly using 'step' and
    // the date.
    if (date < start_date_ || date >= start_date_ + symptoms_.size()) return 0;
    return symptoms_[date - start_date_];
  }

  auto DateOfDeath() const -> std::optional<uint32_t> { return date_of_death_; }

 private:
  uint32_t start_date_;
  std::vector<double> symptoms_;
  std::optional<uint32_t> date_of_death_;
};
