@echo off

REM peepBeefy — double-click launcher (interactive mode)
REM Requires: uv (https://docs.astral.sh/uv/)

set SCRIPT_DIR=%~dp0

where uv >nul 2>nul
if errorlevel 1 (
  echo [peepBeefy] uv not found. Install it with:
  echo.
  echo     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  echo.
  echo Then re-run this file.
  pause
  exit /b 1
)

uv run "%SCRIPT_DIR%src\main.py"
pause
