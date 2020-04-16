from collections import OrderedDict
from enum import Enum
from pathlib import Path
from plotly.graph_objs import Figure, Layout, Heatmap
import argparse
import click
import click_pathlib
import dash
import dash_core_components as dcc
import dash_html_components as html
import math

from .simulation_report import create_simulation_reports


class GrowthType(Enum):
    Exponential = 'exponential'
    Polynomial = 'polynomial'

    def __str__(self):
        return self.value


class HeatMap():
    def __init__(self, simulation_pb2_file: Path):
        reports = create_simulation_reports(simulation_pb2_file)

        self.best_errors = OrderedDict()
        self.growth_type = None
        for report in reports:
            if self.growth_type is None:
                self.growth_type = GrowthType.Polynomial if report.param_name == "alpha" \
                                   else GrowthType.Exponential
                self.param_name = report.param_name

            errors_by_param = self.best_errors.setdefault(report.param, OrderedDict())
            errors = errors_by_param.setdefault(report.prefix_length, [])
            errors.append((report.b0, report.error))

    def create_heatmap(self, param, prefix_dict):
        data = []
        for key, value in prefix_dict.items():
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
                    y=list(prefix_dict.keys()),
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


@click.command(help='COVID-19 simulation heat map for Slovakia')
@click.argument(
    "simulation_protofile",
    required=True,
    type=click_pathlib.Path(exists=True),
)
def show_heat_map(simulation_protofile):
    app = HeatMap(simulation_protofile).create_app(True)
    app.run_server(host="0.0.0.0", port=8080)
