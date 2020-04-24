from conans import ConanFile, CMake


class COVID19Simulation(ConanFile):
    name = "COVID-19-simulation"
    description = 'Simulating COVID-19 in Slovakia'
    url = "https://github.com/lukipuki/COVID-19-simulation",
    license = 'Unlicense'
    version = "1.0.0"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake_paths"
    scm = {
        "type": "git",
        "url": "auto"
    }

    options = {'growth_type': ['exponential', 'polynomial']}
    default_options = dict(growth_type='polynomial')

    build_requires = "gtest/1.8.1", "protoc_installer/3.9.1@bincrafters/stable"
    requires = "protobuf/3.9.1"

    def build(self):
        cmake = CMake(self)
        cmake.definitions['C19_EXPONENTIAL_GROWTH'] = self.options.growth_type == 'exponential'
        cmake.configure()

        if self.should_build:
            cmake.build()
        if self.should_test:
            cmake.test(output_on_failure=True)
        cmake.install()
