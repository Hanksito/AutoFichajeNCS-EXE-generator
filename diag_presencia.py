# -*- coding: utf-8 -*-
"""Diagnóstico profundo: ¿qué muestra REALMENTE la página tras login?

Vuelca el estado de #presencia y compañía leídos de varias formas, espera
generosa a la AJAX, guarda screenshot y HTML para inspección humana.
"""
import sys
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import config
import ncs
from credenciales import CredencialesManager


def _dump_elem(driver, id_):
    try:
        el = driver.find_element(By.ID, id_)
    except NoSuchElementException:
        print(f"  #{id_:12} -> NO EXISTE en el DOM")
        return
    try:
        txt = el.text
    except Exception as e:
        txt = f"<err {e}>"
    try:
        js = driver.execute_script(
            "var e=document.getElementById(arguments[0]);"
            "return e? e.innerText : null;", id_)
    except Exception as e:
        js = f"<err {e}>"
    try:
        outer = el.get_attribute("outerHTML")
    except Exception as e:
        outer = f"<err {e}>"
    print(f"  #{id_:12} .text={txt!r:12} JS.innerText={js!r:12}")
    print(f"               outerHTML={outer!r}")


def main() -> int:
    u, p = CredencialesManager().cargar()
    if not u:
        u, p = config.USUARIO, config.PASSWORD
    print(f"[INFO] Usuario {u[:3]}***")

    driver = ncs.crear_navegador()
    if driver is None:
        print("[ERROR] navegador None"); return 1

    try:
        driver.get(config.URL_FICHAJE)
        time.sleep(2)
        ncs.realizar_login(driver, u, p)
        print(f"[INFO] URL tras login: {driver.current_url}")
        print(f"[INFO] Título: {driver.title}")

        # Alertas
        for sel in [".alert.alert-success", ".alert.alert-info", ".alert"]:
            try:
                a = driver.find_element(By.CSS_SELECTOR, sel)
                print(f"[ALERTA] {sel} visible={a.is_displayed()} text={a.text!r}")
            except NoSuchElementException:
                print(f"[ALERTA] {sel} -> no existe")

        # Vuelca presencia en t=0, 3s, 6s, 10s para ver si la AJAX la rellena
        for espera in [0, 3, 3, 4]:
            if espera:
                time.sleep(espera)
            t = "inicial" if espera == 0 else f"+{espera}s"
            print(f"\n=== Volcado presencia ({t}) ===")
            for id_ in ["presencia", "presencia2", "jornada", "jornada2"]:
                _dump_elem(driver, id_)

        # ¿Hay algún elemento con 'presencia' en el id?
        print("\n=== Todos los ids que contienen 'presencia' ===")
        try:
            ids = driver.execute_script(
                "return Array.from(document.querySelectorAll('[id*=presencia]'))"
                ".map(function(e){return e.id+'='+e.innerText;});")
            print(f"  {ids}")
        except Exception as e:
            print(f"  <err {e}>")

        # Guardar evidencia
        shot = "diag_screenshot.png"
        html = "diag_pagina.html"
        try:
            driver.save_screenshot(shot)
            print(f"\n[INFO] Screenshot -> {shot}")
        except Exception as e:
            print(f"[WARN] screenshot: {e}")
        try:
            with open(html, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"[INFO] HTML -> {html}")
        except Exception as e:
            print(f"[WARN] html: {e}")

        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
