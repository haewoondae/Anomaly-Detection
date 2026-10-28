# Progress: Group Breakdown & Table 4 Parameter Benchmark Evaluation

## Status
- Completed

## Tasks
- [x] Implement `repro/breakdown.py`
- [x] Run ARIMA1 parameter benchmarks (4 commands) - All within ±0.04 of Table 4
- [x] Run State-space parameter benchmarks (4 commands)
- [x] Run full breakdown on `gen_out\statespace` with setting T-A
  - Confirmed recall degradation is heavily concentrated in $\sigma_\epsilon = 300$ (Recall 0.7768 vs 0.9681 at $\sigma=1$)
- [x] Run full breakdown on `gen_out\arima` with setting T-A
  - All 6 scenarios consistent (F1 0.9366 ~ 0.9635)
- [x] Committed and pushed changes to GitHub.
