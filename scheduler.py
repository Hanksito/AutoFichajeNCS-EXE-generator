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
    salida_almuerzo_ts: Optional[datetime] = None
    entrada_almuerzo_ts: Optional[datetime] = None
    reintentos_salida_almuerzo: int = 0
    reintentos_entrada_almuerzo: int = 0

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
        nuevo["salida_almuerzo_ts"] = raw.get("salida_almuerzo_ts")
        nuevo["entrada_almuerzo_ts"] = raw.get("entrada_almuerzo_ts")
        nuevo["reintentos_salida_almuerzo"] = raw.get("reintentos_salida_almuerzo", 0)
        nuevo["reintentos_entrada_almuerzo"] = raw.get("reintentos_entrada_almuerzo", 0)
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
            salida_almuerzo_ts=_dt(d.get("salida_almuerzo_ts")),
            entrada_almuerzo_ts=_dt(d.get("entrada_almuerzo_ts")),
            reintentos_salida_almuerzo=d.get("reintentos_salida_almuerzo", 0),
            reintentos_entrada_almuerzo=d.get("reintentos_entrada_almuerzo", 0),
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
            "salida_almuerzo_ts": self.salida_almuerzo_ts.isoformat() if self.salida_almuerzo_ts else None,
            "entrada_almuerzo_ts": self.entrada_almuerzo_ts.isoformat() if self.entrada_almuerzo_ts else None,
            "reintentos_salida_almuerzo": self.reintentos_salida_almuerzo,
            "reintentos_entrada_almuerzo": self.reintentos_entrada_almuerzo,
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

    def marcar_salida_almuerzo(self) -> None:
        self.salida_almuerzo_ts = datetime.now()
        self.guardar()

    def marcar_entrada_almuerzo(self) -> None:
        self.entrada_almuerzo_ts = datetime.now()
        self.guardar()

    @property
    def entrada_realizada(self) -> bool:
        return self.entrada_ts is not None

    @property
    def salida_realizada(self) -> bool:
        return self.salida_ts is not None

    @property
    def salida_almuerzo_realizada(self) -> bool:
        return self.salida_almuerzo_ts is not None

    @property
    def entrada_almuerzo_realizada(self) -> bool:
        return self.entrada_almuerzo_ts is not None

    def es_dia_completado(self) -> bool:
        return self.entrada_realizada and self.salida_realizada


# ──────────────────────────────────────────────────────────
# Helpers de tiempo
# ──────────────────────────────────────────────────────────

def _es_laborable() -> bool:
    return datetime.now().weekday() in config.DIAS_LABORABLES


def _nombre_dia() -> str:
    return ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][
        datetime.now().weekday()
    ]


def _hora_str_a_dt(hora_str: str, base: Optional[datetime] = None) -> datetime:
    base = base or datetime.now()
    h, m = map(int, hora_str.split(":"))
    return base.replace(hour=h, minute=m, second=0, microsecond=0)


def _hora_aleatoria(desde: str, hasta: str) -> datetime:
    dt1 = _hora_str_a_dt(desde)
    dt2 = _hora_str_a_dt(hasta)
    diff = int((dt2 - dt1).total_seconds())
    offset = random.randint(0, max(0, diff))
    return dt1 + timedelta(seconds=offset)


def _dentro_de_ventana_ampliada(ahora: datetime, hasta_str: str) -> bool:
    # El límite se calcula sobre el MISMO día que `ahora`, no sobre now(),
    # para no mezclar fechas (robusto si el proceso cruza medianoche y testeable).
    limite = _hora_str_a_dt(hasta_str, base=ahora) + timedelta(minutes=config.MARGEN_VENTANA_EXTRA)
    return ahora <= limite


# ──────────────────────────────────────────────────────────
# Fichaje completo (orchestrates login + ncs.realizar_fichaje + csv)
# ──────────────────────────────────────────────────────────

_NCS_TIPO = {
    "ENTRADA":          "ENTRADA",
    "SALIDA":           "SALIDA",
    "SALIDA_ALMUERZO":  "SALIDA",
    "ENTRADA_ALMUERZO": "ENTRADA",
}


def _realizar_fichaje_completo(usuario: str, password: str, tipo: str,
                                  on_log: Callable[[str], None]):
    """Login + fichaje + cierre del navegador. Devuelve ncs.ResultadoFichaje."""
    import ncs
    tipo_ncs = _NCS_TIPO.get(tipo, tipo)
    on_log(f"Abriendo navegador para {tipo}...")
    driver = ncs.crear_navegador(on_log=on_log)
    if driver is None:
        return ncs.ResultadoFichaje(
            success=False, saltado=False, tipo=tipo_ncs,
            hora_fichaje="", presencia="", jornada="", extra="",
            mensaje="No se pudo abrir Chrome (causa real arriba en el log; "
                    "revisa que Chrome esté instalado y haya internet)",
            html_cambio=False,
        )
    try:
        driver.get(config.URL_FICHAJE)
        on_log("Login en NCS...")
        ok = ncs.realizar_login(driver, usuario, password)
        if not ok:
            return ncs.ResultadoFichaje(
                success=False, saltado=False, tipo=tipo_ncs,
                hora_fichaje="", presencia="", jornada="", extra="",
                mensaje="Login fallido (credenciales o web caída)",
                html_cambio=False,
            )
        on_log(f"Verificando estado para {tipo}...")
        return ncs.realizar_fichaje(driver, tipo_esperado=tipo_ncs)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────────────────

class Scheduler:
    def __init__(
        self,
        usuario: str,
        password: str,
        on_log: Callable[[str], None],
        on_estado_cambia: Optional[Callable[[], None]] = None,
    ):
        self.usuario = usuario
        self.password = password
        self._on_log = on_log
        self._on_estado_cambia = on_estado_cambia or (lambda: None)
        self._estado = EstadoDiario.cargar()
        self._running = True

    def _calcular_horarios_si_faltan(self) -> None:
        if self._estado.hora_entrada is None:
            self._estado.hora_entrada = _hora_aleatoria(
                config.ENTRADA_DESDE, config.ENTRADA_HASTA
            )
        if self._estado.hora_salida is None:
            self._estado.hora_salida = _hora_aleatoria(
                config.SALIDA_DESDE, config.SALIDA_HASTA
            )
        self._estado.guardar()

    def _toca_entrada(self, ahora: datetime) -> bool:
        if not _es_laborable():
            return False
        e = self._estado
        if e.entrada_realizada:
            return False
        if e.hora_entrada is None:
            return False
        if ahora < e.hora_entrada:
            return False
        if not _dentro_de_ventana_ampliada(ahora, config.ENTRADA_HASTA):
            return False
        if e.reintentos_entrada >= config.MAX_REINTENTOS:
            return False
        return True

    def _toca_salida(self, ahora: datetime) -> bool:
        if not _es_laborable():
            return False
        e = self._estado
        if e.salida_realizada:
            return False
        if e.hora_salida is None:
            return False
        if ahora < e.hora_salida:
            return False
        if not _dentro_de_ventana_ampliada(ahora, config.SALIDA_HASTA):
            return False
        if e.reintentos_salida >= config.MAX_REINTENTOS:
            return False
        return True

    def _toca_salida_almuerzo(self, ahora: datetime) -> bool:
        if not _es_laborable():
            return False
        e = self._estado
        if e.salida_almuerzo_realizada:
            return False
        if ahora < _hora_str_a_dt(config.SALIDA_ALMUERZO, base=ahora):
            return False
        if not _dentro_de_ventana_ampliada(ahora, config.SALIDA_ALMUERZO):
            return False
        if e.reintentos_salida_almuerzo >= config.MAX_REINTENTOS:
            return False
        return True

    def _toca_entrada_almuerzo(self, ahora: datetime) -> bool:
        if not _es_laborable():
            return False
        e = self._estado
        if e.entrada_almuerzo_realizada:
            return False
        if ahora < _hora_str_a_dt(config.ENTRADA_ALMUERZO, base=ahora):
            return False
        if not _dentro_de_ventana_ampliada(ahora, config.ENTRADA_ALMUERZO):
            return False
        if e.reintentos_entrada_almuerzo >= config.MAX_REINTENTOS:
            return False
        return True

    def _intentar_fichaje(self, tipo: str) -> None:
        """Realiza un intento, gestiona reintentos y notificación."""
        import notifier
        import csv_log
        import time as _time

        if tipo == "ENTRADA":
            reintentos_actuales = self._estado.reintentos_entrada
        elif tipo == "SALIDA":
            reintentos_actuales = self._estado.reintentos_salida
        elif tipo == "SALIDA_ALMUERZO":
            reintentos_actuales = self._estado.reintentos_salida_almuerzo
        else:  # ENTRADA_ALMUERZO
            reintentos_actuales = self._estado.reintentos_entrada_almuerzo

        if reintentos_actuales > 0:
            espera = config.BACKOFF_REINTENTOS[
                min(reintentos_actuales - 1, len(config.BACKOFF_REINTENTOS) - 1)
            ]
            self._on_log(f"Reintento #{reintentos_actuales} {tipo}. Esperando {espera//60}min...")
            _time.sleep(espera)

        self._on_log(f"Intentando fichaje {tipo} (intento {reintentos_actuales + 1}/{config.MAX_REINTENTOS})")
        resultado = _realizar_fichaje_completo(
            self.usuario, self.password, tipo, self._on_log
        )

        logger = csv_log.FichajeCSVLogger()

        if resultado.saltado:
            self._on_log(f"⏭️  {tipo} omitida: {resultado.mensaje}")
            if tipo == "ENTRADA":
                self._estado.marcar_entrada()
            elif tipo == "SALIDA":
                self._estado.marcar_salida()
            elif tipo == "SALIDA_ALMUERZO":
                self._estado.marcar_salida_almuerzo()
            else:
                self._estado.marcar_entrada_almuerzo()
            self._on_estado_cambia()
            return

        if resultado.success:
            self._on_log(f"✅ {tipo} fichada a las {resultado.hora_fichaje}")
            if tipo == "ENTRADA":
                logger.registrar_entrada(resultado.hora_fichaje, observaciones="Automático")
                self._estado.marcar_entrada()
            elif tipo == "SALIDA":
                logger.registrar_salida(
                    resultado.hora_fichaje,
                    presencia=resultado.presencia,
                    jornada=resultado.jornada,
                    extra=resultado.extra,
                    observaciones="Automático",
                )
                self._estado.marcar_salida()
            elif tipo == "SALIDA_ALMUERZO":
                logger.registrar_salida(
                    resultado.hora_fichaje,
                    presencia=resultado.presencia,
                    jornada=resultado.jornada,
                    extra=resultado.extra,
                    observaciones="Almuerzo - Automático",
                )
                self._estado.marcar_salida_almuerzo()
            else:  # ENTRADA_ALMUERZO
                logger.registrar_entrada(resultado.hora_fichaje, observaciones="Almuerzo - Automático")
                self._estado.marcar_entrada_almuerzo()
            self._on_estado_cambia()
            return

        # Fallo
        self._on_log(f"❌ {tipo} fallido: {resultado.mensaje}")
        if tipo == "ENTRADA":
            self._estado.reintentos_entrada += 1
        elif tipo == "SALIDA":
            self._estado.reintentos_salida += 1
        elif tipo == "SALIDA_ALMUERZO":
            self._estado.reintentos_salida_almuerzo += 1
        else:
            self._estado.reintentos_entrada_almuerzo += 1
        self._estado.guardar()
        if tipo in ("ENTRADA", "ENTRADA_ALMUERZO"):
            logger.registrar_entrada(
                "", observaciones=f"ERROR intento {reintentos_actuales + 1}: {resultado.mensaje}"
            )
        else:
            logger.registrar_salida(
                "", "", "", "",
                observaciones=f"ERROR intento {reintentos_actuales + 1}: {resultado.mensaje}",
            )

        if tipo == "ENTRADA":
            reintentos_finales = self._estado.reintentos_entrada
        elif tipo == "SALIDA":
            reintentos_finales = self._estado.reintentos_salida
        elif tipo == "SALIDA_ALMUERZO":
            reintentos_finales = self._estado.reintentos_salida_almuerzo
        else:
            reintentos_finales = self._estado.reintentos_entrada_almuerzo

        if reintentos_finales >= config.MAX_REINTENTOS:
            self._on_log(f"💥 Reintentos agotados para {tipo}. Avisando al usuario.")
            notifier.aviso_fallo(tipo, resultado.mensaje, html_cambio=resultado.html_cambio)
        self._on_estado_cambia()

    def ejecutar(self) -> None:
        import time as _time
        ultimo_dia = None
        while self._running:
            ahora = datetime.now()
            hoy = ahora.date()
            if hoy != ultimo_dia:
                ultimo_dia = hoy
                self._estado = EstadoDiario.cargar()
                self._on_log(f"📅 Nuevo día: {_nombre_dia()} {ahora.strftime('%d/%m/%Y')}")
                if _es_laborable():
                    self._calcular_horarios_si_faltan()
                    self._on_log(
                        f"⏰ Hoy → Entrada: {self._estado.hora_entrada.strftime('%H:%M:%S')} "
                        f"| Almuerzo: {config.SALIDA_ALMUERZO}-{config.ENTRADA_ALMUERZO} "
                        f"| Salida: {self._estado.hora_salida.strftime('%H:%M:%S')}"
                    )
                else:
                    self._on_log(f"🏖️ {_nombre_dia()} no laborable")
                self._on_estado_cambia()

            if self._toca_entrada(ahora):
                self._intentar_fichaje("ENTRADA")
            if self._toca_salida_almuerzo(ahora):
                self._intentar_fichaje("SALIDA_ALMUERZO")
            if self._toca_entrada_almuerzo(ahora):
                self._intentar_fichaje("ENTRADA_ALMUERZO")
            if self._toca_salida(ahora):
                self._intentar_fichaje("SALIDA")

            _time.sleep(60)

    def detener(self) -> None:
        self._running = False
