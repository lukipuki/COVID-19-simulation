#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="covid_web",
    version="1.0",
    description="COVID-19 web apps",
    install_requires=["click", "click_pathlib", "covid_graphs", "dash", "Flask",],
    dependency_links=[],
    python_requires=">=3.7",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "covid_web.run_server = covid_web.server:run_server",
            "covid_web.generate_static_rest = covid_web.rest:generate_static_rest",
        ]
    },
    package_data={"": ["*.html"], "covid_web": ["py.typed"]},
)
