import os, sys
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from models.osESD_Transform import TRES


def author_rep(t, x):
    T = np.asarray(t[:-1], float); D = np.asarray(x[:-1], float)   # 마지막 점 제외
    xb, yb = T.mean(), D.mean()
    beta = np.sum((T - xb) * (D - yb)) / np.sum((T - xb) ** 2)
    return (yb - beta * xb) + beta * T[-1]                          # 직전 시점에서 예측


def test_prev_matches_author_formula():
    rng = np.random.default_rng(0)
    for _ in range(100):
        n = 200
        t = np.cumsum(rng.uniform(.5, 1.5, n)); x = np.cumsum(rng.normal(size=n))
        r = TRES(x[:100], wins=10, time=t[:100])
        for j in range(100, 130):
            r.update(x[j], t[j])
        assert abs(r.loo_prediction(at="prev") - author_rep(r.time, r.data)) < 1e-9
        assert abs(r.loo_prediction(at="now") - author_rep(r.time, r.data)) > 1e-9
