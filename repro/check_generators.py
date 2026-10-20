import sys, os
import pandas as pd
import numpy as np
from scipy import signal, optimize

def analyze_file(csv_path):
    df = pd.read_csv(csv_path)
    val = df["value"].values
    anom = df["anomaly"].values if "anomaly" in df.columns else np.zeros(len(val))
    
    N = len(val)
    n_anom = int(np.sum(anom))
    anom_pct = n_anom / N * 100.0
    
    # Analyze clean values (excluding anomalies) for periodicity
    clean_val = val.copy()
    clean_indices = np.where(anom == 0)[0]
    # Linear interpolation over anomalies for clean signal analysis
    clean_signal = np.interp(np.arange(N), clean_indices, clean_val[clean_indices])
    
    # Detrend linear
    t = np.arange(N)
    poly = np.polyfit(t, clean_signal, 1)
    detrended = clean_signal - np.polyval(poly, t)
    
    # Autocorrelation to find period
    # normalize
    d_norm = detrended - np.mean(detrended)
    autocorr = np.correlate(d_norm, d_norm, mode='full')
    autocorr = autocorr[len(autocorr)//2:]
    
    # Look for peaks between lag 100 and 1500
    peaks, props = signal.find_peaks(autocorr[100:1500], height=0)
    if len(peaks) > 0:
        best_peak = peaks[np.argmax(props['peak_heights'])] + 100
        period = best_peak
    else:
        period = 0
        
    # Fit sine wave: A * sin(2*pi*t/T + phi)
    if period > 50:
        omega = 2 * np.pi / period
        # A*sin(wt + phi) = c1*sin(wt) + c2*cos(wt)
        S = np.sin(omega * t)
        C = np.cos(omega * t)
        X = np.column_stack([S, C, t, np.ones(N)])
        coeffs, residuals, _, _ = np.linalg.lstsq(X, clean_signal, rcond=None)
        amplitude = np.sqrt(coeffs[0]**2 + coeffs[1]**2)
        fit_curve = X @ coeffs
        residual_std = np.std(clean_signal - fit_curve)
    else:
        amplitude = 0.0
        residual_std = np.std(detrended)
        
    return {
        "file": os.path.basename(csv_path),
        "N": N,
        "n_anom": n_anom,
        "anom_pct": anom_pct,
        "period": period,
        "amplitude": amplitude,
        "residual_std": residual_std,
    }

if __name__ == "__main__":
    files = sys.argv[1:]
    print(f"{'File':<22} | {'N':>6} | {'Anom':>4} | {'Anom%':>6} | {'Period':>7} | {'Amplitude':>9} | {'Residual SD':>11}")
    print("-" * 80)
    for f in files:
        res = analyze_file(f)
        print(f"{res['file']:<22} | {res['N']:>6} | {res['n_anom']:>4} | {res['anom_pct']:>5.2f}% | {res['period']:>7} | {res['amplitude']:>9.2f} | {res['residual_std']:>11.3f}")
