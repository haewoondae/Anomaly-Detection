import json, os, sys
import numpy as np, pandas as pd

A, P, O = (json.load(open(p)) for p in sys.argv[1:4])
D = sys.argv[4]

def f1(idx, real):
    pred = np.zeros(len(real), int); pred[idx] = 1
    tp = int(((real == 1) & (pred == 1)).sum()); fp = int(((real == 0) & (pred == 1)).sum())
    fn = int(((real == 1) & (pred == 0)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0; r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0

print("key | author==pypi | patched==author | F1(pypi) F1(patched) | n_pypi n_patched")
bad = 0
for k in sorted(O):
    f, c = k.split("|")
    real = pd.read_csv(os.path.join(D, f))["anomaly"].astype(int).to_numpy()
    same_ap = A.get(k) == O[k]; same_pa = P.get(k) == A.get(k)
    bad += (not same_ap)
    print(k, same_ap, same_pa, "%.3f %.3f" % (f1(O[k], real), f1(P[k], real)), len(O[k]), len(P[k]))
print("author-like != pypi :", bad, "of", len(O))
