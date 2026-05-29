# -*- coding: utf-8 -*-
"""Tests para ncs.py — verificación de estado y guardias de seguridad."""
import importlib
from unittest.mock import MagicMock, patch
import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException


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


# ──────────────────────────────────────────────────────────
# Tests de realizar_fichaje — LAS 3 GUARDIAS
# ──────────────────────────────────────────────────────────

def _driver_completo(alerta_clase, alerta_texto, presencia="00:00"):
    """Driver fake con botón btnTicar también accesible."""
    driver = _driver_con_alerta(alerta_clase, alerta_texto, presencia)
    boton = MagicMock(); boton.click = MagicMock(name="click_boton")
    driver._boton_fichaje = boton
    return driver, boton


def test_aborta_si_estado_desconocido_tras_reintentos(tmp_path, monkeypatch):
    """GUARDIA 1: nunca pulsar si no sabemos el estado."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo(None, "")  # ninguna alerta
    with patch.object(mod, "leer_estado_seguro",
                       return_value=mod.EstadoWeb("DESCONOCIDO", "", False)):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is False, "NO debe pulsar si estado es desconocido"
    assert res.success is False
    assert res.saltado is False
    assert res.html_cambio is True


def test_aborta_si_incoherencia_alerta_presencia(tmp_path, monkeypatch):
    """GUARDIA 2: nunca pulsar si alerta y presencia se contradicen."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("info", "ENTRAR", presencia="09:15")
    estado = mod.EstadoWeb("ENTRADA", "09:15", coherente=False)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is False
    assert res.success is False
    assert res.html_cambio is True


def test_skip_si_ya_dentro_y_tipo_entrada(tmp_path, monkeypatch):
    """GUARDIA 3: skip si ya estás dentro y tocaba ENTRADA."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("success", "SALIR", presencia="00:23")
    estado = mod.EstadoWeb("SALIDA", "00:23", coherente=True)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is False, "NO debe pulsar si ya estás dentro"
    assert res.success is True
    assert res.saltado is True


def test_skip_si_ya_fuera_y_tipo_salida(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("info", "ENTRAR", presencia="00:00")
    estado = mod.EstadoWeb("ENTRADA", "00:00", coherente=True)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="SALIDA")
    assert boton.click.called is False
    assert res.success is True
    assert res.saltado is True


def test_ficha_normal_si_estado_coherente_y_tocaba(tmp_path, monkeypatch):
    """Caso feliz: estado coherente, tocaba el fichaje esperado → click."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("info", "ENTRAR", presencia="00:00")
    estado = mod.EstadoWeb("ENTRADA", "00:00", coherente=True)
    estado_post = mod.EstadoWeb("SALIDA", "00:00", coherente=True)
    with patch.object(mod, "leer_estado_seguro", side_effect=[estado, estado_post]):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is True
    assert res.success is True
    assert res.saltado is False
    assert res.tipo == "ENTRADA"


def test_no_se_pulsa_boton_si_boton_no_se_encuentra(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, _ = _driver_completo("info", "ENTRAR", presencia="00:00")
    estado = mod.EstadoWeb("ENTRADA", "00:00", coherente=True)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=None):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert res.success is False
    assert res.html_cambio is True  # botón no encontrado = HTML cambió


# ──────────────────────────────────────────────────────────
# Tests de realizar_login
# ──────────────────────────────────────────────────────────

def test_login_devuelve_true_si_no_hay_modal(tmp_path, monkeypatch):
    """Si no aparece el modal, ya estamos logueados → success."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = MagicMock()
    with patch("ncs.WebDriverWait") as wait_mock:
        # Simular que detectar_modal_login no encuentra el modal
        wait_mock.return_value.until.side_effect = TimeoutException("no modal")
        ok = mod.realizar_login(driver, "u", "p")
    assert ok is True


def test_login_falla_si_credenciales_erroneas(tmp_path, monkeypatch):
    """Si tras pulsar Login aparece #messenger .failed visible → False."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = MagicMock()
    modal = MagicMock(); modal.is_displayed.return_value = True
    user_field = MagicMock(); pass_field = MagicMock(); boton_login = MagicMock()
    failed_msg = MagicMock(); failed_msg.is_displayed.return_value = True
    failed_msg.text = "Credenciales incorrectas"

    call_count = {"n": 0}

    def wait_until_side_effect(*args, **kwargs):
        # Simulamos: 1ª llamada (detectar modal) → modal,
        # 2ª (campo usuario), 3ª (campo password), 4ª (botón login)
        call_count["n"] += 1
        return [modal, user_field, pass_field, boton_login][min(call_count["n"]-1, 3)]

    def find_element_side_effect(by, selector):
        if "failed" in str(selector):
            return failed_msg
        raise NoSuchElementException()

    driver.find_element = MagicMock(side_effect=find_element_side_effect)

    with patch("ncs.WebDriverWait") as wait_mock:
        wait_mock.return_value.until.side_effect = wait_until_side_effect
        ok = mod.realizar_login(driver, "u", "p")
    assert ok is False


# ──────────────────────────────────────────────────────────
# Tests de crear_navegador (smoke — solo que devuelve algo)
# ──────────────────────────────────────────────────────────

def test_crear_navegador_devuelve_none_si_falla(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    with patch("ncs.ChromeDriverManager") as cdm:
        cdm.return_value.install.side_effect = Exception("simulado")
        driver = mod.crear_navegador()
    assert driver is None
