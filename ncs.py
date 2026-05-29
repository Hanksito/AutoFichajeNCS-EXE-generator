# -*- coding: utf-8 -*-
"""Interacción con clock.ncs.es: login, lectura de estado y fichaje.

Todo lo que sabe del HTML de NCS vive aquí. Si NCS cambia el DOM,
solo este archivo debe actualizarse.

Las funciones críticas tienen GUARDIAS que abortan antes de pulsar
el botón cuando el estado no es claro, para no desfichar al usuario.
"""
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import config


# ──────────────────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────────────────

@dataclass
class EstadoWeb:
    accion_siguiente: Literal["ENTRADA", "SALIDA", "DESCONOCIDO"]
    presencia_actual: str  # "HH:MM"
    coherente: bool


@dataclass
class ResultadoFichaje:
    success: bool
    saltado: bool
    tipo: str
    hora_fichaje: str
    presencia: str
    jornada: str
    extra: str
    mensaje: str
    html_cambio: bool = False


# ──────────────────────────────────────────────────────────
# Helpers humanos
# ──────────────────────────────────────────────────────────

def _pausa_humana(minimo: float = 0.5, maximo: float = 1.5) -> None:
    time.sleep(random.uniform(minimo, maximo))


# ──────────────────────────────────────────────────────────
# Lectura de estado (sin reintentos)
# ──────────────────────────────────────────────────────────

def _detectar_estado_una_vez(driver) -> Literal["ENTRADA", "SALIDA", "DESCONOCIDO"]:
    """Lee la alerta una sola vez."""
    # Alert success → estás DENTRO, próximo es SALIDA
    try:
        a = driver.find_element(By.CSS_SELECTOR, ".alert.alert-success")
        if a.is_displayed():
            texto = a.text.strip().upper()
            if "SALIR" in texto or "DENTRO" in texto:
                return "SALIDA"
    except NoSuchElementException:
        pass
    # Alert info → estás FUERA, próximo es ENTRADA
    try:
        a = driver.find_element(By.CSS_SELECTOR, ".alert.alert-info")
        if a.is_displayed():
            texto = a.text.strip().upper()
            if "ENTRAR" in texto or "FUERA" in texto:
                return "ENTRADA"
    except NoSuchElementException:
        pass
    return "DESCONOCIDO"


def _obtener_presencia(driver) -> str:
    """Lee el campo de presencia. Devuelve 'HH:MM' o '00:00' si no se encuentra."""
    try:
        elem = driver.find_element(By.ID, "presencia")
        return elem.text.strip() or "00:00"
    except NoSuchElementException:
        return "00:00"


def _presencia_a_segundos(presencia: str) -> int:
    """'HH:MM' → segundos. 0 si no se puede parsear."""
    try:
        partes = presencia.strip().split(":")
        if len(partes) >= 2:
            return int(partes[0]) * 3600 + int(partes[1]) * 60
    except ValueError:
        pass
    return 0


# ──────────────────────────────────────────────────────────
# Lectura segura (con reintentos + coherencia)
# ──────────────────────────────────────────────────────────

def leer_estado_seguro(driver, intentos: int = 3, espera: float = 2.0) -> EstadoWeb:
    """Lee el estado con reintentos y verifica coherencia alerta vs presencia.

    Returns:
        EstadoWeb con:
        - accion_siguiente: "ENTRADA", "SALIDA" o "DESCONOCIDO"
        - presencia_actual: "HH:MM" leído de la página
        - coherente: True si alerta y presencia concuerdan
    """
    accion: Literal["ENTRADA", "SALIDA", "DESCONOCIDO"] = "DESCONOCIDO"
    for i in range(intentos):
        accion = _detectar_estado_una_vez(driver)
        if accion != "DESCONOCIDO":
            break
        if i < intentos - 1 and espera > 0:
            time.sleep(espera)

    presencia = _obtener_presencia(driver)
    segs = _presencia_a_segundos(presencia)

    # Coherencia: alerta vs presencia
    coherente = True
    if accion == "ENTRADA" and segs > 0:
        coherente = False
    elif accion == "SALIDA" and segs == 0:
        coherente = False
    elif accion == "DESCONOCIDO":
        coherente = False  # no podemos confirmar nada

    return EstadoWeb(
        accion_siguiente=accion,
        presencia_actual=presencia,
        coherente=coherente,
    )
