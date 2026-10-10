@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [KD-WPC] Python 3 not found on PATH. Install it and try again.
  exit /b 1
)

echo [KD-WPC] Collecting agent activity ^(ingest + tag + build^) from real OpenCode session logs...
python kdwpc_collect.py %*
if errorlevel 1 (
  echo [KD-WPC] Collector failed; see the messages above.
  exit /b 1
)

echo [KD-WPC] Starting dashboard server: http://localhost:8777/kdwpc.html
echo [KD-WPC] Stop it later with Ctrl+C in the server window.
start "KD-WPC dashboard" cmd /k python -m http.server 8777
timeout /t 2 >nul
start "" "http://localhost:8777/kdwpc.html"