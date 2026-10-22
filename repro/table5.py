r"""Table-5 style injection-strategy sensitivity (paper Sec. 4.4), unlabeled auto_osESD tuning.
For every target group the tuner is run with (own strategy, drift, block); the chosen parameters are scored against the
TRUE labels over the whole series.
Usage: python repro/table5.py [--grid reduced|full] [--workers 8] [--per 4] [--eps 10] [--length 10] [--seed 0]
Targets (files must exist under gen_out/): ARIMA1_ber_*, ARIMA1_lin_*, statespace_eps<EPS>_ber_*, statespace_eps<EPS>_lin_*"""
import sys, os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
import glob, argparse, time
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "repro")
from osESD import auto_osESD
from injectors import make_injector
from progress import run_pool

GRIDS = {
    "reduced": dict(sizes=[50, 100], conditions=[True, False], maxrs=[3, 5, 10], dwins=[2, 5, 10], rwins=[4, 5, 10], alphas=[0.005, 0.05]),
    "full": {},                                             # default 2048-combination grid (Table 6)
}
PAPER = {  # Table 5: (P, R, F1)
    ("ARIMA1 (Bernoulli)", "ber"): (0.9688, 0.9954, 0.9819), ("ARIMA1 (Bernoulli)", "drift"): (0.6781, 1.0, 0.8082),
    ("ARIMA1 (Bernoulli)", "block"): (0.6507, 1.0, 0.7884), ("ARIMA1 (Linear)", "lin"): (0.9617, 0.9853, 0.9734),
    ("ARIMA1 (Linear)", "drift"): (0.8145, 0.9902, 0.8938), ("ARIMA1 (Linear)", "block"): (0.8016, 0.9902, 0.8860),
    ("State-space (Bernoulli)", "ber"): (0.9854, 0.9806, 0.9830), ("State-space (Bernoulli)", "drift"): (0.8929, 0.9662, 0.9281),
    ("State-space (Bernoulli)", "block"): (0.9855, 0.9951, 0.9903), ("State-space (Linear)", "lin"): (1.0, 0.8043, 0.8916),
    ("State-space (Linear)", "drift"): (0.9231, 0.8571, 0.8889), ("State-space (Linear)", "block"): (0.9345, 0.8626, 0.8971),
}

def task(a):
    target, path, strat, grid, length, seed = a
    df = pd.read_csv(path); real = df["anomaly"].astype(int).to_numpy()
    t0 = time.time()
    idx = auto_osESD(df, labeled=False, weights=[0, 0, 1, 0], learning_length=0.2, seed=seed,
                     injector=make_injector(strat, length=length), legacy_cap=True, use_author_lambda=True, rep_at="author", **GRIDS[grid])
    pred = np.zeros(len(df), int); pred[list(idx)] = 1
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum()); fn = int(((real == 1) & (pred == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    return target, strat, os.path.basename(path), P, R, (2 * P * R / (P + R) if P + R else 0.0), time.time() - t0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default="reduced"); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per", type=int, default=4); ap.add_argument("--eps", default="10")
    ap.add_argument("--length", type=int, default=10); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    ss_ber = f"gen_out/statespace/statespace_eps{a.eps}_ber_*.csv"
    if not glob.glob(ss_ber):
        ss_ber = f"gen_out/statespace/statespace_sig{a.eps}_ber_*.csv"
    ss_lin = f"gen_out/statespace/statespace_eps{a.eps}_lin_*.csv"
    if not glob.glob(ss_lin):
        ss_lin = f"gen_out/statespace/statespace_sig{a.eps}_lin_*.csv"

    T = {"ARIMA1 (Bernoulli)": ("gen_out/arima/ARIMA1_ber_*.csv", "ber"), "ARIMA1 (Linear)": ("gen_out/arima/ARIMA1_lin_*.csv", "lin"),
         "State-space (Bernoulli)": (ss_ber, "ber"),
         "State-space (Linear)": (ss_lin, "lin")}
    jobs = []
    for tgt, (pat, own) in T.items():
        files = sorted(glob.glob(pat))[: a.per]
        for f in files:
            for s in (own, "drift", "block"):
                jobs.append((tgt, f, s, a.grid, a.length, a.seed))
    print("jobs:", len(jobs), "grid:", a.grid)
    with Pool(a.workers) as pool:
        res = run_pool(pool, task, jobs, "table5")
    print("target | strategy | files | P R F1 (mean) || paper P R F1")
    for tgt, (pat, own) in T.items():
        for s in (own, "drift", "block"):
            r = [x[3:6] for x in res if x[0] == tgt and x[1] == s]
            if not r: continue
            m = np.mean(r, axis=0); p = PAPER[(tgt, s)]
            print("%-24s %-6s %2d  %.3f %.3f %.3f || %.3f %.3f %.3f" % (tgt, s, len(r), *m, *p))
