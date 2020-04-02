#!/usr/bin/env python3
from plotly import offline
from itertools import chain
import argparse
import itertools
import numpy as np
import plotly.graph_objs as go
import yaml
from yaml import CLoader as Loader


parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
parser.add_argument('data', metavar='data', type=str, help=f"YAML file with data")
parser.add_argument('simulated', metavar='simulated', type=str, help=f"YAML file with simulation results")
args = parser.parse_args()


prefix_length = 3

with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        positive = [0] * (prefix_length + 1) + [point['positive'] for point in data]
        date_list = ['2020-03-01'] * (prefix_length + 1) + [point['date'] for point in data]
    except yaml.YAMLError as exc:
        raise exc


with open(args.simulated, 'r') as stream:
    try:
        data = yaml.load(stream, Loader=Loader)
        for group in data:
            if group["params"]["b0"] == 168 and group["params"]["prefix_length"] == prefix_length:
                daily_positive = [result["daily_positive"] for result in group["results"]]
                daily_infected = [list(itertools.accumulate(result["daily_infected"])) for result in group["results"]]
                days = [range(len(result["daily_positive"])) for result in group["results"]]

                daily_positive, daily_infected, days = map(lambda v: list(chain.from_iterable(v)), [daily_positive, daily_infected, days])

    except yaml.YAMLError as exc:
        raise exc


layout = go.Layout(
    xaxis=dict(
        autorange=True,
        title='Days'
    ),
    yaxis=dict(
        autorange=True,
        title='COVID-19 cases'
    ),
    hovermode='x',
    font={'size': 20}
)
figure = go.Figure(layout=layout)
figure.add_trace(
    go.Scatter(
        x=days,
        y=daily_positive,
        text=date_list,
        mode='markers',
        name="Simulated positive cases",
        line={'width': 3},
        marker=dict(size=10, line=dict(width=1), opacity=0.5)
    )
)

figure.add_trace(
    go.Scatter(
        x=list(range(len(positive))),
        y=positive,
        text=date_list,
        mode='lines',
        name=r'Real data',
    )
)

# offline.plot(figure, filename='graph.html')
figure.show()
