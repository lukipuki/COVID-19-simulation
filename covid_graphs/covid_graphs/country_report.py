from dataclasses import dataclass
from google.protobuf import text_format
import numpy as np
from pathlib import Path
from typing import List

from .predictions import CountryPrediction
from .pb.country_data_pb2 import CountryData


class CountryReport:
    def __init__(self, data_dir: Path, country_predictions: List[CountryPrediction]):
        """Constructs a numpy representation of data read from 'data_dir' a given country."""

        # TODO: Check that there is only one country.
        country_name = country_predictions[0].country
        data_file_path = Path(data_dir / f'{country_name}.data')

        country_data = CountryData()
        text_format.Parse(data_file_path.read_text(), country_data)

        self.name = country_name
        self.date_list = [
            f"{day.date.year}-{day.date.month:02d}-{day.date.day:02d}"
            for day in country_data.stats
        ]

        daily_positive = np.array([day.positive for day in country_data.stats])
        self.daily_dead = np.array([day.dead for day in country_data.stats])
        self.daily_recovered = np.array([day.recovered for day in country_data.stats])
        self.daily_active = daily_positive - self.daily_recovered - self.daily_dead

        self.cumulative_active = np.add.accumulate(self.daily_active)
        self.min_case_count = min(prediction.formula.min_case_count for prediction in country_predictions)
