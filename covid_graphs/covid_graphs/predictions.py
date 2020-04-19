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
BK_20200411 = PredictionEvent(name="bk_20200411", date=datetime.date(2020, 4, 11))
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
    CountryPrediction(
        prediction_event=BK_20200329,
        country="France",
        formula=ATG_formula(6.5, 1961, 6.23),
    ),
    CountryPrediction(
        prediction_event=BK_20200329,
        country="Iran",
        formula=ATG_formula(8.7, 2569, 6.23),
    ),

    # BK_20200411
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Australia",
        formula=ATG_formula(4.9667, 426.7599, 5.5868, 83),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Austria",
        formula=ATG_formula(3.4818, 2.135, 8.466, 29),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Iceland",
        formula=ATG_formula(5.5763, 47.8177, 6.0141, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Jordan",
        formula=ATG_formula(8.9873, 4474.6547, 1.8184, 33),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Korea",
        formula=ATG_formula(8.9001, 79719.7898, 2.5156, 171),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Switzerland",
        formula=ATG_formula(4.1902, 16.6454, 7.7792, 28),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Croatia",
        formula=ATG_formula(8.5037, 1608.8302, 4.2301, 14),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Germany",
        formula=ATG_formula(5.9852, 5086.2059, 5.7886, 274),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Israel",
        formula=ATG_formula(3.9904, 0.3155, 9.3991, 29),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Italy",
        formula=ATG_formula(9.6702, 30079.4932, 5.2567, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Malaysia",
        formula=ATG_formula(13.3726, 46881.7586, 2.376, 104),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="NZ",
        formula=ATG_formula(6.401, 1.89E+03, 3.7006, 16),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Spain",
        formula=ATG_formula(5.9344, 1644.5779, 6.5412, 155),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Belgium",
        formula=ATG_formula(8.3277, 2838.2347, 5.6401, 38),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Canada",
        formula=ATG_formula(13.275, 117588.9945, 3.5334, 123),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Chile",
        formula=ATG_formula(18.7647, 152196.2414, 2.5375, 62),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Czechia",
        formula=ATG_formula(13.1119, 40609.4029, 3.3322, 35),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Netherlands",
        formula=ATG_formula(16.7206, 157176.2658, 3.7562, 57),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Norway",
        formula=ATG_formula(15.5411, 48762.3895, 3.4325, 18),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Portugal",
        formula=ATG_formula(11.2156, 31461.9423, 4.2779, 34),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="USA",
        formula=ATG_formula(12.8446, 1406472.4, 4.3383, 1083),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Latvia",
        formula=ATG_formula(17.3709, 16679.8421, 2.3218, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Lithuania",
        formula=ATG_formula(12.792, 11603.8935, 2.8746, 10),
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

    def predictions_for_country(self, country: str) -> List[CountryPrediction]:
        return [p for p in self._prediction_database if p.country == country]


prediction_db = PredictionDb(country_predictions=_prediction_database)
