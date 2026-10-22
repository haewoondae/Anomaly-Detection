r"""Table-3 style ablation (paper Sec. 4.2): osESD vs sosESD / oGESD / norep_osESD.
Usage: python repro/ablation.py <csv_dir> <glob> <size,dwin,rwin,maxr,alpha,cond(0/1)> [workers] [rep_at]
Identical parameters for all variants (as in the paper).
Interpretation choices (paper does not specify further):
  sos   : sequential ESD on the RAW value window of length `size`; no trend vectors, no replacement.
  ogesd : full GESD (largest m with R_m > lambda_m) recomputed from scratch on each trend-vector window;
          trend vectors and replacement kept.
  norep : osESD without replacement of detected anomalies."""
import sys, glob, os, time
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "repro")
from models import osESD_Test, osESD_Transform
from models.osESD_Test import SESD, get_lambda, get_lambda_author
from progress import run_pool


class GESDWindow:
    """Offline GESD (Rosner) re-run on the current sliding window; True if the newest point is flagged."""
    def __init__(self, data, alpha, maxr, use_author_lambda=True):
        self.data = np.asarray(data, float).copy(); self.alpha = alpha; self.maxr = maxr
        self._lam = get_lambda_author if use_author_lambda else get_lambda

    def test(self, on):
        self.data = np.append(self.data[1:], on)
        x = self.data.copy(); idx = np.arange(len(x)); n = len(x); removed, exceed = [], []
        for _ in range(self.maxr):
            if len(x) < 4: break
            sd = x.std(ddof=1)
            if sd <= 1e-12: break
            dev = np.abs(x - x.mean()) / sd; j = int(np.argmax(dev))
            exceed.append(bool(dev[j] > self._lam(self.alpha, len(x)))); removed.append(int(idx[j]))
            x = np.delete(x, j); idx = np.delete(idx, j)
        k = max([m for m, e in enumerate(exceed, 1) if e], default=0)
        return (n - 1) in removed[:k]


def run_variant(variant, data, time_, size, dwin, rwin, maxr, alpha, cond, rep_at="author", author_lambda=True):
    off_d, on_d, off_t, on_t = data[:size], data[size:], time_[:size], time_[size:]
    if variant == "sos":
        s = SESD(off_d, alpha, maxr, use_author_lambda=author_lambda)
        return [size + i for i, x in enumerate(on_d) if s.test(x)]
    c = osESD_Transform.TCHA(off_d, dwin, off_t); r = osESD_Transform.TRES(off_d, rwin, off_t)
    Test = GESDWindow if variant == "ogesd" else SESD
    sc = Test(c.vec, alpha, maxr, author_lambda); sr = Test(r.vec, alpha, maxr, author_lambda)
    out = []
    for i, (x, t) in enumerate(zip(on_d, on_t)):
        ca = sc.test(c.update(x, t)); ra = sr.test(r.update(x, t))
        if (ca and ra) if cond else (ca or ra):
            out.append(size + i)
            if variant != "norep":
                rep = r.loo_prediction("prev" if rep_at in ("prev", "author") else "now")
                c.replace(rep); r.replace(rep)
    return out


def prf(real, pred):
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum())
    fn = int(((real == 1) & (pred == 0)).sum()); tn = int(((real == 0) & (pred == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    return P, R, (2 * P * R / (P + R) if P + R else 0.0), (fp / (fp + tn) if fp + tn else 0.0)


VARIANTS = ("osesd", "sos", "ogesd", "norep")

def one(args):
    path, cfg, rep_at = args
    df = pd.read_csv(path); real = df["anomaly"].astype(int).to_numpy()
    data = df["value"].astype(float).tolist()
    tm = df["timestamps"].tolist() if "timestamps" in df else list(range(1, len(df) + 1))
    res = {}
    for v in VARIANTS:
        t0 = time.time()
        idx = run_variant(v, data, tm, int(cfg[0]), int(cfg[1]), int(cfg[2]), int(cfg[3]), cfg[4], bool(cfg[5]), rep_at)
        pred = np.zeros(len(df), int); pred[idx] = 1
        res[v] = prf(real, pred) + (time.time() - t0,)
    return res

if __name__ == "__main__":
    d, pat, cfgs = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    rep_at = sys.argv[5] if len(sys.argv) > 5 else "author"
    cfg = [float(x) for x in cfgs.split(",")]
    files = sorted(glob.glob(os.path.join(d, pat)))
    with Pool(workers) as pool:
        out = run_pool(pool, one, [(f, cfg, rep_at) for f in files], "ablation", chunksize=2)
    print("variant  files   P      R      F1     TypeI   time(s)")
    for v in VARIANTS:
        m = np.mean([o[v] for o in out], axis=0)
        print("%-7s %5d  %.3f  %.3f  %.3f  %.4f  %.2f" % (v, len(out), m[0], m[1], m[2], m[3], m[4]))
