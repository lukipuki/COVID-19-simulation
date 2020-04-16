import click
import click_pathlib
from dash.dash import Dash
from flask import Flask, render_template, redirect, url_for
import itertools
import logging
from pathlib import Path

import os
import signal
from time import sleep
from multiprocessing import Process
import inotify.adapters

from covid_graphs.country_graph import GraphType
from covid_graphs.heat_map import HeatMap
from covid_graphs import predictions

from . import country_dashboard

CURRENT_DIR = Path(__file__).parent


@click.command(help="COVID-19 web server")
@click.option(
    "-d",
    "--data-dir",
    required=True,
    type=click_pathlib.Path(exists=True),
    help="Directory with country proto files",
)
@click.option(
    "-p",
    "--simulated-polynomial",
    required=True,
    type=click_pathlib.Path(exists=True),
    help="Proto file with simulation results of polynomial growth",
)
@click.option(
    "-e",
    "--simulated-exponential",
    required=True,
    type=click_pathlib.Path(exists=True),
    help="Proto file with simulation results of exponential growth",
)
def run_server(data_dir: Path, simulated_polynomial: Path, simulated_exponential: Path) -> None:
    """Creates and runs a flask server."""
    server = Flask(__name__, template_folder=CURRENT_DIR)

    _create_prediction_apps(server=server, data_dir=data_dir)
    _create_simulation_apps(server, simulated_polynomial, simulated_exponential)

    @server.route("/")
    def home():
        return render_template("index.html")

    @server.route("/covid19/normal")
    def covid19_redirect():
        return redirect(url_for("covid19_predictions", event="apr12", graph_type="normal"))

    server.run(host="0.0.0.0", port=8081, debug=True, extra_files=data_dir.glob("*.data"))


def _create_prediction_apps(data_dir: Path, server: Flask):
    # Note: Event route strings might become part the PredictionEvent class.
    event_by_route = {
        "mar29": predictions.BK_20200329,
        "apr12": predictions.BK_20200412,
    }
    graph_type_by_route = {
        "normal": GraphType.Normal,
        "semilog": GraphType.SemiLog,
        "loglog": GraphType.LogLog,
    }
    route_pairs = itertools.product(event_by_route.keys(), graph_type_by_route.keys())

    prediction_apps = {
        (event_route, graph_type_route): country_dashboard.create_dashboard(
            data_dir=data_dir,
            server=server,
            prediction_event=event_by_route[event_route],
            graph_type=graph_type_by_route[graph_type_route],
        )
        for event_route, graph_type_route in route_pairs
    }

    @server.route("/covid19/predictions/<event>/<graph_type>")
    def covid19_predictions(event: str, graph_type: str):
        return prediction_apps[(event, graph_type)].index()


def _create_simulation_apps(
    server: Flask, simulated_polynomial: Path, simulated_exponential: Path
):
    covid19_heatmap_app = HeatMap(simulated_polynomial).create_app(server)
    covid19_heatmap_exponential_app = HeatMap(simulated_exponential).create_app(server)

    @server.route("/covid19/heatmap/polynomial")
    def covid19_heatmap_polynomial():
        return covid19_heatmap_app.index()

    @server.route("/covid19/heatmap/exponential")
    def covid19_heatmap_exponential():
        return covid19_heatmap_exponential_app.index()

    i = inotify.adapters.InotifyTree(str(data_dir))

    p = Process(target=server.run, kwargs=dict(host="0.0.0.0", port=8081))
    p.start()
    while (True):
        events = list(i.event_gen(yield_nones=False, timeout_s=1))
        if len(events) != 0:
            os.kill(p.pid, signal.SIGKILL)
            p.join()
            p = Process(target=server.run, kwargs=dict(host="0.0.0.0", port=8081))
            p.start()
        sleep(3)
