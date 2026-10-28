# Plan: Yahoo S5 Benchmark Evaluation (Table 2 osESD)

## 1. Objectives
- Run `repro/yahoo_eval.py` across Yahoo A1Benchmark ~ A4Benchmark datasets with two parameter configurations:
  1. Config 1: `50,2,5,3,0.01,1` (size=50, dwin=2, rwin=5, maxr=3, alpha=0.01, condition=True)
  2. Config 2: `50,2,4,3,0.05,0` (size=50, dwin=2, rwin=4, maxr=3, alpha=0.05, condition=False)
- Compare ONLINE and FULL metrics against Table 2 osESD values from the paper:
  - A1: Recall 0.573, Precision 0.516, F1 0.475, Type I 0.008
  - A2: Recall 0.920, Precision 0.901, F1 0.905, Type I 0.000
  - A3: Recall 0.600, Precision 0.661, F1 0.600, Type I 0.004
  - A4: Recall 0.589, Precision 0.858, F1 0.656, Type I 0.006

## 2. Approach
- Data path: `..\Data` relative to `Python/` (contains `A1Benchmark` through `A4Benchmark`, 371 files total).
- Concurrency: 8 parallel worker processes.
- Output metrics: Online and Full Recall, Precision, F1, Type I error, files used, zero-prediction count.
