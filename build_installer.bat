@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0dist\imprimir_gui.exe" goto no_dist

set "APP_VERSION=%~1"
set "ISCC_EXE="

if "%APP_VERSION%"=="" (
    if exist "%~dp0version.txt" (
        set /p APP_VERSION=<"%~dp0version.txt"
    )
)

where iscc >nul 2>nul
if %errorlevel%==0 for /f "delims=" %%I in ('where iscc') do set "ISCC_EXE=%%I"

if not "%ISCC_EXE%"=="" goto found_iscc

if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not "%ISCC_EXE%"=="" goto found_iscc

if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not "%ISCC_EXE%"=="" goto found_iscc

if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not "%ISCC_EXE%"=="" goto found_iscc

echo No se encontro Inno Setup (ISCC.exe).
echo Instala Inno Setup 6 y vuelve a ejecutar este archivo.
exit /b 1

:found_iscc

echo Usando: %ISCC_EXE%
if "%APP_VERSION%"=="" set "APP_VERSION=0.0.0"

echo Compilando instalador version %APP_VERSION%
"%ISCC_EXE%" /DMyAppVersion=%APP_VERSION% "%~dp0imprimir_gui_installer.iss"
if %errorlevel% neq 0 goto build_failed
goto done

:done
echo Instalador generado en: %~dp0installer
exit /b 0

:no_dist
echo No se encontro dist\imprimir_gui.exe
echo Primero compila la app con PyInstaller.
exit /b 1

:build_failed
echo Fallo la compilacion del instalador.
exit /b %errorlevel%
