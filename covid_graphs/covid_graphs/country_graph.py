import datetime
import math
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import click
import click_pathlib
from plotly.graph_objs import Figure, Layout, Scatter

from .country_report import CountryReport, create_report
from .formula import Curve, FittedFormula
from .predictions import CountryPrediction, PredictionEvent, prediction_db

EXTENSION_PERIOD = datetime.timedelta(days=7)


class GraphType(Enum):
    Linear = "linear"
    SemiLog = "semi-log"
    LogLog = "log-log"

    def __str__(self):
        return self.value


def _get_display_range(
    report: CountryReport, curves: List[Curve]
) -> Tuple[datetime.date, datetime.date]:
    start_date = min(curve.start_date for curve in curves)

    display_until = max(
        max(curve.display_at_least_until for curve in curves), report.dates[-1] + EXTENSION_PERIOD,
    )
    return start_date, display_until


class CountryGraph:
    """Constructs a graph for a given country"""

    def __init__(
        self, report: CountryReport, country_predictions: List[CountryPrediction],
    ):
        self.short_name = report.short_name
        self.long_name = report.long_name

        # TODO(lukas): Figure out better strategy for more predictions
        if len(country_predictions) >= 1:
            self.prediction_date = country_predictions[0].prediction_event.date

        self.curves = [
            prediction.formula.get_curve(country_report=report)
            for prediction in country_predictions
        ]

        min_start_date, self.display_until = _get_display_range(report, self.curves)
        min_start_date_idx = report.dates.index(min_start_date)
        # Crop country data to display.
        self.cropped_dates = report.dates[min_start_date_idx:]
        self.cropped_cumulative_active = report.cumulative_active[min_start_date_idx:]

    def create_country_figure(self, graph_type=GraphType.Linear):
        log_xaxis_date_since = self.cropped_dates[0] - datetime.timedelta(days=1)

        def adjust_xlabel(date: datetime.date):
            # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
            # x-axis isn't log-scale.
            if graph_type != GraphType.LogLog:
                return date
            else:
                return (date - log_xaxis_date_since).days

        colors = ["SteelBlue", "Purple", "Green", "Orange", "Gray"][: len(self.curves)]

        traces, shapes = [], []
        maximal_y = max(self.cropped_cumulative_active)
        for color, curve in zip(colors, self.curves):
            xs, ys = curve.generate_trace(self.display_until)
            idx_max = ys.argmax()
            maximal_y = max(maximal_y, ys.max())

            traces.append(
                Scatter(
                    x=list(map(adjust_xlabel, xs)),
                    y=ys,
                    text=xs,
                    mode="lines",
                    name=curve.label,
                    line={"width": 2, "color": color},
                )
            )
            # Add vertical dotted line marking the maximum
            shapes.append(
                dict(
                    type="line",
                    x0=adjust_xlabel(xs[idx_max]),
                    y0=1,
                    x1=adjust_xlabel(xs[idx_max]),
                    y1=ys.max(),
                    line=dict(width=2, dash="dash", color=color),
                )
            )

        traces.append(
            Scatter(
                x=list(map(adjust_xlabel, self.cropped_dates)),
                y=self.cropped_cumulative_active,
                mode="lines+markers",
                name="Active cases",
                marker=dict(size=8),
                line=dict(width=3, color="rgb(239, 85, 59)"),
            )
        )

        # Add green zone marking the data available at the prediction date.
        shapes.append(
            dict(
                type="rect",
                yref="paper",
                x0=adjust_xlabel(self.cropped_dates[0]),
                x1=adjust_xlabel(self.prediction_date),
                y0=0,
                y1=1,
                fillcolor="LightGreen",
                opacity=0.4,
                layer="below",
                line_width=0,
            )
        )

        layout = Layout(
            title=f"Active cases in {self.long_name}",
            xaxis=dict(autorange=True, fixedrange=True, showgrid=False,),
            yaxis=dict(
                tickformat=",.0f", gridcolor="LightGray", fixedrange=True, zerolinecolor="Gray",
            ),
            height=700,
            margin=dict(r=40),
            shapes=shapes,
            hovermode="x",
            font=dict(size=18),
            legend=dict(x=0.01, y=0.99, borderwidth=1),
            plot_bgcolor="White",
        )

        # Note: We silently assume `self.cropped_cumulative_active` does not contain zeros.
        self.log_yrange = [
            math.log10(max(1, self.cropped_cumulative_active.min())) - 0.3,
            math.log10(maximal_y) + 0.3,
        ]
        self.log_title = f"Days [since {log_xaxis_date_since.strftime('%b %d, %Y')}]"
        self.date_title = f"Date [starting from {self.cropped_dates[0].strftime('%b %d, %Y')}]"

        self.figure = Figure(data=traces, layout=layout)
        self.update_graph_type(graph_type)
        return self.figure

    def update_graph_type(self, graph_type: GraphType):
        if graph_type == GraphType.Linear:
            self.figure.update_xaxes(type="date", title=self.date_title)
            self.figure.update_yaxes(type="linear", autorange=True)
        elif graph_type == GraphType.SemiLog:
            self.figure.update_xaxes(type="date", title=self.date_title)
            self.figure.update_yaxes(type="log", autorange=False, range=self.log_yrange)
        elif graph_type == GraphType.LogLog:
            self.figure.update_xaxes(type="log", title=self.log_title)
            self.figure.update_yaxes(type="log", autorange=False, range=self.log_yrange)
        return self.figure


@click.command(help="COVID-19 country growth visualization")
@click.argument(
    "data_dir", required=True, type=click_pathlib.Path(exists=True),
)
@click.argument(
    "country_name", required=True, type=str,
)
def show_country_plot(data_dir: Path, country_name: str):
    country_predictions = prediction_db.predictions_for_country(country=country_name)
    country_report = create_report(data_dir / f"{country_name}.data", short_name=country_name)

    for until_date in [
        country_report.dates[-12],
        country_report.dates[-7],
        country_report.dates[-1],
    ]:
        country_predictions.append(
            CountryPrediction(
                prediction_event=PredictionEvent(
                    name=f"daily_fit_{until_date.strftime('%Y_%m_%d')}", date=until_date
                ),
                country=country_report.short_name,
                formula=FittedFormula(until_date=until_date),
            ),
        )

    country_graph = CountryGraph(report=country_report, country_predictions=country_predictions)
    country_graph.create_country_figure().show()
