# Plan: Reinforcing Equivalence Check & Paper Parameter Analysis

## Objectives
1. **Reinforce Tuning Equivalence Check**:
   - Run `auto_compare.py` in `author` mode for:
     - `ARIMA5_quad_2`
     - `seasonal_ber_16`
     - `seasonal_ber_21`
     - `seasonal_ber_6`
   - Recreate temporary `venv_pypi` and install `osESD pandas scipy matplotlib`.
   - Run `auto_compare.py` in `pypi` mode for the 4 datasets.
   - Run comparison script: `a == b`, lengths.
   - Clean up `venv_pypi`.

2. **Sample Generator & Dataset Diagnostics (`repro/check_generators.py`)**:
   - Implement `check_generators.py` to analyze:
     - Anomaly percentage (ARIMA ~0.02, seasonal ~0.01)
     - Periodicity estimation (FFT / autocorrelation for period ~700-714)
     - Amplitude (sine wave mag ~5)
     - Residual standard deviation (~0.5)
   - Run check on `seasonal_ber_6.csv`, `seasonal_ber_16.csv`, `ARIMA3_lin_4.csv`, `ARIMA5_quad_2.csv`.

3. **Extract Paper Parameters for State-Space Data (from PDF)**:
   - Use `fitz` (PyMuPDF) on `Anomaly detection of automatic online extreme studentized deviate.pdf`.
   - Extract text and render pages 28-31 covering Appendix "Creating datasets", Eq. (17), (18), Fig. 12 and caption.
   - Capture exact parameter formulas and values for $\sigma_\epsilon, \sigma_\eta, \sigma_\xi$.
   - Present captures and parameter values to user.

4. **Progress & Reporting**:
   - Maintain `auto_compare_extension_progress.md`.
   - Report all comparison results and extracted paper details.
