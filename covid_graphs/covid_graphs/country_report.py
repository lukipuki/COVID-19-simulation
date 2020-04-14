import numpy as np
import os
from google.protobuf import text_format
from .pb.country_data_pb2 import CountryData


class CountryReport:
    """Constructs a numpy representation of data read from 'data_dir' a given country."""
    def __init__(self, data_dir, country_tuple):
        with open(os.path.join(data_dir, f'{country_tuple.name}.data'), "rb") as f:
            country_data = CountryData()
            text_format.Parse(f.read(), country_data)
            self.name = country_data.name
            positive = np.array([day.positive for day in country_data.stats])
            self.dead = np.array([day.dead for day in country_data.stats])
            self.recovered = np.array([day.recovered for day in country_data.stats])
            self.active = positive - self.recovered - self.dead
            self.date_list = [
                f"{day.date.year}-{day.date.month:02d}-{day.date.day:02d}"
                for day in country_data.stats
            ]

        self.cumulative_active = np.add.accumulate(self.active)
        self.min_case_count = min(formula.min_case_count for formula in country_tuple.formulas)
