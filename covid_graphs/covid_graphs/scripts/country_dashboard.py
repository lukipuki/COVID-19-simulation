import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import timedelta
from flask import Flask
from pathlib import Path

from covid_graphs.country_graph import CountryGraph, GraphType
from covid_graphs.predictions import prediction_db, PredictionEvent


def create_dashboard(
        data_dir: Path,
        server: Flask,
        prediction_event: PredictionEvent,
):
    # TODO(miskosz): Don't use print.
    print(f"Creating dashboard for {prediction_event.name} graphs.")

    predictions = prediction_db.predictions_for_event(prediction_event)

    # Note: We silently assume there is only one prediction per country.
    country_graphs = [
        CountryGraph(data_dir, [country_prediction]) for country_prediction in predictions
        if (data_dir / f'{country_prediction.country}.data').is_file()
    ]
    country_graphs.sort(key=lambda graph: graph.short_name)

    app = dash.Dash(
        name=f'COVID-19 predictions {prediction_event.name}',
        url_base_pathname=f'/covid19/{prediction_event.name}/',
        server=server,
        external_scripts=[
            'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
        ],
    )
    app.title = 'COVID-19 predictions of Boďová and Kollár'

    content = _get_header_content(app.title)

    next_day = prediction_event.date + timedelta(days=1)
    content += [
        html.Hr(),
        html.H1(f"{next_day.strftime('%B %d')} predictions")
    ]
    buttons = [
        dcc.Dropdown(id='country-short-name',
                     options=[
                         dict(label=graph.long_name, value=graph.short_name)
                         for graph in country_graphs
                     ],
                     value='Italy',
                     style={'width': '30%'}),
        dcc.RadioItems(id='graph-type',
                       options=[{
                           'label': graph_type.value,
                           'value': graph_type.name,
                       } for graph_type in [GraphType.Normal, GraphType.SemiLog, GraphType.LogLog]],
                       value='Normal',
                       labelStyle={'display': 'inline-block'})
    ]
    content += buttons
    content += [dcc.Graph(id='country-graph', figure=dict(layout=dict(height=700)))]

    app.layout = html.Div(children=content, style={'font-family': 'sans-serif'})

    @app.callback(Output('country-graph', component_property='figure'),
                  [Input('graph-type', 'value'),
                   Input('country-short-name', 'value')])
    def update_graph(graph_type_str, country_short_name):
        graph_type = GraphType[graph_type_str]

        graphs = [
            country_graph for country_graph in country_graphs
            if country_graph.short_name == country_short_name
        ]

        figure = graphs[0].create_country_figure(graph_type)
        return figure

    return app


def _get_header_content(title: str):
    mar30_prediction_link = "https://www.facebook.com/permalink.php?"\
        "story_fbid=10113020662000793&id=2247644"
    france_link = "https://www.reuters.com/article/us-health-coronavirus-france-toll/" \
        "french-coronavirus-cases-jump-above-chinas-after-including-nursing-home-tally-idUSKBN21L3BG"
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

            They made two predictions, on [March 30](/covid19/predictions/mar29) (for 7 countries)
            and on [April 12](/covid19/predictions/apr11) (for 23 countries), each based on data available until
            the day before. The first prediction assumed a common growth parameter <em>α</em> = 6.23.

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
                        html.Span('light green zone', style={'background-color': 'lightgreen'}),
                    ]
                ),
            ]
        )
    ]
