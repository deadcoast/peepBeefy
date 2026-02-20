@echo off
REM ═══════════════════════════════════════════════════════════════
REM  peepBeefy — Installer Bootstrap
REM
REM  This is a thin wrapper. All visual logic lives in install.py.
REM  This file exists for ONE reason: to verify uv is present
REM  before Python or Rich are available.
REM
REM  Flow:  install.bat  →  uv run --with rich  →  install.py
REM ═══════════════════════════════════════════════════════════════

REM --- Check for uv (the only thing we can't do from Python) ---
where uv >nul 2>nul
if errorlevel 1 (
    for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "E=%%a"
    echo.
    echo   %E%[1;31m[!!]%E%[0m  uv is not installed.
    echo.
    echo   Install it:
    echo   %E%[1;33mpowershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"%E%[0m
    echo.
    echo   Then close and reopen your terminal and run install.bat again.
    echo.
    pause
    exit /b 1
)

REM --- Hand off to Rich-powered installer ---
REM   --with rich:  ad-hoc dependency (no project venv needed yet)
REM   install.py handles uv sync to create the real project venv.
uv run --with rich "%~dp0install.py"
if errorlevel 1 pause
