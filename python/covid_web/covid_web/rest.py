from pathlib import Path
from typing import Dict, List, Tuple

import flask

from covid_graphs.country_graph import CountryGraph
from covid_graphs.country_report import CountryReport, create_report
from covid_graphs.predictions import prediction_db


class Rest:
    def __init__(self, data_dir: Path):
        self.available_predictions = Rest._create_available_predictions()
        self.country_reports = Rest._create_country_reports(data_dir)
        predictions, country_reports_active = Rest._create_predictions(self.country_reports)
        self.predictions = predictions
        self.country_reports_active = country_reports_active

    @staticmethod
    def _create_available_predictions() -> List[Dict]:
        result = [
            {
                "prediction": x.name,
                "prediction_date": x.prediction_date,
                "country": p.country
            }
            for x in prediction_db.get_prediction_events()
            for p in prediction_db.predictions_for_event(x)
        ]

        return result

    @staticmethod
    def _create_country_reports(data_dir: Path) -> Dict[str, CountryReport]:
        country_reports = {
            country_short_name: create_report(data_dir / f"{country_short_name}.data")
            for country_short_name in prediction_db.get_countries()
            if (data_dir / f"{country_short_name}.data").is_file()
        }

        return country_reports

    @staticmethod
    def _create_predictions(
        country_reports: Dict[str, CountryReport]
    ) -> Tuple[List[Dict], Dict[str, Dict]]:
        predictions = []
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
                predictions.append(
                    {
                        "type": "prediction",
                        "date_list": trace.xs,
                        "values": trace.ys.tolist(),
                        "description": trace.label,
                        "short_name": country_report.short_name,
                        "long_name": country_report.long_name,
                        "max_value_date": trace.max_value_date,
                        "max_value": trace.max_value,
                        "date_name": event.name,
                        "last_data_date": event.last_data_date,
                        "prediction_date": event.prediction_date,
                    }
                )

        return predictions, country_reports_active

    def get_app(self):
        return self

    def get_available_predictions(self):
        return flask.jsonify(self.available_predictions)

    def get_predictions_by_country(self, country: str):
        result = [
            prediction
            for prediction in self.predictions
            if prediction["short_name"] == country
        ]

        if len(result) == 0:
            flask.abort(404)

        return flask.jsonify(result)

    def get_predictions_by_name(self, date: str):
        result = [
            prediction
            for prediction in self.predictions
            if prediction["date_name"] == date
        ]

        if len(result) == 0:
            flask.abort(404)

        return flask.jsonify(result)

    def get_specific_prediction(self, date: str, country: str):
        for prediction in self.predictions:
            if prediction["short_name"] == country and prediction["date_name"] == date:
                return flask.jsonify(prediction)

        flask.abort(404)
        return ""

    def get_country_data(self, country: str):
        if country not in self.country_reports_active:
            flask.abort(404)

        return flask.jsonify(self.country_reports_active[country])
