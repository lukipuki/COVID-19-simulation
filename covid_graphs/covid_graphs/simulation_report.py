from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

from google.protobuf import message

from .pb.simulation_results_pb2 import SimulationResults


class GrowthType(Enum):
    Exponential = "exponential"
    Polynomial = "polynomial"

    def __str__(self):
        return self.value


@dataclass
class SimulationReport:
    daily_positive: List[List[int]]
    daily_infected: List[List[int]]
    deltas: List[float]
    b0: int
    prefix_length: int
    error: float
    # We want to store either alpha or gamma2. We could have two classes, one having alpha and the
    # other gamma2 (in C++ I would make a template). Don't know what's best practice in these
    # situations in Python.
    param: float
    growth_type: GrowthType


def create_simulation_reports(simulation_pb2_file: Path) -> List[SimulationReport]:
    """Parses a proto file and creates a list of SimulationReport out of it"""
    if not simulation_pb2_file.is_file():
        raise FileNotFoundError
    simulation_results = SimulationResults()
    try:
        simulation_results.ParseFromString(simulation_pb2_file.read_bytes())
    except message.DecodeError:
        raise ValueError(f"Cannot parse {simulation_pb2_file}")

    reports = []
    for result in simulation_results.results:
        daily_positive = [run.daily_positive for run in result.runs]
        daily_infected = [run.daily_infected for run in result.runs]
        if result.HasField("alpha"):
            growth_type = GrowthType.Polynomial
            param = result.alpha
        else:
            growth_type = GrowthType.Exponential
            param = result.gamma2

        reports.append(
            SimulationReport(
                daily_positive,
                daily_infected,
                result.deltas,
                result.b0,
                result.prefix_length,
                result.summary.error,
                param,
                growth_type,
            )
        )
    return reports
