#pragma once

#include <cmath>
#include <optional>

constexpr double kDeathThreshold = 0.5;

enum State { Active, Recovered, Dead };

class Person {
 public:
  Person() = default;
  Person(double symptom_max, uint32_t culmination_length, uint32_t start_date)
      : state_{State::Active}, start_date_{start_date}, symptoms_{}, date_of_death_{} {
    double step = symptom_max / culmination_length;
    for (uint32_t i = 0; i <= culmination_length; ++i) {
      symptoms_.push_back(i * step);
    }
    for (int32_t i = static_cast<int32_t>(culmination_length) - 1; i >= 0; --i) {
      symptoms_.push_back(symptoms_[i]);
    }
    if (symptom_max > kDeathThreshold) {
      date_of_death_ = std::ceil(culmination_length * kDeathThreshold / symptom_max) + start_date;
    }
  }

  double CurrentSymptoms(uint32_t date) const {
    if (date < start_date_ || date >= start_date_ + symptoms_.size()) return 0;
    return symptoms_[date - start_date_];
  }

  std::optional<uint32_t> DateOfDeath() const { return date_of_death_; }

 private:
  State state_;
  uint32_t start_date_;
  std::vector<double> symptoms_;
  std::optional<uint32_t> date_of_death_;
};
