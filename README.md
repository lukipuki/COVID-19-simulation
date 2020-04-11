# COVID-19 simulation for Slovakia

Based on [Stochastic Simulation of the Initial Phase of the COVID-19 Epidemic in Slovakia](http://www.iam.fmph.uniba.sk/ospm/Harman/COR01.pdf) by Radoslav Harman.

# Building using CMake

You need [googletest](https://github.com/google/googletest), [protobuf](https://github.com/protocolbuffers/protobuf) and OpenMP installed (usually comes with the compiler). You can also use the `Dockerfile` in the root of the repository, which has all the dependencies installed.

```sh
mkdir build && cd $_
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

# Running and viewing protobuf files

```
build/simulation data/Slovakia.data
protoc --protobuf_in=results.pb --decode SimulationResults src/simulation_results.proto
```

You can also visualize the results, see the [graphs README](graphs/README.md) for examples.

<!--
# Building using Conan

Conan is able to download the dependencies and compile the project. However, you still need OpenMP on your system, though that usually comes installed with the compiler.

```sh
conan create .
```
-->
