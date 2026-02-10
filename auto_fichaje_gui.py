# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║          🕐 AUTO FICHAJE - NCS Clock (Versión GUI)          ║
║          Primera ejecución: Configurar credenciales         ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import base64
import time
import random
import signal
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
from pathlib import Path

# Importar módulos de automatización
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Importar módulos NCS
import ncs_login
import ncs_fichaje
from ncs_csv_logger import FichajeCSVLogger


# ============================================================
# 🔐 Gestión de Credenciales
# ============================================================

class CredencialesManager:
    """Gestiona el almacenamiento seguro de credenciales."""
    
    def __init__(self):
        # Directorio de configuración en AppData
        self.config_dir = Path.home() / "AppData" / "Local" / "AutoFichajeNCS"
        self.config_file = self.config_dir / "config.dat"
        
        # Crear directorio si no existe
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _codificar(self, texto):
        """Codifica texto en base64 (ofuscación básica)."""
        return base64.b64encode(texto.encode('utf-8')).decode('utf-8')
    
    def _decodificar(self, texto_codificado):
        """Decodifica texto desde base64."""
        return base64.b64decode(texto_codificado.encode('utf-8')).decode('utf-8')
    
    def guardar(self, usuario, password):
        """Guarda las credenciales de forma ofuscada."""
        datos = {
            "usuario": self._codificar(usuario),
            "password": self._codificar(password)
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(datos, f)
    
    def cargar(self):
        """Carga las credenciales si existen."""
        if not self.config_file.exists():
            return None, None
        
        try:
            with open(self.config_file, 'r') as f:
                datos = json.load(f)
            
            usuario = self._decodificar(datos["usuario"])
            password = self._decodificar(datos["password"])
            
            return usuario, password
        except Exception:
            return None, None
    
    def existen(self):
        """Verifica si ya hay credenciales guardadas."""
        return self.config_file.exists()
    
    def eliminar(self):
        """Elimina las credenciales guardadas."""
        if self.config_file.exists():
            self.config_file.unlink()


# ============================================================
# 🎨 Ventana de Configuración
# ============================================================

class VentanaConfiguracion:
    """Ventana para configurar las credenciales por primera vez."""
    
    def __init__(self):
        self.usuario = None
        self.password = None
        self.guardado = False
        
        # Crear ventana
        self.root = tk.Tk()
        self.root.title("Auto Fichaje NCS - Configuración Inicial")
        self.root.geometry("450x350")
        self.root.resizable(False, False)
        
        # Centrar ventana
        self.centrar_ventana()
        
        # Crear interfaz
        self.crear_interfaz()
    
    def centrar_ventana(self):
        """Centra la ventana en la pantalla."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def crear_interfaz(self):
        """Crea la interfaz de la ventana."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Título
        titulo = ttk.Label(
            main_frame,
            text="🕐 Auto Fichaje - NCS Clock",
            font=("Arial", 16, "bold")
        )
        titulo.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Subtítulo
        subtitulo = ttk.Label(
            main_frame,
            text="Configura tus credenciales de NCS Clock",
            font=("Arial", 10)
        )
        subtitulo.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        # Campo Usuario
        ttk.Label(main_frame, text="Usuario:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        
        self.entry_usuario = ttk.Entry(main_frame, width=30, font=("Arial", 10))
        self.entry_usuario.grid(row=2, column=1, pady=5, padx=(10, 0))
        self.entry_usuario.focus()
        
        # Campo Contraseña
        ttk.Label(main_frame, text="Contraseña:", font=("Arial", 10, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        
        self.entry_password = ttk.Entry(main_frame, width=30, show="●", font=("Arial", 10))
        self.entry_password.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Checkbox mostrar contraseña
        self.var_mostrar = tk.BooleanVar()
        check_mostrar = ttk.Checkbutton(
            main_frame,
            text="Mostrar contraseña",
            variable=self.var_mostrar,
            command=self.toggle_password
        )
        check_mostrar.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Información
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.grid(row=5, column=0, columnspan=2, pady=20, sticky=(tk.W, tk.E))
        
        info_text = (
            "• Fichaje automático de Lunes a Viernes\n"
            "• Entrada: 8:50 - 9:05 (aleatorio)\n"
            "• Salida: 18:05 - 18:30 (aleatorio)\n"
            "• Se ejecutará en segundo plano"
        )
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(
            button_frame,
            text="Guardar y Continuar",
            command=self.guardar,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancelar",
            command=self.cancelar,
            width=15
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        self.entry_password.bind('<Return>', lambda e: self.guardar())
    
    def toggle_password(self):
        """Muestra/oculta la contraseña."""
        if self.var_mostrar.get():
            self.entry_password.config(show="")
        else:
            self.entry_password.config(show="●")
    
    def guardar(self):
        """Valida y guarda las credenciales."""
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()
        
        if not usuario:
            messagebox.showerror("Error", "El campo usuario no puede estar vacío")
            self.entry_usuario.focus()
            return
        
        if not password:
            messagebox.showerror("Error", "El campo contraseña no puede estar vacío")
            self.entry_password.focus()
            return
        
        # Confirmar
        if messagebox.askyesno(
            "Confirmar",
            f"¿Guardar credenciales para el usuario '{usuario}'?\n\n"
            "El servicio comenzará a funcionar automáticamente."
        ):
            self.usuario = usuario
            self.password = password
            self.guardado = True
            self.root.destroy()
    
    def cancelar(self):
        """Cancela la configuración."""
        if messagebox.askyesno("Cancelar", "¿Salir sin configurar?"):
            self.root.destroy()
    
    def mostrar(self):
        """Muestra la ventana y espera."""
        self.root.mainloop()
        return self.guardado, self.usuario, self.password


# ============================================================
# 🕐 Motor de Fichaje (igual que auto_fichaje.py)
# ============================================================

# Configuración
DIAS_LABORABLES = [0, 1, 2, 3, 4]
ENTRADA_DESDE = "08:50"
ENTRADA_HASTA = "09:05"
SALIDA_DESDE = "18:05"
SALIDA_HASTA = "18:30"
CSV_FICHAJES = "fichajes.csv"


def es_dia_laborable():
    return datetime.now().weekday() in DIAS_LABORABLES


def nombre_dia():
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return dias[datetime.now().weekday()]


def calcular_hora_aleatoria(hora_desde, hora_hasta):
    hoy = datetime.now().date()
    h_desde, m_desde = map(int, hora_desde.split(":"))
    h_hasta, m_hasta = map(int, hora_hasta.split(":"))
    
    dt_desde = datetime.combine(hoy, datetime.min.time().replace(hour=h_desde, minute=m_desde))
    dt_hasta = datetime.combine(hoy, datetime.min.time().replace(hour=h_hasta, minute=m_hasta))
    
    diff_segundos = int((dt_hasta - dt_desde).total_seconds())
    offset = random.randint(0, diff_segundos)
    
    return dt_desde + timedelta(seconds=offset)


def esperar_hasta(hora_objetivo):
    while datetime.now() < hora_objetivo:
        ahora = datetime.now()
        restante = (hora_objetivo - ahora).total_seconds()
        
        if restante <= 0:
            break
        
        if restante > 60:
            time.sleep(30)
        else:
            time.sleep(1)


def segundos_hasta_manana():
    ahora = datetime.now()
    manana = (ahora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (manana - ahora).total_seconds()


def crear_navegador():
    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,768")
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("useAutomationExtension", False)
    opciones.add_argument("--disable-notifications")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opciones)
        
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        
        return driver
    except Exception:
        return None


def realizar_fichaje_completo(usuario, password):
    logger = FichajeCSVLogger(CSV_FICHAJES)
    driver = crear_navegador()
    
    if not driver:
        return False
    
    try:
        url = "https://clock.ncs.es/ClienteReloj/DoTicada"
        driver.get(url)
        time.sleep(3)
        
        resultado_login = ncs_login.realizar_login(driver, usuario, password)
        if not resultado_login["success"]:
            return False
        
        resultado_fichaje = ncs_fichaje.realizar_fichaje(driver)
        
        if resultado_fichaje["success"]:
            logger.registrar_fichaje(
                tipo=resultado_fichaje["tipo"],
                hora=resultado_fichaje["hora_fichaje"],
                presencia=resultado_fichaje.get("presencia", ""),
                jornada=resultado_fichaje.get("jornada", ""),
                extra=resultado_fichaje.get("extra", ""),
                observaciones="Fichaje automático"
            )
            return True
        else:
            return False
    
    except Exception:
        return False
    
    finally:
        driver.quit()


class AutoFichaje:
    def __init__(self, usuario, password):
        self.usuario = usuario
        self.password = password
        self._running = True
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        self._running = False
        sys.exit(0)
    
    def ejecutar_dia(self):
        if not es_dia_laborable():
            return
        
        hora_entrada = calcular_hora_aleatoria(ENTRADA_DESDE, ENTRADA_HASTA)
        hora_salida = calcular_hora_aleatoria(SALIDA_DESDE, SALIDA_HASTA)
        
        ahora = datetime.now()
        
        if ahora < hora_entrada:
            esperar_hasta(hora_entrada)
            realizar_fichaje_completo(self.usuario, self.password)
        elif ahora.hour < 14:
            realizar_fichaje_completo(self.usuario, self.password)
        
        ahora = datetime.now()
        if ahora < hora_salida:
            esperar_hasta(hora_salida)
            realizar_fichaje_completo(self.usuario, self.password)
        else:
            realizar_fichaje_completo(self.usuario, self.password)
    
    def ejecutar_continuo(self):
        while self._running:
            self.ejecutar_dia()
            
            if not self._running:
                break
            
            segundos = segundos_hasta_manana() + random.randint(60, 300)
            inicio_sleep = time.time()
            
            while self._running and (time.time() - inicio_sleep) < segundos:
                time.sleep(min(60, segundos - (time.time() - inicio_sleep)))


# ============================================================
# 🚀 Punto de Entrada Principal
# ============================================================

def main():
    """Punto de entrada con GUI de configuración."""
    
    # Gestionar credenciales
    manager = CredencialesManager()
    
    # Si ya existen credenciales, usarlas
    usuario, password = manager.cargar()
    
    # Si no existen, mostrar ventana de configuración
    if not usuario or not password:
        ventana = VentanaConfiguracion()
        guardado, usuario, password = ventana.mostrar()
        
        if not guardado:
            # Usuario canceló
            sys.exit(0)
        
        # Guardar credenciales
        manager.guardar(usuario, password)
        
        # Mostrar mensaje de éxito
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Configuración Completa",
            "¡Credenciales guardadas correctamente!\n\n"
            "El servicio de fichaje automático está ahora activo.\n"
            "Se ejecutará en segundo plano hasta que apagues el PC.\n\n"
            "Fichaje automático:\n"
            "• Lunes a Viernes\n"
            "• Entrada: 8:50 - 9:05\n"
            "• Salida: 18:05 - 18:30"
        )
        root.destroy()
    
    # Iniciar servicio de fichaje
    auto_fichaje = AutoFichaje(usuario, password)
    auto_fichaje.ejecutar_continuo()


if __name__ == "__main__":
    main()
