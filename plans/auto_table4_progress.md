# Progress: Diagnosis of False Positives Phase Distribution & Table 4 Auto-tuning Verification

## Status
- Completed

## Tasks
- [x] Implement `repro/fp_phase.py`
- [x] Run `repro/fp_phase.py` on $\sigma_\epsilon = 1$ files and analyze phase distribution
  - Output: `files 8 FP total 3641 by phase decile (idx mod 1000): [429, 249, 53, 479, 534, 580, 309, 68, 481, 459]`
  - Finding: Extrema / curvature (deciles 2 & 7) have only 53 and 68 FPs (~3.3%). Steepest slope transitions (deciles 4, 5 and 9, 0) account for the vast majority of FPs.
- [x] Implement `repro/auto_table4.py`
- [x] Run `repro/auto_table4.py` on the 4 ARIMA1 representative datasets in parallel
  - Outputs:
    - `ARIMA1_uni_1.csv         params=[0, 50, 5, 2, 4, 0.01]  P=0.9171 R=0.8939 F1=0.9054  (2560s)`
    - `ARIMA1_quad_1.csv        params=[1, 50, 3, 2, 4, 0.01]  P=0.9396 R=0.9884 F1=0.9634  (2700s)`
    - `ARIMA1_ber_1.csv         params=[1, 50, 3, 2, 4, 0.001]  P=1.0000 R=0.9450 F1=0.9717  (2818s)`
    - `ARIMA1_lin_1.csv         params=[0, 50, 5, 2, 10, 0.005]  P=0.9691 R=0.9947 F1=0.9817  (2929s)`
- [x] Report outputs and scientific synthesis
