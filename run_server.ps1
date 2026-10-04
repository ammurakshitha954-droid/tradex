# Adaptive AI Trading Decision-Support System - PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "Adaptive AI Trading System"
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Starting Adaptive AI Trading Decision-Support Server..." -ForegroundColor Green
Write-Host "Terminal UI:  http://127.0.0.1:8000/dashboard" -ForegroundColor Yellow
Write-Host "API Docs:     http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
