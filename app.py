# -*- coding: utf-8 -*-
"""Entry point del Auto Fichaje NCS Clock.

Modos:
- GUI (default): muestra panel con reloj, log en vivo y estado.
- --silencioso: corre sin ventana, popups solo en fallos críticos.
"""
import argparse
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext

import config
import credenciales
import lock
import notifier
from scheduler import Scheduler, _es_laborable, _nombre_dia


# ──────────────────────────────────────────────────────────
# Logger compartido al archivo
# ──────────────────────────────────────────────────────────

def _escribir_log_archivo(mensaje: str, nivel: str = "INFO") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{nivel}] {mensaje}\n")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────
# Modo silencioso
# ──────────────────────────────────────────────────────────

def _ejecutar_silencioso(usuario: str, password: str) -> None:
    def on_log(m: str) -> None:
        _escribir_log_archivo(m)
        print(m)
    on_log("=" * 60)
    on_log("🚀 AUTO FICHAJE INICIADO (modo silencioso)")
    on_log(f"Ventana entrada: {config.ENTRADA_DESDE}–{config.ENTRADA_HASTA}")
    on_log(f"Ventana salida:  {config.SALIDA_DESDE}–{config.SALIDA_HASTA}")
    on_log("=" * 60)
    sched = Scheduler(usuario, password, on_log=on_log)
    sched.ejecutar()


# ──────────────────────────────────────────────────────────
# Modo GUI
# ──────────────────────────────────────────────────────────

class PanelControl:
    def __init__(self, usuario: str, password: str):
        self.usuario = usuario
        self.password = password

        self.root = tk.Tk()
        self.root.title("🕐 Auto Fichaje NCS — Panel de Control")
        self.root.geometry("600x500")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        notifier.set_root_principal(self.root)

        self._construir_ui()

        self._sched = Scheduler(
            usuario, password,
            on_log=self._log_thread_safe,
            on_estado_cambia=self._refrescar_estado_ui_thread_safe,
        )
        self._thread = threading.Thread(target=self._sched.ejecutar, daemon=True)
        self._thread.start()

        self._tick()

    def _construir_ui(self) -> None:
        cab = tk.Frame(self.root, bg="#1a1a2e", pady=10)
        cab.pack(fill=tk.X)
        tk.Label(cab, text="🕐 Auto Fichaje NCS",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="white").pack()
        tk.Label(cab, text="Panel de Control — Fichaje automático L–V",
                 font=("Arial", 10), bg="#1a1a2e", fg="#aaaaaa").pack()

        reloj = tk.Frame(self.root, bg="#16213e", pady=8)
        reloj.pack(fill=tk.X)
        self.lbl_reloj = tk.Label(reloj, text="", font=("Courier", 22, "bold"),
                                   bg="#16213e", fg="#00d4aa")
        self.lbl_reloj.pack()
        self.lbl_dia = tk.Label(reloj, text="", font=("Arial", 11),
                                 bg="#16213e", fg="#cccccc")
        self.lbl_dia.pack()

        marco = tk.LabelFrame(self.root, text="📊 Estado de Hoy",
                               font=("Arial", 10, "bold"), padx=10, pady=8)
        marco.pack(fill=tk.X, padx=12, pady=8)
        self.lbl_entrada = tk.Label(marco, text="Entrada: —", font=("Courier", 10))
        self.lbl_entrada.pack(anchor="w")
        self.lbl_salida = tk.Label(marco, text="Salida: —", font=("Courier", 10))
        self.lbl_salida.pack(anchor="w")

        log_frame = tk.LabelFrame(self.root, text="📋 Registro de actividad",
                                   font=("Arial", 10, "bold"), padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)
        self.txt_log = scrolledtext.ScrolledText(
            log_frame, height=8, state=tk.DISABLED,
            font=("Courier", 9), bg="#0d0d0d", fg="#00ff88", wrap=tk.WORD,
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        btns = tk.Frame(self.root, pady=8)
        btns.pack(fill=tk.X, padx=12)
        tk.Button(btns, text="🔑 Cambiar credenciales",
                  command=self._cambiar_credenciales,
                  bg="#555", fg="white", relief="flat", padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="🚪 Salir", command=self._on_close,
                  bg="#cc3333", fg="white", relief="flat", padx=10).pack(side=tk.RIGHT, padx=5)

    def _log_thread_safe(self, mensaje: str) -> None:
        _escribir_log_archivo(mensaje)
        self.root.after(0, lambda: self._log(mensaje))

    def _refrescar_estado_ui_thread_safe(self) -> None:
        self.root.after(0, self._refrescar_estado_ui)

    def _log(self, mensaje: str) -> None:
        try:
            self.txt_log.config(state=tk.NORMAL)
            ts = datetime.now().strftime("%H:%M:%S")
            self.txt_log.insert(tk.END, f"[{ts}] {mensaje}\n")
            self.txt_log.see(tk.END)
            self.txt_log.config(state=tk.DISABLED)
        except Exception:
            pass

    def _refrescar_estado_ui(self) -> None:
        e = self._sched._estado
        if e.entrada_realizada:
            self.lbl_entrada.config(text=f"Entrada: ✅ {e.entrada_ts.strftime('%H:%M:%S')}")
        elif e.hora_entrada:
            self.lbl_entrada.config(text=f"Entrada: ⏳ {e.hora_entrada.strftime('%H:%M:%S')}")
        if e.salida_realizada:
            self.lbl_salida.config(text=f"Salida:  ✅ {e.salida_ts.strftime('%H:%M:%S')}")
        elif e.hora_salida:
            self.lbl_salida.config(text=f"Salida:  ⏳ {e.hora_salida.strftime('%H:%M:%S')}")

    def _tick(self) -> None:
        ahora = datetime.now()
        self.lbl_reloj.config(text=ahora.strftime("%H:%M:%S"))
        self.lbl_dia.config(text=f"{_nombre_dia()} {ahora.strftime('%d/%m/%Y')}")
        self.root.after(1000, self._tick)

    def _cambiar_credenciales(self) -> None:
        credenciales.CredencialesManager().eliminar()
        messagebox.showinfo("Credenciales eliminadas",
                            "Reinicia la aplicación para configurar nuevas.")
        self._on_close()

    def _on_close(self) -> None:
        if messagebox.askyesno("Salir", "¿Detener el fichaje automático?"):
            self._sched.detener()
            self.root.destroy()

    def iniciar(self) -> None:
        self.root.mainloop()


# ──────────────────────────────────────────────────────────
# Pedir credenciales (modo GUI)
# ──────────────────────────────────────────────────────────

def _pedir_credenciales_gui() -> tuple[str | None, str | None]:
    root = tk.Tk()
    root.title("Auto Fichaje NCS — Configuración inicial")
    root.geometry("420x250")
    root.resizable(False, False)
    u_var = tk.StringVar()
    p_var = tk.StringVar()
    guardado = {"ok": False}

    tk.Label(root, text="🕐 Auto Fichaje NCS", font=("Arial", 16, "bold")).pack(pady=15)
    tk.Label(root, text="Introduce tus credenciales:", font=("Arial", 10)).pack()
    f = tk.Frame(root, pady=10); f.pack()
    tk.Label(f, text="Usuario:", width=12, anchor="e").grid(row=0, column=0, pady=5)
    tk.Entry(f, textvariable=u_var, width=25).grid(row=0, column=1, pady=5, padx=5)
    tk.Label(f, text="Contraseña:", width=12, anchor="e").grid(row=1, column=0, pady=5)
    tk.Entry(f, textvariable=p_var, show="●", width=25).grid(row=1, column=1, pady=5, padx=5)

    def aceptar():
        if not u_var.get().strip() or not p_var.get().strip():
            messagebox.showerror("Error", "Rellena ambos campos")
            return
        credenciales.CredencialesManager().guardar(u_var.get().strip(), p_var.get().strip())
        guardado["ok"] = True
        root.destroy()

    tk.Button(root, text="Guardar y continuar", command=aceptar,
              bg="#007bff", fg="white", padx=15, pady=5).pack(pady=15)
    root.mainloop()

    if not guardado["ok"]:
        return None, None
    return credenciales.CredencialesManager().cargar()


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="AutoFichajeNCS",
                                 description="Bot de fichaje automático NCS")
    p.add_argument("--silencioso", action="store_true",
                    help="Corre sin GUI, solo popups en fallos críticos")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    try:
        lock.adquirir()
    except lock.LockBusy as e:
        notifier.aviso_doble_instancia(e.pid_otro)
        _escribir_log_archivo(f"Doble instancia rechazada (PID otro={e.pid_otro})", "ERROR")
        return 1

    mgr = credenciales.CredencialesManager()
    usuario, password = mgr.cargar()
    if not usuario or not password:
        if args.silencioso:
            _escribir_log_archivo("Sin credenciales y modo silencioso. No se puede arrancar.", "ERROR")
            return 1
        usuario, password = _pedir_credenciales_gui()
        if not usuario:
            return 0

    if args.silencioso:
        _ejecutar_silencioso(usuario, password)
    else:
        PanelControl(usuario, password).iniciar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
