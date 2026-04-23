@echo off
setlocal
cd /d "%~dp0"

set "OUT_FILE=%~dp0installer\SHA256SUMS.txt"
set "PS_CMD="

where pwsh >nul 2>nul
if not errorlevel 1 set "PS_CMD=pwsh"

if not "%PS_CMD%"=="" goto have_ps

where powershell >nul 2>nul
if not errorlevel 1 set "PS_CMD=powershell"

if not "%PS_CMD%"=="" goto have_ps

if "%PS_CMD%"=="" goto no_ps

:have_ps

%PS_CMD% -NoProfile -ExecutionPolicy Bypass -File "%~dp0create_checksums.ps1"
if errorlevel 1 goto checksum_error

echo Checksums generados en: %OUT_FILE%
exit /b 0

:no_ps
echo No se encontro PowerShell (powershell o pwsh).
exit /b 1

:checksum_error
echo Error generando checksums.
exit /b 1
