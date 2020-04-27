import datetime
import math
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import click
import click_pathlib
from plotly.graph_objs import Figure, Layout, Scatter

from .country_report import CountryReport, create_report
from .formula import FittedFormula, TraceGenerator
from .predictions import CountryPrediction, PredictionEvent, prediction_db

EXTENSION_PERIOD = datetime.timedelta(days=7)


class GraphType(Enum):
    Linear = "linear"
    SemiLog = "semi-log"
    LogLog = "log-log"

    def __str__(self):
        return self.value


def _get_display_range(
    report: CountryReport, trace_generators: List[TraceGenerator]
) -> Tuple[datetime.date, datetime.date]:
    start_date = min(trace_generator.start_date for trace_generator in trace_generators)

    display_until = max(
        max(trace_generator.display_at_least_until for trace_generator in trace_generators),
        report.dates[-1] + EXTENSION_PERIOD,
    )
    return start_date, display_until


class CountryGraph:
    """Constructs a graph for a given country"""

    def __init__(
        self, report: CountryReport, country_predictions: List[CountryPrediction],
    ):
        self.short_name = report.short_name
        self.long_name = report.long_name

        if len(country_predictions) >= 1:
            self.prediction_date = max(
                country_prediction.prediction_event.date
                for country_prediction in country_predictions
            )

        # We create traces in three steps:
        # 1. A formula is first shifted to the appropriate date on the graph, creating a
        #    trace generator.
        # 2. The trace generators are used to calculate the last date of the graph, since each trace
        #    generator stores the minimal display length of its trace.
        # 3. Once we know the date range of the graph, we can plot the formulas, creating traces.
        trace_generators = [
            prediction.formula.get_trace_generator(country_report=report)
            for prediction in country_predictions
        ]
        start_date, display_until = _get_display_range(report, trace_generators)

        self.traces = [
            trace_generator.generate_trace(display_until) for trace_generator in trace_generators
        ]

        start_date_idx = report.dates.index(start_date)
        # Crop country data to display.
        self.cropped_dates = report.dates[start_date_idx:]
        self.cropped_cumulative_active = report.cumulative_active[start_date_idx:]
        self.log_xaxis_date_since = self.cropped_dates[0] - datetime.timedelta(days=1)
        self.log_title = f"Days [since {self.log_xaxis_date_since.strftime('%b %d, %Y')}]"
        self.date_title = "Date"

        max_value = max(
            max(self.cropped_cumulative_active), max(trace.max_value for trace in self.traces)
        )
        self.log_yrange = [
            math.log10(max(1, self.cropped_cumulative_active.min())) - 0.3,
            math.log10(max_value) + 0.3,
        ]

    def create_country_figure(self, graph_type=GraphType.Linear):
        def adjust_xlabel(date: datetime.date):
            # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
            # x-axis isn't log-scale.
            if graph_type != GraphType.LogLog:
                return date
            else:
                return (date - self.log_xaxis_date_since).days

        colors = ["SteelBlue", "Purple", "Green", "Orange", "Gray"][: len(self.traces)]

        traces, shapes = [], []
        for color, trace in zip(colors, self.traces):
            traces.append(
                Scatter(
                    x=list(map(adjust_xlabel, trace.xs)),
                    y=trace.ys,
                    text=trace.xs,
                    mode="lines",
                    name=trace.label,
                    line={"width": 2, "color": color},
                )
            )
            # Add vertical dotted line marking the maximum
            shapes.append(
                dict(
                    type="line",
                    x0=adjust_xlabel(trace.max_value_date),
                    y0=1,
                    x1=adjust_xlabel(trace.max_value_date),
                    y1=trace.max_value,
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

        self.figure = Figure(data=traces, layout=layout)
        return self.update_graph_type(graph_type)

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


def _get_fitted_predictions(report: CountryReport) -> List[CountryPrediction]:
    return [
        CountryPrediction(
            prediction_event=PredictionEvent(
                name=f"daily_fit_{until_date.strftime('%Y_%m_%d')}", date=until_date
            ),
            country=report.short_name,
            formula=FittedFormula(until_date=until_date),
        )
        for until_date in [report.dates[-13], report.dates[-7], report.dates[-1]]
    ]


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
    country_predictions.extend(_get_fitted_predictions(report=country_report))
    country_graph = CountryGraph(report=country_report, country_predictions=country_predictions)
    country_graph.create_country_figure().show()
