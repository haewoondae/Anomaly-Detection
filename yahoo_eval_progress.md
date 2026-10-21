# Progress: Yahoo S5 Benchmark Evaluation (Table 2 osESD)

## Status
- In Progress

## Tasks
- [x] Create evaluation plan
- [x] Run `python repro/yahoo_eval.py ..\Data 50,2,5,3,0.01,1 8`
  - Output:
    ```text
    files: 369 cfg: 50,2,5,3,0.01,1
    group  files(used/total) noanom zeropred | ONLINE R P F1 TypeI | FULL R P F1 | sec
    A1Benchmark   64/ 67    3    3 | 0.432 0.481 0.389 0.0060 | 0.430 0.481 0.389 | 2.39
    A2Benchmark  100/100    0    3 | 0.828 0.947 0.871 0.0001 | 0.828 0.947 0.871 | 1.38
    A3Benchmark  100/101    0    0 | 0.674 0.708 0.673 0.0019 | 0.658 0.708 0.665 | 1.12
    A4Benchmark  100/101    0    1 | 0.673 0.637 0.624 0.0024 | 0.654 0.637 0.613 | 1.12
    ALL Yahoo ONLINE: R=0.673 P=0.714 F1=0.664 TypeI=0.0023
    ```
- [x] Run `python repro/yahoo_eval.py ..\Data 50,2,4,3,0.05,0 8`
  - Output:
    ```text
    files: 369 cfg: 50,2,4,3,0.05,0
    group  files(used/total) noanom zeropred | ONLINE R P F1 TypeI | FULL R P F1 | sec
    A1Benchmark   64/ 67    3    0 | 0.497 0.225 0.254 0.0222 | 0.495 0.225 0.254 | 1.03
    A2Benchmark  100/100    0    0 | 0.849 0.581 0.663 0.0020 | 0.849 0.581 0.663 | 0.88
    A3Benchmark  100/101    0    0 | 0.944 0.782 0.841 0.0019 | 0.921 0.782 0.831 | 1.13
    A4Benchmark  100/101    0    0 | 0.925 0.615 0.707 0.0038 | 0.898 0.615 0.696 | 1.22
    ALL Yahoo ONLINE: R=0.834 P=0.583 F1=0.652 TypeI=0.0060
    ```
- [x] Synthesize results and compare with Table 2
- [x] Clarify Table 5 status and licensing details
