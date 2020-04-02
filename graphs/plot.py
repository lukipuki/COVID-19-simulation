#!/usr/bin/env python3
from plotly import offline
from datetime import datetime, timedelta
import argparse
import itertools
import numpy as np
import plotly.graph_objs as go
import sys
import yaml


parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
parser.add_argument('data', metavar='data', type=str, help=f"YAML file with data")
args = parser.parse_args()


with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        positive = [point['positive'] for point in data]
        date_list = [point['date'] for point in data]
    except yaml.YAMLError as exc:
        raise exc


prefix_length = 9
accumulated = list(itertools.accumulate(positive))[prefix_length:]
date_list = date_list[prefix_length:]

x = np.arange(1, len(accumulated) + 10)
y_power_law = 10 * x ** 1.21

# To add exponential decay, do something like this instead:
# x = np.arange(1, len(accumulated) + 50)
# y_power_law = (x ** 6.23) * np.exp(-x / 8.5) * 10**(-5)


layout = go.Layout(
    xaxis=dict(
        type='log',
        autorange=True,
        title=r'$\text{Days since the 10}^\mathrm{th}\text{ case}$ '
    ),
    yaxis=dict(
        type='log',
        autorange=True,
        title='COVID-19 cases'
    ),
    hovermode='x',
    font={'size': 20}
)
figure = go.Figure(layout=layout)
figure.add_trace(
    go.Scatter(
        x=x,
        y=accumulated,
        text=date_list,
        mode='lines+markers',
        name="Cases in Slovakia",
        line={'width': 3},
        marker={'size': 8}
    )
)

figure.add_trace(
    go.Scatter(
        x=x,
        y=y_power_law,
        text=date_list,
        mode='lines',
        # name=r'$\text{Power law fit: } t^{6.23} / 1.125^t \cdot 0.000019$',
        name=r'$\text{Power law fit: } 10 \cdot t^{1.2}$',
        line={'dash': 'dash', 'width': 2},
    )
)

# offline.plot(figure, filename='graph.html')
figure.show()
