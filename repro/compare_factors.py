import json, os, sys
import numpy as np, pandas as pd

A, P, L, R = (json.load(open(p)) for p in sys.argv[1:5])
D = sys.argv[5]

def f1(idx, real):
    pred = np.zeros(len(real), int); pred[idx] = 1
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum())
    fn = int(((real == 1) & (pred == 0)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0

print("key | lam_only==author | rep_only==author | n(author,lam,rep,patched) | F1(author,lam,rep,patched)")
for k in sorted(A):
    if P[k] == A[k]:
        continue
    f = k.split("|")[0]
    real = pd.read_csv(os.path.join(D, f))["anomaly"].astype(int).to_numpy()
    fs = " ".join("%.3f" % f1(x[k], real) for x in (A, L, R, P))
    print(k, L[k] == A[k], R[k] == A[k], [len(x[k]) for x in (A, L, R, P)], fs)
