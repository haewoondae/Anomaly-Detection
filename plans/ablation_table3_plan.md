# Plan: Table 3 Ablation Study & TP Metrics Analysis

## Objectives
1. **Execute Table 3 Ablation (`repro/ablation.py`) across 3 configurations**:
   - `python repro/ablation.py gen_out\arima "*.csv" 50,2,5,3,0.01,1 8` (ARIMA 96 files, author replacement)
   - `python repro/ablation.py gen_out\statespace "*.csv" 50,2,5,3,0.01,1 8` (State-space 100 files, author replacement)
   - `python repro/ablation.py gen_out\arima "*.csv" 50,2,5,3,0.01,1 8 loo` (ARIMA 96 files, loo replacement)
2. **Extract TP / Recall metrics from `repro/fp_cascade.py`**:
   - Revisit `fp_cascade.py` on $\sigma_\epsilon=1$ and $\sigma_\epsilon=10$ to report True Positives (TP), Total Positives (Real), and Recall for both `author` and `loo` alongside FP.
3. **Address Practical Data & Research Preparation**:
   - Yahoo S5 dataset application instructions.
   - Stock volume (AAPL & TSLA) data acquisition via `yfinance`.
   - Paper PDF Appendix code images (pages 17-23).
   - Clarify vibration data specifications (sampling frequency, channels, labels, indicators) for Stage 2.
