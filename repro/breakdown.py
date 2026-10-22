import sys, os, glob, time, re
import numpy as np
import pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "src"); sys.path.insert(0, "repro")
from osESD import osESD
from progress import run_pool

def parse_params(param_str):
    parts = [p.strip() for p in param_str.split(",")]
    if len(parts) != 6:
        raise ValueError(f"Param string must be 'size,dwin,rwin,maxr,alpha,cond', got: {param_str}")
    return dict(
        size=int(parts[0]),
        dwin=int(parts[1]),
        rwin=int(parts[2]),
        maxr=int(parts[3]),
        alpha=float(parts[4]),
        condition=bool(int(parts[5])),
    )

def extract_metadata(fname):
    base = os.path.basename(fname)
    meta = {}
    m_ar = re.match(r"(ARIMA\d+)_([a-zA-Z]+)_(\d+)\.csv", base)
    if m_ar:
        meta["scenario"] = m_ar.group(1)
        meta["dist"] = m_ar.group(2)
        return meta
    m_ss = re.match(r"statespace_sig(\d+)_([a-zA-Z]+)_(\d+)\.csv", base)
    if m_ss:
        meta["sigma"] = f"sigma_{m_ss.group(1)}"
        meta["dist"] = m_ss.group(2)
        return meta
    m_sn = re.match(r"seasonal_([a-zA-Z]+)_(\d+)\.csv", base)
    if m_sn:
        meta["dist"] = m_sn.group(1)
        return meta
    return meta

def evaluate_file(args):
    fpath, cfg = args
    df = pd.read_csv(fpath)
    val = df["value"].values
    y_true = df["anomaly"].values
    N = len(y_true)
    init_size = cfg["size"]
    
    t0 = time.time()
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
    meta = extract_metadata(fpath)
    
    return {
        "file": os.path.basename(fpath),
        "meta": meta,
        "full": full_m,
        "online": online_m,
        "time": elapsed
    }

def print_group_table(title, group_dict):
    print(f"\n--- {title} (Online Range) ---")
    print(f"{'Group':<14} | {'N':>3} | {'Recall':>7} | {'Precision':>9} | {'F1-score':>8} | {'Type I Err':>10}")
    print("-" * 62)
    for grp, items in sorted(group_dict.items()):
        recs = [it["online"][0] for it in items]
        precs = [it["online"][1] for it in items]
        f1s = [it["online"][2] for it in items]
        t1s = [it["online"][3] for it in items]
        print(f"{grp:<14} | {len(items):>3} | {np.mean(recs):>7.4f} | {np.mean(precs):>9.4f} | {np.mean(f1s):>8.4f} | {np.mean(t1s):>10.6f}")

def main():
    if len(sys.argv) < 4:
        print("Usage: python repro/breakdown.py <folder> <pattern> <size,dwin,rwin,maxr,alpha,cond>")
        sys.exit(1)
        
    folder = sys.argv[1]
    pattern = sys.argv[2]
    param_str = sys.argv[3]
    
    cfg = parse_params(param_str)
    files = sorted(glob.glob(os.path.join(folder, pattern)))
    if not files:
        print(f"No files matched: {os.path.join(folder, pattern)}")
        sys.exit(1)
        
    tasks = [(f, cfg) for f in files]
    max_workers = min(os.cpu_count() or 4, 8)
    
    t_start = time.time()
    with Pool(max_workers) as pool:
        results = run_pool(pool, evaluate_file, tasks, "breakdown", chunksize=2)
    wall_elapsed = time.time() - t_start
    
    # Global metrics
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
    print(f"Target: {folder} / {pattern} ({len(files)} files)")
    print(f"Params: size={cfg['size']}, dwin={cfg['dwin']}, rwin={cfg['rwin']}, maxr={cfg['maxr']}, alpha={cfg['alpha']}, cond={cfg['condition']}")
    print(f"=======================================================")
    print(f"[Full Range (0..N)]")
    print(f"  Recall     : {np.mean(full_recs):.4f} (std: {np.std(full_recs):.4f})")
    print(f"  Precision  : {np.mean(full_precs):.4f} (std: {np.std(full_precs):.4f})")
    print(f"  F1-score   : {np.mean(full_f1s):.4f} (std: {np.std(full_f1s):.4f})")
    print(f"  Type I Err : {np.mean(full_t1s):.6f}")
    print(f"[Online Range ({cfg['size']}..N)]")
    print(f"  Recall     : {np.mean(on_recs):.4f} (std: {np.std(on_recs):.4f})")
    print(f"  Precision  : {np.mean(on_precs):.4f} (std: {np.std(on_precs):.4f})")
    print(f"  F1-score   : {np.mean(on_f1s):.4f} (std: {np.std(on_f1s):.4f})")
    print(f"  Type I Err : {np.mean(on_t1s):.6f}")
    print(f"  Avg Process Time: {np.mean(times):.2f}s | Wall Time: {wall_elapsed:.2f}s")
    
    # Subgroup breakdowns if applicable
    sigmas = {}
    scenarios = {}
    dists = {}
    for r in results:
        meta = r["meta"]
        if "sigma" in meta:
            sigmas.setdefault(meta["sigma"], []).append(r)
        if "scenario" in meta:
            scenarios.setdefault(meta["scenario"], []).append(r)
        if "dist" in meta:
            dists.setdefault(meta["dist"], []).append(r)
            
    if len(scenarios) > 1:
        print_group_table("Breakdown by Scenario", scenarios)
    if len(sigmas) > 1:
        # Sort sigma numerically
        sigmas_sorted = dict(sorted(sigmas.items(), key=lambda x: int(x[0].split("_")[1])))
        print_group_table("Breakdown by Noise Level (sigma_epsilon)", sigmas_sorted)
    if len(dists) > 1:
        print_group_table("Breakdown by Distribution", dists)
        
    print(f"=======================================================\n")

if __name__ == "__main__":
    main()
