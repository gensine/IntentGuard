@echo off
title IntentGuard Launcher
echo ==========================================================
echo    STARTING INTENTGUARD: PAYMENT FIREWALL FOR AI AGENTS
echo ==========================================================

echo [1/2] Launching Backend on http://127.0.0.1:8000...
start cmd /k ".\venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000 --app-dir backend"

timeout /t 2 /nobreak >nul

echo [2/2] Launching Frontend on http://localhost:5173...
start cmd /k "cd frontend && npm run dev"

echo.
echo IntentGuard is starting! Open http://localhost:5173 in your browser.
pause
