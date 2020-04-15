import math
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from enum import Enum
from typing import Callable


@dataclass
class Formula:
    lambd: Callable[[float], float]
    text: str
    second_ip_day: int
    min_case_count: int


class XAxisType(Enum):
    Dated = 'dated'  # with dates
    Numbered = 'numbered'  # numbered instead of dates

    def __str__(self):
        return self.value


def ATG_formula(TG, A, exponent, min_case_count=200):
    text = r'$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{_expon} / e^{t/_TG}$'
    text = text.replace("_A", f"{A}").replace("_TG", f"{TG}").replace("_expon", f"{exponent}")
    # Day of the second inflection point
    second_ip_day = math.ceil(TG * (exponent + math.sqrt(exponent)))
    return Formula(lambda t: (A / TG) * (t / TG)**exponent / np.exp(t / TG), text, second_ip_day,
                   min_case_count)


class Curve():
    """Class containing an curve derived from a formula.

        cumulative_active - list of cumulative active cases
        first_idx - 0-based index where the graph starts, so from cumulative_active[first_idx:].
        last_idx - 0-based index where the graph ends
        first_date - date corresponding to cumulative_active[0]
        xaxis_type - whether we label with numbers or dates
    """
    def __init__(self, formula, cumulative_active, first_idx, last_idx, first_date, xaxis_type):
        self.text = formula.text
        # First index: t=1
        start_idx = np.argmax(cumulative_active >= formula.min_case_count)
        length = last_idx - start_idx + 1
        self.y = formula.lambd(np.arange(length) + 1)
        self.date_list = [(first_date + timedelta(days=d)).strftime('%Y-%m-%d')
                          for d in range(start_idx, last_idx + 1)]
        if xaxis_type == XAxisType.Numbered:
            self.t = np.arange(length) + 1 + (start_idx - first_idx)
        else:
            self.t = self.date_list

        self.maximal_idx = self.y.argmax()

    @staticmethod
    def create_curves(formulas, cumulative_active, first_date, xaxis_type=XAxisType.Dated):
        """Evaluates a list of formulas and finds a suitable range in the graph"""
        # The graph starts where the first curve starts. And each curve starts when the number of
        # active cases exceeds 'min_case_count'.
        first_idx = min(
            np.argmax(cumulative_active >= formula.min_case_count) for formula in formulas)
        # The graph ends where the last curve ends. Each curve ends at its second inflection
        # point.
        last_idx = max(
            np.argmax(cumulative_active >= formula.min_case_count) + formula.second_ip_day
            for formula in formulas)

        return (first_idx, last_idx, [
            Curve(formula, cumulative_active, first_idx, last_idx, first_date, xaxis_type)
            for formula in formulas
        ])
