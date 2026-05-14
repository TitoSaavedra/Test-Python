$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent (Split-Path -Parent $scriptPath)

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

& "$rootPath\.venv\Scripts\Activate.ps1"

Write-Host "[Corsair Downloader] Starting..." -ForegroundColor Green
Write-Host "[Corsair Downloader] Logs will be saved to:" -ForegroundColor Cyan
Write-Host "  - $rootPath\logs\corsair_downloader.log" -ForegroundColor Cyan
Write-Host "  - $scriptPath\logs\corsair_downloader.log" -ForegroundColor Cyan

python "$scriptPath\main.py"

Write-Host "[Corsair Downloader] Finished" -ForegroundColor Green
Read-Host "Press Enter to close"
