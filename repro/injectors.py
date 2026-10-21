"""Pseudo-anomaly injectors for the unlabeled auto_osESD tuning (paper Sec. 3.5 / 4.4).
make_injector(kind) returns f(series, seed) -> {'value': ndarray, 'anomaly': pd.Series(category 0/1)}.
  kind in ber / uni / lin / quad : author injection (cumulative sd of the clean prefix, local_sd=False)
  kind in drift / block          : manual patterns of Sec. 4.4 (ASSUMED details: event length `length`, magnitude M*sd*z
                                   with M = +-1 and sd = sd of the clean prefix before the event start)
    drift : offset grows linearly over the event (steady increase over a window)
    block : constant offset over the event (constant magnitude over a fixed duration)
The paper does not give the event length; `length` is a free parameter (default 10)."""
import numpy as np, pandas as pd
from scipy.stats import norm


def _prefix_sd(y0):
    n = np.arange(1, len(y0) + 1, dtype=float)
    c1, c2 = np.cumsum(y0), np.cumsum(y0 * y0)
    var = np.where(n > 1, (c2 - c1 * c1 / n) / np.maximum(n - 1, 1), 0.0)
    return np.sqrt(np.maximum(var, 0.0))               # sd of y0[:t+1]


def pattern_injector(kind, alpha=0.05, rate=0.02, length=10):
    z = norm.ppf(1 - alpha / 2)

    def inject(series, seed=None):
        rng = np.random.default_rng(seed)
        y0 = np.asarray(series, dtype=float); y = y0.copy(); lab = np.zeros(len(y0), dtype=int)
        sd = _prefix_sd(y0); i = 2; p_start = rate / (length * (1 - rate))   # so that labeled points ~= rate * N
        while i < len(y0) - length:
            if rng.uniform() < p_start:
                mag = rng.choice([-1.0, 1.0]) * sd[i - 1] * z
                prof = (np.arange(length) + 1) / length if kind == "drift" else np.ones(length)
                y[i:i + length] += mag * prof; lab[i:i + length] = 1; i += length
            else:
                i += 1
        return {"value": y, "anomaly": pd.Series(lab, dtype="category")}
    return inject


def make_injector(kind, alpha=0.05, rate=0.02, length=10):
    if kind in ("drift", "block"):
        return pattern_injector(kind, alpha, rate, length)
    from utils.data_aug import contaminate
    return lambda series, seed=None: contaminate(series, alpha, rate, kind, seed=seed, local_sd=False)
