from collections import namedtuple
from datetime import datetime, timedelta
from enum import Enum
from plotly.graph_objs import Figure, Layout, Scatter
import math
import numpy as np
import os
import yaml

EXPONENT = 6.23
PREDICTION_DATE = '2020-03-29'

Country = namedtuple('Country', ['name', 'formula', 'case_count'])
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



class CountryGraph:
    def __init__(self, path, country_basic):
        self.name = country_basic.name
        self.formula = country_basic.formula
        self.path = os.path.join(path, f'data-{self.name}.yaml')
        with open(self.path, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                positive = np.array([point['positive'] for point in data])
                self.dead = np.array([point['dead'] for point in data])
                self.recovered = np.array([point['recovered'] for point in data])
                self.active = positive - self.recovered - self.dead
                self.date_list = [point['date'] for point in data]
            except yaml.YAMLError as exc:
                raise exc

        self.cumulative_active = np.array(
            list(filter(lambda x: x >= country_basic.case_count, np.add.accumulate(self.active))))
        self.date_list = self.date_list[len(self.active) - len(self.cumulative_active):]
        self.x = np.arange(1, self.formula.second_ip_day)
        self.y = country_basic.formula.lambd(self.x)
        self.maximal_date = self.y.argmax()

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
                 x0=x[self.maximal_date],
                 y0=0,
                 x1=x[self.maximal_date],
                 y1=1,
                 line=dict(width=2, dash='dot'))
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
                            title=r'$\text{Days since the 200}^\mathrm{th}\text{ case}$',
                        ),
                        yaxis=dict(autorange=True, title='COVID-19 active cases', tickformat='.0f'),
                        height=700,
                        shapes=shapes,
                        hovermode='x',
                        font={'size': 15},
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        figure = Figure(layout=layout)
        figure.add_trace(
            Scatter(
                x=x,
                y=self.y,
                text=self.date_list,
                mode='lines',
                name=self.formula.text,
                line={
                    'dash': 'dash',
                    'width': 3,
                    'color': 'rgb(31, 119, 180)',
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
