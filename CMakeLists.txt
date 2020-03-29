cmake_minimum_required (VERSION 3.12)
project(covid19_simulation)

set(CMAKE_EXPORT_COMPILE_COMMANDS On)

add_executable(simulation simulation.cpp)
target_compile_features(simulation PRIVATE cxx_std_17)

enable_testing()
find_package(GTest REQUIRED)
include(GoogleTest)

add_executable(test_stats test_stats.cpp)
target_compile_features(test_stats PRIVATE cxx_std_17)
target_link_libraries(test_stats GTest::GTest GTest::Main)
gtest_add_tests(TARGET test_stats)
