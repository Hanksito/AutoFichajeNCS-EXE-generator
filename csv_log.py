# -*- coding: utf-8 -*-
"""Registro CSV histórico de fichajes.

Una fila por día con entrada+salida. Escritura atómica.
"""
import csv
import os
from datetime import datetime
from pathlib import Path

import config


class FichajeCSVLogger:
    FIELDS = [
        "fecha",
        "hora_entrada",
        "hora_salida",
        "total_horas",
        "jornada",
        "extra_ausencia",
        "observaciones",
    ]

    def __init__(self, path: Path | None = None):
        self.path: Path = Path(path) if path else config.CSV_FICHAJES
        self._inicializar()

    # ──────────────────────────────────────────────────────
    # Lectura/escritura
    # ──────────────────────────────────────────────────────

    def _inicializar(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self.FIELDS).writeheader()

    def _leer(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _escribir_atomico(self, rows: list[dict]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, self.path)

    # ──────────────────────────────────────────────────────
    # API pública
    # ──────────────────────────────────────────────────────

    def obtener_registro_hoy(self) -> dict | None:
        hoy = datetime.now().strftime("%Y-%m-%d")
        for fila in reversed(self._leer()):
            if fila["fecha"] == hoy:
                return fila
        return None

    def registrar_entrada(self, hora: str, observaciones: str = "") -> None:
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = self._leer()
        idx_hoy = self._indice_hoy(rows, hoy)
        if idx_hoy is not None:
            rows[idx_hoy]["hora_entrada"] = hora
            if observaciones:
                rows[idx_hoy]["observaciones"] = self._merge_obs(
                    rows[idx_hoy].get("observaciones", ""),
                    f"ENTRADA: {observaciones}",
                )
        else:
            rows.append({
                "fecha": hoy,
                "hora_entrada": hora,
                "hora_salida": "",
                "total_horas": "",
                "jornada": "",
                "extra_ausencia": "",
                "observaciones": observaciones,
            })
        self._escribir_atomico(rows)

    def registrar_salida(
        self,
        hora: str,
        presencia: str = "",
        jornada: str = "",
        extra: str = "",
        observaciones: str = "",
    ) -> None:
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = self._leer()
        idx_hoy = self._indice_hoy(rows, hoy)
        if idx_hoy is not None:
            rows[idx_hoy]["hora_salida"] = hora
            rows[idx_hoy]["total_horas"] = presencia
            rows[idx_hoy]["jornada"] = jornada
            rows[idx_hoy]["extra_ausencia"] = extra
            if observaciones:
                rows[idx_hoy]["observaciones"] = self._merge_obs(
                    rows[idx_hoy].get("observaciones", ""),
                    f"SALIDA: {observaciones}",
                )
        else:
            aviso = "⚠️ Salida sin entrada previa"
            obs = f"{aviso} | {observaciones}".rstrip(" |")
            rows.append({
                "fecha": hoy,
                "hora_entrada": "",
                "hora_salida": hora,
                "total_horas": presencia,
                "jornada": jornada,
                "extra_ausencia": extra,
                "observaciones": obs,
            })
        self._escribir_atomico(rows)

    def resumen_mes(self, mes: int, año: int) -> list[dict]:
        prefijo = f"{año:04d}-{mes:02d}-"
        return [r for r in self._leer() if r["fecha"].startswith(prefijo)]

    # ──────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────

    @staticmethod
    def _indice_hoy(rows: list[dict], hoy: str) -> int | None:
        for i in range(len(rows) - 1, -1, -1):
            if rows[i]["fecha"] == hoy:
                return i
        return None

    @staticmethod
    def _merge_obs(existente: str, nueva: str) -> str:
        if not existente:
            return nueva
        return f"{existente} | {nueva}"
