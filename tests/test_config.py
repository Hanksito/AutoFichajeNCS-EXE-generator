# -*- coding: utf-8 -*-
"""Tests para config.py — resolución de paths."""
import os
import sys
import importlib
from pathlib import Path
import pytest


def _reload_config():
    """Recarga config para que vea cambios en el entorno."""
    import config
    return importlib.reload(config)


def test_data_dir_usa_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    cfg = _reload_config()
    assert cfg.DATA_DIR == tmp_path


def test_data_dir_crea_directorio_si_no_existe(tmp_path, monkeypatch):
    nuevo = tmp_path / "subdir"
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(nuevo))
    cfg = _reload_config()
    assert nuevo.exists()
    assert cfg.DATA_DIR == nuevo


def test_data_dir_default_es_carpeta_del_script(monkeypatch):
    monkeypatch.delenv("AUTO_FICHAJE_DATA_DIR", raising=False)
    # sys.frozen no está set en modo desarrollo
    cfg = _reload_config()
    assert cfg.DATA_DIR == Path(cfg.__file__).parent


def test_data_dir_usa_carpeta_del_exe_si_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "AutoFichajeNCS.exe"
    fake_exe.touch()
    monkeypatch.delenv("AUTO_FICHAJE_DATA_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    cfg = _reload_config()
    assert cfg.DATA_DIR == tmp_path


def test_constantes_de_ventanas_presentes(monkeypatch):
    monkeypatch.delenv("AUTO_FICHAJE_DATA_DIR", raising=False)
    cfg = _reload_config()
    assert cfg.ENTRADA_DESDE == "08:35"
    assert cfg.ENTRADA_HASTA == "09:05"
    assert cfg.SALIDA_DESDE == "18:00"
    assert cfg.SALIDA_HASTA == "18:30"
    assert cfg.DIAS_LABORABLES == [0, 1, 2, 3, 4]
    assert cfg.MAX_REINTENTOS == 3
    assert cfg.BACKOFF_REINTENTOS == [300, 600, 900]
    assert cfg.MARGEN_VENTANA_EXTRA == 30


def test_paths_calculados_relativos_a_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    cfg = _reload_config()
    assert cfg.CSV_FICHAJES == tmp_path / "fichajes.csv"
    assert cfg.ESTADO_FILE == tmp_path / "estado_diario.json"
    assert cfg.LOCK_FILE == tmp_path / "auto_fichaje.lock"
    assert cfg.LOG_FILE == tmp_path / "auto_fichaje.log"
