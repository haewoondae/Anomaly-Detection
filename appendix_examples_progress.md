# Progress: Appendix Exact Examples Verification (t2, t4, t3)

## Status
- In Progress

## Tasks
- [x] Implement `repro/appendix_examples.py`
- [x] Run `python repro/appendix_examples.py t2 ..\osESD_R\data\seasonal_ber_21.csv`
  - Output: `Precision : 1.0, Recall : 1.0, F1-score : 1.0, Time : 2.143 sec`, `Anomalies == Real : True` (98/98 exact match)
- [x] Run `python repro/appendix_examples.py t4 ..\osESD_R\data\seasonal_ber_21.csv`
  - Output: `Precision : 1.0, Recall : 0.98989898989899, F1-score : 0.9949238578680203, Time : 86.484 sec`
  - Exact match: TP=98, FP=0, FN=1, Real=99 -> Recall = 98/99. Missing from Real: [77], Extra FP: []
- [ ] Run `python repro/appendix_examples.py t3 ..\osESD_R\data\ARIMA3_lin_4.csv` (task-2153 running in background)
- [x] Report outputs and clarify Yahoo data origin
