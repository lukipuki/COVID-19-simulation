from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask

import covid_graphs.country_report as country_report
from covid_graphs import country_graph
from covid_graphs.country_graph import CountryGraph, GraphType
from covid_graphs.country_report import CountryReport
from covid_graphs.predictions import BK_20200329, BK_20200411, PredictionEvent, prediction_db


class DashboardType(Enum):
    SingleCountry = "single"
    SingleCountryAllPredictions = "country"
    AllCountries = "all"

    def __str__(self):
        return self.value


TITLE = "COVID-19 predictions of Boďová and Kollár"
CountryGraphsByReportName = Dict[str, List[CountryGraph]]


class CountryDashboard:
    def __init__(self, dashboard_type: DashboardType, data_dir: Path, server: Flask):
        prediction_events = prediction_db.get_prediction_events()
        prediction_events.sort(key=lambda event: event.last_data_date, reverse=True)
        self.prediction_event_by_name = {
            prediction_event.name: prediction_event for prediction_event in prediction_events
        }

        reports = [
            country_report.create_report(
                data_dir / f"{country_short_name}.data", country_short_name
            )
            for country_short_name in prediction_db.get_countries()
            if (data_dir / f"{country_short_name}.data").is_file()
        ]
        self.report_by_short_name = {report.short_name: report for report in reports}

        if (
            dashboard_type == DashboardType.SingleCountry
            or dashboard_type == DashboardType.AllCountries
        ):
            self.graph_dict = {
                prediction_event.name: CountryDashboard._create_graphs(
                    self.report_by_short_name, prediction_event
                )
                for prediction_event in prediction_db.get_prediction_events()
            }

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

        self.app = self._create_dash_app(dashboard_type, server, extra_content)
        if dashboard_type == DashboardType.SingleCountry:
            self._create_single_country_callbacks()
        elif dashboard_type == DashboardType.SingleCountryAllPredictions:
            self._create_single_country_all_predictions_callbacks()
        else:
            self._create_all_countries_callbacks()

    def get_app(self):
        return self.app

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
    ):
        buttons = []
        if (
            dashboard_type == DashboardType.SingleCountry
            or dashboard_type == DashboardType.AllCountries
        ):
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

        if dashboard_type == DashboardType.SingleCountry:
            buttons.append(
                dcc.Dropdown(
                    id="country-short-name",
                    value="Italy",
                    style={"width": "220px", "margin": "8px 0"},
                )
            )
        elif dashboard_type == DashboardType.SingleCountryAllPredictions:
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
                id="graph-type",
                options=[
                    {"label": graph_type.value, "value": graph_type.name}
                    for graph_type in [GraphType.Linear, GraphType.SemiLog]
                ],
                value="Linear",
                labelStyle={"display": "inline-block", "margin": "0 4px 0 0"},
            ),
        )
        return buttons

    def _create_dash_app(
        self, dashboard_type: DashboardType, server: Flask, extra_content: List[Any]
    ):
        app = dash.Dash(
            name=f"COVID-19 predictions",
            url_base_pathname=f"/covid19/predictions/{dashboard_type}/",
            server=server,
            external_scripts=[
                "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
            ],
            meta_tags=[{"name": "viewport", "content": "width=750"}],
        )
        content = _get_header_content(TITLE)
        content += [html.Hr(), html.H1(id="graph-title")]
        content += CountryDashboard._create_buttons(dashboard_type, self.report_by_short_name)
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
        return app

    def _create_single_country_callbacks(self):
        @self.app.callback(
            [
                Output("country-short-name", component_property="options"),
                Output("graph-title", component_property="children"),
            ],
            [Input("prediction-event", "value")],
        )
        def update_event(prediction_event_name):
            options = [
                dict(label=graph.long_name, value=graph.short_name)
                for graph in self.graph_dict[prediction_event_name]
            ]
            prediction_date = self.prediction_event_by_name[prediction_event_name].prediction_date
            return options, f"{prediction_date.strftime('%B %d')} predictions"

        @self.app.callback(
            Output("country-graph", component_property="figure"),
            [
                Input("prediction-event", "value"),
                Input("graph-type", "value"),
                Input("country-short-name", "value"),
            ],
        )
        def update_graph(prediction_event_name, graph_type_str, country_short_name):
            graph_type = GraphType[graph_type_str]

            graphs = [
                country_graph
                for country_graph in self.graph_dict[prediction_event_name]
                if country_graph.short_name == country_short_name
            ]
            if len(graphs) == 0:
                return dash.no_update

            figure = graphs[0].create_country_figure(graph_type)
            return figure

    def _create_single_country_all_predictions_callbacks(self):
        # TODO: Predictions will be generated statically in the future.
        graph_by_short_name = {}
        for country_short_name in prediction_db.get_countries():
            report = self.report_by_short_name[country_short_name]
            country_predictions = prediction_db.predictions_for_country(country=country_short_name)
            country_predictions.extend(country_graph.get_fitted_predictions(report=report))
            graph_by_short_name[country_short_name] = CountryGraph(
                report=report, country_predictions=country_predictions
            )

        @self.app.callback(
            Output("country-graph", component_property="figure"),
            [Input("graph-type", "value"), Input("country-short-name", "value")],
        )
        def update_graph(graph_type_str, country_short_name):
            graph_type = GraphType[graph_type_str]
            figure = graph_by_short_name[country_short_name].create_country_figure(graph_type)
            return figure

    def _create_all_countries_callbacks(self):
        dash_graph_dict = {
            prediction_event_name: [
                dcc.Graph(
                    id=f"{graph.short_name}-graph-{prediction_event_name}",
                    figure=graph.create_country_figure(),
                    config=dict(modeBarButtons=[["toImage"]]),
                )
                for graph in self.graph_dict[prediction_event_name]
            ]
            for prediction_event_name in self.prediction_event_by_name.keys()
        }

        @self.app.callback(
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
        @self.app.callback(
            [
                Output(f"{graph.short_name}-graph-{BK_20200411.name}", component_property="figure")
                for graph in self.graph_dict[BK_20200411.name]
            ],
            [Input("graph-type", "value")],
        )
        def update_country_graphs_20200411(graph_type_str):
            result = []
            for graph in self.graph_dict[BK_20200411.name]:
                result.append(graph.update_graph_type(GraphType[graph_type_str]))
            return result

        @self.app.callback(
            [
                Output(f"{graph.short_name}-graph-{BK_20200329.name}", component_property="figure")
                for graph in self.graph_dict[BK_20200329.name]
            ],
            [Input("graph-type", "value")],
        )
        def update_country_graphs_20200329(graph_type_str):
            result = []
            for graph in self.graph_dict[BK_20200329.name]:
                graph.update_graph_type(GraphType[graph_type_str])
                result.append(graph.figure)
            return result


def _get_header_content(title: str):
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
    ]
