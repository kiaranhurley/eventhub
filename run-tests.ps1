# run-tests.ps1 — run all test layers in order

Write-Host "=== unit ===" -ForegroundColor Cyan
pytest -m unit
if ($LASTEXITCODE -ne 0) { Write-Host "unit tests FAILED" -ForegroundColor Red; exit 1 }

Write-Host "=== contract ===" -ForegroundColor Cyan
pytest -m contract
if ($LASTEXITCODE -ne 0) { Write-Host "contract tests FAILED" -ForegroundColor Red; exit 1 }

Write-Host "=== integration ===" -ForegroundColor Cyan
pytest -m integration
if ($LASTEXITCODE -ne 0) { Write-Host "integration tests FAILED" -ForegroundColor Red; exit 1 }

Write-Host "=== e2e ===" -ForegroundColor Cyan
pytest -m e2e
if ($LASTEXITCODE -ne 0) { Write-Host "e2e tests FAILED" -ForegroundColor Red; exit 1 }

Write-Host "=== performance ===" -ForegroundColor Cyan
pytest -m performance

Write-Host "=== security (bandit) ===" -ForegroundColor Cyan
pytest -m security
if ($LASTEXITCODE -ne 0) { Write-Host "security tests FAILED" -ForegroundColor Red; exit 1 }

Write-Host "All layers done." -ForegroundColor Green
