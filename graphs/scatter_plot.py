#!/usr/bin/env python3
from datetime import datetime, timedelta
from enum import Enum
from itertools import chain, accumulate
import argparse
import yaml
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout, Scatter

parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
parser.add_argument('country_data',
                    metavar='country_data',
                    type=str,
                    help=f"YAML file with country data")
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


with open(args.country_data, 'r') as stream:
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


class SimulationReport():
    def __init__(self, simulation_yaml):
        with open(simulation_yaml, 'r') as stream:
            try:
                data = yaml.load(stream, Loader=Loader)
            except yaml.YAMLError as exc:
                raise exc

            self.best_error, self.best_b0, self.best_gamma2 = 1e20, None, None
            for group in data:
                if "results" not in group:
                    continue
                error = sum(result["error"] for result in group["results"]) / len(group["results"])
                if group["params"]["prefix_length"] == PREFIX_LENGTH and error < self.best_error:
                    results = group["results"]
                    self.daily_positive = [result["daily_positive"] for result in results]
                    self.positive_days = list(
                        chain.from_iterable(
                            range(len(result["daily_positive"])) for result in results))
                    self.daily_infected = [result["daily_infected"] for result in results]
                    self.infected_days = list(
                        chain.from_iterable(
                            range(len(result["daily_infected"])) for result in results))

                    self.deltas = group["params"]["deltas"]
                    self.best_b0 = group["params"]["b0"]
                    # TODO: support both
                    # self.best_gamma2 = group["params"]["gamma2"]
                    self.best_alpha = group["params"]["alpha"]
                    self.best_error = error
            print(
                f"b_0={self.best_b0} is the best fit for prefix_length={PREFIX_LENGTH}, "
                f"error={self.best_error}"
            )

    def create_scatter_plot(self, graph_type=GraphType.Cumulative):
        if graph_type == GraphType.Cumulative:
            title_text = r'$\text{Total COVID-19 cases for }b_0=_b0, \alpha=_alpha, prefix=_prefix$'
        else:
            title_text = r'$\text{Daily new COVID-19 cases for }b_0=_b0, \alpha=_alpha, prefix=_prefix$'
        title_text = title_text.replace("_b0", f"{self.best_b0}").replace(
            "_alpha", f"{self.best_alpha}").replace("_prefix", f"{PREFIX_LENGTH}")

        layout = Layout(title=title_text,
                        xaxis=dict(autorange=True, title='Days'),
                        yaxis=dict(autorange=True, title='COVID-19 cases in Slovakia'),
                        hovermode='x',
                        font={'size': 15},
                        legend=dict(x=0.01, y=0.99, borderwidth=1))

        figure = Figure(layout=layout)

        figure.add_trace(
            Scatter(x=[date_list[d] for d in self.positive_days],
                    y=transform(self.daily_positive, graph_type),
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
            Scatter(x=[date_list[d] for d in self.infected_days],
                    y=transform(self.daily_infected, graph_type),
                    mode='markers',
                    name="Simulated total infected",
                    line={'width': 3},
                    marker=dict(size=10, opacity=0.04)))

        figure.add_trace(
            Scatter(
                x=date_list,
                y=transform([self.deltas], graph_type),
                mode='lines',
                name='Expected infected',
            ))

        return figure


SimulationReport(args.simulated).create_scatter_plot().show()
