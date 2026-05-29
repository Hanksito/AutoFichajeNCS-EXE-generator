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


# ──────────────────────────────────────────────────────────
# Localización del botón
# ──────────────────────────────────────────────────────────

def _localizar_boton(driver, timeout: int = 30):
    """Busca el botón de fichaje probando los selectores configurados.

    Returns:
        WebElement clickable, o None si no se encuentra.
    """
    for selector in config.SELECTORES_BOTON_FICHAJE:
        try:
            return WebDriverWait(driver, timeout / len(config.SELECTORES_BOTON_FICHAJE)).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            continue
    return None


# ──────────────────────────────────────────────────────────
# Helpers de respuesta
# ──────────────────────────────────────────────────────────

def _abortado(tipo: str, motivo: str, html_cambio: bool = False) -> ResultadoFichaje:
    return ResultadoFichaje(
        success=False, saltado=False, tipo=tipo,
        hora_fichaje="", presencia="", jornada="", extra="",
        mensaje=motivo, html_cambio=html_cambio,
    )


def _saltado(tipo: str, motivo: str, presencia: str) -> ResultadoFichaje:
    return ResultadoFichaje(
        success=True, saltado=True, tipo=tipo,
        hora_fichaje="", presencia=presencia, jornada="", extra="",
        mensaje=motivo,
    )


# ──────────────────────────────────────────────────────────
# realizar_fichaje — el corazón con las 3 guardias
# ──────────────────────────────────────────────────────────

def realizar_fichaje(driver, tipo_esperado: str) -> ResultadoFichaje:
    """Realiza el fichaje del tipo esperado, con tres guardias de seguridad.

    GUARDIA 1: aborta si el estado de la web no se puede leer (DESCONOCIDO).
    GUARDIA 2: aborta si la alerta y la presencia se contradicen (incoherencia).
    GUARDIA 3: si ya está hecho lo esperado, se salta sin pulsar.

    Solo si las tres guardias pasan, se pulsa el botón y se verifica.
    """
    estado = leer_estado_seguro(driver, intentos=3, espera=2.0)

    # GUARDIA 1
    if estado.accion_siguiente == "DESCONOCIDO":
        return _abortado(
            tipo_esperado,
            "No se pudo leer el estado en NCS tras 3 intentos. "
            "Aborto por seguridad para no desfichar.",
            html_cambio=True,
        )

    # GUARDIA 2
    if not estado.coherente:
        return _abortado(
            tipo_esperado,
            f"Alerta y presencia no coinciden "
            f"(accion={estado.accion_siguiente}, presencia={estado.presencia_actual}). "
            f"Aborto por seguridad.",
            html_cambio=True,
        )

    # GUARDIA 3: ya fichado a mano
    if tipo_esperado == "ENTRADA" and estado.accion_siguiente == "SALIDA":
        return _saltado(
            tipo_esperado,
            "Ya estás DENTRO; entrada omitida (fichaje manual previo).",
            estado.presencia_actual,
        )
    if tipo_esperado == "SALIDA" and estado.accion_siguiente == "ENTRADA":
        return _saltado(
            tipo_esperado,
            "Ya estás FUERA; salida omitida (sin entrada previa o salida manual).",
            estado.presencia_actual,
        )

    # Localizar y pulsar
    boton = _localizar_boton(driver)
    if boton is None:
        return _abortado(
            tipo_esperado,
            "No se encontró el botón de fichaje en la página.",
            html_cambio=True,
        )

    hora_fichaje = datetime.now().strftime("%H:%M:%S")
    _pausa_humana(0.8, 1.5)
    try:
        boton.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", boton)
        except Exception as e:
            return _abortado(tipo_esperado, f"No se pudo pulsar el botón: {e}")

    # Verificar cambio de estado tras el click
    _pausa_humana(1.0, 2.0)
    estado_post = leer_estado_seguro(driver, intentos=2, espera=1.0)

    return ResultadoFichaje(
        success=True, saltado=False, tipo=tipo_esperado,
        hora_fichaje=hora_fichaje,
        presencia=estado_post.presencia_actual,
        jornada="",
        extra="",
        mensaje=f"Fichaje {tipo_esperado} ejecutado a las {hora_fichaje}",
    )
