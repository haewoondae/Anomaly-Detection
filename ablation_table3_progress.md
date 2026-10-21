# Progress: Table 3 Ablation Study & TP Metrics Analysis

## Status
- Completed

## Tasks
- [x] Measure TP and Recall in `fp_cascade.py` for $\sigma_\epsilon=1$ and $\sigma_\epsilon=10$
  - `eps1`: author TP=1438/1515 (R=0.9492), FP=3641 | loo TP=1432/1515 (R=0.9452), FP=3
  - `eps10`: author TP=1526/1604 (R=0.9514), FP=111 | loo TP=1525/1604 (R=0.9507), FP=18
  - Key finding: `author` achieves no meaningful Recall gain (+0.0040 in eps1, +0.0007 in eps10) while suffering massive FP cascade.
- [x] Run `python repro/ablation.py gen_out\arima "*.csv" 50,2,5,3,0.01,1 8`
  - Output:
    ```
    variant  files   P      R      F1     TypeI   time(s)
    osesd      99  0.971  0.923  0.945  0.0006  11.61
    sos        99  0.941  0.835  0.881  0.0011  5.50
    ogesd      99  0.963  0.929  0.945  0.0007  24.46
    norep      99  0.579  0.748  0.652  0.0110  12.03
    ```
- [x] Run `python repro/ablation.py gen_out\statespace "*.csv" 50,2,5,3,0.01,1 8`
  - Output:
    ```
    variant  files   P      R      F1     TypeI   time(s)
    osesd     100  0.774  0.902  0.783  0.0136  7.80
    sos       100  0.992  0.904  0.944  0.0001  3.91
    ogesd     100  0.766  0.913  0.782  0.0146  18.71
    norep     100  0.579  0.727  0.641  0.0107  8.27
    ```
- [x] Run `python repro/ablation.py gen_out\arima "*.csv" 50,2,5,3,0.01,1 4 loo`
  - Output:
    ```
    variant  files   P      R      F1     TypeI   time(s)
    osesd      99  0.936  0.919  0.927  0.0013  8.69
    sos        99  0.941  0.835  0.881  0.0011  3.88
    ogesd      99  0.907  0.925  0.915  0.0020  16.98
    norep      99  0.579  0.748  0.652  0.0110  8.46
    ```
- [x] Document ablation results and provide answers on Yahoo S5, stock data, PDF images, and vibration data specs
