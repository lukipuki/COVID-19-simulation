#pragma once

#include <cstdint>
#include <vector>

#include "yaml-cpp/yaml.h"

struct SimulationResult {
  explicit SimulationResult(const std::vector<uint32_t>& infected)
      : daily_positive{}, daily_infected{infected}, error{0}, dead_count{} {}
  auto Serialize() const -> YAML::Node {
    YAML::Node node;
    node["error"] = error;
    node["daily_positive"] = daily_positive;
    node["daily_infected"] = daily_infected;
    node["dead_count"] = dead_count;
    return node;
  }
  std::vector<uint32_t> daily_positive;
  std::vector<uint32_t> daily_infected;
  std::vector<uint32_t> dead_count;
  double error;
};
