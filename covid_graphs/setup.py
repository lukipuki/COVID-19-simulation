#!/usr/bin/env python3

from setuptools import find_namespace_packages, setup

setup(
    name="covid_graphs",
    version="1.0",
    description="COVID-19 graph plotting",
    install_requires=[
        "click",
        "click_pathlib",
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
    python_requires=">=3.7",
    packages=find_namespace_packages(),
    scripts=["covid_graphs/scripts/prepare_data.py", "covid_graphs/scripts/scatter_plot.py"],
    entry_points={
        "console_scripts": [
            "covid_graphs.run_server=covid_graphs.scripts.server:run_server"
        ]
    },
    package_data={"": ["*.html"]},
)
