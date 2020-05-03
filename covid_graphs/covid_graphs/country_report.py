import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
from google.protobuf import text_format  # type: ignore

from .pb.country_data_pb2 import CountryData


@dataclass
class CountryReport:
    short_name: str
    long_name: str
    dates: List[datetime.date]
    daily_positive: np.ndarray
    daily_dead: np.ndarray
    daily_recovered: np.ndarray
    daily_active: np.ndarray
    cumulative_active: np.ndarray


def create_report(country_data_file: Path) -> CountryReport:
    """Constructs a numpy representation of data read from 'data_dir' a given country."""
    country_data = CountryData()
    text_format.Parse(country_data_file.read_text(), country_data)

    long_name = country_data.name
    short_name = country_data.short_name
    dates = [
        datetime.date(day=day.date.day, month=day.date.month, year=day.date.year)
        for day in country_data.stats
    ]

    daily_positive = np.array([day.positive for day in country_data.stats])
    daily_dead = np.array([day.dead for day in country_data.stats])
    daily_recovered = np.array([day.recovered for day in country_data.stats])
    daily_active = daily_positive - daily_recovered - daily_dead

    cumulative_active = np.add.accumulate(daily_active)

    return CountryReport(
        short_name,
        long_name,
        dates,
        daily_positive,
        daily_dead,
        daily_recovered,
        daily_active,
        cumulative_active,
    )
