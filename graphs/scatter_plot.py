#!/usr/bin/env python3
from itertools import chain
from datetime import datetime, timedelta
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

prefix_length = 4


def accumulate(a):
    return list(itertools.accumulate(a))


with open(args.data, 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        real_positive = [0] * prefix_length + [point['positive'] for point in data]
        date_list = [point['date'] for point in data]

        first_date = datetime.strptime(date_list[0], '%Y-%m-%d')
        prefix = [(first_date + timedelta(days=d)).strftime('%Y-%m-%d')
                  for d in range(-prefix_length, 0)]
        date_list = prefix + date_list

    except yaml.YAMLError as exc:
        raise exc

with open(args.simulated, 'r') as stream:
    try:
        data = yaml.load(stream, Loader=Loader)
    except yaml.YAMLError as exc:
        raise exc

    best_error, best_b0, best_gamma2 = 1e10, None, None
    for group in data:
        if "results" not in group:
            continue
        if group["params"]["prefix_length"] == prefix_length and sum(
                result["error"] for result in group["results"]) < best_error:
            results = group["results"]
            best_error = sum(result["error"] for result in results)
            daily_positive = [result["daily_positive"] for result in results]
            cumulative_daily_positive = [accumulate(result["daily_positive"]) for result in results]
            daily_infected = [
                list(itertools.accumulate(result["daily_infected"])) for result in results
            ]
            days = [range(len(result["daily_positive"])) for result in results]
            deltas = group["params"]["deltas"]
            best_b0 = group["params"]["b0"]
            # best_gamma2 = group["params"]["gamma2"]
            best_alpha = group["params"]["alpha"]

            daily_positive, daily_infected, days, cumulative_daily_positive = map(
                lambda v: list(chain.from_iterable(v)),
                [daily_positive, daily_infected, days, cumulative_daily_positive])

cumulative_real_positive = accumulate(real_positive)

print(f"b_0={best_b0} is the best fit for prefix_length={prefix_length}")

# title_text = r'$\text{Daily new COVID-19 cases for }b_0=_b0, \alpha=_alpha, prefix=_prefix$'
title_text = r'$\text{Total COVID-19 cases for }b_0=_b0, \alpha=_alpha, prefix=_prefix$'
title_text = title_text.replace("_b0", f"{best_b0}").replace("_alpha", f"{best_alpha}").replace(
    "_prefix", f"{prefix_length}")

layout = Layout(title=title_text,
                xaxis=dict(autorange=True, title='Days'),
                yaxis=dict(autorange=True, title='COVID-19 cases in Slovakia'),
                hovermode='x',
                font={'size': 15},
                legend=dict(x=0.01, y=0.99, borderwidth=1))

figure = Figure(layout=layout)
figure.add_trace(
    Scatter(
        x=[date_list[d] for d in days],
        y=cumulative_daily_positive,
        # y=daily_positive,
        text=date_list,
        mode='markers',
        name="Simulated daily cases",
        line={'width': 3},
        marker=dict(size=10, opacity=0.07)))

figure.add_trace(
    Scatter(
        x=date_list,
        y=cumulative_real_positive,
        # y=real_positive,
        text=date_list,
        mode='lines',
        name=r'Real daily cases',
    ))

figure.add_trace(Scatter(
    x=date_list,
    y=deltas,
    mode='lines',
    name='Expected infected',
))

figure.show()
