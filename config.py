# -*- coding: utf-8 -*-
"""Configuración central del Auto Fichaje NCS Clock.

Constantes (horarios, reintentos, selectores) + resolución de paths.

Los archivos de runtime viven en `DATA_DIR`, que se resuelve así:
  1. Variable de entorno `AUTO_FICHAJE_DATA_DIR` (se crea si no existe).
  2. Si el proceso está congelado por PyInstaller → carpeta del .exe.
  3. Modo desarrollo → carpeta de este archivo.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _data_dir() -> Path:
    env = os.getenv("AUTO_FICHAJE_DATA_DIR")
    if env:
        p = Path(env).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DATA_DIR = _data_dir()

# Archivos de runtime
CSV_FICHAJES = DATA_DIR / "fichajes.csv"
ESTADO_FILE = DATA_DIR / "estado_diario.json"
LOCK_FILE = DATA_DIR / "auto_fichaje.lock"
LOG_FILE = DATA_DIR / "auto_fichaje.log"

# URL del fichaje
URL_FICHAJE = "https://clock.ncs.es/ClienteReloj/DoTicada"

# Ventanas horarias (hora española)
ENTRADA_DESDE = "08:35"
ENTRADA_HASTA = "09:05"
SALIDA_DESDE = "18:00"
SALIDA_HASTA = "18:30"

SALIDA_ALMUERZO = "14:01"
ENTRADA_ALMUERZO = "15:01"

# Reintentos
MAX_REINTENTOS = 3
BACKOFF_REINTENTOS = [300, 600, 900]  # 5, 10, 15 min
MARGEN_VENTANA_EXTRA = 30  # min tras cierre de ventana

# Días laborables (0=Lunes, 4=Viernes)
DIAS_LABORABLES = [0, 1, 2, 3, 4]

# Credenciales (lectura desde .env como respaldo; modo principal: credenciales.py)
USUARIO = os.getenv("NCS_USUARIO", "")
PASSWORD = os.getenv("NCS_PASSWORD", "")

# Comportamiento humano simulado
PAUSA_MIN = 1.0
PAUSA_MAX = 3.5
TIMEOUT_CARGA = 30

# Selectores CSS para el boton de fichaje (probados en orden).
# El HTML actual de NCS usa <a id="btnTicar"> (enlace, NO un button).
# Mantenemos varios para tolerar cambios futuros del DOM.
SELECTORES_BOTON_FICHAJE = [
    "a#btnTicar",                # actual: <a id="btnTicar">Marcar</a>
    "#btnTicar",                 # fallback: cualquier tag con ese id
    "button#btnTicar",           # por si lo cambian a button
    "input#btnTicar",
    "a#btnTicada",
    "#btnTicada",
]

# Selectores para login
SELECTOR_CAMPO_USUARIO = "input#tbUserName"
SELECTOR_CAMPO_PASSWORD = "input#tbPassword"
SELECTOR_BOTON_LOGIN = "button#LoginBtn, input#LoginBtn"
