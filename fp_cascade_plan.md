# Plan: False Positive Cascade Diagnosis & Reproduction Documentation

## Objectives
1. **Diagnosis: False Positive Cascade Mechanism (`repro/fp_cascade.py`)**:
   - Compare `rep_at="author"` (previous-step prediction replacement) vs `rep_at="loo"` (leave-one-out replacement) on:
     - `statespace_eps1_*.csv` ($\sigma_\epsilon = 1$, 8 files)
     - `statespace_eps10_*.csv` ($\sigma_\epsilon = 10$, 8 files)
   - Metrics to collect for both `author` and `loo`:
     - Total false positives (`FP`)
     - Number of consecutive FP runs (`runs`)
     - Mean run length (`mean_len`)
     - Max run length (`max_len`)
     - Count of long runs ($len \ge 10$)
     - Phase decile distribution ($t \pmod{1000} // 100$)
   - Distinguish whether the massive FPs on steep slopes with $\sigma_\epsilon=1$ are caused by:
     - **Substitution lag accumulation (치환 지연 누적)**: if `author` exhibits long consecutive runs and `loo` drastically reduces them.
     - **Test statistic / windowing artifact**: if both `author` and `loo` exhibit similar FP patterns.

2. **Reproduction Documentation (`docs/REPRODUCTION.md`)**:
   - Document the structured reproduction status table and nuanced scientific findings:
     - Implementation equivalence (PyPI 1.1.6 vs Python port on 5 large files & 27 golden tests)
     - A2_44 example output exact match
     - Table 2 ARIMA close match ($\Delta$F1 -0.022)
     - Table 2(g) State-space status: "정보 부족으로 미확정 (unverified due to undisclosed $\sigma_\epsilon$ distribution)"
     - Table 4 ARIMA1 qualitative consistency (3/6 parameter mismatch, flat F1 objective landscape)
     - Ablation, Yahoo, comparison models: unperformed
     - Appendices runtime correspondence (2,560~2,929s vs 3,123~3,478s)

3. **Execution & Reporting**:
   - Execute both runs and provide the 2-line output of `fp_cascade.py`.
   - Provide objective analysis of the cascade diagnosis.
