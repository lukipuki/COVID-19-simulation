import click
import click_pathlib
from flask import Flask, render_template, redirect, url_for
from pathlib import Path

from covid_graphs.country_graph import CountryGraph, GraphType
from covid_graphs.heat_map import HeatMap


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

    covid19_normal_app = CountryGraph.create_dashboard(data_dir, server, GraphType.Normal)
    covid19_semilog_app = CountryGraph.create_dashboard(data_dir, server, GraphType.SemiLog)
    covid19_loglog_app = CountryGraph.create_dashboard(data_dir, server, GraphType.LogLog)
    covid19_heatmap_app = HeatMap(simulated_polynomial).create_app(server)
    covid19_heatmap_exponential_app = HeatMap(simulated_exponential).create_app(server)

    @server.route("/")
    def home():
        return render_template("index.html")

    @server.route("/covid19/")
    def covid19_redirect():
        return redirect(url_for("covid19_normal"))

    @server.route("/covid19/normal")
    def covid19_normal():
        return covid19_normal_app.index()

    @server.route("/covid19/semilog")
    def covid19_semilog():
        return covid19_semilog_app.index()

    @server.route("/covid19/loglog")
    def covid19_loglog():
        return covid19_loglog_app.index()

    @server.route("/covid19/heatmap/polynomial")
    def covid19_heatmap_polynomial():
        return covid19_heatmap_app.index()

    @server.route("/covid19/heatmap/exponential")
    def covid19_heatmap_exponential():
        return covid19_heatmap_exponential_app.index()

    server.run(host="0.0.0.0", port=8081, debug=True, extra_files=data_dir.glob("*.data"))
