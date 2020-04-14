from dataclasses import dataclass
import datetime
from typing import List

from .formula import ATG_formula, Formula


# Make the class hashable.
@dataclass(frozen=True, eq=True)
class PredictionEvent:
    name: str
    date: datetime.date


@dataclass
class CountryPrediction:
    prediction_event: PredictionEvent
    country: str
    formula: Formula


BK_20200329 = PredictionEvent(name="bk_20200329", date=datetime.date(2020, 3, 29))
BK_20200413 = PredictionEvent(name="bk_20200413", date=datetime.date(2020, 4, 13))
OTHER = PredictionEvent(name="other", date=datetime.date(2020, 4, 13)) # TODO: When did we add SVK prediction?

predictions_database = [
    # OTHER
    CountryPrediction(
        prediction_event=OTHER,
        country="Slovakia",
        formula=Formula(lambda t: 8 * t**1.28, r'$8 \cdot t^{1.28}$', 40, 10),
    ),

    # BK_20200329
    CountryPrediction(
        prediction_event=BK_20200329,
        country="Italy",
        formula=ATG_formula(7.8, 4417, 6.23),
    ),
    CountryPrediction(
        prediction_event=BK_20200329,
        country="USA",
        formula=ATG_formula(10.2, 72329, 6.23),
    ),
    CountryPrediction(
        prediction_event=BK_20200329,
        country="Spain",
        formula=ATG_formula(6.4, 3665, 6.23),
    ),
    CountryPrediction(
        prediction_event=BK_20200329,
        country="Germany",
        formula=ATG_formula(6.7, 3773, 6.23),
    ),
    CountryPrediction(
        prediction_event=BK_20200329,
        country="UK",
        formula=ATG_formula(7.2, 2719, 6.23),
    ),

    # BK_20200413
    CountryPrediction(
        prediction_event=BK_20200413,
        country="Italy",
        formula=ATG_formula(9.67, 30080, 5.26, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200413,
        country="USA",
        formula=ATG_formula(12.8, 1406000, 4.3, 1083),
    ),
    CountryPrediction(
        prediction_event=BK_20200413,
        country="Spain",
        formula=ATG_formula(5.93, 1645, 6.54, 155),
    ),
    CountryPrediction(
        prediction_event=BK_20200413,
        country="Germany",
        formula=ATG_formula(5.99, 5086, 5.79, 274),
    ),
    CountryPrediction(
        prediction_event=BK_20200413,
        country="Switzerland",
        formula=ATG_formula(4.19, 16.65, 7.78, 28),
    ),
]

prediction_event_list: List[PredictionEvent] = list(set(p.prediction_event for p in predictions_database))
country_list: List[str] = list(set(p.country for p in predictions_database))


def predictions_for_event(prediction_event: PredictionEvent) -> List[CountryPrediction]:
    return [p for p in predictions_database if p.prediction_event == prediction_event]


def predictions_for_country(country: str) ->  List[CountryPrediction]:
    return [p for p in predictions_database if p.country == country]


# TODO(miskosz): A separate file with tests.