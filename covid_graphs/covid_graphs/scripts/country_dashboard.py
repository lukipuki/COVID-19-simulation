import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import timedelta
from flask import Flask
from pathlib import Path
from typing import List

from covid_graphs.country_graph import CountryGraph, GraphType
from covid_graphs.country_report import CountryReport
from covid_graphs.predictions import prediction_db, PredictionEvent, BK_20200411, OTHER


def create_graphs(
    reports: List[CountryReport], prediction_event: PredictionEvent,
):
    report_from_name = {report.short_name: report for report in reports}

    # Note: We silently assume there is only one prediction per country.
    country_graphs = [
        CountryGraph(report_from_name[country_prediction.country], [country_prediction])
        for country_prediction in prediction_db.predictions_for_event(prediction_event)
    ]
    country_graphs.sort(key=lambda graph: graph.short_name)
    return country_graphs


def create_dashboard(
    data_dir: Path, server: Flask,
):
    # TODO(miskosz): Don't use print.
    print("Creating dashboard for prediction graphs.")
    prediction_events = prediction_db.get_prediction_events()
    prediction_events.sort(key=lambda event: event.date, reverse=True)
    prediction_event_from_name = {
        prediction_event.name: prediction_event for prediction_event in prediction_events
    }

    # TODO: parsing the proto can fail
    reports = [
        CountryReport(data_dir / f"{country_short_name}.data", country_short_name)
        for country_short_name in prediction_db.get_countries()
        if (data_dir / f"{country_short_name}.data").is_file()
    ]
    graph_dict = {
        prediction_event.name: create_graphs(reports, prediction_event)
        for prediction_event in prediction_db.get_prediction_events()
    }

    app = dash.Dash(
        name=f"COVID-19 predictions",
        url_base_pathname=f"/covid19/predictions/",
        server=server,
        external_scripts=[
            "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML"
        ],
    )
    app.title = "COVID-19 predictions of Boďová and Kollár"

    content = _get_header_content(app.title)

    content += [html.Hr(), html.H1(id="graph-title")]
    buttons = [
        dcc.Dropdown(
            id="prediction-event",
            options=[
                dict(label=(event.date + timedelta(days=1)).strftime("%B %d"), value=event.name)
                for event in prediction_events
                if event != OTHER
            ],
            value=BK_20200411.name,
            style={"width": "40%"},
        ),
        dcc.Dropdown(id="country-short-name", value="Italy", style={"width": "40%"}),
        dcc.RadioItems(
            id="graph-type",
            options=[
                {"label": graph_type.value, "value": graph_type.name,}
                for graph_type in [GraphType.Normal, GraphType.SemiLog, GraphType.LogLog]
            ],
            value="Normal",
            labelStyle={"display": "inline-block"},
        ),
    ]
    content += buttons
    content += [dcc.Graph(id="country-graph", figure=dict(layout=dict(height=700)))]

    app.layout = html.Div(children=content, style={"font-family": "sans-serif"})

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
        next_day = prediction_event_from_name[prediction_event_name].date + timedelta(days=1)
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


def _get_header_content(title: str):
    mar30_prediction_link = (
        "https://www.facebook.com/permalink.php?story_fbid=10113020662000793&id=2247644"
    )
    france_link = (
        "https://www.reuters.com/article/us-health-coronavirus-france-toll/"
        "french-coronavirus-cases-jump-above-chinas-after-including-nursing-home-tally-idUSKBN21L3BG"
    )
    return [
        html.H1(children=title),
        dcc.Markdown(
            f"""
            Mathematicians Katarína Boďová and Richard Kollár predicted in March and April 2020
            the growth of active cases during COVID-19 pandemic. Assuming social distancing measures
            limit the rate of spread of the disease, their model suggests a polynomial growth with exponential
            decay given by:

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
            * April 13 predictions: Personal communication

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
