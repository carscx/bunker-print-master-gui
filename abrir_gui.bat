@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0dist\imprimir_gui.exe" (
    start "" "%~dp0dist\imprimir_gui.exe"
    exit /b 0
)

if exist "..\.venv\Scripts\pythonw.exe" (
    start "" "..\.venv\Scripts\pythonw.exe" "%~dp0imprimir_gui.py"
    exit /b 0
)

if exist "..\.venv\Scripts\python.exe" (
    start "" "..\.venv\Scripts\python.exe" "%~dp0imprimir_gui.py"
    exit /b 0
)

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw "%~dp0imprimir_gui.py"
    exit /b 0
)

echo No se encontro Python para abrir la GUI.
echo Instala Python o crea el entorno virtual en ..\.venv
pause
