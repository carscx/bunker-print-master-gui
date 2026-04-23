@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" goto usage

set "TARGET_FILE=%~1"
if not exist "%TARGET_FILE%" (
    echo No existe el archivo a firmar: %TARGET_FILE%
    exit /b 1
)

if "%SIGN_PFX%"=="" (
    echo Debes configurar SIGN_PFX con la ruta del certificado .pfx
    exit /b 1
)

if not exist "%SIGN_PFX%" (
    echo No existe el certificado: %SIGN_PFX%
    exit /b 1
)

if "%SIGN_PFX_PASSWORD%"=="" (
    echo Debes configurar SIGN_PFX_PASSWORD con la clave del .pfx
    exit /b 1
)

if "%SIGN_TIMESTAMP_URL%"=="" (
    set "SIGN_TIMESTAMP_URL=http://timestamp.digicert.com"
)

set "SIGNTOOL_EXE="
where signtool >nul 2>nul
if %errorlevel%==0 for /f "delims=" %%I in ('where signtool') do set "SIGNTOOL_EXE=%%I"

if "%SIGNTOOL_EXE%"=="" if exist "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" set "SIGNTOOL_EXE=C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
if "%SIGNTOOL_EXE%"=="" if exist "C:\Program Files\Windows Kits\10\bin\x64\signtool.exe" set "SIGNTOOL_EXE=C:\Program Files\Windows Kits\10\bin\x64\signtool.exe"

if "%SIGNTOOL_EXE%"=="" (
    echo No se encontro signtool.exe.
    echo Instala Windows SDK o agrega signtool al PATH.
    exit /b 1
)

echo Usando signtool: %SIGNTOOL_EXE%
"%SIGNTOOL_EXE%" sign /f "%SIGN_PFX%" /p "%SIGN_PFX_PASSWORD%" /fd SHA256 /tr "%SIGN_TIMESTAMP_URL%" /td SHA256 /d "Bunker Print Master GUI" /v "%TARGET_FILE%"
if %errorlevel% neq 0 (
    echo Error firmando: %TARGET_FILE%
    exit /b %errorlevel%
)

"%SIGNTOOL_EXE%" verify /pa /v "%TARGET_FILE%"
if %errorlevel% neq 0 (
    echo Error verificando firma: %TARGET_FILE%
    exit /b %errorlevel%
)

echo Firma aplicada correctamente: %TARGET_FILE%
exit /b 0

:usage
echo Uso: sign_release.bat "ruta\\archivo.exe"
echo Requiere variables: SIGN_PFX y SIGN_PFX_PASSWORD
exit /b 1
