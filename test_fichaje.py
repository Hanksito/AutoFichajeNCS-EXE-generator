# -*- coding: utf-8 -*-
"""
Script de prueba COMPLETO para NCS Clock
Prueba: Login → Fichaje → Registro CSV
"""

import sys
import os
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


def test_fichaje_completo():
    """Prueba completa: Login → Fichaje → CSV."""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       🧪 TEST COMPLETO - NCS Clock                          ║")
    print("║       Login → Fichaje → Registro CSV                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Obtener credenciales
    usuario = os.getenv("NCS_USUARIO", "")
    password = os.getenv("NCS_PASSWORD", "")
    
    if not usuario or not password:
        print("❌ ERROR: No se encontraron credenciales en el archivo .env")
        print()
        print("Configura NCS_USUARIO y NCS_PASSWORD en el archivo .env")
        return False
    
    print(f"📋 Usuario: {usuario}")
    print(f"📋 Password: {'*' * len(password)}")
    print()
    
    # Inicializar logger CSV
    logger = FichajeCSVLogger("fichajes.csv")
    print("📊 Logger CSV inicializado")
    print()
    
    # Configurar Chrome
    print("🌐 Configurando navegador Chrome...")
    opciones = Options()
    
    # Modo headless (invisible)
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,768")
    
    # Opciones anti-detección
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("useAutomationExtension", False)
    
    driver = None
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opciones)
        
        # Eliminar navigator.webdriver
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        
        print("✅ Navegador abierto")
        print()
        
        # Paso 1: Navegar a la página de fichaje
        url = "https://clock.ncs.es/ClienteReloj/DoTicada"
        print(f"📄 Navegando a {url}...")
        driver.get(url)
        
        import time
        time.sleep(3)
        print("✅ Página cargada")
        print()
        
        # Paso 2: Login (si es necesario)
        resultado_login = ncs_login.realizar_login(driver, usuario, password)
        
        if not resultado_login["success"]:
            print("❌ LOGIN FALLIDO")
            print(f"   {resultado_login['mensaje']}")
            return False
        
        print()
        print("✅ LOGIN EXITOSO")
        print()
        
        # Paso 3: Realizar fichaje
        resultado_fichaje = ncs_fichaje.realizar_fichaje(driver)
        
        print()
        print("=" * 60)
        
        if resultado_fichaje["success"]:
            print("✅ ¡FICHAJE EXITOSO!")
            print(f"   Tipo: {resultado_fichaje['tipo']}")
            print(f"   Hora: {resultado_fichaje['hora_fichaje']}")
            print(f"   Presencia: {resultado_fichaje['presencia']}")
            print(f"   Jornada: {resultado_fichaje['jornada']}")
            
            # Paso 4: Registrar en CSV
            print()
            print("📝 Registrando en CSV...")
            
            logger.registrar_fichaje(
                tipo=resultado_fichaje["tipo"],
                hora=resultado_fichaje["hora_fichaje"],
                presencia=resultado_fichaje.get("presencia", ""),
                jornada=resultado_fichaje.get("jornada", ""),
                extra=resultado_fichaje.get("extra", ""),
                observaciones="Fichaje automático exitoso"
            )
            
            print("✅ Registro CSV completado")
            print()
            print("=" * 60)
            print()
            
            # Mostrar resumen del día
            registro_hoy = logger.obtener_registro_hoy()
            if registro_hoy:
                print("📊 RESUMEN DEL DÍA:")
                print(f"   Fecha: {registro_hoy['fecha']}")
                print(f"   Entrada: {registro_hoy['hora_entrada'] or 'Pendiente'}")
                print(f"   Salida: {registro_hoy['hora_salida'] or 'Pendiente'}")
                print(f"   Total horas: {registro_hoy['total_horas'] or 'En curso'}")
                print(f"   {registro_hoy['extra_ausencia']}")
            
            print()
            return True
        else:
            print("❌ FICHAJE FALLIDO")
            print(f"   {resultado_fichaje['mensaje']}")
            
            # Registrar el fallo en CSV
            logger.registrar_fichaje(
                tipo=resultado_fichaje["tipo"],
                hora="",
                observaciones=f"ERROR: {resultado_fichaje['mensaje']}"
            )
            
            return False
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
        
    finally:
        if driver:
            print()
            print("🔒 Cerrando navegador...")
            driver.quit()
            print("✅ Navegador cerrado")


if __name__ == "__main__":
    print()
    exito = test_fichaje_completo()
    print()
    
    if exito:
        print("=" * 60)
        print("✅ TEST COMPLETADO CON ÉXITO")
        print("=" * 60)
        print()
        print("💡 Revisa el archivo 'fichajes.csv' para ver el registro")
        print()
        sys.exit(0)
    else:
        print("=" * 60)
        print("❌ TEST FALLIDO")
        print("=" * 60)
        print()
        sys.exit(1)
