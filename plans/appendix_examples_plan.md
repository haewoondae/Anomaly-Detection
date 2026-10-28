# Plan: Appendix Exact Examples Verification (t2, t4, t3)

## Objectives
1. **Execute Appendix Example t2 (Single osESD Seasonal)**:
   - Data: `..\osESD_R\data\seasonal_ber_21.csv`
   - Parameters: `size=100, dwin=5, rwin=5, maxr=6, alpha=0.01`
   - Scoring window: `true_outlier = df['anomaly'][(size+1):]`
   - Target: $P=R=F_1=1.0$, `Anomalies == Real: True`.
2. **Execute Appendix Example t4 (128-comb User Grid Seasonal)**:
   - Data: `..\osESD_R\data\seasonal_ber_21.csv`
   - Parameters: `sizes=[50,200], conditions=[True,False], alphas=[0.001,0.05], dwins=[2,30], rwins=[4,30], weights=[0,0,1,0], learning_length=0.2`
   - Scoring window: entire series
   - Target: $P=1.0$, $R = 98/99 \approx 0.98989898989899$, $F_1 = 0.9949238578680203$.
3. **Execute Appendix Example t3 (2048-comb Default Grid ARIMA3)**:
   - Data: `..\osESD_R\data\ARIMA3_lin_4.csv`
   - Parameters: default 2,048 grid, `learning_length=0.2`, `weights=[0,0,1,0]`
   - Scoring window: entire series
   - Target: $P=1.0$, $R = 199/205 \approx 0.9707317073170731$, $F_1 = 0.9851485148514851$.
4. **Answer Yahoo Data Origin and License Clarification**:
   - Clarify that the 372 files in `Anomaly Detection\Data` were previously downloaded by the user locally from Hugging Face under the Yahoo Research TOU.
