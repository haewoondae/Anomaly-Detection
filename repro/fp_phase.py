import sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from osESD import osESD

pattern = sys.argv[1]
files = sorted(glob.glob(pattern))
if not files and "eps1" in pattern:
    files = sorted(glob.glob(pattern.replace("eps1", "sig1")))
if not files and "sig1" in pattern:
    files = sorted(glob.glob(pattern.replace("sig1", "eps1")))
    
files = files[: int(sys.argv[2]) if len(sys.argv) > 2 else 6]

hist = np.zeros(10, int); tot = 0
for f in files:
    df = pd.read_csv(f); real = df["anomaly"].astype(int).to_numpy()
    idx = osESD(df, value_name="value", anomaly_name="anomaly", size=50, dwin=2, rwin=5, maxr=3,
                alpha=0.01, condition=True, use_author_lambda=True, rep_at="author")
    fp = np.array([i for i in idx if real[i] == 0], dtype=int)
    if len(fp):
        hist += np.bincount((fp % 1000) // 100, minlength=10); tot += len(fp)
print("files", len(files), "FP total", tot, "by phase decile (idx mod 1000):", hist.tolist())
