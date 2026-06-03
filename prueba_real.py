# -*- coding: utf-8 -*-
"""Prueba de integración REAL contra clock.ncs.es.

Replica las condiciones de producción (Chrome headless) y demuestra el fix:
el bot confía en la ALERTA (señal autoritativa de NCS) en vez de cruzarla
con #presencia, que puede valer 00:00 de forma legítima.

Uso:
    python prueba_real.py            # solo diagnóstico, NO ficha
    python prueba_real.py --ficha    # además ficha de verdad (toggle)

Nunca imprime la contraseña.
"""
import sys
import time

import config
import ncs
from credenciales import CredencialesManager


def _cargar_credenciales():
    u, p = CredencialesManager().cargar()
    if not u:
        u, p = config.USUARIO, config.PASSWORD
    return u, p


def main() -> int:
    ficha = "--ficha" in sys.argv

    usuario, password = _cargar_credenciales()
    if not usuario or not password:
        print("[ERROR] No hay credenciales en config.dat ni en .env.")
        return 1
    print(f"[INFO] Usuario: {usuario[:3]}***  (contraseña oculta)")

    print("[INFO] Abriendo Chrome headless (igual que producción)...")
    driver = ncs.crear_navegador()
    if driver is None:
        print("[ERROR] No se pudo crear el navegador.")
        return 1

    try:
        print(f"[INFO] Navegando a {config.URL_FICHAJE}")
        driver.get(config.URL_FICHAJE)
        time.sleep(2)

        print("[INFO] Login...")
        ok = ncs.realizar_login(driver, usuario, password)
        print(f"[INFO] Login {'OK' if ok else 'FALLIDO'}")
        if not ok:
            print("[ERROR] Login falló. Revisa credenciales.")
            return 1

        # ── Demostración del bug/fix ───────────────────────────────
        # 1) Lectura INMEDIATA de presencia = lo que veía el código VIEJO.
        accion_inmediata = ncs._detectar_estado_una_vez(driver)
        presencia_inmediata = ncs._obtener_presencia(driver)
        print("\n=== LECTURA INMEDIATA (código viejo) ===")
        print(f"  accion    = {accion_inmediata}")
        print(f"  presencia = {presencia_inmediata}  <- si es 00:00 aquí, el viejo abortaba")

        # 2) Lectura con el FIX (espera a la AJAX + recarga si hace falta).
        estado = ncs.leer_estado_seguro(driver)
        print("\n=== LECTURA SEGURA (código nuevo, con el fix) ===")
        print(f"  accion_siguiente = {estado.accion_siguiente}")
        print(f"  presencia_actual = {estado.presencia_actual}")
        print(f"  coherente        = {estado.coherente}")

        if estado.coherente:
            print("\n[OK] Estado coherente: el bot puede fichar sin abortar. FIX FUNCIONA.")
        else:
            print("\n[WARN] Estado incoherente incluso tras el fix. Revisar.")

        # ── Fichaje real opcional ──────────────────────────────────
        if ficha:
            tipo = estado.accion_siguiente
            if tipo == "DESCONOCIDO":
                print("[WARN] Estado DESCONOCIDO, no ficho por seguridad.")
            else:
                print(f"\n[INFO] Fichando de verdad (tipo detectado: {tipo})...")
                res = ncs.realizar_fichaje(driver, tipo_esperado=tipo)
                print(f"  success = {res.success}")
                print(f"  saltado = {res.saltado}")
                print(f"  hora    = {res.hora_fichaje}")
                print(f"  mensaje = {res.mensaje}")
                # Releer para confirmar el cambio de estado
                time.sleep(2)
                estado2 = ncs.leer_estado_seguro(driver)
                print(f"\n[INFO] Estado tras fichar: accion={estado2.accion_siguiente}, "
                      f"presencia={estado2.presencia_actual}, coherente={estado2.coherente}")
                if estado2.accion_siguiente != tipo:
                    print("[OK] El estado cambio tras pulsar -> el fichaje REGISTRO.")
                else:
                    print("[WARN] El estado no cambio. Puede que no registrara.")
        else:
            print("\n[INFO] Modo solo-diagnóstico. Lanza con --ficha para fichar de verdad.")

        return 0
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
