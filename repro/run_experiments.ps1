$ErrorActionPreference = "Stop"

$lengths = @(5, 10, 20, 40)
foreach ($L in $lengths) {
    Write-Host "=========================================="
    Write-Host ">>> Running Table 5: Length Sensitivity L=$L (eps=100, per=8, workers=6)"
    Write-Host "=========================================="
    py -3.11 -u repro/table5.py --grid reduced --per 8 --workers 6 --eps 100 --length $L | Tee-Object -FilePath "results\table5_len$L.txt"
}

$epsilons = @(1, 300)
foreach ($E in $epsilons) {
    Write-Host "=========================================="
    Write-Host ">>> Running Table 5: Sigma_epsilon Sensitivity eps=$E (per=8, workers=6, length=10)"
    Write-Host "=========================================="
    py -3.11 -u repro/table5.py --grid reduced --per 8 --workers 6 --eps $E --length 10 | Tee-Object -FilePath "results\table5_eps$E.txt"
}

Write-Host "=========================================="
Write-Host ">>> All 6 Table 5 sensitivity runs completed successfully!"
Write-Host "=========================================="
