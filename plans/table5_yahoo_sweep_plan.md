# Plan: Table 5 Implementation & Yahoo Sweep Analysis

## Objectives
1. **Calibrate Yahoo Reproduction Documentation**:
   - Update `docs/REPRODUCTION.md` to state: "같은 규모의 성능 영역, 정확한 일치는 아님 (두 설정을 시도해 가장 가까운 쪽을 보고한 것임)".
   - Identify the exact files skipped in Yahoo S5 benchmarks (e.g., A3/A4 101st file).

2. **Table 5 Implementation & Execution**:
   - Update `src/models/auto_osESD_Detector.py` with `injector` parameter and custom branch.
   - Update `src/osESD.py` to pass `injector=injector`.
   - Create `repro/injectors.py` (prefix_sd, pattern_injector for drift/block, make_injector).
   - Create `repro/table5.py` (reduced grid: 216 combinations, 48 jobs).
   - Run `python repro/table5.py --grid reduced --per 4 --workers 8`.

3. **Yahoo Sensitivity Sweep**:
   - Create `repro/yahoo_sweep.py` (48 configs over S5 groups, upper-bound analysis).
   - Launch `python repro/yahoo_sweep.py ..\Data 8` in the background.
