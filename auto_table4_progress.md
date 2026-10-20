# Progress: Diagnosis of False Positives Phase Distribution & Table 4 Auto-tuning Verification

## Status
- In Progress

## Tasks
- [x] Implement `repro/fp_phase.py`
- [x] Run `repro/fp_phase.py` on $\sigma_\epsilon = 1$ files and analyze phase distribution
  - Output: `files 8 FP total 3641 by phase decile (idx mod 1000): [429, 249, 53, 479, 534, 580, 309, 68, 481, 459]`
  - Finding: Extrema / curvature (deciles 2 & 7) have only 53 and 68 FPs (~3.3%). Steepest slope transitions (deciles 4, 5 and 9, 0) account for the vast majority of FPs.
- [x] Implement `repro/auto_table4.py`
- [ ] Run `repro/auto_table4.py` on the 4 ARIMA1 representative datasets in parallel (task running)
- [ ] Report outputs and scientific synthesis
