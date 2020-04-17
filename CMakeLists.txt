cmake_minimum_required (VERSION 3.12)
project(covid19_simulation)

set(CMAKE_EXPORT_COMPILE_COMMANDS On)

if(EXISTS ${CMAKE_BINARY_DIR}/conan_paths.cmake)
  include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
endif()

find_package(OpenMP)
find_package(Protobuf REQUIRED)

protobuf_generate_cpp(SRCS_SIMULATION HDRS_SIMULATION src/simulation_results.proto)
protobuf_generate_cpp(SRCS_COUNTRY HDRS_COUNTRY src/country_data.proto)

add_executable(simulation src/simulation.cpp ${SRCS_SIMULATION} ${SRCS_COUNTRY} ${HDRS_SIMULATION}
  ${HDRS_COUNTRY})
target_compile_features(simulation PRIVATE cxx_std_17)
target_link_libraries(simulation PRIVATE $<$<BOOL:${OpenMP_FOUND}>:OpenMP::OpenMP_CXX>
  protobuf::libprotobuf)
target_include_directories(simulation PRIVATE src/ ${CMAKE_CURRENT_BINARY_DIR}/)

install(TARGETS simulation
  RUNTIME DESTINATION bin
)

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
