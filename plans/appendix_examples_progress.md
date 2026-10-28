# Progress: Appendix Exact Examples Verification (t2, t4, t3)

## Status
- In Progress

## Tasks
- [x] Synchronize `repro/appendix_examples.py` with user's exact code verbatim
- [x] Run `python repro/appendix_examples.py t2 ..\osESD_R\data\seasonal_ber_21.csv` with user's script
  - Output: `t2 Precision=1.0 Recall=1.0 F1=1.0  (TP=98 FP=0 FN=0)  4.392s`
  - `Anomalies == Real (index >= size+1): True` (98/98 exact match on index >= 101)
- [x] Run `python repro/appendix_examples.py t4 ..\osESD_R\data\seasonal_ber_21.csv` with user's script
  - Output: `t4 Precision=1.0 Recall=0.98989898989899 F1=0.9949238578680203  (TP=98 FP=0 FN=1)  135.624s`
  - `expected recall: 0.98989898989899` (98/99 exact match to 14 decimal places)
- [x] Run `python repro/appendix_examples.py t3 ..\osESD_R\data\ARIMA3_lin_4.csv`
  - Output: `Precision : 1.0, Recall : 0.9707317073170731, F1-score : 0.9851485148514851, Time : 2076.672 sec`
  - `Counts : TP=199, FP=0, FN=6, Real=205 -> Recall = 199/205`
  - Exact match to paper appendix: $P=1.0$, $R=199/205$, $F_1=0.9851485148514851$, Anomalies start `[97, 99, 200, 279, 300, 340, ...]` and end `[..., 9965, 9971]`.

