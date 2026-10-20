import sys, os, glob, time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, "src")
from osESD import osESD

CONFIGS = {
    "A": dict(size=50, condition=True, dwin=2, rwin=5, maxr=3, alpha=0.01),
    "B": dict(size=100, condition=False, dwin=2, rwin=4, maxr=10, alpha=0.05),
    "C": dict(size=100, condition=True, dwin=10, rwin=10, maxr=10, alpha=0.01),
}

def evaluate_single(args):
    fpath, cfg, init_size = args
    df = pd.read_csv(fpath)
    val = df["value"].values
    y_true = df["anomaly"].values
    N = len(y_true)
    
    t0 = time.time()
    # Run osESD with author settings
    preds = osESD(
        df,
        **cfg,
        use_author_lambda=True,
        rep_at="author"
    )
    elapsed = time.time() - t0
    
    y_pred = np.zeros(N, dtype=int)
    for p in preds:
        if 0 <= p < N:
            y_pred[p] = 1
            
    def calc_metrics(yt, yp):
        tp = np.sum((yt == 1) & (yp == 1))
        fp = np.sum((yt == 0) & (yp == 1))
        fn = np.sum((yt == 1) & (yp == 0))
        tn = np.sum((yt == 0) & (yp == 0))
        
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        type1 = fp / (tn + fp) if (tn + fp) > 0 else 0.0
        return rec, prec, f1, type1

    full_m = calc_metrics(y_true, y_pred)
    online_m = calc_metrics(y_true[init_size:], y_pred[init_size:])
    
    return {
        "full": full_m,
        "online": online_m,
        "time": elapsed
    }

def main():
    if len(sys.argv) < 4:
        print("Usage: python repro/run_table2.py <folder> <glob_pattern> <config A/B/C>")
        sys.exit(1)
        
    folder = sys.argv[1]
    pattern = sys.argv[2]
    cfg_name = sys.argv[3].upper()
    
    if cfg_name not in CONFIGS:
        raise ValueError(f"Unknown config: {cfg_name}. Must be A, B, or C.")
        
    cfg = CONFIGS[cfg_name]
    init_size = cfg["size"]
    
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    if not files:
        print(f"No files found matching {os.path.join(folder, pattern)}")
        sys.exit(1)
        
    tasks = [(f, cfg, init_size) for f in files]
    
    # Run in parallel across CPU cores
    max_workers = min(os.cpu_count() or 4, 8)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(evaluate_single, tasks))
        
    full_recs = [r["full"][0] for r in results]
    full_precs = [r["full"][1] for r in results]
    full_f1s = [r["full"][2] for r in results]
    full_t1s = [r["full"][3] for r in results]
    times = [r["time"] for r in results]
    
    on_recs = [r["online"][0] for r in results]
    on_precs = [r["online"][1] for r in results]
    on_f1s = [r["online"][2] for r in results]
    on_t1s = [r["online"][3] for r in results]
    
    print(f"\n=======================================================")
    print(f"Dataset: {folder} ({len(files)} files) | Config: {cfg_name}")
    print(f"Parameters: {cfg}")
    print(f"=======================================================")
    print(f"[Full Range (0..N)]")
    print(f"  Recall     : {np.mean(full_recs):.4f} (std: {np.std(full_recs):.4f})")
    print(f"  Precision  : {np.mean(full_precs):.4f} (std: {np.std(full_precs):.4f})")
    print(f"  F1-score   : {np.mean(full_f1s):.4f} (std: {np.std(full_f1s):.4f})")
    print(f"  Type I Err : {np.mean(full_t1s):.6f}")
    print(f"[Online Range ({init_size}..N)]")
    print(f"  Recall     : {np.mean(on_recs):.4f} (std: {np.std(on_recs):.4f})")
    print(f"  Precision  : {np.mean(on_precs):.4f} (std: {np.std(on_precs):.4f})")
    print(f"  F1-score   : {np.mean(on_f1s):.4f} (std: {np.std(on_f1s):.4f})")
    print(f"  Type I Err : {np.mean(on_t1s):.6f}")
    print(f"  Avg Time   : {np.mean(times):.2f}s per file (Total wall: {np.sum(times):.1f}s CPU)")
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
