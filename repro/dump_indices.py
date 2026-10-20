import sys, json, os, glob
import pandas as pd

mode, data_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
if mode != "pypi":
    sys.path.insert(0, "src")
from osESD import osESD

CFGS = {
    "A": dict(size=100, dwin=5,  rwin=5,  maxr=10, alpha=0.01,  condition=True),
    "B": dict(size=50,  dwin=2,  rwin=4,  maxr=3,  alpha=0.05,  condition=False),
    "C": dict(size=150, dwin=10, rwin=10, maxr=7,  alpha=0.001, condition=True),
    "D": dict(size=50,  dwin=2,  rwin=10, maxr=3,  alpha=0.05,  condition=False),   # OR, 큰 rwin
    "E": dict(size=50,  dwin=2,  rwin=4,  maxr=3,  alpha=0.05,  condition=True),    # AND, 작은 rwin
    "F": dict(size=50,  dwin=2,  rwin=10, maxr=3,  alpha=0.05,  condition=True),    # AND, 큰 rwin
}
EXTRA = {
    "author":   dict(use_author_lambda=True,  rep_at="author"),
    "patched":  {},
    "lam_only": dict(use_author_lambda=False, rep_at="author"),   # Rosner λ + 저자식 치환
    "rep_only": dict(use_author_lambda=True,  rep_at="loo"),      # 저자 λ + LOO(현재 시점) 치환
    "pypi":     {},
}[mode]
res = {}
for f in sorted(glob.glob(os.path.join(data_dir, "*.csv"))):
    df = pd.read_csv(f)
    if not {"value", "anomaly"} <= set(df.columns):
        print("skip", f, list(df.columns)); continue
    for c, kw in CFGS.items():
        idx = osESD(df.copy(), value_name="value", anomaly_name="anomaly", **kw, **EXTRA)
        res[os.path.basename(f) + "|" + c] = [int(i) for i in idx]
        print(mode, os.path.basename(f), c, len(idx))
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
json.dump(res, open(out, "w"))
