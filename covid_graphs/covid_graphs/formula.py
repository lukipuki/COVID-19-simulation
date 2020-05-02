import datetime
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, List

import numpy as np

from . import fit_atg_model
from .country_report import CountryReport


@dataclass
class Trace:
    xs: List[datetime.date]
    ys: np.ndarray
    max_value_date: datetime.date
    max_value: float

    # The label uses a placeholder %PREDICTION_DATE%.
    label: str


@dataclass
class TraceGenerator:
    func: Callable
    start_date: datetime.date
    display_at_least_until: datetime.date
    label: str

    """
    Trace is created from a function `func(x)`, which has x=0 at `start_date`. It's only defined for
    x >= 0.
    """

    def generate_trace(self, display_until: datetime.date) -> Trace:
        """Generates trace corresponding to the closed interval [self.start_date, end_date]"""
        raw_xs = np.arange((display_until - self.start_date).days + 1)
        ys = np.array([self.func(x) for x in raw_xs])
        xs = [self.start_date + datetime.timedelta(days=int(x)) for x in raw_xs]
        idx_max = ys.argmax()
        max_value_date, max_value = xs[idx_max], ys[idx_max]
        return Trace(xs, ys, max_value_date, max_value, label=self.label)


class Formula:
    @abstractmethod
    def get_trace_generator(self, country_report: CountryReport) -> TraceGenerator:
        pass


@dataclass
class PolynomialFormula(Formula):
    a: float
    exponent: float
    min_case_count: int

    def get_trace_generator(self, country_report: CountryReport) -> TraceGenerator:
        label = r"$_a \cdot t^{_expon}$"
        label = label.replace("_a", f"{self.a:.0f}").replace("_expon", f"{self.exponent}")

        start_idx = np.argmax(country_report.cumulative_active >= self.min_case_count)
        # start_idx marks t=1, so t=0 is one day earlier
        start_date = country_report.dates[start_idx - 1]
        display_at_least_until = country_report.dates[-1]

        return TraceGenerator(
            func=lambda x: self.a * (x ** self.exponent),
            start_date=start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )


def _create_atg_label(prefix: str, tg: float, alpha: float) -> str:
    return f"{prefix} %PREDICTION_DATE% (α={alpha:.2f}, T<sub>G</sub>={tg:.2f})"


@dataclass
class AtgFormula(Formula):
    tg: float
    a: float
    exponent: float
    min_case_count: int

    def get_trace_generator(self, country_report: CountryReport) -> TraceGenerator:
        label = _create_atg_label(prefix="Boďová and Kollár", tg=self.tg, alpha=self.exponent)

        # Display values from the first day for which the number of cumulative active is
        # at least min_case_count. This day is also "day one".
        start_idx = np.argmax(country_report.cumulative_active >= self.min_case_count)
        start_date = country_report.dates[start_idx - 1]
        display_at_least_until = _get_display_at_least_until(
            tg=self.tg, exp=self.exponent, start_date=start_date,
        )

        def formula(x: float):
            x /= self.tg
            return (self.a / self.tg) * x ** self.exponent / np.exp(x)

        return TraceGenerator(
            func=formula,
            start_date=start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )


@dataclass
class FittedFormula(Formula):
    # Date until which to consider data. Inclusive.
    until_date: datetime.date

    def get_trace_generator(self, country_report: CountryReport) -> TraceGenerator:
        until_idx = country_report.dates.index(self.until_date)

        # The choice of date zero is in theory arbitrary.
        date_zero = country_report.dates[0]
        xs = [(date - date_zero).days for date in country_report.dates[: until_idx + 1]]
        fit = fit_atg_model.fit_atg_model(
            xs=xs, ys=country_report.cumulative_active[: until_idx + 1],
        )
        label = _create_atg_label("Daily prediction", tg=fit.tg, alpha=fit.exp)

        # Counterintuitively, `date` + `timedelta` results in `date`.
        whole_day_offset = np.floor(fit.t0)
        start_date = date_zero + datetime.timedelta(days=whole_day_offset)
        display_at_least_until = _get_display_at_least_until(
            tg=fit.tg, exp=fit.exp, start_date=start_date,
        )

        return TraceGenerator(
            func=lambda x: fit.predict(x + whole_day_offset),
            start_date=start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )


def _get_display_at_least_until(tg: float, exp: float, start_date: datetime.date) -> datetime.date:
    # Display values until the second inflection point.
    days_till_second_ip = math.ceil(tg * (exp + math.sqrt(exp)))
    return start_date + datetime.timedelta(days=days_till_second_ip)
