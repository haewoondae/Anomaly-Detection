r"""Sensitivity sweep of fixed osESD configs over the Yahoo S5 groups (upper-bound analysis, NOT a reproduction:
configs are selected with the test labels).
Usage: python repro/yahoo_sweep.py <root with A1Benchmark..A4Benchmark> [workers]
Writes results/yahoo_sweep.csv and prints the best config per group and the best single config overall."""
import sys, os, glob, csv, collections
from multiprocessing import Pool
import numpy as np
sys.path.insert(0, "src"); sys.path.insert(0, "repro")
from yahoo_eval import one, GROUPS
from progress import run_pool

CFGS = [(50, dw, rw, mr, al, c) for c in (1, 0) for mr in (3, 10) for dw in (2, 5) for rw in (4, 10) for al in (0.001, 0.01, 0.05)]

def work(a):
    path, cfg = a
    return cfg, one((path, list(cfg)))

if __name__ == "__main__":
    root = sys.argv[1]; workers = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    files = [f for g in GROUPS for f in sorted(glob.glob(os.path.join(root, g, "*.csv")))]
    tasks = [(f, c) for c in CFGS for f in files]
    print("configs:", len(CFGS), "files:", len(files), "tasks:", len(tasks))
    agg = collections.defaultdict(list)
    with Pool(workers) as pool:
        for cfg, (g, name, status, r) in run_pool(pool, work, tasks, "yahoo_sweep", chunksize=16):
            if status == "ok" and r["n_real"] > 0:
                agg[(cfg, g)].append(r["on"])                # (R, P, F1, TypeI) on the online range
    os.makedirs("results", exist_ok=True)
    rows = []
    for (cfg, g), v in agg.items():
        m = np.mean(v, axis=0); rows.append((cfg, g, len(v), *m))
    with open("results/yahoo_sweep.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["size", "dwin", "rwin", "maxr", "alpha", "and", "group", "files", "R", "P", "F1", "TypeI"])
        for cfg, g, n, R, P, F, T in sorted(rows, key=lambda x: (x[1], -x[5])):
            w.writerow(list(cfg) + [g, n, "%.4f" % R, "%.4f" % P, "%.4f" % F, "%.5f" % T])
    print("best config per group (by mean F1):")
    for g in GROUPS:
        cand = [r for r in rows if r[1] == g]
        if cand:
            b = max(cand, key=lambda x: x[5]); print("  %-12s cfg=%s  R=%.3f P=%.3f F1=%.3f TypeI=%.4f" % (g, b[0], b[3], b[4], b[5], b[6]))
    by = collections.defaultdict(dict)
    for cfg, g, n, R, P, F, T in rows: by[cfg][g] = F
    full = {c: np.mean([d[g] for g in GROUPS]) for c, d in by.items() if len(d) == len(GROUPS)}
    if full:
        c = max(full, key=full.get); print("best single config (mean group F1 = %.3f): %s" % (full[c], c))
        print("  per group F1:", {g: round(by[c][g], 3) for g in GROUPS})
