#!/usr/bin/env python3
from datetime import datetime
import argparse
import math
import yaml
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout
import plotly.graph_objects as go

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
        assert ("results" in group) or ("result_abbrev" in group)

        prefix_length = group["params"]["prefix_length"]
        b0 = group["params"]["b0"]
        gamma2 = group["params"]["gamma2"]

        if "result_abbrev" in group:
            error_sum = group["result_abbrev"]["error"]
        else:
            error_sum = sum(result["error"] for result in group["results"]) / len(group["results"])
        best_errors.setdefault(gamma2, {})[(b0, prefix_length)] = error_sum


def create_heatmap(gamma, gamma_dict):
    b0_set = set(i[0] for i in gamma_dict.keys())
    prefix_len_set = set(i[1] for i in gamma_dict.keys())
    min_b0, max_b0 = min(b0_set), max(b0_set)
    min_prefix_len, max_prefix_len = min(prefix_len_set), max(prefix_len_set)
    data, prefix_axis = [], []
    for prefix_len in range(min_prefix_len, max_prefix_len + 1):
        curr = []
        for b0 in range(min_b0, max_b0 + 1):
            if b0 not in b0_set:
                continue
            curr.append(gamma_dict.get((b0, prefix_len), 0))
        if len(curr) != 0:
            prefix_axis.append(prefix_len)
            data.append(curr)

    data = [[math.log(j) for j in i] for i in data]

    layout = Layout(
        title=f"Logarithm of error average of particular (b0, prefix_length) combination",
        xaxis=dict(title=r'b0'),
        yaxis=dict(title=r'prefix_length'))

    fig = go.Figure(layout=layout,
                    data=go.Heatmap(z=data,
                                    x=sorted(b0_set),
                                    y=sorted(prefix_len_set),
                                    reversescale=True,
                                    colorscale='Viridis'))
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
    dcc.Graph(id=f'{item[0]}', figure=create_heatmap(item[0], item[1]))
    for item in best_errors.items()
]

app.layout = html.Div(children=[
    html.H1(children='Visualizations of a COVID-19 stochastic model by Radoslav Harman'),
    html.Ul([
        html.Li('Individual squares correspond to combination of b0 and prefix_len.'),
        html.Li('Heat is the total amount of error for these parameters')
    ])
] + graphs,
                      style={'font-family': 'sans-serif'})

app.run_server(host="0.0.0.0", port=8080)
