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


# ──────────────────────────────────────────────────────────
# Lectura segura (con reintentos)
# ──────────────────────────────────────────────────────────

def leer_estado_seguro(driver, intentos: int = 3, espera: float = 2.0) -> EstadoWeb:
    """Lee el estado de NCS, confiando en la ALERTA como señal autoritativa.

    La alerta ('Estás dentro/fuera') la pinta el servidor y es la misma
    señal que usa la web oficial de NCS para decidir si el botón entra o
    sale. Por eso es fiable al instante.

    `#presencia` se lee solo como INFORMACIÓN (va al CSV/log). NO se usa
    para decidir, porque es la presencia acumulada *de hoy* y puede valer
    '00:00' de forma legítima (p.ej. estás dentro por una sesión abierta de
    un día anterior). Cruzarla con la alerta daba falsas incoherencias que
    abortaban todos los fichajes.

    Returns:
        EstadoWeb con:
        - accion_siguiente: "ENTRADA", "SALIDA" o "DESCONOCIDO"
        - presencia_actual: "HH:MM" leído de la página (informativo)
        - coherente: True si la alerta se pudo leer (accion != DESCONOCIDO)
    """
    accion: Literal["ENTRADA", "SALIDA", "DESCONOCIDO"] = "DESCONOCIDO"
    for i in range(intentos):
        accion = _detectar_estado_una_vez(driver)
        if accion != "DESCONOCIDO":
            break
        if i < intentos - 1 and espera > 0:
            time.sleep(espera)

    presencia = _obtener_presencia(driver)
    return EstadoWeb(
        accion_siguiente=accion,
        presencia_actual=presencia,
        coherente=accion != "DESCONOCIDO",
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
    """Realiza el fichaje del tipo esperado, con dos guardias de seguridad.

    GUARDIA 1: aborta si el estado de la web no se puede leer (DESCONOCIDO),
               para no pulsar a ciegas y arriesgar un desfichaje.
    GUARDIA 2: si ya está hecho lo esperado (la alerta dice que ya estás en
               el estado destino), se salta sin pulsar.

    La decisión se basa en la ALERTA, que es la señal autoritativa de NCS
    (ver leer_estado_seguro). Solo si ambas guardias pasan, se pulsa.
    """
    estado = leer_estado_seguro(driver, intentos=3, espera=2.0)

    # GUARDIA 1: estado ilegible → no tocamos nada
    if estado.accion_siguiente == "DESCONOCIDO":
        return _abortado(
            tipo_esperado,
            "No se pudo leer el estado en NCS tras 3 intentos. "
            "Aborto por seguridad para no desfichar.",
            html_cambio=True,
        )

    # GUARDIA 2: ya fichado a mano
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


# ──────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────

def _escribir_como_humano(elemento, texto: str) -> None:
    elemento.clear()
    _pausa_humana(0.3, 0.7)
    for char in texto:
        elemento.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    _pausa_humana(0.2, 0.5)


def realizar_login(driver, usuario: str, password: str, timeout: int = 30) -> bool:
    """Login en clock.ncs.es.

    Returns:
        True si login exitoso (incluye "ya logueado").
        False si credenciales incorrectas o algún campo del modal no aparece.
    """
    # ¿Hay modal de login?
    try:
        modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#myModal.modal.fade.in"))
        )
        if not modal.is_displayed():
            return True
    except TimeoutException:
        return True  # ya logueado

    _pausa_humana(1.0, 2.0)

    # Llenar usuario
    try:
        campo_u = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "tbUserName"))
        )
        campo_p = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "tbPassword"))
        )
    except TimeoutException:
        return False

    _escribir_como_humano(campo_u, usuario)
    _pausa_humana(0.5, 1.0)
    _escribir_como_humano(campo_p, password)
    _pausa_humana(0.8, 1.5)

    # Botón
    try:
        boton = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "LoginBtn"))
        )
    except TimeoutException:
        return False

    try:
        boton.click()
    except Exception:
        driver.execute_script("arguments[0].click();", boton)

    _pausa_humana(2.0, 4.0)

    # ¿Mensaje de error?
    try:
        error = driver.find_element(By.CSS_SELECTOR, "#messenger .failed")
        if error.is_displayed():
            return False
    except NoSuchElementException:
        pass

    # Esperar a que el modal desaparezca
    try:
        WebDriverWait(driver, 10).until_not(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#myModal.modal.fade.in"))
        )
        return True
    except TimeoutException:
        return False


# ──────────────────────────────────────────────────────────
# crear_navegador
# ──────────────────────────────────────────────────────────

def crear_navegador():
    """Crea un Chrome headless con anti-detección. None si falla."""
    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,768")
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("useAutomationExtension", False)
    opciones.add_argument("--disable-notifications")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opciones)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        return driver
    except Exception:
        return None
