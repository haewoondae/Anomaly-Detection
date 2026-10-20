# Progress: Diagnosis of Prefix Anomaly Counts & Table 2 Data Function Analysis

## Status
- In Progress

## Tasks
- [x] Create `repro/diag_prefix.py`
- [x] Run `python repro/diag_prefix.py ..\osESD_R\data` (Completed):
  - `A2Benchmark_synthetic_19.csv`: N=1421, prefix=284, prefix_anoms=0, params=[True, 28, 3, 2, 4, 0.01]
  - `A2Benchmark_synthetic_44.csv`: N=1421, prefix=284, prefix_anoms=0, params=[True, 28, 3, 2, 4, 0.01]
  - `A3Benchmark_TS79.csv`: N=1680, prefix=336, prefix_anoms=1, params=[True, 33, 3, 2, 4, 0.01]
  - `A3Benchmark_TS86.csv`: N=1680, prefix=336, prefix_anoms=1, params=[True, 33, 3, 2, 4, 0.01]
  - `ARIMA3_lin_4.csv`: N=10000, prefix=2000, prefix_anoms=45, params=[False, 50, 3, 2, 10, 0.01]
  - `ARIMA5_quad_2.csv`: N=10000, prefix=2000, prefix_anoms=36, params=[True, 100, 10, 2, 10, 0.05]
  - `seasonal_ber_16.csv`: N=10000, prefix=2000, prefix_anoms=21, params=[True, 50, 3, 2, 4, 0.01]
  - `seasonal_ber_21.csv`: N=10000, prefix=2000, prefix_anoms=22, params=[True, 50, 3, 2, 5, 0.01]
  - `seasonal_ber_6.csv`: N=10000, prefix=2000, prefix_anoms=14, params=[True, 50, 3, 2, 5, 0.01]
- [x] Inspect `..\osESD_R\R\data_functions.R`:
  - Identified `RUN_DATA_1` to `RUN_DATA_6` (6 ARIMA scenarios).
  - Identified `State_space_data` (local linear trend + seasonal component).
  - Identified `contaminate` (Bernoulli, Uniform, Linear, Quadratic multipliers).
  - Identified generation scripts for Table 2 datasets (16 datasets x 6 ARIMA scenarios = 96 datasets, and 100 Seasonal datasets).
- [x] Check Yahoo Webscope A1~A4 dataset availability: Not present locally (needs application/confirmation).
- [x] Report outputs and analysis to user.
