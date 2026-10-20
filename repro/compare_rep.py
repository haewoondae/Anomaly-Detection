import json, os, sys, collections
import numpy as np, pandas as pd

A, R = (json.load(open(p)) for p in sys.argv[1:3]); D = sys.argv[3]

def f1(idx, real):
    pred = np.zeros(len(real), int); pred[idx] = 1
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum())
    fn = int(((real == 1) & (pred == 0)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0

agg = collections.defaultdict(list)
for k in A:
    f, c = k.split("|")
    real = pd.read_csv(os.path.join(D, f))["anomaly"].astype(int).to_numpy()
    agg[c].append((len(A[k]), len(R[k]), f1(A[k], real), f1(R[k], real), A[k] != R[k]))
print("cfg  n(author) n(loo)  F1(author) F1(loo)  files_differing")
for c, v in sorted(agg.items()):
    a = np.array(v, float)
    print(c, a[:, 0].mean().round(1), a[:, 1].mean().round(1), a[:, 2].mean().round(3), a[:, 3].mean().round(3), int(a[:, 4].sum()), "/", len(v))
