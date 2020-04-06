#!/usr/bin/env python3
from datetime import datetime, timedelta
from enum import Enum
from itertools import chain, accumulate
import argparse
import itertools
import yaml
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout, Scatter

parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
parser.add_argument('data', metavar='data', type=str, help=f"YAML file with data")
parser.add_argument('simulated',
                    metavar='simulated',
                    type=str,
                    help=f"YAML file with simulation results")
args = parser.parse_args()

PREFIX_LENGTH = 4


class GraphType(Enum):
    Cumulative = 'cumulative'
    Daily = 'normal'

    def __str__(self):
        return self.value


def transform(list_2d, graph_type=GraphType.Cumulative):
    if graph_type == GraphType.Cumulative:
        return list(chain.from_iterable(accumulate(a) for a in list_2d))
    else:
        return list(chain.from_iterable(list_2d))


with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        real_positive = [0] * PREFIX_LENGTH + [point['positive'] for point in data]
        date_list = [point['date'] for point in data]

        first_date = datetime.strptime(date_list[0], '%Y-%m-%d')
        prefix = [(first_date + timedelta(days=d)).strftime('%Y-%m-%d')
                  for d in range(-PREFIX_LENGTH, 0)]
        date_list = prefix + date_list
        last_date = datetime.strptime(date_list[-1], '%Y-%m-%d')
        for d in range(10):
            date_list.append((last_date + timedelta(days=d + 1)).strftime('%Y-%m-%d'))

    except yaml.YAMLError as exc:
        raise exc

with open(args.simulated, 'r') as stream:
    try:
        data = yaml.load(stream, Loader=Loader)
    except yaml.YAMLError as exc:
        raise exc

    best_error, best_b0, best_gamma2 = 1e20, None, None
    for group in data:
        if "results" not in group:
            continue
        error = sum(result["error"] for result in group["results"]) / len(group["results"])
        if group["params"]["prefix_length"] == PREFIX_LENGTH and error < best_error:
            results = group["results"]
            daily_positive = [result["daily_positive"] for result in results]
            positive_days = list(
                chain.from_iterable(range(len(result["daily_positive"])) for result in results))
            daily_infected = [result["daily_infected"] for result in results]
            infected_days = list(
                chain.from_iterable(range(len(result["daily_infected"])) for result in results))

            deltas = group["params"]["deltas"]
            best_b0 = group["params"]["b0"]
            # best_gamma2 = group["params"]["gamma2"]
            best_alpha = group["params"]["alpha"]
            best_error = error

print(f"b_0={best_b0} is the best fit for prefix_length={PREFIX_LENGTH}, error={best_error}")

# title_text = r'$\text{Daily new COVID-19 cases for }b_0=_b0, \alpha=_alpha, prefix=_prefix$'
title_text = r'$\text{Total COVID-19 cases for }b_0=_b0, \alpha=_alpha, prefix=_prefix$'
title_text = title_text.replace("_b0", f"{best_b0}").replace("_alpha", f"{best_alpha}").replace(
    "_prefix", f"{PREFIX_LENGTH}")

layout = Layout(title=title_text,
                xaxis=dict(autorange=True, title='Days'),
                yaxis=dict(autorange=True, title='COVID-19 cases in Slovakia'),
                hovermode='x',
                font={'size': 15},
                legend=dict(x=0.01, y=0.99, borderwidth=1))

figure = Figure(layout=layout)
graph_type = GraphType.Cumulative

figure.add_trace(
    Scatter(x=[date_list[d] for d in positive_days],
            y=transform(daily_positive, graph_type),
            mode='markers',
            name="Simulated confirmed cases",
            line={'width': 3},
            marker=dict(size=10, opacity=0.04)))

figure.add_trace(
    Scatter(
        x=date_list,
        y=transform([real_positive], graph_type),
        text=date_list,
        mode='lines',
        name=r'Real confirmed cases',
    ))

figure.add_trace(
    Scatter(x=[date_list[d] for d in infected_days],
            y=transform(daily_infected, graph_type),
            mode='markers',
            name="Simulated total infected",
            line={'width': 3},
            marker=dict(size=10, opacity=0.04)))

figure.add_trace(
    Scatter(
        x=date_list,
        y=transform([deltas], graph_type),
        mode='lines',
        name='Expected infected',
    ))

figure.show()
