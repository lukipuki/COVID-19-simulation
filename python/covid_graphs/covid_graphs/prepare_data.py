import datetime
import json
from pathlib import Path

import click
import click_pathlib
import pandas as pd
from google.protobuf import text_format  # type: ignore

from .pb.country_data_pb2 import CountryData, DailyStats


@click.command(help="COVID-19 data downloader, writes into current directory")
@click.argument(
    "country", required=True, type=str,
)
@click.option(
    "-s", "--short_name", type=str, required=True, default=None, help="Short name of the country",
)
@click.option("--start", type=click.DateTime(formats=["%Y-%m-%d"]), default="2020-01-22")
@click.option(
    "--end", type=click.DateTime(formats=["%Y-%m-%d"]), default=str(datetime.date.today())
)
@click.option(
    "-d",
    "--data-dir",
    required=False,
    default=Path("."),
    type=click_pathlib.Path(exists=True),
    help="Directory with the population JSON",
)
def main(
    country: str,
    short_name: str,
    start: datetime.datetime,
    end: datetime.datetime,
    data_dir: Path,
):
    with (data_dir / "country-populations.json").open() as stream:
        population = {}
        for data in json.load(stream):
            population[data["country"]] = data["population"]

    def diff(a):
        "Calculates the daily increase from a cumulative number"
        a = list(map(int, a))
        for i in range(len(a) - 1, 0, -1):
            a[i] -= a[i - 1]
        return a

    # JHU uses country names that we want to improve.
    name_map = {"United States": "US", "South Korea": "Korea, South"}
    country_name_JHU = country if country not in name_map else name_map[country]
    data = {}

    for typ in ["deaths", "recovered", "confirmed"]:
        url = (
            "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
            f"csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{typ}_global.csv"
        )
        table = pd.read_csv(url)
        row = table.loc[table["Country/Region"] == country_name_JHU].iloc[:, 4:].sum()
        data[typ] = diff(row.values.tolist())

    start_day = datetime.datetime(2020, 1, 22)
    length = len(data["deaths"])
    dates = [(start_day + datetime.timedelta(days=i)).date() for i in range(length)]

    points = []
    country_data = CountryData()
    country_data.name = country
    country_data.short_name = short_name
    country_data.population = population[country]
    for c, r, d, t in zip(data["confirmed"], data["recovered"], data["deaths"], dates):
        if t < start.date() or t > end.date():
            continue
        points.append({"positive": c, "recovered": r, "dead": d, "date": t.strftime("%Y-%m-%d")})
        stats = DailyStats()
        stats.positive = c
        stats.recovered = r
        stats.dead = d
        date = stats.date
        date.day, date.month, date.year = t.day, t.month, t.year
        country_data.stats.append(stats)

    with open(f"{short_name}.data", "w") as output:
        output.write(text_format.MessageToString(country_data))
