cmake_minimum_required (VERSION 3.12)
project(covid19_simulation)

set(CMAKE_EXPORT_COMPILE_COMMANDS On)

if(EXISTS ${CMAKE_BINARY_DIR}/conan_paths.cmake)
  include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
endif()

find_package(OpenMP)
find_package(yaml-cpp REQUIRED)

add_executable(simulation src/simulation.cpp)
target_compile_features(simulation PRIVATE cxx_std_17)
target_link_libraries(simulation PRIVATE yaml-cpp $<$<BOOL:${OpenMP_FOUND}>:OpenMP::OpenMP_CXX>)
target_include_directories(simulation PRIVATE src/)

enable_testing()
find_package(GTest REQUIRED)
include(GoogleTest)

add_executable(test_stats tests/test_stats.cpp)
target_compile_features(test_stats PRIVATE cxx_std_17)
target_link_libraries(test_stats GTest::GTest GTest::Main)
target_include_directories(test_stats PRIVATE src/)
gtest_add_tests(TARGET test_stats)

add_executable(test_generators tests/test_generators.cpp)
target_compile_features(test_generators PRIVATE cxx_std_17)
target_link_libraries(test_generators GTest::GTest GTest::Main)
target_include_directories(test_generators PRIVATE src/)
gtest_add_tests(TARGET test_generators)
