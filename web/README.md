# Graphs and visualizations related to COVID-19

## Running the whole server

In the root directory of the repository, run `docker-compose`.
```sh
docker-compose up --build # Optionally add -d for deamon
```
You can then access the server locally at [localhost:8081](http://127.0.0.1:8081).


### Running without Docker
Alternatively, you can run the server locally without Docker. Create a virtual
environment, install the `covid_graphs` package from `../covid_graphs` and install `covid_web`. You can use
a script provided in this directory:
```sh
cd ../covid_graphs
./create_dev_venv.sh
source .venv/bin/activate
cd ../covid_web
covid_web.run_server --data-dir ../data
```
Run `covid_web.run_server --help` for help on command parameters.


## Local development

This script creates a virtual environment with all development dependencies.
```sh
./create_dev_venv.sh
source .venv/bin/activate # Don't forget to activate the environment
```
