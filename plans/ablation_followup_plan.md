# Plan: Table 3 Ablation Follow-up & Configuration Sensitivity Diagnosis

## Objectives
1. **Diagnosis 1: Investigate the 99 ARIMA files**:
   - Run the PowerShell filter to identify the 3 anomalous files.
   - Clarify origin (the 3 alias copies created earlier: `ARIMA1_uni_1.csv`, `ARIMA1_lin_1.csv`, `ARIMA1_quad_1.csv`).
   - Remove the 3 alias copies to restore the true 96 files.

2. **Diagnosis 2: State-space under `loo` replacement**:
   - Run `python repro/ablation.py gen_out\statespace "*.csv" 50,2,5,3,0.01,1 4 loo`.
   - Verify if `loo` resolves the cascade false alarms and inspect the resulting `osesd` vs `sos` F1 ranking.

3. **Diagnosis 3: Parameter sensitivity of `norep` and `oGESD`**:
   - Run Setting A (`100,10,10,10,0.01,1`) on `gen_out\arima "*_1.csv"`.
   - Run Setting B (`100,2,4,10,0.05,0`) on `gen_out\arima "*_1.csv"`.
   - Check if `norep` transitions to the paper's pattern (high precision, low recall / masking).

4. **Update `docs/REPRODUCTION.md`**:
   - Update Table 3 entry to "Table 3 정성적 부분 재현 (ARIMA의 osESD > sos > norep 순위와 속도 순서). norep의 정밀도·재현율 패턴, oGESD 정밀도 붕괴, State-space는 재현 실패 또는 구현 해석 차이."

5. **Answers to User Queries**:
   - Investigate vibration data format in `ifacts-vib` (sampling rate, features, operational state).
   - Search for paper PDF pages 17-23 across the system / user environment.
   - Yahoo S5 application status & grid size / CPU core count recommendations for Stage 2.
