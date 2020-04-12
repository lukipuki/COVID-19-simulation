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

    def predict(self, x: float) -> float:
        ys = _model(params=[self.a, self.tg], xs=[x])
        return ys[0]


def fit_atg_model(xs: np.ndarray, ys: np.ndarray) -> AtgModelFit:
    """
    Fits atg model through `(xs, ys)` datapoints.
    """
    assert len(xs) == len(ys), "Inconsistent number of datapoints to fit."
    assert np.all(xs > 0), "No support for non-positive values for `xs`."
    assert np.all(ys >= 0), "No support for negative values for `ys`."
    a0 = 2000.0
    tg0 = 7.0
    # TODO(miskosz): Handle failures.
    least_squares_result = least_squares(fun=_residuals, x0=[a0, tg0], args=(xs, ys))
    return AtgModelFit(a=least_squares_result.x[0], tg=least_squares_result.x[1])


def _residuals(params: List[float], xs: np.ndarray, ys: np.ndarray) -> float:
    """
    Returns the residual ("error") of model fitting with parameter values `params`
    to the datapoints (xs, ys).

    NOTE: We compute the logarithm in logspace since the data spans multiple orders.
    We don't care if the model is off by 10 for values close to 20000, but we care
    for small values. We choose natural base of the logarithm.
    """
    return np.log(1. + _model(params=params, xs=xs)) - np.log(1. + ys)


def _model(params: List[float], xs: np.ndarray) -> np.ndarray:
    """
    Returns predicted y-values of the model
        y = (a/tg) * (x/tg)^6.23 * e^(-x/tg)
    with parameters `params` for the values `x` in `xs`, where `a=params[0]` and `tg=params[1]`.
    """
    a, tg = params
    # Note(miskosz): Optimise `tg` in logspace if the following line becomes a problem.
    assert tg > 0, f"No support for negative values for `tg` (tg={tg})."
    return (a/tg) * (xs/tg)**EXPONENT * np.exp(-xs/tg)


# Note(miskosz): Lousy test at the bottom of the file O:)
# TODO(miskosz): Add a testing script. Atm can be tested by `pytest graphs/fit_atg_model.py`.
def test_fit_atg_model():
    a = 2719.0
    tg = 7.2
    xs = np.arange(1, 100)

    # Test perfect fit.
    ys = _model(params=[a, tg], xs=xs)
    fit = fit_atg_model(xs=xs, ys=ys)
    assert np.allclose([fit.a, fit.tg], [a, tg])

    # Test noisy fit.
    ys += np.random.rand(len(ys))
    fit = fit_atg_model(xs=xs, ys=ys)
    assert fit.a == pytest.approx(a, rel=0.1)
    assert fit.tg == pytest.approx(tg, rel=0.1)
