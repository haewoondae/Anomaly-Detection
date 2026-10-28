r"""Table-5 style injection-strategy sensitivity (paper Sec. 4.4), unlabeled auto_osESD tuning.
For every target group the tuner is run with (own strategy, drift, block); the chosen parameters are scored against the
TRUE labels over the whole series.
Usage: python repro/table5.py [--grid reduced|full] [--workers 8] [--per 4] [--eps 10] [--length 10] [--seed 0]
Targets (files must exist under gen_out/): ARIMA1_ber_*, ARIMA1_lin_*, statespace_eps<EPS>_ber_*, statespace_eps<EPS>_lin_*"""
import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
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
    prefix_len = int(len(df) * 0.2)
    inj = make_injector(strat, length=length)
    contam = inj(df["value"], seed)
    n_pref = int(contam["anomaly"].astype(int).to_numpy()[:prefix_len].sum())

    t0 = time.time()
    idx = auto_osESD(df, labeled=False, weights=[0, 0, 1, 0], learning_length=0.2, seed=seed,
                     injector=inj, legacy_cap=True, use_author_lambda=True, rep_at="author", **GRIDS[grid])
    pred = np.zeros(len(df), int); pred[list(idx)] = 1
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum()); fn = int(((real == 1) & (pred == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    return target, strat, os.path.basename(path), P, R, (2 * P * R / (P + R) if P + R else 0.0), time.time() - t0, n_pref

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", default="reduced"); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--per", type=int, default=4); ap.add_argument("--eps", default="10")
    ap.add_argument("--length", type=int, default=10); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--target", default="all", choices=["all", "statespace", "arima"])
    a = ap.parse_args()

    arima_dir = "gen_out/arima_big" if os.path.exists("gen_out/arima_big") and len(glob.glob("gen_out/arima_big/ARIMA1_ber_*.csv")) >= a.per else "gen_out/arima"
    ss_dir = "gen_out/statespace_big" if os.path.exists("gen_out/statespace_big") and len(glob.glob(f"gen_out/statespace_big/statespace_sig{a.eps}_ber_*.csv")) >= a.per else "gen_out/statespace"

    ss_ber = f"{ss_dir}/statespace_eps{a.eps}_ber_*.csv"
    if not glob.glob(ss_ber):
        ss_ber = f"{ss_dir}/statespace_sig{a.eps}_ber_*.csv"
    ss_lin = f"{ss_dir}/statespace_eps{a.eps}_lin_*.csv"
    if not glob.glob(ss_lin):
        ss_lin = f"{ss_dir}/statespace_sig{a.eps}_lin_*.csv"

    T = {"ARIMA1 (Bernoulli)": (f"{arima_dir}/ARIMA1_ber_*.csv", "ber"), "ARIMA1 (Linear)": (f"{arima_dir}/ARIMA1_lin_*.csv", "lin"),
         "State-space (Bernoulli)": (ss_ber, "ber"),
         "State-space (Linear)": (ss_lin, "lin")}
    if a.target == "statespace":
        T = {k: v for k, v in T.items() if "State-space" in k}
    elif a.target == "arima":
        T = {k: v for k, v in T.items() if "ARIMA" in k}
    jobs = []
    for tgt, (pat, own) in T.items():
        files = sorted(glob.glob(pat))[: a.per]
        for k, f in enumerate(files):
            for s in (own, "drift", "block"):
                jobs.append((tgt, f, s, a.grid, a.length, a.seed + k))
    print("jobs:", len(jobs), "grid:", a.grid, "per:", a.per)
    with Pool(a.workers) as pool:
        res = run_pool(pool, task, jobs, "table5")

    zero_tasks = [x for x in res if x[7] == 0]
    zero_db = [x for x in res if x[7] == 0 and x[1] in ("drift", "block")]
    print("\n--- Tuning Prefix Anomaly Check ---")
    print(f"Tasks with n_pref == 0: {len(zero_tasks)} / {len(res)} (drift/block: {len(zero_db)} / {sum(1 for x in res if x[1] in ('drift', 'block'))})")
    if zero_tasks:
        print("Note: When n_pref == 0, tuning F1 is degenerate (all 0), so the first grid parameter is picked by tie-break.")

    print("\ntarget | strategy | files | P R F1 (mean) || paper P R F1")
    f1_diffs = []
    f1_diffs_db = []
    f1_diffs_own = []
    for tgt, (pat, own) in T.items():
        for s in (own, "drift", "block"):
            r = [x[3:6] for x in res if x[0] == tgt and x[1] == s]
            if not r: continue
            m = np.mean(r, axis=0); sd = np.std(r, axis=0, ddof=1) if len(r) > 1 else np.zeros(3); p = PAPER[(tgt, s)]
            diff = abs(m[2] - p[2])
            f1_diffs.append(diff)
            if s in ("drift", "block"):
                f1_diffs_db.append(diff)
            else:
                f1_diffs_own.append(diff)
            print("%-24s %-6s %2d  P=%.3f+/-%.3f R=%.3f+/-%.3f F1=%.3f+/-%.3f || %.3f %.3f %.3f" % (tgt, s, len(r), m[0], sd[0], m[1], sd[1], m[2], sd[2], *p))
    if f1_diffs:
        print("Global MAE (|Delta F1| across %d cells): %.4f" % (len(f1_diffs), float(np.mean(f1_diffs))))
        if f1_diffs_db:
            print("8-cell (Drift/Block) MAE: %.4f" % float(np.mean(f1_diffs_db)))
        if f1_diffs_own:
            print("4-cell (Own strategy) MAE: %.4f" % float(np.mean(f1_diffs_own)))

    print("\n--- Paired F1 Differences (per-file) ---")
    for tgt, (pat, own) in T.items():
        by_file = {}
        for x in res:
            if x[0] == tgt:
                by_file.setdefault(x[2], {})[x[1]] = x[5]
        diff_d = [v[own] - v["drift"] for v in by_file.values() if own in v and "drift" in v]
        diff_b = [v[own] - v["block"] for v in by_file.values() if own in v and "block" in v]
        diff_db = [v["drift"] - v["block"] for v in by_file.values() if "drift" in v and "block" in v]
        m_d, s_d = np.mean(diff_d), (np.std(diff_d, ddof=1) if len(diff_d) > 1 else 0.0)
        m_b, s_b = np.mean(diff_b), (np.std(diff_b, ddof=1) if len(diff_b) > 1 else 0.0)
        m_db, s_db = np.mean(diff_db), (np.std(diff_db, ddof=1) if len(diff_db) > 1 else 0.0)
        n = len(diff_d)
        se_d = s_d / np.sqrt(n) if n > 0 else 0.0
        se_b = s_b / np.sqrt(n) if n > 0 else 0.0
        se_db = s_db / np.sqrt(n) if n > 0 else 0.0
        print("%-24s (n=%d)  own-drift: %+.3f+/-%.3f (se=%.3f)  own-block: %+.3f+/-%.3f (se=%.3f)  drift-block: %+.3f+/-%.3f (se=%.3f)" % (tgt, n, m_d, s_d, se_d, m_b, s_b, se_b, m_db, s_db, se_db))

