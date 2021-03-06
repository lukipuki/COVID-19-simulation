import datetime
import math
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Tuple

import click
import click_pathlib
from plotly.graph_objs import Figure, Layout, Scatter

from . import predictions
from .country_report import CountryReport, create_report
from .formula import FittedFormula, TraceGenerator
from .predictions import BK_20200329, BK_20200411, CountryPrediction, PredictionEvent

# Extend the predictions at least by 1/5th of the length of active cases.
EXTENSION_RATIO = 0.2


class GraphType(Enum):
    Slider = "slider"
    SinglePrediction = "single"
    MultiPredictions = "multi"
    BayesPredictions = "bayes"

    def __str__(self):
        return self.value


class GraphAxisType(Enum):
    Linear = "linear"
    SemiLog = "semi-log"
    LogLog = "log-log"

    def __str__(self):
        return self.value


def _get_display_range(
    report: CountryReport, trace_generators: Iterable[TraceGenerator]
) -> Tuple[datetime.date, datetime.date]:
    start_date = min(
        [trace_generator.start_date for trace_generator in trace_generators] + [report.dates[0]]
    )

    last_report_date = report.dates[-1]
    report_length = last_report_date - start_date + datetime.timedelta(days=1)
    report_extension = report_length * EXTENSION_RATIO

    display_until = max(
        [trace_generator.display_at_least_until for trace_generator in trace_generators]
        + [last_report_date + report_extension]
    )

    return start_date, display_until


class CountryGraph:
    """Constructs a graph for a given country"""

    def __init__(
        self,
        report: CountryReport,
        country_predictions: List[CountryPrediction],
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
        start_date, display_until = _get_display_range(report, trace_generator_by_event.values())
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
        self.date_title = None

        self.max_value = max(
            [trace.max_value for trace in self.trace_by_event.values()]
            + [self.cropped_cumulative_active.max()]
        )
        self.log_yrange = [
            math.log10(max(1, self.cropped_cumulative_active.min())) - 0.3,
            math.log10(self.max_value) + 0.3,
        ]

    def _create_slider(self, traces: List[Scatter], events: List[PredictionEvent]):
        def _create_visibility_vector(event_name: str) -> List[bool]:
            return [
                trace.legendgroup == event_name or trace.legendgroup is None for trace in traces
            ]

        steps = [
            dict(
                method="restyle",
                args=("visible", _create_visibility_vector(event.name)),
                label=event.last_data_date.strftime("%B %d"),
            )
            for event in self.trace_by_event.keys()
        ]
        # Mark trace corresponding to the latest prediction event as visible
        for trace in traces:
            if trace.legendgroup == events[-1].name or trace.legendgroup is None:
                trace.visible = True

        return dict(
            active=len(steps) - 1,
            currentvalue={"prefix": "Prediction date: "},
            pad={"b": 20},
            steps=steps,
            y=1,
            yanchor="bottom",
        )

    def create_country_figure(
        self,
        graph_axis_type: GraphAxisType = GraphAxisType.Linear,
        graph_type: GraphType = GraphType.SinglePrediction,
    ):
        def adjust_xlabel(date: datetime.date):
            # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
            # x-axis isn't log-scale.
            if graph_axis_type != GraphAxisType.LogLog:
                return date
            else:
                return (date - self.log_xaxis_date_since).days

        def color_and_opacity_by_event(event: PredictionEvent, count: int):
            orange = "rgb(255, 123, 37)"
            blue = "rgb(0, 121, 177)"
            green = "rgb(43, 161, 59)"
            # Matplotlib colors.
            if event == BK_20200329:
                return orange, 1.0
            if event == BK_20200411:
                return green, 1.0

            if graph_type == GraphType.MultiPredictions:
                # GraphType.MultiPredictions doesn't contain green BK_20200411, so it can have green
                return green, count / len(self.trace_by_event)
            elif graph_type == GraphType.BayesPredictions:
                return blue, min(1.0, 10.0 / len(self.trace_by_event))
            else:
                return blue, 1.0

        traces = []
        visibility = graph_type != GraphType.Slider
        count = 0
        for event, trace in self.trace_by_event.items():
            prediction_date_str = event.prediction_date.strftime("%b %d")
            data_until_idx = trace.xs.index(event.last_data_date)

            count += 1
            color, opacity = color_and_opacity_by_event(event, count)

            if graph_type == GraphType.MultiPredictions:
                # Last data date mark.
                data_until_y = trace.ys[data_until_idx]
                traces.append(
                    Scatter(
                        x=[
                            adjust_xlabel(event.last_data_date),
                            adjust_xlabel(event.last_data_date),
                        ],
                        y=[1.0, data_until_y],
                        mode="markers",
                        name="Data cutoff",
                        marker=dict(size=15, symbol="circle", color=color),
                        line=dict(width=3, color=color),
                        opacity=opacity,
                        legendgroup=event.name,
                        showlegend=False,
                        hoverinfo="skip",
                        visible=True,
                    )
                )
            elif graph_type != GraphType.BayesPredictions or count == 1:
                # For Bayesian predictions we only want to draw one rectangle
                rect_x = [
                    adjust_xlabel(self.cropped_dates[0]),
                    adjust_xlabel(event.last_data_date),
                ]
                rect_x = rect_x + rect_x[::-1]
                traces.append(
                    Scatter(
                        x=rect_x,
                        y=[0, 0, self.max_value, self.max_value],
                        mode="none",
                        fill="tozerox",
                        fillcolor="rgba(144, 238, 144, 0.4)",
                        opacity=0.4,
                        line=dict(color="rgba(255,255,255,0)"),
                        showlegend=False,
                        hoverinfo="skip",
                        legendgroup=event.name,
                        visible=visibility,
                    )
                )

            traces.append(
                Scatter(
                    x=list(map(adjust_xlabel, trace.xs[: data_until_idx + 1])),
                    y=trace.ys[: data_until_idx + 1],
                    text=trace.xs[: data_until_idx + 1],
                    mode="lines",
                    # TODO(lukas): we should have a better API then '.replace'
                    name=trace.label.replace("%PREDICTION_DATE%", prediction_date_str),
                    line=dict(width=2, color=color),
                    opacity=opacity,
                    legendgroup=event.name,
                    visible=visibility,
                )
            )
            traces.append(
                Scatter(
                    x=list(map(adjust_xlabel, trace.xs[data_until_idx:])),
                    y=trace.ys[data_until_idx:],
                    text=trace.xs[data_until_idx:],
                    mode="lines",
                    name=trace.label.replace("%PREDICTION_DATE%", prediction_date_str),
                    line=dict(width=2, dash="dot", color=color),
                    opacity=opacity,
                    legendgroup=event.name,
                    showlegend=False,
                    visible=visibility,
                )
            )

            if graph_type != GraphType.BayesPredictions:
                # Maximum mark.
                traces.append(
                    Scatter(
                        mode="markers",
                        x=[
                            adjust_xlabel(trace.max_value_date),
                            adjust_xlabel(trace.max_value_date),
                        ],
                        y=[1.0, trace.max_value],
                        name="Peak",
                        line=dict(color=color),
                        opacity=opacity,
                        marker=dict(size=15, symbol="star"),
                        legendgroup=event.name,
                        showlegend=False,
                        hoverinfo="skip",
                        visible=visibility,
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

        sliders = []
        if graph_type == GraphType.Slider and len(self.trace_by_event) > 0:
            sliders.append(self._create_slider(traces, list(self.trace_by_event.keys())))

        layout = Layout(
            title=dict(text=f"Active cases in {self.long_name}", x=0.5, xanchor="center", y=1),
            xaxis=dict(
                autorange=True,
                fixedrange=True,
                showgrid=False,
            ),
            yaxis=dict(
                tickformat=",.0f",
                gridcolor="LightGray",
                fixedrange=True,
                zerolinecolor="Gray",
            ),
            height=700,
            margin=dict(r=40),
            hovermode="x" if graph_type != GraphType.MultiPredictions else "closest",
            font=dict(size=18),
            legend=dict(x=0.01, y=0.99, borderwidth=1),
            showlegend=graph_type != GraphType.BayesPredictions,
            plot_bgcolor="White",
            sliders=sliders,
        )

        self.figure = Figure(data=traces, layout=layout)
        return self.update_graph_axis_type(graph_axis_type)

    def update_graph_axis_type(self, graph_axis_type: GraphAxisType):
        if graph_axis_type == GraphAxisType.Linear:
            self.figure.update_xaxes(type="date", title=self.date_title)
            self.figure.update_yaxes(type="linear", autorange=True)
        elif graph_axis_type == GraphAxisType.SemiLog:
            self.figure.update_xaxes(type="date", title=self.date_title)
            self.figure.update_yaxes(type="log", autorange=False, range=self.log_yrange)
        elif graph_axis_type == GraphAxisType.LogLog:
            self.figure.update_xaxes(type="log", title=self.log_title)
            self.figure.update_yaxes(type="log", autorange=False, range=self.log_yrange)
        return self.figure


@click.command(help="COVID-19 visualization of active cases")
@click.argument(
    "country_data_file",
    required=True,
    type=click_pathlib.Path(exists=True),
)
@click.argument(
    "prediction_dir",
    required=True,
    type=click_pathlib.Path(exists=True),
)
def show_country_plot(country_data_file: Path, prediction_dir: Path):
    country_report = create_report(country_data_file)
    prediction_db = predictions.load_prediction_db(prediction_dir=prediction_dir)
    country_predictions = [
        prediction
        for prediction in prediction_db.select_predictions(
            country=country_report.short_name, last_data_dates=country_report.dates[-28:]
        )
        # We do not want to show BK predictions on the slider
        if type(prediction.formula) == FittedFormula
    ]

    country_graph = CountryGraph(report=country_report, country_predictions=country_predictions)
    country_graph.create_country_figure(graph_type=GraphType.Slider).show()
