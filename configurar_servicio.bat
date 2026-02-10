@echo off
REM ============================================================
REM Script para encontrar pythonw.exe y configurar el servicio
REM ============================================================

echo.
echo ========================================
echo   Configurador de Servicio Auto Fichaje
echo ========================================
echo.

REM Buscar pythonw.exe
echo [1/3] Buscando pythonw.exe...
for /f "delims=" %%i in ('where pythonw 2^>nul') do set PYTHONW_PATH=%%i

if "%PYTHONW_PATH%"=="" (
    echo.
    echo ERROR: No se encontro pythonw.exe
    echo.
    echo Instala Python desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion
    echo.
    pause
    exit /b 1
)

echo    Encontrado: %PYTHONW_PATH%
echo.

REM Obtener directorio actual
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo [2/3] Directorio del script:
echo    %SCRIPT_DIR%
echo.

REM Mostrar configuración
echo [3/3] Configuracion para el Programador de Tareas:
echo.
echo ========================================
echo   COPIA ESTA INFORMACION:
echo ========================================
echo.
echo Programa o script:
echo    %PYTHONW_PATH%
echo.
echo Agregar argumentos:
echo    auto_fichaje.py
echo.
echo Iniciar en:
echo    %SCRIPT_DIR%
echo.
echo ========================================
echo.

echo Ahora sigue estos pasos:
echo.
echo 1. Presiona Win+R
echo 2. Escribe: taskschd.msc
echo 3. Crear tarea basica...
echo 4. Nombre: Auto Fichaje NCS
echo 5. Desencadenador: Al iniciar sesion
echo 6. Accion: Iniciar un programa
echo 7. Usa los valores mostrados arriba
echo.

pause
