import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, "repro")
import data_gen as G

os.makedirs("gen_out/arima_big", exist_ok=True)
os.makedirs("gen_out/statespace_big", exist_ok=True)

rng = np.random.default_rng(7)

print("Generating 20 ARIMA1 datasets for ber and lin...")
for j in range(1, 21):
    for f in ("ber", "lin"):
        raw_ts = G.run_arima(1, length=10000, noise_val=0.3, rng=rng)
        df = G.contaminate_global(raw_ts, alpha=0.05, anom_percent=0.02, func=f, rng=rng)
        path = f"gen_out/arima_big/ARIMA1_{f}_{j}.csv"
        df.to_csv(path, index=False)
print("ARIMA1 generation complete: 40 files.")

print("Generating 20 State-space datasets (sigma=300) for ber and lin...")
for j in range(1, 21):
    for f in ("ber", "lin"):
        raw_ts = G.run_state_space(length=10000, wp=10000, sd_epsilon=300.0, sd_eta=0.1, sd_Xi=0.02, sd_of="y", rng=rng)
        df = G.contaminate_global(raw_ts, alpha=0.01, anom_percent=0.02, func=f, rng=rng)
        path = f"gen_out/statespace_big/statespace_sig300_{f}_{j}.csv"
        df.to_csv(path, index=False)
print("State-space generation complete: 40 files.")
