r"""Exact appendix examples of the paper (Python). Run from the repo root.
  python repro/appendix_examples.py t2 <seasonal_ber_21.csv>      # osESD, 5.776 s example (Fig. 9 region)
  python repro/appendix_examples.py t4 <seasonal_ber_21.csv>      # auto_osESD custom 128-combination grid (245.853 s example)
  python repro/appendix_examples.py t3 <ARIMA3_lin_4.csv>         # auto_osESD default 2048-combination grid (3478.699 s example)
Expected (paper):
  t2: P=R=F1=1.0 on indices >= size+1; Anomalies == Real = [137,153,214,262,289,374,...,9992,9994]
  t4: P=1.0, R=0.98989898989899 (=98/99), F1=0.9949238578680203; Anomalies start [137,153,214,262,289,374,...,9992,9994]
  t3: P=1.0, R=0.9707317073170731 (=199/205), F1=0.9851485148514851; Anomalies start [97,99,200,279,300,340,...,9965,9971]"""
import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from osESD import osESD, auto_osESD

AUTHOR = dict(use_author_lambda=True, rep_at="author")

def prf(real, pred):
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum()); fn = int(((real == 1) & (pred == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0.0; R = tp / (tp + fn) if tp + fn else 0.0
    return P, R, (2 * P * R / (P + R) if P + R else 0.0), tp, fp, fn

def show(tag, P, R, F, tp, fp, fn, sec, real_idx, pred_idx):
    print(tag, "Precision=%r Recall=%r F1=%r  (TP=%d FP=%d FN=%d)  %.3fs" % (P, R, F, tp, fp, fn, sec))
    print("  Real     :", list(map(int, real_idx[:8])), "...", list(map(int, real_idx[-3:])))
    print("  Anomalies:", list(map(int, pred_idx[:8])), "...", list(map(int, pred_idx[-3:])))

mode, path = sys.argv[1], sys.argv[2]
df = pd.read_csv(path); N = len(df)
if mode == "t2":
    size = 100
    t0 = time.time()
    anoms = osESD(df, value_name="value", anomaly_name="anomaly", size=size, dwin=5, rwin=5, maxr=6, alpha=0.01, **AUTHOR)
    sec = time.time() - t0
    real = df["anomaly"].astype(int).to_numpy(); pred = np.zeros(N, int); pred[list(anoms)] = 1
    s = size + 1                                     # the paper scores only df['anomaly'][(size+1):]
    P, R, F, tp, fp, fn = prf(real[s:], pred[s:])
    show("t2", P, R, F, tp, fp, fn, sec, np.where(real == 1)[0], np.array(sorted(anoms)))
    print("  Anomalies == Real (index >= size+1):", sorted(i for i in anoms if i >= s) == list(np.where(real[s:] == 1)[0] + s))
elif mode in ("t3", "t4"):
    t0 = time.time()
    if mode == "t4":
        idx = auto_osESD(df, sizes=[50, 200], conditions=[True, False], alphas=[0.001, 0.05], dwins=[2, 30], rwins=[4, 30],
                         weights=[0, 0, 1, 0], learning_length=0.2, legacy_cap=True, **AUTHOR)
    else:
        idx = auto_osESD(df, legacy_cap=True, **AUTHOR)
    sec = time.time() - t0
    real = df["anomaly"].astype(int).to_numpy(); pred = np.zeros(N, int); pred[list(idx)] = 1
    P, R, F, tp, fp, fn = prf(real, pred)            # the paper scores the whole series for auto_osESD
    show(mode, P, R, F, tp, fp, fn, sec, np.where(real == 1)[0], np.array(sorted(idx)))
    print("  expected recall: %r" % ((98 / 99) if mode == "t4" else (199 / 205)))
