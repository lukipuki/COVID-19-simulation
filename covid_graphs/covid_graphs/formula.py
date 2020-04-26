import datetime
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Tuple

import numpy as np

from . import fit_atg_model
from .country_report import CountryReport


@dataclass
class Curve:
    func: Callable
    start_date: datetime.date
    display_at_least_until: datetime.date
    label: str

    def generate_trace(self, end_date: datetime.date) -> Tuple[List[datetime.date], np.ndarray]:
        """Generates trace corresponding to the half-open interval [self.start_date, end_date)"""
        raw_xs = np.arange((end_date - self.start_date).days)
        ys = np.array([self.func(x) for x in raw_xs])
        xs = [self.start_date + datetime.timedelta(days=int(x)) for x in raw_xs]
        return xs, ys


class Formula:
    @abstractmethod
    def get_curve(self, country_report: CountryReport) -> Curve:
        pass


@dataclass
class PolynomialFormula(Formula):
    a: float
    exponent: float
    min_case_count: int

    def get_curve(self, country_report: CountryReport) -> Curve:
        label = r"$_a \cdot t^{_expon}$"
        label = label.replace("_a", f"{self.a:.0f}").replace("_expon", f"{self.exponent}")

        start_idx = np.argmax(country_report.cumulative_active >= self.min_case_count)
        # start_idx marks t=1, so t=0 is one day earlier
        start_date = country_report.dates[start_idx - 1]
        display_at_least_until = country_report.dates[-1]

        return Curve(
            func=lambda x: self.a * (x ** self.exponent),
            start_date=start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )


def create_label(a: float, tg: float, exponent: float, prefix=""):
    label = (
        r"$\textrm{_prefix}\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{_expon} / e^{t/_TG}$"
    )
    return (
        label.replace("_A", f"{a:.0f}")
        .replace("_TG", f"{tg:.2f}")
        .replace("_expon", f"{exponent:.2f}")
        .replace("_prefix", prefix)
    )


@dataclass
class AtgFormula(Formula):
    tg: float
    a: float
    exponent: float
    min_case_count: int

    def get_curve(self, country_report: CountryReport) -> Curve:
        label = create_label(self.a, self.tg, self.exponent)

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

        return Curve(
            func=formula,
            start_date=start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )


@dataclass
class FittedFormula(Formula):
    # Date until which to consider data. Inclusive.
    until_date: datetime.date

    def get_curve(self, country_report: CountryReport) -> Curve:
        until_idx = country_report.dates.index(self.until_date)

        # The choice of date zero is in theory arbitrary.
        date_zero = datetime.date(2020, 2, 1)
        xs = [(date - date_zero).days for date in country_report.dates[: until_idx + 1]]
        fit = fit_atg_model.fit_atg_model(
            xs=xs, ys=country_report.cumulative_active[: until_idx + 1],
        )
        prefix = f"{self.until_date.strftime('%b %d')}: "
        label = create_label(fit.a, fit.tg, fit.exp, prefix=prefix)
        # TODO(miskosz): Remove the print when we integrate with a dashboard.
        print(fit)

        start_date = date_zero + datetime.timedelta(days=fit.t0)
        display_at_least_until = _get_display_at_least_until(
            tg=fit.tg, exp=fit.exp, start_date=start_date,
        )

        return Curve(
            func=lambda x: fit.predict(x),
            start_date=start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )


def _get_display_at_least_until(tg: float, exp: float, start_date: datetime.date) -> datetime.date:
    # Display values until the second inflection point.
    days_till_second_ip = math.ceil(tg * (exp + math.sqrt(exp)))
    return start_date + datetime.timedelta(days=days_till_second_ip)
