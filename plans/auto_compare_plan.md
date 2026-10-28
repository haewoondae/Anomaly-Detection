# Plan: auto_osESD PyPI Equivalence & Default rep_at Configuration

## Objectives
1. **Set `rep_at='author'` default**:
   - Update `rep_at` parameter default from `"loo"` to `"author"` in:
     - `src/models/osESD_Detector.py: osESD()`
     - `src/osESD.py: osESD()`
     - `src/osESD.py: auto_osESD()`
     - `src/models/auto_osESD_Detector.py: osESD_Detector_auto()` & `run_osESD_modified()`
   - Add docstrings explaining that `loo` is experimental and carries overdetection risk with small `rwin` (<= 5).
   - Keep lambda default as Rosner (`use_author_lambda=False`).
   - Check existing tests (`tests/test_osesd.py`, `tests/test_pypi_golden.py`).
   - Commit & push changes.

2. **Equivalence Test (`auto_osESD`) against PyPI (`osESD 1.1.6`)**:
   - Create `repro/auto_compare.py` testing grid:
     - `sizes=[50, 100]`
     - `conditions=[True, False]`
     - `maxrs=[3, 10]`
     - `dwins=[2, 5, 10]`
     - `rwins=[4, 5, 10]`
     - `alphas=[0.01, 0.05]`
     (144 combinations)
   - Run on 3 datasets:
     - `A2Benchmark_synthetic_44.csv`
     - `A3Benchmark_TS86.csv`
     - `ARIMA3_lin_4.csv`
   - Test both `author` mode (modified with `legacy_cap=True, use_author_lambda=True, rep_at="author"`) and `pypi` mode (using official PyPI `osESD` in `venv_pypi`).
   - Compare index outputs (`a == b`, lengths).
   - Clean up `venv_pypi` after verification.

3. **Reporting**:
   - Confirm push and default setting.
   - Print `signature:` output of PyPI `auto_osESD`.
   - Report exact 3-line comparison output.
