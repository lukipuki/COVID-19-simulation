#!/usr/bin/env python3
from datetime import datetime, timedelta
import argparse
import itertools
import numpy as np
import yaml
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout, Scatter
import plotly.express as px

import dash
import dash_core_components as dcc
import dash_html_components as html

parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
parser.add_argument('simulated',
                    metavar='simulated',
                    type=str,
                    help=f"YAML file with simulation results")
args = parser.parse_args()

with open(args.simulated, 'r') as stream:
    try:
        data = yaml.load(stream, Loader=Loader)
    except yaml.YAMLError as exc:
        raise exc

    best_errors = {}
    for group in data:
        if ("results" not in group) and ("result_abbrev" not in group):
            continue

        prefix_length = group["params"]["prefix_length"]
        b0 = group["params"]["b0"]
        gamma2 = group["params"]["gamma2"]

        if gamma2 not in best_errors:
            best_errors[gamma2] = {}

        if "result_abbrev" in group:
            error_sum = group["result_abbrev"]["error"]
        else:
            error_sum = sum(result["error"] for result in group["results"])
        best_errors[gamma2][(b0, prefix_length)] = error_sum


def create_heatmap(gamma, gamma_dict):
    min_b0, max_b0 = min(i[0] for i in gamma_dict.keys()), max(i[0] for i in gamma_dict.keys())
    min_prefix_len, max_prefix_len = min(i[1] for i in gamma_dict.keys()), max(
        i[1] for i in gamma_dict.keys())
    data, prefix_axis, b0_axis = [], [], []
    for prefix_len in range(min_prefix_len, max_prefix_len + 1):
        curr = []
        not_empty = False
        for b0 in range(min_b0, max_b0 + 1):
            if (b0, prefix_len) in gamma_dict:
                curr.append(gamma_dict[(b0, prefix_len)])
                not_empty = True
            else:
                curr.append(0)
        if not_empty:
            prefix_axis.append(prefix_len)
            data.append(curr)
    fig = px.imshow(data[::-1],
                    labels=dict(x="b0", y="Prefix length", color="Error sum"),
                    y=prefix_axis[::-1])
    fig.update_xaxes(side="top")
    return fig


app = dash.Dash(
    name=f'COVID-19 Heat map',
    url_base_pathname=f'/heatmap/',
    external_scripts=[
        'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
    ])
app.title = 'COVID-19 predictions heat_map of parameters'

graphs = [
    dcc.Graph(id=f'hehee', figure=create_heatmap(item[0], item[1])) for item in best_errors.items()
]

app.layout = html.Div(children=[
    html.H1(children='Visualizations of a COVID-19 stochastic model by Radoslav Harman'),
    html.Ul([
        html.Li('Individual squares correspond to combination of b0 and prefix_len.'),
        html.Li('Heat is the total amount of error for these parameters')
    ])
] + graphs)

app.run_server(host="0.0.0.0", port=8080)
