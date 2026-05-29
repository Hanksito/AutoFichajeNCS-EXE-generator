# -*- coding: utf-8 -*-
"""Tests para notifier.py — solo lógica de composición de mensajes.

Los popups Tk en sí se verifican manualmente; aquí testamos que el
mensaje correcto se compone según el evento.
"""
import importlib
from unittest.mock import patch
import pytest


def _reload_notifier(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import notifier
    return importlib.reload(notifier)


def test_componer_mensaje_fallo_normal(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    titulo, msg = n._componer_fallo(
        tipo="ENTRADA",
        motivo="Login fallido",
        html_cambio=False,
    )
    assert "ENTRADA" in titulo or "ENTRADA" in msg
    assert "Login fallido" in msg
    assert "manualmente" in msg.lower() or "a mano" in msg.lower()
    # No debe mencionar cambio de HTML cuando html_cambio=False
    assert "html" not in msg.lower() and "cambi" not in msg.lower()


def test_componer_mensaje_fallo_html_cambio(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    titulo, msg = n._componer_fallo(
        tipo="SALIDA",
        motivo="No pude leer NCS",
        html_cambio=True,
    )
    assert "SALIDA" in titulo or "SALIDA" in msg
    assert "No pude leer NCS" in msg
    # Sí debe mencionar el cambio de HTML / avisar al desarrollador
    assert "desarrollador" in msg.lower() or "actualiza" in msg.lower() or "cambi" in msg.lower()


def test_componer_mensaje_doble_instancia(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    titulo, msg = n._componer_doble_instancia(pid_otro=12345)
    assert "12345" in msg
    assert "instancia" in msg.lower() or "arranc" in msg.lower()


def test_aviso_fallo_invoca_popup(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    with patch.object(n, "_mostrar_popup") as mock_show:
        n.aviso_fallo(tipo="ENTRADA", motivo="test", html_cambio=False)
        assert mock_show.called
        args, kwargs = mock_show.call_args
        # Debe pasar titulo y mensaje
        assert len(args) >= 2 or ("titulo" in kwargs and "mensaje" in kwargs)


def test_aviso_doble_instancia_invoca_popup(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    with patch.object(n, "_mostrar_popup") as mock_show:
        n.aviso_doble_instancia(pid_otro=999)
        assert mock_show.called
