from datetime import timedelta
from enum import Enum
from itertools import accumulate, chain
import numpy as np
from pathlib import Path
from plotly.graph_objs import Figure, Layout, Scatter
import click
import click_pathlib

from .country_report import CountryReport
from .pb.simulation_results_pb2 import SimulationResults


EXTENSION = 10


class GraphType(Enum):
    Cumulative = 'cumulative'
    Daily = 'normal'

    def __str__(self):
        return self.value


class SimulationReport():
    def __init__(self, country_data_file: Path, simulation_pb2_file: Path):
        simulation_results = SimulationResults()
        simulation_results.ParseFromString(simulation_pb2_file.read_bytes())

        self.best_error, self.best_b0, self.best_gamma2 = 1e20, None, None
        for result in simulation_results.results:
            if result.summary.error > self.best_error:
                continue
            runs = result.runs
            self.simulated_positive = [run.daily_positive for run in runs]
            self.positive_days = chain.from_iterable(
                range(len(run.daily_positive)) for run in runs)
            self.daily_infected = [run.daily_infected for run in runs]
            self.infected_days = chain.from_iterable(
                range(len(run.daily_infected)) for run in runs)

            self.deltas = result.deltas
            self.best_b0 = result.b0
            self.prefix_length = result.prefix_length
            if result.HasField("alpha"):
                self.param_name = "alpha"
                self.best_param = result.alpha
            else:
                self.param_name = "gamma_2"
                self.best_param = result.gamma2

            self.best_error = result.summary.error

        print(f"b_0={self.best_b0}, {self.param_name}={self.best_param} is the best fit "
              f"for prefix_length={self.prefix_length}, error={self.best_error}")

        country_report = CountryReport(country_data_file)
        # TODO: Complete Slovak data, so that we don't have to do this dance
        self.daily_positive = np.concatenate((np.zeros(self.prefix_length),
                                             country_report.daily_positive), 0)
        first_date = country_report.dates[0] - timedelta(days=self.prefix_length)
        self.date_list = [(first_date + timedelta(days=d)).strftime('%Y-%m-%d')
                          for d in range(len(self.daily_positive) + EXTENSION)]

    def create_scatter_plot(self, graph_type=GraphType.Cumulative):
        if graph_type == GraphType.Cumulative:
            title_text = r'$\text{Total COVID-19 cases for }b_0=_b0, \_param=_alpha, prefix=_prefix$'
        else:
            title_text = r'$\text{Daily new COVID-19 cases for }b_0=_b0, \_param=_alpha, prefix=_prefix$'
        title_text = title_text.replace("_b0", f"{self.best_b0}") \
            .replace("_alpha", f"{self.best_param}") \
            .replace("_param", self.param_name).replace("_prefix", f"{self.prefix_length}")

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
                    y=transform(self.simulated_positive, graph_type),
                    mode='markers',
                    name="Simulated confirmed cases",
                    line={'width': 3},
                    marker=dict(size=10, opacity=0.04)))

        figure.add_trace(
            Scatter(
                x=self.date_list,
                y=transform([self.daily_positive], graph_type),
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


@click.command(help='COVID-19 simulation visualization for Slovakia')
@click.argument(
    "country_data",
    required=True,
    type=click_pathlib.Path(exists=True),
    # help="Protobuf file with country data"
)
@click.argument(
    "simulation_protofile",
    required=True,
    type=click_pathlib.Path(exists=True),
    # help="Protobuf file with simulation results"
)
def show_scatter_plot(country_data: Path, simulation_protofile: Path):
    SimulationReport(country_data, simulation_protofile).create_scatter_plot().show()
