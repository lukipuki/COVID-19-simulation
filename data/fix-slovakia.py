#!/usr/bin/env python3
import yaml
from datetime import datetime, timedelta


with open("data.yaml", 'r') as stream:
    data_jh = yaml.safe_load(stream)
    extra = {}
    for point in data_jh:
        date = (datetime.strptime(point["date"], '%Y-%m-%d') -
                timedelta(days=1)).strftime('%Y-%m-%d')
        extra[date] = point

with open('data-slovakia.yaml', 'r') as stream:
    data = yaml.safe_load(stream)
    for point in data:
        if point['date'] not in extra:
            continue
        e = extra[point['date']]
        point['recovered'] = e['recovered']
        point['dead'] = e['dead']
        if point['positive'] != e['positive']:
            print(f'Difference for {point["date"]}: {point["positive"]} vs {e["positive"]}')


with open("data-new.yaml", 'w') as f:
    yaml.dump(data, f, default_flow_style=False)
