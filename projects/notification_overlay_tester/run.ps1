$ErrorActionPreference = "Stop"

Write-Host "[Notification Overlay Tester] Starting..." -ForegroundColor Cyan
Write-Host "[Notification Overlay Tester] Press Ctrl+C to stop" -ForegroundColor Yellow

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "[Notification Overlay Tester] Python executable not found: $pythonExe" -ForegroundColor Red
    exit 1
}

& $pythonExe (Join-Path $PSScriptRoot "main.py")
