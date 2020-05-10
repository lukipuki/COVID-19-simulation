from pathlib import Path

import click
import click_pathlib
from flask import Flask, redirect, render_template, url_for

from covid_graphs.heat_map import create_heat_map_dashboard
from covid_graphs.simulation_report import GrowthType

from .country_dashboard import DashboardFactory, DashboardType
from .rest import Rest

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
    _create_rest(server=server, data_dir=data_dir, prediction_dir=prediction_dir)

    return server


def _create_rest(server: Flask, data_dir: Path, prediction_dir: Path):
    rest = Rest(data_dir=data_dir, prediction_dir=prediction_dir)

    @server.route("/covid19/rest/data/<country>")
    def covid19_country_data(country):
        return rest.get_country_data(country)

    @server.route("/covid19/rest/predictions/list")
    def covid19_available_predictions():
        return rest.get_available_predictions()

    @server.route("/covid19/rest/predictions/by_prediction/<prediction>")
    def covid19_get_predictions_by_name(prediction):
        return rest.get_predictions_by_name(prediction)

    @server.route("/covid19/rest/predictions/by_country/<country>")
    def covid19_get_predictions_by_country(country):
        return rest.get_predictions_by_country(country)

    @server.route("/covid19/rest/predictions/by_prediction/<prediction>/<country>")
    @server.route("/covid19/rest/predictions/by_country/<country>/<prediction>")
    def covid19_get_specific_prediction(prediction, country):
        return rest.get_specific_prediction(prediction, country)


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
        return single_prediction_app.index()

    @server.route("/covid19/predictions/daily/")
    def covid19_single_country_all_predictions():
        return single_country_all_predictions_app.index()

    @server.route("/covid19/predictions/all/")
    def covid19_all_predictions():
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
        return covid19_heatmap_polynomial_app.index()

    @server.route("/covid19/heatmap/exponential/")
    def covid19_heatmap_exponential():
        return covid19_heatmap_exponential_app.index()
