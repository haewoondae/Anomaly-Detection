# Plan: Diagnosis of False Positives Phase Distribution & Table 4 Auto-tuning Verification

## Objectives
1. **Diagnosis 1 (`repro/fp_phase.py`)**:
   - Inspect false positive distribution across 10 deciles of the seasonal phase ($t \pmod{1000} // 100$) for $\sigma_\epsilon = 1$ files.
   - Discriminate between curvature effect (extrema at phase 250 and 750, deciles 2 and 7), slope effect (phases 0 and 500, deciles 0 and 5), and uniform noise variance.

2. **Diagnosis 2 (`repro/auto_table4.py`)**:
   - Run full 2,048-combination automatic tuning (`auto_osESD` with `parameters=[]`, `legacy_cap=True`, `use_author_lambda=True`, `rep_at="author"`) on the 4 ARIMA1 representative datasets:
     - `gen_out\arima\ARIMA1_ber_1.csv`
     - `gen_out\arima\ARIMA1_uni_1.csv`
     - `gen_out\arima\ARIMA1_lin_1.csv`
     - `gen_out\arima\ARIMA1_quad_1.csv`
   - Run across 4 parallel processes.
   - Compare tuned parameters, Precision, Recall, and F1 against Table 4.

3. **Synthesis & Scientific Assessment**:
   - Classify State-space replication status as "정보 부족으로 부분 재현 (partial replication due to lack of ground truth $\sigma_\epsilon$ distribution)".
   - Synthesize ARIMA and tuning path equivalence results.
