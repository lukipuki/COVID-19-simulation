import datetime
import math
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import click
import click_pathlib
from plotly.graph_objs import Figure, Layout, Scatter

from .country_report import CountryReport, create_report
from .formula import TraceGenerator
from .prediction_generator import get_fitted_predictions
from .predictions import BK_20200329, BK_20200411, CountryPrediction, prediction_db

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
            self.prediction_last_data_date = max(
                country_prediction.prediction_event.last_data_date
                for country_prediction in country_predictions
            )

        # We create traces in three steps:
        # 1. A formula is first shifted to the appropriate date on the graph, creating a
        #    trace generator.
        # 2. The trace generators are used to calculate the last date of the graph, since each trace
        #    generator stores the minimal display length of its trace.
        # 3. Once we know the date range of the graph, we can plot the formulas, creating traces.
        trace_generator_by_event = {
            prediction.prediction_event: prediction.formula.get_trace_generator(
                country_report=report
            )
            for prediction in country_predictions
        }
        start_date, display_until = _get_display_range(
            report, list(trace_generator_by_event.values())
        )
        self.trace_by_event = {
            event: trace_generator.generate_trace(display_until)
            for event, trace_generator in trace_generator_by_event.items()
        }

        start_date_idx = report.dates.index(start_date)
        # Crop country data to display.
        self.cropped_dates = report.dates[start_date_idx:]
        self.cropped_cumulative_active = report.cumulative_active[start_date_idx:]
        self.log_xaxis_date_since = self.cropped_dates[0] - datetime.timedelta(days=1)
        self.log_title = f"Days [since {self.log_xaxis_date_since.strftime('%b %d, %Y')}]"
        self.date_title = "Date"

        max_value = max(
            max(self.cropped_cumulative_active),
            max(trace.max_value for trace in self.trace_by_event.values()),
        )
        self.log_yrange = [
            math.log10(max(1, self.cropped_cumulative_active.min())) - 0.3,
            math.log10(max_value) + 0.3,
        ]

    def create_country_figure(
        self, graph_type: GraphType = GraphType.Linear, show_green_zone: bool = False
    ):
        def adjust_xlabel(date: datetime.date):
            # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
            # x-axis isn't log-scale.
            if graph_type != GraphType.LogLog:
                return date
            else:
                return (date - self.log_xaxis_date_since).days

        # Matplotlib colors.
        color_by_event = {
            BK_20200329: "rgb(255, 123, 37)",
            BK_20200411: "rgb(0, 121, 177)",
        }
        extra_colors = [
            "rgba(43, 161, 59, 0.4)",
            "rgba(43, 161, 59, 0.7)",
            "rgba(43, 161, 59, 1.0)",
        ]
        for event in self.trace_by_event:
            if event not in color_by_event:
                color_by_event[event] = extra_colors.pop()

        traces, shapes = [], []

        for event, trace in self.trace_by_event.items():
            prediction_date_str = event.prediction_date.strftime("%b %d")
            data_until_idx = trace.xs.index(event.last_data_date)
            traces.append(
                Scatter(
                    x=list(map(adjust_xlabel, trace.xs[: data_until_idx + 1])),
                    y=trace.ys[: data_until_idx + 1],
                    text=trace.xs[: data_until_idx + 1],
                    mode="lines",
                    name=trace.label.replace("%PREDICTION_DATE%", prediction_date_str),
                    line=dict(width=2, color=color_by_event[event]),
                    legendgroup=event.name,
                )
            )
            traces.append(
                Scatter(
                    x=list(map(adjust_xlabel, trace.xs[data_until_idx:])),
                    y=trace.ys[data_until_idx:],
                    text=trace.xs[data_until_idx:],
                    mode="lines",
                    name=trace.label.replace("%PREDICTION_DATE%", prediction_date_str),
                    line=dict(width=2, dash="dash", color=color_by_event[event]),
                    legendgroup=event.name,
                    showlegend=False,
                )
            )
            # Maximum mark.
            traces.append(
                Scatter(
                    mode="markers",
                    x=[adjust_xlabel(trace.max_value_date), adjust_xlabel(trace.max_value_date)],
                    y=[1.0, trace.max_value],
                    name="Peak",
                    line=dict(color=color_by_event[event]),
                    marker=dict(size=15, symbol="star"),
                    legendgroup=event.name,
                    showlegend=False,
                )
            )
            # Last data date mark.
            data_until_y = trace.ys[data_until_idx]
            traces.append(
                Scatter(
                    x=[adjust_xlabel(event.last_data_date), adjust_xlabel(event.last_data_date)],
                    y=[1.0, data_until_y],
                    mode="markers",
                    name=f"Data cutoff",
                    marker=dict(size=15, symbol="circle", color=color_by_event[event]),
                    line=dict(width=3, color=color_by_event[event]),
                    legendgroup=event.name,
                    showlegend=False,
                    visible=not show_green_zone,
                )
            )

        if show_green_zone:
            shapes.append(
                dict(
                    type="rect",
                    yref="paper",
                    x0=adjust_xlabel(self.cropped_dates[0]),
                    x1=adjust_xlabel(self.prediction_last_data_date),
                    y0=0,
                    y1=1,
                    fillcolor="LightGreen",
                    opacity=0.4,
                    layer="below",
                    line_width=0,
                )
            )

        # Add cumulated active cases trace.
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


@click.command(help="COVID-19 country growth visualization")
@click.argument(
    "data_dir", required=True, type=click_pathlib.Path(exists=True),
)
@click.argument(
    "country_name", required=True, type=str,
)
def show_country_plot(data_dir: Path, country_name: str):
    country_predictions = prediction_db.predictions_for_country(country=country_name)
    country_report = create_report(data_dir / f"{country_name}.data")

    fitted_predictions = get_fitted_predictions(
        report=country_report, dates=[country_report.dates[-1], country_report.dates[-8]]
    )
    country_predictions.extend(fitted_predictions)
    country_graph = CountryGraph(report=country_report, country_predictions=country_predictions)
    country_graph.create_country_figure().show()
