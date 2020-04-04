# COVID-19 simulation for Slovakia

Based on [Stochastic Simulation of the Initial Phase of the COVID-19 Epidemic in Slovakia](http://www.iam.fmph.uniba.sk/ospm/Harman/COR01.pdf) by Radoslav Harman.

# Building using CMake

You need [googletest](https://github.com/google/googletest), [yaml-cpp](https://github.com/jbeder/yaml-cpp) and OpenMP installed (usually comes with the compiler).

```sh
mkdir build && cd $_
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
```

# Known issues

* Code doesn't compile in clang, due to `constexpr` functions that aren't really `constexpr`.


<!--
# Building using Conan

NOTE: Ideally, Conan downloads the dependencies for you and compiles the project, but the package for `yaml-cpp` is broken and we therefore recommend installing it, e.g. by `apt-get install libyaml-cpp-dev` in Ubuntu.

Conan is able to download the dependencies and compile the project. However, you still need OpenMP on your system, though that usually comes installed with the compiler.

```sh
conan create .
```

TODO: expand on actually running the code
-->
