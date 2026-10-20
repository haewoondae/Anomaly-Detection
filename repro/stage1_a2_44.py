import sys, time
import numpy as np, pandas as pd
sys.path.insert(0, 'src')
from osESD import osESD          # src/osESD.py 래퍼

df = pd.read_csv(sys.argv[1])
real = df['anomaly'].astype(int).to_numpy()
for name, kw in {"author-like": dict(use_author_lambda=True, rep_at="author"),
                 "patched(loo, Rosner)": dict()}.items():
    t0 = time.time()
    idx = osESD(df, value_name='value', anomaly_name='anomaly', **kw)
    sec = time.time() - t0
    pred = np.zeros(len(df), int); pred[idx] = 1
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum()); fn = int(((real == 1) & (pred == 0)).sum())
    P = tp / (tp + fp) if tp + fp else 0; R = tp / (tp + fn) if tp + fn else 0
    print(name, "indices:", list(map(int, idx)), "P=%.3f R=%.3f" % (P, R), "%.3fs" % sec)
