"""Data augmentation utilities for osESD.

contaminate() injects pseudo-anomalies into a clean time series following
the injection scheme described in Section 3.5 / Eq. (12) of the paper.

Key design decisions
--------------------
* The perturbation scale uses the **local** standard deviation — computed
  on the segment since the previous injected anomaly — rather than the
  cumulative sd of the entire prefix.  This matches the intent of Eq. (12).
* Multiplier distributions match the four named strategies in the paper.
* A seeded RNG is exposed so results are reproducible.
"""

import numpy as np
from scipy.stats import norm

import pandas as pd
import matplotlib.pyplot as plt
import warnings
from datetime import datetime

warnings.filterwarnings(action="ignore")


# ===========================================================================
# Multiplier distributions
# ===========================================================================

def sample_multiplier(kind: str, rng: np.random.Generator) -> float:
    """Return one signed multiplier M drawn from the requested distribution.

    Parameters
    ----------
    kind : str
        One of 'bernoulli'/'ber', 'uniform'/'uni', 'linear'/'lin',
        'quadratic'/'quad'.
    rng : np.random.Generator

    Returns
    -------
    float in [-1, 1]
    """
    s = rng.choice([-1.0, 1.0])
    kind = kind.lower()
    if kind in ("bernoulli", "ber"):
        return s
    if kind in ("linear", "lin"):
        # |M| ~ triangular on [0,1] with PDF f(m)=2m  →  CDF^{-1} = sqrt(U)
        return s * float(np.sqrt(rng.uniform()))
    if kind in ("quadratic", "quad"):
        # |M| ~ PDF f(m)=3m^2  →  CDF^{-1} = U^{1/3}
        return s * float(rng.uniform() ** (1.0 / 3.0))
    if kind in ("uniform", "uni"):
        return float(rng.uniform(-1, 1))
    raise ValueError(
        f"kind must be 'bernoulli', 'uniform', 'linear', or 'quadratic'; got {kind!r}"
    )


# ===========================================================================
# Main injection function
# ===========================================================================

def contaminate(ts, alpha, anom_percent, kind, local_sd=True, seed=None):
    """Inject pseudo-anomalies into time series `ts`.

    Implements Eq. (12):
        x̃_p = x_p  +  M · s_p · z_{1-α/2}

    where s_p is the standard deviation of the *local* segment since the
    previous injected anomaly (local_sd=True, default) or the entire
    prefix (local_sd=False, matches the original author code behaviour).

    Parameters
    ----------
    ts : array-like
        Clean time series.
    alpha : float
        Nominal detection level used to set the injection magnitude.
    anom_percent : float
        Probability that any given time step is selected for injection.
    kind : str
        Multiplier distribution ('bernoulli', 'uniform', 'linear', 'quadratic').
    local_sd : bool
        If True (default) compute s_p on the segment since the last anomaly.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    dict with keys:
        'value'   : np.ndarray  (contaminated series)
        'anomaly' : pd.Categorical (0/1 labels)
    """
    rng = np.random.default_rng(seed)
    y0 = np.asarray(ts, dtype=float)
    y = y0.copy()
    z = norm.ppf(1 - alpha / 2)
    label = np.zeros(len(y), dtype=int)

    prev = 0  # index of the previous injected anomaly (or series start)

    for p in range(1, len(y)):
        if rng.uniform() < anom_percent:
            # Choose the segment for sd estimation
            lo = prev if local_sd else 0
            seg = y0[lo:p]
            if len(seg) < 2:
                seg = y0[:p]
            if len(seg) < 2:
                continue  # not enough data to estimate sd

            sd_p = float(np.std(seg, ddof=1))
            y[p] = y0[p] + sample_multiplier(kind, rng) * sd_p * z
            label[p] = 1
            prev = p

    anomal_val = pd.Series(label, dtype="category")
    return {"value": y, "anomaly": anomal_val}


# ===========================================================================
# Helper utilities (kept for backward compatibility)
# ===========================================================================

def add_timestamp(dataframe):
    if "timestamps" not in dataframe.columns:
        dataframe["timestamps"] = list(range(1, len(dataframe) + 1))
    return dataframe


def change_to_timestamp(df, column, fmt):
    df["timestamps"] = df[column].apply(
        lambda x: datetime.timestamp(datetime.strptime(x, fmt))
    )
    return df


def change_to_index(values, length):
    temp = [0] * length
    for i in values:
        temp[i] = 1
    return temp


def math_round(x):
    M = x // 1
    return M if x - M < 0.5 else M + 1


# ===========================================================================
# Stand-alone multiplier generators (legacy — used by original __main__ block)
# ===========================================================================

def bernoulli(n=10000):
    return np.random.choice([-1, 1], n, p=[0.5, 0.5])


def uniform(n=10000):
    return np.random.uniform(-1, 1, n)


def linear(n=10000):
    x = np.arange(1, n + 1)
    probs = np.linspace(0, 1, n)
    probs /= probs.sum()
    samples = np.random.choice(x / n, size=n, replace=True, p=probs)
    return samples * bernoulli(n)


def quadratic(n=10000):
    x = np.arange(1, n + 1)
    probs = np.linspace(0, 1, n) ** 2
    probs /= probs.sum()
    samples = np.random.choice(x / n, size=n, replace=True, p=probs)
    return samples * bernoulli(n)


if __name__ == "__main__":
    for name, fn in [("bernoulli", bernoulli), ("uniform", uniform),
                     ("linear", linear), ("quadratic", quadratic)]:
        plt.figure()
        plt.hist(fn(), bins=100)
        plt.title(name)
        plt.tight_layout()
        plt.savefig(f"../results/plots/{name}_distribution.png")
        plt.show()
