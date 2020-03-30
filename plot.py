#!/usr/bin/env python3
from plotly import offline
import plotly.graph_objs as go
import itertools
import numpy as np


positive = [0,  0,  0, 0,  1,  2,  2, 2,  0,  3,  11, 11, 12, 17,
            11, 25, 8, 19, 13, 41, 7, 19, 12, 10, 43, 23, 22]
accumulated = list(itertools.accumulate(positive))
accumulated = accumulated[9:]

x = np.arange(1, len(accumulated) + 1)
y_polynomial = 10 * (x ** 1.19)

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
        mode='lines+markers',
        name="Cases in Slovakia",
        line={'width': 3},
        marker={'size': 8}
    )
)

figure.add_trace(
    go.Scatter(
        x=x,
        y=y_polynomial,
        mode='lines',
        name=r'$\text{Power law fit: }10 \cdot t^{1.19}$',
        line={'width': 3},
    )
)

# offline.plot(figure, filename='graph.html')
figure.show()
