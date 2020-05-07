import datetime
from pathlib import Path
from typing import List

import click
import click_pathlib
from google.protobuf import text_format  # type: ignore

from .country_report import CountryReport, create_report
from .formula import fit_country_data
from .pb.atg_prediction_pb2 import CountryAtgParameters
from .predictions import CountryPrediction, PredictionEvent

PREDICTION_DAYS = 21


def get_fitted_predictions(
    report: CountryReport, dates: List[datetime.date]
) -> List[CountryPrediction]:
    return list(
        CountryPrediction(
            prediction_event=PredictionEvent(
                name=f"daily_fit_{last_data_date.strftime('%Y_%m_%d')}",
                last_data_date=last_data_date,
                prediction_date=last_data_date,
            ),
            country=report.short_name,
            formula=fit_country_data(last_data_date=last_data_date, country_report=report),
        )
        for last_data_date in dates
        if last_data_date in report.dates
    )


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
    last_date_dates = country_report.dates[-PREDICTION_DAYS:]
    fitted_formulas = {
        last_data_date: fit_country_data(
            last_data_date=last_data_date, country_report=country_report
        )
        for last_data_date in last_date_dates
    }

    short_country_name = country_report.short_name
    country_atg_parameters = CountryAtgParameters()
    country_atg_parameters.long_country_name = country_report.long_name
    country_atg_parameters.short_country_name = short_country_name
    for last_data_date, formula in fitted_formulas.items():
        country_atg_parameters.parameters.append(formula.serialize())

    with open(output_dir / f"{short_country_name}.atg", "w") as output:
        output.write(text_format.MessageToString(country_atg_parameters))
