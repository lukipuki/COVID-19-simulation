from dataclasses import dataclass
from datetime import datetime
from google.protobuf import text_format # type: ignore
import numpy as np
from pathlib import Path

from .pb.country_data_pb2 import CountryData


class CountryReport:
    def __init__(self, country_data_file: Path):
        """Constructs a numpy representation of data read from 'data_dir' a given country."""
        country_data = CountryData()
        text_format.Parse(country_data_file.read_text(), country_data)

        self.name = country_data.name
        self.dates = [
            datetime(day=day.date.day, month=day.date.month, year=day.date.year)
            for day in country_data.stats
        ]
        self.dates_str = list(map(lambda d: d.strftime("%Y-%m-%d"), self.dates))

        self.daily_positive = np.array([day.positive for day in country_data.stats])
        self.daily_dead = np.array([day.dead for day in country_data.stats])
        self.daily_recovered = np.array([day.recovered for day in country_data.stats])
        self.daily_active = self.daily_positive - self.daily_recovered - self.daily_dead

        self.cumulative_active = np.add.accumulate(self.daily_active)
