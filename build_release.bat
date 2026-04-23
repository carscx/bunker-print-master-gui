@echo off
setlocal
cd /d "%~dp0"

set "APP_VERSION=%~1"
set "PY_CMD="
set "LATEST_INSTALLER="

if "%APP_VERSION%"=="" (
    if exist "%~dp0version.txt" (
        set /p APP_VERSION=<"%~dp0version.txt"
    )
)
if "%APP_VERSION%"=="" set "APP_VERSION=0.0.0"

echo Preparando release v%APP_VERSION%
>"%~dp0version.txt" echo %APP_VERSION%

echo Limpiando instaladores antiguos...
for %%F in ("%~dp0installer\Setup-Bunker-Print-Master-GUI-*.exe") do (
    if exist "%%~fF" del /q "%%~fF"
)
if exist "%~dp0installer\SHA256SUMS.txt" del /q "%~dp0installer\SHA256SUMS.txt"

if exist "..\.venv\Scripts\python.exe" (
    set "PY_CMD=..\.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
    echo No se encontro Python para compilar.
    echo Instala Python o crea el entorno virtual en ..\.venv
    exit /b 1
)

echo [1/2] Compilando ejecutable con PyInstaller...
%PY_CMD% -m PyInstaller imprimir_gui.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo Fallo la compilacion del ejecutable.
    exit /b %errorlevel%
)

if not "%SIGN_PFX%"=="" (
    echo [Firma] Firmando ejecutable...
    call "%~dp0sign_release.bat" "%~dp0dist\imprimir_gui.exe"
    if %errorlevel% neq 0 (
        echo Fallo el firmado del ejecutable.
        exit /b %errorlevel%
    )
) else (
    echo [Firma] SIGN_PFX no configurado. Se omite firma del ejecutable.
)

echo [2/2] Compilando instalador con Inno Setup...
call "%~dp0build_installer.bat" %APP_VERSION%
if %errorlevel% neq 0 (
    echo Fallo la compilacion del instalador.
    exit /b %errorlevel%
)

for /f "delims=" %%I in ('dir /b /a:-d /o:-d "%~dp0installer\Setup-Bunker-Print-Master-GUI-*.exe" 2^>nul') do (
    set "LATEST_INSTALLER=%~dp0installer\%%I"
    goto installer_found
)

:installer_found

if "%LATEST_INSTALLER%"=="" (
    echo No se encontro instalador para firmar.
    exit /b 1
)

if not "%SIGN_PFX%"=="" (
    echo [Firma] Firmando instalador...
    call "%~dp0sign_release.bat" "%LATEST_INSTALLER%"
    if %errorlevel% neq 0 (
        echo Fallo el firmado del instalador.
        exit /b %errorlevel%
    )
) else (
    echo [Firma] SIGN_PFX no configurado. Se omite firma del instalador.
)

echo [Extra] Generando checksums SHA256...
call "%~dp0create_checksums.bat"
if %errorlevel% neq 0 (
    echo Fallo la generacion de checksums.
    exit /b %errorlevel%
)

echo Release generada correctamente.
echo Instalador mas reciente: %LATEST_INSTALLER%
echo Revisa la carpeta: %~dp0installer
exit /b 0



