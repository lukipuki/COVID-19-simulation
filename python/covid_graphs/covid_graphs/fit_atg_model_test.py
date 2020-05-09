import numpy as np
import pytest

from . import fit_atg_model
from .fit_atg_model import AtgModelFit


def test_fit_atg_model():
    a = 2719.0
    tg = 7.2
    exp = 6.23
    t0 = 2.5
    xs = np.arange(1, 100)

    # Test perfect fit.
    ys = fit_atg_model._model(params=[a, tg, exp, t0], xs=xs)
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    assert np.allclose([fit.a, fit.tg, fit.exp, fit.t0], [a, tg, exp, t0])

    # Test a noisy fit.
    ys += np.random.rand(len(ys))
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    assert [fit.a, fit.tg, fit.exp, fit.t0] == pytest.approx([a, tg, exp, t0], rel=0.1)

    # Test with real-world data. (Jordan until 2020-4-23.)
    # fmt: off
    ys = np.array(
        [
            0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 7, 16, 33, 51, 68, 84, 84, 111, 126, 153, 171,
            211, 216, 227, 238, 237, 239, 237, 249, 247, 244, 230, 217, 209, 202, 204, 195, 197,
            181, 169, 155, 144, 136, 135, 137, 134, 136, 124, 113, 112,
        ]
    )
    # fmt: on
    xs = np.arange(len(ys))
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    assert [fit.a, fit.tg, fit.exp, fit.t0] == pytest.approx([2243, 7, 2, 11], abs=1.0)


def test_atg_model_fit_predict():
    fit = AtgModelFit(a=1.2, tg=2.3, exp=3.4, t0=5.6)
    x = 10.0
    expected = 1.2 / 2.3 * ((x - 5.6) / 2.3) ** 3.4 / np.exp((x - 5.6) / 2.3)
    assert fit.predict(x) == pytest.approx(expected)
    assert fit.predict(4.0) == pytest.approx(0.0)
