# -*- coding: utf-8 -*-
"""
Script para compilar auto_fichaje.py en un ejecutable (.exe)
Usa PyInstaller para crear un .exe standalone
"""

import os
import sys
import subprocess

print("=" * 60)
print("  🔨 COMPILADOR DE AUTO FICHAJE A EJECUTABLE")
print("=" * 60)
print()

# Verificar que PyInstaller está instalado
try:
    import PyInstaller
    print("✅ PyInstaller encontrado")
except ImportError:
    print("❌ PyInstaller no está instalado")
    print()
    print("Instalando PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("✅ PyInstaller instalado")

print()
print("Preparando compilación...")
print()

# Comando de PyInstaller
comando = [
    "pyinstaller",
    "--onefile",                    # Un solo archivo .exe
    "--noconsole",                  # Sin ventana de consola (segundo plano)
    "--name=AutoFichajeNCS",        # Nombre del ejecutable
    "--icon=NONE",                  # Sin icono (puedes agregar uno si quieres)
    "--add-data=.env.example;.",    # Incluir .env.example
    "--hidden-import=selenium",
    "--hidden-import=selenium.webdriver",
    "--hidden-import=selenium.webdriver.chrome.service",
    "--hidden-import=selenium.webdriver.chrome.options",
    "--hidden-import=webdriver_manager",
    "--hidden-import=webdriver_manager.chrome",
    "--hidden-import=dotenv",
    "--collect-all=selenium",
    "--collect-all=webdriver_manager",
    "auto_fichaje.py"
]

print("Ejecutando PyInstaller...")
print()

try:
    subprocess.check_call(comando)
    print()
    print("=" * 60)
    print("✅ ¡COMPILACIÓN EXITOSA!")
    print("=" * 60)
    print()
    print("El ejecutable se encuentra en:")
    print(f"   📁 dist\\AutoFichajeNCS.exe")
    print()
    print("Próximos pasos:")
    print("1. Asegúrate de tener el archivo .env en la misma carpeta que el .exe")
    print("2. Ejecuta: dist\\AutoFichajeNCS.exe")
    print("3. O configúralo como servicio con NSSM (ver SERVICIO_WINDOWS.md)")
    print()
    
except subprocess.CalledProcessError as e:
    print()
    print("=" * 60)
    print("❌ ERROR EN LA COMPILACIÓN")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    sys.exit(1)
