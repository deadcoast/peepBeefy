@echo off

REM beefy — CLI wrapper
REM Usage:
REM   beefy            -> interactive mode
REM   beefy peep io    -> CLI-only mode
REM   beefy --help     -> help

set SCRIPT_DIR=%~dp0

where uv >nul 2>nul
if errorlevel 1 (
  echo [beefy] uv not found. Install it with:
  echo.
  echo     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  echo.
  exit /b 1
)

uv run "%SCRIPT_DIR%src\main.py" %*
