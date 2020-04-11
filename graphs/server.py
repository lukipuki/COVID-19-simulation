#!/usr/bin/env python3
from country import CountryReport, GraphType
from heat_map import HeatMap, GrowthType
from flask import Flask, render_template, redirect, url_for
import argparse

parser = argparse.ArgumentParser(description='COVID-19 web server')
parser.add_argument('data_dir',
                    metavar='data_dir',
                    type=str,
                    help=f"Directory with country proto files")
parser.add_argument('simulated_polynomial',
                    metavar='simulated_polynomial',
                    type=str,
                    help=f"Proto file with simulation results of polynomial growth")
parser.add_argument('simulated_exponential',
                    metavar='simulated_exponential',
                    type=str,
                    help=f"Proto file with simulation results of exponential growth")
args = parser.parse_args()

server = Flask(__name__, template_folder='.')

covid19_normal_app = CountryReport.create_dashboard(args.data_dir, server, GraphType.Normal)
covid19_semilog_app = CountryReport.create_dashboard(args.data_dir, server, GraphType.SemiLog)
covid19_loglog_app = CountryReport.create_dashboard(args.data_dir, server, GraphType.LogLog)
covid19_heatmap_app = HeatMap(args.simulated_polynomial).create_app(server)
covid19_heatmap_exponential_app = HeatMap(args.simulated_exponential).create_app(server)


@server.route("/")
def home():
    return render_template('index.html')


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


server.run(host="0.0.0.0", port=8080)
