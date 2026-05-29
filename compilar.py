# -*- coding: utf-8 -*-
"""Compila Auto Fichaje NCS a un único .exe distribuible.

Uso:
    python compilar.py

Salida:
    dist\\AutoFichajeNCS.exe
"""
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    raiz = Path(__file__).parent

    args = [
        "pyinstaller",
        str(raiz / "app.py"),
        "--name=AutoFichajeNCS",
        "--onefile",
        "--windowed",
        f"--add-data={raiz / '.env.example'};.",
        "--clean",
        "--noconfirm",
    ]
    icono = raiz / "icono.ico"
    if icono.exists():
        args.append(f"--icon={icono}")

    print("Compilando con: " + " ".join(args))
    resultado = subprocess.run(args, cwd=str(raiz))
    if resultado.returncode != 0:
        print("[ERROR] Compilacion fallida.")
        return resultado.returncode

    exe = raiz / "dist" / "AutoFichajeNCS.exe"
    if exe.exists():
        print(f"[OK] .exe creado: {exe}")
        print(f"     Tamano: {exe.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print("[WARN] Compilacion termino pero el .exe no aparece.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
