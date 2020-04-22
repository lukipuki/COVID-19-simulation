from abc import abstractmethod
import datetime
import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Tuple

import numpy as np

from .country_report import CountryReport


@dataclass
class Curve:
    # Mypy has trouble with `Callable[[datetime.date], float]` annotation:
    # https://github.com/python/mypy/issues/708
    func: Callable
    start_date: datetime.date  # inclusive
    end_date: datetime.date  # exclusive
    label: str

    def get_trace(self) -> Tuple[List[datetime.date], List[float]]:
        """
        Returns TODO
        """
        xs = [
            self.start_date + datetime.timedelta(days=d)
            for d in range((self.end_date - self.start_date).days)
        ]
        ys = [self.func(x) for x in xs]
        return xs, ys


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
        # more than min_case_count.
        start_idx = np.argmax(country_report.cumulative_active > self.min_case_count)
        start_date = country_report.dates[start_idx]

        # Display values until the second inflection point.
        second_ip_days = math.ceil(self.tg * (self.exponent + math.sqrt(self.exponent)))
        end_date = start_date + datetime.timedelta(days=second_ip_days)

        def formula(date: datetime.date):
            x = (date - start_date).days / self.tg
            return (self.a / self.tg) * x ** self.exponent / np.exp(x)

        return Curve(func=formula, start_date=start_date, end_date=end_date, label=label)

