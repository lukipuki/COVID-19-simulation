import math
from enum import Enum
from pathlib import Path
from typing import List

import click
import click_pathlib
import numpy as np
from plotly.graph_objs import Figure, Layout, Scatter

from .country_report import CountryReport
from .formula import Curve
from .predictions import CountryPrediction, prediction_db


class GraphType(Enum):
    Normal = "normal"
    SemiLog = "semi-log"
    LogLog = "log-log"

    def __str__(self):
        return self.value


class CountryGraph:
    """Constructs a graph for a given country"""

    def __init__(
        self, report: CountryReport, country_predictions: List[CountryPrediction],
    ):
        # TODO(miskosz): We assume there is only one country.
        # This might change soon though if we want to have a country dropdown in one graph.
        self.short_name = country_predictions[0].country
        self.min_case_count = min(
            prediction.formula.min_case_count for prediction in country_predictions
        )

        # TODO(lukas): Figure out better strategy for more predictions
        if len(country_predictions) >= 1:
            self.prediction_date = country_predictions[0].prediction_event.date.strftime("%Y-%m-%d")

        self.long_name = report.long_name

        first_idx, last_idx, self.curves = Curve.create_curves(
            [prediction.formula for prediction in country_predictions],
            report.cumulative_active,
            report.dates[0],
        )
        self.cumulative_active = report.cumulative_active[first_idx:]
        self.date_list = report.dates_str[first_idx:]
        self.t = np.arange(len(self.cumulative_active)) + 1

    def create_country_figure(self, graph_type: GraphType):

        # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
        # aren't using logs.
        def pick_xaxis_labels(object):
            if graph_type == GraphType.Normal:
                return object.date_list
            else:
                return object.t

        colors = ["SteelBlue", "Purple", "Green"][: len(self.curves)]
        shapes = [
            # Add vertical dotted lines marking the maxima
            dict(
                type="line",
                x0=pick_xaxis_labels(curve)[curve.maximal_idx],
                y0=1,
                x1=pick_xaxis_labels(curve)[curve.maximal_idx],
                y1=curve.maximal_y,
                line=dict(width=2, dash="dash", color=color),
            )
            for color, curve in zip(colors, self.curves)
        ]
        try:
            prediction_date = self.date_list.index(self.prediction_date)
            # Add green zone marking the data available at the prediction date.
            shapes.append(
                dict(
                    type="rect",
                    yref="paper",
                    x0=pick_xaxis_labels(self)[0],
                    x1=pick_xaxis_labels(self)[prediction_date],
                    y0=0,
                    y1=1,
                    fillcolor="LightGreen",
                    opacity=0.4,
                    layer="below",
                    line_width=0,
                )
            )
        except ValueError:
            pass

        layout = Layout(
            title=f"Active cases in {self.long_name}",
            xaxis=dict(
                autorange=True,
                fixedrange=True,
                title=f"Day [starting at the {self.min_case_count}th case]",
                showgrid=False,
            ),
            yaxis=dict(
                tickformat=",.0f",
                gridcolor="LightGray",
                autorange=(graph_type == GraphType.Normal),
                fixedrange=True,
                zerolinecolor="Gray",
            ),
            height=700,
            margin=dict(r=40),
            shapes=shapes,
            hovermode="x",
            font=dict(size=18),
            legend=dict(x=0.01, y=0.99, borderwidth=1),
            plot_bgcolor="White",
        )
        if graph_type != GraphType.Normal:
            maximal_y = max(
                max(curve.maximal_y for curve in self.curves), max(self.cumulative_active)
            )
            layout.yaxis["range"] = [
                math.log10(self.cumulative_active.min()) - 0.3,
                math.log10(maximal_y) + 0.3,
            ]

        figure = Figure(layout=layout)
        for color, curve in zip(colors, self.curves):
            figure.add_trace(
                Scatter(
                    x=pick_xaxis_labels(curve),
                    y=curve.y,
                    text=curve.date_list,
                    mode="lines",
                    name=curve.text,
                    line={"width": 2, "color": color},
                )
            )

        figure.add_trace(
            Scatter(
                x=pick_xaxis_labels(self),
                y=self.cumulative_active,
                mode="lines+markers",
                name="Active cases",
                marker=dict(size=8),
                line=dict(width=3, color="rgb(239, 85, 59)"),
            )
        )

        if graph_type == GraphType.Normal:
            figure.update_yaxes(type="linear")
        elif graph_type == GraphType.SemiLog:
            figure.update_xaxes(type="linear")
            figure.update_yaxes(type="log")
        elif graph_type == GraphType.LogLog:
            figure.update_xaxes(type="log")
            figure.update_yaxes(type="log")
        return figure


@click.command(help="COVID-19 country growth visualization")
@click.argument(
    "data_dir", required=True, type=click_pathlib.Path(exists=True),
)
@click.argument(
    "country_name", required=True, type=str,
)
def show_country_plot(data_dir: Path, country_name: str):
    country_predictions = prediction_db.predictions_for_country(country=country_name)
    country_report = CountryReport(data_dir / f"{country_name}.data", short_name=country_name)
    country_graph = CountryGraph(report=country_report, country_predictions=country_predictions)
    country_graph.create_country_figure(GraphType.Normal).show()
