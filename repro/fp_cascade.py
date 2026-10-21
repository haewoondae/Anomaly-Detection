import sys, os, glob
import numpy as np, pandas as pd
sys.path.insert(0, "src")
from osESD import osESD

def analyze_runs(fp_list):
    if len(fp_list) == 0:
        return []
    diffs = np.diff(fp_list)
    split_pts = np.where(diffs != 1)[0] + 1
    return [len(chunk) for chunk in np.split(fp_list, split_pts)]

def eval_mode(files, rep_mode):
    tot_fp = 0
    all_runs = []
    hist = np.zeros(10, int)
    for f in files:
        df = pd.read_csv(f)
        real = df["anomaly"].astype(int).to_numpy()
        idx = osESD(df, value_name="value", anomaly_name="anomaly", size=50, dwin=2, rwin=5, maxr=3,
                    alpha=0.01, condition=True, use_author_lambda=True, rep_at=rep_mode)
        fp = np.sort([i for i in idx if real[i] == 0])
        tot_fp += len(fp)
        if len(fp):
            all_runs.extend(analyze_runs(fp))
            hist += np.bincount((fp % 1000) // 100, minlength=10)
            
    n_runs = len(all_runs)
    mean_len = float(np.mean(all_runs)) if n_runs else 0.0
    max_len = int(np.max(all_runs)) if n_runs else 0
    ge10 = int(sum(1 for r in all_runs if r >= 10))
    return tot_fp, n_runs, mean_len, max_len, ge10, hist.tolist()

if __name__ == "__main__":
    pattern = sys.argv[1]
    files = sorted(glob.glob(pattern))
    if not files and "eps" in pattern:
        files = sorted(glob.glob(pattern.replace("eps", "sig")))
    if not files and "sig" in pattern:
        files = sorted(glob.glob(pattern.replace("sig", "eps")))
        
    n_files = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    files = files[:n_files]
    
    # Extract label for tag (e.g. eps1, eps10)
    tag = os.path.basename(pattern).split("_")[1]
    
    fp_a, n_a, mean_a, max_a, ge10_a, hist_a = eval_mode(files, "author")
    fp_l, n_l, mean_l, max_l, ge10_l, hist_l = eval_mode(files, "loo")
    
    print(f"{tag} ({len(files)} files) | author: FP={fp_a} runs={n_a} mean={mean_a:.1f} max={max_a} ge10={ge10_a} phase={hist_a} | loo: FP={fp_l} runs={n_l} mean={mean_l:.1f} max={max_l} ge10={ge10_l} phase={hist_l}")
