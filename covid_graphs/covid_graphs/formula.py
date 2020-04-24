import datetime
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

import numpy as np

from .country_report import CountryReport


class Curve:
    def __init__(
        self,
        func: Callable[[datetime.date], float],
        start_date: datetime.date,
        end_date: datetime.date,
        label: str,
    ) -> None:
        """
        Calculates function trace for dates in a half-open interval [start_date, end_date).

        Sets the trace as properties `xs` and `ys`. Also calculates a point (x_max, y_max)
        for which the maximum is achieved.

        Note: The current design assumes the range of the plot is known at initialisation.
        """
        self.start_date = start_date
        self.end_date = end_date
        self.label = label

        self.xs = [
            start_date + datetime.timedelta(days=d)
            for d in range((end_date - start_date).days)
        ]
        self.ys = [func(x) for x in self.xs]

        idx_max = np.argmax(self.ys)
        self.x_max = self.xs[idx_max]
        self.y_max = self.ys[idx_max]


class CurveConstructor:
    @abstractmethod
    def get_curve(self, country_report: CountryReport) -> Curve:
        pass


@dataclass
class AtgCurveConstructor(CurveConstructor):
    tg: float
    a: float
    exponent: float
    min_case_count: int

    def get_curve(self, country_report: CountryReport) -> Curve:
        label = r"$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{_expon} / e^{t/_TG}$"
        label = (
            label.replace("_A", f"{self.a:.0f}")
            .replace("_TG", f"{self.tg}")
            .replace("_expon", f"{self.exponent}")
        )

        # Display values from the first day for which the number of cumulative active is
        # at least min_case_count. This day is also "day one".
        start_idx = np.argmax(country_report.cumulative_active >= self.min_case_count)
        start_date = country_report.dates[start_idx]
        day_zero = start_date - datetime.timedelta(days=1)

        # Display values until the second inflection point or one week after data finishes.
        days_till_second_ip = math.ceil(self.tg * (self.exponent + math.sqrt(self.exponent)))
        second_ip_date = start_date + datetime.timedelta(days=days_till_second_ip)
        week_after_data_ends_date = country_report.dates[-1] + datetime.timedelta(days=7)
        end_date = max(second_ip_date, week_after_data_ends_date)

        def formula(date: datetime.date):
            x = (date - day_zero).days / self.tg
            return (self.a / self.tg) * x ** self.exponent / np.exp(x)

        return Curve(func=formula, start_date=start_date, end_date=end_date, label=label)
