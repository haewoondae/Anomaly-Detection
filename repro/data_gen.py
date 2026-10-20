import sys, os
import numpy as np
import pandas as pd
from scipy import stats

def get_anomaly_multipliers(func, size, rng):
    func = func.lower()
    signs = rng.choice([-1.0, 1.0], size=size, p=[0.5, 0.5])
    if func in ("ber", "bernoulli"):
        return signs
    elif func in ("uni", "uniform"):
        return rng.uniform(-1.0, 1.0, size=size)
    elif func in ("lin", "linear"):
        # linear density f(x) = 2x on [0, 1] -> CDF F(x) = x^2 -> inverse CDF x = sqrt(u)
        u = rng.uniform(0.0, 1.0, size=size)
        return np.sqrt(u) * signs
    elif func in ("quad", "quadratic"):
        # quadratic density f(x) = 3x^2 on [0, 1] -> CDF F(x) = x^3 -> inverse CDF x = u^(1/3)
        u = rng.uniform(0.0, 1.0, size=size)
        return (u ** (1.0 / 3.0)) * signs
    else:
        raise ValueError(f"Unknown anomaly function: {func}")

def contaminate_global(ts, alpha=0.05, anom_percent=0.02, func="ber", rng=None):
    if rng is None:
        rng = np.random.default_rng()
    
    L = len(ts)
    ts_out = ts.copy().astype(float)
    anom_index = []
    
    # Pre-generate multipliers and uniform random tests
    multipliers = get_anomaly_multipliers(func, L, rng)
    randoms = rng.uniform(0.0, 1.0, size=L)
    crit_z = stats.norm.ppf(1.0 - alpha / 2.0)
    
    # Running mean and variance using R's exact formula
    # len=1: mean=ts[0], sd=0
    running_mean = float(ts_out[0])
    running_sd = 0.0
    
    for i in range(1, L):
        val = ts_out[i]
        # Update running stats
        # In R: Len is length of previous List (which is i)
        Len = i
        new_std = np.sqrt(((Len - 1) / Len) * (running_sd ** 2) + (1.0 / (Len + 1)) * ((val - running_mean) ** 2))
        new_mean = running_mean * (Len / (Len + 1)) + val / (Len + 1)
        
        running_mean = new_mean
        running_sd = new_std
        
        if randoms[i] < anom_percent:
            mult = multipliers[i]
            anom_index.append(i)
            ts_out[i] += mult * crit_z * running_sd

    anomal_val = np.zeros(L, dtype=int)
    anomal_val[anom_index] = 1
    
    df = pd.DataFrame({
        "timestamps": np.arange(L),
        "value": ts_out,
        "anomaly": anomal_val
    })
    return df

# --- ARIMA Scenarios ---
def run_arima(scenario, length=10000, noise_val=0.3, rng=None):
    if rng is None:
        rng = np.random.default_rng()
        
    alpha1 = np.array([0.6, -0.5, 0.4, -0.4, 0.3])
    beta1 = np.array([0.3, -0.2])
    
    seq_d0 = np.zeros(length)
    
    if scenario == 1:
        last_seq = noise_val * rng.normal(0, 1, len(alpha1))
        last_noise = noise_val * rng.normal(0, 1, len(beta1))
        for t in range(length):
            noise_t = rng.normal(0, noise_val)
            val = np.sum(alpha1 * last_seq) + np.sum(beta1 * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
    elif scenario == 2:
        noise_terms = rng.uniform(-noise_val, noise_val, size=length)
        last_seq = rng.uniform(-noise_val, noise_val, size=len(alpha1))
        last_noise = rng.uniform(-noise_val, noise_val, size=len(beta1))
        half = length // 2
        for t in range(half):
            noise_t = noise_terms[t]
            val = np.sum(alpha1 * last_seq) + np.sum(beta1 * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
        alpha2 = np.array([-0.4, -0.5, 0.4, 0.4, 0.1])
        beta2 = np.array([-0.3, 0.2])
        for t in range(half, length):
            noise_t = noise_terms[t]
            val = np.sum(alpha2 * last_seq) + np.sum(beta2 * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
    elif scenario == 3:
        noise_terms = rng.uniform(-noise_val, noise_val, size=length)
        last_seq = rng.uniform(-noise_val, noise_val, size=len(alpha1))
        last_noise = rng.uniform(-noise_val, noise_val, size=len(beta1))
        third = length // 3
        
        for t in range(third):
            noise_t = noise_terms[t]
            val = np.sum(alpha1 * last_seq) + np.sum(beta1 * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
        alpha2 = np.array([-0.4, -0.5, 0.4, 0.4, 0.1])
        beta2 = np.array([-0.3, 0.2])
        for t in range(third, 2 * third):
            noise_t = noise_terms[t]
            val = np.sum(alpha2 * last_seq) + np.sum(beta2 * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
        alpha3 = np.array([0.5, -0.3, 0.5, -0.6, 0.4])
        beta3 = np.array([0.2, -0.3])
        for t in range(2 * third, length):
            noise_t = noise_terms[t]
            val = np.sum(alpha3 * last_seq) + np.sum(beta3 * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
    elif scenario == 4:
        alpha_start = np.array([-0.4, 0.5, 0.4, 0.4, 0.1])
        alpha_end = np.array([0.6, -0.5, 0.4, -0.4, 0.3])
        beta = np.array([0.3, -0.2])
        last_seq = noise_val * rng.normal(0, 1, len(alpha_start))
        last_noise = noise_val * rng.normal(0, 1, len(beta))
        for t in range(length):
            noise_t = rng.normal(0, noise_val)
            w = (t + 1) / length
            alpha_t = alpha_start * w + alpha_end * (1.0 - w)
            val = np.sum(alpha_t * last_seq) + np.sum(beta * last_noise) + noise_t
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_t], last_noise[:-1]))
            
    elif scenario == 5:
        last_seq = noise_val * rng.normal(0, 1, len(alpha1))
        last_noise = noise_val * rng.normal(0, 1, len(beta1))
        noise_term = 0.0
        for t in range(length):
            noise_term = noise_term * 0.3 + rng.normal(0, noise_val)
            val = np.sum(alpha1 * last_seq) + np.sum(beta1 * last_noise) + noise_term
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_term], last_noise[:-1]))
            
    elif scenario == 6:
        last_seq = noise_val * rng.normal(0, 1, len(alpha1))
        last_noise = noise_val * rng.normal(0, 1, len(beta1))
        noise_term = 0.0
        half = length // 2
        for t in range(half):
            noise_term = noise_term * 0.3 + rng.normal(0, noise_val)
            val = np.sum(alpha1 * last_seq) + np.sum(beta1 * last_noise) + noise_term
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_term], last_noise[:-1]))
            
        alpha2 = np.array([-0.4, -0.5, 0.4, 0.4, 0.1])
        beta2 = np.array([-0.3, 0.2])
        for t in range(half, length):
            noise_term = noise_term * 0.3 + rng.normal(0, noise_val)
            val = np.sum(alpha2 * last_seq) + np.sum(beta2 * last_noise) + noise_term
            seq_d0[t] = val
            last_seq = np.concatenate(([val], last_seq[:-1]))
            last_noise = np.concatenate(([noise_term], last_noise[:-1]))
            
    # cumsum for degree d=1
    return np.cumsum(seq_d0)

# --- Seasonal new_data() ---
def run_seasonal_new(length=10000, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    season = 700
    mag = 5.0
    trend = rng.uniform(-0.001, 0.001)
    
    # Sine factor
    offset = int(rng.uniform(0, season))
    s_indices = np.arange(offset, offset + length)
    s_factor = mag * np.sin(2.0 * np.pi * s_indices / season)
    
    noise_A = rng.normal(0, 0.1, size=length)
    noise_B = rng.normal(0, 0.5, size=length)
    
    t = np.arange(1, length + 1)
    ts = s_factor + t * trend + noise_A + noise_B
    return ts

# --- State-space Model ---
def run_state_space(length=10000, wp=10000, sd_epsilon=1.0, sd_eta=0.1, sd_Xi=0.02, sd_of="y", rng=None):
    if rng is None:
        rng = np.random.default_rng()
        
    total_len = wp + length
    season = int(length * 0.1) # 1000
    
    sine_factor = np.sin(2.0 * np.pi * np.arange(1, season + 1) / season)
    
    mu = 0.0
    beta = 0.0
    ts_val = 0.0
    
    non_seasonal_mean = 0.0
    non_seasonal_sd = 0.0
    
    vals = np.zeros(total_len)
    
    for t in range(total_len):
        Xi = rng.normal(0, sd_Xi)
        beta += Xi
        eta = rng.normal(0, sd_eta)
        mu += beta + eta
        
        seasonal_sin = sine_factor[t % season]
        
        # update running stat
        target = ts_val if sd_of == "y" else mu
        Len = t + 1
        new_sd = np.sqrt(((Len - 1) / Len) * (non_seasonal_sd ** 2) + (1.0 / (Len + 1)) * ((target - non_seasonal_mean) ** 2))
        new_mean = non_seasonal_mean * (Len / (Len + 1)) + target / (Len + 1)
        non_seasonal_mean = new_mean
        non_seasonal_sd = new_sd
        
        epsilon = rng.normal(0, sd_epsilon)
        ts_val = mu + epsilon + non_seasonal_sd * seasonal_sin
        vals[t] = ts_val
        
    return vals[wp:]

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "gen_out"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    rng = np.random.default_rng(seed)
    
    arima_dir = os.path.join(out_dir, "arima")
    ss_dir = os.path.join(out_dir, "statespace")
    snew_dir = os.path.join(out_dir, "seasonal_new")
    
    for d in (arima_dir, ss_dir, snew_dir):
        os.makedirs(d, exist_ok=True)
        
    funcs = ["ber", "uni", "lin", "quad"]
    
    # 1. ARIMA: 6 scenarios x 16 files = 96
    print("Generating 96 ARIMA datasets...")
    for s in range(1, 7):
        for i in range(1, 17):
            func = funcs[(i - 1) % 4]
            raw_ts = run_arima(s, length=10000, noise_val=0.3, rng=rng)
            df = contaminate_global(raw_ts, alpha=0.05, anom_percent=0.02, func=func, rng=rng)
            fname = f"ARIMA{s}_{func}_{i}.csv"
            df.to_csv(os.path.join(arima_dir, fname), index=False)
            
    # 2. Seasonal new_data: 100 files
    print("Generating 100 Seasonal (new_data) datasets...")
    for i in range(1, 101):
        func = funcs[(i - 1) % 4]
        raw_ts = run_seasonal_new(length=10000, rng=rng)
        df = contaminate_global(raw_ts, alpha=0.05, anom_percent=0.01, func=func, rng=rng)
        fname = f"seasonal_{func}_{i}.csv"
        df.to_csv(os.path.join(snew_dir, fname), index=False)
        
    # 3. State-space: 100 files (25 each for sigma_epsilon in [1, 10, 100, 300])
    print("Generating 100 State-space datasets...")
    sigmas = [1.0, 10.0, 100.0, 300.0]
    count = 0
    for sig in sigmas:
        for j in range(1, 26):
            count += 1
            func = funcs[(count - 1) % 4]
            raw_ts = run_state_space(length=10000, wp=10000, sd_epsilon=sig, sd_eta=0.1, sd_Xi=0.02, sd_of="y", rng=rng)
            df = contaminate_global(raw_ts, alpha=0.01, anom_percent=0.02, func=func, rng=rng)
            fname = f"statespace_sig{int(sig)}_{func}_{j}.csv"
            df.to_csv(os.path.join(ss_dir, fname), index=False)
            
    print(f"Dataset generation complete in '{out_dir}'!")

if __name__ == "__main__":
    main()
