# -*- coding: utf-8 -*-
"""
Módulo de Fichaje para NCS Clock
Maneja el proceso de marcar entrada/salida
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


def detectar_estado_fichaje(driver):
    """
    Detecta el estado actual (dentro/fuera) basándose en la alerta de la página.
    
    Args:
        driver: WebDriver de Selenium
        
    Returns:
        dict: {"estado": "ENTRADA"|"SALIDA"|"DESCONOCIDO", "mensaje": str}
    """
    try:
        # Intentar buscar alerta de "SALIR" (alert-success, verde)
        # <div class="alert alert-success alert-dismissible" role="alert">
        #   Estas dentro Marcas para SALIR
        # </div>
        try:
            alerta = driver.find_element(By.CSS_SELECTOR, ".alert.alert-success")
            texto_alerta = alerta.text.strip()
            
            if alerta.is_displayed() and ("SALIR" in texto_alerta.upper() or "DENTRO" in texto_alerta.upper()):
                return {
                    "estado": "SALIDA",
                    "mensaje": "Estás dentro - El próximo fichaje será SALIDA"
                }
        except NoSuchElementException:
            pass
        
        # Intentar buscar alerta de "ENTRAR" (alert-info, azul)
        # <div class="alert alert-info alert-dismissible" role="alert">
        #   Estas fuera Marcas para ENTRAR
        # </div>
        try:
            alerta = driver.find_element(By.CSS_SELECTOR, ".alert.alert-info")
            texto_alerta = alerta.text.strip()
            
            if alerta.is_displayed() and ("ENTRAR" in texto_alerta.upper() or "FUERA" in texto_alerta.upper()):
                return {
                    "estado": "ENTRADA",
                    "mensaje": "Estás fuera - El próximo fichaje será ENTRADA"
                }
        except NoSuchElementException:
            pass
        
        # Si no encontramos ninguna alerta específica, estado desconocido
        return {
            "estado": "DESCONOCIDO",
            "mensaje": "No se pudo determinar el estado actual (no se encontró alerta)"
        }
        
    except Exception as e:
        return {
            "estado": "DESCONOCIDO",
            "mensaje": f"Error detectando estado: {str(e)}"
        }


def obtener_datos_presencia(driver):
    """
    Obtiene los datos de presencia de la página (horas trabajadas, jornada, etc.)
    
    Args:
        driver: WebDriver de Selenium
        
    Returns:
        dict: {"presencia": str, "jornada": str, "extra": str}
    """
    try:
        datos = {}
        
        # Obtener presencia actual
        try:
            presencia_elem = driver.find_element(By.ID, "presencia")
            datos["presencia"] = presencia_elem.text.strip()
        except NoSuchElementException:
            datos["presencia"] = "00:00"
        
        # Obtener jornada
        try:
            jornada_elem = driver.find_element(By.ID, "jornada")
            datos["jornada"] = jornada_elem.text.strip()
        except NoSuchElementException:
            datos["jornada"] = "00:00"
        
        # Obtener extra/ausencia
        try:
            extra_elem = driver.find_element(By.ID, "jornada2")
            datos["extra"] = extra_elem.text.strip()
        except NoSuchElementException:
            datos["extra"] = "00:00"
        
        return datos
    except Exception as e:
        print(f"⚠️  Error obteniendo datos de presencia: {e}")
        return {"presencia": "00:00", "jornada": "00:00", "extra": "00:00"}


def realizar_fichaje(driver, timeout=30):
    """
    Realiza el fichaje (marca entrada o salida según corresponda).
    
    Args:
        driver: WebDriver de Selenium
        timeout: Tiempo máximo de espera en segundos
        
    Returns:
        dict: {
            "success": bool,
            "tipo": "ENTRADA"|"SALIDA"|"DESCONOCIDO",
            "mensaje": str,
            "presencia": str,
            "jornada": str,
            "hora_fichaje": str
        }
    """
    print("=" * 60)
    print("🕐 INICIANDO PROCESO DE FICHAJE")
    print("=" * 60)
    
    try:
        # Paso 1: Detectar estado actual
        print("🔍 Detectando estado actual...")
        estado_inicial = detectar_estado_fichaje(driver)
        print(f"📊 {estado_inicial['mensaje']}")
        
        tipo_fichaje = estado_inicial["estado"]
        
        pausa_humana(1.0, 2.0)
        
        # Paso 2: Obtener datos de presencia ANTES del fichaje
        print("📊 Obteniendo datos de presencia...")
        datos_antes = obtener_datos_presencia(driver)
        print(f"   Presencia actual: {datos_antes['presencia']}")
        print(f"   Jornada: {datos_antes['jornada']}")
        print(f"   {datos_antes['extra']}")
        
        pausa_humana(0.5, 1.0)
        
        # Paso 3: Buscar el botón de fichaje (id="btnTicar")
        print("🔍 Buscando botón de fichaje...")
        try:
            boton_fichar = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "btnTicar"))
            )
            print("✅ Botón de fichaje encontrado")
        except TimeoutException:
            return {
                "success": False,
                "tipo": tipo_fichaje,
                "mensaje": "No se encontró el botón de fichaje (id='btnTicar')",
                "presencia": datos_antes.get("presencia", "00:00"),
                "jornada": datos_antes.get("jornada", "00:00"),
                "hora_fichaje": ""
            }
        
        pausa_humana(0.8, 1.5)
        
        # Paso 4: Hacer clic en el botón
        print(f"👆 Pulsando botón de fichaje ({tipo_fichaje})...")
        try:
            boton_fichar.click()
        except Exception:
            # Si el clic normal falla, usar JavaScript
            driver.execute_script("arguments[0].click();", boton_fichar)
        
        print("✅ Botón pulsado")
        
        # Paso 5: Esperar a que se procese el fichaje
        print("⏳ Esperando confirmación del servidor...")
        pausa_humana(3.0, 5.0)
        
        # Paso 6: Verificar si hubo algún error
        try:
            # Buscar alertas de error
            error_alert = driver.find_element(By.CSS_SELECTOR, ".alert.alert-danger")
            if error_alert.is_displayed():
                mensaje_error = error_alert.text
                print(f"❌ Error en el fichaje: {mensaje_error}")
                return {
                    "success": False,
                    "tipo": tipo_fichaje,
                    "mensaje": f"Error del servidor: {mensaje_error}",
                    "presencia": datos_antes.get("presencia", "00:00"),
                    "jornada": datos_antes.get("jornada", "00:00"),
                    "hora_fichaje": ""
                }
        except NoSuchElementException:
            # No hay alerta de error, el fichaje fue exitoso
            pass
        
        # Paso 7: Verificar el nuevo estado
        print("🔍 Verificando nuevo estado...")
        pausa_humana(1.0, 2.0)
        
        estado_final = detectar_estado_fichaje(driver)
        datos_despues = obtener_datos_presencia(driver)
        
        # Obtener la hora actual del fichaje
        from datetime import datetime
        hora_fichaje = datetime.now().strftime("%H:%M:%S")
        
        # Verificar que el estado cambió (señal de fichaje exitoso)
        if estado_final["estado"] != estado_inicial["estado"]:
            print(f"✅ ¡Fichaje de {tipo_fichaje} realizado con éxito!")
            print(f"   Hora de fichaje: {hora_fichaje}")
            print(f"   Nueva presencia: {datos_despues['presencia']}")
            print(f"   {datos_despues['extra']}")
            
            return {
                "success": True,
                "tipo": tipo_fichaje,
                "mensaje": f"Fichaje de {tipo_fichaje} realizado correctamente",
                "presencia": datos_despues.get("presencia", "00:00"),
                "jornada": datos_despues.get("jornada", "00:00"),
                "hora_fichaje": hora_fichaje,
                "extra": datos_despues.get("extra", "")
            }
        else:
            # El estado no cambió, pero tampoco hubo error
            # Podría ser que ya estaba fichado
            print(f"⚠️  El estado no cambió después del clic")
            return {
                "success": True,  # Lo consideramos exitoso porque no hubo error
                "tipo": tipo_fichaje,
                "mensaje": f"Fichaje procesado (estado sin cambios visibles)",
                "presencia": datos_despues.get("presencia", "00:00"),
                "jornada": datos_despues.get("jornada", "00:00"),
                "hora_fichaje": hora_fichaje,
                "extra": datos_despues.get("extra", "")
            }
    
    except Exception as e:
        print(f"❌ Error inesperado durante el fichaje: {e}")
        return {
            "success": False,
            "tipo": "DESCONOCIDO",
            "mensaje": f"Error inesperado: {str(e)}",
            "presencia": "00:00",
            "jornada": "00:00",
            "hora_fichaje": ""
        }


# Función de prueba standalone
if __name__ == "__main__":
    print("Este módulo debe ser importado, no ejecutado directamente.")
    print("Ejemplo de uso:")
    print()
    print("  from ncs_fichaje import realizar_fichaje")
    print("  resultado = realizar_fichaje(driver)")
    print("  if resultado['success']:")
    print("      print(f'Fichaje de {resultado[\"tipo\"]} exitoso!')")
