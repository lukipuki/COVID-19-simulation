# COVID-19 simulation for Slovakia

Based on [Stochastic Simulation of the Initial Phase of the
COVID-19 Epidemic in Slovakia](http://www.iam.fmph.uniba.sk/ospm/Harman/COR01.pdf) by Radoslav Harman.

# Building using Conan

Conan is able to download the dependencies and compile the project. However, you still need OpenMP on your system, though that usually comes installed with the compiler.

```sh
conan create .
```

TODO: expand on actually running the code


# Building using CMake

```sh
mkdir build && cd $_
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

You need [googletest](https://github.com/google/googletest), [yaml-cpp](https://github.com/jbeder/yaml-cpp) and OpenMP installed.
