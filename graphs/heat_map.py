#!/usr/bin/env python3
from datetime import datetime, timedelta
import argparse
import itertools
import numpy as np
import yaml
from yaml import CLoader as Loader
from plotly.graph_objs import Figure, Layout, Scatter
import plotly.express as px

parser = argparse.ArgumentParser(description='COVID-19 visualization for Slovakia')
parser.add_argument('simulated',
                    metavar='simulated',
                    type=str,
                    help=f"YAML file with simulation results")
args = parser.parse_args()

with open(args.simulated, 'r') as stream:
    try:
        data = yaml.load(stream, Loader=Loader)
    except yaml.YAMLError as exc:
        raise exc

    best_errors = {}
    for group in data:
        if "results" not in group:
            continue
        prefix_length = group["params"]["prefix_length"]
        b0 = group["params"]["b0"]
        gamma2 = group["params"]["gamma2"]
        errors = [result["error"] for result in group["results"]]
        if gamma2 not in best_errors:
            best_errors[gamma2] = {}
        best_errors[gamma2][(b0, prefix_length)] = sum(errors) / len(errors)

for item in best_errors.items():
    gamma, gamma_dict = item
    min_b0, max_b0 = min(i[0] for i in gamma_dict.keys()), max(i[0] for i in gamma_dict.keys())
    min_prefix_len, max_prefix_len = min(i[1] for i in gamma_dict.keys()), max(
        i[1] for i in gamma_dict.keys())
    data, prefix_axis, b0_axis = [], [], []
    for prefix_len in range(min_prefix_len, max_prefix_len + 1):
        curr = []
        not_empty = False
        for b0 in range(min_b0, max_b0 + 1):
            if (b0, prefix_len) in gamma_dict:
                curr.append(gamma_dict[(b0, prefix_len)])
                not_empty = True
            else:
                curr.append(0)
        if not_empty:
            prefix_axis.append(prefix_len)
            data.append(curr)
    fig = px.imshow(data[::-1],
                    labels=dict(x="b0", y="Prefix length", color="Average error"),
                    y=prefix_axis[::-1])
    fig.update_xaxes(side="top")
    fig.show()
