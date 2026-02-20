@echo off
setlocal enabledelayedexpansion

REM beefy / peepBeefy command wrapper
REM Usage:
REM   beefy            -> starts interactive mode
REM   beefy peep io    -> CLI-only mode
REM   beefy --help     -> help

set SCRIPT_DIR=%~dp0
set SCRIPT=%SCRIPT_DIR%peepBeefy.py

where py >nul 2>nul
if errorlevel 1 (
  echo [peepBeefy] Python launcher ^(py^) not found. Install Python 3 and try again.
  exit /b 1
)

py -3 -c "import psutil, rich, typer" >nul 2>nul
if errorlevel 1 (
  echo [peepBeefy] Missing packages. Run:
  echo     py -m pip install --user psutil rich typer
  exit /b 1
)

py -3 "%SCRIPT%" %*
endlocal
