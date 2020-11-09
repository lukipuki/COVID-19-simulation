import datetime
import math
from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np

from . import fit_atg_model
from .country_report import CountryReport
from .fit_atg_model import AtgModelFit
from .pb.atg_prediction_pb2 import AtgParameters


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
    """
    Trace is created from a function `func(x)`, which has x=0 at `start_date`. It's only defined for
    x >= 0.
    """

    func: Callable
    start_date: datetime.date
    display_at_least_until: datetime.date
    label: str

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

    @abstractmethod
    def get_peak(self, country_report: CountryReport) -> Optional[datetime.datetime]:
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

    def get_peak(self, country_report: CountryReport) -> Optional[datetime.datetime]:
        return None


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
            tg=self.tg,
            exp=self.exponent,
            start_date=start_date,
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

    def get_peak(self, country_report: CountryReport) -> Optional[datetime.datetime]:
        start_idx = np.argmax(country_report.cumulative_active >= self.min_case_count)
        start_date = country_report.dates[start_idx - 1]

        return datetime.datetime.combine(
            start_date, datetime.datetime.min.time()
        ) + datetime.timedelta(days=self.exponent * self.tg)


def _set_proto_date(proto_date, date: datetime.date) -> None:
    proto_date.year = date.year
    proto_date.month = date.month
    proto_date.day = date.day


@dataclass
class FittedFormula(Formula):
    """
    The model ('fit') was fitted using data until 'last_data_date'.
    The trace created by this model starts at 'start_date' shifted by 'fit.t0' days ('fit.t0' is
    less than 1).
    """

    fit: AtgModelFit
    start_date: datetime.date
    last_data_date: datetime.date

    def serialize(self):
        atg_parameters = AtgParameters()

        atg_parameters.alpha = self.fit.exp
        atg_parameters.tg = self.fit.tg
        atg_parameters.offset = self.fit.t0
        atg_parameters.a = self.fit.a

        _set_proto_date(atg_parameters.last_data_date, self.last_data_date)
        _set_proto_date(atg_parameters.start_date, self.start_date)

        return atg_parameters

    def get_trace_generator(self, country_report: CountryReport) -> TraceGenerator:
        display_at_least_until = _get_display_at_least_until(
            tg=self.fit.tg,
            exp=self.fit.exp,
            start_date=self.start_date,
        )
        label = _create_atg_label("Daily prediction", tg=self.fit.tg, alpha=self.fit.exp)
        return TraceGenerator(
            func=self.fit.predict,
            start_date=self.start_date,
            display_at_least_until=display_at_least_until,
            label=label,
        )

    def get_peak(self, country_report: Optional[CountryReport] = None) -> datetime.datetime:
        return datetime.datetime.combine(
            self.start_date, datetime.datetime.min.time()
        ) + datetime.timedelta(days=self.fit.exp * self.fit.tg + self.fit.t0)


def fit_country_data(country_report: CountryReport, last_data_date: datetime.date) -> FittedFormula:
    """
    last_data_date: Date until which to consider data. Inclusive.
    country_report: CountryReport containing epidemiological data for the country.
    """
    until_idx = country_report.dates.index(last_data_date)

    # The choice of date zero is in theory arbitrary.
    date_zero = country_report.dates[0]
    xs = [(date - date_zero).days for date in country_report.dates[: until_idx + 1]]
    fit = fit_atg_model.fit_atg_model(
        xs=xs,
        ys=country_report.cumulative_active[: until_idx + 1],
    )
    whole_day_offset = np.floor(fit.t0)

    # Move the fitted model by 'whole_day_offset', so that '0 <= fit.t0 < 1'.
    shifted_fit = AtgModelFit(exp=fit.exp, tg=fit.tg, t0=fit.t0 - whole_day_offset, a=fit.a)

    # Counterintuitively, `date` + `timedelta` results in `date`.
    start_date = date_zero + datetime.timedelta(days=whole_day_offset)
    return FittedFormula(fit=shifted_fit, start_date=start_date, last_data_date=last_data_date)


def _date_from_proto(proto_date) -> datetime.date:
    return datetime.date(year=proto_date.year, month=proto_date.month, day=proto_date.day)


def create_formula_from_proto(atg_parameters) -> FittedFormula:
    fit = AtgModelFit(
        exp=atg_parameters.alpha, tg=atg_parameters.tg, t0=atg_parameters.offset, a=atg_parameters.a
    )
    start_date = _date_from_proto(atg_parameters.start_date)
    last_data_date = _date_from_proto(atg_parameters.last_data_date)
    return FittedFormula(fit, start_date, last_data_date)


def _get_display_at_least_until(tg: float, exp: float, start_date: datetime.date) -> datetime.date:
    # Display values until the second inflection point.
    days_till_second_ip = math.ceil(tg * (exp + math.sqrt(exp)))
    return start_date + datetime.timedelta(days=days_till_second_ip)
