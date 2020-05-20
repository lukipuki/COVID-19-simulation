import os
from pathlib import Path

import click
import click_pathlib
from flask import Flask, redirect, render_template, request, url_for

import requests
from covid_graphs.heat_map import create_heat_map_dashboard
from covid_graphs.simulation_report import GrowthType

from .country_dashboard import DashboardFactory, DashboardType

CURRENT_DIR = Path(__file__).parent


@click.command(help="COVID-19 web server")
@click.option(
    "-d",
    "--data-dir",
    required=True,
    type=click_pathlib.Path(exists=True),
    help="Directory with country and simulation proto files",
)
@click.option(
    "-p",
    "--prediction-dir",
    required=True,
    type=click_pathlib.Path(exists=True),
    help="Directory with prediction proto files",
)
def run_server(data_dir: Path, prediction_dir: Path) -> None:
    server = setup_server(data_dir, prediction_dir)
    server.run(host="0.0.0.0", port=8081)


GA_TRACKING_ID = os.environ["GA_TRACKING_ID"]


def track_pageview(path):
    data = {
        "v": "1",
        "tid": GA_TRACKING_ID,  # Tracking ID / Property ID.
        "cid": 47,
        "t": "pageview",
        "dp": f"/covid19/{path}",
        "dh": "graphs.lukipuki.sk",
        "ua": request.headers.get("User-Agent"),
    }

    response = requests.post("https://www.google-analytics.com/collect", data=data)
    response.raise_for_status()


def setup_server(data_dir: Path, prediction_dir: Path) -> Flask:
    server = Flask(__name__, template_folder=str(CURRENT_DIR))

    @server.route("/")
    def home():
        return render_template("index.html")

    @server.route("/covid19/normal/")
    def covid19_normal_redirect():
        return redirect(url_for("covid19_all_predictions"))

    @server.route("/covid19/predictions/")
    def covid19_predictions_redirect():
        return redirect(url_for("covid19_single_predictions"))

    _create_prediction_apps(server=server, data_dir=data_dir, prediction_dir=prediction_dir)
    _create_simulation_apps(server=server, data_dir=data_dir)

    return server


def _create_prediction_apps(server: Flask, data_dir: Path, prediction_dir: Path):
    dashboard_factory = DashboardFactory(data_dir, prediction_dir)
    single_prediction_app = dashboard_factory.create_dashboard(
        dashboard_type=DashboardType.SingleCountry, server=server
    )
    single_country_all_predictions_app = dashboard_factory.create_dashboard(
        dashboard_type=DashboardType.SingleCountryAllPredictions, server=server
    )
    all_predictions_app = dashboard_factory.create_dashboard(
        dashboard_type=DashboardType.AllCountries, server=server
    )

    @server.route("/covid19/predictions/single/")
    def covid19_single_predictions():
        track_pageview("predictions/single/")
        return single_prediction_app.index()

    @server.route("/covid19/predictions/daily/")
    def covid19_single_country_all_predictions():
        track_pageview("predictions/daily/")
        return single_country_all_predictions_app.index()

    @server.route("/covid19/predictions/all/")
    def covid19_all_predictions():
        track_pageview("predictions/all/")
        return all_predictions_app.index()


def _create_simulation_apps(server: Flask, data_dir: Path):
    simulated_polynomial = data_dir / "polynomial.sim"
    simulated_exponential = data_dir / "exponential.sim"
    covid19_heatmap_polynomial_app = create_heat_map_dashboard(
        simulated_polynomial, GrowthType.Polynomial, server
    )
    covid19_heatmap_exponential_app = create_heat_map_dashboard(
        simulated_exponential, GrowthType.Exponential, server
    )

    @server.route("/covid19/heatmap/polynomial/")
    def covid19_heatmap_polynomial():
        track_pageview("heatmap/polynomial/")
        return covid19_heatmap_polynomial_app.index()

    @server.route("/covid19/heatmap/exponential/")
    def covid19_heatmap_exponential():
        track_pageview("heatmap/exponential/")
        return covid19_heatmap_exponential_app.index()
