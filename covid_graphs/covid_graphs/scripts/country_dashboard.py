from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Tuple

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask, jsonify, abort

from covid_graphs.country_graph import CountryGraph, GraphType
from covid_graphs.country_report import CountryReport
from covid_graphs.predictions import BK_20200411, OTHER, PredictionEvent, prediction_db


class DashboardType(Enum):
    SingleCountry = "single"
    AllCountries = "all"

    def __str__(self):
        return self.value


TITLE = "COVID-19 predictions of Boďová and Kollár"
CountryGraphsByReportName = Dict[str, List[CountryGraph]]


def _create_buttons(dashboard_type: DashboardType):
    buttons = [
        dcc.Dropdown(
            id="prediction-event",
            options=[
                dict(label=(event.date + timedelta(days=1)).strftime("%B %d"), value=event.name)
                for event in prediction_db.get_prediction_events()
                if event != OTHER
            ],
            value=BK_20200411.name,
            style={"width": "220px", "margin": "8px 0"},
        )
    ]
    if dashboard_type == DashboardType.SingleCountry:
        buttons.append(
            dcc.Dropdown(
                id="country-short-name", value="Italy", style={"width": "220px", "margin": "8px 0"}
            )
        )

    buttons.append(
        dcc.RadioItems(
            id="graph-type",
            options=[
                {"label": graph_type.value, "value": graph_type.name}
                for graph_type in [GraphType.Normal, GraphType.SemiLog, GraphType.LogLog]
            ],
            value="Normal",
            labelStyle={"display": "inline-block", "margin": "0 4px 0 0"},
        ),
    )
    return buttons


def create_graphs(
    report_by_short_name: Dict[str, CountryReport], prediction_event: PredictionEvent,
) -> List[CountryGraph]:
    # Note: We silently assume there is only one prediction per country.
    country_graphs = [
        CountryGraph(report_by_short_name[country_prediction.country], [country_prediction])
        for country_prediction in prediction_db.predictions_for_event(prediction_event)
    ]
    country_graphs.sort(key=lambda graph: graph.short_name)
    return country_graphs


def _prepare_data_structures(
    data_dir: Path,
) -> Tuple[Dict[str, PredictionEvent], CountryGraphsByReportName]:
    prediction_events = prediction_db.get_prediction_events()
    prediction_events.sort(key=lambda event: event.date, reverse=True)
    prediction_event_by_name = {
        prediction_event.name: prediction_event for prediction_event in prediction_events
    }

    # TODO: parsing the proto can fail
    reports = [
        CountryReport(data_dir / f"{country_short_name}.data", country_short_name)
        for country_short_name in prediction_db.get_countries()
        if (data_dir / f"{country_short_name}.data").is_file()
    ]
    report_by_short_name = {report.short_name: report for report in reports}
    graph_dict = {
        prediction_event.name: create_graphs(report_by_short_name, prediction_event)
        for prediction_event in prediction_db.get_prediction_events()
    }
    return prediction_event_by_name, graph_dict


def _create_dash_app(dashboard_type: DashboardType, server: Flask, extra_content: List[Any]):
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
    content += _create_buttons(dashboard_type)
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


def create_single_country_dashboard(data_dir: Path, server: Flask):
    # TODO(miskosz): Don't use print.
    print("Creating dashboard for a single country.")

    graph = dcc.Graph(
        id="country-graph",
        figure=dict(layout=dict(height=700)),
        config=dict(modeBarButtons=[["toImage"]]),
    )

    app = _create_dash_app(DashboardType.SingleCountry, server, extra_content=[graph])

    prediction_event_by_name, graph_dict = _prepare_data_structures(data_dir)

    @app.callback(
        [
            Output("country-short-name", component_property="options"),
            Output("graph-title", component_property="children"),
        ],
        [Input("prediction-event", "value")],
    )
    def update_event(prediction_event_name):
        options = [
            dict(label=graph.long_name, value=graph.short_name)
            for graph in graph_dict[prediction_event_name]
        ]
        next_day = prediction_event_by_name[prediction_event_name].date + timedelta(days=1)
        return options, f"{next_day.strftime('%B %d')} predictions"

    @app.callback(
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
            for country_graph in graph_dict[prediction_event_name]
            if country_graph.short_name == country_short_name
        ]
        if len(graphs) == 0:
            return dash.no_update

        return graphs[0].create_country_figure(graph_type)

    return app


def create_all_countries_dashboard(data_dir: Path, server: Flask):
    # TODO(miskosz): Don't use print.
    print("Creating dashboard for all countries.")
    extra_content = [html.Div(id="country-graphs")]

    app = _create_dash_app(DashboardType.AllCountries, server, extra_content)

    prediction_event_by_name, graph_dict = _prepare_data_structures(data_dir)

    dash_graph_dict = {
        (prediction_event_name, graph_type.name): [
            dcc.Graph(
                id=f"country-graph-{graph.short_name}",
                figure=graph.create_country_figure(graph_type),
                config=dict(modeBarButtons=[["toImage"]]),
            )
            for graph in graph_dict[prediction_event_name]
        ]
        for prediction_event_name in prediction_event_by_name.keys()
        for graph_type in GraphType
    }

    @app.callback(
        [
            Output("country-graphs", component_property="children"),
            Output("graph-title", component_property="children"),
        ],
        [Input("prediction-event", "value"), Input("graph-type", "value")],
    )
    def update_event(prediction_event_name, graph_type_str):
        graphs = dash_graph_dict[(prediction_event_name, graph_type_str)]
        next_day = prediction_event_by_name[prediction_event_name].date + timedelta(days=1)
        return graphs, f"{next_day.strftime('%B %d')} predictions"


def _get_header_content(title: str):
    mar30_prediction_link = (
        "https://www.facebook.com/permalink.php?story_fbid=10113020662000793&id=2247644"
    )
    # france_link = (
    #     "https://www.reuters.com/article/us-health-coronavirus-france-toll/"
    #     "french-coronavirus-cases-jump-above-chinas-after-including-nursing-home-tally-idUSKBN21L3BG"
    # )
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
        # TODO: Include these?
        # ### Notes about the graphs
        # * France has been excluded, since they [screwed up daily data reporting]({france_link}).
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

class PredictionRest:
    def __init__(self, data_dir: Path):
        prediction_event_by_name, graph_dict = _prepare_data_structures(data_dir)
        self.prediction_event_by_name = prediction_event_by_name
        self.graph_dict = graph_dict
    
    def get_available_predictions(self):
        result = {}
        for x in prediction_db.get_prediction_events():
            result[x.name] = {
                "label": x.date,
                "countries": [p.country for p in prediction_db.predictions_for_event(x)]
            }
        return jsonify(result)

    def get_specific_prediction(self, date: str, country: str):
        if date not in self.graph_dict:
            abort(404)

        for graph in self.graph_dict[date]:
            if graph.short_name == country:
                return jsonify(graph.create_country_rest_data())

        abort(404)
        return null
    

def create_prediction_rest(data_dir: Path, server: Flask):
    return PredictionRest(data_dir)