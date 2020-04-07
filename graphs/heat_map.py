#!/usr/bin/env python3
from datetime import datetime
from enum import Enum
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout
import argparse
import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import plotly.graph_objects as go
import yaml


class GrowthType(Enum):
    Exponential = 'exponential'
    Polynomial = 'polynomial'

    def __str__(self):
        return self.value


class HeatMap():
    def __init__(self, simulation_yaml):
        with open(simulation_yaml, 'r') as stream:
            data = yaml.load(stream, Loader=Loader)

            self.best_errors = {}
            for group in data:
                assert ("results" in group) or ("result_abbrev" in group)

                self.prefix_length = group["params"]["prefix_length"]
                self.b0 = group["params"]["b0"]
                self.alpha = group["params"]["alpha"]

                if "result_abbrev" in group:
                    error_sum = group["result_abbrev"]["error"]
                else:
                    error_sum = sum(result["error"]
                                    for result in group["results"]) / len(group["results"])
                self.best_errors.setdefault(self.alpha,
                                            {})[(self.b0, self.prefix_length)] = error_sum

    def create_heatmap(self, gamma, gamma_dict):
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
            title=
            f"Logarithm of error average of particular (b0, prefix_length) combination for alpha = {gamma}",
            xaxis=dict(title='b0'),
            yaxis=go.layout.YAxis(title=go.layout.yaxis.Title(text='prefix_len', )))

        fig = go.Figure(
            layout=layout,
            data=go.Heatmap(
                z=data,
                x=sorted(b0_set),
                y=sorted(prefix_len_set),
                reversescale=True,
                colorscale='Viridis',
                hovertemplate=
                'b0: %{x}<br>prefix_len: %{y}<br>log(average_error): %{z}<extra></extra>'))
        fig.update_xaxes(side="top")
        return fig

    def create_app(self, url_base_pathname):
        app = dash.Dash(
            name=f'COVID-19 Heat map',
            url_base_pathname=url_base_pathname,
            external_scripts=[
                'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
            ])
        app.title = 'COVID-19 predictions heat_map of parameters'

        graphs = [
            dcc.Graph(id=f'{key}', figure=self.create_heatmap(key, value))
            for key, value in self.best_errors.items()
        ]

        app.layout = html.Div(children=[
            html.H1(children='Visualizations of a COVID-19 stochastic model by Radoslav Harman'),
            html.Ul([
                html.Li('Individual squares correspond to combination of b0 and prefix_len.'),
                html.Li('Heat is the total amount of error for these parameters')
            ])
        ] + graphs,
                              style={'font-family': 'sans-serif'})
        return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
    parser.add_argument('simulated',
                        metavar='simulated',
                        type=str,
                        help=f"YAML file with simulation results")
    args = parser.parse_args()

    app = HeatMap(args.simulated).create_app("/")
    app.run_server(host="0.0.0.0", port=8080)
