@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.ps1 first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" start.py %*
if errorlevel 1 (
    echo WordNest could not start. Read the message above.
    pause
    exit /b 1
)
