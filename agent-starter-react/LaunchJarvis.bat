@echo off
title JARVIS SYSTEM INITIALIZATION
color 0b

:: SET PROJECT PATHS
set FRONTEND_DIR=%~dp0
set BACKEND_DIR=%~dp0..\Jarvis_code

echo [SYSTEM] INITIALIZING NEURAL NETWORK (AGENT)...
cd /d "%BACKEND_DIR%"
:: Use venv if it exists
if exist venv (
    start cmd /k ".\venv\Scripts\activate && python agent.py dev"
) else (
    start cmd /k "python agent.py dev"
)

echo [SYSTEM] STARTING INTERFACE (FRONTEND)...
cd /d "%FRONTEND_DIR%"
:: Check for pnpm first, then npm
where pnpm >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start cmd /k "pnpm dev"
) else (
    start cmd /k "npm run dev"
)

echo [SYSTEM] OPENING HUD...
timeout /t 10
start http://localhost:3000/gesture.html

echo [SYSTEM] JARVIS IS ONLINE. AWAITING GESTURE COMMANDS.
pause