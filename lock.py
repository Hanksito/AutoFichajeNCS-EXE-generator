# -*- coding: utf-8 -*-
"""Lock file con verificación de PID vivo.

Evita doble instancia, pero detecta locks huérfanos (proceso muerto
o más antiguos de 24h) para no bloquearse tras un crash.
"""
import atexit
import os
from datetime import datetime, timedelta
from pathlib import Path

import psutil

import config


class LockBusy(Exception):
    """Hay otra instancia VIVA del proceso ejecutándose."""

    def __init__(self, pid_otro: int):
        self.pid_otro = pid_otro
        super().__init__(f"Otra instancia viva ya tiene el lock (PID={pid_otro})")


def _pid_vivo(pid: int) -> bool:
    """True si un proceso con ese PID existe en el sistema."""
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False


def _parse_contenido(contenido: str) -> tuple[int, datetime | None]:
    """Extrae (pid, iniciado) de un lock file. PID=-1 si no se puede parsear."""
    pid = -1
    iniciado: datetime | None = None
    for parte in contenido.split():
        if parte.startswith("PID="):
            try:
                pid = int(parte.split("=", 1)[1])
            except ValueError:
                pid = -1
        elif parte.startswith("iniciado="):
            try:
                iniciado = datetime.fromisoformat(parte.split("=", 1)[1])
            except ValueError:
                iniciado = None
    return pid, iniciado


def _es_huerfano(contenido: str) -> tuple[bool, int]:
    """Devuelve (es_huérfano, pid). Es huérfano si:
    - archivo corrupto (no parseable)
    - PID no vive en el sistema
    - iniciado hace más de 24 horas
    """
    pid, iniciado = _parse_contenido(contenido)
    if pid < 0:
        return True, pid
    if not _pid_vivo(pid):
        return True, pid
    if iniciado and (datetime.now() - iniciado) > timedelta(hours=24):
        return True, pid
    return False, pid


def adquirir() -> None:
    """Crea LOCK_FILE con el PID actual.

    Raises:
        LockBusy: si ya hay un lock con un PID vivo y reciente.
    """
    lock_path: Path = config.LOCK_FILE
    if lock_path.exists():
        contenido = lock_path.read_text(encoding="utf-8").strip()
        es_huerfano, pid_existente = _es_huerfano(contenido)
        if not es_huerfano:
            raise LockBusy(pid_existente)
        # Huérfano → sobrescribimos sin error
    pid_actual = os.getpid()
    nuevo = f"PID={pid_actual} iniciado={datetime.now().isoformat()}"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(nuevo, encoding="utf-8")
    atexit.register(liberar)


def liberar() -> None:
    """Borra LOCK_FILE si existe. Idempotente."""
    try:
        config.LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
