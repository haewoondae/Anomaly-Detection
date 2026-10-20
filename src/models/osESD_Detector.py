"""osESD online detector.

Performs offline initialisation on the first `train_size` points, then
processes remaining observations one at a time via the update loop.
"""

from . import osESD_Test, osESD_Transform


def osESD(
    data,
    dwins,
    rwins,
    train_size,
    alpha,
    maxr,
    condition,
    time=None,
    sync_stats=False,
    use_author_lambda=False,
    rep_at="author",
):
    """Run the online sequential ESD detector.

    Parameters
    ----------
    data : list or array-like
        Full time-series values.
    dwins : int
        Change-rate window size (dwin).
    rwins : int
        Residual window size (rwin).
    train_size : int
        Number of points used for offline initialisation.
    alpha : float
        ESD significance level.
    maxr : int
        Maximum number of anomalies tested per window per step.
    condition : bool
        True  → AND condition (both c and r must flag).
        False → OR  condition (either c or r flags).
    time : list, optional
        Timestamps.  Defaults to 1, 2, …, len(data).
    sync_stats : bool, optional
        If True, update the SESD sliding statistics after replacement so
        the test window reflects the corrected value.  The paper does not
        specify this; default is False (off) to match original behaviour.
    use_author_lambda : bool, optional
        Use the author's original lambda denominator (size + t²) instead
        of the Rosner standard (size - 2 + t²).  Default False (Rosner).
    rep_at : str, optional
        Strategy for computing the replacement value when an anomaly occurs:
        - 'prev' or 'author': 이상치를 제외한 n-1개로 적합해 직전 시점에서 예측 (default, replicates original author codebase).
        - 'loo': regression prediction at anomalous timestamp using the leave-one-out
                 fit of preceding n-1 points. (실험 옵션, 작은 rwin(≤5)에서 과탐지 위험이 있음).

    Returns
    -------
    list of int
        Zero-based indices of detected anomalies in `data`.
    """
    if time is None:
        time = list(range(1, len(data) + 1))

    off_d, on_d = data[:train_size], data[train_size:]
    off_t, on_t = time[:train_size], time[train_size:]

    # --- Build transform objects on training window -----------------------
    c = osESD_Transform.TCHA(off_d, dwins, off_t)
    r = osESD_Transform.TRES(off_d, rwins, off_t)

    # --- Initialise SESD detectors from training vectors ------------------
    sc = osESD_Test.SESD(c.vec, alpha, maxr, use_author_lambda=use_author_lambda)
    sr = osESD_Test.SESD(r.vec, alpha, maxr, use_author_lambda=use_author_lambda)

    anomalies = []

    for i, (x, t) in enumerate(zip(on_d, on_t)):
        ca = sc.test(c.update(x, t))
        ra = sr.test(r.update(x, t))

        is_anomaly = (ca and ra) if condition else (ca or ra)

        if is_anomaly:
            anomalies.append(i + train_size)

            rep = r.loo_prediction(at="prev" if rep_at in ("prev", "author") else "now")
            c.replace(rep)
            r.replace(rep)

            # Optionally keep SESD windows consistent with replaced value
            if sync_stats:
                sc.replace_last(c.last)
                sr.replace_last(r.last)

    return anomalies
