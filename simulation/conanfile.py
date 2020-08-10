from conans import ConanFile, CMake
import os


class COVID19Simulation(ConanFile):
    name = "COVID-19-simulation"
    description = "Simulating COVID-19 in Slovakia"
    url = "https://github.com/lukipuki/COVID-19-simulation"
    license = "Unlicense"
    version = "1.0.0"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake_paths"
    no_copy_source = True
    scm = {"type": "git", "url": "auto", "revision": "auto"}
    # export_sources = "simulation/*"

    options = {"growth_type": ["exponential", "polynomial"]}
    default_options = dict(growth_type="polynomial")

    build_requires = "gtest/1.8.1", "protoc_installer/3.9.1@bincrafters/stable"
    requires = "protobuf/3.9.1@bincrafters/stable"

    def build(self):
        cmake = CMake(self)
        cmake.definitions["C19_EXPONENTIAL_GROWTH"] = self.options.growth_type == "exponential"

        # We need to distinguish between two ways of building, e.g. 'conan create ..' versus
        # 'conan install .. & conan build'. Then self.source_folder is set differently.
        source_folder = self.source_folder
        if not os.path.isfile(os.path.join(source_folder, "conanfile.py")):
            source_folder = os.path.join(self.source_folder, "simulation")

        # kwargs = {'build_folder': 'build'}
        cmake.configure(source_folder=source_folder)

        if self.should_build:
            cmake.build()
        if self.should_test:
            cmake.test(output_on_failure=True)
        cmake.install()
