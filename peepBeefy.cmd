@echo off

REM peepBeefy — CLI wrapper
REM Usage:
REM   peepBeefy            -> interactive mode
REM   peepBeefy peep io    -> CLI-only mode
REM   peepBeefy --help     -> help

set SCRIPT_DIR=%~dp0

where uv >nul 2>nul
if errorlevel 1 (
  echo [peepBeefy] uv not found. Install it with:
  echo.
  echo     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  echo.
  exit /b 1
)

uv run "%SCRIPT_DIR%src\main.py" %*
