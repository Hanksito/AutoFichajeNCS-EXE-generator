# -*- coding: utf-8 -*-
"""Bucle diario del fichaje + estado persistente.

Contiene:
- EstadoDiario: dataclass con persistencia atómica y migración legacy.
- Scheduler: bucle infinito que decide cuándo fichar (Task 11 lo añadirá).
"""
import json
import os
import random
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import config


# ──────────────────────────────────────────────────────────
# EstadoDiario
# ──────────────────────────────────────────────────────────

@dataclass
class EstadoDiario:
    fecha: str
    hora_entrada: Optional[datetime] = None
    hora_salida: Optional[datetime] = None
    entrada_ts: Optional[datetime] = None
    salida_ts: Optional[datetime] = None
    reintentos_entrada: int = 0
    reintentos_salida: int = 0

    @classmethod
    def _vacio_hoy(cls) -> "EstadoDiario":
        return cls(fecha=date.today().isoformat())

    @classmethod
    def cargar(cls) -> "EstadoDiario":
        path: Path = config.ESTADO_FILE
        if not path.exists():
            return cls._vacio_hoy()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls._vacio_hoy()
        if raw.get("fecha") != date.today().isoformat():
            return cls._vacio_hoy()
        migrado = cls._migrar(raw)
        e = cls._desde_dict(migrado)
        if migrado != raw:
            e.guardar()
        return e

    @staticmethod
    def _migrar(raw: dict) -> dict:
        nuevo = {"fecha": raw.get("fecha")}
        nuevo["hora_entrada"] = raw.get("hora_entrada") or raw.get("hora_entrada_random")
        nuevo["hora_salida"] = raw.get("hora_salida") or raw.get("hora_salida_random")
        if "entrada_ts" in raw:
            nuevo["entrada_ts"] = raw["entrada_ts"]
        elif "entrada_realizada_ts" in raw:
            nuevo["entrada_ts"] = raw["entrada_realizada_ts"]
        elif raw.get("entrada_realizada") is True:
            nuevo["entrada_ts"] = datetime.now().isoformat()
        else:
            nuevo["entrada_ts"] = None
        if "salida_ts" in raw:
            nuevo["salida_ts"] = raw["salida_ts"]
        elif "salida_realizada_ts" in raw:
            nuevo["salida_ts"] = raw["salida_realizada_ts"]
        elif raw.get("salida_realizada") is True:
            nuevo["salida_ts"] = datetime.now().isoformat()
        else:
            nuevo["salida_ts"] = None
        nuevo["reintentos_entrada"] = raw.get("reintentos_entrada", 0)
        nuevo["reintentos_salida"] = raw.get("reintentos_salida", 0)
        return nuevo

    @classmethod
    def _desde_dict(cls, d: dict) -> "EstadoDiario":
        def _dt(v):
            return datetime.fromisoformat(v) if v else None
        return cls(
            fecha=d["fecha"],
            hora_entrada=_dt(d.get("hora_entrada")),
            hora_salida=_dt(d.get("hora_salida")),
            entrada_ts=_dt(d.get("entrada_ts")),
            salida_ts=_dt(d.get("salida_ts")),
            reintentos_entrada=d.get("reintentos_entrada", 0),
            reintentos_salida=d.get("reintentos_salida", 0),
        )

    def guardar(self) -> None:
        path: Path = config.ESTADO_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        d = {
            "fecha": self.fecha,
            "hora_entrada": self.hora_entrada.isoformat() if self.hora_entrada else None,
            "hora_salida": self.hora_salida.isoformat() if self.hora_salida else None,
            "entrada_ts": self.entrada_ts.isoformat() if self.entrada_ts else None,
            "salida_ts": self.salida_ts.isoformat() if self.salida_ts else None,
            "reintentos_entrada": self.reintentos_entrada,
            "reintentos_salida": self.reintentos_salida,
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)

    def marcar_entrada(self) -> None:
        self.entrada_ts = datetime.now()
        self.guardar()

    def marcar_salida(self) -> None:
        self.salida_ts = datetime.now()
        self.guardar()

    @property
    def entrada_realizada(self) -> bool:
        return self.entrada_ts is not None

    @property
    def salida_realizada(self) -> bool:
        return self.salida_ts is not None

    def es_dia_completado(self) -> bool:
        return self.entrada_realizada and self.salida_realizada
