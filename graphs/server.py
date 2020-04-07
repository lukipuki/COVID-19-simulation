#!/usr/bin/env python3
from country import CountryReport, GraphType
from flask import Flask, render_template
import argparse


parser = argparse.ArgumentParser(description='COVID-19 web server')
parser.add_argument('data_dir', metavar='data_dir', type=str, help=f"Directory with YAML files")
args = parser.parse_args()


server = Flask(__name__, template_folder='.')

covid19_normal_app = CountryReport.create_dashboard(args.data_dir, server, GraphType.Normal)
covid19_semilog_app = CountryReport.create_dashboard(args.data_dir, server, GraphType.SemiLog)
covid19_loglog_app = CountryReport.create_dashboard(args.data_dir, server, GraphType.LogLog)


@server.route("/")
def home():
    return render_template('index.html')


@server.route("/covid19/normal")
def covid19_normal():
    return covid19_normal_app.index()


@server.route("/covid19/semilog")
def covid19_semilog():
    return covid19_semilog_app.index()


@server.route("/covid19/loglog")
def covid19_loglog():
    return covid19_loglog_app.index()


server.run(host="0.0.0.0", port=8080)
