@echo off
chcp 65001 > nul
echo ========================================================
echo   INICIANDO DASHBOARD DE RENTABILIDAD COMERCIAL (BI)
echo ========================================================
echo.

REM Verificar si existe el entorno de python en AppData o rutas estandar
set PYTHON_EXE=C:\Users\DELL\python311\python.exe

if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)

echo Usando ejecutable: %PYTHON_EXE%
"%PYTHON_EXE%" -m streamlit run app.py --server.port 8502

pause
