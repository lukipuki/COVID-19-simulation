from multiprocessing import Process
from pathlib import Path
from time import sleep

import click
import click_pathlib
from flask import Flask, redirect, render_template, url_for, send_from_directory, send_file
from inotify import adapters, constants

from covid_graphs.heat_map import create_heat_map_dashboard
from covid_graphs.simulation_report import GrowthType

from . import country_dashboard

CURRENT_DIR = Path(__file__).parent


@click.command(help="COVID-19 web server")
@click.option(
    "-d",
    "--data-dir",
    required=True,
    type=click_pathlib.Path(exists=True),
    help="Directory with country and simulation proto files",
)
def run_server(data_dir: Path) -> None:
    """Creates and runs a flask server."""
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

    i = adapters.InotifyTree(
        str(data_dir), mask=(constants.IN_MODIFY | constants.IN_DELETE | constants.IN_CREATE)
    )
    p = Process(target=_run_flask_server, kwargs=dict(server=server, data_dir=data_dir))
    p.start()
    while True:
        events = list(i.event_gen(yield_nones=False, timeout_s=1))
        if len(events) != 0:
            print("Data changed. Restarting server...")
            p.terminate()
            p.join()
            p = Process(target=_run_flask_server, kwargs=dict(server=server, data_dir=data_dir))
            p.start()
            print("Server restarted.")
        sleep(10)


def _run_flask_server(server: Flask, data_dir: Path):
    _create_prediction_apps(server=server, data_dir=data_dir)
    _create_simulation_apps(server=server, data_dir=data_dir)
    _create_prediction_rest(server=server, data_dir=data_dir)
    _create_graphs_app(server=server)
    server.run(host="0.0.0.0", port=8081)

def _create_prediction_rest(data_dir: Path, server: Flask):
    prediction_rest = country_dashboard.create_prediction_rest(
        data_dir=data_dir, server=server
    )
    
    @server.route("/covid19/predictions/list/")
    def covid19_available_predictions():
        return prediction_rest.get_available_predictions()
    
    @server.route("/covid19/predictions/data/<date>/<country>")
    def covid19_get_specific_prediction(date, country):
        return prediction_rest.get_specific_prediction(date, country)
    
def _create_graphs_app(server: Flask):
    #TODO (rejdi): It's better to use nginx for static files
    @server.route('/covid19/predictions/graphs/')
    def covid_19_graphs_index():
        return send_file('../../../web/build/index.html', add_etags=True)
    
    @server.route('/covid19/predictions/graphs/<path:filename>')
    def covid_19_graphs(filename):
        return send_from_directory('../../../web/build/', filename, add_etags=True)

def _create_prediction_apps(data_dir: Path, server: Flask):
    single_prediction_app = country_dashboard.create_single_country_dashboard(
        data_dir=data_dir, server=server
    )
    all_predictions_app = country_dashboard.create_all_countries_dashboard(
        data_dir=data_dir, server=server
    )

    @server.route("/covid19/predictions/single/")
    def covid19_single_predictions():
        return single_prediction_app.index()

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
