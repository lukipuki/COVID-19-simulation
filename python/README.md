# Graphs and visualizations related to COVID-19

## Usage

To run a web server, run `docker-compose` in the root directory of the repository.
```sh
docker-compose up --build # Optionally add -d for daemon
```
You can then access the server locally at [localhost:8081](http://127.0.0.1:8081).

Alternatively, you can install the libraries and run the server locally, see below.

## Local development

Create a virtual environment with all development dependencies:
```sh
./setup_environment.sh
source .venv/bin/activate # Don't forget to activate the environment
./run_tests.sh
./format_code.sh # Helper script to do code autoformat. The format is checked by tests.
```

To run a web server:
```sh
covid_web.run_server --data-dir ../data
```

For quick development or data examination, running standalone graphs can be useful.
```sh
covid_graphs.show_country_plot ../data/Spain.data
covid_graphs.show_scatter_plot ../data/Slovakia.data polynomial.sim
covid_graphs.show_heat_map exponential.sim
```

All the commands above can be called with `--help` option for additional information.
