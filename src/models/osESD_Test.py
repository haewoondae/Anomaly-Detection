
import numpy as np
import scipy.stats as stats


def get_lambda(alpha, size):
    """Critical value lambda_m of Eq. (2).

    size = n - m + 1 (shrinks by 1 each ESD iteration).

    NOTE: The denominator uses (size - 2 + t²) which matches the Rosner (1983)
    standard formula:
        lambda_m = (n-m) * t_{p, n-m-1} / sqrt((n-m-1 + t²)(n-m+1))
    The original author code uses (size + t²) in the denominator, yielding
    a lambda ~1.6% smaller at typical window sizes. Both versions are supported
    via the `use_author_lambda` flag for A/B comparison against the Appendix example.
    """
    if size < 4:
        return 0.0
    p = 1 - alpha / (2 * size)
    t = stats.t.ppf(p, size - 2)
    return (size - 1) * t / np.sqrt((size - 2 + t * t) * size)


def get_lambda_author(alpha, size):
    """Author's original lambda formula (size + t² denominator) kept for A/B."""
    if size < 4:
        return 0.0
    p = 1 - alpha / (2 * size)
    t = stats.t.ppf(p, size - 2)
    return (size - 1) * t / np.sqrt((size + t * t) * size)


class SESD:
    """Sequential ESD on a sliding vector.

    Used for both the change-rate (TCHA) and residual (TRES) vectors.
    Replaces the original SESD_tres / SESD_tcha pair which were identical.

    Parameters
    ----------
    data : array-like
        Initial window values (length = sliding window size).
    alpha : float
        Significance level for the ESD critical value.
    maxr : int
        Maximum number of outliers to strip per call to test().
    use_author_lambda : bool
        If True, use the author's original lambda formula instead of the
        Rosner standard formula. Default False (Rosner).
    """

    def __init__(self, data, alpha=0.01, maxr=10, use_author_lambda=False):
        self.data = np.asarray(data, dtype=float).copy()
        self.size = len(self.data)
        self.alpha = alpha
        self.maxr = maxr
        self._lam = get_lambda_author if use_author_lambda else get_lambda
        # O(1) sliding statistics
        self.mean = float(self.data.mean())
        self.sqsum = float(np.sum(self.data ** 2))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def test(self, on):
        """Slide one new value in, test whether it is anomalous.

        Returns True if the newest point (last index) is flagged as an
        outlier by the sequential ESD procedure.
        """
        out = self.data[0]
        self.data = np.append(self.data[1:], on)
        self.mean += (on - out) / self.size
        self.sqsum += on * on - out * out

        # Work on local copies so object state is not corrupted mid-loop
        data_, mean_, sqsum_, size_ = (
            self.data.copy(), self.mean, self.sqsum, self.size
        )

        for _ in range(self.maxr):
            if size_ < 4:
                return False
            var = (sqsum_ - size_ * mean_ ** 2) / (size_ - 1)
            if var <= 1e-12:
                # Near-constant window: no meaningful test possible
                return False
            sd_ = np.sqrt(var)
            ares = np.abs(data_ - mean_) / sd_
            idx = int(np.argmax(ares))

            if ares[idx] <= self._lam(self.alpha, size_):
                # Test fails: the largest deviation is not significant → stop
                return False

            if idx == size_ - 1:
                # The most extreme point IS the newest one → anomaly confirmed
                return True

            # Most extreme point is an older spike masking the new value.
            # Remove it and continue (ESD sequential stripping).
            x = data_[idx]
            mean_ = (size_ * mean_ - x) / (size_ - 1)
            sqsum_ -= x * x
            data_ = np.delete(data_, idx)
            size_ -= 1

        return False

    def replace_last(self, new):
        """Replace the most-recently appended value with a regression prediction.

        Called after anomaly replacement so that the SESD window reflects
        the corrected value rather than the detected outlier.
        """
        old = self.data[-1]
        self.data[-1] = new
        self.mean += (new - old) / self.size
        self.sqsum += new * new - old * old


# ---------------------------------------------------------------------------
# Backward-compatibility aliases (used by auto_osESD_Detector.py)
# ---------------------------------------------------------------------------

class SESD_tres(SESD):
    """Alias kept for backward compatibility with auto_osESD_Detector.py."""
    def __init__(self, data, alpha=0.01, maxr=10, use_author_lambda=False):
        super().__init__(data=np.asarray(data, dtype=float), alpha=alpha, maxr=maxr, use_author_lambda=use_author_lambda)


class SESD_tcha(SESD):
    """Alias kept for backward compatibility with auto_osESD_Detector.py."""
    def __init__(self, data, alpha=0.01, maxr=10, use_author_lambda=False):
        super().__init__(data=np.asarray(data, dtype=float), alpha=alpha, maxr=maxr, use_author_lambda=use_author_lambda)
