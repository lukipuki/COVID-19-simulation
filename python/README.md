# Graphs and visualizations related to COVID-19

## Local development

This script creates a virtual environment with all development dependencies.
```sh
./create_dev_venv.sh
source .venv/bin/activate # Don't forget to activate the environment
```
To run tests, simply run:
```sh
./run_tests.sh
```

For quick development or data examination, running standalone graphs can be useful.
```sh
covid_graphs.show_country_plot data/Spain.data
covid_graphs.show_scatter_plot data/Slovakia.data polynomial.sim
covid_graphs.show_heat_map exponential.sim
```
