import sys, json, inspect, time
import pandas as pd

mode, csv, out = sys.argv[1:4]
if mode != "pypi":
    sys.path.insert(0, "src")
from osESD import auto_osESD

print("signature:", inspect.signature(auto_osESD))
df = pd.read_csv(csv)
GRID = dict(sizes=[50, 100], conditions=[True, False], maxrs=[3, 10],
            dwins=[2, 5, 10], rwins=[4, 5, 10], alphas=[0.01, 0.05])
extra = dict(legacy_cap=True, use_author_lambda=True, rep_at="author") if mode == "author" else {}
t0 = time.time()
idx = auto_osESD(df, labeled=True, value_name="value", anomaly_name="anomaly",
                 weights=[0, 0, 1, 0], learning_length=0.2, **GRID, **extra)
idx = sorted(int(i) for i in idx)
json.dump(idx, open(out, "w"))
print(mode, csv, "n_pred =", len(idx), "%.1fs" % (time.time() - t0))
