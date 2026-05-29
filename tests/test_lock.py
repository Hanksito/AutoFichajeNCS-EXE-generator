# -*- coding: utf-8 -*-
"""Tests para lock.py — single-instance con verificación de PID."""
import os
import importlib
from datetime import datetime, timedelta
import pytest


def _reload_lock(tmp_path, monkeypatch):
    """Recarga config y lock apuntando LOCK_FILE a tmp_path."""
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import lock
    return importlib.reload(lock)


def test_lock_se_adquiere_si_no_existe(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    lk.adquirir()
    assert (tmp_path / "auto_fichaje.lock").exists()
    contenido = (tmp_path / "auto_fichaje.lock").read_text(encoding="utf-8")
    assert f"PID={os.getpid()}" in contenido
    lk.liberar()
    assert not (tmp_path / "auto_fichaje.lock").exists()


def test_lock_rechaza_si_pid_vivo(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    # Usamos nuestro propio PID (que sí está vivo) como "lock existente"
    (tmp_path / "auto_fichaje.lock").write_text(
        f"PID={os.getpid()} iniciado={datetime.now().isoformat()}",
        encoding="utf-8",
    )
    with pytest.raises(lk.LockBusy) as exc_info:
        lk.adquirir()
    assert exc_info.value.pid_otro == os.getpid()


def test_lock_sobrescribe_si_pid_muerto(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    # PID 999999 muy improbable que exista
    (tmp_path / "auto_fichaje.lock").write_text(
        f"PID=999999 iniciado={datetime.now().isoformat()}",
        encoding="utf-8",
    )
    lk.adquirir()  # no debe lanzar
    contenido = (tmp_path / "auto_fichaje.lock").read_text(encoding="utf-8")
    assert f"PID={os.getpid()}" in contenido
    lk.liberar()


def test_lock_sobrescribe_si_mas_de_24h(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    hace_25h = (datetime.now() - timedelta(hours=25)).isoformat()
    # Usamos MI propio PID (vivo) pero hace 25h
    (tmp_path / "auto_fichaje.lock").write_text(
        f"PID={os.getpid()} iniciado={hace_25h}",
        encoding="utf-8",
    )
    lk.adquirir()  # debe considerar huérfano por antigüedad
    contenido = (tmp_path / "auto_fichaje.lock").read_text(encoding="utf-8")
    # El timestamp debe ser nuevo
    assert hace_25h not in contenido
    lk.liberar()


def test_lock_sobrescribe_si_archivo_corrupto(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    (tmp_path / "auto_fichaje.lock").write_text("contenido basura", encoding="utf-8")
    lk.adquirir()  # no debe lanzar
    lk.liberar()


def test_liberar_es_idempotente(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    lk.liberar()  # archivo no existe, no debe lanzar
    lk.adquirir()
    lk.liberar()
    lk.liberar()  # tampoco debe lanzar
