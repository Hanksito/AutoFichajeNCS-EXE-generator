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
ENTRADA_DESDE = "08:45"
ENTRADA_HASTA = "08:55"

# Horarios de salida (formato HH:MM)
SALIDA_DESDE = "18:05"
SALIDA_HASTA = "18:30"

# Archivo CSV de registro
CSV_FICHAJES = "fichajes.csv"

# Archivo de log
LOG_FILE = "auto_fichaje.log"


# ============================================================
# 📝 Sistema de Logging
# ============================================================

def escribir_log(mensaje, nivel="INFO"):
    """Escribe un mensaje en el archivo de log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{timestamp}] [{nivel}] {mensaje}\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(linea)
    except Exception:
        pass  # Silenciar errores de logging


def log_info(mensaje):
    """Log de nivel INFO."""
    escribir_log(mensaje, "INFO")
    print(f"ℹ️  {mensaje}")


def log_success(mensaje):
    """Log de nivel SUCCESS."""
    escribir_log(mensaje, "SUCCESS")
    print(f"✅ {mensaje}")


def log_warning(mensaje):
    """Log de nivel WARNING."""
    escribir_log(mensaje, "WARNING")
    print(f"⚠️  {mensaje}")


def log_error(mensaje):
    """Log de nivel ERROR."""
    escribir_log(mensaje, "ERROR")
    print(f"❌ {mensaje}")



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
        log_error("No se encontraron credenciales en .env")
        return False
    
    log_info(f"Iniciando proceso de fichaje ({tipo_esperado})")
    
    # Crear logger CSV
    logger = FichajeCSVLogger(CSV_FICHAJES)
    
    # Crear navegador
    driver = crear_navegador()
    if not driver:
        log_error("No se pudo crear el navegador")
        return False
    
    try:
        # Navegar a la página
        url = "https://clock.ncs.es/ClienteReloj/DoTicada"
        log_info(f"Navegando a {url}")
        driver.get(url)
        time.sleep(3)
        
        # Login (si es necesario)
        resultado_login = ncs_login.realizar_login(driver, usuario, password)
        if not resultado_login["success"]:
            log_error(f"Login fallido: {resultado_login['mensaje']}")
            return False
        
        log_success("Login exitoso")
        
        # Realizar fichaje verificando estado real de la web
        resultado_fichaje = ncs_fichaje.realizar_fichaje(driver, tipo_esperado=tipo_esperado)

        print()
        print("=" * 60)

        if resultado_fichaje.get("saltado"):
            # Alguien ya fichó manualmente → no era necesario actuar
            motivo = resultado_fichaje["mensaje"]
            print(f"⏭️  FICHAJE OMITIDO: {motivo}")
            log_warning(f"Fichaje {tipo_esperado} omitido: {motivo}")
            return True  # No es un error, el estado ya era el correcto

        if resultado_fichaje["success"]:
            tipo     = resultado_fichaje["tipo"]
            hora     = resultado_fichaje["hora_fichaje"]
            presencia = resultado_fichaje.get("presencia", "")
            jornada  = resultado_fichaje.get("jornada", "")
            extra    = resultado_fichaje.get("extra", "")

            print(f"✅ ¡FICHAJE DE {tipo} EXITOSO!")
            print(f"   📅 {datetime.now().strftime('%d/%m/%Y')}")
            print(f"   ⏰ Hora: {hora}")
            print(f"   📊 Presencia: {presencia}")
            print(f"   📋 Jornada: {jornada}")
            if extra:
                print(f"   {extra}")
            print("=" * 60)

            log_success(f"Fichaje {tipo} exitoso a las {hora} - Presencia: {presencia}")

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
            mensaje_error = resultado_fichaje['mensaje']
            print(f"❌ Fichaje fallido: {mensaje_error}")
            log_error(f"Fichaje fallido: {mensaje_error}")
            
            # Registrar el fallo
            logger.registrar_fichaje(
                tipo=tipo_esperado,
                hora="",
                observaciones=f"ERROR: {mensaje_error}"
            )
            
            return False
    
    except Exception as e:
        error_msg = f"Error inesperado: {e}"
        print(f"❌ {error_msg}")
        log_error(error_msg)
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

        # Registro de lo que ya se ha hecho HOY (evita dobles fichajes)
        self._fecha_entrada = None   # fecha en que se fichó entrada
        self._fecha_salida = None    # fecha en que se fichó salida

        # Hora aleatoria calculada para hoy
        self._hora_entrada_hoy = None
        self._hora_salida_hoy = None

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Maneja Ctrl+C de forma limpia."""
        log_info("Señal de interrupción recibida. Cerrando...")
        self._running = False
        sys.exit(0)

    def _calcular_horarios_para_hoy(self):
        """Calcula (o recalcula) los horarios aleatorios para el día actual."""
        self._hora_entrada_hoy = calcular_hora_aleatoria(ENTRADA_DESDE, ENTRADA_HASTA)
        self._hora_salida_hoy  = calcular_hora_aleatoria(SALIDA_DESDE,  SALIDA_HASTA)
        log_info(f"Horarios de hoy → Entrada: {self._hora_entrada_hoy.strftime('%H:%M:%S')} | Salida: {self._hora_salida_hoy.strftime('%H:%M:%S')}")

    def _es_nuevo_dia(self):
        """Devuelve True si hoy es un día diferente al último ciclo procesado."""
        hoy = datetime.now().date()
        # Si ninguno de los dos está registrado O el último registrado no es hoy
        ultima = self._fecha_salida or self._fecha_entrada
        return ultima is None or ultima != hoy

    def _ventana_entrada_activa(self, ahora: datetime) -> bool:
        """True si estamos dentro de la ventana horaria de entrada."""
        h_desde = datetime.strptime(ENTRADA_DESDE, "%H:%M").replace(
            year=ahora.year, month=ahora.month, day=ahora.day)
        h_hasta = datetime.strptime(ENTRADA_HASTA, "%H:%M").replace(
            year=ahora.year, month=ahora.month, day=ahora.day)
        return h_desde <= ahora <= h_hasta

    def _ventana_salida_activa(self, ahora: datetime) -> bool:
        """True si estamos dentro de la ventana horaria de salida."""
        h_desde = datetime.strptime(SALIDA_DESDE, "%H:%M").replace(
            year=ahora.year, month=ahora.month, day=ahora.day)
        h_hasta = datetime.strptime(SALIDA_HASTA, "%H:%M").replace(
            year=ahora.year, month=ahora.month, day=ahora.day)
        return h_desde <= ahora <= h_hasta

    def ejecutar_continuo(self):
        """
        Bucle principal: comprueba cada minuto si hay que fichar.
        - Al inicio del día (o arranque) calcula horarios aleatorios.
        - Ficha ENTRADA cuando la hora aleatoria llega dentro de la ventana.
        - Ficha SALIDA cuando la hora aleatoria llega dentro de la ventana.
        - Nunca ficha dos veces el mismo tipo en el mismo día.
        """
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
        print(f"📄 Log:     {LOG_FILE}")
        print()

        log_info("=" * 60)
        log_info("🚀 AUTO FICHAJE INICIADO")
        log_info(f"Ventana entrada: {ENTRADA_DESDE}-{ENTRADA_HASTA} | Ventana salida: {SALIDA_DESDE}-{SALIDA_HASTA}")
        log_info("=" * 60)

        ultimo_dia_procesado = None  # para detectar cambio de día

        while self._running:
            ahora = datetime.now()
            hoy   = ahora.date()

            # ── Detectar nuevo día y calcular horarios frescos ──────────
            if hoy != ultimo_dia_procesado:
                ultimo_dia_procesado = hoy
                print(f"\n📅 Nuevo día: {nombre_dia()} {ahora.strftime('%d/%m/%Y')}")
                log_info(f"===== INICIO DE DÍA: {nombre_dia()} {ahora.strftime('%d/%m/%Y')} =====")

                if not es_dia_laborable():
                    log_warning(f"Hoy es {nombre_dia()} (no laborable). Esperando al lunes...")
                    print(f"🏖️  Hoy es {nombre_dia()}, no es día laborable. Descansando...")
                else:
                    self._calcular_horarios_para_hoy()

            # ── Solo actuar en días laborables ───────────────────────────
            if not es_dia_laborable():
                time.sleep(60)
                continue

            entrada_ya_hecha = self._fecha_entrada == hoy
            salida_ya_hecha  = self._fecha_salida  == hoy

            # ── Fichaje de ENTRADA ────────────────────────────────────────
            if (not entrada_ya_hecha
                    and self._hora_entrada_hoy is not None
                    and ahora >= self._hora_entrada_hoy
                    and self._ventana_entrada_activa(ahora)):

                log_info(f"⏰ Hora de entrada alcanzada ({ahora.strftime('%H:%M:%S')}). Fichando ENTRADA...")
                print(f"\n🕐 Fichando ENTRADA a las {ahora.strftime('%H:%M:%S')}...\n")
                exito = realizar_fichaje_completo("ENTRADA")
                if exito:
                    self._fecha_entrada = hoy
                    log_success(f"Entrada registrada el {hoy}")
                else:
                    log_error("Fallo en fichaje de ENTRADA - se reintentará en 5 min")
                    # dejar _fecha_entrada = None para reintentar en la siguiente iteración
                    time.sleep(300)
                    continue

            # ── Fichaje de SALIDA ─────────────────────────────────────────
            if (not salida_ya_hecha
                    and self._hora_salida_hoy is not None
                    and ahora >= self._hora_salida_hoy
                    and self._ventana_salida_activa(ahora)):

                log_info(f"⏰ Hora de salida alcanzada ({ahora.strftime('%H:%M:%S')}). Fichando SALIDA...")
                print(f"\n🕐 Fichando SALIDA a las {ahora.strftime('%H:%M:%S')}...\n")
                exito = realizar_fichaje_completo("SALIDA")
                if exito:
                    self._fecha_salida = hoy
                    log_success(f"Salida registrada el {hoy}")
                    log_success(f"===== DÍA COMPLETADO: {ahora.strftime('%d/%m/%Y %H:%M:%S')} =====")
                    print("✅ Día completado. Esperando al próximo día laborable...")
                else:
                    log_error("Fallo en fichaje de SALIDA - se reintentará en 5 min")
                    time.sleep(300)
                    continue

            # ── Mostrar estado cada 30 min (informativo) ─────────────────
            if ahora.minute % 30 == 0 and ahora.second < 61:
                estado_e = "✅" if entrada_ya_hecha else f"⏳ {self._hora_entrada_hoy.strftime('%H:%M') if self._hora_entrada_hoy else '?'}"
                estado_s = "✅" if salida_ya_hecha  else f"⏳ {self._hora_salida_hoy.strftime('%H:%M')  if self._hora_salida_hoy  else '?'}"
                print(f"\r[{ahora.strftime('%H:%M')}] Entrada: {estado_e} | Salida: {estado_s}   ", end='', flush=True)

            # ── Esperar 60 segundos antes de la siguiente comprobación ───
            time.sleep(60)


# ============================================================
# 🚀 Punto de Entrada
# ============================================================

def main():
    """Punto de entrada principal."""
    auto_fichaje = AutoFichaje()
    auto_fichaje.ejecutar_continuo()


if __name__ == "__main__":
    main()

