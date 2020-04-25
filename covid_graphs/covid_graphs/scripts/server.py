from multiprocessing import Process
from pathlib import Path
from time import sleep

import click
import click_pathlib
from flask import Flask, redirect, render_template, url_for

from covid_graphs.heat_map import create_heat_map_dashboard
from covid_graphs.simulation_report import GrowthType

from . import country_dashboard

CURRENT_DIR = Path(__file__).parent


platform_supports_inotify = False
try:
    from inotify import adapters, constants

    platform_supports_inotify = True
except:
    print("⚠️  inotify is not supported! Will run the server without reloading.")
    pass


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

    if platform_supports_inotify:
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
    else:
        _run_flask_server(server=server, data_dir=data_dir)


def _run_flask_server(server: Flask, data_dir: Path):
    _create_prediction_apps(server=server, data_dir=data_dir)
    _create_simulation_apps(server=server, data_dir=data_dir)
    server.run(host="0.0.0.0", port=8081)


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
