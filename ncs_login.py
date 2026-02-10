# -*- coding: utf-8 -*-
"""
Módulo de Login para NCS Clock
Maneja la autenticación en el sistema NCS Clock
"""

import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def pausa_humana(minimo=0.5, maximo=1.5):
    """Pausa aleatoria para simular comportamiento humano."""
    tiempo = random.uniform(minimo, maximo)
    time.sleep(tiempo)


def escribir_como_humano(elemento, texto):
    """
    Escribe texto en un campo de forma humana (carácter por carácter).
    
    Args:
        elemento: WebElement donde escribir
        texto: Texto a escribir
    """
    elemento.clear()
    pausa_humana(0.3, 0.7)
    
    for char in texto:
        elemento.send_keys(char)
        # Velocidad de escritura humana: 50-150ms por carácter
        time.sleep(random.uniform(0.05, 0.15))
    
    pausa_humana(0.2, 0.5)


def detectar_modal_login(driver, timeout=5):
    """
    Detecta si el modal de login está visible.
    
    Args:
        driver: WebDriver de Selenium
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        bool: True si el modal está visible, False si no
    """
    try:
        # Buscar el modal con id="myModal" y class="modal fade in" (visible)
        modal = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#myModal.modal.fade.in"))
        )
        
        # Verificar que el modal esté realmente visible (display: block)
        is_visible = modal.is_displayed()
        
        if is_visible:
            print("✅ Modal de login detectado")
            return True
        else:
            print("⚠️  Modal de login existe pero no está visible")
            return False
            
    except (TimeoutException, NoSuchElementException):
        print("ℹ️  No se detectó modal de login (probablemente ya estás logueado)")
        return False


def realizar_login(driver, usuario, password, timeout=30):
    """
    Realiza el proceso completo de login en NCS Clock.
    
    Args:
        driver: WebDriver de Selenium
        usuario: Nombre de usuario
        password: Contraseña
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        dict: {"success": bool, "mensaje": str}
    """
    print("=" * 60)
    print("🔐 INICIANDO PROCESO DE LOGIN")
    print("=" * 60)
    
    try:
        # Paso 1: Detectar si hay modal de login
        if not detectar_modal_login(driver, timeout=5):
            return {
                "success": True,
                "mensaje": "Ya estás logueado (no se detectó modal de login)"
            }
        
        # Paso 2: Esperar a que el modal esté completamente cargado
        print("⏳ Esperando a que el modal de login esté listo...")
        pausa_humana(1.0, 2.0)
        
        # Paso 3: Buscar campo de usuario (id="tbUserName")
        print("🔍 Buscando campo de usuario...")
        try:
            campo_usuario = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "tbUserName"))
            )
            print("✅ Campo de usuario encontrado")
        except TimeoutException:
            return {
                "success": False,
                "mensaje": "No se encontró el campo de usuario (id='tbUserName')"
            }
        
        # Paso 4: Buscar campo de contraseña (id="tbPassword")
        print("🔍 Buscando campo de contraseña...")
        try:
            campo_password = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "tbPassword"))
            )
            print("✅ Campo de contraseña encontrado")
        except TimeoutException:
            return {
                "success": False,
                "mensaje": "No se encontró el campo de contraseña (id='tbPassword')"
            }
        
        # Paso 5: Escribir usuario
        print(f"⌨️  Escribiendo usuario: {usuario}")
        escribir_como_humano(campo_usuario, usuario)
        print("✅ Usuario escrito correctamente")
        
        pausa_humana(0.5, 1.0)
        
        # Paso 6: Escribir contraseña
        print("⌨️  Escribiendo contraseña: " + "*" * len(password))
        escribir_como_humano(campo_password, password)
        print("✅ Contraseña escrita correctamente")
        
        pausa_humana(0.8, 1.5)
        
        # Paso 7: Buscar y pulsar botón de login (id="LoginBtn")
        print("🔍 Buscando botón de login...")
        try:
            boton_login = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "LoginBtn"))
            )
            print("✅ Botón de login encontrado")
        except TimeoutException:
            return {
                "success": False,
                "mensaje": "No se encontró el botón de login (id='LoginBtn')"
            }
        
        pausa_humana(0.5, 1.0)
        
        print("👆 Pulsando botón de login...")
        try:
            boton_login.click()
        except Exception:
            # Si el clic normal falla, usar JavaScript
            driver.execute_script("arguments[0].click();", boton_login)
        
        print("✅ Botón de login pulsado")
        
        # Paso 8: Esperar a que el modal desaparezca (señal de login exitoso)
        print("⏳ Esperando respuesta del servidor...")
        pausa_humana(2.0, 4.0)
        
        # Verificar si el modal sigue visible (login fallido)
        try:
            # Buscar el div con class="failed" que aparece en caso de error
            error_msg = driver.find_element(By.CSS_SELECTOR, "#messenger .failed")
            if error_msg.is_displayed():
                mensaje_error = error_msg.text
                print(f"❌ Login fallido: {mensaje_error}")
                return {
                    "success": False,
                    "mensaje": f"Credenciales incorrectas: {mensaje_error}"
                }
        except NoSuchElementException:
            # No hay mensaje de error, el login fue exitoso
            pass
        
        # Verificar si el modal desapareció (login exitoso)
        try:
            # Esperar a que el modal ya no esté visible
            WebDriverWait(driver, 10).until_not(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#myModal.modal.fade.in"))
            )
            print("✅ Modal de login cerrado - Login exitoso")
            
            pausa_humana(1.0, 2.0)
            
            return {
                "success": True,
                "mensaje": "Login realizado correctamente"
            }
            
        except TimeoutException:
            # El modal sigue visible después de 10 segundos
            print("⚠️  El modal de login sigue visible después del clic")
            
            # Verificar de nuevo si hay mensaje de error
            try:
                error_msg = driver.find_element(By.CSS_SELECTOR, "#messenger .failed")
                if error_msg.is_displayed():
                    return {
                        "success": False,
                        "mensaje": f"Error de login: {error_msg.text}"
                    }
            except NoSuchElementException:
                pass
            
            return {
                "success": False,
                "mensaje": "El modal de login no se cerró (posible error de red o credenciales)"
            }
    
    except Exception as e:
        print(f"❌ Error inesperado durante el login: {e}")
        return {
            "success": False,
            "mensaje": f"Error inesperado: {str(e)}"
        }


def verificar_sesion_activa(driver):
    """
    Verifica si hay una sesión activa (no aparece el modal de login).
    
    Args:
        driver: WebDriver de Selenium
        
    Returns:
        bool: True si hay sesión activa, False si necesita login
    """
    # Si no hay modal de login visible, la sesión está activa
    return not detectar_modal_login(driver, timeout=3)


# Función de prueba standalone
if __name__ == "__main__":
    print("Este módulo debe ser importado, no ejecutado directamente.")
    print("Ejemplo de uso:")
    print()
    print("  from ncs_login import realizar_login")
    print("  resultado = realizar_login(driver, 'mi_usuario', 'mi_password')")
    print("  if resultado['success']:")
    print("      print('Login exitoso!')")
    print("  else:")
    print("      print(f'Error: {resultado[\"mensaje\"]}')")
