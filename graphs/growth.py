#!/usr/bin/env python3
from country import Country, CountryReport, GraphType, Formula, ATG_formula, PREDICTION_DATE
from flask import Flask, render_template
import argparse
import dash
import dash_core_components as dcc
import dash_html_components as html
import os

parser = argparse.ArgumentParser(description='COVID-19 country growth visualization')
parser.add_argument('data', metavar='data', type=str, help=f"Directory with YAML files")
parser.add_argument('country', metavar='country', type=str, help=f"Country name or 'ALL'")
args = parser.parse_args()


countries = [
    Country('Slovakia', Formula(lambda t: 8 * t**1.28, r'$8 \cdot t^{1.28}$', 60, 60), 10),
    Country('Italy', ATG_formula(7.8, 4417), 200),
    # The following two are for the blog post
    # Country('Italy', Formula(lambda t: 2.5 * t**3, r'$2.5 \cdot t^{3}$', 60, 60), 200),
    # Country('Italy', Formula(lambda t: (229/1.167) * 1.167**t, r'$196 \cdot 1.167^t$', 60, 60), 200),
    Country('Spain', ATG_formula(6.4, 3665), 200),
    Country('Germany', ATG_formula(6.7, 3773), 200),
    Country('USA', ATG_formula(10.2, 72329), 200),
    Country('UK', ATG_formula(7.2, 2719), 200),
    Country('France', ATG_formula(6.5, 1961), 200),
    Country('Iran', ATG_formula(8.7, 2569), 200)
]


def create_dashboard(countries_data, server, graph_type=GraphType.Normal):
    app = dash.Dash(
        name=f'COVID-19 {graph_type}',
        url_base_pathname=f'/covid19/{graph_type}/',
        server=server,
        external_scripts=[
            'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
        ])
    app.title = 'COVID-19 predictions'
    if graph_type != GraphType.Normal:
        app.title += f' on a {graph_type} graph'

    graphs = [
        dcc.Graph(id=f'{country_data.name} {graph_type}',
                  figure=country_data.create_country_figure(graph_type))
        for country_data in countries_data
    ]

    content = [
        html.H1(children='COVID-19 predictions of Boďová and Kollár'),
        html.P(children=[
            'On 2020-03-30, mathematicians Boďová and Kollár made predictions about 7 ',
            f'countries. The data available up to that point (until {PREDICTION_DATE}) is in the ',
            html.Span('green zone', style={'color': 'green'
                                           }), f'. Data coming after {PREDICTION_DATE} is in the ',
            html.Span('blue zone.', style=dict(color='blue'))
        ]),
        html.P('The black dotted line marks the predicted maximum.')
    ] + graphs

    app.layout = html.Div(children=content, style={'font-family': 'sans-serif'})
    return app


if args.country != "ALL":
    country = next(c for c in countries if c.name == args.country)
    country_data = CountryReport(args.data, country)
    country_data.create_country_figure().show()
    # plotly.offline.plot(country_data.create_country_figure(), filename='graph.html')
else:
    countries_data = [
        CountryReport(args.data, country) for country in countries
        if os.path.isfile(os.path.join(args.data, f'data-{country.name}.yaml'))
    ]

    server = Flask(__name__, template_folder='.')

    covid19_normal_app = create_dashboard(countries_data, server, GraphType.Normal)
    covid19_semilog_app = create_dashboard(countries_data, server, GraphType.SemiLog)
    covid19_loglog_app = create_dashboard(countries_data, server, GraphType.LogLog)

    @server.route("/")
    def home():
        return render_template('index.html')

    @server.route("/covid19/normal")
    def covid19_normal():
        return covid19_normal_app.index()

    @server.route("/covid19/semilog")
    def covid19_semilog():
        return covid19_semilog_app.index()

    @server.route("/covid19/loglog")
    def covid19_loglog():
        return covid19_loglog_app.index()

    server.run(host="0.0.0.0", port=8080)
