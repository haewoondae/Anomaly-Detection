"""Baseline detectors for the Table-2 comparison (paper Sec. 4.1): Z-Score, HW-A, IF, RRCF, AE, VAE, LSTM-ED.
Every function: det(x, ntr, **kw) -> (pred int array, same length as x).
x is a 1-D float array; the first `ntr` points are the (unlabeled) training part; only indices >= ntr are scored.
The paper does NOT specify architectures, window lengths or thresholds, so these are ASSUMED defaults; only rankings/trends should be compared with the paper.
Threshold rule (all learned models): score > mean(train scores) + k*std(train scores), k=3."""
import numpy as np

def windows(x, w):
    idx = np.arange(w)[None, :] + np.arange(len(x) - w + 1)[:, None]
    return x[idx]  # row i ends at point i+w-1

def _std(x, ntr):
    return (x - x[:ntr].mean()) / (x[:ntr].std() + 1e-9)

def _flag(scores_by_point, ntr, k):
    s = scores_by_point
    tr = s[:ntr][np.isfinite(s[:ntr])]
    thr = tr.mean() + k * tr.std()
    pred = np.zeros(len(s), int)
    pred[ntr:] = (np.nan_to_num(s[ntr:], nan=-np.inf) > thr)
    return pred

def topk_pred(s, ntr, k):
    """ORACLE rule: flag the k highest-scoring points of the test region (k = number of true anomalies there)."""
    pred = np.zeros(len(s), int)
    if k <= 0:
        return pred
    t = np.nan_to_num(s[ntr:], nan=-np.inf)
    pred[np.argsort(-t, kind="stable")[:k] + ntr] = 1
    return pred

def zscore(x, ntr, w=50, k=3.0):
    cs = np.r_[0.0, np.cumsum(x)]
    cs2 = np.r_[0.0, np.cumsum(x * x)]
    pred = np.zeros(len(x), int)
    for t in range(max(ntr, w), len(x)):
        m = (cs[t] - cs[t - w]) / w
        v = max((cs2[t] - cs2[t - w]) / w - m * m, 1e-12)
        pred[t] = abs(x[t] - m) / np.sqrt(v) > k
    return pred

def _period(tr):
    y = tr - np.polyval(np.polyfit(np.arange(len(tr)), tr, 1), np.arange(len(tr)))
    n = len(y)
    f = np.fft.rfft(y, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    ac /= ac[0] + 1e-12
    lo, hi = 4, min(n // 3, 400)
    if hi <= lo:
        return None
    lag = lo + int(np.argmax(ac[lo:hi]))
    return lag if ac[lag] > 0.3 else None

def hwa(x, ntr, m=None, k=3.0):
    """Additive Holt-Winters. Smoothing parameters and initial states are fitted on the training part with statsmodels;
    one-step-ahead residuals are then produced by running the (verified) additive recursion over the whole series."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    tr = x[:ntr]
    m = m or _period(tr)
    seas = m is not None and ntr >= 2 * m + 2
    kw = dict(trend="add", seasonal="add" if seas else None, seasonal_periods=m if seas else None)
    p = ExponentialSmoothing(tr, **kw).fit().params
    a, bt = p["smoothing_level"], p["smoothing_trend"]
    g = p["smoothing_seasonal"] if seas else 0.0
    l, b = p["initial_level"], p["initial_trend"]
    s = list(p["initial_seasons"]) if seas else [0.0]
    res = np.empty(len(x))
    for t, yt in enumerate(x):
        s0 = s[0] if seas else 0.0
        res[t] = yt - (l + b + s0)
        ln = a * (yt - s0) + (1 - a) * (l + b)
        bn = bt * (ln - l) + (1 - bt) * b
        if seas:
            s = s[1:] + [g * (yt - l - b) + (1 - g) * s0]
        l, b = ln, bn
    sd = res[:ntr].std() + 1e-12
    pred = np.zeros(len(x), int)
    pred[ntr:] = np.abs(res[ntr:]) > k * sd
    return pred

def iforest(x, ntr, w=32, k=3.0, seed=0, return_scores=False, feat="win", fit="train"):
    """feat: win (w-point window, current) | raw (value) | rawdiff (value + first difference) | diff (first difference)
       fit : train (first ntr points only) | all (whole series, transductive)"""
    from sklearn.ensemble import IsolationForest
    z = _std(x, ntr)
    if feat == "win":
        X = windows(z, w)
        off = w - 1
    elif feat == "raw":
        X = z.reshape(-1, 1)
        off = 0
    elif feat == "rawdiff":
        X = np.c_[z, np.r_[0.0, np.diff(z)]]
        off = 0
    elif feat == "diff":
        X = np.r_[0.0, np.diff(z)].reshape(-1, 1)
        off = 0
    else:
        raise ValueError(feat)
    n_fit = len(X) if fit == "all" else ntr - off
    f = IsolationForest(n_estimators=100, random_state=seed).fit(X[:n_fit])
    s = np.full(len(x), np.nan)
    s[off:] = -f.score_samples(X)
    if return_scores:
        return s
    return _flag(s, ntr, k)

def cover_mean(sw, n, w):
    """window score -> point score: mean over the windows covering the point"""
    m = len(sw); pe = np.zeros(n); cnt = np.zeros(n)
    for j in range(w): pe[j:j + m] += sw; cnt[j:j + m] += 1
    s = pe / np.maximum(cnt, 1); s[cnt == 0] = np.nan
    return s

def rrcf_det(x, ntr, w=32, trees=40, tree_size=256, k=3.0, seed=0, return_scores=False):
    import rrcf
    X = windows(_std(x, ntr), w)
    np.random.seed(seed)
    forest = [rrcf.RCTree() for _ in range(trees)]
    cd = np.zeros(len(X))
    for i in range(len(X)):
        for tr in forest:
            if len(tr.leaves) > tree_size:
                tr.forget_point(i - tree_size)
            tr.insert_point(X[i], index=i)
            cd[i] += tr.codisp(i) / trees
    s = cover_mean(cd, len(x), w)
    if return_scores:
        return s
    return _flag(s, ntr, k)

def torch_det(kind, x, ntr, w=32, epochs=40, k=3.0, seed=0, device=None, batch=256, return_scores=False, feat="win", fit="train"):
    import torch, torch.nn as nn
    torch.manual_seed(seed)
    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    z = _std(x, ntr)
    if feat == "diff":
        z = np.r_[0.0, np.diff(z)]
        z = z / (z[:ntr].std() + 1e-9)
    W = windows(z, w)
    if feat == "center":
        W = W - W.mean(1, keepdims=True)
    X = torch.tensor(W, dtype=torch.float32)
    ntrw = ntr - w + 1
    Xtr = (X if fit == "all" else X[:ntrw]).to(dev)

    class AE(nn.Module):
        def __init__(s):
            super().__init__()
            s.e = nn.Sequential(nn.Linear(w, 16), nn.ReLU(), nn.Linear(16, 6))
            s.d = nn.Sequential(nn.Linear(6, 16), nn.ReLU(), nn.Linear(16, w))
        def forward(s, a):
            return s.d(s.e(a)), 0.0

    class VAE(nn.Module):
        def __init__(s):
            super().__init__()
            s.e = nn.Sequential(nn.Linear(w, 16), nn.ReLU())
            s.mu = nn.Linear(16, 4)
            s.lv = nn.Linear(16, 4)
            s.d = nn.Sequential(nn.Linear(4, 16), nn.ReLU(), nn.Linear(16, w))
        def forward(s, a):
            h = s.e(a)
            mu, lv = s.mu(h), s.lv(h)
            z = mu + torch.randn_like(mu) * torch.exp(0.5 * lv) if s.training else mu
            return s.d(z), -0.5 * torch.mean(1 + lv - mu ** 2 - lv.exp())

    class LSTMED(nn.Module):
        def __init__(s):
            super().__init__()
            s.enc = nn.LSTM(1, 32, batch_first=True)
            s.dec = nn.LSTM(32, 32, batch_first=True)
            s.out = nn.Linear(32, 1)
        def forward(s, a):
            _, (h, _) = s.enc(a.unsqueeze(-1))
            y, _ = s.dec(h[-1].unsqueeze(1).repeat(1, a.shape[1], 1))
            return s.out(y).squeeze(-1), 0.0

    net = {"ae": AE, "vae": VAE, "lstm": LSTMED}[kind]().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    for _ in range(epochs):
        net.train()
        perm = torch.randperm(len(Xtr), device=dev)
        for i in range(0, len(Xtr), batch):
            b = Xtr[perm[i:i + batch]]
            rec, kl = net(b)
            loss = ((rec - b) ** 2).mean() + 1e-3 * kl
            opt.zero_grad()
            loss.backward()
            opt.step()
    net.eval(); sc = []
    with torch.no_grad():
        for i in range(0, len(X), 2048):
            b = X[i:i + 2048].to(dev); rec, _ = net(b); sc.append(((rec - b) ** 2).cpu())   # (batch, w) position-wise squared error
    E = torch.cat(sc).numpy(); m = len(E); n = len(x)
    pe = np.zeros(n); cnt = np.zeros(n)
    for j in range(w):                                   # position j of window i is point i+j
        pe[j:j + m] += E[:, j]; cnt[j:j + m] += 1
    s = pe / np.maximum(cnt, 1)                          # mean error of the point over all windows covering it
    s[cnt == 0] = np.nan
    if return_scores: return s
    return _flag(s, ntr, k)
