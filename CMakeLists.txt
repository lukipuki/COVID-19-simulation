cmake_minimum_required (VERSION 3.12)
project(covid19_simulation)

set(CMAKE_EXPORT_COMPILE_COMMANDS On)

find_package(OpenMP)
find_package(yaml-cpp REQUIRED)

if(EXISTS ${CMAKE_BINARY_DIR}/conan_paths.cmake)
  include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
endif()

add_executable(simulation simulation.cpp)
target_compile_features(simulation PRIVATE cxx_std_17)
target_link_libraries(simulation PRIVATE yaml-cpp $<$<BOOL:${OpenMP_FOUND}>:OpenMP::OpenMP_CXX>)

enable_testing()
find_package(GTest REQUIRED)
include(GoogleTest)

add_executable(test_stats test_stats.cpp)
target_compile_features(test_stats PRIVATE cxx_std_17)
target_link_libraries(test_stats GTest::GTest GTest::Main)
gtest_add_tests(TARGET test_stats)
