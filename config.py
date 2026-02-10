# -*- coding: utf-8 -*-
"""
Configuración del script de fichaje automático - NCS Clock
Edita este archivo para personalizar los horarios y comportamiento.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 🌐 URL de fichaje
# ============================================================
URL_FICHAJE = "https://clock.ncs.es/ClienteReloj/DoTicada"
URL_LOGIN = "https://clock.ncs.es/User/PopUpLogin"

# ============================================================
# ⏰ Horarios de fichaje (formato HH:MM)
# ============================================================
# ENTRADA: se fichará en un minuto aleatorio entre estas dos horas
ENTRADA_DESDE = "08:55"
ENTRADA_HASTA = "09:05"

# SALIDA: se fichará en un minuto aleatorio entre estas dos horas
SALIDA_DESDE = "18:00"
SALIDA_HASTA = "18:30"

# ============================================================
# 📅 Días laborables (0=Lunes, 4=Viernes)
# ============================================================
DIAS_LABORABLES = [0, 1, 2, 3, 4]  # Lunes a Viernes

# ============================================================
# 🧑 Credenciales (se leen desde .env)
# ============================================================
USUARIO = os.getenv("NCS_USUARIO", "")
PASSWORD = os.getenv("NCS_PASSWORD", "")

# ============================================================
# 🌐 Configuración del navegador Chrome
# ============================================================
# Ruta al perfil de usuario de Chrome para reutilizar la sesión
# Típicamente: C:\Users\TU_USUARIO\AppData\Local\Google\Chrome\User Data
CHROME_USER_DATA_DIR = os.getenv(
    "CHROME_USER_DATA_DIR",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
)

# Nombre del perfil de Chrome (normalmente "Default" o "Profile 1", etc.)
CHROME_PROFILE = os.getenv("CHROME_PROFILE", "Default")

# Ruta al ejecutable de Chrome (None = autodetectar)
CHROME_BINARY = os.getenv("CHROME_BINARY", None)

# ============================================================
# 🤖 Comportamiento humano simulado
# ============================================================
# Pausas aleatorias entre acciones (en segundos)
PAUSA_MIN = 1.0   # Mínimo de pausa entre acciones
PAUSA_MAX = 3.5   # Máximo de pausa entre acciones

# Tiempo máximo de espera para cargar la página (segundos)
TIMEOUT_CARGA = 30

# ============================================================
# 🔍 Selectores CSS para encontrar elementos en la página
# ============================================================
# Estos selectores se usan para encontrar el botón de fichaje.
# Si la página cambia, ajústalos con el modo --descubrir.
# Se prueban en orden hasta encontrar uno que funcione.
SELECTORES_BOTON_FICHAJE = [
    "button#btnTicada",
    "input#btnTicada",
    "a#btnTicada",
    "button.btn-ticada",
    "input[type='submit'][value*='Ticar']",
    "input[type='button'][value*='Ticar']",
    "button[onclick*='Ticada']",
    "input[type='submit'][value*='Fichar']",
    "button:contains('Fichar')",
    "input[type='submit']",
    "button.btn-primary",
    "#btnDoTicada",
    ".btn-ticada",
    "a.btn-primary",
]

# Selectores para detectar confirmación de fichaje exitoso
SELECTORES_CONFIRMACION = [
    ".alert-success",
    ".msg-ok",
    ".ticada-ok",
    "#msgExito",
    ".text-success",
    "[class*='success']",
    "[class*='exito']",
]

# Selectores para campos de login (por si se necesita login)
SELECTOR_CAMPO_USUARIO = "input#UserName, input[name='UserName'], input[name='usuario'], input[type='email']"
SELECTOR_CAMPO_PASSWORD = "input#Password, input[name='Password'], input[name='password'], input[type='password']"
SELECTOR_BOTON_LOGIN = "input[type='submit'], button[type='submit'], button.btn-primary, #btnLogin"
