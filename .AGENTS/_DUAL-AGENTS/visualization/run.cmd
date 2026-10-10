@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [KD-WPC] Python 3 not found on PATH. Install it and try again.
  exit /b 1
)

rem `run.cmd live` -> live mode: collector --watch 30 in its own window, then the servers.
if /i "%~1"=="live" goto live
rem `run.cmd jev` -> start ONLY the JEV suggestion bridge (needs JEV_API_KEY).
if /i "%~1"=="jev" goto jev

echo [KD-WPC] Collecting agent activity ^(ingest + tag + build^) from real OpenCode session logs...
python kdwpc_collect.py %*
if errorlevel 1 (
  echo [KD-WPC] Collector failed; see the messages above.
  exit /b 1
)

echo [KD-WPC] Starting loop board ... http://localhost:8777/kdwpc.html
echo [KD-WPC] Starting demonstration output ... http://localhost:8779/output.html
echo [KD-WPC] Stop the servers later with Ctrl+C in each server window.
start "KD-WPC board" cmd /k python -m http.server 8777
start "KD-WPC output" cmd /k python -m http.server 8779
timeout /t 2 >nul
start "" "http://localhost:8777/kdwpc.html"
start "" "http://localhost:8779/output.html"
goto :eof

:jev
echo [KD-WPC] JEV suggestion bridge: http://localhost:8778
echo [KD-WPC] Set the key first if it isn't global:  set JEV_API_KEY=sk-...
python kdwpc_jev.py
goto :eof

:live
echo [KD-WPC] LIVE mode: collector will refresh every 30s. Close that window (Ctrl+C) to stop.
start "KD-WPC live collector" cmd /k python kdwpc_collect.py --watch 30
echo [KD-WPC] Starting JEV suggestion bridge: http://localhost:8778  ^(set JEV_API_KEY in that window first if it's not global^)
start "KD-WPC JEV bridge" cmd /k python kdwpc_jev.py
echo [KD-WPC] Starting loop board: http://localhost:8777/kdwpc.html
start "KD-WPC board" cmd /k python -m http.server 8777
echo [KD-WPC] Starting demonstration output: http://localhost:8779/output.html
start "KD-WPC output" cmd /k python -m http.server 8779
timeout /t 3 >nul
start "" "http://localhost:8777/kdwpc.html"
start "" "http://localhost:8779/output.html"