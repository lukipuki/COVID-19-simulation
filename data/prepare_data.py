#!/usr/bin/env python3
import argparse
import pandas as pd
import yaml
from datetime import datetime, timedelta

parser = argparse.ArgumentParser(description='COVID-19 data downloader')
parser.add_argument('country', metavar='country', type=str, help=f"Country")
args = parser.parse_args()


def diff(a):
    "Calculates the daily increase from a cumulative number"
    a = list(map(int, a))
    for i in range(len(a) - 1, 0, -1):
        a[i] -= a[i - 1]
    return a


data = {}
for typ in ["deaths", "recovered", "confirmed"]:
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/" \
           f"csse_covid_19_time_series/time_series_covid19_{typ}_global.csv"
    table = pd.read_csv(url)
    row = table.loc[(table["Country/Region"] == args.country) & (table["Province/State"].isnull())]
    data[typ] = diff(row.iloc[:, 4:].values.tolist()[0])


start_day = datetime(2020, 1, 22)
delta = -1 if args.country == 'Slovakia' else 0
length = len(data["deaths"])
dates = [(start_day + timedelta(days=i + delta)).strftime("%Y-%m-%d") for i in range(length)]

points = []
for c, r, d, t in zip(data["confirmed"], data["recovered"], data["deaths"], dates):
    points.append({'positive': c, 'recovered': r, 'dead': d, 'date': t})

with open("data.yaml", 'w') as f:
    yaml.dump(points, f, default_flow_style=False)
