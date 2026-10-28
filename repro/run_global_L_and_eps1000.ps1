$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"


$lengths = @(5, 10, 20, 40, 80, 160)
foreach ($L in $lengths) {
    Write-Host "=========================================="
    Write-Host ">>> Running Global Length Sensitivity: L=$L (eps=100, per=4, workers=6, seed=0)"
    Write-Host "=========================================="
    py -3.11 -u repro/table5.py --grid reduced --per 4 --workers 6 --eps 100 --length $L --seed 0 | Tee-Object -FilePath "results\table5_len$L.txt"
}

Write-Host "=========================================="
Write-Host ">>> All runs (eps=1000 and L in 5,10,20,40,80,160) completed successfully!"
Write-Host "=========================================="
