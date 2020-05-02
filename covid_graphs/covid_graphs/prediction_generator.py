import datetime
from pathlib import Path
from typing import List

import click
import click_pathlib
from google.protobuf import text_format  # type: ignore

from .country_report import CountryReport, create_report
from .formula import FittedFormula
from .pb.atg_prediction_pb2 import AtgTraceGenerator, AtgTraceGenerators
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
    "country_short_name", required=True, type=str,
)
@click.argument(
    "prediction_dir", required=True, type=click_pathlib.Path(exists=True),
)
def store_predictions(data_dir: Path, country_short_name: str, prediction_dir: Path) -> None:
    country_report = create_report(
        data_dir / f"{country_short_name}.data", short_name=country_short_name
    )
    last_date_dates = country_report.dates[-PREDICTION_DAYS:]
    fitted_formulas = list(
        FittedFormula(until_date=last_data_date, country_report=country_report)
        for last_data_date in last_date_dates
    )

    trace_generators = AtgTraceGenerators()
    for last_date_date, formula in zip(last_date_dates, fitted_formulas):
        generator = AtgTraceGenerator()
        generator.last_data_date.year = last_date_date.year
        generator.last_data_date.month = last_date_date.month
        generator.last_data_date.day = last_date_date.day

        trace_generator = formula.get_trace_generator(country_report)
        generator.alpha = formula.fit.exp
        generator.tg = formula.fit.tg
        generator.t0 = formula.fit.t0
        generator.a = formula.fit.a
        generator.start_date.year = trace_generator.start_date.year
        generator.start_date.month = trace_generator.start_date.month
        generator.start_date.day = trace_generator.start_date.day

        trace_generators.generators.append(generator)

    with open(prediction_dir / f"{country_short_name}.atg", "w") as output:
        output.write(text_format.MessageToString(trace_generators))
