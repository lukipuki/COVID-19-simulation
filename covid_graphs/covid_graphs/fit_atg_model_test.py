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

    # Test with real-world data. (UK active since 2020-3-7.)
    xs = np.arange(1, 27)
    ys = np.array(
        [
            186.0,
            252.0,
            299.0,
            358.0,
            430.0,
            430.0,
            772.0,
            1101.0,
            1101.0,
            1468.0,
            1843.0,
            2490.0,
            2487.0,
            3741.0,
            4720.0,
            5337.0,
            6250.0,
            7520.0,
            8929.0,
            10945.0,
            13649.0,
            15935.0,
            18159.0,
            20598.0,
            23226.0,
            26987.0,
        ]
    )
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    # TODO(miskosz): Use a country that is after IP for a stable fit.
    assert [fit.a, fit.tg, fit.exp, fit.t0] == pytest.approx([10, 10, 9, -18], abs=1.0)


def test_atg_model_fit_predict():
    fit = AtgModelFit(a=1.2, tg=2.3, exp=3.4, t0=5.6)
    x = 10.0
    expected = 1.2 / 2.3 * ((x - 5.6) / 2.3) ** 3.4 / np.exp((x - 5.6) / 2.3)
    assert fit.predict(x) == pytest.approx(expected)
    assert fit.predict(4.0) == pytest.approx(0.0)
