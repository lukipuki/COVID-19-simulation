#!/usr/bin/env python3
from collections import OrderedDict
from enum import Enum
from plotly.graph_objs import Figure, Layout, Heatmap
import argparse
import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import simulation_results_pb2


class GrowthType(Enum):
    Exponential = 'exponential'
    Polynomial = 'polynomial'

    def __str__(self):
        return self.value


class HeatMap():
    def __init__(self, simulation_proto):
        with open(simulation_proto, "rb") as f:
            read_simulation_results = simulation_results_pb2.SimulationResults()
            read_simulation_results.ParseFromString(f.read())

            self.best_errors = OrderedDict()
            self.growth_type = None
            for result in read_simulation_results.results:

                if self.growth_type is None:
                    if result.HasField("alpha"):
                        self.growth_type = GrowthType.Polynomial
                        self.param_name = "alpha"
                    else:
                        self.growth_type = GrowthType.Exponential
                        self.param_name = "gamma2"

                if self.growth_type == GrowthType.Polynomial:
                    self.param = result.alpha
                else:
                    self.param = result.gamma2

                errors_by_param = self.best_errors.setdefault(self.param, OrderedDict())
                errors = errors_by_param.setdefault(result.prefix_length, [])
                errors.append((result.b0, result.summary.error))

    def create_heatmap(self, param, gamma_dict):
        data = []
        for key, value in gamma_dict.items():
            value.sort()
            b0_set = [x[0] for x in value]
            data.append([math.log(x[1]) for x in value])

        layout = Layout(title=f'Logarithm of average error for {self.param_name} = {param}',
                        xaxis=dict(title='$b_0$'),
                        yaxis=dict(title='prefix length'),
                        height=700,
                        font={'size': 20})

        figure = Figure(layout=layout)
        figure.add_trace(
            Heatmap(z=data,
                    x=b0_set,
                    y=list(gamma_dict.keys()),
                    reversescale=True,
                    colorscale='Viridis',
                    hovertemplate='b0: %{x}<br>prefix_len: %{y}<br>'
                    'log(error): %{z}<extra></extra>'))

        return figure

    def create_app(self, server):
        app = dash.Dash(
            name=f'COVID-19 {self.growth_type} heat map',
            server=server,
            url_base_pathname=f"/covid19/heatmap/{self.growth_type}/",
            external_scripts=[
                'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
            ])
        app.title = 'Visualizations of a COVID-19 stochastic model, with {self.growth_type} growth'

        graphs = [
            dcc.Graph(id=f'{key}', figure=self.create_heatmap(key, value))
            for key, value in sorted(self.best_errors.items())
        ]

        body = [
            dcc.Markdown(f"""
                # Visualizations of a COVID-19 stochastic model, with {self.growth_type} growth
                Model is by Radoslav Harman. You can read the
                [description of the model](http://www.iam.fmph.uniba.sk/ospm/Harman/COR01.pdf).

                * Squares correspond to a combination of b<sub>0</sub> and prefix length.
                * Heat is the average error for these parameters, averaged over 200 simulations.
                  We show the logarithm of the error, since we want to emphasize differences
                  between small values.
            """,
                         dangerously_allow_html=True)
        ] + graphs
        app.layout = html.Div(body, style={'font-family': 'sans-serif'})
        return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
    parser.add_argument('simulated',
                        metavar='simulated',
                        type=str,
                        help=f"Protobuf file with simulation results")
    args = parser.parse_args()

    app = HeatMap(args.simulated).create_app(True)
    app.run_server(host="0.0.0.0", port=8080)
