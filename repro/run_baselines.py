r"""Table-2 style comparison harness (v2: threshold rules).
Usage: py -3.11 -u repro/run_baselines.py <csv_dir> "<glob>" [--models osesd,zscore,hwa,if,rrcf,ae,vae,lstm]
                                                            [--train 0.2] [--cfg 50,2,5,3,0.01,1] [--workers 6] [--limit 0]
                                                            [--thr train|oracle|both]
All models are scored on the SAME region (indices >= int(train*N)) against the true labels.
Score-based models (if, rrcf, ae, vae, lstm) are run once and judged with
  train  : score > mean(train scores) + 3*std(train scores) (deployable)
  oracle : flag the k highest test scores, k = #true anomalies in the test region (uses labels; NOT deployable)
Oracle rows are printed as '<model>@oracle'.
Z-Score, HW-A and osESD keep their own rules."""
import sys, os, glob, time, re, argparse
from multiprocessing import Pool
import numpy as np, pandas as pd

sys.path.insert(0, "src")
sys.path.insert(0, "repro")
from progress import run_pool
import baselines as B

CPU = ("osesd", "zscore", "hwa", "if", "rrcf")
GPU = ("ae", "vae", "lstm")
SCORE = ("if", "rrcf", "ae", "vae", "lstm")

def family(path):
    n = os.path.basename(path)
    d = os.path.basename(os.path.dirname(path))
    if d.startswith("A") and d.endswith("Benchmark"):
        return d
    m = re.match(r"(ARIMA\d|statespace|seasonal)", n)
    return m.group(1) if m else d

def load(path):
    df = pd.read_csv(path)
    lc = "anomaly" if "anomaly" in df.columns else "is_anomaly"
    return df, df["value"].to_numpy(float), df[lc].astype(int).to_numpy()

def metrics(real, pred, s):
    r, p = real[s:], pred[s:]
    tp = int(((r == 1) & (p == 1)).sum())
    fp = int(((r == 0) & (p == 1)).sum())
    fn = int(((r == 1) & (p == 0)).sum())
    tn = int(((r == 0) & (p == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0
    R = tp / (tp + fn) if tp + fn else 0.0
    F1 = 2 * P * R / (P + R) if P + R else 0.0
    TypeI = fp / (fp + tn) if fp + tn else 0.0
    return R, P, F1, TypeI

def get_scores(name, x, ntr, opts):
    if name == "if":
        return B.iforest(x, ntr, feat=opts["if_feat"], fit=opts["if_fit"], return_scores=True)
    if name == "rrcf":
        return B.rrcf_det(x, ntr, return_scores=True)
    return B.torch_det(name, x, ntr, feat=opts["dl_feat"], fit=opts["dl_fit"], return_scores=True)

def run_osesd(df, x, cfg):
    from osESD import osESD
    kw = dict(value_name="value", anomaly_name="anomaly" if "anomaly" in df.columns else "is_anomaly",
              size=int(cfg[0]), dwin=int(cfg[1]), rwin=int(cfg[2]), maxr=int(cfg[3]),
              alpha=cfg[4], condition=bool(cfg[5]), use_author_lambda=True, rep_at="author")
    for c in ("timestamps", "timestamp"):
        if c in df.columns:
            kw["timestamp_name"] = c
            break
    pred = np.zeros(len(x), int)
    pred[list(osESD(df, **kw))] = 1
    return pred

def task(a):
    path, name, train, cfg, thr, opts = a
    fam = family(path)
    try:
        df, x, real = load(path)
        ntr = int(train * len(x))
        if real.sum() == 0 or ntr < 100:
            return [(fam, name, None)]
        t0 = time.time()
        if name in SCORE:
            s = get_scores(name, x, ntr, opts)
            sec = time.time() - t0
            out = []
            if thr in ("train", "both"):
                out.append((fam, name, metrics(real, B._flag(s, ntr, 3.0), ntr) + (sec,)))
            if thr in ("oracle", "both"):
                out.append((fam, name + "@oracle", metrics(real, B.topk_pred(s, ntr, int(real[ntr:].sum())), ntr) + (sec,)))
            return out
        if name == "osesd":
            pred = run_osesd(df, x, cfg)
        elif name == "zscore":
            pred = B.zscore(x, ntr)
        else:
            pred = B.hwa(x, ntr)
        return [(fam, name, metrics(real, pred, ntr) + (time.time() - t0,))]
    except Exception as e:
        return [(fam, name, "error: %r" % (e,))]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("glob")
    ap.add_argument("--models", default="osesd,zscore,hwa,if,rrcf,ae,vae,lstm")
    ap.add_argument("--train", type=float, default=0.2)
    ap.add_argument("--cfg", default="50,2,5,3,0.01,1")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--thr", default="train", choices=["train", "oracle", "both"])
    ap.add_argument("--if-feat", default="win", choices=["win", "raw", "rawdiff", "diff"])
    ap.add_argument("--if-fit", default="train", choices=["train", "all"])
    ap.add_argument("--dl-feat", default="win", choices=["win", "diff", "center"])
    ap.add_argument("--dl-fit", default="train", choices=["train", "all"])
    a = ap.parse_args()

    cfg = [float(v) for v in a.cfg.split(",")]
    files = sorted(glob.glob(os.path.join(a.root, a.glob), recursive=True))
    if a.limit:
        files = files[:a.limit]
    models = a.models.split(",")
    res = []
    cpu = [m for m in models if m in CPU]
    gpu = [m for m in models if m in GPU]
    opts = {"if_feat": a.if_feat, "if_fit": a.if_fit, "dl_feat": a.dl_feat, "dl_fit": a.dl_fit}

    if cpu:
        with Pool(a.workers) as pool:
            for r in run_pool(pool, task, [(f, m, a.train, cfg, a.thr, opts) for f in files for m in cpu], "baselines-cpu"):
                res += r

    for m in gpu:
        print("[%s] sequential on GPU/CPU, %d files" % (m, len(files)), flush=True)
        for i, f in enumerate(files):
            res += task((f, m, a.train, cfg, a.thr, opts))
            if (i + 1) % 20 == 0:
                print("[%s] %d/%d" % (m, i + 1, len(files)), flush=True)

    names = []
    for m in models:
        if m in SCORE:
            if a.thr in ("train", "both"):
                names.append(m)
            if a.thr in ("oracle", "both"):
                names.append(m + "@oracle")
        else:
            names.append(m)

    errs = [r for r in res if isinstance(r[2], str)]
    for e in errs[:8]:
        print("ERROR", e)

    print("family | model | files | R P F1 TypeI | sec | flagged/true (=R/P)")
    for fam in sorted({r[0] for r in res}):
        for m in names:
            v = [r[2] for r in res if r[0] == fam and r[1] == m and isinstance(r[2], tuple)]
            if v:
                z = np.mean(v, axis=0)
                rp_ratio = z[0] / z[1] if z[1] > 0 else float("nan")
                print("%-12s %-12s %3d %.3f %.3f %.3f %.4f %.2f %.2f" % (fam, m, len(v), *z, rp_ratio))
