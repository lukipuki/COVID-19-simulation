from pathlib import Path
from typing import Dict, List, Tuple

from flask import Flask, abort, jsonify

from covid_graphs.country_graph import CountryGraph
from covid_graphs.country_report import CountryReport, create_report
from covid_graphs.predictions import prediction_db

TITLE = "COVID-19 predictions of Boďová and Kollár"
CountryGraphsByReportName = Dict[str, List[CountryGraph]]


class Rest:
    def __init__(self, data_dir: Path):
        self.available_predictions = Rest._create_available_predictions_by_date()
        self.country_reports = Rest._create_country_reports(data_dir)
        predictions, country_reports_active = Rest._create_predictions(self.country_reports)
        self.predictions = predictions
        self.country_reports_active = country_reports_active

    @staticmethod
    def _create_available_predictions_by_date() -> Dict[str, Dict]:
        result = {}
        for x in prediction_db.get_prediction_events():
            result[x.name] = {
                "label": x.date,
                "countries": [p.country for p in prediction_db.predictions_for_event(x)],
            }
        return result

    @staticmethod
    def _create_country_reports(data_dir: Path) -> Dict[str, CountryReport]:
        country_reports = {}
        for country_short_name in prediction_db.get_countries():
            if (data_dir / f"{country_short_name}.data").is_file():
                country_report = create_report(
                    data_dir / f"{country_short_name}.data", country_short_name
                )
                country_reports[country_report.short_name] = country_report

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
            for prediction, curve in zip(country_predictions, graph.curves):
                xs, ys = curve.generate_trace(graph.display_until)
                idx_max = ys.argmax()
                predictions.append(
                    {
                        "type": "prediction",
                        "date_list": xs,
                        "values": ys.tolist(),
                        "description": curve.label,
                        "short_name": country_report.short_name,
                        "long_name": country_report.long_name,
                        "max_value_date": xs[idx_max],
                        "max_value": ys.max(),
                        "date_name": prediction.prediction_event.name,
                        "date": prediction.prediction_event.date,
                    }
                )

        return predictions, country_reports_active

    def get_app(self):
        return self

    def get_available_predictions(self):
        return jsonify(self.available_predictions)

    def get_specific_prediction(self, date: str, country: str):
        for prediction in self.predictions:
            if prediction["short_name"] == country and prediction["date_name"] == date:
                return jsonify(prediction)

        abort(404)
        return ""

    def get_country_data(self, country: str):
        if country not in self.country_reports_active:
            abort(404)

        return jsonify(self.country_reports_active[country])


def create_rest(data_dir: Path, server: Flask):
    # TODO(rejdi): Don't use print.
    print("Creating dashboard for REST calls.")
    return Rest(data_dir)
