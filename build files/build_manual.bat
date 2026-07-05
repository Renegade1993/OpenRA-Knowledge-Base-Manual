@echo off
setlocal enabledelayedexpansion

:: build_manual.bat
:: Wrapper for build_manual.ps1 that automatically requests Administrator privileges
:: when needed and bypasses the PowerShell execution-policy restriction.
:: Usage: build_manual.bat [none|docx|pdf|all]

:: Check if we are running as Administrator.
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================================
    echo This build may need Administrator privileges to install
    echo or update external tools (MiKTeX packages, Chocolatey, etc.).
    echo Re-launching as Administrator...
    echo ========================================================
    timeout /t 2 /nobreak >nul
    powershell -Command "Start-Process '%~f0' -Verb runAs -ArgumentList '%*'"
    exit /b %errorLevel%
)

:: Locate the sibling PowerShell script.
set "PS_SCRIPT=%~dp0build_manual.ps1"
if not exist "%PS_SCRIPT%" (
    echo ERROR: Could not find %PS_SCRIPT%
    pause
    exit /b 1
)

:: Run the PowerShell script with Bypass execution policy and forward all arguments.
echo Running: powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*
powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" %*

if %errorLevel% neq 0 (
    echo.
    echo Build finished with errors (exit code %errorLevel%).
    pause
    exit /b %errorLevel%
)

echo.
echo Build finished successfully.
pause
exit /b 0
