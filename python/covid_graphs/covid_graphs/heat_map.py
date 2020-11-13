import math
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import click
import click_pathlib
import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask
from plotly.graph_objs import Figure, Heatmap, Layout

from .simulation_report import GrowthType, SimulationReport, create_simulation_reports


@dataclass
class SimulationTable:
    growth_type: GrowthType
    param_name: str
    param: float
    # TODO(lukas): Consider using pandas DataFrame here, this is actually a table.
    errors: Dict[int, List[Tuple[int, float]]]


def group_data(simulation_reports: List[SimulationReport]) -> Dict[float, SimulationTable]:
    """Groups data in SimulationReport's by the value of alpha or gamma2"""
    heat_maps: OrderedDict[float, SimulationTable] = OrderedDict()
    for report in simulation_reports:
        if report.param not in heat_maps:
            param_name = "alpha" if report.growth_type == GrowthType.Polynomial else "gamma2"
            simulation_table = heat_maps.setdefault(
                report.param,
                SimulationTable(report.growth_type, param_name, report.param, OrderedDict()),
            )
        else:
            simulation_table = heat_maps[report.param]
        errors_by_prefix = simulation_table.errors.setdefault(report.prefix_length, [])
        errors_by_prefix.append((report.b0, report.error))

    return heat_maps


def create_heat_map(simulation_table: SimulationTable):
    data = []
    for errors in simulation_table.errors.values():
        errors.sort()
        b0_set = [b0 for b0, _ in errors]
        data.append([math.log(error) for _, error in errors])

    layout = Layout(
        title=f"Logarithm of average error for {simulation_table.param_name} = "
        f"{simulation_table.param}",
        xaxis=dict(title="$b_0$"),
        yaxis=dict(title="prefix length"),
        height=700,
        font={"size": 20},
    )

    figure = Figure(layout=layout)
    figure.add_trace(
        Heatmap(
            z=data,
            x=b0_set,
            y=list(simulation_table.errors.keys()),
            reversescale=True,
            colorscale="Viridis",
            hovertemplate="b0: %{x}<br>prefix_len: %{y}<br>" "log(error): %{z}<extra></extra>",
        )
    )

    return figure


def create_heat_map_dashboard(simulation_pb2_file: Path, growth_type: GrowthType, server: Flask):
    app = dash.Dash(
        name=f"COVID-19 {growth_type} heat map",
        server=server,
        url_base_pathname=f"/covid19/heatmap/{growth_type}/",
        external_scripts=[
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
        ],
    )
    try:
        simulation_reports = create_simulation_reports(simulation_pb2_file)
    except (ValueError, FileNotFoundError) as e:
        print(e)
        app.layout = html.Div(
            dcc.Markdown(
                f"""
            # Error in parsing simulation proto file

            The file `{simulation_pb2_file}` failed to parse.
            Please contact the site administrator.
            """
            ),
            style={"font-family": "sans-serif"},
        )
        return app

    growth_type = next(iter(simulation_reports)).growth_type
    app.title = "Heat map of a COVID-19 stochastic model, with {growth_type} growth"

    simulation_tables = group_data(simulation_reports)
    graphs = [
        dcc.Graph(id=f"{simulation_table.param}", figure=create_heat_map(simulation_table))
        for simulation_table in simulation_tables.values()
    ]

    body = (
        [
            dcc.Markdown(
                f"""
            # Visualizations of a COVID-19 stochastic model, with {growth_type} growth
            Model is by Radoslav Harman. You can read the
            [description of the model](http://www.iam.fmph.uniba.sk/ospm/Harman/COR01.pdf).

            * Squares correspond to a combination of b<sub>0</sub> and prefix length.
            * Heat is the average error for these parameters, averaged over 200 simulations.
              We show the logarithm of the error, since we want to emphasize differences
              between small values.
        """,
                dangerously_allow_html=True,
            )
        ]
        + graphs
    )
    app.layout = html.Div(body, style={"font-family": "sans-serif"})
    return app


@click.command(help="COVID-19 simulation heat map for Slovakia")
@click.argument(
    "simulation_protofile",
    required=True,
    type=click_pathlib.Path(exists=True),
)
def show_heat_map(simulation_protofile):
    # TODO(lukas): This can be exponential growth, but if the file fails to parse there's no way of
    # knowing it.
    app = create_heat_map_dashboard(simulation_protofile, GrowthType.Polynomial, True)
    app.run_server(host="0.0.0.0", port=8080)
