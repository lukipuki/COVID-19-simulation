import sys
import numpy as np
import yaml
import argparse
from datetime import datetime, timedelta
from google.protobuf import text_format

sys.path.append('../graphs')

from country_data_pb2 import CountryData, DailyStats

parser = argparse.ArgumentParser(description='COVID-19 web server')
parser.add_argument('country_name', metavar='country_name', type=str, help=f"Directory with YAML files")
args = parser.parse_args()

with open(f'data-{args.country_name}.yaml', 'r') as stream:
    try:
        data = yaml.safe_load(stream)
        positive = np.array([point['positive'] for point in data])
        dead = np.array([point['dead'] for point in data])
        recovered = np.array([point['recovered'] for point in data])
        if "tested" in data:
            tested = np.array([point['tested'] for point in data])
        else:
            tested = np.zeros(len(data)) - 1
        active = positive - recovered - dead
        date_list = [point["date"] for point in data]
        
    except yaml.YAMLError as exc:
            raise exc

    country_data = CountryData()
    country_data.name = args.country_name

    for c, r, d, t, test in zip(positive, recovered, dead, date_list, tested):
        stats = DailyStats()
        stats.positive = c
        stats.recovered = r
        stats.dead = d
        if test != -1:
            stats.tested = test
        date = stats.date
        t = datetime.strptime(t, "%Y-%m-%d")
        date.day, date.month, date.year = t.day, t.month, t.year
        country_data.stats.append(stats)

    with open(f'{args.country_name}.data', "w") as output:
        output.write(text_format.MessageToString(country_data))
