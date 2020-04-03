#!/usr/bin/env python3
import argparse
import pandas as pd
import yaml
from sys import stdin
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
    rows = table.loc[table["Country/Region"] == "Italy"]
    data[typ] = diff(rows.iloc[:, 4:].values.tolist()[0])

positive = data["confirmed"]
recovered = data["recovered"]
dead = data["deaths"]

start_day = datetime(2020, 1, 22)
dates = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(len(positive))]

points = []
for c, r, d, t in zip(positive, recovered, dead, dates):
    points.append({'positive': c, 'recovered': r, 'dead': d, 'date': t})

with open("data.yaml", 'w') as f:
    yaml.dump(points, f, default_flow_style=False)
