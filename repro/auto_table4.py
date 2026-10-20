import sys, os, time
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from models import auto_osESD_Detector as A

def run(path):
    df = pd.read_csv(path); real = df["anomaly"].astype(int).to_numpy()
    t0 = time.time()
    flags, _, params = A.osESD_Detector_auto(database=df, data_label=True, weights=[0, 0, 1, 0], par_len=0.2,
                                             parameters=[], min_max_switch=False, legacy_cap=True,
                                             use_author_lambda=True, rep_at="author")
    init = int(params[1]); pred = np.array(flags); r, p = real[init:], pred[init:]
    tp = int(((r == 1) & (p == 1)).sum()); fp = int(((r == 0) & (p == 1)).sum()); fn = int(((r == 1) & (p == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    F = 2 * P * R / (P + R) if P + R else 0.0
    return os.path.basename(path), params, P, R, F, time.time() - t0

if __name__ == "__main__":
    tasks = sys.argv[1:]
    n_workers = min(len(tasks), 4)
    with Pool(n_workers) as pool:
        for name, params, P, R, F, sec in pool.imap_unordered(run, tasks):
            print("%-24s params=%s  P=%.4f R=%.4f F1=%.4f  (%.0fs)" % (name, params, P, R, F, sec), flush=True)
