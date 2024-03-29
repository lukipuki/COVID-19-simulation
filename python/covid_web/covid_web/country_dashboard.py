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
from covid_graphs import predictions
from covid_graphs.country_graph import CountryGraph, GraphAxisType, GraphType
from covid_graphs.country_report import CountryReport
from covid_graphs.predictions import BK_20200329, BK_20200411, PredictionDb, PredictionEvent


class DashboardType(Enum):
    SingleCountry = "single"
    SingleCountryAllPredictions = "daily"
    AllCountries = "all"

    def __str__(self):
        return self.value


TITLE = "COVID-19 predictions of Boďová and Kollár"
CountryGraphsByReportName = Dict[str, List[CountryGraph]]
CURRENT_DIR = Path(__file__).parent


class DashboardFactory:
    def __init__(self, data_dir: Path, prediction_dir: Path):
        self.prediction_db = predictions.load_prediction_db(prediction_dir=prediction_dir)
        prediction_events = self.prediction_db.get_prediction_events()
        prediction_events.sort(key=lambda event: event.last_data_date)
        self.prediction_event_by_name = {
            prediction_event.name: prediction_event for prediction_event in prediction_events
        }
        self._dropdown_prediction_events = [
            prediction_events[-1],
            prediction_events[-8],
            prediction_events[-15],
            prediction_events[-22],
            prediction_events[-29],
            BK_20200411,
            BK_20200329,
        ]
        # Show the week-old prediction by default
        self._dropdown_initial_value = self._dropdown_prediction_events[1]

        reports = [
            country_report.create_report(data_dir / f"{country_short_name}.data")
            for country_short_name in self.prediction_db.get_countries()
            if (data_dir / f"{country_short_name}.data").is_file()
        ]
        self.report_by_short_name = {report.short_name: report for report in reports}

        self.graphs_by_event = {
            prediction_event.name: DashboardFactory._create_graphs(
                self.prediction_db, self.report_by_short_name, prediction_event
            )
            for prediction_event in self.prediction_db.get_prediction_events()
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
            name="COVID-19 predictions",
            # TODO(lukas): Dash registers the pathname with Flask, however we would like to execute
            # some code before the Dash app loads, so we append '-dash'.
            # See also https://github.com/plotly/dash/issues/214
            url_base_pathname=f"/covid19/predictions/{dashboard_type}-dash/",
            server=server,
            external_scripts=[
                "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
            ],
            meta_tags=[{"name": "viewport", "content": "width=750"}],
        )

        content = _get_header_content(title=TITLE, dashboard_type=dashboard_type)

        if dashboard_type != DashboardType.SingleCountryAllPredictions:
            content += [html.H1(id="graph-title")]
        else:
            content += [
                html.H1(id="graph-title", children="Automated daily predictions"),
            ]
        content += self._create_buttons(dashboard_type, self.report_by_short_name)
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
        prediction_db: PredictionDb,
        report_by_short_name: Dict[str, CountryReport],
        prediction_event: PredictionEvent,
    ) -> List[CountryGraph]:
        # Note: We silently assume there is only one prediction per country.
        country_graphs = [
            CountryGraph(report_by_short_name[country_prediction.country], [country_prediction])
            for country_prediction in prediction_db.predictions_for_event(prediction_event)
        ]
        country_graphs.sort(key=lambda graph: graph.long_name)
        return country_graphs

    def _create_buttons(
        self, dashboard_type: DashboardType, report_by_short_name: Dict[str, CountryReport]
    ) -> List[dash.development.base_component.Component]:
        buttons = []
        if dashboard_type == DashboardType.AllCountries:
            buttons.append(
                dcc.Dropdown(
                    id="prediction-event",
                    options=[
                        dict(
                            label=event.create_label(),
                            value=event.name,
                        )
                        for event in self._dropdown_prediction_events
                    ],
                    value=self._dropdown_initial_value.name,
                    style={"width": "350px", "margin": "8px 0"},
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
        graphs_by_country = {
            country_short_name: CountryGraph(
                self.report_by_short_name[country_short_name],
                # TODO(mszabados): Make it possible to select only automatic predictions.
                # Right now this shows BK predictions as well, which makes for a strange experience
                # (the curve changes color, etc).
                self.prediction_db.select_predictions(
                    country=country_short_name,
                    last_data_dates=self.report_by_short_name[country_short_name].dates,
                ),
            )
            for country_short_name in self.prediction_db.get_countries()
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
        graph_by_short_name = {}
        for country_short_name in self.prediction_db.get_countries():
            report = self.report_by_short_name[country_short_name]
            country_predictions = self.prediction_db.select_predictions(
                country=country_short_name,
                last_data_dates=[
                    report.dates[-1],
                    report.dates[-8],
                    report.dates[-15],
                    report.dates[-22],
                    report.dates[-29],
                ],
            )
            if len(country_predictions) > 0:
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
            (prediction_event_name, graph_axis_type): [
                dcc.Graph(
                    id=f"{graph.short_name}-graph-{prediction_event_name}",
                    figure=graph.create_country_figure(
                        graph_type=GraphType.SinglePrediction, graph_axis_type=graph_axis_type
                    ),
                    config=dict(modeBarButtons=[["toImage"]]),
                )
                for graph in self.graphs_by_event[prediction_event_name]
            ]
            for graph_axis_type in [GraphAxisType.Linear, GraphAxisType.SemiLog]
            for prediction_event_name in self.prediction_event_by_name.keys()
        }

        @app.callback(
            [
                Output("country-graphs", component_property="children"),
                Output("graph-title", component_property="children"),
            ],
            [Input("prediction-event", "value"), Input("graph-axis-type", "value")],
        )
        def update_dashboard(prediction_event_name: str, graph_axis_type_str: str):
            graph_axis_type = GraphAxisType[graph_axis_type_str]
            graphs = dash_graph_dict[(prediction_event_name, graph_axis_type)]

            prediction_date = self.prediction_event_by_name[prediction_event_name].prediction_date
            return graphs, f"{prediction_date.strftime('%B %d')} predictions"


def _get_header_content(title: str, dashboard_type: DashboardType) -> List[Component]:
    about = ""
    with open(CURRENT_DIR / "about.md", "r", encoding="utf-8") as about_file:
        about = about_file.read()

    if dashboard_type == DashboardType.SingleCountryAllPredictions:
        end_of_data_legend = ["Circle marks the date of prediction"]
    else:
        end_of_data_legend = [
            "Data available until the date of prediction is in ",
            html.Span("light green zone", style={"background-color": "lightgreen"}),
        ]

    return [
        html.H1(children=title),
        dcc.Markdown(about, dangerously_allow_html=True),
        html.H3(children="Legend"),
        html.Ul(
            children=[
                html.Li("Solid/dashed line is prediction"),
                html.Li("Star marks the culmination of the prediction"),
                html.Li("Red line is observed number of active cases"),
                html.Li(children=end_of_data_legend),
            ]
        ),
        html.Hr(),
    ]
