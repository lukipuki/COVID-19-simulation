#!/usr/bin/env python3
from datetime import datetime, timedelta
from enum import Enum
from itertools import accumulate
from itertools.chain import from_iterable
import argparse
import yaml
from simulation_results_pb2 import SimulationResults
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout, Scatter

PREFIX_LENGTH = 4


class GraphType(Enum):
    Cumulative = 'cumulative'
    Daily = 'normal'

    def __str__(self):
        return self.value


class SimulationReport():
    def __init__(self, simulation_pb2_file, country_yaml):
        with open(simulation_pb2_file, 'rb') as stream:
            simulation_results = SimulationResults()
            simulation_results.ParseFromString(stream.read())

            self.best_error, self.best_b0, self.best_gamma2 = 1e20, None, None
            for result in simulation_results.results:
                if result.prefix_length != PREFIX_LENGTH or result.summary.error > self.best_error:
                    continue
                runs = result.runs
                self.daily_positive = [run.daily_positive for run in runs]
                self.positive_days = chain.from_iterable(
                    range(len(run.daily_positive)) for run in runs)
                self.daily_infected = [run.daily_infected for run in runs]
                self.infected_days = chain.from_iterable(
                    range(len(run.daily_infected)) for run in runs)

                self.deltas = result.deltas
                self.best_b0 = result.b0
                # TODO: support both
                # self.best_gamma2 = result.gamma2
                self.best_alpha = result.alpha
                self.best_error = result.summary.error

            print(f"b_0={self.best_b0} is the best fit for prefix_length={PREFIX_LENGTH}, "
                  f"error={self.best_error}")

        with open(country_yaml, 'r') as stream:
            data = yaml.safe_load(stream)
            self.real_positive = [0] * PREFIX_LENGTH + [point['positive'] for point in data]
            date_list = [point['date'] for point in data]

            first_date = datetime.strptime(date_list[0], '%Y-%m-%d')
            prefix = [(first_date + timedelta(days=d)).strftime('%Y-%m-%d')
                      for d in range(-PREFIX_LENGTH, 0)]
            date_list = prefix + date_list
            last_date = datetime.strptime(date_list[-1], '%Y-%m-%d')
            for d in range(10):
                date_list.append((last_date + timedelta(days=d + 1)).strftime('%Y-%m-%d'))
            self.date_list = date_list

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

        def transform(list_2d, graph_type=GraphType.Cumulative):
            if graph_type == GraphType.Cumulative:
                return list(chain.from_iterable(accumulate(a) for a in list_2d))
            else:
                return list(chain.from_iterable(list_2d))

        figure.add_trace(
            Scatter(x=[self.date_list[d] for d in self.positive_days],
                    y=transform(self.daily_positive, graph_type),
                    mode='markers',
                    name="Simulated confirmed cases",
                    line={'width': 3},
                    marker=dict(size=10, opacity=0.04)))

        figure.add_trace(
            Scatter(
                x=self.date_list,
                y=transform([self.real_positive], graph_type),
                text=self.date_list,
                mode='lines',
                name=r'Real confirmed cases',
            ))

        figure.add_trace(
            Scatter(x=[self.date_list[d] for d in self.infected_days],
                    y=transform(self.daily_infected, graph_type),
                    mode='markers',
                    name="Simulated total infected",
                    line={'width': 3},
                    marker=dict(size=10, opacity=0.04)))

        figure.add_trace(
            Scatter(
                x=self.date_list,
                y=transform([self.deltas], graph_type),
                mode='lines',
                name='Expected infected',
            ))

        return figure


if __name__ == '__main__':
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

    SimulationReport(args.simulated, args.country_data).create_scatter_plot().show()
