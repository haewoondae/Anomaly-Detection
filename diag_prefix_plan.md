# Plan: Diagnosis of Prefix Anomaly Counts & Table 2 Data Function Analysis

## Objectives
1. **Prefix Anomaly & Tuning Diagnosis (`repro/diag_prefix.py`)**:
   - Write `repro/diag_prefix.py` to inspect the 9 sample csv files in `../osESD_R/data`.
   - Calculate for each dataset:
     - Total length $N$
     - Prefix length `par_len = int(N * 0.2)`
     - Prefix anomaly count `prefix_anoms = int(df["anomaly"][:par_len].sum())`
     - Selected parameters from `A.osESD_Detector_auto` with author mode (`legacy_cap=True, use_author_lambda=True, rep_at="author"`).
   - Identify files with `prefix_anoms == 0` (where tuning degenerates to default first grid parameters) vs `prefix_anoms > 0` (where true parameter tuning occurs).

2. **Inspect `../osESD_R/R/data_functions.R`**:
   - Analyze how synthetic datasets (ARIMA scenarios 1~6, state-space models) are generated.
   - Assess feasibility of porting to Python for Table 2 reproduction.

3. **Status Assessment of Yahoo Benchmark (A1~A4)**:
   - Check if Yahoo Webscope A1~A4 benchmark files are present in the local workspace or environment.
   - Clearly inform the user about dataset availability.

4. **Deliverables**:
   - Console output of `diag_prefix.py`.
   - Structural summary and analysis of `data_functions.R`.
   - Yahoo Webscope status.
