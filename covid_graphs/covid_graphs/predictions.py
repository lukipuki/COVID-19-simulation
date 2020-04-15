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
BK_20200412 = PredictionEvent(name="bk_20200412", date=datetime.date(2020, 4, 12))
OTHER = PredictionEvent(name="other", date=datetime.date(2020, 4, 1))

_prediction_database = [
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

    # BK_20200412
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Korea",
        formula=ATG_formula(8.9, 79720, 2.52, 171),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Austria",
        formula=ATG_formula(3.48, 2.13, 8.47, 29),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Iceland",
        formula=ATG_formula(5.58, 47.8, 6.01, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Jordan",
        formula=ATG_formula(7.99, 3121, 2.18, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Switzerland",
        formula=ATG_formula(4.19, 16.65, 7.78, 28),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Australia",
        formula=ATG_formula(4.97, 426.75, 5.59, 83),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Croatia",
        formula=ATG_formula(8.5, 1608, 4.23, 14),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Germany",
        formula=ATG_formula(5.99, 5086, 5.79, 274),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Israel",
        formula=ATG_formula(3.99, 0.32, 9.40, 29),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Italy",
        formula=ATG_formula(9.67, 30080, 5.26, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Malaysia",
        formula=ATG_formula(13.37, 46882, 2.38, 104),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="New Zealand",
        formula=ATG_formula(2.96, 0.00024, 11.36, 4),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Spain",
        formula=ATG_formula(5.93, 1645, 6.54, 155),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Belgium",
        formula=ATG_formula(8.33, 2838, 5.64, 38),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Canada",
        formula=ATG_formula(13.3, 117591, 3.5, 123),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Chile",
        formula=ATG_formula(18.8, 152200, 2.5, 62),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Czechia",
        formula=ATG_formula(13.1, 40610, 3.3, 35),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Latvia",
        formula=ATG_formula(17.4, 16680, 2.3, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Lithuania",
        formula=ATG_formula(8.2, 822, 4.5, 1),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Netherlands",
        formula=ATG_formula(16.7, 157180, 3.8, 57),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Norway",
        formula=ATG_formula(15.5, 48762, 3.4, 18),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="Portugal",
        formula=ATG_formula(11.2, 31462, 4.28, 34),
    ),
    CountryPrediction(
        prediction_event=BK_20200412,
        country="USA",
        formula=ATG_formula(12.8, 1406478, 4.3, 1083),
    ),
]


# TODO(miskosz): Really really add tests in another PR.
class PredictionDb:
    """Interface to access prediction data."""

    def __init__(self, country_predictions: List[CountryPrediction]) -> None:
        self._prediction_database = country_predictions
        self._prediction_events = list(set(p.prediction_event for p in self._prediction_database))
        self._countries = list(set(p.country for p in self._prediction_database))

    def get_prediction_events(self) -> List[PredictionEvent]:
        """Returns an unordered list of all prediction events."""
        return self._prediction_events

    def get_countries(self) -> List[str]:
        """Returns an unordered list of all countries."""
        return self._countries

    def predictions_for_event(self, prediction_event: PredictionEvent) -> List[CountryPrediction]:
        return [p for p in self._prediction_database if p.prediction_event == prediction_event]

    def predictions_for_country(self, country: str) ->  List[CountryPrediction]:
        return [p for p in self._prediction_database if p.country == country]


prediction_db = PredictionDb(country_predictions=_prediction_database)
