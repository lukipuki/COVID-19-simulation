import math
from datetime import datetime, timedelta
import numpy as np
from collections import namedtuple
from enum import Enum

EXPONENT = 6.23

# TODO(lukas): Move to dataclass?
Formula = namedtuple('Formula', ['lambd', 'text', 'second_ip_day', 'min_case_count'])


class XAxisType(Enum):
    Dated = 'dated'  # with dates
    Numbered = 'numbered'  # numbered instead of dates

    def __str__(self):
        return self.value


def ATG_formula(TG, A, exponent=EXPONENT, min_case_count=200):
    text = r'$\frac{_A}{_TG} \cdot \left(\frac{t}{_TG}\right)^{_expon} / e^{t/_TG}$'
    text = text.replace("_A", f"{A}").replace("_TG", f"{TG}").replace("_expon", f"{exponent}")
    # Second inflection point day
    second_ip_day = math.ceil(TG * (exponent + math.sqrt(exponent)))
    return Formula(lambda t: (A / TG) * (t / TG)**exponent / np.exp(t / TG), text, second_ip_day,
                   min_case_count)


class EvaluatedFormula():
    def __init__(self,
                 formula,
                 cumulative_active,
                 first_idx,
                 last_idx,
                 first_date,
                 xaxis_type=XAxisType.Dated):
        self.text = formula.text
        # First index: t=1
        start_idx = np.argmax(cumulative_active >= formula.min_case_count)
        length = last_idx - start_idx
        self.y = formula.lambd(np.arange(length) + 1)
        self.date_list = [(first_date + timedelta(days=d)).strftime('%Y-%m-%d')
                          for d in range(start_idx, last_idx + 1)]
        if xaxis_type == XAxisType.Numbered:
            self.t = np.arange(length) + 1 + (start_idx - first_idx)
        else:
            self.t = self.date_list

        self.maximal_idx = self.y.argmax()

    @staticmethod
    def evaluate_formulas(formulas, cumulative_active, first_date, xaxis_type=XAxisType.Dated):
        first_idx = min(
            np.argmax(cumulative_active >= formula.min_case_count) for formula in formulas)
        last_idx = max(
            np.argmax(cumulative_active >= formula.min_case_count) + formula.second_ip_day
            for formula in formulas)

        first_date_parsed = datetime.strptime(first_date, '%Y-%m-%d')
        return (first_idx, last_idx, [
            EvaluatedFormula(formula, cumulative_active, first_idx, last_idx, first_date_parsed)
            for formula in formulas
        ])
