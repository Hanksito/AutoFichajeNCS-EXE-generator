# -*- coding: utf-8 -*-
"""Popups modales thread-safe para avisos al usuario.

Diseño:
- Si ya hay una ventana raíz Tk activa (modo GUI), se delega vía
  root.after(0, ...) para mostrar en el event loop principal.
- Si no (modo --silencioso), se crea una Tk root temporal en un
  hilo aparte para mostrar el messagebox y se destruye.

El popup es bloqueante para el usuario, pero el scheduler sigue.
"""
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

# Referencia opcional a la root Tk de la GUI principal.
# El módulo app.py debe asignarla con `notifier.set_root_principal(root)`.
_root_principal: Optional[tk.Tk] = None
_root_lock = threading.Lock()


def set_root_principal(root: Optional[tk.Tk]) -> None:
    """Registra la root Tk de la GUI principal (o None si no hay GUI)."""
    global _root_principal
    with _root_lock:
        _root_principal = root


# ──────────────────────────────────────────────────────────
# Composición de mensajes (testable)
# ──────────────────────────────────────────────────────────

def _componer_fallo(tipo: str, motivo: str, html_cambio: bool) -> tuple[str, str]:
    titulo = f"Fichaje {tipo} fallido"
    cuerpo = (
        f"No se pudo fichar la {tipo} hoy tras 3 intentos.\n\n"
        f"Causa: {motivo}\n\n"
        f"Por favor, ficha la {tipo} manualmente en clock.ncs.es."
    )
    if html_cambio:
        cuerpo += (
            "\n\nAVISO: la web de NCS pudo haber cambiado. "
            "Avisa al desarrollador para actualizar el bot."
        )
    return titulo, cuerpo


def _componer_doble_instancia(pid_otro: int) -> tuple[str, str]:
    titulo = "Auto Fichaje ya en ejecucion"
    cuerpo = (
        f"Ya hay otra instancia de Auto Fichaje corriendo (PID={pid_otro}).\n\n"
        f"Esta instancia no arrancara. Si quieres reiniciar, cierra la otra primero."
    )
    return titulo, cuerpo


# ──────────────────────────────────────────────────────────
# Visualización
# ──────────────────────────────────────────────────────────

def _mostrar_popup(titulo: str, mensaje: str, icono: str = "error") -> None:
    """Muestra el popup. Usa root principal si existe, si no crea uno efímero."""
    with _root_lock:
        root = _root_principal  # snapshot atómico
    if root is not None:
        # Inyectamos en el event loop principal de Tk
        root.after(0, lambda: _show_message(titulo, mensaje, icono))
    else:
        # Modo silencioso: hilo con Tk efímera. daemon=False para que el
        # popup pueda completarse aunque el scheduler termine antes.
        threading.Thread(
            target=_mostrar_efimero,
            args=(titulo, mensaje, icono),
            daemon=False,
        ).start()


def _show_message(titulo: str, mensaje: str, icono: str) -> None:
    if icono == "error":
        messagebox.showerror(titulo, mensaje)
    elif icono == "warning":
        messagebox.showwarning(titulo, mensaje)
    else:
        messagebox.showinfo(titulo, mensaje)


def _mostrar_efimero(titulo: str, mensaje: str, icono: str) -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        _show_message(titulo, mensaje, icono)
    finally:
        root.destroy()


# ──────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────

def aviso_fallo(tipo: str, motivo: str, html_cambio: bool = False) -> None:
    titulo, mensaje = _componer_fallo(tipo, motivo, html_cambio)
    _mostrar_popup(titulo, mensaje, icono="error")


def aviso_doble_instancia(pid_otro: int) -> None:
    titulo, mensaje = _componer_doble_instancia(pid_otro)
    _mostrar_popup(titulo, mensaje, icono="warning")
