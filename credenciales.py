# -*- coding: utf-8 -*-
"""Gestión de credenciales del usuario.

Almacena usuario/contraseña ofuscados en base64 en
%LOCALAPPDATA%\\AutoFichajeNCS\\config.dat por defecto.

Nota: base64 NO es cifrado real, solo evita lectura casual.
"""
import base64
import json
from pathlib import Path


class CredencialesManager:
    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path.home() / "AppData" / "Local" / "AutoFichajeNCS"
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.dat"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _cod(texto: str) -> str:
        return base64.b64encode(texto.encode("utf-8")).decode("utf-8")

    @staticmethod
    def _dec(texto: str) -> str:
        return base64.b64decode(texto.encode("utf-8")).decode("utf-8")

    def guardar(self, usuario: str, password: str) -> None:
        datos = {"u": self._cod(usuario), "p": self._cod(password)}
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(datos, f)

    def cargar(self) -> tuple[str | None, str | None]:
        if not self.config_file.exists():
            return None, None
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            return self._dec(d["u"]), self._dec(d["p"])
        except Exception:
            return None, None

    def eliminar(self) -> None:
        try:
            self.config_file.unlink(missing_ok=True)
        except Exception:
            pass
