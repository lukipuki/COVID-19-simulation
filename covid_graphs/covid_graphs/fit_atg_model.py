from dataclasses import dataclass
from typing import List

import numpy as np
from scipy.optimize import least_squares


@dataclass
class AtgModelFit:
    a: float
    tg: float
    exp: float
    t0: float

    def predict(self, x: float) -> float:
        ys = _model(params=[self.a, self.tg, self.exp, self.t0], xs=np.array([x]))
        return ys[0]

    # TODO: simplify the usage of this class so that we don't have to do this
    def shift_forward(self, day_count: int) -> None:
        self.t0 -= day_count


def fit_atg_model(xs: np.ndarray, ys: np.ndarray) -> AtgModelFit:
    """
    Fits atg model through `(xs, ys)` datapoints.
    """
    assert len(xs) == len(ys), "Inconsistent number of datapoints to fit."
    assert np.all(ys >= 0), "No support for negative values for `ys`."
    a_init = 2000.0
    tg_init = 7.0
    exp_init = 6.23
    t0_init = xs[0]
    least_squares_result = least_squares(
        fun=_residuals,
        x0=[a_init, tg_init, exp_init, t0_init],
        bounds=([0.0, 0.0, 0.0, xs[0]], np.inf),
        args=(xs, ys),
    )
    a, tg, exp, t0 = least_squares_result.x
    return AtgModelFit(a=a, tg=tg, exp=exp, t0=t0)


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
    Returns predicted y-values of the model for values `x` in `xs`:
        x' = (x-t0) / tg
        y = (a/tg) * (x')^exp * e^(-x')  | if x' > 0
          = 0                            | otherwise.
    with parameters `a, tg, exp`, and `t0` passed in  `params` .
    """
    a, tg, exp, t0 = params
    x_prime = np.maximum(0.0, (xs - t0)) / tg
    return (a / tg) * x_prime ** exp * np.exp(-x_prime)
