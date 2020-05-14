import datetime
import math

import numpy as np
import pytest

from .country_report import CountryReport
from .formula import AtgFormula


def test_two_traces():
    cumulative_active = np.array([0, 0, 1, 2, 5, 18, 45])
    start_date = datetime.date(2020, 4, 17)
    dates = [start_date + datetime.timedelta(days=d) for d in range(len(cumulative_active))]
    report = CountryReport(
        short_name="UK",
        long_name="United Kingdom",
        dates=dates,
        daily_positive=None,
        daily_dead=None,
        daily_recovered=None,
        daily_active=None,
        cumulative_active=cumulative_active,
        population=None,
    )
    display_until = datetime.date(2020, 4, 30)

    f1 = AtgFormula(tg=2, a=47, exponent=1.5, min_case_count=2)
    # The trace starts (t=0) at 2020-04-19. The maximum of this trace is at t = TG * exponent = 3.
    max_t1, start_date1 = 3, datetime.date(2020, 4, 19)
    length1 = math.ceil(2 * (1.5 + math.sqrt(1.5)))

    f2 = AtgFormula(tg=3, a=12, exponent=2, min_case_count=1)
    # The trace starts (t=0) at 2020-04-18. The maximum of this trace is at t = TG * exponent = 6.
    max_t2, start_date2, length2 = 6, datetime.date(2020, 4, 18), math.ceil(3 * (2 + math.sqrt(2)))

    trace_generator1 = f1.get_trace_generator(report)
    trace1 = trace_generator1.generate_trace(display_until)
    assert trace1.max_value == pytest.approx((47 / 2) * (max_t1 / 2) ** 1.5 * math.exp(-max_t1 / 2))
    assert trace1.max_value_date == start_date1 + datetime.timedelta(days=max_t1)
    assert trace1.xs[0] == start_date1
    assert trace_generator1.display_at_least_until == start_date1 + datetime.timedelta(days=length1)

    trace_generator2 = f2.get_trace_generator(report)
    trace2 = trace_generator2.generate_trace(display_until)
    assert trace2.max_value == pytest.approx((12 / 3) * (max_t2 / 3) ** 2 * math.exp(-max_t2 / 3))
    assert trace2.max_value_date == start_date2 + datetime.timedelta(days=max_t2)
    assert trace2.xs[0] == start_date2
    assert trace_generator2.display_at_least_until == start_date2 + datetime.timedelta(days=length2)
