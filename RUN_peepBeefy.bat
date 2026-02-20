@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM  peepBeefy — Installation Script
REM  First-time setup for the peepBeefy CLI application.
REM  After install, run the app with:  beefy  (interactive)  or  beefy dev ...
REM ============================================================================

REM --- ANSI escape code setup (Windows 10+ / Windows Terminal) ---
for /F "delims=" %%a in ('echo prompt $E ^| cmd') do set "E=%%a"

set "C_CYAN=%E%[36m"
set "C_GREEN=%E%[32m"
set "C_RED=%E%[31m"
set "C_YELLOW=%E%[33m"
set "C_BOLD=%E%[1m"
set "C_DIM=%E%[2m"
set "C_RESET=%E%[0m"
set "C_BCYAN=%E%[1;36m"
set "C_BGREEN=%E%[1;32m"
set "C_BRED=%E%[1;31m"
set "C_BYELLOW=%E%[1;33m"

set "SCRIPT_DIR=%~dp0"
set "PASS=%C_BGREEN%[ok]%C_RESET%"
set "FAIL=%C_BRED%[!!]%C_RESET%"
set "STEP=%C_BCYAN%[>>]%C_RESET%"
set "INFO=%C_DIM%[..]%C_RESET%"

cls

REM --- Header ---
echo.
echo %C_CYAN%  ========================================================================%C_RESET%
echo %C_CYAN%  ==%C_RESET%                                                                %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BCYAN%              (          (%C_RESET%                              %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BCYAN%   (   (      ( )\   (   ( )\ ) (%C_RESET%                      %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_CYAN% `  )   ))\ ))\`  ) )((_) ))\ ))(()/( )\ )%C_RESET%              %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_CYAN% /(/(  /((_)((_)(/(((_)_ /((_)((_)(_)^|()/ (%C_RESET%            %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BOLD%((_)_\(_))(_))((_)_\^| _ ^|_))(_))(_) _^|)(_))%C_RESET%           %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BOLD%^| '_ \) -_) -_) '_ \) _ Y -_) -_)^|  _^| ^|^| ^|%C_RESET%          %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BOLD%^| .__/\___\___^| .__/^|___^|___\___^|^|_^|  \_, ^|%C_RESET%          %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BOLD%^|_^|           ^|_^|                     ^|__/%C_RESET%            %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%                                                                %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_BOLD%peepBeefy%C_RESET% %C_DIM%v0.0.4%C_RESET%                                             %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%  %C_DIM%Find and display heavy running processes (gamer-friendly)%C_RESET% %C_CYAN%==%C_RESET%
echo %C_CYAN%  ==%C_RESET%                                                                %C_CYAN%==%C_RESET%
echo %C_CYAN%  ========================================================================%C_RESET%
echo.
echo   %C_BCYAN%INSTALLER%C_RESET%  %C_DIM%First-time setup%C_RESET%
echo   %C_DIM%This script prepares your system to run peepBeefy.%C_RESET%
echo   %C_DIM%After setup, you will never need to run this file again.%C_RESET%
echo.
echo %C_CYAN%  ------------------------------------------------------------------------%C_RESET%
echo.

REM -------------------------------------------------------------------------
REM  STEP 1: Check for uv
REM -------------------------------------------------------------------------
echo   %STEP%  %C_BOLD%Checking for uv package manager...%C_RESET%

where uv >nul 2>nul
if errorlevel 1 (
    echo   %FAIL%  %C_BRED%uv not found.%C_RESET%
    echo.
    echo   %C_CYAN%  +----------------------------------------------------------+%C_RESET%
    echo   %C_CYAN%  ^|%C_RESET%  uv is required to manage Python and dependencies.      %C_CYAN%^|%C_RESET%
    echo   %C_CYAN%  ^|%C_RESET%                                                         %C_CYAN%^|%C_RESET%
    echo   %C_CYAN%  ^|%C_RESET%  %C_BOLD%Install uv:%C_RESET%                                            %C_CYAN%^|%C_RESET%
    echo   %C_CYAN%  ^|%C_RESET%  %C_BYELLOW%powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"%C_RESET% %C_CYAN%^|%C_RESET%
    echo   %C_CYAN%  ^|%C_RESET%                                                         %C_CYAN%^|%C_RESET%
    echo   %C_CYAN%  ^|%C_RESET%  Then %C_BOLD%close and reopen your terminal%C_RESET% and run this again.  %C_CYAN%^|%C_RESET%
    echo   %C_CYAN%  +----------------------------------------------------------+%C_RESET%
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('uv --version 2^>nul') do set "UV_VER=%%v"
echo   %PASS%  Found %C_GREEN%%UV_VER%%C_RESET%

REM -------------------------------------------------------------------------
REM  STEP 2: Check Python version
REM -------------------------------------------------------------------------
echo.
echo   %STEP%  %C_BOLD%Checking Python 3.11+...%C_RESET%

uv python find 3.11 >nul 2>nul
if errorlevel 1 (
    echo   %INFO%  Python 3.11 not found locally. Installing via uv...
    uv python install 3.11
    if errorlevel 1 (
        echo   %FAIL%  %C_BRED%Failed to install Python 3.11.%C_RESET%
        pause
        exit /b 1
    )
)
echo   %PASS%  Python 3.11 available

REM -------------------------------------------------------------------------
REM  STEP 3: Sync dependencies
REM -------------------------------------------------------------------------
echo.
echo   %STEP%  %C_BOLD%Installing dependencies...%C_RESET%
echo   %INFO%  %C_DIM%psutil, rich, typer%C_RESET%

pushd "%SCRIPT_DIR%"
uv sync --quiet 2>nul
if errorlevel 1 (
    echo   %FAIL%  %C_BRED%Dependency install failed.%C_RESET%
    echo   %C_DIM%  Try running: uv sync  (from the project directory)%C_RESET%
    popd
    pause
    exit /b 1
)
popd

echo   %PASS%  All dependencies installed

REM -------------------------------------------------------------------------
REM  STEP 4: Verify the app runs
REM -------------------------------------------------------------------------
echo.
echo   %STEP%  %C_BOLD%Verifying peepBeefy...%C_RESET%

uv run "%SCRIPT_DIR%src\main.py" --help >nul 2>nul
if errorlevel 1 (
    echo   %FAIL%  %C_BRED%Application failed to start.%C_RESET%
    pause
    exit /b 1
)

echo   %PASS%  peepBeefy is ready
echo.

REM -------------------------------------------------------------------------
REM  SUCCESS
REM -------------------------------------------------------------------------
echo %C_CYAN%  ------------------------------------------------------------------------%C_RESET%
echo.
echo   %C_BGREEN%Setup complete.%C_RESET%
echo.
echo %C_CYAN%  +----------------------------------------------------------------------+%C_RESET%
echo %C_CYAN%  ^|%C_RESET%                                                                    %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%  %C_BOLD%How to use peepBeefy:%C_RESET%                                            %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%                                                                    %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%  Open any terminal and type:                                       %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%                                                                    %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_BCYAN%beefy%C_RESET%                %C_DIM%Interactive mode (recommended)%C_RESET%          %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_BCYAN%beefy peep all%C_RESET%       %C_DIM%Quick scan from the command line%C_RESET%        %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_BCYAN%beefy peep cpu%C_RESET%       %C_DIM%Find CPU hogs%C_RESET%                           %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_BCYAN%beefy peep watch%C_RESET%     %C_DIM%Live scoreboard%C_RESET%                          %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%                                                                    %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%  %C_DIM%Developer spec:%C_RESET%                                                %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_YELLOW%beefy dev dump%C_RESET%       %C_DIM%Full JSON process dump%C_RESET%                  %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_YELLOW%beefy dev info PID%C_RESET%   %C_DIM%Deep process inspection%C_RESET%                 %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%    %C_YELLOW%beefy dev top beef%C_RESET%   %C_DIM%Developer top-N view%C_RESET%                    %C_CYAN%^|%C_RESET%
echo %C_CYAN%  ^|%C_RESET%                                                                    %C_CYAN%^|%C_RESET%
echo %C_CYAN%  +----------------------------------------------------------------------+%C_RESET%
echo.
echo   %C_DIM%You can close this window. peepBeefy is installed.%C_RESET%
echo.
pause
