#!/usr/bin/env python3
from plotly import offline
import plotly.graph_objs as go
import itertools
import numpy as np
from datetime import datetime, timedelta


positive = [0,  0,  0, 0,  1,  2,  2, 2,  0,  3,  11, 11, 12, 17,
            11, 25, 8, 19, 13, 41, 7, 19, 12, 10, 43, 23, 22, 22, 27, 37]
prefix_length = 9
accumulated = list(itertools.accumulate(positive))[prefix_length:]

x = np.arange(1, len(accumulated) + 10)
y_power_law = 10 * x ** 1.20

# To add exponential decay, do something like this instead:
# x = np.arange(1, len(accumulated) + 50)
# y_power_law = (x ** 6.23) * np.exp(-x / 8.5) * 10**(-5)

date_list = [(datetime(2020, 3, 1) + timedelta(days=int(d + prefix_length))) for d in x]
date_list = [d.strftime('%Y-%m-%d') for d in date_list]

layout = go.Layout(
    xaxis=dict(
        type='log',
        autorange=True,
        title=r'$\text{Days since the 10}^\mathrm{th}\text{ case}$ '
    ),
    yaxis=dict(
        type='log',
        autorange=True,
        title='COVID-19 cases'
    ),
    hovermode='x',
    font={'size': 20}
)
figure = go.Figure(layout=layout)
figure.add_trace(
    go.Scatter(
        x=x,
        y=accumulated,
        text=date_list,
        mode='lines+markers',
        name="Cases in Slovakia",
        line={'width': 3},
        marker={'size': 8}
    )
)

figure.add_trace(
    go.Scatter(
        x=x,
        y=y_power_law,
        text=date_list,
        mode='lines',
        # name=r'$\text{Power law fit: } t^{6.23} / 1.125^t \cdot 0.000019$',
        name=r'$\text{Power law fit: } 10 \cdot t^{1.2}$',
        line={'width': 3},
    )
)

# offline.plot(figure, filename='graph.html')
figure.show()
