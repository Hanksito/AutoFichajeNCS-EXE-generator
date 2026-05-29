# -*- coding: utf-8 -*-
"""Tests para csv_log.py."""
import csv
import importlib
from datetime import datetime
import pytest


def _reload_csv_log(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import csv_log
    return importlib.reload(csv_log)


def test_crea_archivo_con_cabeceras_si_no_existe(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    assert (tmp_path / "fichajes.csv").exists()
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        cabeceras = next(reader)
    assert cabeceras == [
        "fecha", "hora_entrada", "hora_salida",
        "total_horas", "jornada", "extra_ausencia", "observaciones",
    ]


def test_registrar_entrada_crea_fila(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_entrada("08:53:12", observaciones="Automático")
    hoy = datetime.now().strftime("%Y-%m-%d")
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["fecha"] == hoy
    assert rows[0]["hora_entrada"] == "08:53:12"
    assert rows[0]["hora_salida"] == ""
    assert "Automático" in rows[0]["observaciones"]


def test_registrar_salida_completa_fila_existente(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_entrada("08:53:12")
    logger.registrar_salida("18:18:45", "09:25", "08:00", "Extr. 01:25")
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1, "salida debe actualizar la fila de entrada, no crear otra"
    assert rows[0]["hora_entrada"] == "08:53:12"
    assert rows[0]["hora_salida"] == "18:18:45"
    assert rows[0]["total_horas"] == "09:25"
    assert rows[0]["jornada"] == "08:00"
    assert rows[0]["extra_ausencia"] == "Extr. 01:25"


def test_salida_sin_entrada_previa_crea_fila_con_aviso(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_salida("18:18:45", "09:25", "08:00", "")
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["hora_entrada"] == ""
    assert rows[0]["hora_salida"] == "18:18:45"
    assert "sin entrada previa" in rows[0]["observaciones"].lower()


def test_obtener_registro_hoy_devuelve_none_si_no_hay(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    assert logger.obtener_registro_hoy() is None


def test_resumen_mes_filtra_correctamente(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    csv_path = tmp_path / "fichajes.csv"
    # Inyectamos un CSV con entradas de varios meses
    csv_path.write_text(
        "fecha,hora_entrada,hora_salida,total_horas,jornada,extra_ausencia,observaciones\n"
        "2026-05-01,08:50:00,18:10:00,09:20,08:00,,Auto\n"
        "2026-05-02,08:51:00,18:11:00,09:20,08:00,,Auto\n"
        "2026-04-30,08:52:00,18:12:00,09:20,08:00,,Auto\n",
        encoding="utf-8",
    )
    logger = mod.FichajeCSVLogger()
    resumen = logger.resumen_mes(5, 2026)
    assert len(resumen) == 2
    assert all(r["fecha"].startswith("2026-05") for r in resumen)


def test_escritura_atomica_no_corrompe_si_falla_a_medias(tmp_path, monkeypatch):
    """Si la escritura falla, el archivo original sigue intacto."""
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_entrada("08:00:00")
    contenido_original = (tmp_path / "fichajes.csv").read_text(encoding="utf-8")

    # Forzamos un fallo simulando que os.replace falla
    def replace_falla(*args, **kwargs):
        raise OSError("simulado")
    monkeypatch.setattr("os.replace", replace_falla)

    # La operación falla pero el archivo original se mantiene
    with pytest.raises(OSError):
        logger.registrar_salida("18:00:00", "10:00", "08:00", "")
    contenido_tras_fallo = (tmp_path / "fichajes.csv").read_text(encoding="utf-8")
    assert contenido_tras_fallo == contenido_original
