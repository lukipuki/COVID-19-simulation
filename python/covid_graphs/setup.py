#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="covid_graphs",
    version="1.0",
    description="COVID-19 graph plotting",
    install_requires=[
        "click==7.0",
        "click_pathlib",
        "dash==1.21.0", "Flask==1.1.1",
        "numpy==1.21.5",
        "pandas==0.25.3",
        "plotly==4.14.3",
        "protobuf==3.17.3",
        "pymc3==3.11.5",
        "pytest",
        "scipy==1.7.3",
    ],
    dependency_links=[],
    python_requires=">=3.7",
    packages=find_packages(),
    package_data={"covid_graphs": ["py.typed"]},
    entry_points={
        "console_scripts": [
            "covid_graphs.prepare_data = covid_graphs.prepare_data:main",
            "covid_graphs.show_country_plot = covid_graphs.country_graph:show_country_plot",
            "covid_graphs.show_heat_map = covid_graphs.heat_map:show_heat_map",
            "covid_graphs.show_scatter_plot = covid_graphs.scatter_plot:show_scatter_plot",
            "covid_graphs.generate_predictions = covid_graphs.prediction_generator:generate_predictions",
            "covid_graphs.calculate_posterior = covid_graphs.bayesian:calculate_posterior",
        ]
    },
)
