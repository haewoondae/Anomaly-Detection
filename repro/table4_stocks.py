r"""Table-4 stock experiment (paper Sec. 4.3): unlabeled auto_osESD on AAPL / TSLA daily volume.
Usage:  pip install yfinance
        py -3.11 -u repro/table4_stocks.py [--seeds 3] [--workers 6]
The paper's tickers are written 'APPL' (typo for AAPL). Series: AAPL 2001-01-01..2023-06-30 (paper: 5926 pts),
TSLA 2010-06-29..2023-06-30 (paper: 3227 pts); counts from yfinance may differ slightly (print them).
Paper Table 4 chosen parameters [window, cond, maxr, dwin, rwin, alpha]:  AAPL 118, Or, 7, 5, 30, 0.005 ; TSLA 64, And, 3, 30, 5, 0.05
Unlabeled tuning uses random pseudo-anomalies (author injection, global sd), so parameters vary with the seed."""
import sys, os, argparse, time
from multiprocessing import Pool
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "repro")
from models import auto_osESD_Detector as A
from progress import run_pool

SPECS = {"AAPL": ("2000-01-01", "2023-07-01"), "TSLA": ("2010-06-29", "2023-07-01")}   # yfinance 'end' is exclusive

def load(tk):
    os.makedirs("results", exist_ok=True); path = "results/%s_volume.csv" % tk
    if not os.path.exists(path):
        import yfinance as yf
        d = yf.download(tk, start=SPECS[tk][0], end=SPECS[tk][1], auto_adjust=False, progress=False)
        v = d["Volume"].squeeze().astype(float)
        pd.DataFrame({"timestamps": range(1, len(v) + 1), "date": v.index.strftime("%Y-%m-%d"), "value": v.values}).to_csv(path, index=False)
    return pd.read_csv(path)

def task(a):
    tk, seed = a
    df = load(tk); t0 = time.time()
    flags, preds, params = A.osESD_Detector_auto(database=df, data_label=False, weights=[0, 0, 1, 0], par_len=0.2,
                                                 parameters=[], min_max_switch=False, seed=seed, legacy_cap=True,
                                                 use_author_lambda=True, rep_at="author")
    return tk, seed, len(df), params, len(preds), preds[:8], time.time() - t0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", type=int, default=3); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    for tk in SPECS: print(tk, "points:", len(load(tk)))            # load once (also caches the CSV) before forking
    jobs = [(tk, s) for tk in SPECS for s in range(a.seeds)]
    with Pool(a.workers) as pool:
        res = run_pool(pool, task, jobs, "table4_stocks")
    print("ticker seed N | chosen [cond(1=And), window, maxr, dwin, rwin, alpha] | #anoms | first anomalies | sec")
    for tk, s, n, p, k, first, sec in sorted(res):
        print(tk, s, n, p, k, first, "%.0f" % sec)
