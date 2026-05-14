#Requires -RunAsAdministrator

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootPath = Split-Path -Parent (Split-Path -Parent $scriptPath)

Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

& "$rootPath\.venv\Scripts\Activate.ps1"

Write-Host "[BDO Auto Clicker] Starting with administrator privileges..." -ForegroundColor Green
Write-Host "[BDO Auto Clicker] Make sure BDO is open on the main screen" -ForegroundColor Yellow
Write-Host "[BDO Auto Clicker] Logs will be saved to:" -ForegroundColor Cyan
Write-Host "  - $rootPath\logs\bdo_auto_clicker.log" -ForegroundColor Cyan
Write-Host "  - $scriptPath\logs\bdo_auto_clicker.log" -ForegroundColor Cyan

python "$scriptPath\main.py"

Write-Host "[BDO Auto Clicker] Program finished" -ForegroundColor Green
Read-Host "Press Enter to close"
