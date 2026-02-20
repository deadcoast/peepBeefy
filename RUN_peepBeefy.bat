@echo off
setlocal enabledelayedexpansion

REM peepBeefy launcher for Windows
REM - Opens the interactive CLI with minimal typing.
REM - Requires Python 3 and the deps: psutil, rich, typer.

set SCRIPT_DIR=%~dp0
set SCRIPT=%SCRIPT_DIR%main.py

where py >nul 2>nul
if errorlevel 1 (
  echo [peepBeefy] Python launcher ^(py^) not found.
  echo Install Python 3 from python.org, then re-run this file.
  pause
  exit /b 1
)

py -3 -c "import psutil, rich, typer" >nul 2>nul
if errorlevel 1 (
  echo [peepBeefy] Missing Python packages.
  echo.
  echo Run this once in PowerShell:
  echo     py -m pip install --user psutil rich typer
  echo.
  pause
  exit /b 1
)

py -3 "%SCRIPT%"
endlocal
