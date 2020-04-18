# Graphs and visualizations related to COVID-19

## Running the whole server

In the root directory of the repository, run `docker-compose`.
```sh
docker-compose up --build # Optionally add -d for deamon
```
You can then access the server locally at [localhost:8081](http://127.0.0.1:8081).


### Running without Docker
Alternatively, you can run the server locally without Docker. Create a virtual
environment, install the `covid_graphs` package an run the server. You can use
a script provided in this directory:
```sh
./create_dev_venv.sh
source .venv/bin/activate
covid_graphs.run_server --data-dir data
```
Run `covid_graphs.run_server --help` for help on command parameters.


## Local development

This script creates a virtual environment with all development dependencies.
Don't forget to activate the environment:
```sh
./create_dev_venv.sh
source .venv/bin/activate
```

To run tests, simply run:
```sh
./run_tests.sh
```

For quick development or data examination, running standalone graphs can be useful.
```sh
covid_graphs.show_country_plot data Spain
covid_graphs.show_scatter_plot data/Slovakia.data polynomial.sim
covid_graphs.show_heat_map exponential.sim
```
