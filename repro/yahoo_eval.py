r"""Table-2 style evaluation of the author-mode osESD on the Yahoo S5 benchmarks (A1..A4).
Usage: python repro/yahoo_eval.py <root containing A1Benchmark..A4Benchmark> <size,dwin,rwin,maxr,alpha,cond(0/1)> [workers]
Example: python repro/yahoo_eval.py D:\data\yahoo 50,2,5,3,0.01,1 8
Handles the column-name differences of S5: timestamp|timestamps, is_anomaly|anomaly.
Files without any labeled anomaly are excluded from the P/R/F1 means (counted separately)."""
import sys, os, glob, time
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "repro")
from osESD import osESD
from progress import run_pool

GROUPS = ["A1Benchmark", "A2Benchmark", "A3Benchmark", "A4Benchmark"]

def pick(cols, names):
    for n in names:
        if n in cols: return n
    return None

def prf(real, pred):
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum())
    fn = int(((real == 1) & (pred == 0)).sum()); tn = int(((real == 0) & (pred == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    return R, P, (2 * P * R / (P + R) if P + R else 0.0), (fp / (fp + tn) if fp + tn else 0.0)

def one(args):
    path, cfg = args
    group = os.path.basename(os.path.dirname(path))
    try:
        df = pd.read_csv(path)
        lcol = pick(df.columns, ["anomaly", "is_anomaly"]); tcol = pick(df.columns, ["timestamps", "timestamp"])
        size = int(cfg[0])
        if lcol is None or "value" not in df.columns or len(df) <= size + 10:
            return group, os.path.basename(path), "skip", None
        real = df[lcol].astype(int).to_numpy()
        kw = dict(value_name="value", anomaly_name=lcol, size=size, dwin=int(cfg[1]), rwin=int(cfg[2]), maxr=int(cfg[3]),
                  alpha=cfg[4], condition=bool(cfg[5]), use_author_lambda=True, rep_at="author")
        if tcol: kw["timestamp_name"] = tcol
        t0 = time.time(); idx = osESD(df, **kw); sec = time.time() - t0
        pred = np.zeros(len(df), int); pred[list(idx)] = 1
        return group, os.path.basename(path), "ok", dict(on=prf(real[size:], pred[size:]), full=prf(real, pred),
                                                         n_real=int(real.sum()), n_pred=int(pred.sum()), sec=sec)
    except Exception as e:
        return group, os.path.basename(path), "error: %r" % (e,), None

if __name__ == "__main__":
    root, cfgs = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    cfg = [float(x) for x in cfgs.split(",")]
    files = [(f, cfg) for g in GROUPS for f in sorted(glob.glob(os.path.join(root, g, "*.csv")))]
    print("files:", len(files), "cfg:", cfgs)
    with Pool(workers) as pool:
        res = run_pool(pool, one, files, "yahoo_eval", chunksize=4)
    errs = [(g, n, s) for g, n, s, _ in res if s.startswith("error")]
    for e in errs[:10]: print("ERROR", e)
    print("group  files(used/total) noanom zeropred | ONLINE R P F1 TypeI | FULL R P F1 | sec")
    allon = []
    for g in GROUPS:
        rows = [r for gg, _, s, r in res if gg == g and s == "ok"]
        total = sum(1 for gg, _, _, _ in res if gg == g)
        use = [r for r in rows if r["n_real"] > 0]
        if not use:
            print(g, "no usable files"); continue
        on = np.mean([r["on"] for r in use], axis=0); fu = np.mean([r["full"] for r in use], axis=0)
        allon += [r["on"] for r in use]
        print("%-12s %3d/%3d  %3d  %3d | %.3f %.3f %.3f %.4f | %.3f %.3f %.3f | %.2f" % (
            g, len(use), total, len(rows) - len(use), sum(1 for r in use if r["n_pred"] == 0),
            *on, *fu[:3], np.mean([r["sec"] for r in use])))
    if allon:
        m = np.mean(allon, axis=0); print("ALL Yahoo ONLINE: R=%.3f P=%.3f F1=%.3f TypeI=%.4f" % tuple(m))