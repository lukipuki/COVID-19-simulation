import dash
import dash_core_components as dcc
import dash_html_components as html
from flask import Flask
from pathlib import Path

from covid_graphs.country_graph import CountryGraph, GraphType
from covid_graphs.predictions import prediction_db, PredictionEvent


def create_dashboard(
    data_dir: Path,
    server: Flask,
    prediction_event: PredictionEvent,
    graph_type: GraphType,
):
    # TODO(miskosz): Don't use print.
    print(f"Creating dashboard for {prediction_event.name} {graph_type} graphs.")

    predictions = prediction_db.predictions_for_event(prediction_event)

    # Note: We silently assume there is only one prediction per country.
    country_graphs = [
        CountryGraph(data_dir, [country_prediction], graph_type)
        for country_prediction in predictions
        if (data_dir / f'{country_prediction.country}.data').is_file()
    ]
    country_graphs.sort(key=lambda graph: graph.name)

    app = dash.Dash(
        name=f'COVID-19 {graph_type}',
        url_base_pathname=f'/covid19/{prediction_event.name}/{graph_type}/',
        server=server,
        external_scripts=[
            'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
        ],
    )
    app.title = 'COVID-19 predictions'
    if graph_type != GraphType.Normal:
        app.title += f' on a {graph_type} graph'

    graphs = [
        dcc.Graph(id=f'{country_graph.name} {graph_type}',
                  figure=country_graph.create_country_figure())
        for country_graph in country_graphs
    ]

    content = _get_header_content(prediction_event) + graphs

    app.layout = html.Div(children=content, style={'font-family': 'sans-serif'})
    return app


def _get_header_content(prediction_event: PredictionEvent):
    # TODO: Rewrite the header to be general for both prediction pages.
    # TODO: Description in the text of this date is wrong.
    prediction_date_str = prediction_event.date.strftime("%Y-%m-%d")
    prediction_link = "https://www.facebook.com/permalink.php?"\
        "story_fbid=10113020662000793&id=2247644"
    france_link = "https://www.reuters.com/article/us-health-coronavirus-france-toll/" \
        "french-coronavirus-cases-jump-above-chinas-after-including-nursing-home-tally-idUSKBN21L3BG"
    return [
        html.H1(children='COVID-19 predictions of Boďová and Kollár'),
        html.P(children=[
            'On 2020-03-30, mathematicians Katarína Boďová and Richard Kollár ',
            html.A('made predictions about 7 countries', href=prediction_link),
            f'. The data available up to that point (until {prediction_date_str}) is in the ',
            html.Span('green zone', style={'color': 'green'}),
            f'. Data coming after {prediction_date_str} is in the ',
            html.Span('blue zone.', style=dict(color='blue')),
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