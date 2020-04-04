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
import os
from collections import namedtuple

Country = namedtuple('Country', ['name', 'formula', 'case_count'])
Formula = namedtuple('Formula', ['lambd', 'text'])

parser = argparse.ArgumentParser(description='COVID-19 country growth visualization')
parser.add_argument('data', metavar='data', type=str, help=f"Directory with YAML files")
parser.add_argument('country', metavar='country', type=str, help=f"Country or ALL")
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

class CountryData:
    def __init__(self, path, name, country_basic):
        self.name = name
        self.country_basic = country_basic
        self.path = os.path.join(path, 'data-' + name + '.yaml')
        with open(self.path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                self.active = [point['positive'] - point['recovered'] - point['dead'] for point in data]
                self.dead = [point['dead'] for point in data]
                self.recovered = [point['recovered'] for point in data]
                self.date_list = [point['date'] for point in data]
            except yaml.YAMLError as exc:
                raise exc

        self.cumulative_active = list(filter(lambda x: x >= self.country_basic.case_count, itertools.accumulate(self.active)))
        self.date_list = self.date_list[len(self.active) - len(self.cumulative_active):]
        self.x = np.arange(1, len(self.cumulative_active) * 2)
        self.y = self.country_basic.formula.lambd(self.x)

        self.last_date = datetime.strptime(self.date_list[-1], '%Y-%m-%d')
        self.date_list += [(self.last_date + timedelta(days=d)).strftime('%Y-%m-%d') for d in range(1, 51)]

    def create_country_figure(self):
    
        layout = Layout(title=f"Active cases in {self.country_basic.name}",
                        xaxis=dict(autorange=True,
                                title=r'$\text{Days since the 200}^\mathrm{th}\text{ case}$'),
                        yaxis=dict(type='log', autorange=True, title='COVID-19 active cases'),
                        hovermode='x',
                        font={'size': 15},
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        figure = Figure(layout=layout)
        figure.add_trace(
            Scatter(x=self.x,
                    y=self.cumulative_active,
                    mode='lines+markers',
                    name=f"Active cases",
                    line={'width': 3},
                    marker={'size': 8}))

        figure.add_trace(
            Scatter(
                x=self.x,
                y=self.y,
                text=self.date_list,
                mode='lines',
                name=self.country_basic.formula.text,
                line={
                    'dash': 'dash',
                    'width': 3
                },
            ))
        return figure

if args.country != "ALL":
    country = next(c for c in countries if c.name == args.country)
    country_data = CountryData(args.data, args.country, country)
    country_data.create_country_figure().show()
    # offline.plot(country_data.create_country_figure(), filename='graph.html')
    exit(0)

countries_data = [CountryData(args.data, country.name, country) for country in countries]

import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash(external_scripts = [
        'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
    ])

graphs = [dcc.Graph(id = country_data.name, figure = country_data.create_country_figure())
            for country_data in countries_data]

app.layout = html.Div(graphs)
app.run_server(port=8080)
