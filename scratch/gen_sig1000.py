import os, sys
sys.path.insert(0, ".")
import numpy as np
import pandas as pd
from repro.data_gen import run_state_space, contaminate_global

out_dir = "gen_out/statespace"
os.makedirs(out_dir, exist_ok=True)
funcs = ["ber", "uni", "lin", "quad"]

# Use a fixed seed for reproducible generation
rng = np.random.default_rng(1000)
sig = 1000.0

print("Generating 25 State-space datasets with sigma_epsilon = 1000.0...")
for j in range(1, 26):
    func = funcs[(j - 1) % 4]
    raw_ts = run_state_space(length=10000, wp=10000, sd_epsilon=sig, sd_eta=0.1, sd_Xi=0.02, sd_of="y", rng=rng)
    df = contaminate_global(raw_ts, alpha=0.01, anom_percent=0.02, func=func, rng=rng)
    fname = f"statespace_sig{int(sig)}_{func}_{j}.csv"
    df.to_csv(os.path.join(out_dir, fname), index=False)
print("Complete!")
