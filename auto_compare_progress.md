# Progress: auto_osESD PyPI Equivalence & Default rep_at Configuration

## Status
- Completed

## Completed Tasks
- [x] Changed `rep_at` default to `"author"` in:
  - `src/models/osESD_Detector.py`
  - `src/osESD.py` (`osESD` and `auto_osESD`)
  - `src/models/auto_osESD_Detector.py` (`osESD_Detector_auto` and `run_osESD_modified`)
- [x] Updated docstrings: documented that `"loo"` is experimental and may cause overdetection on small `rwin` (<= 5).
- [x] Verified existing tests (`pytest tests/test_pypi_golden.py` passed 27/27, `pytest tests/test_osesd.py` passed).
- [x] Committed and pushed `rep_at='author'` default changes (commit `1453b92`).
- [x] Created `repro/auto_compare.py`.
- [x] Executed `auto_compare.py` in `author` mode for the 3 target datasets:
  - `A2Benchmark_synthetic_44.csv`: 6 anomalies, 32.0s
  - `A3Benchmark_TS86.csv`: 13 anomalies, 7.5s
  - `ARIMA3_lin_4.csv`: 205 anomalies, 220.7s
- [x] Created `venv_pypi` virtual environment.
- [x] Installed packages in `venv_pypi` (`pip install osESD pandas scipy matplotlib`).
- [x] Ran `auto_compare.py pypi` for the 3 target datasets:
  - `A2Benchmark_synthetic_44`: 6 anomalies (23.0s)
  - `A3Benchmark_TS86`: 13 anomalies (28.7s)
  - `ARIMA3_lin_4`: 205 anomalies (320.4s)
- [x] Ran comparison check:
  - `A2Benchmark_synthetic_44 True 6 6`
  - `A3Benchmark_TS86 True 13 13`
  - `ARIMA3_lin_4 True 205 205`
  (100% exact index equivalence with PyPI package)
- [x] Cleaned up `venv_pypi`.
- [x] Committed and pushed results.
