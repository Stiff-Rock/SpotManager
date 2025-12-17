@echo off
setlocal

set VENV_DIR=.venv

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

echo [^>] Iniciando SpotManager...
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] La aplicacion se detuvo de forma inesperada.
    pause
)

endlocal
