"""Tests for osESD implementation and its components."""
import os
import sys
import numpy as np
import pytest

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from models.osESD_Transform import TCHA, TRES
from models.osESD_Test import SESD, get_lambda, get_lambda_author
from models.osESD_Detector import osESD as run_osESD
from utils.data_aug import contaminate, sample_multiplier


def test_tcha_basic_and_default_time():
    data = [10.0, 12.0, 15.0, 14.0, 18.0]
    c = TCHA(data, wins=3)
    assert len(c.vec) == 3
    # Update with default time
    new_c = c.update(22.0)
    assert isinstance(new_c, float)
    # Replace
    c.replace(20.0)
    assert c._data[-1] == 20.0


def test_tres_sliding_vs_polyfit():
    np.random.seed(42)
    data = np.cumsum(np.random.randn(150)).tolist()
    time = list(range(1, 151))
    wins = 10
    r = TRES(data[:50], wins=wins, time=time[:50])

    for i in range(50, 100):
        val = r.update(data[i], time[i])
        tw = np.array(time[i - wins + 1 : i + 1], dtype=float)
        dw = np.array(data[i - wins + 1 : i + 1], dtype=float)
        exp = dw[-1] - np.polyval(np.polyfit(tw, dw, 1), tw[-1])
        assert abs(val - exp) < 1e-9

    # Test LOO prediction
    loo = r.loo_prediction()
    t_loo = np.array(r.time[:-1], dtype=float)
    d_loo = np.array(r.data[:-1], dtype=float)
    exp_loo = np.polyval(np.polyfit(t_loo, d_loo, 1), r.time[-1])
    assert abs(loo - exp_loo) < 1e-9

    # Test replace
    r.replace(loo)
    assert abs(r.last) < 1e-8


def test_sesd_gaussian_normal_and_masking():
    rng = np.random.default_rng(42)
    win_normal = rng.standard_normal(50).tolist()
    sesd = SESD(win_normal, alpha=0.01, maxr=5)
    # Inlier should not flag
    assert sesd.test(0.01) is False

    # Masking scenario: prior spike masking subsequent moderate outlier
    win_mask = [0.1] * 48 + [6.0] + [0.1]
    sesd_mask = SESD(win_mask, alpha=0.05, maxr=5)
    assert sesd_mask.test(2.5) is True


def test_lambda_rosner_vs_author():
    lam_rosner = get_lambda(0.05, 50)
    lam_author = get_lambda_author(0.05, 50)
    assert lam_rosner > lam_author
    assert abs((lam_rosner - lam_author) / lam_rosner) < 0.05


def test_detector_rep_at_options():
    ts = np.cumsum(np.random.default_rng(123).standard_normal(300)).tolist()
    ts[150] += 20.0
    anoms_loo = run_osESD(ts, dwins=5, rwins=10, train_size=80, alpha=0.05, maxr=5, condition=False, rep_at='loo')
    anoms_prev = run_osESD(ts, dwins=5, rwins=10, train_size=80, alpha=0.05, maxr=5, condition=False, rep_at='prev')
    assert 150 in anoms_loo
    assert 150 in anoms_prev


def test_data_aug_multipliers_and_local_sd():
    rng = np.random.default_rng(1)
    for k in ['ber', 'uni', 'lin', 'quad']:
        m = sample_multiplier(k, rng)
        assert -1.0 <= m <= 1.0

    ts = np.concatenate([
        np.random.default_rng(10).normal(0.0, 0.2, 150),
        np.random.default_rng(10).normal(5.0, 2.5, 150)
    ])
    res_g = contaminate(ts, alpha=0.05, anom_percent=0.05, kind='bernoulli', seed=10, local_sd=False)
    res_l = contaminate(ts, alpha=0.05, anom_percent=0.05, kind='bernoulli', seed=10, local_sd=True)
    assert not np.allclose(res_g['value'], res_l['value'])
