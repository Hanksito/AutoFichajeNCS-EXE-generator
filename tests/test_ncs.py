# -*- coding: utf-8 -*-
"""Tests para ncs.py — verificación de estado y guardias de seguridad."""
import importlib
from unittest.mock import MagicMock, patch
import pytest
from selenium.common.exceptions import NoSuchElementException


def _reload_ncs(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import ncs
    return importlib.reload(ncs)


# ──────────────────────────────────────────────────────────
# Helpers de mock del driver
# ──────────────────────────────────────────────────────────

def _driver_con_alerta(clase_alerta: str | None, texto: str, presencia: str = "00:00"):
    """Crea un driver fake. clase_alerta = None → no aparece alerta."""
    driver = MagicMock()
    alerta_elem = MagicMock()
    alerta_elem.text = texto
    alerta_elem.is_displayed.return_value = True

    presencia_elem = MagicMock()
    presencia_elem.text = presencia

    def find_element(by, selector):
        s = str(selector)
        if "alert-success" in s and clase_alerta == "success":
            return alerta_elem
        if "alert-info" in s and clase_alerta == "info":
            return alerta_elem
        if "alert-danger" in s:
            raise NoSuchElementException("sin error")
        if "alert" in s:
            raise NoSuchElementException("alerta no presente")
        if "presencia" in s.lower() or s == "presencia":
            return presencia_elem
        elem = MagicMock(); elem.text = "00:00"
        return elem

    def find_element_by_id(id_):
        if id_ == "presencia":
            return presencia_elem
        elem = MagicMock(); elem.text = "00:00"
        return elem

    # Soportamos ambos APIs: find_element(by, sel) y por ID
    driver.find_element = MagicMock(side_effect=find_element)
    return driver


# ──────────────────────────────────────────────────────────
# Tests de leer_estado_seguro
# ──────────────────────────────────────────────────────────

def test_leer_estado_devuelve_entrada_si_alerta_info(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = _driver_con_alerta("info", "Estas fuera Marcas para ENTRAR", presencia="00:00")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "ENTRADA"
    assert estado.coherente is True


def test_leer_estado_devuelve_salida_si_alerta_success(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = _driver_con_alerta("success", "Estas dentro Marcas para SALIR", presencia="00:23")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "SALIDA"
    assert estado.coherente is True


def test_leer_estado_reintenta_si_desconocido(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = _driver_con_alerta(None, "")  # ninguna alerta
    estado = mod.leer_estado_seguro(driver, intentos=3, espera=0.0)
    assert estado.accion_siguiente == "DESCONOCIDO"
    # Debe haber intentado leer 3 veces
    # (find_element se llama al menos 2 veces por intento: success + info)
    assert driver.find_element.call_count >= 6


def test_estado_incoherente_si_alerta_entrada_pero_presencia_no_cero(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    # Alerta dice "ENTRAR" (fuera) pero presencia es 09:15 (estuviste dentro)
    driver = _driver_con_alerta("info", "Estas fuera Marcas para ENTRAR", presencia="09:15")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "ENTRADA"
    assert estado.coherente is False


def test_estado_incoherente_si_alerta_salida_pero_presencia_cero(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    # Alerta dice "SALIR" (dentro) pero presencia es 00:00 (acabas de entrar?)
    driver = _driver_con_alerta("success", "Estas dentro Marcas para SALIR", presencia="00:00")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "SALIDA"
    assert estado.coherente is False
