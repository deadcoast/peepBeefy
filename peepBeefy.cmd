@echo off
setlocal enabledelayedexpansion

REM beefy / peepBeefy command wrapper v0.0.4
REM Usage:
REM   peepBeefy            -> starts interactive mode
REM   peepBeefy peep io    -> CLI-only mode
REM   peepBeefy --help     -> help

set SCRIPT_DIR=%~dp0
set SCRIPT=%SCRIPT_DIR%src\main.py

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
