#!/usr/bin/env python3
import yaml
from sys import stdin
from datetime import datetime, timedelta


# TODO: download it from
# From https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series

def diff(a):
    "Calculates the daily increase from a cumulative number"
    a = list(map(int, a))
    for i in range(len(a) - 1, 0, -1):
        a[i] -= a[i - 1]
    return a


cases = diff(stdin.readline().split())
recovered = diff(stdin.readline().split())
dead = diff(stdin.readline().split())

start_day = datetime(2020, 1, 22)
dates = [(start_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(len(cases))]

points = []
for c, r, d, t in zip(cases, recovered, dead, dates):
    points.append({'positive': c, 'recovered': r, 'dead': d, 'date': t})


with open("data.yaml", 'w') as f:
    yaml.dump(points, f, default_flow_style=False)
