import sys, os
sys.stdout.reconfigure(encoding='utf-8')

def parse_file(path):
    raw = open(path, 'rb').read()
    for enc in ['utf-8', 'utf-16le', 'cp949']:
        try:
            text = raw.decode(enc)
            if '||' in text: break
        except Exception:
            pass
    lines = [l.strip().replace('\ufffd', '+/-') for l in text.splitlines() if '||' in l]
    res = {}
    for l in lines:
        parts = l.split('||')
        left, paper = parts[0].strip(), parts[1].strip()
        tokens = left.split()
        strat = tokens[-5]
        files = tokens[-4]
        P = tokens[-3].replace('P=', '').replace('+/-+/-', '+/-')
        R = tokens[-2].replace('R=', '').replace('+/-+/-', '+/-')
        F1 = tokens[-1].replace('F1=', '').replace('+/-+/-', '+/-')
        tgt = ' '.join(tokens[:-5])
        res[(tgt, strat)] = {'files': files, 'P': P, 'R': R, 'F1': F1, 'paper': paper}
    return res

len_data = {L: parse_file(f'results/table5_len{L}.txt') for L in [5, 10, 20, 40]}
eps_data = {E: parse_file(f'results/table5_eps{E}.txt') for E in [1, 300]}

print("=========================================================================================")
print("1. Event Length Sensitivity (eps=100)")
print("=========================================================================================")
for tgt in ["ARIMA1 (Bernoulli)", "ARIMA1 (Linear)", "State-space (Bernoulli)", "State-space (Linear)"]:
    print(f"\n[{tgt}]")
    strats = ["ber", "drift", "block"] if "Bernoulli" in tgt else ["lin", "drift", "block"]
    for s in strats:
        p = len_data[10][(tgt, s)]['paper']
        print(f"  Strategy: {s:<6} (Paper: {p})")
        for L in [5, 10, 20, 40]:
            entry = len_data[L][(tgt, s)]
            print(f"    L={L:2d} (n={entry['files']}): P={entry['P']}  R={entry['R']}  F1={entry['F1']}")

print("\n=========================================================================================")
print("2. Sigma_epsilon Sensitivity (State-space, L=10)")
print("=========================================================================================")
for tgt in ["State-space (Bernoulli)", "State-space (Linear)"]:
    print(f"\n[{tgt}]")
    strats = ["ber", "drift", "block"] if "Bernoulli" in tgt else ["lin", "drift", "block"]
    for s in strats:
        p = len_data[10][(tgt, s)]['paper']
        print(f"  Strategy: {s:<6} (Paper: {p})")
        # eps 1
        e1 = eps_data[1][(tgt, s)]
        print(f"    sigma_eps=  1 (n={e1['files']}): P={e1['P']}  R={e1['R']}  F1={e1['F1']}")
        # eps 100
        e100 = len_data[10][(tgt, s)]
        print(f"    sigma_eps=100 (n={e100['files']}): P={e100['P']}  R={e100['R']}  F1={e100['F1']}")
        # eps 300
        e300 = eps_data[300][(tgt, s)]
        print(f"    sigma_eps=300 (n={e300['files']}): P={e300['P']}  R={e300['R']}  F1={e300['F1']}")
