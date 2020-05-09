import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from google.protobuf import text_format  # type: ignore

from . import formula
from .formula import AtgFormula, FittedFormula, Formula
from .pb.atg_prediction_pb2 import CountryAtgParameters

MAX_PEAK_DISTANCE = datetime.timedelta(days=14)


# Make the class hashable.
@dataclass(frozen=True, eq=True)
class PredictionEvent:
    name: str
    # Data until this date (inclusive) was used for the prediction.
    last_data_date: datetime.date
    prediction_date: datetime.date


@dataclass
class CountryPrediction:
    prediction_event: PredictionEvent
    country: str
    formula: Formula


BK_20200329 = PredictionEvent(
    name="bk_20200329",
    last_data_date=datetime.date(2020, 3, 29),
    prediction_date=datetime.date(2020, 3, 30),
)
BK_20200411 = PredictionEvent(
    name="bk_20200411",
    last_data_date=datetime.date(2020, 4, 11),
    prediction_date=datetime.date(2020, 4, 12),
)

_prediction_database = [
    # BK_20200329
    CountryPrediction(
        prediction_event=BK_20200329, country="Italy", formula=AtgFormula(7.8, 4417, 6.23, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200329, country="USA", formula=AtgFormula(10.2, 72329, 6.23, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200329, country="Spain", formula=AtgFormula(6.4, 3665, 6.23, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200329, country="Germany", formula=AtgFormula(6.7, 3773, 6.23, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200329, country="UK", formula=AtgFormula(7.2, 2719, 6.23, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200329, country="France", formula=AtgFormula(6.5, 1961, 6.23, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200329, country="Iran", formula=AtgFormula(8.7, 2569, 6.23, 200),
    ),
    # BK_20200411
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Australia",
        formula=AtgFormula(4.9667, 426.7599, 5.5868, 83),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Austria",
        # Fix buggy offset.
        formula=AtgFormula(3.4818, 2.135, 8.466, 29 + 1),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Iceland",
        formula=AtgFormula(5.5763, 47.8177, 6.0141, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Jordan",
        formula=AtgFormula(8.9873, 4474.6547, 1.8184, 33),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Korea",
        formula=AtgFormula(8.9001, 79719.7898, 2.5156, 171),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Switzerland",
        formula=AtgFormula(4.1902, 16.6454, 7.7792, 28),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Croatia",
        formula=AtgFormula(8.5037, 1608.8302, 4.2301, 14),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Germany",
        formula=AtgFormula(5.9852, 5086.2059, 5.7886, 274),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Israel",
        formula=AtgFormula(3.9904, 0.3155, 9.3991, 29),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Italy",
        formula=AtgFormula(9.6702, 30079.4932, 5.2567, 200),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Malaysia",
        formula=AtgFormula(13.3726, 46881.7586, 2.376, 104),
    ),
    CountryPrediction(
        prediction_event=BK_20200411, country="NZ", formula=AtgFormula(6.401, 1.89e03, 3.7006, 16),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Spain",
        formula=AtgFormula(5.9344, 1644.5779, 6.5412, 155),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Belgium",
        formula=AtgFormula(8.3277, 2838.2347, 5.6401, 38),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Canada",
        formula=AtgFormula(13.275, 117588.9945, 3.5334, 123),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Chile",
        formula=AtgFormula(18.7647, 152196.2414, 2.5375, 62),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Czechia",
        formula=AtgFormula(13.1119, 40609.4029, 3.3322, 35),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Netherlands",
        formula=AtgFormula(16.7206, 157176.2658, 3.7562, 57),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Norway",
        formula=AtgFormula(15.5411, 48762.3895, 3.4325, 18),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Portugal",
        formula=AtgFormula(11.2156, 31461.9423, 4.2779, 34),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="USA",
        formula=AtgFormula(12.8446, 1406472.4, 4.3383, 1083),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Latvia",
        formula=AtgFormula(17.3709, 16679.8421, 2.3218, 10),
    ),
    CountryPrediction(
        prediction_event=BK_20200411,
        country="Lithuania",
        formula=AtgFormula(12.792, 11603.8935, 2.8746, 10),
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

    def select_predictions(
        self, country: str, last_data_dates: List[datetime.date]
    ) -> List[CountryPrediction]:
        return [
            p
            for p in self._prediction_database
            if p.country == country and p.prediction_event.last_data_date in last_data_dates
        ]


def load_prediction_db(prediction_dir: Path) -> PredictionDb:
    country_predictions = _prediction_database[:]

    # TODO: Load all predictions from prediction dir. Make the folder existence mandatory.
    if not prediction_dir.is_dir():
        logging.warning(f"Could not load predictions from {prediction_dir}.")

    for country_atg_params_path in prediction_dir.glob("*.atg"):
        country_atg_parameters = CountryAtgParameters()
        text_format.Parse(country_atg_params_path.read_text(), country_atg_parameters)

        fitted_formulas = [
            formula.create_formula_from_proto(atg_parameters)
            for atg_parameters in country_atg_parameters.parameters
        ]
        # TODO(miskosz): The decision on which predictions to display should be made by the caller.
        start_idx = _calculate_earliest_displayable_idx(fitted_formulas, MAX_PEAK_DISTANCE)
        fitted_predictions = _create_predictions_from_formulas(
            fitted_formulas[start_idx:], country_atg_parameters.short_country_name
        )
        country_predictions.extend(fitted_predictions)

    return PredictionDb(country_predictions=country_predictions)


# TODO(miskosz): Move to the caller.
def _calculate_earliest_displayable_idx(
    fitted_formulas: Iterable[FittedFormula], max_peak_distance: datetime.timedelta
) -> int:
    """
    Calculates the earliest index in fitted_formulas, after which the peaks of formulas are within
    'max_peak_distance'.
    """
    peak_days = [
        formula.get_peak(country_report=None) for formula in reversed(list(fitted_formulas))
    ]

    min_peak, max_peak = peak_days[0], peak_days[0]
    take_count = 1
    for peak in peak_days[1:]:
        min_peak = min(min_peak, peak)
        max_peak = max(max_peak, peak)
        if max_peak - min_peak <= max_peak_distance:
            take_count += 1
        else:
            break
    return len(peak_days) - take_count


def _create_predictions_from_formulas(
    fitted_formulas: Iterable[FittedFormula], country_short_name: str
) -> List[CountryPrediction]:
    return [
        CountryPrediction(
            prediction_event=PredictionEvent(
                name=f"daily_fit_{fitted_formula.last_data_date.strftime('%Y_%m_%d')}",
                last_data_date=fitted_formula.last_data_date,
                prediction_date=fitted_formula.last_data_date,
            ),
            country=country_short_name,
            formula=fitted_formula,
        )
        for fitted_formula in fitted_formulas
    ]
