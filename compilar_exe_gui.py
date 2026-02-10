# -*- coding: utf-8 -*-
"""
Script para compilar auto_fichaje_gui.py en un ejecutable (.exe)
con interfaz gráfica de configuración
"""

import os
import sys
import subprocess

print("=" * 60)
print("  🔨 COMPILADOR DE AUTO FICHAJE GUI A EJECUTABLE")
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
print("Preparando compilación de versión GUI...")
print()

# Comando de PyInstaller
comando = [
    "pyinstaller",
    "--onefile",                    # Un solo archivo .exe
    "--windowed",                   # Sin consola (pero con GUI)
    "--name=AutoFichajeNCS",        # Nombre del ejecutable
    "--icon=NONE",                  # Sin icono
    "--hidden-import=selenium",
    "--hidden-import=selenium.webdriver",
    "--hidden-import=selenium.webdriver.chrome.service",
    "--hidden-import=selenium.webdriver.chrome.options",
    "--hidden-import=webdriver_manager",
    "--hidden-import=webdriver_manager.chrome",
    "--hidden-import=tkinter",
    "--collect-all=selenium",
    "--collect-all=webdriver_manager",
    "auto_fichaje_gui.py"
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
    print("🎉 LISTO PARA DISTRIBUIR:")
    print()
    print("1. Copia 'dist\\AutoFichajeNCS.exe' a cualquier PC")
    print("2. Ejecuta el .exe")
    print("3. Aparecerá una ventana para introducir usuario y contraseña")
    print("4. Las credenciales se guardan automáticamente")
    print("5. El servicio queda funcionando hasta apagar el PC")
    print()
    print("Para tus compañeros:")
    print("- Solo necesitan el .exe")
    print("- Al ejecutarlo, introducen sus credenciales")
    print("- ¡Ya está funcionando!")
    print()
    
except subprocess.CalledProcessError as e:
    print()
    print("=" * 60)
    print("❌ ERROR EN LA COMPILACIÓN")
    print("=" * 60)
    print()
    print(f"Error: {e}")
    sys.exit(1)
