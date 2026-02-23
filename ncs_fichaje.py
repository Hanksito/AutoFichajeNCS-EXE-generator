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


def realizar_fichaje(driver, tipo_esperado="", timeout=30):
    """
    Realiza el fichaje verificando primero el estado real de la web.

    La lógica es:
      - Si tipo_esperado == "ENTRADA" → la web debe indicar FUERA.
        Si indica DENTRO significa que alguien ya fichó → NO fichar.
      - Si tipo_esperado == "SALIDA"  → la web debe indicar DENTRO.
        Si indica FUERA significa que ya se salió → NO fichar.

    Args:
        driver:         WebDriver de Selenium
        tipo_esperado:  "ENTRADA" o "SALIDA" (obligatorio para seguridad)
        timeout:        Tiempo máximo de espera en segundos

    Returns:
        dict: {
            "success":      bool,
            "tipo":         str,
            "mensaje":      str,
            "presencia":    str,
            "jornada":      str,
            "hora_fichaje": str,
            "saltado":      bool  ← True si se omitió porque ya estaba hecho
        }
    """
    print("=" * 60)
    print("🕐 INICIANDO PROCESO DE FICHAJE")
    print("=" * 60)

    def resultado_saltado(motivo):
        return {
            "success": True,   # no es un error, simplemente no era necesario fichar
            "tipo": tipo_esperado,
            "mensaje": motivo,
            "presencia": "",
            "jornada": "",
            "hora_fichaje": "",
            "saltado": True,
        }

    def resultado_error(motivo):
        return {
            "success": False,
            "tipo": tipo_esperado,
            "mensaje": motivo,
            "presencia": "",
            "jornada": "",
            "hora_fichaje": "",
            "saltado": False,
        }

    try:
        # ── Paso 1: Leer estado real de la web ───────────────────────
        print("🔍 Leyendo estado actual de la web...")
        estado_web = detectar_estado_fichaje(driver)
        estado_actual = estado_web["estado"]   # "ENTRADA" | "SALIDA" | "DESCONOCIDO"
        print(f"📊 Estado web: {estado_web['mensaje']}")

        # ── Paso 2: Verificar si el fichaje tiene sentido ─────────────
        if tipo_esperado == "ENTRADA":
            if estado_actual == "SALIDA":
                # Web dice DENTRO → alguien ya fichó entrada
                motivo = "Ya estás DENTRO (alguien fichó antes). Se omite el fichaje de ENTRADA."
                print(f"⏭️  {motivo}")
                return resultado_saltado(motivo)
            elif estado_actual == "DESCONOCIDO":
                print("⚠️  Estado desconocido, se intentará fichar igualmente")

        elif tipo_esperado == "SALIDA":
            if estado_actual == "ENTRADA":
                # Web dice FUERA → ya se salió o nadie entró
                motivo = "Ya estás FUERA (salida ya realizada o no había entrada). Se omite el fichaje de SALIDA."
                print(f"⏭️  {motivo}")
                return resultado_saltado(motivo)
            elif estado_actual == "DESCONOCIDO":
                print("⚠️  Estado desconocido, se intentará fichar igualmente")

        # ── Paso 3: Datos de presencia antes del fichaje ──────────────
        print("📊 Obteniendo datos de presencia...")
        datos_antes = obtener_datos_presencia(driver)
        print(f"   Presencia actual: {datos_antes['presencia']}")
        print(f"   Jornada: {datos_antes['jornada']}")

        pausa_humana(0.8, 1.5)

        # ── Paso 4: Buscar el botón de fichaje ────────────────────────
        print("🔍 Buscando botón de fichaje...")
        try:
            boton_fichar = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "btnTicar"))
            )
            print("✅ Botón de fichaje encontrado")
        except TimeoutException:
            return resultado_error("No se encontró el botón de fichaje (id='btnTicar')")

        pausa_humana(0.8, 1.5)

        # ── Paso 5: Clic en el botón ──────────────────────────────────
        print(f"👆 Pulsando botón de fichaje ({tipo_esperado})...")
        try:
            boton_fichar.click()
        except Exception:
            driver.execute_script("arguments[0].click();", boton_fichar)
        print("✅ Botón pulsado")

        # ── Paso 6: Esperar confirmación ──────────────────────────────
        print("⏳ Esperando confirmación del servidor...")
        pausa_humana(3.0, 5.0)

        # ── Paso 7: Verificar errores del servidor ────────────────────
        try:
            error_alert = driver.find_element(By.CSS_SELECTOR, ".alert.alert-danger")
            if error_alert.is_displayed():
                return resultado_error(f"Error del servidor: {error_alert.text}")
        except NoSuchElementException:
            pass

        # ── Paso 8: Confirmar que el estado cambió ────────────────────
        print("🔍 Verificando nuevo estado...")
        pausa_humana(1.0, 2.0)

        from datetime import datetime
        hora_fichaje = datetime.now().strftime("%H:%M:%S")

        estado_final = detectar_estado_fichaje(driver)
        datos_despues = obtener_datos_presencia(driver)

        if estado_final["estado"] != estado_actual:
            print(f"✅ ¡Fichaje de {tipo_esperado} realizado con éxito!")
            print(f"   Hora de fichaje: {hora_fichaje}")
            print(f"   Nueva presencia: {datos_despues['presencia']}")
            return {
                "success": True,
                "tipo": tipo_esperado,
                "mensaje": f"Fichaje de {tipo_esperado} realizado correctamente",
                "presencia": datos_despues.get("presencia", ""),
                "jornada": datos_despues.get("jornada", ""),
                "hora_fichaje": hora_fichaje,
                "extra": datos_despues.get("extra", ""),
                "saltado": False,
            }
        else:
            # Estado no cambió pero tampoco hubo error → aceptar
            print(f"⚠️  El estado no cambió visualmente, pero no hubo error")
            return {
                "success": True,
                "tipo": tipo_esperado,
                "mensaje": "Fichaje procesado (sin cambio de estado visible)",
                "presencia": datos_despues.get("presencia", ""),
                "jornada": datos_despues.get("jornada", ""),
                "hora_fichaje": hora_fichaje,
                "extra": datos_despues.get("extra", ""),
                "saltado": False,
            }

    except Exception as e:
        return resultado_error(f"Error inesperado: {str(e)}") 


# Módulo de fichaje - debe importarse, no ejecutarse directamente
if __name__ == "__main__":
    print("Este módulo debe ser importado, no ejecutado directamente.")
    print("Uso:  from ncs_fichaje import realizar_fichaje")

