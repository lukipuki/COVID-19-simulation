import datetime
from pathlib import Path
from typing import List

import click
import click_pathlib
from google.protobuf import text_format  # type: ignore

from .country_report import CountryReport, create_report
from .formula import FittedFormula
from .pb.atg_prediction_pb2 import AtgParameters, CountryAtgParameters
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
            formula=FittedFormula(until_date=last_data_date, country_report=report),
        )
        for last_data_date in dates
    )


@click.command(help="COVID-19 country predictions calculation")
@click.argument(
    "data_dir", required=True, type=click_pathlib.Path(exists=True),
)
@click.argument(
    "short_country_name", required=True, type=str,
)
@click.argument(
    "output_dir", required=True, type=click_pathlib.Path(),
)
def generate_predictions(data_dir: Path, short_country_name: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    country_report = create_report(
        data_dir / f"{short_country_name}.data", short_name=short_country_name
    )
    last_date_dates = country_report.dates[-PREDICTION_DAYS:]
    fitted_formulas = {
        last_data_date: FittedFormula(until_date=last_data_date, country_report=country_report)
        for last_data_date in last_date_dates
    }

    arg_parameters = CountryAtgParameters()
    arg_parameters.short_country_name = short_country_name
    arg_parameters.long_country_name = country_report.long_name
    for last_data_date, formula in fitted_formulas.items():
        parameters = AtgParameters()
        parameters.last_data_date.year = last_data_date.year
        parameters.last_data_date.month = last_data_date.month
        parameters.last_data_date.day = last_data_date.day

        trace_generator = formula.get_trace_generator(country_report)
        parameters.alpha = formula.fit.exp
        parameters.tg = formula.fit.tg
        parameters.t0 = formula.fit.t0
        parameters.a = formula.fit.a
        parameters.start_date.year = trace_generator.start_date.year
        parameters.start_date.month = trace_generator.start_date.month
        parameters.start_date.day = trace_generator.start_date.day

        arg_parameters.parameters.append(parameters)

    with open(output_dir / f"{short_country_name}.atg", "w") as output:
        output.write(text_format.MessageToString(arg_parameters))
