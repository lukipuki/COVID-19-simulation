from pathlib import Path
from typing import Dict, List, Tuple

import click
import click_pathlib
import flask

from covid_graphs import predictions
from covid_graphs.country_graph import CountryGraph
from covid_graphs.country_report import CountryReport, create_report
from covid_graphs.predictions import PredictionDb


@click.command(help="COVID-19 static REST generator")
@click.argument("data_dir", required=True, type=click_pathlib.Path(exists=True))
@click.argument("output_dir", required=True, type=click_pathlib.Path())
def generate_static_rest(data_dir: Path, output_dir: Path) -> None:
    rest = Rest(data_dir=data_dir, prediction_dir=data_dir / "predictions")
    rest.generate_static_files(output_dir)


class Rest:
    def __init__(self, data_dir: Path, prediction_dir: Path):
        self.prediction_db = predictions.load_prediction_db(prediction_dir=prediction_dir)
        self.available_predictions = Rest._create_available_predictions(self.prediction_db)
        self.country_reports = Rest._create_country_reports(self.prediction_db, data_dir)
        country_predictions, country_reports_active = Rest._create_predictions(
            self.prediction_db, self.country_reports
        )
        self.country_predictions = country_predictions
        self.country_reports_active = country_reports_active

    @staticmethod
    def _create_available_predictions(prediction_db: PredictionDb) -> List[Dict]:
        return [
            {"prediction": x.name, "prediction_date": x.prediction_date, "country": p.country}
            for x in prediction_db.get_prediction_events()
            for p in prediction_db.predictions_for_event(x)
        ]

    @staticmethod
    def _create_country_reports(
        prediction_db: PredictionDb, data_dir: Path
    ) -> Dict[str, CountryReport]:
        return {
            country_short_name: create_report(data_dir / f"{country_short_name}.data")
            for country_short_name in prediction_db.get_countries()
            if (data_dir / f"{country_short_name}.data").is_file()
        }

    @staticmethod
    def _create_predictions(
        prediction_db: PredictionDb, country_reports: Dict[str, CountryReport]
    ) -> Tuple[List[Dict], Dict[str, Dict]]:
        result_predictions = []
        country_reports_active = {}
        for country in prediction_db.get_countries():
            country_predictions = prediction_db.predictions_for_country(country)
            country_report = country_reports[country]
            graph = CountryGraph(report=country_report, country_predictions=country_predictions)
            country_reports_active[country] = {
                "type": "cumulative_active",
                "date_list": graph.cropped_dates,
                "values": graph.cropped_cumulative_active.tolist(),
                "short_name": country_report.short_name,
                "long_name": country_report.long_name,
            }
            for event, trace in graph.trace_by_event.items():
                result_predictions.append(
                    {
                        "type": "prediction",
                        "date_list": trace.xs,
                        "values": trace.ys.tolist(),
                        "description": trace.label,
                        "short_name": country_report.short_name,
                        "long_name": country_report.long_name,
                        "max_value_date": trace.max_value_date,
                        "max_value": trace.max_value,
                        "prediction_name": event.name,
                        "last_data_date": event.last_data_date,
                        "prediction_date": event.prediction_date,
                    }
                )

        return result_predictions, country_reports_active

    def get_app(self):
        return self

    def get_available_predictions(self):
        return flask.jsonify(self.available_predictions)

    def _get_predictions_by_country(self, country: str):
        return [
            prediction
            for prediction in self.country_predictions
            if prediction["short_name"] == country
        ]

    def get_predictions_by_country(self, country: str):
        result = self._get_predictions_by_country(country=country)

        if len(result) == 0:
            flask.abort(404)

        return flask.jsonify(result)

    def _get_predictions_by_name(self, prediction_name: str):
        return [
            prediction
            for prediction in self.country_predictions
            if prediction["prediction_name"] == prediction_name
        ]

    def get_predictions_by_name(self, date: str):
        result = self._get_predictions_by_name(prediction_name=date)

        if len(result) == 0:
            flask.abort(404)

        return flask.jsonify(result)

    def _get_specific_prediction(self, date: str, country: str):
        for prediction in self.country_predictions:
            if prediction["short_name"] == country and prediction["prediction_name"] == date:
                return prediction

        return ""

    def get_specific_prediction(self, date: str, country: str):
        result = self._get_specific_prediction(date=date, country=country)
        if result == "":
            flask.abort(404)

        return flask.jsonify(result)

    def get_country_data(self, country: str):
        if country not in self.country_reports_active:
            flask.abort(404)

        return flask.jsonify(self.country_reports_active[country])

    def generate_static_files(self, output_dir: Path) -> None:
        Path(output_dir / f"data").mkdir(parents=True, exist_ok=True)
        Path(output_dir / f"predictions/by_prediction").mkdir(parents=True, exist_ok=True)
        Path(output_dir / f"predictions/by_country").mkdir(parents=True, exist_ok=True)

        # country data
        for country in self.country_reports_active:
            with open(output_dir / "data" / f"{country}.json", "w") as output:
                output.write(flask.json.dumps(self.country_reports_active[country]))

        # list of all available predictions for each country
        with open(output_dir / "predictions" / f"list.json", "w") as output:
            output.write(flask.json.dumps(self.available_predictions))

        # all predictions by country
        for country in self.prediction_db.get_countries():
            predictions = self._get_predictions_by_country(country)
            with open(output_dir / "predictions" / "by_country" / f"{country}.json", "w") as output:
                output.write(flask.json.dumps(predictions))

        # all predictions by prediction name
        for prediction_event in self.prediction_db.get_prediction_events():
            predictions = self._get_predictions_by_name(prediction_event.name)
            with open(
                output_dir / "predictions" / "by_prediction" / f"{prediction_event.name}.json", "w"
            ) as output:
                output.write(flask.json.dumps(predictions))

        # all combinations
        for prediction in self.country_predictions:
            prediction_data = flask.json.dumps(prediction)
            Path(
                output_dir / "predictions" / "by_prediction" / f"{prediction['prediction_name']}"
            ).mkdir(parents=True, exist_ok=True)
            Path(output_dir / "predictions" / "by_country" / f"{prediction['short_name']}").mkdir(
                parents=True, exist_ok=True
            )

            with open(
                output_dir
                / "predictions"
                / "by_prediction"
                / prediction["prediction_name"]
                / f"{prediction['short_name']}.json",
                "w",
            ) as output:
                output.write(prediction_data)

            Path(output_dir / "predictions" / "by_country" / prediction["short_name"]).mkdir(
                parents=True, exist_ok=True
            )
            with open(
                output_dir
                / "predictions"
                / "by_country"
                / prediction["short_name"]
                / f"{prediction['prediction_name']}.json",
                "w",
            ) as output:
                output.write(prediction_data)
