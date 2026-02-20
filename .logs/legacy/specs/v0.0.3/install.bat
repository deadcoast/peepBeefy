@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM  peepBeefy  --  Installation Script
REM  First-time setup. After install, use:  beefy  or  beefy dev ...
REM ============================================================================

REM --- Generate ESC character for ANSI sequences (reliable via PowerShell) ---
for /f %%e in ('powershell -noprofile -command "[char]27"') do set "ESC=%%e"

set "C=%ESC%[36m"
set "BC=%ESC%[1;36m"
set "G=%ESC%[32m"
set "BG=%ESC%[1;32m"
set "R=%ESC%[1;31m"
set "Y=%ESC%[33m"
set "BY=%ESC%[1;33m"
set "B=%ESC%[1m"
set "D=%ESC%[2m"
set "X=%ESC%[0m"

set "SCRIPT_DIR=%~dp0"

cls

REM --- Header ----------------------------------------------------------------

echo.
echo %C%  ========================================================================%X%
echo %C%  ==%X%                                                              %C%==%X%
echo %C%  ==%X%  %BC%              (          (%X%                           %C%==%X%
echo %C%  ==%X%  %BC%   (   (      ( )\   (   ( )\ ) (%X%                    %C%==%X%
echo %C%  ==%X%  %C% `  )   ))\ ))\`  ) )((_) ))\ ))(()/(  )\ )%X%           %C%==%X%
echo %C%  ==%X%  %C% /(/(  /((_)((_)(/(((_)_ /((_)((_)(_)^|()/ (%X%          %C%==%X%
echo %C%  ==%X%  %B%((_)_\(_))(_))((_)_\^| _ ^|_))(_))(_) _^|)(_))%X%        %C%==%X%
echo %C%  ==%X%  %B%^| '_ \) -_) -_) '_ \) _ Y -_) -_)^|  _^| ^|^| ^|%X%     %C%==%X%
echo %C%  ==%X%  %B%^| .__/\___\___^| .__/^|___^|___\___^|^|_^|  \_, ^|%X%   %C%==%X%
echo %C%  ==%X%  %B%^|_^|           ^|_^|                     ^|__/%X%       %C%==%X%
echo %C%  ==%X%                                                              %C%==%X%
echo %C%  ==%X%  %B%peepBeefy%X% %D%v0.0.4%X%                                %C%==%X%
echo %C%  ==%X%  %D%Find and display heavy running processes             %X% %C%==%X%
echo %C%  ==%X%                                                              %C%==%X%
echo %C%  ========================================================================%X%
echo.
echo   %BC%INSTALLER%X%  %D%First-time setup%X%
echo   %D%This script prepares your system to run peepBeefy.%X%
echo   %D%After setup, you will never need to run this file again.%X%
echo.
echo %C%  ------------------------------------------------------------------------%X%
echo.

REM -------------------------------------------------------------------------
REM  STEP 1 : Check for uv
REM -------------------------------------------------------------------------
echo   %BC%[^>^>]%X%  %B%Checking for uv package manager...%X%

where uv >nul 2>nul
if errorlevel 1 goto :no_uv

for /f "tokens=*" %%v in ('uv --version 2^>nul') do set "UV_VER=%%v"
echo   %BG%[ok]%X%  Found %G%%UV_VER%%X%
goto :step2

:no_uv
echo   %R%[!!]%X%  %R%uv not found.%X%
echo.
echo   %C%  +----------------------------------------------------------+%X%
echo   %C%  ^|%X%  uv is required to manage Python and dependencies.      %C%^|%X%
echo   %C%  ^|%X%                                                         %C%^|%X%
echo   %C%  ^|%X%  %B%Install uv:%X%                                            %C%^|%X%
echo   %C%  ^|%X%  %BY%powershell -c "irm https://astral.sh/uv/install.ps1 ^| iex"%X% %C%^|%X%
echo   %C%  ^|%X%                                                         %C%^|%X%
echo   %C%  ^|%X%  Then %B%close and reopen your terminal%X% and run this again.  %C%^|%X%
echo   %C%  +----------------------------------------------------------+%X%
echo.
pause
exit /b 1

REM -------------------------------------------------------------------------
REM  STEP 2 : Check Python 3.11
REM -------------------------------------------------------------------------
:step2
echo.
echo   %BC%[^>^>]%X%  %B%Checking Python 3.11+...%X%

uv python find 3.11 >nul 2>nul
if errorlevel 1 goto :install_python

echo   %BG%[ok]%X%  Python 3.11 available
goto :step3

:install_python
echo   %D%[..]%X%  Python 3.11 not found locally. Installing via uv...
uv python install 3.11
if errorlevel 1 goto :python_fail
echo   %BG%[ok]%X%  Python 3.11 installed
goto :step3

:python_fail
echo   %R%[!!]%X%  %R%Failed to install Python 3.11.%X%
pause
exit /b 1

REM -------------------------------------------------------------------------
REM  STEP 3 : Sync dependencies
REM -------------------------------------------------------------------------
:step3
echo.
echo   %BC%[^>^>]%X%  %B%Installing dependencies...%X%
echo   %D%[..]%X%  %D%psutil, rich, typer%X%

pushd "%SCRIPT_DIR%"
uv sync --quiet 2>nul
if errorlevel 1 goto :sync_fail
popd

echo   %BG%[ok]%X%  All dependencies installed
goto :step4

:sync_fail
echo   %R%[!!]%X%  %R%Dependency install failed.%X%
echo   %D%  Try running:  uv sync  from the project directory%X%
popd
pause
exit /b 1

REM -------------------------------------------------------------------------
REM  STEP 4 : Verify the app runs
REM -------------------------------------------------------------------------
:step4
echo.
echo   %BC%[^>^>]%X%  %B%Verifying peepBeefy...%X%

uv run "%SCRIPT_DIR%src\main.py" --help >nul 2>nul
if errorlevel 1 goto :verify_fail

echo   %BG%[ok]%X%  peepBeefy is ready
goto :success

:verify_fail
echo   %R%[!!]%X%  %R%Application failed to start.%X%
pause
exit /b 1

REM -------------------------------------------------------------------------
REM  SUCCESS
REM -------------------------------------------------------------------------
:success
echo.
echo %C%  ------------------------------------------------------------------------%X%
echo.
echo   %BG%Setup complete.%X%
echo.
echo %C%  +----------------------------------------------------------------------+%X%
echo %C%  ^|%X%                                                                    %C%^|%X%
echo %C%  ^|%X%  %B%How to use peepBeefy:%X%                                            %C%^|%X%
echo %C%  ^|%X%                                                                    %C%^|%X%
echo %C%  ^|%X%  Open any terminal and type:                                       %C%^|%X%
echo %C%  ^|%X%                                                                    %C%^|%X%
echo %C%  ^|%X%    %BC%beefy%X%                %D%Interactive mode ^(recommended^)%X%          %C%^|%X%
echo %C%  ^|%X%    %BC%beefy peep all%X%       %D%Quick scan from the command line%X%        %C%^|%X%
echo %C%  ^|%X%    %BC%beefy peep cpu%X%       %D%Find CPU hogs%X%                           %C%^|%X%
echo %C%  ^|%X%    %BC%beefy peep watch%X%     %D%Live scoreboard%X%                          %C%^|%X%
echo %C%  ^|%X%                                                                    %C%^|%X%
echo %C%  ^|%X%  %D%Developer spec:%X%                                                %C%^|%X%
echo %C%  ^|%X%    %Y%beefy dev dump%X%       %D%Full JSON process dump%X%                  %C%^|%X%
echo %C%  ^|%X%    %Y%beefy dev info PID%X%   %D%Deep process inspection%X%                 %C%^|%X%
echo %C%  ^|%X%    %Y%beefy dev top beef%X%   %D%Developer top-N view%X%                    %C%^|%X%
echo %C%  ^|%X%                                                                    %C%^|%X%
echo %C%  +----------------------------------------------------------------------+%X%
echo.
echo   %D%You can close this window. peepBeefy is installed.%X%
echo.
pause
