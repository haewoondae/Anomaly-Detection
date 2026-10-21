# Progress: Table 5 Implementation & Yahoo Sweep Analysis

## Status
- In Progress

## Tasks
- [x] Identify skipped Yahoo S5 files
  - `A3Benchmark_all.csv` (100-series combined table, no `value` column)
  - `A4Benchmark_all.csv` (100-series combined table, no `value` column)
  - Both skipped normally due to column format; all 100 individual TS files in A3 and A4 evaluated 100/100.
- [x] Update `docs/REPRODUCTION.md` with calibrated Yahoo evaluation wording
- [x] Modify `src/models/auto_osESD_Detector.py` for `injector` parameter
- [x] Modify `src/osESD.py` for `injector` parameter
- [x] Implement `repro/injectors.py`
- [x] Implement `repro/table5.py`
- [x] Implement `repro/yahoo_sweep.py`
- [ ] Run `python repro/table5.py --grid reduced --per 4 --workers 8` (running in background `task-2432`, ~12-14 min)
- [ ] Run `python repro/yahoo_sweep.py ..\Data 8`
