#!/usr/bin/env python3
from plotly import offline
from plotly.graph_objs import Figure, Layout, Scatter
from datetime import datetime, timedelta
import argparse
import itertools
import numpy as np
import plotly.graph_objs as go
import sys
import yaml
from collections import namedtuple

Country = namedtuple('Country', ['name', 'formula', 'case_count'])
Formula = namedtuple('Formula', ['lambd', 'text'])

parser = argparse.ArgumentParser(description='COVID-19 country growth visualization')
parser.add_argument('data', metavar='data', type=str, help=f"YAML file with data")
parser.add_argument('country', metavar='country', type=str, help=f"Country")
args = parser.parse_args()


def TG_formula(TG, A):
    text = r'$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{6.23} / e^{t/_TG}$'
    text = text.replace("_A", f"{A}").replace("_TG", f"{TG}")
    return Formula(lambda t: (A / TG) * ((t / TG)**6.23) / np.exp(t / TG), text)


countries = [
    Country('Slovakia', Formula(lambda t: 8 * t**1.28, r'$8 \cdot t^{1.28}$'), 10),
    Country('Italy', TG_formula(7.8, 4417), 200),
    # Country('Italy', Formula(lambda t: 0.5382 * t**3.37, r'$0.5382 \cdot t^{3.37}$'), 200),
    Country('Spain', TG_formula(6.4, 3665), 200),
    Country('Germany', TG_formula(6.7, 3773), 200),
    Country('USA', TG_formula(10.2, 72329), 200),
    Country('UK', TG_formula(7.2, 2719), 200),
    Country('France', TG_formula(6.5, 1961), 200),
    Country('Iran', TG_formula(8.7, 2569), 200)
]
country = next(c for c in countries if c.name == args.country)

with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        active = [point['positive'] - point['recovered'] - point['dead'] for point in data]
        dead = [point['dead'] for point in data]
        recovered = [point['recovered'] for point in data]
        date_list = [point['date'] for point in data]
    except yaml.YAMLError as exc:
        raise exc

cumulative_active = list(filter(lambda x: x >= country.case_count, itertools.accumulate(active)))
date_list = date_list[len(active) - len(cumulative_active):]
x = np.arange(1, len(cumulative_active) * 2)
y = country.formula.lambd(x)

last_date = datetime.strptime(date_list[-1], '%Y-%m-%d')
date_list += [(last_date + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(1, 51)]

layout = Layout(title=f"Active cases in {country.name}",
                xaxis=dict(autorange=True,
                           title=r'$\text{Days since the 200}^\mathrm{th}\text{ case}$'),
                yaxis=dict(type='log', autorange=True, title='COVID-19 active cases'),
                hovermode='x',
                font={'size': 15},
                legend=dict(x=0.01, y=0.99, borderwidth=1))

figure = Figure(layout=layout)
figure.add_trace(
    Scatter(x=x,
            y=cumulative_active,
            mode='lines+markers',
            name=f"Active cases",
            line={'width': 3},
            marker={'size': 8}))

figure.add_trace(
    Scatter(
        x=x,
        y=y,
        text=date_list,
        mode='lines',
        name=country.formula.text,
        line={
            'dash': 'dash',
            'width': 3
        },
    ))

# offline.plot(figure, filename='graph.html')
figure.show()
