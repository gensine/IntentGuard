# IntentGuard - One-Click Launcher (Backend & Frontend)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    STARTING INTENTGUARD: PAYMENT FIREWALL FOR AI AGENTS  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Backend in separate window
Write-Host "[1/2] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000 --app-dir backend"

Start-Sleep -Seconds 2

# 2. Start Frontend in separate window
Write-Host "[2/2] Launching Frontend Web Dashboard on http://localhost:5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host "`n✓ System services launched! Open http://localhost:5173 in your browser." -ForegroundColor Green
