import datetime
from pathlib import Path
from typing import Iterable, List

import click
import click_pathlib
from google.protobuf import text_format  # type: ignore

from . import formula
from .country_report import CountryReport, create_report
from .formula import FittedFormula
from .pb.atg_prediction_pb2 import CountryAtgParameters
from .predictions import CountryPrediction, PredictionEvent

# Five weeks
PREDICTION_DAYS = 7 * 5


def create_fitted_formulas(
    country_report: CountryReport, last_data_dates: Iterable[datetime.date]
) -> List[FittedFormula]:
    return [
        formula.fit_country_data(last_data_date=last_data_date, country_report=country_report)
        for last_data_date in last_data_dates
    ]


def create_predictions_from_formulas(
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


def get_fitted_predictions(
    country_report: CountryReport, last_data_dates: List[datetime.date]
) -> List[CountryPrediction]:
    # Only use last_data_dates that appear in country_report.dates
    filtered_dates = list(set(last_data_dates) & set(country_report.dates))
    fitted_formulas = create_fitted_formulas(country_report, last_data_dates=filtered_dates)
    return create_predictions_from_formulas(fitted_formulas, country_report.short_name)


@click.command(help="COVID-19 country predictions calculation")
@click.argument(
    "filename", required=True, type=click_pathlib.Path(exists=True),
)
@click.argument(
    "output_dir", required=True, type=click_pathlib.Path(),
)
def generate_predictions(filename: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    country_report = create_report(filename)
    last_data_dates = country_report.dates[-PREDICTION_DAYS:]
    fitted_formulas = create_fitted_formulas(country_report, last_data_dates)

    short_country_name = country_report.short_name
    country_atg_parameters = CountryAtgParameters()
    country_atg_parameters.long_country_name = country_report.long_name
    country_atg_parameters.short_country_name = short_country_name
    for fitted_formula in fitted_formulas:
        country_atg_parameters.parameters.append(fitted_formula.serialize())

    with open(output_dir / f"{short_country_name}.atg", "w") as output:
        output.write(text_format.MessageToString(country_atg_parameters))
