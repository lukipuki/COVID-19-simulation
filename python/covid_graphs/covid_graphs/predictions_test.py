import datetime

from . import predictions
from .fit_atg_model import AtgModelFit
from .formula import FittedFormula


def test_displayable_formulas():
    start_date = datetime.date(2020, 5, 1)
    base_last_data_date = datetime.date(2020, 5, 11)  # 10 days after start date
    a = 17
    t0 = 0.4

    fitted_formulas = [
        # Peak exp*tg = 2*10 days after start_date
        FittedFormula(
            fit=AtgModelFit(a=a, exp=2, tg=10, t0=t0),
            start_date=start_date,
            last_data_date=base_last_data_date + datetime.timedelta(days=0),
        ),
        # Peak exp*tg = 2*11 = 22 days after start_date
        FittedFormula(
            fit=AtgModelFit(a=a, exp=2, tg=11, t0=t0),
            start_date=start_date,
            last_data_date=base_last_data_date + datetime.timedelta(days=1),
        ),
        # Peak exp*tg = 3*9 = 27 days after start_date
        FittedFormula(
            fit=AtgModelFit(a=a, exp=3, tg=9, t0=t0),
            start_date=start_date,
            last_data_date=base_last_data_date + datetime.timedelta(days=2),
        ),
        # Peak exp*tg = 3*12 = 36 days after start_date
        FittedFormula(
            fit=AtgModelFit(a=a, exp=3, tg=12, t0=t0),
            start_date=start_date,
            last_data_date=base_last_data_date + datetime.timedelta(days=3),
        ),
        # Peak exp*tg = 3*10 = 30 days after start_date
        FittedFormula(
            fit=AtgModelFit(a=a, exp=3, tg=10, t0=t0),
            start_date=start_date,
            last_data_date=base_last_data_date + datetime.timedelta(days=4),
        ),
    ]

    now = datetime.datetime(2020, 5, 15)  # last_data_date of the last formula
    displayable_formulas = predictions._calculate_displayable_predictions(
        fitted_formulas,
        max_peak_distance=datetime.timedelta(days=15),
        max_peak_variability=datetime.timedelta(days=6),
        now=now,
    )

    assert displayable_formulas[0].last_data_date == base_last_data_date + datetime.timedelta(
        days=1
    )
    assert displayable_formulas[1].last_data_date == base_last_data_date + datetime.timedelta(
        days=2
    )
