"""fit_glms drops the odour-intensity terms exactly when the scent statistic IS the intensity.

Hypervigilance tooling plan (R8): in the single-channel and matched-strength layouts
`*_olf_intensity == *_predatorness`, so keeping both makes the GLM singular. The two-channel
layout must keep them (byte-identity of published CSVs).
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                "scripts", "analysis"))
import hiding_drivers as H  # noqa: E402


def _synthetic_D(n=3000, same=True, seed=0):
    rng = np.random.default_rng(seed)
    n_pred = rng.integers(0, 3, n).astype(float)
    n_rab = rng.integers(0, 3, n).astype(float)
    rp = rng.normal(0.6, 0.3, n)
    pp = rng.normal(0.7, 0.3, n)
    L = rng.integers(20, 200, n).astype(float)
    p = 1 / (1 + np.exp(-(-1.5 + 0.5 * rp + 0.3 * n_pred)))
    Y = rng.binomial(L.astype(int), p).astype(float)
    IB = np.zeros((n, 4)); IB[:, 0] = L
    NB = np.zeros((n, 4)); NB[:, 2] = L
    D = dict(n_steps=L, bush_steps=Y, inj0=rng.uniform(0, 100, n), nut0=rng.uniform(0, 100, n),
             n_pred=n_pred, n_rab=n_rab, n_bush=rng.integers(4, 11, n).astype(float),
             n_rock=rng.integers(6, 13, n).astype(float), n_food=rng.integers(1, 5, n).astype(float),
             n_ambush=rng.integers(2, 13, n).astype(float), d_bush0=rng.integers(0, 6, n).astype(float),
             pred_detect=rng.uniform(1, 7, n), pred_delay=rng.uniform(1, 3, n),
             pred_range=rng.uniform(2, 3, n), pred_stamina=rng.uniform(30, 150, n),
             pred_predatorness=pp, rab_predatorness=rp,
             pred_olf_intensity=pp.copy() if same else pp + rng.normal(0, 0.3, n),
             rab_olf_intensity=rp.copy() if same else rp + rng.normal(0, 0.3, n),
             d_pred0=rng.integers(1, 9, n).astype(float),
             pred_detect_max=rng.uniform(1, 7, n), IB=IB, NB=NB,
             inj_sum=L * 10, inj_max=rng.uniform(0, 100, n), nut_sum=L * 50, dmg_sum=rng.uniform(0, 50, n),
             n_ate=rng.integers(0, 20, n).astype(float), n_rest=rng.integers(0, 20, n).astype(float),
             n_pred_near=rng.integers(0, 20, n).astype(float),
             n_rab_near=rng.integers(0, 20, n).astype(float))
    D["pred_detect_min"] = D["pred_detect_max"] - rng.uniform(0, 1, n)
    return D


def test_single_layout_drops_intensity_and_fits(tmp_path):
    uni, multi = H.fit_glms(_synthetic_D(same=True), str(tmp_path), layout="single")
    assert not any("olf_intensity" in t for t in uni.term)
    assert not any("olf_intensity" in t for t in multi.term)
    assert np.isfinite(multi[multi.model.str.startswith("M3")].coef).all()


def test_difference_layout_keeps_intensity(tmp_path):
    uni, multi = H.fit_glms(_synthetic_D(same=False), str(tmp_path), layout="difference")
    assert {"rab_olf_intensity", "pred_olf_intensity"} <= set(uni.term)
    m3 = multi[multi.model.str.startswith("M3")]
    assert {"rab_olf_intensity", "pred_olf_intensity"} <= set(m3.term)


def test_fit_glms_requires_the_layout_keyword(tmp_path):
    with pytest.raises(TypeError):
        H.fit_glms(_synthetic_D(), str(tmp_path))
