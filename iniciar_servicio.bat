@echo off
REM ============================================================
REM Script para iniciar Auto Fichaje en segundo plano
REM ============================================================

cd /d "%~dp0"

REM Usar pythonw.exe (sin ventana) en lugar de python.exe
pythonw.exe auto_fichaje.py

exit
