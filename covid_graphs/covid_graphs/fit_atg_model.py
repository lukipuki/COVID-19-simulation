from dataclasses import dataclass
from typing import List

import numpy as np
import pytest
from scipy.optimize import least_squares

# TODO(miskosz): Pass in as a parameter?
EXPONENT = 6.23

@dataclass
class AtgModelFit:
    """
    Result of fitting (x, y) data samples to the curve:
        y = (a/tg) * (x/tg)^6.23 * e^(-x/tg)
    
    TODO(miskosz): Maybe return also something like a standard deviation of the fit.
    """
    a: float
    tg: float
    x0: float

    def predict(self, x: float) -> float:
        ys = _model(params=[self.a, self.tg, self.x0], xs=np.array([x]))
        return ys[0]


def fit_atg_model(xs: np.ndarray, ys: np.ndarray) -> AtgModelFit:
    """
    Fits atg model through `(xs, ys)` datapoints.
    """
    assert len(xs) == len(ys), "Inconsistent number of datapoints to fit."
    assert np.all(xs > 0), "No support for non-positive values for `xs`."
    assert np.all(ys >= 0), "No support for negative values for `ys`."
    a0 = 10000.0
    tg0 = 8.0
    x00 = 0.0
    least_squares_result = least_squares(fun=_residuals, x0=[a0, tg0, x00], bounds=([0, 0, -np.inf], np.inf), args=(xs, ys))
    return AtgModelFit(a=least_squares_result.x[0], tg=least_squares_result.x[1], x0=least_squares_result.x[2])


def _residuals(params: List[float], xs: np.ndarray, ys: np.ndarray) -> float:
    """
    Returns the residual ("error") of model fitting with parameter values `params`
    to the datapoints (xs, ys).

    Note: The error terms could be computed in logspace so that they are not dominated by datapoints
    with high values. However, it seems this method gives closest results to those of Bodova & Kollar.
    """
    return _model(params=params, xs=xs) - ys


def _model(params: List[float], xs: np.ndarray) -> np.ndarray:
    """
    Returns predicted y-values of the model
        y = (a/tg) * (x/tg)^6.23 * e^(-x/tg)
    with parameters `params` for the values `x` in `xs`, where `a=params[0]` and `tg=params[1]`.
    """
    a, tg, x0 = params
    # Note(miskosz): Optimise `tg` in logspace if the following line becomes a problem.
    assert tg > 0, f"No support for non-positive values for `tg` (tg={tg})."
    xs = np.where(xs < x0, 0, xs - x0)
    return (a/tg) * (xs/tg)**EXPONENT * np.exp(-xs/tg)
