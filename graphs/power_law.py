#!/usr/bin/env python3
from plotly import offline
from datetime import datetime, timedelta
import argparse
import itertools
import numpy as np
import plotly.graph_objs as go
import sys
import yaml
from collections import namedtuple


Country = namedtuple('Country', ['name', 'fit', 'fit_description'])

parser = argparse.ArgumentParser(description='COVID-19 power law visualization')
parser.add_argument('data',
                    metavar='data',
                    type=str,
                    help=f"YAML file with data")
args = parser.parse_args()

with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        # active = [point['positive'] - point['recovered'] - point['dead'] for point in data]
        active = [point['positive'] for point in data]
        # dead = [point['dead'] for point in data]
        # recovered = [point['recovered'] for point in data]
        date_list = [point['date'] for point in data]
    except yaml.YAMLError as exc:
        raise exc

cumulative_active = list(filter(lambda x: x >= 10, itertools.accumulate(active)))
date_list = date_list[len(active) - len(cumulative_active):]
x = np.arange(1, len(cumulative_active) + 10)


countries = [Country('Slovakia', 10 * x ** 1.21, r'$\text{Fitted curve: } 10 \cdot t^{1.2}$'),
             Country('Italy', 0.48 * x ** 3.35, r'$\text{Fitted curve: } 0.5382 \cdot t^{3.37}$')]
ctr = countries[0]

y_power_law = ctr.fit

# To add exponential decay, do something like this instead:
# x = np.arange(1, len(cumulative_active) + 50)
# y_power_law = (x ** 6.23) * np.exp(-x / 8.5) * 10**(-5)

layout = go.Layout(
    title=f"Active cases in {ctr.name}",
    xaxis=dict(
        type='log',
        autorange=True,
        title=r'$\text{Days since the 10}^\mathrm{th}\text{ case}$'
    ),
    yaxis=dict(type='log',
               autorange=True,
               title='COVID-19 active cases'),
    hovermode='x',
    font={'size': 20})
figure = go.Figure(layout=layout)
figure.add_trace(
    go.Scatter(x=x,
               y=cumulative_active,
               text=date_list,
               mode='lines+markers',
               name=f"Active cases",
               line={'width': 3},
               marker={'size': 8}))

figure.add_trace(
    go.Scatter(
        x=x,
        y=y_power_law,
        text=date_list,
        mode='lines',
        name=ctr.fit_description,
        line={
            'dash': 'dash',
            'width': 3
        },
    ))

# offline.plot(figure, filename='graph.html')
figure.show()
