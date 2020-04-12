import numpy as np
import pytest

import fit_atg_model

def test_fit_atg_model():
    a = 2719.0
    tg = 7.2
    xs = np.arange(1, 100)

    # Test perfect fit.
    ys = fit_atg_model._model(params=[a, tg], xs=xs)
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    assert np.allclose([fit.a, fit.tg], [a, tg])

    # Test a noisy fit.
    ys += np.random.rand(len(ys))
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    assert fit.a == pytest.approx(a, rel=0.1)
    assert fit.tg == pytest.approx(tg, rel=0.1)

    # Test with real-world data. (UK active since 2020-3-7.)
    xs = np.arange(1, 27)
    ys = np.array([
        186.,
        252.,
        299.,
        358.,
        430.,
        430.,
        772.,
        1101.,
        1101.,
        1468.,
        1843.,
        2490.,
        2487.,
        3741.,
        4720.,
        5337.,
        6250.,
        7520.,
        8929.,
        10945.,
        13649.,
        15935.,
        18159.,
        20598.,
        23226.,
        26987.,
    ])
    fit = fit_atg_model.fit_atg_model(xs=xs, ys=ys)
    assert fit.a == pytest.approx(2498, rel=0.01)
    assert fit.tg == pytest.approx(7.3, rel=0.01)
