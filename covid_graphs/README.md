# Graphs and visualizations related to COVID-19

## Running the whole server

In the root directory of the repository, run `docker-compose`.
```sh
docker-compose up --build # Optionally add -d for deamon
```
You can then access the server locally at [localhost:8081](http://127.0.0.1:8081).


### Running without Docker
Alternatively, you can run the server locally without Docker. Create a virtual
environment, install the `covid_graphs` package an run the server.
```sh
python3.7 -m venv your/path/to/venv
source your/path/to/venv/bin/activate
pip install --upgrade setuptools
pip install -e . # With -e the package will automatically reload with any local changes.
covid_graphs.run_server --data-dir data/ --simulated-polynomial data/results-poly.pb --simulated-exponential data/results-exp.pb
```
Run `covid_graphs.run_server --help` for help on command parameters.


## Running standalone graphs

For quick development or data examination, running standalone graphs is useful.

```sh
covid_graphs.show_country_plot data Spain
covid_graphs.show_scatter_plot data/Slovakia.data results.pb
covid_graphs.show_heat_map results.pb
```
