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
        TODO
        [start_date, end_date)
        """
        self._func = func
        self.start_date = start_date
        self.end_date = end_date
        self.label = label
        self._xs: Optional[List[datetime.date]] = None
        self._ys: Optional[List[float]] = None

    def get_trace(
        self, plot_start_date: datetime.date, plot_end_date: datetime.date
    ) -> Tuple[List[datetime.date], List[float]]:
        self._xs = [
            plot_start_date + datetime.timedelta(days=d)
            for d in range((plot_end_date - plot_start_date).days)
        ]
        self._ys = [self._func(x) for x in self._xs]
        return self._xs, self._ys

    def get_maximum(self) -> Tuple[datetime.date, float]:
        """
        Return TODO
        """
        if self._xs is None or self._ys is None:
            raise ValueError("Must call get_trace() first.")
        idx = np.argmax(self._ys)
        return self._xs[idx], self._ys[idx]


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

        # Display values until the second inflection point.
        second_ip_days = math.ceil(self.tg * (self.exponent + math.sqrt(self.exponent)))
        end_date = start_date + datetime.timedelta(days=second_ip_days)

        def formula(date: datetime.date):
            x = (date - day_zero).days / self.tg
            return (self.a / self.tg) * x ** self.exponent / np.exp(x)

        return Curve(func=formula, start_date=start_date, end_date=end_date, label=label)
