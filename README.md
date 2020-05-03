# COVID-19 prediction graphs and simulation of the initial phase in Slovakia

[![Build Status](https://travis-ci.com/lukipuki/COVID-19-simulation.svg?branch=master)](https://travis-ci.com/lukipuki/COVID-19-simulation)

This repository has two main parts, prediction graphs and simulation of the initial phase of the epidemic in Slovakia.

# Prediction graphs

The graphs show [COVID-19 predictions by mathematicians Katarína Boďová and Richard Kollár](https://graphs.lukipuki.sk/covid19/normal/). This part is in the [covid_graphs directory](./covid_graphs) and has its own [README](covid_graphs/README.md).

![Graph of active cases in Germany](content/germany-apr11.png)


# Simulation of the initial phase in Slovakia

The simulation is for the initial phase of the epidemic in Slovakia, based on [Stochastic Simulation of the Initial Phase of the COVID-19 Epidemic in Slovakia](http://www.iam.fmph.uniba.sk/ospm/Harman/COR01.pdf) by the statistician Radoslav Harman. Some visualization tools for the simulation also sit in the [covid_graphs](./covid_graphs) directory.

![Simulation of total confirmed COVID-19 cases in Slovakia](content/cumulative_simulation.png)


## Building using Conan

[Conan](https://conan.io) is able to download the dependencies and compile the project. However, you still need OpenMP on your system, though that usually comes installed with the compiler (for Clang, you need to also install `libomp`).

If you've never used Conan, you need to configure it first.

```sh
conan profile new default --detect
conan profile update settings.compiler.libcxx=libstdc++11 default
```

Once configured, you can create the package.
```
conan create .
# Alternatively, adding '-o growth_type=exponential' creates a binary with simulated exponential growth.
```

## Running and viewing protobuf files

```sh
conan install -g virtualrunenv 'COVID-19-simulation/1.0.0@'
source activate_run.sh
simulation Slovakia.data
source deactivate_run.sh  # deactivate once you're done
# The simulation creates a proto file 'polynomial.sim' or 'exponential.sim', which can be examined using protoc
cat polynomial.sim | protoc --decode SimulationResults src/simulation_results.proto
```

You can visualize the simulation in graphs. See the [covid_graphs README](covid_graphs/README.md) for examples.

Conan can be used to install `protoc`. This is especially useful on Debian-based systems, which have an old version.

```sh
conan install -g virtualrunenv 'protoc_installer/[>=0]@bincrafters/stable'
source activate_run.sh && protoc --decode ...  # More information on protoc usage is above
...
source deactivate_run.sh  # deactivate once you're done
```

## Building using CMake [NOT RECOMMENDED]

This method is not recommended, since Debian-based systems including Ubuntu ship a very old version of the protobuf library (3.6). This clashes with the version used by our visualizations. If you do not want to create any graphs or your system runs a newer version of the protobuf library (we tested 3.9 and 3.11), then the CMake method works too.

You need [googletest](https://github.com/google/googletest), [protobuf](https://github.com/protocolbuffers/protobuf) and OpenMP installed (usually comes with the compiler). You can also use the `Dockerfile` in the root of the repository, which has all the dependencies installed.

```sh
mkdir build && cd $_
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```
