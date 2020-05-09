from enum import Enum
from pathlib import Path
from typing import Dict, List

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.development.base_component import Component
from flask import Flask

import covid_graphs.country_report as country_report
from covid_graphs.country_graph import CountryGraph, GraphAxisType, GraphType
from covid_graphs.country_report import CountryReport
from covid_graphs.predictions import BK_20200329, BK_20200411, PredictionEvent, prediction_db
from covid_graphs.prediction_generator import get_fitted_predictions


class DashboardType(Enum):
    SingleCountry = "single"
    SingleCountryAllPredictions = "country"
    AllCountries = "all"

    def __str__(self):
        return self.value


TITLE = "COVID-19 predictions of Boďová and Kollár"
CountryGraphsByReportName = Dict[str, List[CountryGraph]]


class DashboardFactory:
    def __init__(self, data_dir: Path):
        prediction_events = prediction_db.get_prediction_events()
        prediction_events.sort(key=lambda event: event.last_data_date, reverse=True)
        self.prediction_event_by_name = {
            prediction_event.name: prediction_event for prediction_event in prediction_events
        }

        reports = [
            country_report.create_report(data_dir / f"{country_short_name}.data")
            for country_short_name in prediction_db.get_countries()
            if (data_dir / f"{country_short_name}.data").is_file()
        ]
        self.report_by_short_name = {report.short_name: report for report in reports}

        self.graphs_by_event = {
            prediction_event.name: DashboardFactory._create_graphs(
                self.report_by_short_name, prediction_event
            )
            for prediction_event in prediction_db.get_prediction_events()
        }

    def create_dashboard(self, dashboard_type: DashboardType, server: Flask) -> dash.Dash:
        if dashboard_type == DashboardType.AllCountries:
            extra_content = [html.Div(id="country-graphs")]
        else:
            extra_content = [
                dcc.Graph(
                    id="country-graph",
                    figure=dict(layout=dict(height=700)),
                    config=dict(modeBarButtons=[["toImage"]]),
                )
            ]

        app = dash.Dash(
            name=f"COVID-19 predictions",
            url_base_pathname=f"/covid19/predictions/{dashboard_type}/",
            server=server,
            external_scripts=[
                "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
            ],
            meta_tags=[{"name": "viewport", "content": "width=750"}],
        )

        content = _get_header_content(title=TITLE)

        if dashboard_type != DashboardType.SingleCountryAllPredictions:
            content += [html.H1(id="graph-title")]
        else:
            content += [
                html.H1(id="graph-title", children="Automated daily predictions"),
                dcc.Markdown(
                    f"""
                    We display an automated prediction until yesterday and the week before. Note that the method to compute
                    these predictions slightly differs from Boďová and Kollár due to differences in implementation details.
                    """
                ),
            ]
        content += DashboardFactory._create_buttons(dashboard_type, self.report_by_short_name)
        content += extra_content

        app.title = TITLE
        app.layout = html.Div(
            children=content,
            style={
                "font-family": "sans-serif",
                "text-size-adjust": "none",
                "-webkit-text-size-adjust": "none",
            },
        )
        if dashboard_type == DashboardType.SingleCountry:
            self._create_single_country_callbacks(app)
        elif dashboard_type == DashboardType.SingleCountryAllPredictions:
            self._create_single_country_all_predictions_callbacks(app)
        else:
            self._create_all_countries_callbacks(app)

        return app

    @staticmethod
    def _create_graphs(
        report_by_short_name: Dict[str, CountryReport], prediction_event: PredictionEvent,
    ) -> List[CountryGraph]:
        # Note: We silently assume there is only one prediction per country.
        country_graphs = [
            CountryGraph(report_by_short_name[country_prediction.country], [country_prediction])
            for country_prediction in prediction_db.predictions_for_event(prediction_event)
        ]
        country_graphs.sort(key=lambda graph: graph.long_name)
        return country_graphs

    @staticmethod
    def _create_buttons(
        dashboard_type: DashboardType, report_by_short_name: Dict[str, CountryReport]
    ) -> List[dash.development.base_component.Component]:
        buttons = []
        if dashboard_type == DashboardType.AllCountries:
            buttons.append(
                dcc.Dropdown(
                    id="prediction-event",
                    options=[
                        dict(label=event.prediction_date.strftime("%B %d"), value=event.name,)
                        for event in [BK_20200329, BK_20200411]
                    ],
                    value=BK_20200411.name,
                    style={"width": "220px", "margin": "8px 0"},
                )
            )

        if (
            dashboard_type == DashboardType.SingleCountry
            or dashboard_type == DashboardType.SingleCountryAllPredictions
        ):
            buttons.append(
                dcc.Dropdown(
                    id="country-short-name",
                    options=[
                        dict(label=report.long_name, value=report.short_name)
                        for report in sorted(
                            report_by_short_name.values(), key=lambda x: x.long_name
                        )
                    ],
                    value="Italy",
                    style={"width": "220px", "margin": "8px 0"},
                )
            )

        buttons.append(
            dcc.RadioItems(
                id="graph-axis-type",
                options=[
                    {"label": graph_axis_type.value, "value": graph_axis_type.name}
                    for graph_axis_type in [GraphAxisType.Linear, GraphAxisType.SemiLog]
                ],
                value="Linear",
                labelStyle={"display": "inline-block", "margin": "0 4px 0 0"},
            ),
        )
        return buttons

    def _create_single_country_callbacks(self, app: dash.Dash) -> None:
        # TODO: Predictions will be generated statically in the future.
        graphs_by_country = {
            country_short_name: CountryGraph(
                self.report_by_short_name[country_short_name],
                get_fitted_predictions(
                    self.report_by_short_name[country_short_name],
                    last_data_dates=self.report_by_short_name[country_short_name].dates[-1:],
                ),
            )
            for country_short_name in prediction_db.get_countries()
        }

        @app.callback(
            Output("country-graph", component_property="figure"),
            [Input("graph-axis-type", "value"), Input("country-short-name", "value")],
        )
        def update_graph(graph_axis_type_str, country_short_name):
            graph = graphs_by_country[country_short_name]
            return graph.create_country_figure(
                graph_axis_type=GraphAxisType[graph_axis_type_str], graph_type=GraphType.Slider
            )

    def _create_single_country_all_predictions_callbacks(self, app: dash.Dash) -> None:
        # TODO: Predictions will be generated statically in the future.
        graph_by_short_name = {}
        for country_short_name in prediction_db.get_countries():
            report = self.report_by_short_name[country_short_name]
            country_predictions = prediction_db.predictions_for_country(country=country_short_name)
            country_predictions.extend(
                get_fitted_predictions(
                    country_report=report, last_data_dates=[report.dates[-1], report.dates[-8]]
                )
            )
            graph_by_short_name[country_short_name] = CountryGraph(
                report=report, country_predictions=country_predictions
            )

        @app.callback(
            Output("country-graph", component_property="figure"),
            [Input("graph-axis-type", "value"), Input("country-short-name", "value")],
        )
        def update_graph(graph_axis_type_str, country_short_name):
            graph_axis_type = GraphAxisType[graph_axis_type_str]
            return graph_by_short_name[country_short_name].create_country_figure(
                graph_axis_type=graph_axis_type, graph_type=GraphType.MultiPredictions
            )

    def _create_all_countries_callbacks(self, app: dash.Dash) -> None:
        dash_graph_dict = {
            prediction_event_name: [
                dcc.Graph(
                    id=f"{graph.short_name}-graph-{prediction_event_name}",
                    figure=graph.create_country_figure(graph_type=GraphType.SinglePrediction),
                    config=dict(modeBarButtons=[["toImage"]]),
                )
                for graph in self.graphs_by_event[prediction_event_name]
            ]
            for prediction_event_name in self.prediction_event_by_name.keys()
        }

        @app.callback(
            [
                Output("country-graphs", component_property="children"),
                Output("graph-title", component_property="children"),
            ],
            [Input("prediction-event", "value")],
        )
        def update_event(prediction_event_name):
            graphs = dash_graph_dict[prediction_event_name]
            next_day = self.prediction_event_by_name[prediction_event_name].prediction_date
            return graphs, f"{next_day.strftime('%B %d')} predictions"

        # TODO(lukas): only have one callback for all prediction events
        @app.callback(
            [
                Output(f"{graph.short_name}-graph-{BK_20200411.name}", component_property="figure")
                for graph in self.graphs_by_event[BK_20200411.name]
            ],
            [Input("graph-axis-type", "value")],
        )
        def update_country_graphs_20200411(graph_axis_type_str):
            result = []
            for graph in self.graphs_by_event[BK_20200411.name]:
                result.append(graph.update_graph_axis_type(GraphAxisType[graph_axis_type_str]))
            return result

        @app.callback(
            [
                Output(f"{graph.short_name}-graph-{BK_20200329.name}", component_property="figure")
                for graph in self.graphs_by_event[BK_20200329.name]
            ],
            [Input("graph-axis-type", "value")],
        )
        def update_country_graphs_20200329(graph_axis_type_str):
            result = []
            for graph in self.graphs_by_event[BK_20200329.name]:
                graph.update_graph_axis_type(GraphAxisType[graph_axis_type_str])
                result.append(graph.figure)
            return result


def _get_header_content(title: str) -> List[Component]:
    mar30_prediction_link = (
        "https://www.facebook.com/permalink.php?story_fbid=10113020662000793&id=2247644"
    )
    return [
        html.H1(children=title),
        dcc.Markdown(
            f"""
            Mathematicians Katarína Boďová and Richard Kollár predicted in March and April 2020
            the growth of active cases during COVID-19 pandemic. Their model suggests polynomial
            growth with exponential decay given by:

            * <em>N</em>(<em>t</em>) = (<em>A</em>/<em>T</em><sub><em>G</em></sub>) ⋅
              (<em>t</em>/<em>T</em><sub><em>G</em></sub>)<sup>α</sup> /
              e<sup><em>t</em>/<em>T</em><sub><em>G</em></sub></sup>

            Where:

            * *t* is time in days counted from a country-specific "day one"
            * *N(t)* the number of active cases (cumulative positively tested minus recovered and deceased)
            * *A*, *T<sub>G</sub>* and *α* are country-specific parameters

            They made two predictions, on March 30 (for 7 countries) and on April 12 (for 23
            countries), each based on data available until the day before. The first prediction
            assumed a common growth parameter *α* = 6.23.

            ### References
            * [Polynomial growth in age-dependent branching processes with diverging
              reproductive number](https://arxiv.org/abs/cond-mat/0505116) by Alexei Vazquez
            * [Fractal kinetics of COVID-19 pandemic]
              (https://www.medrxiv.org/content/10.1101/2020.02.16.20023820v2.full.pdf)
              by Robert Ziff and Anna Ziff
            * Unpublished manuscript by Katarína Boďová and Richard Kollár
            * March 30 predictions: [Facebook post]({mar30_prediction_link})
            * April 12 predictions: Personal communication

            ### Legend
            """,
            dangerously_allow_html=True,
        ),
        html.Ul(
            children=[
                html.Li("Solid line is prediction"),
                html.Li("Dashed line marks the culmination of the prediction"),
                html.Li("Red line is observed number of active cases"),
                html.Li(
                    children=[
                        "Data available until the date of prediction is in ",
                        html.Span("light green zone", style={"background-color": "lightgreen"}),
                    ]
                ),
            ]
        ),
        html.Hr(),
    ]
