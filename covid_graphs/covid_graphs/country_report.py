from dataclasses import dataclass
from google.protobuf import text_format
import numpy as np
from pathlib import Path
from typing import List

from .formula import Formula
from .pb.country_data_pb2 import CountryData


@dataclass
class Country:
    name: str
    formulas: List[Formula]


class CountryReport:
    def __init__(self, data_dir: Path, country: Country):
        """Constructs a numpy representation of data read from 'data_dir' a given country."""
        country_data = CountryData()
        data_file = Path(data_dir / f'{country.name}.data')
        text_format.Parse(data_file.read_text(), country_data)

        self.name = country.name
        self.date_list = [
            f"{day.date.year}-{day.date.month:02d}-{day.date.day:02d}"
            for day in country_data.stats
        ]

        daily_positive = np.array([day.positive for day in country_data.stats])
        self.daily_dead = np.array([day.dead for day in country_data.stats])
        self.daily_recovered = np.array([day.recovered for day in country_data.stats])
        self.daily_active = daily_positive - self.daily_recovered - self.daily_dead

        self.cumulative_active = np.add.accumulate(self.daily_active)
        self.min_case_count = min(formula.min_case_count for formula in country.formulas)
