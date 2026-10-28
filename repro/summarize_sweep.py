import os, glob, re
import numpy as np

PAPER = {
    ('ARIMA1 (Bernoulli)', 'ber'): (0.9688, 0.9954, 0.9819),
    ('ARIMA1 (Bernoulli)', 'drift'): (0.6781, 1.0, 0.8082),
    ('ARIMA1 (Bernoulli)', 'block'): (0.6507, 1.0, 0.7884),
    ('ARIMA1 (Linear)', 'lin'): (0.9617, 0.9853, 0.9734),
    ('ARIMA1 (Linear)', 'drift'): (0.8145, 0.9902, 0.8938),
    ('ARIMA1 (Linear)', 'block'): (0.8016, 0.9902, 0.8860),
    ('State-space (Bernoulli)', 'ber'): (0.9854, 0.9806, 0.9830),
    ('State-space (Bernoulli)', 'drift'): (0.8929, 0.9662, 0.9281),
    ('State-space (Bernoulli)', 'block'): (0.9855, 0.9951, 0.9903),
    ('State-space (Linear)', 'lin'): (1.0, 0.8043, 0.8916),
    ('State-space (Linear)', 'drift'): (0.9231, 0.8571, 0.8889),
    ('State-space (Linear)', 'block'): (0.9345, 0.8626, 0.8971),
}

lengths = [5, 10, 20, 40, 80, 160]
all_data = {}

for L in lengths:
    path = f'results/table5_len{L}.txt'
    with open(path, 'rb') as f:
        b = f.read()
    if b.startswith(b'\xff\xfe'):
        text = b.decode('utf-16', errors='replace')
    else:
        text = b.decode('utf-8', errors='replace')
    data = {}
    mae = None
    paired = {}
    for line in text.splitlines():
        m = re.match(r'^([\w\s()-]+?)\s+(ber|lin|drift|block)\s+(\d+)\s+P=([\d.]+)\+\/-([\d.]+)\s+R=([\d.]+)\+\/-([\d.]+)\s+F1=([\d.]+)\+\/-([\d.]+)', line)
        if m:
            tgt = m.group(1).strip()
            strat = m.group(2).strip()
            p, p_sd = float(m.group(4)), float(m.group(5))
            r, r_sd = float(m.group(6)), float(m.group(7))
            f1, f1_sd = float(m.group(8)), float(m.group(9))
            data[(tgt, strat)] = (p, p_sd, r, r_sd, f1, f1_sd)
        m_mae = re.search(r'Global MAE.*:\s*([\d.]+)', line)
        if m_mae:
            mae = float(m_mae.group(1))
        m_p = re.match(r'^([\w\s()-]+?)\s+\(n=\d+\)\s+own-drift:\s*([+-][\d.]+)\+\/-([\d.]+)\s+own-block:\s*([+-][\d.]+)\+\/-([\d.]+)\s+drift-block:\s*([+-][\d.]+)\+\/-([\d.]+)', line)
        if m_p:
            tgt = m_p.group(1).strip()
            paired[tgt] = (float(m_p.group(2)), float(m_p.group(3)),
                           float(m_p.group(4)), float(m_p.group(5)),
                           float(m_p.group(6)), float(m_p.group(7)))
    if mae is None and len(data) == 12:
        diffs = [abs(data[k][4] - PAPER[k][2]) for k in PAPER]
        mae = float(np.mean(diffs))
    all_data[L] = {'data': data, 'mae': mae, 'paired': paired}

print("=== 12-Cell Global MAE vs L ===")
for L in lengths:
    mae_val = all_data[L]["mae"]
    print(f"L = {L:<3}: MAE = {mae_val:.4f}" if mae_val is not None else f"L = {L:<3}: N/A")

print("\n=== Detailed F1 and Precision Table across L ===")
targets = [
    ('ARIMA1 (Bernoulli)', 'ber'),
    ('ARIMA1 (Bernoulli)', 'drift'),
    ('ARIMA1 (Bernoulli)', 'block'),
    ('ARIMA1 (Linear)', 'lin'),
    ('ARIMA1 (Linear)', 'drift'),
    ('ARIMA1 (Linear)', 'block'),
    ('State-space (Bernoulli)', 'ber'),
    ('State-space (Bernoulli)', 'drift'),
    ('State-space (Bernoulli)', 'block'),
    ('State-space (Linear)', 'lin'),
    ('State-space (Linear)', 'drift'),
    ('State-space (Linear)', 'block'),
]

header = f"{'Target':<24} {'Strat':<6} {'Paper F1':<8} " + " ".join([f"L={L:<5} F1" for L in lengths])
print(header)
print("-" * len(header))
for tgt, strat in targets:
    paper_f1 = PAPER[(tgt, strat)][2]
    f1_vals = []
    for L in lengths:
        val = all_data[L]['data'].get((tgt, strat))
        if val:
            f1_vals.append(f"{val[4]:.3f}")
        else:
            f1_vals.append(" N/A ")
    print(f"{tgt:<24} {strat:<6} {paper_f1:<8.3f} " + "   ".join(f1_vals))

print("\n=== Precision across L ===")
header_p = f"{'Target':<24} {'Strat':<6} {'Paper P':<8} " + " ".join([f"L={L:<5} P " for L in lengths])
print(header_p)
print("-" * len(header_p))
for tgt, strat in targets:
    paper_p = PAPER[(tgt, strat)][0]
    p_vals = []
    for L in lengths:
        val = all_data[L]['data'].get((tgt, strat))
        if val:
            p_vals.append(f"{val[0]:.3f}")
        else:
            p_vals.append(" N/A ")
    print(f"{tgt:<24} {strat:<6} {paper_p:<8.3f} " + "   ".join(p_vals))

print("\n=== Paired Differences Summary across L ===")
for tgt in ['ARIMA1 (Bernoulli)', 'ARIMA1 (Linear)', 'State-space (Bernoulli)', 'State-space (Linear)']:
    print(f"\n[{tgt}]")
    print(f"{'L':<4} | {'own - drift':<18} | {'own - block':<18} | {'drift - block':<18}")
    print("-" * 62)
    for L in lengths:
        p = all_data[L]['paired'].get(tgt)
        if p:
            print(f"{L:<4} | {p[0]:+.3f}+/-{p[1]:.3f}      | {p[2]:+.3f}+/-{p[3]:.3f}      | {p[4]:+.3f}+/-{p[5]:.3f}")
