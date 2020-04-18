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

    content = _get_header_content(prediction_event, app.title)
    content += [html.Hr()]
    buttons = [
        dcc.Dropdown(id='country-short-name',
                     options=[
                         dict(label=graph.short_name, value=graph.short_name)
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


def _get_header_content(prediction_event: PredictionEvent, title: str):
    # TODO: Rewrite the header to be general for both prediction pages.
    # TODO: Description in the text of this date is wrong.
    prediction_date_str = prediction_event.date.strftime("%Y-%m-%d")
    prediction_link = "https://www.facebook.com/permalink.php?"\
        "story_fbid=10113020662000793&id=2247644"
    france_link = "https://www.reuters.com/article/us-health-coronavirus-france-toll/" \
        "french-coronavirus-cases-jump-above-chinas-after-including-nursing-home-tally-idUSKBN21L3BG"
    next_day = prediction_event.date + timedelta(days=1)
    return [
        html.H1(children=title),
        html.P(children=[
            # TODO: fix the date
            f'On {next_day}, mathematicians Katarína Boďová and Richard Kollár ',
            html.A('made predictions about 7 countries', href=prediction_link),
            f'. The data available up to that point (until {prediction_date_str}) is in the ',
            html.Span('light green zone', style={'background-color': 'lightgreen'}),
            f'. Data coming after {prediction_date_str} is in the white zone.',
            dcc.Markdown(
                """
                The predicted number of active cases <em>N</em>(<em>t</em>) on day <em>t</em> is
                calculated as follows (constants <em>A</em> and <em>T</em><sub><em>G</em></sub>
                are country-specific):
                <em>N</em>(<em>t</em>) = (<em>A</em>/<em>T</em><sub><em>G</em></sub>) ⋅
                (<em>t</em>/<em>T</em><sub><em>G</em></sub>)<sup>6.23</sup> /
                e<sup><em>t</em>/<em>T</em><sub><em>G</em></sub></sup>
                """,
                dangerously_allow_html=True,
            ),
        ]),
        dcc.Markdown("""
            ### References
            * [Polynomial growth in age-dependent branching processes with diverging
              reproductive number](https://arxiv.org/abs/cond-mat/0505116) by Alexei Vazquez
            * [Fractal kinetics of COVID-19 pandemic]
              (https://www.medrxiv.org/content/10.1101/2020.02.16.20023820v2.full.pdf)
              by Robert Ziff and Anna Ziff
            * Unpublished manuscript by Katarína Boďová and Richard Kollár
            """),
        dcc.Markdown(f"""
            ### Notes about the graphs

            * Dashed lines are the predictions, solid red lines are the real active
              cases. Black dotted lines mark the predicted maximums.
            * We've now added new prediction made on 2020-04-13 by the same authors. There's a
              second dashed line for Italy, Spain, USA and Germany.
            * France has been excluded, since they [screwed up daily data reporting]({france_link}).
            """,
                     dangerously_allow_html=True)
    ]
