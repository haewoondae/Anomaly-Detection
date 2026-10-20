# Plan: Group Breakdown & Table 4 Parameter Benchmark Evaluation

## Objectives
1. **Implement `repro/breakdown.py`**:
   - Parse arguments: `<folder> <glob_pattern> <size,dwin,rwin,maxr,alpha,cond>`
   - Execute `osESD` in parallel using 8 workers with `use_author_lambda=True, rep_at="author"`.
   - Calculate Precision, Recall, F1-score, Type I error rate on both Full and Online intervals.
   - Extract group labels (Scenario 1..6, Distribution ber/uni/lin/quad, $\sigma_\epsilon \in \{1, 10, 100, 300\}$).
   - Output overall summary and detailed breakdown tables.

2. **Execute Table 4 Parameter Benchmarks**:
   - ARIMA1:
     - `ARIMA1_ber_*.csv` with `50,2,5,3,0.05,1`
     - `ARIMA1_uni_*.csv` with `50,2,4,5,0.005,1`
     - `ARIMA1_lin_*.csv` with `150,2,4,5,0.05,1`
     - `ARIMA1_quad_*.csv` with `50,2,5,3,0.01,1`
   - State-space:
     - `*_ber_*.csv` with `50,5,4,3,0.01,1`
     - `*_uni_*.csv` with `50,10,30,3,0.01,0`
     - `*_lin_*.csv` with `50,2,10,3,0.001,1`
     - `*_quad_*.csv` with `50,2,10,3,0.005,1`

3. **Execute Full Breakdown under Setting T-A (`50,2,5,3,0.01,1`)**:
   - `gen_out\statespace` with `"*.csv"`: inspect breakdown by $\sigma_\epsilon \in \{1, 10, 100, 300\}$ to verify if recall drop is concentrated in $\sigma_\epsilon = 300$.
   - `gen_out\arima` with `"*.csv"`: inspect breakdown by scenario (ARIMA 1..6) and distribution.

4. **Reporting**:
   - Report all execution outputs cleanly.
   - Clarify notation distinction (T-A, T-B, T-C vs previous A, B, C).
   - Note CPU time vs elapsed wall clock time.
