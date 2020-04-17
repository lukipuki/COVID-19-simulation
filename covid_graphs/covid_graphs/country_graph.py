from enum import Enum
from plotly.graph_objs import Figure, Layout, Scatter
import click
import click_pathlib
import numpy as np
from pathlib import Path
from typing import List

from .predictions import prediction_db, CountryPrediction
from .country_report import CountryReport
from .formula import Curve, XAxisType


class GraphType(Enum):
    Normal = 'normal'
    SemiLog = 'semi-log'
    LogLog = 'log-log'

    def __str__(self):
        return self.value


class CountryGraph:
    """Constructs a graph for a given country"""
    def __init__(
        self,
        data_dir: Path,
        country_predictions: List[CountryPrediction],
        graph_type: GraphType = GraphType.Normal,
    ):
        self.graph_type = graph_type

        # TODO(miskosz): We assume there is only one country.
        # This might change soon though if we want to have a country dropdown in one graph.
        country_name = country_predictions[0].country

        # TODO(lukas): Figure out better strategy for more predictions
        if len(country_predictions) >= 1:
            self.prediction_date = country_predictions[0].prediction_event.date.strftime("%Y-%m-%d")

        # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
        # aren't using logs.
        axis_type = XAxisType.Dated if graph_type == GraphType.Normal else XAxisType.Numbered

        report = CountryReport(country_data_file=data_dir / f'{country_name}.data')

        first_idx, last_idx, self.curves = Curve.create_curves(
            [prediction.formula for prediction in country_predictions],
            report.cumulative_active,
            report.dates[0],
            axis_type,
        )
        self.name = report.name
        self.min_case_count = min(prediction.formula.min_case_count
                                  for prediction in country_predictions)

        self.cumulative_active = report.cumulative_active[first_idx:].copy()
        self.date_list = report.dates_str[first_idx:]
        if axis_type == XAxisType.Dated:
            self.t = self.date_list
        else:
            self.t = np.arange(len(self.cumulative_active)) + 1

    def create_country_figure(self):
        shapes = [
            # Add vertical dotted lines marking the maxima
            dict(type="line",
                 yref="paper",
                 x0=curve.t[curve.maximal_idx],
                 y0=0,
                 x1=curve.t[curve.maximal_idx],
                 y1=1,
                 line=dict(width=2, dash='dot')) for curve in self.curves
        ]
        try:
            prediction_date = self.date_list.index(self.prediction_date)
            # Add green zone marking the data available at the prediction date.
            shapes.append(
                dict(type="rect",
                     yref="paper",
                     x0=self.t[0],
                     x1=self.t[prediction_date],
                     y0=0,
                     y1=1,
                     fillcolor="LightGreen",
                     opacity=0.5,
                     layer="below",
                     line_width=0))
        except ValueError:
            pass

        layout = Layout(title=f"Active cases in {self.name}",
                        xaxis=dict(
                            autorange=True,
                            title=f'Day [starting at the {self.min_case_count}th case]',
                        ),
                        yaxis=dict(autorange=True,
                                   title=f'COVID-19 active cases in {self.name}',
                                   tickformat='.0f'),
                        height=700,
                        shapes=shapes,
                        hovermode='x',
                        font=dict(size=20),
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        figure = Figure(layout=layout)
        colors = ['rgb(31, 119, 180)', '#bcbd22', 'violet'][:len(self.curves)]
        for color, curve in zip(colors, self.curves):
            figure.add_trace(
                Scatter(
                    x=curve.t,
                    y=curve.y,
                    text=curve.date_list,
                    mode='lines',
                    name=curve.text,
                    line={
                        'dash': 'dash',
                        'width': 2,
                        'color': color
                    },
                ))

        figure.add_trace(
            Scatter(x=self.t,
                    y=self.cumulative_active,
                    mode='lines+markers',
                    name="Active cases",
                    line={
                        'width': 3,
                        'color': 'rgb(239, 85, 59)',
                    },
                    marker={'size': 8}))

        if self.graph_type == GraphType.Normal:
            figure.update_yaxes(type="linear")
        elif self.graph_type == GraphType.SemiLog:
            figure.update_xaxes(type="linear")
            figure.update_yaxes(type="log")
        elif self.graph_type == GraphType.LogLog:
            figure.update_xaxes(type="log")
            figure.update_yaxes(type="log")
        return figure


@click.command(help='COVID-19 country growth visualization')
@click.argument(
    "data_dir",
    required=True,
    type=click_pathlib.Path(exists=True),
)
@click.argument(
    "country_name",
    required=True,
    type=str,
)
def show_country_plot(data_dir: Path, country_name: str):
    country_predictions = prediction_db.predictions_for_country(country=country_name)
    country_graph = CountryGraph(data_dir=data_dir,
                                 country_predictions=country_predictions,
                                 graph_type=GraphType.Normal)
    country_graph.create_country_figure().show()
