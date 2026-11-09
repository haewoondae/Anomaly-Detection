# osESD Issues and Test Refinement Plan

## 1. Goal
Address the issues identified in `osESD` code and tests:
- `validate_patch.py`: Fix normal value test scenario (use Gaussian noise instead of near-constant flatline), fix assertions (`abs(r.last) < 1e-8`), assert masking, and improve contamination/lambda checks.
- `auto_osESD_Detector.py`: 
  - Fix `win_size = min(win_size, int(par_len * 0.1))` causing collapse to same small value when tuning interval is short.
  - Skip invalid combinations where `win_size < max(dwin, rwin)`.
  - Fix `full_size` slice / loop index offset when `labeled=False`.
  - Expose `seed` parameter in `auto_osESD_Detector` / `contaminate`.
- `osESD_Detector.py`:
  - Add `rep_at` option (`'loo'` vs `'prev'` / `'author'`) to support author-identical comparison (A/B testing).
- `osESD_Test.py`:
  - Ensure `SESD_tres` / `SESD_tcha` and `SESD` properly propagate `use_author_lambda`.
  - Fix docstring inconsistencies.
- `osESD_Transform.py`:
  - Clean up / fix `x_bar` (time mean) vs `y_bar` (value mean) or remove unused misleading properties.
  - Use relative scale threshold in `_fit` instead of pure absolute `1e-12`.
- Run tests and verify with `pytest` / validation script.

## 2. Execution Order
1. Analyze and edit `src/models/osESD_Transform.py`
2. Analyze and edit `src/models/osESD_Test.py`
3. Analyze and edit `src/models/osESD_Detector.py`
4. Analyze and edit `src/models/auto_osESD_Detector.py`
5. Update `validate_patch.py` and run tests.
6. Commit & push changes to GitHub.
