import argparse
import pandas as pd
from datetime import datetime, timedelta
from google.protobuf import text_format

from .pb.country_data_pb2 import CountryData, DailyStats


def main():
    parser = argparse.ArgumentParser(description='COVID-19 data downloader')
    parser.add_argument('country', metavar='country', type=str, help=f"Country")
    parser.add_argument('--short_name',
                        metavar='short_name',
                        type=str,
                        help=f"Short name of the country",
                        default=None)
    args = parser.parse_args()
    short_name = args.short_name if args.short_name is not None else args.country

    def diff(a):
        "Calculates the daily increase from a cumulative number"
        a = list(map(int, a))
        for i in range(len(a) - 1, 0, -1):
            a[i] -= a[i - 1]
        return a

    data = {}
    country_name_JHU = args.country if args.country != "United States" else "US"
    for typ in ["deaths", "recovered", "confirmed"]:
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/" \
            f"csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{typ}_global.csv"
        table = pd.read_csv(url)
        row = table.loc[table["Country/Region"] == country_name_JHU].iloc[:, 4:].sum()
        data[typ] = diff(row.values.tolist())

    start_day = datetime(2020, 1, 22)
    delta = -1 if args.country == 'Slovakia' else 0
    length = len(data["deaths"])
    dates = [start_day + timedelta(days=i + delta) for i in range(length)]

    points = []
    country_data = CountryData()
    country_data.name = args.country
    for c, r, d, t in zip(data["confirmed"], data["recovered"], data["deaths"], dates):
        points.append({'positive': c, 'recovered': r, 'dead': d, 'date': t.strftime("%Y-%m-%d")})
        stats = DailyStats()
        stats.positive = c
        stats.recovered = r
        stats.dead = d
        date = stats.date
        date.day, date.month, date.year = t.day, t.month, t.year
        country_data.stats.append(stats)

    with open(f'{short_name}.data', "w") as output:
        output.write(text_format.MessageToString(country_data))
