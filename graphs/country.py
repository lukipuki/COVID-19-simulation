#!/usr/bin/env python3
from collections import namedtuple
from datetime import datetime, timedelta
from enum import Enum
from plotly.graph_objs import Figure, Layout, Scatter
import argparse
import dash
import dash_core_components as dcc
import dash_html_components as html
import math
import numpy as np
import os
import yaml

EXPONENT = 6.23
PREDICTION_DATE = '2020-03-29'

Country = namedtuple('Country', ['name', 'formulas', 'case_count'])
Formula = namedtuple('Formula', ['lambd', 'text', 'maximal_day', 'second_ip_day'])


class GraphType(Enum):
    Normal = 'normal'
    SemiLog = 'semi-log'
    LogLog = 'log-log'

    def __str__(self):
        return self.value


def ATG_formula(TG, A):
    text = r'$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{6.23} / e^{t/_TG}$'
    text = text.replace("_A", f"{A}").replace("_TG", f"{TG}")
    # Second inflection point day
    second_ip_day = math.ceil(TG * (EXPONENT + math.sqrt(EXPONENT)))
    return Formula(lambda t: (A / TG) * (t / TG)**EXPONENT / np.exp(t / TG), text, EXPONENT * TG,
                   second_ip_day)


countries = [
    Country('Slovakia', [Formula(lambda t: 8 * t**1.28, r'$8 \cdot t^{1.28}$', 40, 40)], 10),
    Country('Italy', [ATG_formula(7.8, 4417)], 200),
    Country('USA', [ATG_formula(10.2, 72329)], 200),
    # The following two are for the blog post
    # Country('Italy', Formula(lambda t: 2.5 * t**3, r'$2.5 \cdot t^{3}$', 60, 60), 200),
    # Country('Italy', Formula(lambda t: (229/1.167) * 1.167**t, r'$196 \cdot 1.167^t$', 60, 60), 200),
    #
    # Spain and Germany seem to have better fits as of 2020-04-06
    Country('Spain', [ATG_formula(6.4, 3665), ATG_formula(6.2, 3120)], 200),
    Country('Germany', [ATG_formula(6.7, 3773), ATG_formula(6.3, 2850)], 200),
    Country('UK', [ATG_formula(7.2, 2719)], 200),
    Country('France', [ATG_formula(6.5, 1961)], 200),
    Country('Iran', [ATG_formula(8.7, 2569)], 200)
]


class CountryReport:
    def __init__(self, data_dir, country_basic):
        self.name = country_basic.name
        self.formulas = country_basic.formulas
        self.data_dir = os.path.join(data_dir, f'data-{self.name}.yaml')
        with open(self.data_dir, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                positive = np.array([point['positive'] for point in data])
                self.dead = np.array([point['dead'] for point in data])
                self.recovered = np.array([point['recovered'] for point in data])
                self.active = positive - self.recovered - self.dead
                self.date_list = [point['date'] for point in data]
            except yaml.YAMLError as exc:
                raise exc

        self.case_count = country_basic.case_count
        self.cumulative_active = np.array(
            list(filter(lambda x: x >= self.case_count, np.add.accumulate(self.active))))
        self.date_list = self.date_list[len(self.active) - len(self.cumulative_active):]
        self.x = np.arange(1, max(f.second_ip_day for f in self.formulas) + 1)
        self.y = [formula.lambd(self.x) for formula in self.formulas]
        self.maximal_dates = [y.argmax() for y in self.y]

        self.last_date = datetime.strptime(self.date_list[-1], '%Y-%m-%d')
        self.date_list += [(self.last_date + timedelta(days=d)).strftime('%Y-%m-%d')
                           for d in range(1,
                                          len(self.x) - len(self.date_list) + 1)]
        self.x = self.x[:len(self.date_list)]

    def create_country_figure(self, graph_type=GraphType.Normal):

        x = self.x if graph_type != GraphType.Normal else self.date_list
        shapes = [
            dict(type="line",
                 yref="paper",
                 x0=x[maximal_date],
                 y0=0,
                 x1=x[maximal_date],
                 y1=1,
                 line=dict(width=2, dash='dot')) for maximal_date in self.maximal_dates
        ]
        try:
            prediction_date = self.date_list.index(PREDICTION_DATE)
            shapes.append(
                dict(type="rect",
                     yref="paper",
                     x0=x[0],
                     x1=x[prediction_date],
                     y0=0,
                     y1=1,
                     fillcolor="LightGreen",
                     opacity=0.5,
                     layer="below",
                     line_width=0))
        except ValueError:
            pass

        layout = Layout(title=f"Active cases in {self.name}",
                        xaxis=dict(
                            autorange=True,
                            title=f'Day [starting at the {self.case_count}th case]',
                        ),
                        yaxis=dict(autorange=True, title='COVID-19 active cases', tickformat='.0f'),
                        height=700,
                        shapes=shapes,
                        hovermode='x',
                        font=dict(size=20),
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        figure = Figure(layout=layout)
        colors = ['rgb(31, 119, 180)', '#bcbd22', 'violet'][:len(self.formulas)]
        for color, formula in zip(colors, self.formulas):
            figure.add_trace(
                Scatter(
                    x=x,
                    y=formula.lambd(self.x),
                    text=self.date_list,
                    mode='lines',
                    name=formula.text,
                    line={
                        'dash': 'dash',
                        'width': 2,
                        'color': color
                    },
                ))

        figure.add_trace(
            Scatter(x=x,
                    y=self.cumulative_active,
                    mode='lines+markers',
                    name=f"Active cases",
                    line={
                        'width': 3,
                        'color': 'rgb(239, 85, 59)',
                    },
                    marker={'size': 8}))

        if graph_type == GraphType.Normal:
            figure.update_yaxes(type="linear")
        elif graph_type == GraphType.SemiLog:
            figure.update_xaxes(type="linear")
            figure.update_yaxes(type="log")
        elif graph_type == GraphType.LogLog:
            figure.update_xaxes(type="log")
            figure.update_yaxes(type="log")
        return figure

    @staticmethod
    def create_dashboard(data_dir, server, graph_type=GraphType.Normal):
        country_reports = [
            CountryReport(data_dir, country) for country in countries
            if os.path.isfile(os.path.join(data_dir, f'data-{country.name}.yaml'))
        ]

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
            for country_data in country_reports
        ]

        prediction_link = "https://www.facebook.com/permalink.php?"\
            "story_fbid=10113020662000793&id=2247644"
        france_link = "https://www.reuters.com/article/us-health-coronavirus-france-toll/" \
            "french-coronavirus-cases-jump-above-chinas-after-including-nursing-home-tally-idUSKBN21L3BG"
        content = [
            html.H1(children='COVID-19 predictions of Boďová and Kollár'),
            html.P(children=[
                'On 2020-03-30, mathematicians Katarína Boďová and Richard Kollár ',
                html.A('made predictions about 7 countries', href=prediction_link),
                f'. The data available up to that point (until {PREDICTION_DATE}) is in the ',
                html.Span('green zone', style={'color': 'green'}),
                f'. Data coming after {PREDICTION_DATE} is in the ',
                html.Span('blue zone.', style=dict(color='blue')),
                dcc.Markdown("""
                The predicted number of active cases <em>N</em>(<em>t</em>) on day <em>t</em> is
                calculated as follows (constants <em>A</em> and <em>T</em><sub><em>G</em></sub>
                are country-specific):
                <em>N</em>(<em>t</em>) = (<em>A</em>/<em>T</em><sub><em>G</em></sub>) ⋅
                (<em>t</em>/<em>T</em><sub><em>G</em></sub>)<sup>6.23</sup> /
                e<sup><em>t</em>/<em>T</em><sub><em>G</em></sub></sup>
                """,
                             dangerously_allow_html=True)
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
                * 8 days after the prediction, it's apparent that Spain and Germany do better
                  than predicted. We've now added a second curve with <em>T<sub>G</sub></em> equal
                  to 6.2 and 6.3 respectively.
                * France included data [from nursing homes all at once on
                  2020-04-04]({france_link}), which makes the graph look strange.
                """,
                         dangerously_allow_html=True)
        ] + graphs

        app.layout = html.Div(children=content, style={'font-family': 'sans-serif'})
        return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='COVID-19 country growth visualization')
    parser.add_argument('data_dir', metavar='data_dir', type=str, help=f"Directory with YAML files")
    parser.add_argument('country', metavar='country', type=str, help=f"Country name or 'ALL'")
    args = parser.parse_args()

    country = next(c for c in countries if c.name == args.country)
    country_data = CountryReport(args.data_dir, country)
    country_data.create_country_figure().show()
