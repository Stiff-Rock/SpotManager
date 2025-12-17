@echo off
setlocal

:: 1. Definir el nombre de la carpeta del entorno virtual
set VENV_DIR=.venv

:: 2. Verificar si el entorno virtual existe
if not exist %VENV_DIR% (
    echo [!] No se encontro el entorno virtual. Creandolo...
    python -m venv %VENV_DIR%
    
    echo [!] Instalando dependencias desde requirements.txt...
    call %VENV_DIR%\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo [OK] Entorno preparado.
) else (
    echo [OK] Entorno virtual detectado.
    call %VENV_DIR%\Scripts\activate
)

:: 3. Ejecutar la aplicación
echo [>] Iniciando SpotManager...
python main.py

:: 4. Pausar en caso de error para poder leer el traceback
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] La aplicacion se detuvo de forma inesperada.
    pause
)

endlocal
