"""osESD transform modules: TCHA and TRES.

TCHA  — Change-rate trend vector (Eq. 3 in paper).
TRES  — Residual trend vector   (Eq. 4) with O(1) sliding sum updates.
"""

from collections import deque

import numpy as np


# ===========================================================================
# TCHA: Change-rate trend vector
# ===========================================================================

class TCHA:
    """Change-rate trend vector, Eq. (3).

    Each element is the slope between the two endpoints of a dwin-length
    window:  c_i = (x_{i} - x_{i - dwin}) / (t_{i} - t_{i - dwin})

    Parameters
    ----------
    data : array-like
        Training data (length >= wins).
    wins : int
        Change-rate window size (dwin).
    time : array-like, optional
        Timestamps matching data.  Defaults to 1, 2, …, len(data).
    """

    def __init__(self, data, wins, time=None):
        data = np.asarray(data, dtype=float)
        n = len(data)
        time = (
            np.arange(1, n + 1, dtype=float)
            if time is None
            else np.asarray(time, dtype=float)
        )
        self.wins = wins

        # Keep the last `wins` raw values for future update steps
        self._data = deque(data[-wins:].tolist())
        self._time = deque(time[-wins:].tolist())

        # Build the full training vector
        dt = time[wins - 1:] - time[: n - wins + 1]
        self.vec = (data[wins - 1:] - data[: n - wins + 1]) / dt
        self.last = float(self.vec[-1])

    # ------------------------------------------------------------------

    def _calc(self):
        return (self._data[-1] - self._data[0]) / (self._time[-1] - self._time[0])

    def update(self, x, t=None):
        """Slide one new observation in and return the newest c element."""
        if t is None:
            # Safe default: one step beyond the current last timestamp
            t = self._time[-1] + 1
        self._data.popleft()
        self._data.append(x)
        self._time.popleft()
        self._time.append(float(t))
        self.last = self._calc()
        return self.last

    def replace(self, rep):
        """Replace the most-recently appended raw value with `rep`."""
        self._data[-1] = rep
        self.last = self._calc()


# ===========================================================================
# TRES: Residual trend vector with O(1) sliding sums
# ===========================================================================

class TRES:
    """Residual trend vector, Eq. (4), with O(1) sum-statistic updates.

    Sliding OLS residual:  r_i = x_i - (α̂ + β̂ · t_i)
    where (α̂, β̂) are fitted on the current rwin-length window.

    The regression coefficients are expressed via sufficient statistics:
        β̂ = (Stx - St·Sx/n) / (Stt - St²/n)
        α̂ = (Sx - β̂·St) / n
    All four sums (St, Sx, Stt, Stx) are updated in O(1) by adding the
    new element and subtracting the dropped element.  Periodic full
    recomputation guards against floating-point drift.

    Parameters
    ----------
    data : array-like
    wins : int
        Residual window size (rwin).
    time : array-like, optional
    resum_every : int
        Full recompute of sums every this many online steps (default 5000).
    """

    def __init__(self, data, wins, time=None, resum_every=5000):
        data = np.asarray(data, dtype=float)
        n = len(data)
        time = (
            np.arange(1, n + 1, dtype=float)
            if time is None
            else np.asarray(time, dtype=float)
        )

        self.n = wins
        self.t0 = float(time[0])        # anchor: makes sums numerically smaller
        self.resum_every = resum_every
        self._steps = 0

        # Shift time to reduce magnitude of Stt / Stx
        tt = time - self.t0

        # Sliding deques hold the current window
        self._t = deque(tt[:wins].tolist())
        self._x = deque(data[:wins].tolist())

        # Initialise sum statistics
        self._resum()

        # Build training residual vector
        res = [self._resid()]
        for j in range(wins, n):
            res.append(self._slide(data[j], tt[j]))
        self.vec = np.array(res)
        self.last = res[-1]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resum(self):
        """Full O(wins) recomputation of the four sufficient statistics."""
        t = np.array(self._t)
        x = np.array(self._x)
        self.St = float(t.sum())
        self.Sx = float(x.sum())
        self.Stt = float((t * t).sum())
        self.Stx = float((t * x).sum())

    def _fit(self, n, St, Sx, Stt, Stx):
        """Return (alpha, beta) from sufficient statistics."""
        denom = Stt - St * St / n
        if abs(denom) < 1e-12:
            # Degenerate (all timestamps equal): fall back to mean
            return Sx / n, 0.0
        beta = (Stx - St * Sx / n) / denom
        alpha = (Sx - beta * St) / n
        return alpha, beta

    def _resid(self):
        """Residual of the last element against the current window fit."""
        a, b = self._fit(self.n, self.St, self.Sx, self.Stt, self.Stx)
        return self._x[-1] - (a + b * self._t[-1])

    def _slide(self, x, t):
        """O(1) slide: drop oldest, add newest, update sums, return residual."""
        ot, ox = self._t.popleft(), self._x.popleft()
        self._t.append(t)
        self._x.append(x)
        self.St += t - ot
        self.Sx += x - ox
        self.Stt += t * t - ot * ot
        self.Stx += t * x - ot * ox

        self._steps += 1
        if self._steps % self.resum_every == 0:
            # Periodic recompute to prevent floating-point drift
            self._resum()

        self.last = self._resid()
        return self.last

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self, x, t=None):
        """Slide one new observation in and return the newest residual."""
        if t is None:
            # Safe default in shifted coordinates
            t = self._t[-1] + self.t0 + 1
        return self._slide(x, float(t) - self.t0)

    def loo_prediction(self):
        """Regression prediction at the newest time, fitted WITHOUT the newest point.

        Used as the replacement value when the newest point is an anomaly:
        the predicted 'clean' value given only the n-1 preceding observations.
        """
        tl = self._t[-1]
        xl = self._x[-1]
        a, b = self._fit(
            self.n - 1,
            self.St - tl,
            self.Sx - xl,
            self.Stt - tl * tl,
            self.Stx - tl * xl,
        )
        return a + b * tl

    def replace(self, rep):
        """Replace the most-recently appended value with `rep` and sync sums."""
        prev = self._x[-1]
        self._x[-1] = rep
        self.Sx += rep - prev
        self.Stx += self._t[-1] * (rep - prev)
        self.last = self._resid()

    # ------------------------------------------------------------------
    # Backward-compatibility shims (used by auto_osESD_Detector.py)
    # ------------------------------------------------------------------

    @property
    def data(self):
        return list(self._x)

    @property
    def time(self):
        # Return absolute timestamps (undo the t0 shift)
        return [v + self.t0 for v in self._t]

    @property
    def x_bar(self):
        return self.Sx / self.n

    @property
    def y_bar(self):
        return self.Sx / self.n   # kept for API compat; auto_osESD uses this name

    @property
    def tres(self):
        return list(self.vec)
