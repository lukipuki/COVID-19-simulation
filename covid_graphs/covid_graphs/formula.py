import datetime
import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Tuple

import numpy as np

from .country_report import CountryReport


@dataclass
class GraphFunction:
    # Mypy has trouble with `Callable[[int], float]` annotation:
    # https://github.com/python/mypy/issues/708
    func: Callable
    min_t: int  # inclusive
    max_t: int  # exclusive
    label: str

    def get_trace(self) -> Tuple[List[int], List[float]]:
        """
        Returns TODO
        """
        xs = list(range(self.min_t, self.max_t))
        ys = [self.func(x) for x in xs]
        return xs, ys


@dataclass
class AtgFormula:
    tg: float
    a: float
    exponent: float
    min_case_count: int

    def get_graph_function(self, country_report: CountryReport) -> GraphFunction:
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
        min_t = epoch_days(start_date)

        # Display values until the second inflection point.
        second_ip_days = math.ceil(self.tg * (self.exponent + math.sqrt(self.exponent)))
        max_t = epoch_days(start_date + datetime.timedelta(days=second_ip_days))

        formula = (
            lambda t: (self.a / self.tg)
            * ((t - min_t) / self.tg) ** self.exponent
            / np.exp((t - min_t) / self.tg)
        )
        return GraphFunction(func=formula, min_t=min_t, max_t=max_t, label=label)


def epoch_days(date: datetime.date):
    """
    TODO
    """
    return (date - datetime.datetime(1970, 1, 1)).days
