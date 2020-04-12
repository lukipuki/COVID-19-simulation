# Graphs and visualizations related to COVID-19

## Running the whole server

In the root directory of the repository, run `docker-compose`.
```sh
docker-compose up --build # Optionally add -d for deamon
```

Alternatively, you can run the server locally without Docker.
```sh
./graphs/server.py data build/results-poly.pb build/results-exp.pb
```


## Running standalone graphs

For quick development or data examination, running standalone graphs is useful. We're assuming that the programs are run from the root of the repository.

```sh
./graphs/country.py data Spain
./graphs/scatter_plot.py data/Slovakia.data build/results.pb
./graphs/heat_map.py build/results.pb
```
