# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║          🕐 AUTO FICHAJE - NCS Clock                        ║
║          Fichaje automático Lunes a Viernes                 ║
║          Entrada: 8:50-9:05 | Salida: 18:05-18:30          ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
import signal
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Importar módulos NCS
import ncs_login
import ncs_fichaje
from ncs_csv_logger import FichajeCSVLogger

# Cargar variables de entorno
load_dotenv()

# ============================================================
# ⚙️ CONFIGURACIÓN
# ============================================================

# Días laborables (0=Lunes, 4=Viernes)
DIAS_LABORABLES = [0, 1, 2, 3, 4]

# Horarios de entrada (formato HH:MM)
ENTRADA_DESDE = "08:50"
ENTRADA_HASTA = "09:05"

# Horarios de salida (formato HH:MM)
SALIDA_DESDE = "18:05"
SALIDA_HASTA = "18:30"

# Archivo CSV de registro
CSV_FICHAJES = "fichajes.csv"


# ============================================================
# 🕐 Funciones de Tiempo
# ============================================================

def es_dia_laborable():
    """Comprueba si hoy es día laborable (Lunes-Viernes)."""
    return datetime.now().weekday() in DIAS_LABORABLES


def nombre_dia():
    """Devuelve el nombre del día actual en español."""
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    return dias[datetime.now().weekday()]


def calcular_hora_aleatoria(hora_desde, hora_hasta):
    """
    Calcula un datetime aleatorio entre dos horas para el día de hoy.
    
    Args:
        hora_desde: Hora inicio (formato HH:MM)
        hora_hasta: Hora fin (formato HH:MM)
        
    Returns:
        datetime: Hora aleatoria entre ambas
    """
    hoy = datetime.now().date()
    h_desde, m_desde = map(int, hora_desde.split(":"))
    h_hasta, m_hasta = map(int, hora_hasta.split(":"))
    
    dt_desde = datetime.combine(hoy, datetime.min.time().replace(hour=h_desde, minute=m_desde))
    dt_hasta = datetime.combine(hoy, datetime.min.time().replace(hour=h_hasta, minute=m_hasta))
    
    diff_segundos = int((dt_hasta - dt_desde).total_seconds())
    offset = random.randint(0, diff_segundos)
    
    return dt_desde + timedelta(seconds=offset)


def esperar_hasta(hora_objetivo):
    """
    Espera hasta la hora objetivo mostrando el tiempo restante.
    
    Args:
        hora_objetivo: datetime objetivo
    """
    while datetime.now() < hora_objetivo:
        ahora = datetime.now()
        restante = (hora_objetivo - ahora).total_seconds()
        
        if restante <= 0:
            break
        
        # Mostrar tiempo restante cada minuto
        horas = int(restante // 3600)
        minutos = int((restante % 3600) // 60)
        
        if restante > 60:
            print(f"\r⏳ Esperando... Faltan {horas}h {minutos}min hasta las {hora_objetivo.strftime('%H:%M:%S')}  ", end='', flush=True)
            time.sleep(30)  # Actualizar cada 30 segundos
        else:
            time.sleep(1)


def segundos_hasta_manana():
    """Calcula los segundos hasta las 00:00 del día siguiente."""
    ahora = datetime.now()
    manana = (ahora + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (manana - ahora).total_seconds()


# ============================================================
# 🌐 Gestión del Navegador
# ============================================================

def crear_navegador():
    """Crea y configura el navegador Chrome en modo headless."""
    print("🌐 Preparando navegador...")
    
    opciones = Options()
    
    # Modo headless (invisible)
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,768")
    
    # Anti-detección
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("useAutomationExtension", False)
    opciones.add_argument("--disable-notifications")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opciones)
        
        # Eliminar navigator.webdriver
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        
        print("✅ Navegador listo")
        return driver
        
    except Exception as e:
        print(f"❌ Error al crear el navegador: {e}")
        return None


# ============================================================
# 🕐 Proceso de Fichaje
# ============================================================

def realizar_fichaje_completo(tipo_esperado=""):
    """
    Realiza el proceso completo: Login → Fichaje → CSV.
    
    Args:
        tipo_esperado: "ENTRADA" o "SALIDA" (para logs)
        
    Returns:
        bool: True si fue exitoso, False si falló
    """
    # Obtener credenciales
    usuario = os.getenv("NCS_USUARIO", "")
    password = os.getenv("NCS_PASSWORD", "")
    
    if not usuario or not password:
        print("❌ ERROR: No se encontraron credenciales en .env")
        return False
    
    # Crear logger CSV
    logger = FichajeCSVLogger(CSV_FICHAJES)
    
    # Crear navegador
    driver = crear_navegador()
    if not driver:
        return False
    
    try:
        # Navegar a la página
        url = "https://clock.ncs.es/ClienteReloj/DoTicada"
        print(f"📄 Navegando a la página de fichaje...")
        driver.get(url)
        time.sleep(3)
        
        # Login (si es necesario)
        resultado_login = ncs_login.realizar_login(driver, usuario, password)
        if not resultado_login["success"]:
            print(f"❌ Login fallido: {resultado_login['mensaje']}")
            return False
        
        print("✅ Login exitoso")
        print()
        
        # Realizar fichaje
        resultado_fichaje = ncs_fichaje.realizar_fichaje(driver)
        
        print()
        print("=" * 60)
        
        if resultado_fichaje["success"]:
            tipo = resultado_fichaje["tipo"]
            hora = resultado_fichaje["hora_fichaje"]
            presencia = resultado_fichaje.get("presencia", "")
            jornada = resultado_fichaje.get("jornada", "")
            extra = resultado_fichaje.get("extra", "")
            
            print(f"✅ ¡FICHAJE DE {tipo} EXITOSO!")
            print(f"   📅 {datetime.now().strftime('%d/%m/%Y')}")
            print(f"   ⏰ Hora: {hora}")
            print(f"   📊 Presencia: {presencia}")
            print(f"   📋 Jornada: {jornada}")
            if extra:
                print(f"   {extra}")
            print("=" * 60)
            
            # Registrar en CSV
            logger.registrar_fichaje(
                tipo=tipo,
                hora=hora,
                presencia=presencia,
                jornada=jornada,
                extra=extra,
                observaciones="Fichaje automático"
            )
            
            print("📝 Fichaje registrado en CSV")
            return True
        else:
            print(f"❌ Fichaje fallido: {resultado_fichaje['mensaje']}")
            
            # Registrar el fallo
            logger.registrar_fichaje(
                tipo=tipo_esperado,
                hora="",
                observaciones=f"ERROR: {resultado_fichaje['mensaje']}"
            )
            
            return False
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
    
    finally:
        driver.quit()
        print("🔒 Navegador cerrado")


# ============================================================
# 🔄 Ejecución Continua
# ============================================================

class AutoFichaje:
    """Gestiona la ejecución continua del fichaje automático."""
    
    def __init__(self):
        self._running = True
        
        # Manejar Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Maneja Ctrl+C de forma limpia."""
        print("\n\n🛑 Señal de interrupción recibida. Cerrando...")
        self._running = False
        sys.exit(0)
    
    def ejecutar_dia(self):
        """Ejecuta el fichaje de un día completo (entrada + salida)."""
        print("\n")
        print("╔" + "═" * 58 + "╗")
        print(f"║  📅 {nombre_dia()} {datetime.now().strftime('%d/%m/%Y')}" + " " * 34 + "║")
        print("╚" + "═" * 58 + "╝")
        
        if not es_dia_laborable():
            print("🏖️  Hoy no es día laborable. Esperando al próximo día...")
            return
        
        # --- FICHAJE DE ENTRADA ---
        hora_entrada = calcular_hora_aleatoria(ENTRADA_DESDE, ENTRADA_HASTA)
        print(f"⏰ Hora de ENTRADA programada: {hora_entrada.strftime('%H:%M:%S')}")
        
        # --- FICHAJE DE SALIDA ---
        hora_salida = calcular_hora_aleatoria(SALIDA_DESDE, SALIDA_HASTA)
        print(f"⏰ Hora de SALIDA programada:  {hora_salida.strftime('%H:%M:%S')}")
        print()
        
        ahora = datetime.now()
        
        # Realizar fichaje de entrada (si no ha pasado ya)
        if ahora < hora_entrada:
            esperar_hasta(hora_entrada)
            print("\n🕐 Realizando fichaje de ENTRADA...\n")
            realizar_fichaje_completo("ENTRADA")
        elif ahora.hour < 14:  # Si aún es por la mañana temprano
            print("⚠️  La hora de entrada ya pasó, fichando ahora...")
            realizar_fichaje_completo("ENTRADA")
        else:
            print("⏭️  Hora de entrada ya pasada, solo se realizará la salida")
        
        # Esperar a la hora de salida
        ahora = datetime.now()
        if ahora < hora_salida:
            print()
            esperar_hasta(hora_salida)
            print("\n🕐 Realizando fichaje de SALIDA...\n")
            realizar_fichaje_completo("SALIDA")
        else:
            print("⚠️  La hora de salida ya pasó, fichando ahora...")
            realizar_fichaje_completo("SALIDA")
        
        print()
        print("✅ Día completado")
    
    def ejecutar_continuo(self):
        """Ejecuta el fichaje de forma continua, día tras día."""
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 10 + "🕐 AUTO FICHAJE - NCS Clock" + " " * 21 + "║")
        print("║" + " " * 10 + "Fichaje Automático L-V" + " " * 26 + "║")
        print("╚" + "═" * 58 + "╝")
        print()
        print(f"📍 URL: https://clock.ncs.es/ClienteReloj/DoTicada")
        print(f"⏰ Entrada: {ENTRADA_DESDE} - {ENTRADA_HASTA}")
        print(f"⏰ Salida:  {SALIDA_DESDE} - {SALIDA_HASTA}")
        print(f"📅 Días:    Lunes a Viernes")
        print(f"📝 Log CSV: {CSV_FICHAJES}")
        print()
        
        while self._running:
            self.ejecutar_dia()
            
            if not self._running:
                break
            
            # Esperar al día siguiente
            segundos = segundos_hasta_manana() + random.randint(60, 300)
            proximo = datetime.now() + timedelta(seconds=segundos)
            
            print()
            print("─" * 60)
            print(f"💤 Próximo día: {proximo.strftime('%A %d/%m/%Y %H:%M')}")
            print(f"💤 Durmiendo {int(segundos // 3600)}h {int((segundos % 3600) // 60)}min...")
            print("─" * 60)
            
            # Dormir hasta el día siguiente
            inicio_sleep = time.time()
            while self._running and (time.time() - inicio_sleep) < segundos:
                time.sleep(min(60, segundos - (time.time() - inicio_sleep)))


# ============================================================
# 🚀 Punto de Entrada
# ============================================================

def main():
    """Punto de entrada principal."""
    auto_fichaje = AutoFichaje()
    auto_fichaje.ejecutar_continuo()


if __name__ == "__main__":
    main()
