#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="covid_graphs",
    version="1.0",
    description="COVID-19 graph plotting",
    install_requires=[
        "dash",
        "Flask",
        "numpy",
        "pandas",
        "protobuf",
        "plotly",
        "pytest",
        "scipy",

    ],
    dependency_links=[],
    include_package_data=True,
    python_requires=">=3.7",
    packages=find_packages(),
    scripts=["covid_graphs/scripts/converter.py", "covid_graphs/scripts/prepare_data.py", "covid_graphs/scripts/server.py"],
    package_data={},
)
