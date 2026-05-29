# -*- coding: utf-8 -*-
"""Tests para credenciales.py."""
import importlib
import json
import pytest


def _reload(tmp_path, monkeypatch):
    """Apunta el config_dir a tmp_path para no tocar AppData real."""
    import credenciales
    importlib.reload(credenciales)
    # Forzamos el directorio a tmp_path
    return credenciales


def test_carga_devuelve_none_si_no_existe(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    u, p = mgr.cargar()
    assert u is None
    assert p is None


def test_guardar_y_cargar_round_trip(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.guardar("alberto", "mi_pass_123")
    u, p = mgr.cargar()
    assert u == "alberto"
    assert p == "mi_pass_123"


def test_guardar_crea_archivo_con_b64(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.guardar("user", "pass")
    config_file = tmp_path / "config.dat"
    assert config_file.exists()
    contenido = json.loads(config_file.read_text(encoding="utf-8"))
    # Texto plano NO debe aparecer
    assert "user" not in config_file.read_text()
    assert "pass" not in config_file.read_text()
    assert "u" in contenido
    assert "p" in contenido


def test_cargar_devuelve_none_si_archivo_corrupto(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    (tmp_path / "config.dat").write_text("basura no json", encoding="utf-8")
    u, p = mgr.cargar()
    assert u is None
    assert p is None


def test_eliminar_borra_el_archivo(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.guardar("u", "p")
    assert (tmp_path / "config.dat").exists()
    mgr.eliminar()
    assert not (tmp_path / "config.dat").exists()


def test_eliminar_es_idempotente(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.eliminar()  # archivo no existe, no debe lanzar
    mgr.eliminar()
