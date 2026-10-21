import sys, os, time
import numpy as np, pandas as pd

sys.path.insert(0, "src")
from osESD import osESD, auto_osESD
from utils import scores_module

def run_t2(path):
    print(f"=== Running Appendix Example t2 (Single osESD Seasonal) on {os.path.basename(path)} ===")
    df = pd.read_csv(path)
    size = 100
    t1 = time.time()
    anoms_2 = osESD(df, value_name='value', anomaly_name='anomaly',
                    size=size, dwin=5, rwin=5, maxr=6, alpha=0.01,
                    use_author_lambda=True, rep_at='author')
    t2 = time.time()
    
    true_outlier = df['anomaly'][(size + 1):].astype(int)
    pred_outlier = pd.Series(0, index=true_outlier.index)
    valid_anoms = [idx for idx in anoms_2 if idx in pred_outlier.index]
    pred_outlier.loc[valid_anoms] = 1
    
    values = scores_module.return_PRF_values(true_outlier, pred_outlier, t1, t2)
    real_indices = true_outlier[true_outlier == 1].index.tolist()
    pred_indices = sorted(valid_anoms)
    
    print(f"Precision : {values[2]}, Recall : {values[3]}, F1-score : {values[4]}, Time : {values[5]} sec")
    print(f"Real ({len(real_indices)}) : {real_indices[:7]} ... {real_indices[-5:]}")
    print(f"Anomalies ({len(pred_indices)}) : {pred_indices[:7]} ... {pred_indices[-5:]}")
    print(f"Anomalies == Real : {pred_indices == real_indices}")
    return values

def run_t4(path):
    print(f"=== Running Appendix Example t4 (128-comb Custom Grid) on {os.path.basename(path)} ===")
    df = pd.read_csv(path)
    t1 = time.time()
    auto_anoms_2 = auto_osESD(df,
                              sizes=[50, 200],
                              conditions=[True, False],
                              alphas=[0.001, 0.05],
                              dwins=[2, 30],
                              rwins=[4, 30],
                              weights=[0, 0, 1, 0],
                              learning_length=0.2,
                              legacy_cap=True,
                              use_author_lambda=True,
                              rep_at='author')
    t2 = time.time()
    
    true_outlier = df['anomaly'].astype(int)
    pred_outlier = pd.Series([1 if i in auto_anoms_2 else 0 for i in range(len(df))], index=df.index)
    values = scores_module.return_PRF_values(true_outlier, pred_outlier, t1, t2)
    
    real_indices = true_outlier[true_outlier == 1].index.tolist()
    pred_indices = sorted(auto_anoms_2)
    
    tp = int(((true_outlier == 1) & (pred_outlier == 1)).sum())
    fp = int(((true_outlier == 0) & (pred_outlier == 1)).sum())
    fn = int(((true_outlier == 1) & (pred_outlier == 0)).sum())
    
    print(f"Precision : {values[2]}, Recall : {values[3]}, F1-score : {values[4]}, Time : {values[5]} sec")
    print(f"Counts : TP={tp}, FP={fp}, FN={fn}, Real={len(real_indices)} -> Recall = {tp}/{len(real_indices)}")
    print(f"Real ({len(real_indices)}) : {real_indices[:7]} ... {real_indices[-5:]}")
    print(f"Anomalies ({len(pred_indices)}) : {pred_indices[:7]} ... {pred_indices[-5:]}")
    if real_indices != pred_indices:
        diff_missing = [x for x in real_indices if x not in pred_indices]
        diff_extra = [x for x in pred_indices if x not in real_indices]
        print(f"Missing from Real: {diff_missing[:10]}")
        print(f"Extra FP: {diff_extra[:10]}")
    return values

def run_t3(path):
    print(f"=== Running Appendix Example t3 (2048-comb Default Grid) on {os.path.basename(path)} ===")
    df = pd.read_csv(path)
    t1 = time.time()
    auto_anoms_1 = auto_osESD(df,
                              weights=[0, 0, 1, 0],
                              learning_length=0.2,
                              legacy_cap=True,
                              use_author_lambda=True,
                              rep_at='author')
    t2 = time.time()
    
    true_outlier = df['anomaly'].astype(int)
    pred_outlier = pd.Series([1 if i in auto_anoms_1 else 0 for i in range(len(df))], index=df.index)
    values = scores_module.return_PRF_values(true_outlier, pred_outlier, t1, t2)
    
    real_indices = true_outlier[true_outlier == 1].index.tolist()
    pred_indices = sorted(auto_anoms_1)
    
    tp = int(((true_outlier == 1) & (pred_outlier == 1)).sum())
    fp = int(((true_outlier == 0) & (pred_outlier == 1)).sum())
    fn = int(((true_outlier == 1) & (pred_outlier == 0)).sum())
    
    print(f"Precision : {values[2]}, Recall : {values[3]}, F1-score : {values[4]}, Time : {values[5]} sec")
    print(f"Counts : TP={tp}, FP={fp}, FN={fn}, Real={len(real_indices)} -> Recall = {tp}/{len(real_indices)}")
    print(f"Real ({len(real_indices)}) : {real_indices[:7]} ... {real_indices[-5:]}")
    print(f"Anomalies ({len(pred_indices)}) : {pred_indices[:7]} ... {pred_indices[-5:]}")
    if real_indices != pred_indices:
        diff_missing = [x for x in real_indices if x not in pred_indices]
        diff_extra = [x for x in pred_indices if x not in real_indices]
        print(f"Missing from Real: {diff_missing[:10]}")
        print(f"Extra FP: {diff_extra[:10]}")
    return values

if __name__ == "__main__":
    mode = sys.argv[1].lower()
    path = sys.argv[2]
    
    if mode == "t2":
        run_t2(path)
    elif mode == "t4":
        run_t4(path)
    elif mode == "t3":
        run_t3(path)
    else:
        print(f"Unknown mode: {mode}. Choose from t2, t4, t3.")
