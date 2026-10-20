import sys, glob, os
import pandas as pd
sys.path.insert(0, "src")
from models import auto_osESD_Detector as A

GRID = [["--WindowSizes", [50, 100]], ["--AndOr", [True, False]], ["--MaxRs", [3, 10]],
        ["--Dwins", [2, 5, 10]], ["--Rwins", [4, 5, 10]], ["--Alphas", [0.01, 0.05]]]
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.csv"))):
    df = pd.read_csv(f)
    if not {"value", "anomaly"} <= set(df.columns):
        continue
    par_len = int(len(df) * 0.2)
    n_pref = int(df["anomaly"][:par_len].sum())
    _, _, params = A.osESD_Detector_auto(database=df, data_label=True, weights=[0, 0, 1, 0],
                                         par_len=0.2, parameters=GRID, min_max_switch=False,
                                         legacy_cap=True, use_author_lambda=True, rep_at="author")
    print(os.path.basename(f), "N=%d prefix=%d prefix_anoms=%d" % (len(df), par_len, n_pref), "params=", params)
