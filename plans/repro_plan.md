# Plan: Implement rep_at='prev' update, run tests, and execute Stages 1~3

## Objectives
1. **Step 0**:
   - Update `src/models/osESD_Transform.py` to support `loo_prediction(self, at="now")` where `at="prev"` evaluates at `self._t[-2]`.
   - Update `src/models/osESD_Detector.py` to call `r.loo_prediction(at="prev" if rep_at in ("prev", "author") else "now")` and update docstrings.
   - Create `tests/test_rep_at_author.py` with author formula test.
2. **Step 1**:
   - Check `python --version`, `pip list | findstr ...`
   - Run `python -m pytest -q` (expect 7 passed).
   - Run `python validate_patch.py` (expect all checks passed).
3. **Step 2**:
   - Clone `https://github.com/iguv221/osESD_R` outside the repo directory (`../osESD_R`).
   - Run sanity check python script on `A2Benchmark_synthetic_44.csv`.
   - Create `repro/stage1_a2_44.py` and run against the dataset.
4. **Step 3**:
   - Create clean temporary virtual environment (`venv_pypi`).
   - Install `osESD` and `pandas`.
   - Run oracle comparison using PyPI package.
   - Clean up venv.
5. **Output**:
   - Report all required console outputs cleanly to user.
