# -*- coding: utf-8 -*-
"""Tests para EstadoDiario en scheduler.py (persistencia + migración)."""
import importlib
import json
from datetime import datetime, date, timedelta
import pytest


def _reload(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import scheduler
    return importlib.reload(scheduler)


def _hoy() -> str:
    return date.today().isoformat()


def test_cargar_devuelve_vacio_si_archivo_no_existe(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    e = mod.EstadoDiario.cargar()
    assert e.fecha == _hoy()
    assert e.hora_entrada is None
    assert e.hora_salida is None
    assert e.entrada_ts is None
    assert e.salida_ts is None
    assert e.reintentos_entrada == 0
    assert e.reintentos_salida == 0


def test_cargar_resetea_si_fecha_distinta(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    (tmp_path / "estado_diario.json").write_text(json.dumps({
        "fecha": "2000-01-01",
        "hora_entrada": "2000-01-01T08:50:00",
        "hora_salida": None,
        "entrada_ts": "2000-01-01T08:50:00",
        "salida_ts": None,
        "reintentos_entrada": 2,
        "reintentos_salida": 0,
    }), encoding="utf-8")
    e = mod.EstadoDiario.cargar()
    assert e.fecha == _hoy()
    assert e.hora_entrada is None
    assert e.reintentos_entrada == 0


def test_guardar_y_recargar_preserva_horas(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    hora = datetime(2026, 5, 29, 8, 53, 12)
    e = mod.EstadoDiario.cargar()
    e.hora_entrada = hora
    e.guardar()
    e2 = mod.EstadoDiario.cargar()
    assert e2.hora_entrada == hora


def test_marcar_entrada_persiste_timestamp(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    e = mod.EstadoDiario.cargar()
    e.marcar_entrada()
    e2 = mod.EstadoDiario.cargar()
    assert e2.entrada_ts is not None
    assert (datetime.now() - e2.entrada_ts).total_seconds() < 5


def test_migracion_esquema_legacy_cli(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    legacy = {
        "fecha": _hoy(),
        "hora_entrada_random": f"{_hoy()}T08:43:42",
        "hora_salida_random": f"{_hoy()}T18:21:13",
        "entrada_realizada_ts": f"{_hoy()}T08:44:07.063918",
        "salida_realizada_ts": None,
        "reintentos_entrada": 0,
        "reintentos_salida": 0,
    }
    (tmp_path / "estado_diario.json").write_text(json.dumps(legacy), encoding="utf-8")
    e = mod.EstadoDiario.cargar()
    assert e.hora_entrada == datetime.fromisoformat(legacy["hora_entrada_random"])
    assert e.hora_salida == datetime.fromisoformat(legacy["hora_salida_random"])
    assert e.entrada_ts == datetime.fromisoformat(legacy["entrada_realizada_ts"])
    assert e.salida_ts is None
    en_disco = json.loads((tmp_path / "estado_diario.json").read_text(encoding="utf-8"))
    assert "hora_entrada" in en_disco
    assert "hora_entrada_random" not in en_disco


def test_migracion_esquema_legacy_gui_bool_a_timestamp(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    legacy = {
        "fecha": _hoy(),
        "hora_entrada": f"{_hoy()}T08:50:00",
        "hora_salida": None,
        "entrada_realizada": True,
        "salida_realizada": False,
        "reintentos_entrada": 1,
        "reintentos_salida": 0,
    }
    (tmp_path / "estado_diario.json").write_text(json.dumps(legacy), encoding="utf-8")
    e = mod.EstadoDiario.cargar()
    assert e.entrada_ts is not None
    assert e.salida_ts is None
    assert e.reintentos_entrada == 1
