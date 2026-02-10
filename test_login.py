# -*- coding: utf-8 -*-
"""
Script de prueba para el módulo de login de NCS Clock
Úsalo para verificar que las credenciales funcionan correctamente
"""

import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Importar el módulo de login
import ncs_login

# Cargar variables de entorno
load_dotenv()

def test_login():
    """Prueba el módulo de login."""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       🧪 TEST DE LOGIN - NCS Clock                          ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    # Obtener credenciales del .env
    usuario = os.getenv("NCS_USUARIO", "")
    password = os.getenv("NCS_PASSWORD", "")
    
    if not usuario or not password:
        print("❌ ERROR: No se encontraron credenciales en el archivo .env")
        print()
        print("Por favor:")
        print("1. Copia el archivo .env.example como .env")
        print("2. Edita .env y rellena NCS_USUARIO y NCS_PASSWORD")
        print()
        return False
    
    print(f"📋 Usuario: {usuario}")
    print(f"📋 Password: {'*' * len(password)}")
    print()
    
    # Configurar Chrome
    print("🌐 Configurando navegador Chrome...")
    opciones = Options()
    
    # Modo headless (navegador invisible)
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,768")
    
    # Opciones anti-detección
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("useAutomationExtension", False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opciones)
        
        # Eliminar la propiedad navigator.webdriver
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
        
        driver.set_window_size(1366, 768)
        print("✅ Navegador abierto correctamente")
        print()
        
        # Navegar a la página de fichaje
        url = "https://clock.ncs.es/ClienteReloj/DoTicada"
        print(f"📄 Navegando a {url}...")
        driver.get(url)
        
        # Esperar a que la página cargue
        import time
        time.sleep(3)
        print("✅ Página cargada")
        print()
        
        # Intentar login
        resultado = ncs_login.realizar_login(driver, usuario, password)
        
        print()
        print("=" * 60)
        if resultado["success"]:
            print("✅ ¡LOGIN EXITOSO!")
            print(f"   {resultado['mensaje']}")
            print("=" * 60)
            print()
            print("🎉 El módulo de login funciona correctamente")
            print()
            print("⏸️  El navegador se mantendrá abierto 10 segundos para que veas el resultado...")
            time.sleep(10)
            
            return True
        else:
            print("❌ LOGIN FALLIDO")
            print(f"   {resultado['mensaje']}")
            print("=" * 60)
            print()
            print("💡 Verifica que las credenciales en .env sean correctas")
            print()
            print("⏸️  El navegador se mantendrá abierto 15 segundos para que veas el error...")
            time.sleep(15)
            
            return False
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        return False
        
    finally:
        if 'driver' in locals():
            print("🔒 Cerrando navegador...")
            driver.quit()
            print("✅ Navegador cerrado")


if __name__ == "__main__":
    print()
    exito = test_login()
    print()
    
    if exito:
        print("✅ TEST COMPLETADO CON ÉXITO")
        sys.exit(0)
    else:
        print("❌ TEST FALLIDO")
        sys.exit(1)
