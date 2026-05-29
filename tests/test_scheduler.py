# -*- coding: utf-8 -*-
"""Tests para Scheduler — decisión de cuándo fichar (sin bucle infinito)."""
import importlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest


def _reload(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import scheduler
    return importlib.reload(scheduler)


def test_no_actua_en_fin_de_semana(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    with patch.object(mod, "_es_laborable", return_value=False):
        assert sched._toca_entrada(datetime(2026, 5, 30, 9, 0)) is False
        assert sched._toca_salida(datetime(2026, 5, 30, 18, 0)) is False


def test_calcula_horarios_solo_una_vez(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    msgs = []
    sched = mod.Scheduler(usuario="u", password="p", on_log=msgs.append)
    sched._calcular_horarios_si_faltan()
    h1_entrada = sched._estado.hora_entrada
    h1_salida = sched._estado.hora_salida
    assert h1_entrada is not None and h1_salida is not None
    sched._calcular_horarios_si_faltan()
    assert sched._estado.hora_entrada == h1_entrada
    assert sched._estado.hora_salida == h1_salida


def test_toca_entrada_dentro_de_ventana(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    with patch.object(mod, "_es_laborable", return_value=True):
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 49)) is False
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 50)) is True
        assert sched._toca_entrada(datetime(2026, 5, 29, 9, 25)) is True
        assert sched._toca_entrada(datetime(2026, 5, 29, 10, 30)) is False


def test_no_toca_si_ya_realizado(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    sched._estado.entrada_ts = datetime(2026, 5, 29, 8, 51)
    with patch.object(mod, "_es_laborable", return_value=True):
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 55)) is False


def test_no_toca_si_max_reintentos(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    import config
    sched._estado.reintentos_entrada = config.MAX_REINTENTOS
    with patch.object(mod, "_es_laborable", return_value=True):
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 55)) is False


def test_dispara_notifier_al_llegar_a_max_reintentos(tmp_path, monkeypatch):
    """Tras el 3er fallo, debe llamar notifier.aviso_fallo."""
    mod = _reload(tmp_path, monkeypatch)
    msgs = []
    sched = mod.Scheduler(usuario="u", password="p", on_log=msgs.append)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)

    import ncs
    import config
    resultado_fallido = ncs.ResultadoFichaje(
        success=False, saltado=False, tipo="ENTRADA",
        hora_fichaje="", presencia="", jornada="", extra="",
        mensaje="login fallido", html_cambio=False,
    )

    with patch.object(mod, "_realizar_fichaje_completo", return_value=resultado_fallido):
        with patch("notifier.aviso_fallo") as notif_mock:
            with patch("time.sleep"):  # no quiero esperar el backoff de verdad
                for i in range(config.MAX_REINTENTOS):
                    sched._intentar_fichaje("ENTRADA")
            assert notif_mock.called


def test_no_dispara_notifier_si_solo_un_fallo(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    import ncs
    res = ncs.ResultadoFichaje(False, False, "ENTRADA", "", "", "", "", "login fallido", False)
    with patch.object(mod, "_realizar_fichaje_completo", return_value=res):
        with patch("notifier.aviso_fallo") as notif_mock:
            with patch("time.sleep"):
                sched._intentar_fichaje("ENTRADA")
            assert notif_mock.called is False
