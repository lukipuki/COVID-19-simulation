from collections import namedtuple
from enum import Enum
from plotly.graph_objs import Figure, Layout, Scatter
import argparse
import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import os

from .country_report import CountryReport
from .formula import ATG_formula, EvaluatedFormula, Formula, XAxisType

PREDICTION_DATE = '2020-03-29'

Country = namedtuple('Country', ['name', 'formulas'])


class GraphType(Enum):
    Normal = 'normal'
    SemiLog = 'semi-log'
    LogLog = 'log-log'

    def __str__(self):
        return self.value


countries = [
    Country('Slovakia', [Formula(lambda t: 8 * t**1.28, r'$8 \cdot t^{1.28}$', 40, 10)]),
    Country('Italy',
            [ATG_formula(9.67, 30080, 5.26), ATG_formula(7.8, 4417)]),
    Country('USA', [ATG_formula(12.8, 1406000, 4.3, 1083),
                    ATG_formula(10.2, 72329)]),
    # The following two are for the blog post
    # Country('Italy', Formula(lambda t: 2.5 * t**3, r'$2.5 \cdot t^{3}$', 60, 200)),
    # Country('Italy', Formula(lambda t: (229/1.167) * 1.167**t, r'$196 \cdot 1.167^t$', 60, 200)),
    #
    # Spain and Germany seem to have better fits as of 2020-04-06
    Country('Spain',
            [ATG_formula(6.4, 3665), ATG_formula(5.93, 1645, 6.54, 155)]),
    Country('Germany',
            [ATG_formula(6.7, 3773), ATG_formula(5.99, 5086, 5.79, 274)]),
    Country('UK', [ATG_formula(7.2, 2719)]),
    Country('Switzerland', [ATG_formula(4.19, 16.65, 7.78, 28)]),
]
 

class CountryGraph:
    """Constructs a graph for a given country"""
    def __init__(self, data_dir, country_tuple, graph_type=GraphType.Normal):
        self.graph_type = graph_type
        # Due to plotly limitations, we can only have graphs with dates on the x-axis when we
        # aren't using logs.
        axis_type = XAxisType.Dated if graph_type == GraphType.Normal else XAxisType.Numbered
        report = CountryReport(data_dir, country_tuple)
        first_idx, last_idx, self.evaluated_formulas = EvaluatedFormula.evaluate_formulas(
            country_tuple.formulas, report.cumulative_active, report.date_list[0], axis_type)
        self.name = report.name
        self.min_case_count = report.min_case_count
        self.cumulative_active = report.cumulative_active[first_idx:].copy()
        self.date_list = report.date_list[first_idx:]
        if axis_type == XAxisType.Dated:
            self.t = self.date_list
        else:
            self.t = np.arange(len(self.cumulative_active)) + 1

    def create_country_figure(self):
        shapes = [
            # Add vertical dotted lines marking the maxima
            dict(type="line",
                 yref="paper",
                 x0=evaluated_formula.t[evaluated_formula.maximal_idx],
                 y0=0,
                 x1=evaluated_formula.t[evaluated_formula.maximal_idx],
                 y1=1,
                 line=dict(width=2, dash='dot')) for evaluated_formula in self.evaluated_formulas
        ]
        try:
            prediction_date = self.date_list.index(PREDICTION_DATE)
            # Add green zone marking the data available at the prediction date.
            shapes.append(
                dict(type="rect",
                     yref="paper",
                     x0=self.t[0],
                     x1=self.t[prediction_date],
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
                            title=f'Day [starting at the {self.min_case_count}th case]',
                        ),
                        yaxis=dict(autorange=True,
                                   title=f'COVID-19 active cases in {self.name}',
                                   tickformat='.0f'),
                        height=700,
                        shapes=shapes,
                        hovermode='x',
                        font=dict(size=20),
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        figure = Figure(layout=layout)
        colors = ['rgb(31, 119, 180)', '#bcbd22', 'violet'][:len(self.evaluated_formulas)]
        for color, evaluated_formula in zip(colors, self.evaluated_formulas):
            figure.add_trace(
                Scatter(
                    x=evaluated_formula.t,
                    y=evaluated_formula.y,
                    text=evaluated_formula.date_list,
                    mode='lines',
                    name=evaluated_formula.text,
                    line={
                        'dash': 'dash',
                        'width': 2,
                        'color': color
                    },
                ))

        figure.add_trace(
            Scatter(x=self.t,
                    y=self.cumulative_active,
                    mode='lines+markers',
                    name="Active cases",
                    line={
                        'width': 3,
                        'color': 'rgb(239, 85, 59)',
                    },
                    marker={'size': 8}))

        if self.graph_type == GraphType.Normal:
            figure.update_yaxes(type="linear")
        elif self.graph_type == GraphType.SemiLog:
            figure.update_xaxes(type="linear")
            figure.update_yaxes(type="log")
        elif self.graph_type == GraphType.LogLog:
            figure.update_xaxes(type="log")
            figure.update_yaxes(type="log")
        return figure

    @staticmethod
    def create_dashboard(data_dir, server, graph_type=GraphType.Normal):
        country_graphs = [
            CountryGraph(data_dir, country, graph_type) for country in countries
            if os.path.isfile(os.path.join(data_dir, f'{country.name}.data'))
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
            dcc.Graph(id=f'{country_graph.name} {graph_type}',
                      figure=country_graph.create_country_figure())
            for country_graph in country_graphs
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
                * We've now added new prediction made on 2020-04-13 by the same authors. There's a
                  second dashed line for Italy, Spain, USA and Germany.
                * France has been excluded, since they [screwed up daily data reporting]({france_link}).
                """,
                         dangerously_allow_html=True)
        ] + graphs

        app.layout = html.Div(children=content, style={'font-family': 'sans-serif'})
        return app


def main():
    parser = argparse.ArgumentParser(description='COVID-19 country growth visualization')
    parser.add_argument('data_dir',
                        metavar='data_dir',
                        type=str,
                        help=f"Directory with country proto files")
    parser.add_argument('country', metavar='country', type=str, help=f"Country name")
    args = parser.parse_args()

    country = next(c for c in countries if c.name == args.country)
    country_graph = CountryGraph(args.data_dir, country, GraphType.Normal)
    country_graph.create_country_figure().show()
