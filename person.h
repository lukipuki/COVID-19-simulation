#pragma once

constexpr double kDeathThreshold = 0.5;

enum State { Active, Recovered, Dead };

class Person {
 public:
  Person() = default;
  Person(double symptom_max, uint32_t culmination_length, uint32_t start_date)
      : state_(State::Active), start_date_(start_date), symptoms_() {
    double step = symptom_max / culmination_length;
    for (uint32_t i = 0; i <= culmination_length; ++i) {
      symptoms_.push_back(i * step);
    }
    for (int32_t i = static_cast<int32_t>(culmination_length) - 1; i >= 0; --i) {
      symptoms_.push_back(symptoms_[i]);
    }
  }

  double CurrentSymptoms(uint32_t date) const {
    if (date < start_date_ || date >= start_date_ + symptoms_.size()) return 0;
    return symptoms_[date - start_date_];
  }

  auto HasDied(uint32_t date) -> bool const {
    if (date < start_date_ || date >= start_date_ + symptoms_.size()) return false;
    if (state_ == State::Active && symptoms_[date - start_date_] > kDeathThreshold) {
      state_ = State::Dead;
      return true;
    }
  }

 private:
  State state_;
  uint32_t start_date_;
  std::vector<double> symptoms_;
};
