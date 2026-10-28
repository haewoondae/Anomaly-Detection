# Progress: Table 3 Ablation Follow-up & Configuration Sensitivity Diagnosis

## Status
- In Progress

## Tasks
- [ ] 1. Identify and explain the 3 extra files in `gen_out\arima` (PowerShell check)
- [ ] 2. Run State-space with `loo` replacement: `python repro/ablation.py gen_out\statespace "*.csv" 50,2,5,3,0.01,1 4 loo`
- [ ] 3. Run parameter sensitivity tests on `gen_out\arima "*_1.csv"`:
  - [ ] Setting A: `100,10,10,10,0.01,1`
  - [ ] Setting B: `100,2,4,10,0.05,0`
- [ ] 4. Update `docs/REPRODUCTION.md` with accurate qualification
- [ ] 5. Answer user queries on vibration data, PDF appendix, Yahoo S5, and Stage 2 grid/cores
