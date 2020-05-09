# Code inspired by a program from Vladimír Boža

import random
from pathlib import Path
from typing import List

import click
import click_pathlib
import matplotlib.pyplot as plt
import numpy as np
import pymc3 as pm

from . import country_report
from .country_graph import CountryGraph, GraphType
from .fit_atg_model import AtgModelFit
from .formula import FittedFormula
from .predictions import CountryPrediction, PredictionEvent


def fit_bayesian_model(cases: np.ndarray) -> List[AtgModelFit]:
    base_length = 800
    with pm.Model() as model:  # noqa: F841
        days = np.arange(len(cases))

        alpha = pm.Uniform("alpha", 1, 20)
        shift = pm.Uniform("shift", 0, 40)
        peak = pm.Uniform("peak", 30, 80)
        mult = pm.Uniform("mult", -30, 20)

        tg = pm.Deterministic("tg", peak / alpha)
        x = pm.math.maximum(0, (days - shift) / tg)
        x_prev = pm.math.maximum(0, (days - 1 - shift) / tg)
        exp_cases = pm.Deterministic(
            "exp_cases",
            pm.math.exp(mult - x) * (x ** alpha) - pm.math.exp(mult - x_prev) * (x_prev ** alpha),
        )

        sigma = pm.HalfCauchy("sigma", beta=500)
        # likelihood = pm.Normal("y", mu=exp_cases, sigma=sigma, observed=cases)
        # likelihood = pm.Cauchy("y", alpha=exp_cases, beta=sigma, observed=cases)
        likelihood = pm.Laplace("obs", mu=exp_cases, b=sigma, observed=cases)  # noqa: F841

        step = pm.NUTS(target_accept=0.9)
        start = pm.find_MAP()
        trace = pm.sample(
            2 * base_length, chains=4, cores=4, tune=base_length, start=start, step=step
        )
        trace = trace[base_length:]

    pm.traceplot(trace)
    plt.show()

    alpha_t = trace["alpha"][-base_length:]
    shift_t = trace["shift"][-base_length:]
    tg_t = trace["tg"][-base_length:]
    a_t = np.exp(trace["mult"][-base_length:]) * tg_t

    return [
        AtgModelFit(exp=alpha, tg=tg, a=a, t0=shift + 1)
        for alpha, tg, a, shift in zip(alpha_t, tg_t, a_t, shift_t)
    ]


@click.command(help="COVID-19 country growth visualization")
@click.argument("filename", required=True, type=click_pathlib.Path(exists=True))
@click.argument("cutoff", required=False, type=int, default=0)
def calculate_posterior(filename: Path, cutoff: int):
    report = country_report.create_report(filename)

    used_length = len(report.dates) - cutoff
    print(used_length)
    cases = np.diff(report.cumulative_active[:used_length])

    fits = random.sample(fit_bayesian_model(cases), 100)
    print("Five random fits:")
    for fit in fits[:5]:
        print(fit)

    last_data_date = report.dates[used_length - 1]
    predictions = [
        CountryPrediction(
            prediction_event=PredictionEvent(
                name=f"daily_fit_{last_data_date.strftime('%Y_%m_%d')}_{i}",
                last_data_date=last_data_date,
                prediction_date=last_data_date,
            ),
            country=report.short_name,
            formula=FittedFormula(fit, report.dates[0], last_data_date),
        )
        for i, fit in enumerate(fits)
    ]
    country_graph = CountryGraph(report=report, country_predictions=predictions)
    country_graph.create_country_figure(graph_type=GraphType.BayesPredictions).show()
