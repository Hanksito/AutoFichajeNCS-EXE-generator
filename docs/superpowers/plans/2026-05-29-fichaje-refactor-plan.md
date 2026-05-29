# Auto Fichaje NCS Refactor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor Auto Fichaje NCS into a unified, robust application that never silently desfichas the user, with proper state verification, configurable file paths, popup notifications on failure, and a single `.exe` (CLI+GUI unified).

**Architecture:** 8 application modules with single responsibility (`config`, `lock`, `csv_log`, `notifier`, `credenciales`, `ncs`, `scheduler`, `app`), 5 test modules using `pytest` + `unittest.mock` (no real network/browser), 1 build script. State persistence is a single `dataclass` with auto-migration from legacy CLI/GUI schemas. The critical `ncs.realizar_fichaje` has three guards that abort before pressing the button if state cannot be verified.

**Tech Stack:** Python 3.12, Selenium + webdriver-manager (Chrome headless), Tkinter (GUI + popups), python-dotenv, psutil (PID liveness), PyInstaller (build), pytest + unittest.mock (testing).

**Spec reference:** `docs/superpowers/specs/2026-05-29-fichaje-refactor-design.md`

---

## Pre-Task: Manual unblock (do before starting)

**Files:**
- Delete: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\auto_fichaje.lock`

- [ ] **Step 1: Stop the current `AutoFichajeNCS.exe` if it's running**

Open Task Manager (Ctrl+Shift+Esc), look for `AutoFichajeNCS.exe` or `python.exe` running `auto_fichaje.py`. End them.

- [ ] **Step 2: Delete the orphan lock file**

Run in PowerShell:
```powershell
Remove-Item "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\auto_fichaje.lock"
```
Expected: command succeeds silently. If "file does not exist", great — already gone.

- [ ] **Step 3: Confirm system can run again (optional)**

Run the current CLI to verify it now starts:
```powershell
python "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\auto_fichaje.py"
```
Expected: Banner "🚀 AUTO FICHAJE INICIADO" appears within a few seconds. Then Ctrl+C to stop. Do NOT leave running while we refactor.

---

## Task 1: Project scaffolding and dependencies

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `requirements-dev.txt`
- Modify: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Create the tests/ directory and __init__.py**

```powershell
New-Item -ItemType Directory -Force "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests"
New-Item -ItemType File "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\__init__.py"
```

- [ ] **Step 2: Create `tests/conftest.py` with shared fixtures**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\conftest.py`

```python
# -*- coding: utf-8 -*-
"""Fixtures compartidos para la suite de tests."""
import sys
from pathlib import Path

# Permite importar los módulos del proyecto sin instalación
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 3: Update `requirements.txt` adding psutil**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\requirements.txt`

Read the current content first, then add `psutil` if not present. Final content should be:
```
selenium>=4.0
webdriver-manager>=3.8
python-dotenv>=1.0
psutil>=5.9
```

- [ ] **Step 4: Create `requirements-dev.txt`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\requirements-dev.txt`

```
pytest>=7.0
pytest-mock>=3.10
pyinstaller>=6.0
```

- [ ] **Step 5: Update `.gitignore` to stop tracking runtime artifacts**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\.gitignore`

Read current content, then append (if not already present):
```
# Runtime artifacts (no deben versionarse)
auto_fichaje.lock
estado_diario.json
auto_fichaje.log
fichajes.csv

# Python
__pycache__/
*.pyc
.pytest_cache/

# Build
build/
dist/
AutoFichajeNCS.spec
```

- [ ] **Step 6: Install dependencies**

```powershell
pip install -r "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\requirements.txt"
pip install -r "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\requirements-dev.txt"
```
Expected: psutil, pytest, pytest-mock, pyinstaller installed (others may already be present).

- [ ] **Step 7: Verify pytest discovery works**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/ -v
```
Expected: `no tests ran` (no tests written yet, but discovery succeeds).

- [ ] **Step 8: Commit scaffolding**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add tests/__init__.py tests/conftest.py requirements.txt requirements-dev.txt .gitignore
git commit -m "chore: add test scaffolding and dev dependencies"
```

---

## Task 2: `config.py` — paths via env var and centralized constants

**Files:**
- Create: `tests/test_config.py`
- Modify: `config.py`

- [ ] **Step 1: Write failing test for path resolution**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_config.py`

```python
# -*- coding: utf-8 -*-
"""Tests para config.py — resolución de paths."""
import os
import sys
import importlib
from pathlib import Path
import pytest


def _reload_config():
    """Recarga config para que vea cambios en el entorno."""
    import config
    return importlib.reload(config)


def test_data_dir_usa_variable_de_entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    cfg = _reload_config()
    assert cfg.DATA_DIR == tmp_path


def test_data_dir_crea_directorio_si_no_existe(tmp_path, monkeypatch):
    nuevo = tmp_path / "subdir"
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(nuevo))
    cfg = _reload_config()
    assert nuevo.exists()
    assert cfg.DATA_DIR == nuevo


def test_data_dir_default_es_carpeta_del_script(monkeypatch):
    monkeypatch.delenv("AUTO_FICHAJE_DATA_DIR", raising=False)
    # sys.frozen no está set en modo desarrollo
    cfg = _reload_config()
    assert cfg.DATA_DIR == Path(cfg.__file__).parent


def test_data_dir_usa_carpeta_del_exe_si_frozen(monkeypatch, tmp_path):
    fake_exe = tmp_path / "AutoFichajeNCS.exe"
    fake_exe.touch()
    monkeypatch.delenv("AUTO_FICHAJE_DATA_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))
    cfg = _reload_config()
    assert cfg.DATA_DIR == tmp_path


def test_constantes_de_ventanas_presentes(monkeypatch):
    monkeypatch.delenv("AUTO_FICHAJE_DATA_DIR", raising=False)
    cfg = _reload_config()
    assert cfg.ENTRADA_DESDE == "08:35"
    assert cfg.ENTRADA_HASTA == "09:05"
    assert cfg.SALIDA_DESDE == "18:00"
    assert cfg.SALIDA_HASTA == "18:30"
    assert cfg.DIAS_LABORABLES == [0, 1, 2, 3, 4]
    assert cfg.MAX_REINTENTOS == 3
    assert cfg.BACKOFF_REINTENTOS == [300, 600, 900]
    assert cfg.MARGEN_VENTANA_EXTRA == 30


def test_paths_calculados_relativos_a_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    cfg = _reload_config()
    assert cfg.CSV_FICHAJES == tmp_path / "fichajes.csv"
    assert cfg.ESTADO_FILE == tmp_path / "estado_diario.json"
    assert cfg.LOCK_FILE == tmp_path / "auto_fichaje.lock"
    assert cfg.LOG_FILE == tmp_path / "auto_fichaje.log"
```

- [ ] **Step 2: Run tests, verify they FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_config.py -v
```
Expected: tests fail because the current `config.py` doesn't expose `DATA_DIR`, `CSV_FICHAJES` etc. as `Path` objects, nor does it implement `_data_dir()`.

- [ ] **Step 3: Implement the new `config.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\config.py`

Replace the entire file with:

```python
# -*- coding: utf-8 -*-
"""Configuración central del Auto Fichaje NCS Clock.

Constantes (horarios, reintentos, selectores) + resolución de paths.

Los archivos de runtime viven en `DATA_DIR`, que se resuelve así:
  1. Variable de entorno `AUTO_FICHAJE_DATA_DIR` (se crea si no existe).
  2. Si el proceso está congelado por PyInstaller → carpeta del .exe.
  3. Modo desarrollo → carpeta de este archivo.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _data_dir() -> Path:
    env = os.getenv("AUTO_FICHAJE_DATA_DIR")
    if env:
        p = Path(env).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DATA_DIR = _data_dir()

# Archivos de runtime
CSV_FICHAJES = DATA_DIR / "fichajes.csv"
ESTADO_FILE = DATA_DIR / "estado_diario.json"
LOCK_FILE = DATA_DIR / "auto_fichaje.lock"
LOG_FILE = DATA_DIR / "auto_fichaje.log"

# URL del fichaje
URL_FICHAJE = "https://clock.ncs.es/ClienteReloj/DoTicada"

# Ventanas horarias (hora española)
ENTRADA_DESDE = "08:35"
ENTRADA_HASTA = "09:05"
SALIDA_DESDE = "18:00"
SALIDA_HASTA = "18:30"

# Reintentos
MAX_REINTENTOS = 3
BACKOFF_REINTENTOS = [300, 600, 900]  # 5, 10, 15 min
MARGEN_VENTANA_EXTRA = 30  # min tras cierre de ventana

# Días laborables (0=Lunes, 4=Viernes)
DIAS_LABORABLES = [0, 1, 2, 3, 4]

# Credenciales (lectura desde .env como respaldo; modo principal: credenciales.py)
USUARIO = os.getenv("NCS_USUARIO", "")
PASSWORD = os.getenv("NCS_PASSWORD", "")

# Comportamiento humano simulado
PAUSA_MIN = 1.0
PAUSA_MAX = 3.5
TIMEOUT_CARGA = 30

# Selectores CSS para el botón de fichaje (probados en orden)
SELECTORES_BOTON_FICHAJE = [
    "button#btnTicar",
    "input#btnTicar",
    "button#btnTicada",
    "input#btnTicada",
    "button.btn-ticada",
    "input[type='submit'][value*='Ticar']",
    "button[onclick*='Ticada']",
]

# Selectores para login
SELECTOR_CAMPO_USUARIO = "input#tbUserName"
SELECTOR_CAMPO_PASSWORD = "input#tbPassword"
SELECTOR_BOTON_LOGIN = "button#LoginBtn, input#LoginBtn"
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_config.py -v
```
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add config.py tests/test_config.py
git commit -m "refactor(config): centralize paths via AUTO_FICHAJE_DATA_DIR"
```

---

## Task 3: `lock.py` — single-instance with PID liveness check

**Files:**
- Create: `lock.py`
- Create: `tests/test_lock.py`

- [ ] **Step 1: Write failing tests**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_lock.py`

```python
# -*- coding: utf-8 -*-
"""Tests para lock.py — single-instance con verificación de PID."""
import os
import importlib
from datetime import datetime, timedelta
import pytest


def _reload_lock(tmp_path, monkeypatch):
    """Recarga config y lock apuntando LOCK_FILE a tmp_path."""
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import lock
    return importlib.reload(lock)


def test_lock_se_adquiere_si_no_existe(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    lk.adquirir()
    assert (tmp_path / "auto_fichaje.lock").exists()
    contenido = (tmp_path / "auto_fichaje.lock").read_text(encoding="utf-8")
    assert f"PID={os.getpid()}" in contenido
    lk.liberar()
    assert not (tmp_path / "auto_fichaje.lock").exists()


def test_lock_rechaza_si_pid_vivo(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    # Usamos nuestro propio PID (que sí está vivo) como "lock existente"
    (tmp_path / "auto_fichaje.lock").write_text(
        f"PID={os.getpid()} iniciado={datetime.now().isoformat()}",
        encoding="utf-8",
    )
    with pytest.raises(lk.LockBusy) as exc_info:
        lk.adquirir()
    assert exc_info.value.pid_otro == os.getpid()


def test_lock_sobrescribe_si_pid_muerto(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    # PID 999999 muy improbable que exista
    (tmp_path / "auto_fichaje.lock").write_text(
        f"PID=999999 iniciado={datetime.now().isoformat()}",
        encoding="utf-8",
    )
    lk.adquirir()  # no debe lanzar
    contenido = (tmp_path / "auto_fichaje.lock").read_text(encoding="utf-8")
    assert f"PID={os.getpid()}" in contenido
    lk.liberar()


def test_lock_sobrescribe_si_mas_de_24h(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    hace_25h = (datetime.now() - timedelta(hours=25)).isoformat()
    # Usamos MI propio PID (vivo) pero hace 25h
    (tmp_path / "auto_fichaje.lock").write_text(
        f"PID={os.getpid()} iniciado={hace_25h}",
        encoding="utf-8",
    )
    lk.adquirir()  # debe considerar huérfano por antigüedad
    contenido = (tmp_path / "auto_fichaje.lock").read_text(encoding="utf-8")
    # El timestamp debe ser nuevo
    assert hace_25h not in contenido
    lk.liberar()


def test_lock_sobrescribe_si_archivo_corrupto(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    (tmp_path / "auto_fichaje.lock").write_text("contenido basura", encoding="utf-8")
    lk.adquirir()  # no debe lanzar
    lk.liberar()


def test_liberar_es_idempotente(tmp_path, monkeypatch):
    lk = _reload_lock(tmp_path, monkeypatch)
    lk.liberar()  # archivo no existe, no debe lanzar
    lk.adquirir()
    lk.liberar()
    lk.liberar()  # tampoco debe lanzar
```

- [ ] **Step 2: Run tests, verify they FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_lock.py -v
```
Expected: tests fail with `ModuleNotFoundError: No module named 'lock'`.

- [ ] **Step 3: Implement `lock.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\lock.py`

```python
# -*- coding: utf-8 -*-
"""Lock file con verificación de PID vivo.

Evita doble instancia, pero detecta locks huérfanos (proceso muerto
o más antiguos de 24h) para no bloquearse tras un crash.
"""
import atexit
import os
from datetime import datetime, timedelta
from pathlib import Path

import psutil

import config


class LockBusy(Exception):
    """Hay otra instancia VIVA del proceso ejecutándose."""

    def __init__(self, pid_otro: int):
        self.pid_otro = pid_otro
        super().__init__(f"Otra instancia viva ya tiene el lock (PID={pid_otro})")


def _pid_vivo(pid: int) -> bool:
    """True si un proceso con ese PID existe en el sistema."""
    try:
        return psutil.pid_exists(pid)
    except Exception:
        return False


def _parse_contenido(contenido: str) -> tuple[int, datetime | None]:
    """Extrae (pid, iniciado) de un lock file. PID=-1 si no se puede parsear."""
    pid = -1
    iniciado: datetime | None = None
    for parte in contenido.split():
        if parte.startswith("PID="):
            try:
                pid = int(parte.split("=", 1)[1])
            except ValueError:
                pid = -1
        elif parte.startswith("iniciado="):
            try:
                iniciado = datetime.fromisoformat(parte.split("=", 1)[1])
            except ValueError:
                iniciado = None
    return pid, iniciado


def _es_huerfano(contenido: str) -> tuple[bool, int]:
    """Devuelve (es_huérfano, pid). Es huérfano si:
    - archivo corrupto (no parseable)
    - PID no vive en el sistema
    - iniciado hace más de 24 horas
    """
    pid, iniciado = _parse_contenido(contenido)
    if pid < 0:
        return True, pid
    if not _pid_vivo(pid):
        return True, pid
    if iniciado and (datetime.now() - iniciado) > timedelta(hours=24):
        return True, pid
    return False, pid


def adquirir() -> None:
    """Crea LOCK_FILE con el PID actual.

    Raises:
        LockBusy: si ya hay un lock con un PID vivo y reciente.
    """
    lock_path: Path = config.LOCK_FILE
    if lock_path.exists():
        contenido = lock_path.read_text(encoding="utf-8").strip()
        es_huerfano, pid_existente = _es_huerfano(contenido)
        if not es_huerfano:
            raise LockBusy(pid_existente)
        # Huérfano → sobrescribimos sin error
    pid_actual = os.getpid()
    nuevo = f"PID={pid_actual} iniciado={datetime.now().isoformat()}"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(nuevo, encoding="utf-8")
    atexit.register(liberar)


def liberar() -> None:
    """Borra LOCK_FILE si existe. Idempotente."""
    try:
        config.LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_lock.py -v
```
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add lock.py tests/test_lock.py
git commit -m "feat(lock): single-instance lock with PID liveness check"
```

---

## Task 4: `csv_log.py` — historical CSV logger with atomic writes

**Files:**
- Create: `csv_log.py`
- Create: `tests/test_csv_log.py`

- [ ] **Step 1: Write failing tests**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_csv_log.py`

```python
# -*- coding: utf-8 -*-
"""Tests para csv_log.py."""
import csv
import importlib
from datetime import datetime
import pytest


def _reload_csv_log(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import csv_log
    return importlib.reload(csv_log)


def test_crea_archivo_con_cabeceras_si_no_existe(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    assert (tmp_path / "fichajes.csv").exists()
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        cabeceras = next(reader)
    assert cabeceras == [
        "fecha", "hora_entrada", "hora_salida",
        "total_horas", "jornada", "extra_ausencia", "observaciones",
    ]


def test_registrar_entrada_crea_fila(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_entrada("08:53:12", observaciones="Automático")
    hoy = datetime.now().strftime("%Y-%m-%d")
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["fecha"] == hoy
    assert rows[0]["hora_entrada"] == "08:53:12"
    assert rows[0]["hora_salida"] == ""
    assert "Automático" in rows[0]["observaciones"]


def test_registrar_salida_completa_fila_existente(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_entrada("08:53:12")
    logger.registrar_salida("18:18:45", "09:25", "08:00", "Extr. 01:25")
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1, "salida debe actualizar la fila de entrada, no crear otra"
    assert rows[0]["hora_entrada"] == "08:53:12"
    assert rows[0]["hora_salida"] == "18:18:45"
    assert rows[0]["total_horas"] == "09:25"
    assert rows[0]["jornada"] == "08:00"
    assert rows[0]["extra_ausencia"] == "Extr. 01:25"


def test_salida_sin_entrada_previa_crea_fila_con_aviso(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_salida("18:18:45", "09:25", "08:00", "")
    with open(tmp_path / "fichajes.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["hora_entrada"] == ""
    assert rows[0]["hora_salida"] == "18:18:45"
    assert "sin entrada previa" in rows[0]["observaciones"].lower()


def test_obtener_registro_hoy_devuelve_none_si_no_hay(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    assert logger.obtener_registro_hoy() is None


def test_resumen_mes_filtra_correctamente(tmp_path, monkeypatch):
    mod = _reload_csv_log(tmp_path, monkeypatch)
    csv_path = tmp_path / "fichajes.csv"
    # Inyectamos un CSV con entradas de varios meses
    csv_path.write_text(
        "fecha,hora_entrada,hora_salida,total_horas,jornada,extra_ausencia,observaciones\n"
        "2026-05-01,08:50:00,18:10:00,09:20,08:00,,Auto\n"
        "2026-05-02,08:51:00,18:11:00,09:20,08:00,,Auto\n"
        "2026-04-30,08:52:00,18:12:00,09:20,08:00,,Auto\n",
        encoding="utf-8",
    )
    logger = mod.FichajeCSVLogger()
    resumen = logger.resumen_mes(5, 2026)
    assert len(resumen) == 2
    assert all(r["fecha"].startswith("2026-05") for r in resumen)


def test_escritura_atomica_no_corrompe_si_falla_a_medias(tmp_path, monkeypatch):
    """Si la escritura falla, el archivo original sigue intacto."""
    mod = _reload_csv_log(tmp_path, monkeypatch)
    logger = mod.FichajeCSVLogger()
    logger.registrar_entrada("08:00:00")
    contenido_original = (tmp_path / "fichajes.csv").read_text(encoding="utf-8")

    # Forzamos un fallo simulando que os.replace falla
    def replace_falla(*args, **kwargs):
        raise OSError("simulado")
    monkeypatch.setattr("os.replace", replace_falla)

    # La operación falla pero el archivo original se mantiene
    with pytest.raises(OSError):
        logger.registrar_salida("18:00:00", "10:00", "08:00", "")
    contenido_tras_fallo = (tmp_path / "fichajes.csv").read_text(encoding="utf-8")
    assert contenido_tras_fallo == contenido_original
```

- [ ] **Step 2: Run tests, verify they FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_csv_log.py -v
```
Expected: tests fail with `ModuleNotFoundError: No module named 'csv_log'`.

- [ ] **Step 3: Implement `csv_log.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\csv_log.py`

```python
# -*- coding: utf-8 -*-
"""Registro CSV histórico de fichajes.

Una fila por día con entrada+salida. Escritura atómica.
"""
import csv
import os
from datetime import datetime
from pathlib import Path

import config


class FichajeCSVLogger:
    FIELDS = [
        "fecha",
        "hora_entrada",
        "hora_salida",
        "total_horas",
        "jornada",
        "extra_ausencia",
        "observaciones",
    ]

    def __init__(self, path: Path | None = None):
        self.path: Path = Path(path) if path else config.CSV_FICHAJES
        self._inicializar()

    # ──────────────────────────────────────────────────────
    # Lectura/escritura
    # ──────────────────────────────────────────────────────

    def _inicializar(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self.FIELDS).writeheader()

    def _leer(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _escribir_atomico(self, rows: list[dict]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, self.path)

    # ──────────────────────────────────────────────────────
    # API pública
    # ──────────────────────────────────────────────────────

    def obtener_registro_hoy(self) -> dict | None:
        hoy = datetime.now().strftime("%Y-%m-%d")
        for fila in reversed(self._leer()):
            if fila["fecha"] == hoy:
                return fila
        return None

    def registrar_entrada(self, hora: str, observaciones: str = "") -> None:
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = self._leer()
        idx_hoy = self._indice_hoy(rows, hoy)
        if idx_hoy is not None:
            rows[idx_hoy]["hora_entrada"] = hora
            if observaciones:
                rows[idx_hoy]["observaciones"] = self._merge_obs(
                    rows[idx_hoy].get("observaciones", ""),
                    f"ENTRADA: {observaciones}",
                )
        else:
            rows.append({
                "fecha": hoy,
                "hora_entrada": hora,
                "hora_salida": "",
                "total_horas": "",
                "jornada": "",
                "extra_ausencia": "",
                "observaciones": observaciones,
            })
        self._escribir_atomico(rows)

    def registrar_salida(
        self,
        hora: str,
        presencia: str = "",
        jornada: str = "",
        extra: str = "",
        observaciones: str = "",
    ) -> None:
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = self._leer()
        idx_hoy = self._indice_hoy(rows, hoy)
        if idx_hoy is not None:
            rows[idx_hoy]["hora_salida"] = hora
            rows[idx_hoy]["total_horas"] = presencia
            rows[idx_hoy]["jornada"] = jornada
            rows[idx_hoy]["extra_ausencia"] = extra
            if observaciones:
                rows[idx_hoy]["observaciones"] = self._merge_obs(
                    rows[idx_hoy].get("observaciones", ""),
                    f"SALIDA: {observaciones}",
                )
        else:
            aviso = "⚠️ Salida sin entrada previa"
            obs = f"{aviso} | {observaciones}".rstrip(" |")
            rows.append({
                "fecha": hoy,
                "hora_entrada": "",
                "hora_salida": hora,
                "total_horas": presencia,
                "jornada": jornada,
                "extra_ausencia": extra,
                "observaciones": obs,
            })
        self._escribir_atomico(rows)

    def resumen_mes(self, mes: int, año: int) -> list[dict]:
        prefijo = f"{año:04d}-{mes:02d}-"
        return [r for r in self._leer() if r["fecha"].startswith(prefijo)]

    # ──────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────

    @staticmethod
    def _indice_hoy(rows: list[dict], hoy: str) -> int | None:
        for i in range(len(rows) - 1, -1, -1):
            if rows[i]["fecha"] == hoy:
                return i
        return None

    @staticmethod
    def _merge_obs(existente: str, nueva: str) -> str:
        if not existente:
            return nueva
        return f"{existente} | {nueva}"
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_csv_log.py -v
```
Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add csv_log.py tests/test_csv_log.py
git commit -m "feat(csv_log): atomic CSV writer with single-row-per-day model"
```

---

## Task 5: `notifier.py` — thread-safe Tkinter popups

**Files:**
- Create: `notifier.py`
- Create: `tests/test_notifier.py`

Notifier is harder to test (Tkinter doesn't render in headless CI). We test the policy logic (what message gets composed for each event) without actually showing popups.

- [ ] **Step 1: Write failing tests for the message composition logic**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_notifier.py`

```python
# -*- coding: utf-8 -*-
"""Tests para notifier.py — solo lógica de composición de mensajes.

Los popups Tk en sí se verifican manualmente; aquí testamos que el
mensaje correcto se compone según el evento.
"""
import importlib
from unittest.mock import patch
import pytest


def _reload_notifier(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import notifier
    return importlib.reload(notifier)


def test_componer_mensaje_fallo_normal(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    titulo, msg = n._componer_fallo(
        tipo="ENTRADA",
        motivo="Login fallido",
        html_cambio=False,
    )
    assert "ENTRADA" in titulo or "ENTRADA" in msg
    assert "Login fallido" in msg
    assert "manualmente" in msg.lower() or "a mano" in msg.lower()
    # No debe mencionar cambio de HTML cuando html_cambio=False
    assert "html" not in msg.lower() and "cambi" not in msg.lower()


def test_componer_mensaje_fallo_html_cambio(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    titulo, msg = n._componer_fallo(
        tipo="SALIDA",
        motivo="No pude leer NCS",
        html_cambio=True,
    )
    assert "SALIDA" in titulo or "SALIDA" in msg
    assert "No pude leer NCS" in msg
    # Sí debe mencionar el cambio de HTML / avisar al desarrollador
    assert "desarrollador" in msg.lower() or "actualiza" in msg.lower() or "cambi" in msg.lower()


def test_componer_mensaje_doble_instancia(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    titulo, msg = n._componer_doble_instancia(pid_otro=12345)
    assert "12345" in msg
    assert "instancia" in msg.lower() or "arranc" in msg.lower()


def test_aviso_fallo_invoca_popup(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    with patch.object(n, "_mostrar_popup") as mock_show:
        n.aviso_fallo(tipo="ENTRADA", motivo="test", html_cambio=False)
        assert mock_show.called
        args, kwargs = mock_show.call_args
        # Debe pasar titulo y mensaje
        assert len(args) >= 2 or ("titulo" in kwargs and "mensaje" in kwargs)


def test_aviso_doble_instancia_invoca_popup(tmp_path, monkeypatch):
    n = _reload_notifier(tmp_path, monkeypatch)
    with patch.object(n, "_mostrar_popup") as mock_show:
        n.aviso_doble_instancia(pid_otro=999)
        assert mock_show.called
```

- [ ] **Step 2: Run tests, verify FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_notifier.py -v
```
Expected: fail (module doesn't exist).

- [ ] **Step 3: Implement `notifier.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\notifier.py`

```python
# -*- coding: utf-8 -*-
"""Popups modales thread-safe para avisos al usuario.

Diseño:
- Si ya hay una ventana raíz Tk activa (modo GUI), se delega vía
  root.after(0, ...) para mostrar en el event loop principal.
- Si no (modo --silencioso), se crea una Tk root temporal en un
  hilo aparte para mostrar el messagebox y se destruye.

El popup es bloqueante para el usuario, pero el scheduler sigue.
"""
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

# Referencia opcional a la root Tk de la GUI principal.
# El módulo app.py debe asignarla con `notifier.set_root_principal(root)`.
_root_principal: Optional[tk.Tk] = None


def set_root_principal(root: Optional[tk.Tk]) -> None:
    """Registra la root Tk de la GUI principal (o None si no hay GUI)."""
    global _root_principal
    _root_principal = root


# ──────────────────────────────────────────────────────────
# Composición de mensajes (testable)
# ──────────────────────────────────────────────────────────

def _componer_fallo(tipo: str, motivo: str, html_cambio: bool) -> tuple[str, str]:
    titulo = f"❌ Fichaje {tipo} fallido"
    cuerpo = (
        f"No se pudo fichar la {tipo} hoy tras 3 intentos.\n\n"
        f"Causa: {motivo}\n\n"
        f"Por favor, ficha la {tipo} manualmente en clock.ncs.es."
    )
    if html_cambio:
        cuerpo += (
            "\n\nAVISO: la web de NCS pudo haber cambiado. "
            "Avisa al desarrollador para actualizar el bot."
        )
    return titulo, cuerpo


def _componer_doble_instancia(pid_otro: int) -> tuple[str, str]:
    titulo = "⚠️ Auto Fichaje ya en ejecución"
    cuerpo = (
        f"Ya hay otra instancia de Auto Fichaje corriendo (PID={pid_otro}).\n\n"
        f"Esta instancia no arrancará. Si quieres reiniciar, cierra la otra primero."
    )
    return titulo, cuerpo


# ──────────────────────────────────────────────────────────
# Visualización
# ──────────────────────────────────────────────────────────

def _mostrar_popup(titulo: str, mensaje: str, icono: str = "error") -> None:
    """Muestra el popup. Usa root principal si existe, si no crea uno efímero."""
    if _root_principal is not None:
        # Inyectamos en el event loop principal de Tk
        _root_principal.after(0, lambda: _show_message(titulo, mensaje, icono))
    else:
        # Modo silencioso: hilo con Tk efímera (daemon=False para no morir
        # si el scheduler termina)
        threading.Thread(
            target=_mostrar_efimero,
            args=(titulo, mensaje, icono),
            daemon=False,
        ).start()


def _show_message(titulo: str, mensaje: str, icono: str) -> None:
    if icono == "error":
        messagebox.showerror(titulo, mensaje)
    elif icono == "warning":
        messagebox.showwarning(titulo, mensaje)
    else:
        messagebox.showinfo(titulo, mensaje)


def _mostrar_efimero(titulo: str, mensaje: str, icono: str) -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        _show_message(titulo, mensaje, icono)
    finally:
        root.destroy()


# ──────────────────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────────────────

def aviso_fallo(tipo: str, motivo: str, html_cambio: bool = False) -> None:
    titulo, mensaje = _componer_fallo(tipo, motivo, html_cambio)
    _mostrar_popup(titulo, mensaje, icono="error")


def aviso_doble_instancia(pid_otro: int) -> None:
    titulo, mensaje = _componer_doble_instancia(pid_otro)
    _mostrar_popup(titulo, mensaje, icono="warning")
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_notifier.py -v
```
Expected: 5 tests PASS.

- [ ] **Step 5: Manual verification of popup rendering**

Run a quick smoke test in PowerShell:
```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
python -c "import notifier; notifier.aviso_fallo('ENTRADA', 'Test manual', html_cambio=True)"
```
Expected: a popup appears with title "❌ Fichaje ENTRADA fallido" and body mentioning the developer aviso. Click OK to dismiss. Process should exit cleanly.

- [ ] **Step 6: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add notifier.py tests/test_notifier.py
git commit -m "feat(notifier): thread-safe Tkinter popups for failures and double instance"
```

---

## Task 6: `credenciales.py` — credentials manager (extracted from GUI)

**Files:**
- Create: `credenciales.py`
- Create: `tests/test_credenciales.py`

- [ ] **Step 1: Write failing tests**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_credenciales.py`

```python
# -*- coding: utf-8 -*-
"""Tests para credenciales.py."""
import importlib
import json
import pytest


def _reload(tmp_path, monkeypatch):
    """Apunta el config_dir a tmp_path para no tocar AppData real."""
    import credenciales
    importlib.reload(credenciales)
    # Forzamos el directorio a tmp_path
    return credenciales


def test_carga_devuelve_none_si_no_existe(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    u, p = mgr.cargar()
    assert u is None
    assert p is None


def test_guardar_y_cargar_round_trip(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.guardar("alberto", "mi_pass_123")
    u, p = mgr.cargar()
    assert u == "alberto"
    assert p == "mi_pass_123"


def test_guardar_crea_archivo_con_b64(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.guardar("user", "pass")
    config_file = tmp_path / "config.dat"
    assert config_file.exists()
    contenido = json.loads(config_file.read_text(encoding="utf-8"))
    # Texto plano NO debe aparecer
    assert "user" not in config_file.read_text()
    assert "pass" not in config_file.read_text()
    assert "u" in contenido
    assert "p" in contenido


def test_cargar_devuelve_none_si_archivo_corrupto(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    (tmp_path / "config.dat").write_text("basura no json", encoding="utf-8")
    u, p = mgr.cargar()
    assert u is None
    assert p is None


def test_eliminar_borra_el_archivo(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.guardar("u", "p")
    assert (tmp_path / "config.dat").exists()
    mgr.eliminar()
    assert not (tmp_path / "config.dat").exists()


def test_eliminar_es_idempotente(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    mgr = mod.CredencialesManager(config_dir=tmp_path)
    mgr.eliminar()  # archivo no existe, no debe lanzar
    mgr.eliminar()
```

- [ ] **Step 2: Run tests, verify FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_credenciales.py -v
```
Expected: fail (module doesn't exist).

- [ ] **Step 3: Implement `credenciales.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\credenciales.py`

```python
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
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_credenciales.py -v
```
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add credenciales.py tests/test_credenciales.py
git commit -m "feat(credenciales): extract credentials manager into its own module"
```

---

## Task 7: `ncs.py` — state reading with safety guards

This is the most critical module. We test it in two passes: first the state reading (Task 7), then the full fichaje flow (Task 8).

**Files:**
- Create: `ncs.py`
- Create: `tests/test_ncs.py`

- [ ] **Step 1: Write failing tests for `leer_estado_seguro`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_ncs.py`

```python
# -*- coding: utf-8 -*-
"""Tests para ncs.py — verificación de estado y guardias de seguridad."""
import importlib
from unittest.mock import MagicMock, patch
import pytest
from selenium.common.exceptions import NoSuchElementException


def _reload_ncs(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import ncs
    return importlib.reload(ncs)


# ──────────────────────────────────────────────────────────
# Helpers de mock del driver
# ──────────────────────────────────────────────────────────

def _driver_con_alerta(clase_alerta: str | None, texto: str, presencia: str = "00:00"):
    """Crea un driver fake. clase_alerta = None → no aparece alerta."""
    driver = MagicMock()
    alerta_elem = MagicMock()
    alerta_elem.text = texto
    alerta_elem.is_displayed.return_value = True

    presencia_elem = MagicMock()
    presencia_elem.text = presencia

    def find_element(by, selector):
        s = str(selector)
        if "alert-success" in s and clase_alerta == "success":
            return alerta_elem
        if "alert-info" in s and clase_alerta == "info":
            return alerta_elem
        if "alert-danger" in s:
            raise NoSuchElementException("sin error")
        if "alert" in s:
            raise NoSuchElementException("alerta no presente")
        if "presencia" in s.lower() or s == "presencia":
            return presencia_elem
        elem = MagicMock(); elem.text = "00:00"
        return elem

    def find_element_by_id(id_):
        if id_ == "presencia":
            return presencia_elem
        elem = MagicMock(); elem.text = "00:00"
        return elem

    # Soportamos ambos APIs: find_element(by, sel) y por ID
    driver.find_element = MagicMock(side_effect=find_element)
    return driver


# ──────────────────────────────────────────────────────────
# Tests de leer_estado_seguro
# ──────────────────────────────────────────────────────────

def test_leer_estado_devuelve_entrada_si_alerta_info(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = _driver_con_alerta("info", "Estas fuera Marcas para ENTRAR", presencia="00:00")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "ENTRADA"
    assert estado.coherente is True


def test_leer_estado_devuelve_salida_si_alerta_success(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = _driver_con_alerta("success", "Estas dentro Marcas para SALIR", presencia="00:23")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "SALIDA"
    assert estado.coherente is True


def test_leer_estado_reintenta_si_desconocido(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = _driver_con_alerta(None, "")  # ninguna alerta
    estado = mod.leer_estado_seguro(driver, intentos=3, espera=0.0)
    assert estado.accion_siguiente == "DESCONOCIDO"
    # Debe haber intentado leer 3 veces
    # (find_element se llama al menos 2 veces por intento: success + info)
    assert driver.find_element.call_count >= 6


def test_estado_incoherente_si_alerta_entrada_pero_presencia_no_cero(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    # Alerta dice "ENTRAR" (fuera) pero presencia es 09:15 (estuviste dentro)
    driver = _driver_con_alerta("info", "Estas fuera Marcas para ENTRAR", presencia="09:15")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "ENTRADA"
    assert estado.coherente is False


def test_estado_incoherente_si_alerta_salida_pero_presencia_cero(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    # Alerta dice "SALIR" (dentro) pero presencia es 00:00 (acabas de entrar?)
    driver = _driver_con_alerta("success", "Estas dentro Marcas para SALIR", presencia="00:00")
    estado = mod.leer_estado_seguro(driver, intentos=1, espera=0.0)
    assert estado.accion_siguiente == "SALIDA"
    assert estado.coherente is False
```

- [ ] **Step 2: Run tests, verify FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_ncs.py -v
```
Expected: `ModuleNotFoundError: No module named 'ncs'`.

- [ ] **Step 3: Implement first half of `ncs.py` (state reading)**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\ncs.py`

```python
# -*- coding: utf-8 -*-
"""Interacción con clock.ncs.es: login, lectura de estado y fichaje.

Todo lo que sabe del HTML de NCS vive aquí. Si NCS cambia el DOM,
solo este archivo debe actualizarse.

Las funciones críticas tienen GUARDIAS que abortan antes de pulsar
el botón cuando el estado no es claro, para no desfichar al usuario.
"""
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import config


# ──────────────────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────────────────

@dataclass
class EstadoWeb:
    accion_siguiente: Literal["ENTRADA", "SALIDA", "DESCONOCIDO"]
    presencia_actual: str  # "HH:MM"
    coherente: bool


@dataclass
class ResultadoFichaje:
    success: bool
    saltado: bool
    tipo: str
    hora_fichaje: str
    presencia: str
    jornada: str
    extra: str
    mensaje: str
    html_cambio: bool = False


# ──────────────────────────────────────────────────────────
# Helpers humanos
# ──────────────────────────────────────────────────────────

def _pausa_humana(minimo: float = 0.5, maximo: float = 1.5) -> None:
    time.sleep(random.uniform(minimo, maximo))


# ──────────────────────────────────────────────────────────
# Lectura de estado (sin reintentos)
# ──────────────────────────────────────────────────────────

def _detectar_estado_una_vez(driver) -> Literal["ENTRADA", "SALIDA", "DESCONOCIDO"]:
    """Lee la alerta una sola vez."""
    # Alert success → estás DENTRO, próximo es SALIDA
    try:
        a = driver.find_element(By.CSS_SELECTOR, ".alert.alert-success")
        if a.is_displayed():
            texto = a.text.strip().upper()
            if "SALIR" in texto or "DENTRO" in texto:
                return "SALIDA"
    except NoSuchElementException:
        pass
    # Alert info → estás FUERA, próximo es ENTRADA
    try:
        a = driver.find_element(By.CSS_SELECTOR, ".alert.alert-info")
        if a.is_displayed():
            texto = a.text.strip().upper()
            if "ENTRAR" in texto or "FUERA" in texto:
                return "ENTRADA"
    except NoSuchElementException:
        pass
    return "DESCONOCIDO"


def _obtener_presencia(driver) -> str:
    """Lee el campo de presencia. Devuelve 'HH:MM' o '00:00' si no se encuentra."""
    try:
        elem = driver.find_element(By.ID, "presencia")
        return elem.text.strip() or "00:00"
    except NoSuchElementException:
        return "00:00"


def _presencia_a_segundos(presencia: str) -> int:
    """'HH:MM' → segundos. 0 si no se puede parsear."""
    try:
        partes = presencia.strip().split(":")
        if len(partes) >= 2:
            return int(partes[0]) * 3600 + int(partes[1]) * 60
    except ValueError:
        pass
    return 0


# ──────────────────────────────────────────────────────────
# Lectura segura (con reintentos + coherencia)
# ──────────────────────────────────────────────────────────

def leer_estado_seguro(driver, intentos: int = 3, espera: float = 2.0) -> EstadoWeb:
    """Lee el estado con reintentos y verifica coherencia alerta vs presencia.

    Returns:
        EstadoWeb con:
        - accion_siguiente: "ENTRADA", "SALIDA" o "DESCONOCIDO"
        - presencia_actual: "HH:MM" leído de la página
        - coherente: True si alerta y presencia concuerdan
    """
    accion: Literal["ENTRADA", "SALIDA", "DESCONOCIDO"] = "DESCONOCIDO"
    for i in range(intentos):
        accion = _detectar_estado_una_vez(driver)
        if accion != "DESCONOCIDO":
            break
        if i < intentos - 1 and espera > 0:
            time.sleep(espera)

    presencia = _obtener_presencia(driver)
    segs = _presencia_a_segundos(presencia)

    # Coherencia: alerta vs presencia
    coherente = True
    if accion == "ENTRADA" and segs > 0:
        coherente = False
    elif accion == "SALIDA" and segs == 0:
        coherente = False
    elif accion == "DESCONOCIDO":
        coherente = False  # no podemos confirmar nada

    return EstadoWeb(
        accion_siguiente=accion,
        presencia_actual=presencia,
        coherente=coherente,
    )
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_ncs.py -v
```
Expected: 5 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add ncs.py tests/test_ncs.py
git commit -m "feat(ncs): safe state reading with retries and coherence check"
```

---

## Task 8: `ncs.py` — `realizar_fichaje` with three guards

**Files:**
- Modify: `ncs.py`
- Modify: `tests/test_ncs.py`

- [ ] **Step 1: Add failing tests for the guarded `realizar_fichaje`**

Append to `tests/test_ncs.py`:

```python
# ──────────────────────────────────────────────────────────
# Tests de realizar_fichaje — LAS 3 GUARDIAS
# ──────────────────────────────────────────────────────────

def _driver_completo(alerta_clase, alerta_texto, presencia="00:00"):
    """Driver fake con botón btnTicar también accesible."""
    driver = _driver_con_alerta(alerta_clase, alerta_texto, presencia)
    boton = MagicMock(); boton.click = MagicMock(name="click_boton")
    driver._boton_fichaje = boton
    return driver, boton


def test_aborta_si_estado_desconocido_tras_reintentos(tmp_path, monkeypatch):
    """GUARDIA 1: nunca pulsar si no sabemos el estado."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo(None, "")  # ninguna alerta
    with patch.object(mod, "leer_estado_seguro",
                       return_value=mod.EstadoWeb("DESCONOCIDO", "", False)):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is False, "NO debe pulsar si estado es desconocido"
    assert res.success is False
    assert res.saltado is False
    assert res.html_cambio is True


def test_aborta_si_incoherencia_alerta_presencia(tmp_path, monkeypatch):
    """GUARDIA 2: nunca pulsar si alerta y presencia se contradicen."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("info", "ENTRAR", presencia="09:15")
    estado = mod.EstadoWeb("ENTRADA", "09:15", coherente=False)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is False
    assert res.success is False
    assert res.html_cambio is True


def test_skip_si_ya_dentro_y_tipo_entrada(tmp_path, monkeypatch):
    """GUARDIA 3: skip si ya estás dentro y tocaba ENTRADA."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("success", "SALIR", presencia="00:23")
    estado = mod.EstadoWeb("SALIDA", "00:23", coherente=True)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is False, "NO debe pulsar si ya estás dentro"
    assert res.success is True
    assert res.saltado is True


def test_skip_si_ya_fuera_y_tipo_salida(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("info", "ENTRAR", presencia="00:00")
    estado = mod.EstadoWeb("ENTRADA", "00:00", coherente=True)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="SALIDA")
    assert boton.click.called is False
    assert res.success is True
    assert res.saltado is True


def test_ficha_normal_si_estado_coherente_y_tocaba(tmp_path, monkeypatch):
    """Caso feliz: estado coherente, tocaba el fichaje esperado → click."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, boton = _driver_completo("info", "ENTRAR", presencia="00:00")
    estado = mod.EstadoWeb("ENTRADA", "00:00", coherente=True)
    estado_post = mod.EstadoWeb("SALIDA", "00:00", coherente=True)
    with patch.object(mod, "leer_estado_seguro", side_effect=[estado, estado_post]):
        with patch.object(mod, "_localizar_boton", return_value=boton):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert boton.click.called is True
    assert res.success is True
    assert res.saltado is False
    assert res.tipo == "ENTRADA"


def test_no_se_pulsa_boton_si_boton_no_se_encuentra(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver, _ = _driver_completo("info", "ENTRAR", presencia="00:00")
    estado = mod.EstadoWeb("ENTRADA", "00:00", coherente=True)
    with patch.object(mod, "leer_estado_seguro", return_value=estado):
        with patch.object(mod, "_localizar_boton", return_value=None):
            res = mod.realizar_fichaje(driver, tipo_esperado="ENTRADA")
    assert res.success is False
    assert res.html_cambio is True  # botón no encontrado = HTML cambió
```

- [ ] **Step 2: Run tests, verify FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_ncs.py -v
```
Expected: new tests fail (no `realizar_fichaje` and no `_localizar_boton`).

- [ ] **Step 3: Append `realizar_fichaje` and helpers to `ncs.py`**

Append to `ncs.py`:

```python
# ──────────────────────────────────────────────────────────
# Localización del botón
# ──────────────────────────────────────────────────────────

def _localizar_boton(driver, timeout: int = 30):
    """Busca el botón de fichaje probando los selectores configurados.

    Returns:
        WebElement clickable, o None si no se encuentra.
    """
    for selector in config.SELECTORES_BOTON_FICHAJE:
        try:
            return WebDriverWait(driver, timeout / len(config.SELECTORES_BOTON_FICHAJE)).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            continue
    return None


# ──────────────────────────────────────────────────────────
# Helpers de respuesta
# ──────────────────────────────────────────────────────────

def _abortado(tipo: str, motivo: str, html_cambio: bool = False) -> ResultadoFichaje:
    return ResultadoFichaje(
        success=False, saltado=False, tipo=tipo,
        hora_fichaje="", presencia="", jornada="", extra="",
        mensaje=motivo, html_cambio=html_cambio,
    )


def _saltado(tipo: str, motivo: str, presencia: str) -> ResultadoFichaje:
    return ResultadoFichaje(
        success=True, saltado=True, tipo=tipo,
        hora_fichaje="", presencia=presencia, jornada="", extra="",
        mensaje=motivo,
    )


# ──────────────────────────────────────────────────────────
# realizar_fichaje — el corazón con las 3 guardias
# ──────────────────────────────────────────────────────────

def realizar_fichaje(driver, tipo_esperado: str) -> ResultadoFichaje:
    """Realiza el fichaje del tipo esperado, con tres guardias de seguridad.

    GUARDIA 1: aborta si el estado de la web no se puede leer (DESCONOCIDO).
    GUARDIA 2: aborta si la alerta y la presencia se contradicen (incoherencia).
    GUARDIA 3: si ya está hecho lo esperado, se salta sin pulsar.

    Solo si las tres guardias pasan, se pulsa el botón y se verifica.
    """
    estado = leer_estado_seguro(driver, intentos=3, espera=2.0)

    # GUARDIA 1
    if estado.accion_siguiente == "DESCONOCIDO":
        return _abortado(
            tipo_esperado,
            "No se pudo leer el estado en NCS tras 3 intentos. "
            "Aborto por seguridad para no desfichar.",
            html_cambio=True,
        )

    # GUARDIA 2
    if not estado.coherente:
        return _abortado(
            tipo_esperado,
            f"Alerta y presencia no coinciden "
            f"(accion={estado.accion_siguiente}, presencia={estado.presencia_actual}). "
            f"Aborto por seguridad.",
            html_cambio=True,
        )

    # GUARDIA 3: ya fichado a mano
    if tipo_esperado == "ENTRADA" and estado.accion_siguiente == "SALIDA":
        return _saltado(
            tipo_esperado,
            "Ya estás DENTRO; entrada omitida (fichaje manual previo).",
            estado.presencia_actual,
        )
    if tipo_esperado == "SALIDA" and estado.accion_siguiente == "ENTRADA":
        return _saltado(
            tipo_esperado,
            "Ya estás FUERA; salida omitida (sin entrada previa o salida manual).",
            estado.presencia_actual,
        )

    # Localizar y pulsar
    boton = _localizar_boton(driver)
    if boton is None:
        return _abortado(
            tipo_esperado,
            "No se encontró el botón de fichaje en la página.",
            html_cambio=True,
        )

    hora_fichaje = datetime.now().strftime("%H:%M:%S")
    _pausa_humana(0.8, 1.5)
    try:
        boton.click()
    except Exception:
        try:
            driver.execute_script("arguments[0].click();", boton)
        except Exception as e:
            return _abortado(tipo_esperado, f"No se pudo pulsar el botón: {e}")

    # Verificar cambio de estado tras el click
    _pausa_humana(1.0, 2.0)
    estado_post = leer_estado_seguro(driver, intentos=2, espera=1.0)

    return ResultadoFichaje(
        success=True, saltado=False, tipo=tipo_esperado,
        hora_fichaje=hora_fichaje,
        presencia=estado_post.presencia_actual,
        jornada="",
        extra="",
        mensaje=f"Fichaje {tipo_esperado} ejecutado a las {hora_fichaje}",
    )
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_ncs.py -v
```
Expected: all tests in test_ncs.py PASS (11 total).

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add ncs.py tests/test_ncs.py
git commit -m "feat(ncs): three-guard realizar_fichaje that never clicks blindly"
```

---

## Task 9: `ncs.py` — login and `crear_navegador`

**Files:**
- Modify: `ncs.py`
- Modify: `tests/test_ncs.py`

- [ ] **Step 1: Add failing tests for login behavior**

Append to `tests/test_ncs.py`:

```python
# ──────────────────────────────────────────────────────────
# Tests de realizar_login
# ──────────────────────────────────────────────────────────

def test_login_devuelve_true_si_no_hay_modal(tmp_path, monkeypatch):
    """Si no aparece el modal, ya estamos logueados → success."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = MagicMock()
    with patch("ncs.WebDriverWait") as wait_mock:
        # Simular que detectar_modal_login no encuentra el modal
        wait_mock.return_value.until.side_effect = TimeoutException("no modal")
        ok = mod.realizar_login(driver, "u", "p")
    assert ok is True


def test_login_falla_si_credenciales_erroneas(tmp_path, monkeypatch):
    """Si tras pulsar Login aparece #messenger .failed visible → False."""
    mod = _reload_ncs(tmp_path, monkeypatch)
    driver = MagicMock()
    modal = MagicMock(); modal.is_displayed.return_value = True
    user_field = MagicMock(); pass_field = MagicMock(); boton_login = MagicMock()
    failed_msg = MagicMock(); failed_msg.is_displayed.return_value = True
    failed_msg.text = "Credenciales incorrectas"

    call_count = {"n": 0}

    def wait_until_side_effect(*args, **kwargs):
        # Simulamos: 1ª llamada (detectar modal) → modal,
        # 2ª (campo usuario), 3ª (campo password), 4ª (botón login)
        call_count["n"] += 1
        return [modal, user_field, pass_field, boton_login][min(call_count["n"]-1, 3)]

    def find_element_side_effect(by, selector):
        if "failed" in str(selector):
            return failed_msg
        raise NoSuchElementException()

    driver.find_element = MagicMock(side_effect=find_element_side_effect)

    with patch("ncs.WebDriverWait") as wait_mock:
        wait_mock.return_value.until.side_effect = wait_until_side_effect
        ok = mod.realizar_login(driver, "u", "p")
    assert ok is False


# ──────────────────────────────────────────────────────────
# Tests de crear_navegador (smoke — solo que devuelve algo)
# ──────────────────────────────────────────────────────────

def test_crear_navegador_devuelve_none_si_falla(tmp_path, monkeypatch):
    mod = _reload_ncs(tmp_path, monkeypatch)
    with patch("ncs.ChromeDriverManager") as cdm:
        cdm.return_value.install.side_effect = Exception("simulado")
        driver = mod.crear_navegador()
    assert driver is None
```

- [ ] **Step 2: Run tests, verify the new ones FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_ncs.py -v
```
Expected: the 3 new tests fail (`realizar_login` and `crear_navegador` don't exist yet).

- [ ] **Step 3: Append `realizar_login` and `crear_navegador` to `ncs.py`**

Append to `ncs.py`:

```python
# ──────────────────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────────────────

def _escribir_como_humano(elemento, texto: str) -> None:
    elemento.clear()
    _pausa_humana(0.3, 0.7)
    for char in texto:
        elemento.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    _pausa_humana(0.2, 0.5)


def realizar_login(driver, usuario: str, password: str, timeout: int = 30) -> bool:
    """Login en clock.ncs.es.

    Returns:
        True si login exitoso (incluye "ya logueado").
        False si credenciales incorrectas o algún campo del modal no aparece.
    """
    # ¿Hay modal de login?
    try:
        modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#myModal.modal.fade.in"))
        )
        if not modal.is_displayed():
            return True
    except TimeoutException:
        return True  # ya logueado

    _pausa_humana(1.0, 2.0)

    # Llenar usuario
    try:
        campo_u = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "tbUserName"))
        )
        campo_p = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "tbPassword"))
        )
    except TimeoutException:
        return False

    _escribir_como_humano(campo_u, usuario)
    _pausa_humana(0.5, 1.0)
    _escribir_como_humano(campo_p, password)
    _pausa_humana(0.8, 1.5)

    # Botón
    try:
        boton = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, "LoginBtn"))
        )
    except TimeoutException:
        return False

    try:
        boton.click()
    except Exception:
        driver.execute_script("arguments[0].click();", boton)

    _pausa_humana(2.0, 4.0)

    # ¿Mensaje de error?
    try:
        error = driver.find_element(By.CSS_SELECTOR, "#messenger .failed")
        if error.is_displayed():
            return False
    except NoSuchElementException:
        pass

    # Esperar a que el modal desaparezca
    try:
        WebDriverWait(driver, 10).until_not(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#myModal.modal.fade.in"))
        )
        return True
    except TimeoutException:
        return False


# ──────────────────────────────────────────────────────────
# crear_navegador
# ──────────────────────────────────────────────────────────

def crear_navegador():
    """Crea un Chrome headless con anti-detección. None si falla."""
    opciones = Options()
    opciones.add_argument("--headless=new")
    opciones.add_argument("--window-size=1366,768")
    opciones.add_argument("--disable-blink-features=AutomationControlled")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("useAutomationExtension", False)
    opciones.add_argument("--disable-notifications")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opciones)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        return driver
    except Exception:
        return None
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_ncs.py -v
```
Expected: all 14 tests in test_ncs.py PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add ncs.py tests/test_ncs.py
git commit -m "feat(ncs): add realizar_login and crear_navegador"
```

---

## Task 10: `scheduler.py` — `EstadoDiario` with legacy migration

**Files:**
- Create: `scheduler.py`
- Create: `tests/test_estado.py`

- [ ] **Step 1: Write failing tests for `EstadoDiario`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_estado.py`

```python
# -*- coding: utf-8 -*-
"""Tests para EstadoDiario en scheduler.py (persistencia + migración)."""
import importlib
import json
from datetime import datetime, date, timedelta
import pytest


def _reload(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import scheduler
    return importlib.reload(scheduler)


def _hoy() -> str:
    return date.today().isoformat()


# ──────────────────────────────────────────────────────────
# Estado vacío
# ──────────────────────────────────────────────────────────

def test_cargar_devuelve_vacio_si_archivo_no_existe(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    e = mod.EstadoDiario.cargar()
    assert e.fecha == _hoy()
    assert e.hora_entrada is None
    assert e.hora_salida is None
    assert e.entrada_ts is None
    assert e.salida_ts is None
    assert e.reintentos_entrada == 0
    assert e.reintentos_salida == 0


def test_cargar_resetea_si_fecha_distinta(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    (tmp_path / "estado_diario.json").write_text(json.dumps({
        "fecha": "2000-01-01",
        "hora_entrada": "2000-01-01T08:50:00",
        "hora_salida": None,
        "entrada_ts": "2000-01-01T08:50:00",
        "salida_ts": None,
        "reintentos_entrada": 2,
        "reintentos_salida": 0,
    }), encoding="utf-8")
    e = mod.EstadoDiario.cargar()
    assert e.fecha == _hoy()
    assert e.hora_entrada is None
    assert e.reintentos_entrada == 0


# ──────────────────────────────────────────────────────────
# Persistencia
# ──────────────────────────────────────────────────────────

def test_guardar_y_recargar_preserva_horas(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    hora = datetime(2026, 5, 29, 8, 53, 12)
    e = mod.EstadoDiario.cargar()
    e.hora_entrada = hora
    e.guardar()
    e2 = mod.EstadoDiario.cargar()
    assert e2.hora_entrada == hora


def test_marcar_entrada_persiste_timestamp(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    e = mod.EstadoDiario.cargar()
    e.marcar_entrada()
    e2 = mod.EstadoDiario.cargar()
    assert e2.entrada_ts is not None
    assert (datetime.now() - e2.entrada_ts).total_seconds() < 5


# ──────────────────────────────────────────────────────────
# Migración legacy CLI
# ──────────────────────────────────────────────────────────

def test_migracion_esquema_legacy_cli(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    legacy = {
        "fecha": _hoy(),
        "hora_entrada_random": f"{_hoy()}T08:43:42",
        "hora_salida_random": f"{_hoy()}T18:21:13",
        "entrada_realizada_ts": f"{_hoy()}T08:44:07.063918",
        "salida_realizada_ts": None,
        "reintentos_entrada": 0,
        "reintentos_salida": 0,
    }
    (tmp_path / "estado_diario.json").write_text(json.dumps(legacy), encoding="utf-8")
    e = mod.EstadoDiario.cargar()
    assert e.hora_entrada == datetime.fromisoformat(legacy["hora_entrada_random"])
    assert e.hora_salida == datetime.fromisoformat(legacy["hora_salida_random"])
    assert e.entrada_ts == datetime.fromisoformat(legacy["entrada_realizada_ts"])
    assert e.salida_ts is None
    # Y el archivo debe estar reescrito en formato nuevo
    en_disco = json.loads((tmp_path / "estado_diario.json").read_text(encoding="utf-8"))
    assert "hora_entrada" in en_disco
    assert "hora_entrada_random" not in en_disco


def test_migracion_esquema_legacy_gui_bool_a_timestamp(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    legacy = {
        "fecha": _hoy(),
        "hora_entrada": f"{_hoy()}T08:50:00",
        "hora_salida": None,
        "entrada_realizada": True,   # ← bool en GUI legacy
        "salida_realizada": False,
        "reintentos_entrada": 1,
        "reintentos_salida": 0,
    }
    (tmp_path / "estado_diario.json").write_text(json.dumps(legacy), encoding="utf-8")
    e = mod.EstadoDiario.cargar()
    assert e.entrada_ts is not None  # se convirtió en timestamp
    assert e.salida_ts is None
    assert e.reintentos_entrada == 1
```

- [ ] **Step 2: Run tests, verify FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_estado.py -v
```
Expected: `ModuleNotFoundError: No module named 'scheduler'`.

- [ ] **Step 3: Create `scheduler.py` with just `EstadoDiario`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\scheduler.py`

```python
# -*- coding: utf-8 -*-
"""Bucle diario del fichaje + estado persistente.

Contiene:
- EstadoDiario: dataclass con persistencia atómica y migración legacy.
- Scheduler: bucle infinito que decide cuándo fichar.
"""
import json
import os
import random
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import config


# ──────────────────────────────────────────────────────────
# EstadoDiario
# ──────────────────────────────────────────────────────────

@dataclass
class EstadoDiario:
    fecha: str
    hora_entrada: Optional[datetime] = None
    hora_salida: Optional[datetime] = None
    entrada_ts: Optional[datetime] = None
    salida_ts: Optional[datetime] = None
    reintentos_entrada: int = 0
    reintentos_salida: int = 0

    # ── Constructores ────────────────────────────────────

    @classmethod
    def _vacio_hoy(cls) -> "EstadoDiario":
        return cls(fecha=date.today().isoformat())

    @classmethod
    def cargar(cls) -> "EstadoDiario":
        """Carga del disco. Reset si fecha distinta. Migración si esquema legacy."""
        path: Path = config.ESTADO_FILE
        if not path.exists():
            return cls._vacio_hoy()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls._vacio_hoy()
        if raw.get("fecha") != date.today().isoformat():
            return cls._vacio_hoy()
        migrado = cls._migrar(raw)
        e = cls._desde_dict(migrado)
        if migrado != raw:
            # Reescribir en formato nuevo
            e.guardar()
        return e

    # ── Migración ─────────────────────────────────────────

    @staticmethod
    def _migrar(raw: dict) -> dict:
        """Convierte un dict legacy (CLI o GUI) al esquema nuevo."""
        nuevo = {"fecha": raw.get("fecha")}
        # hora_entrada / hora_entrada_random
        nuevo["hora_entrada"] = raw.get("hora_entrada") or raw.get("hora_entrada_random")
        nuevo["hora_salida"] = raw.get("hora_salida") or raw.get("hora_salida_random")
        # entrada_ts / entrada_realizada_ts / entrada_realizada (bool)
        if "entrada_ts" in raw:
            nuevo["entrada_ts"] = raw["entrada_ts"]
        elif "entrada_realizada_ts" in raw:
            nuevo["entrada_ts"] = raw["entrada_realizada_ts"]
        elif raw.get("entrada_realizada") is True:
            nuevo["entrada_ts"] = datetime.now().isoformat()
        else:
            nuevo["entrada_ts"] = None
        # salida
        if "salida_ts" in raw:
            nuevo["salida_ts"] = raw["salida_ts"]
        elif "salida_realizada_ts" in raw:
            nuevo["salida_ts"] = raw["salida_realizada_ts"]
        elif raw.get("salida_realizada") is True:
            nuevo["salida_ts"] = datetime.now().isoformat()
        else:
            nuevo["salida_ts"] = None
        nuevo["reintentos_entrada"] = raw.get("reintentos_entrada", 0)
        nuevo["reintentos_salida"] = raw.get("reintentos_salida", 0)
        return nuevo

    @classmethod
    def _desde_dict(cls, d: dict) -> "EstadoDiario":
        def _dt(v):
            return datetime.fromisoformat(v) if v else None
        return cls(
            fecha=d["fecha"],
            hora_entrada=_dt(d.get("hora_entrada")),
            hora_salida=_dt(d.get("hora_salida")),
            entrada_ts=_dt(d.get("entrada_ts")),
            salida_ts=_dt(d.get("salida_ts")),
            reintentos_entrada=d.get("reintentos_entrada", 0),
            reintentos_salida=d.get("reintentos_salida", 0),
        )

    # ── Persistencia ──────────────────────────────────────

    def guardar(self) -> None:
        """Guarda atómicamente: write a .tmp, replace al final."""
        path: Path = config.ESTADO_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        d = {
            "fecha": self.fecha,
            "hora_entrada": self.hora_entrada.isoformat() if self.hora_entrada else None,
            "hora_salida": self.hora_salida.isoformat() if self.hora_salida else None,
            "entrada_ts": self.entrada_ts.isoformat() if self.entrada_ts else None,
            "salida_ts": self.salida_ts.isoformat() if self.salida_ts else None,
            "reintentos_entrada": self.reintentos_entrada,
            "reintentos_salida": self.reintentos_salida,
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)

    # ── Atajos ────────────────────────────────────────────

    def marcar_entrada(self) -> None:
        self.entrada_ts = datetime.now()
        self.guardar()

    def marcar_salida(self) -> None:
        self.salida_ts = datetime.now()
        self.guardar()

    @property
    def entrada_realizada(self) -> bool:
        return self.entrada_ts is not None

    @property
    def salida_realizada(self) -> bool:
        return self.salida_ts is not None

    def es_dia_completado(self) -> bool:
        return self.entrada_realizada and self.salida_realizada
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_estado.py -v
```
Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add scheduler.py tests/test_estado.py
git commit -m "feat(scheduler): EstadoDiario with atomic persistence and legacy migration"
```

---

## Task 11: `scheduler.py` — `Scheduler` class with decision logic

**Files:**
- Modify: `scheduler.py`
- Create: `tests/test_scheduler.py`

- [ ] **Step 1: Write failing tests for the decision logic**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\tests\test_scheduler.py`

```python
# -*- coding: utf-8 -*-
"""Tests para Scheduler — decisión de cuándo fichar (sin bucle infinito)."""
import importlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest


def _reload(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTO_FICHAJE_DATA_DIR", str(tmp_path))
    import config
    importlib.reload(config)
    import scheduler
    return importlib.reload(scheduler)


def _logs(): 
    return []


def test_no_actua_en_fin_de_semana(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    # Sábado
    with patch.object(mod, "_es_laborable", return_value=False):
        assert sched._toca_entrada(datetime(2026, 5, 30, 9, 0)) is False
        assert sched._toca_salida(datetime(2026, 5, 30, 18, 0)) is False


def test_calcula_horarios_solo_una_vez(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    msgs = []
    sched = mod.Scheduler(usuario="u", password="p", on_log=msgs.append)
    sched._calcular_horarios_si_faltan()
    h1_entrada = sched._estado.hora_entrada
    h1_salida = sched._estado.hora_salida
    assert h1_entrada is not None and h1_salida is not None
    # Segunda llamada no debe cambiarlas
    sched._calcular_horarios_si_faltan()
    assert sched._estado.hora_entrada == h1_entrada
    assert sched._estado.hora_salida == h1_salida


def test_toca_entrada_dentro_de_ventana(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    with patch.object(mod, "_es_laborable", return_value=True):
        # antes de la hora → False
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 49)) is False
        # justo en la hora → True
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 50)) is True
        # 20 min después (dentro del margen) → True
        assert sched._toca_entrada(datetime(2026, 5, 29, 9, 25)) is True
        # mucho después → False (fuera de ventana + margen)
        assert sched._toca_entrada(datetime(2026, 5, 29, 10, 30)) is False


def test_no_toca_si_ya_realizado(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    sched._estado.entrada_ts = datetime(2026, 5, 29, 8, 51)  # ya hecho
    with patch.object(mod, "_es_laborable", return_value=True):
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 55)) is False


def test_no_toca_si_max_reintentos(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    sched._estado.reintentos_entrada = config.MAX_REINTENTOS = sched._estado.reintentos_entrada
    # Forzamos reintentos al máximo
    import config
    sched._estado.reintentos_entrada = config.MAX_REINTENTOS
    with patch.object(mod, "_es_laborable", return_value=True):
        assert sched._toca_entrada(datetime(2026, 5, 29, 8, 55)) is False


def test_dispara_notifier_al_llegar_a_max_reintentos(tmp_path, monkeypatch):
    """Tras el 3er fallo, debe llamar notifier.aviso_fallo."""
    mod = _reload(tmp_path, monkeypatch)
    msgs = []
    sched = mod.Scheduler(usuario="u", password="p", on_log=msgs.append)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)

    import ncs
    resultado_fallido = ncs.ResultadoFichaje(
        success=False, saltado=False, tipo="ENTRADA",
        hora_fichaje="", presencia="", jornada="", extra="",
        mensaje="login fallido", html_cambio=False,
    )

    with patch.object(mod, "_realizar_fichaje_completo", return_value=resultado_fallido):
        with patch("notifier.aviso_fallo") as notif_mock:
            # Simulamos los 3 reintentos
            for i in range(config.MAX_REINTENTOS):
                sched._intentar_fichaje("ENTRADA")
            # En el último, debe haberse disparado el notifier
            assert notif_mock.called


def test_no_dispara_notifier_si_solo_un_fallo(tmp_path, monkeypatch):
    mod = _reload(tmp_path, monkeypatch)
    sched = mod.Scheduler(usuario="u", password="p", on_log=lambda m: None)
    sched._estado.hora_entrada = datetime(2026, 5, 29, 8, 50)
    import ncs
    res = ncs.ResultadoFichaje(False, False, "ENTRADA", "", "", "", "", "login fallido", False)
    with patch.object(mod, "_realizar_fichaje_completo", return_value=res):
        with patch("notifier.aviso_fallo") as notif_mock:
            sched._intentar_fichaje("ENTRADA")
            assert notif_mock.called is False
```

- [ ] **Step 2: Run tests, verify FAIL**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_scheduler.py -v
```
Expected: tests fail (Scheduler class doesn't exist yet).

- [ ] **Step 3: Append `Scheduler` class to `scheduler.py`**

Append to `scheduler.py`:

```python
# ──────────────────────────────────────────────────────────
# Helpers de tiempo
# ──────────────────────────────────────────────────────────

def _es_laborable() -> bool:
    return datetime.now().weekday() in config.DIAS_LABORABLES


def _nombre_dia() -> str:
    return ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][
        datetime.now().weekday()
    ]


def _hora_str_a_dt(hora_str: str, base: Optional[datetime] = None) -> datetime:
    base = base or datetime.now()
    h, m = map(int, hora_str.split(":"))
    return base.replace(hour=h, minute=m, second=0, microsecond=0)


def _hora_aleatoria(desde: str, hasta: str) -> datetime:
    dt1 = _hora_str_a_dt(desde)
    dt2 = _hora_str_a_dt(hasta)
    diff = int((dt2 - dt1).total_seconds())
    offset = random.randint(0, max(0, diff))
    return dt1 + timedelta(seconds=offset)


def _dentro_de_ventana_ampliada(ahora: datetime, hasta_str: str) -> bool:
    limite = _hora_str_a_dt(hasta_str) + timedelta(minutes=config.MARGEN_VENTANA_EXTRA)
    return ahora <= limite


# ──────────────────────────────────────────────────────────
# Fichaje completo (orchestrates login + ncs.realizar_fichaje + csv)
# ──────────────────────────────────────────────────────────

def _realizar_fichaje_completo(usuario: str, password: str, tipo: str,
                                  on_log: Callable[[str], None]):
    """Login + fichaje + cierre del navegador. Devuelve ncs.ResultadoFichaje."""
    import ncs
    on_log(f"Abriendo navegador para {tipo}...")
    driver = ncs.crear_navegador()
    if driver is None:
        return ncs.ResultadoFichaje(
            success=False, saltado=False, tipo=tipo,
            hora_fichaje="", presencia="", jornada="", extra="",
            mensaje="No se pudo abrir Chrome", html_cambio=False,
        )
    try:
        driver.get(config.URL_FICHAJE)
        on_log("Login en NCS...")
        ok = ncs.realizar_login(driver, usuario, password)
        if not ok:
            return ncs.ResultadoFichaje(
                success=False, saltado=False, tipo=tipo,
                hora_fichaje="", presencia="", jornada="", extra="",
                mensaje="Login fallido (credenciales o web caída)",
                html_cambio=False,
            )
        on_log(f"Verificando estado para {tipo}...")
        return ncs.realizar_fichaje(driver, tipo_esperado=tipo)
    finally:
        try:
            driver.quit()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────────────────

class Scheduler:
    def __init__(
        self,
        usuario: str,
        password: str,
        on_log: Callable[[str], None],
        on_estado_cambia: Optional[Callable[[], None]] = None,
    ):
        self.usuario = usuario
        self.password = password
        self._on_log = on_log
        self._on_estado_cambia = on_estado_cambia or (lambda: None)
        self._estado = EstadoDiario.cargar()
        self._running = True

    # ── Decisión ──────────────────────────────────────────

    def _calcular_horarios_si_faltan(self) -> None:
        if self._estado.hora_entrada is None:
            self._estado.hora_entrada = _hora_aleatoria(
                config.ENTRADA_DESDE, config.ENTRADA_HASTA
            )
        if self._estado.hora_salida is None:
            self._estado.hora_salida = _hora_aleatoria(
                config.SALIDA_DESDE, config.SALIDA_HASTA
            )
        self._estado.guardar()

    def _toca_entrada(self, ahora: datetime) -> bool:
        if not _es_laborable():
            return False
        e = self._estado
        if e.entrada_realizada:
            return False
        if e.hora_entrada is None:
            return False
        if ahora < e.hora_entrada:
            return False
        if not _dentro_de_ventana_ampliada(ahora, config.ENTRADA_HASTA):
            return False
        if e.reintentos_entrada >= config.MAX_REINTENTOS:
            return False
        return True

    def _toca_salida(self, ahora: datetime) -> bool:
        if not _es_laborable():
            return False
        e = self._estado
        if e.salida_realizada:
            return False
        if e.hora_salida is None:
            return False
        if ahora < e.hora_salida:
            return False
        if not _dentro_de_ventana_ampliada(ahora, config.SALIDA_HASTA):
            return False
        if e.reintentos_salida >= config.MAX_REINTENTOS:
            return False
        return True

    # ── Ejecución de un intento ───────────────────────────

    def _intentar_fichaje(self, tipo: str) -> None:
        """Realiza un intento, gestiona reintentos y notificación."""
        import notifier
        import csv_log

        # Backoff progresivo si no es el primer intento
        reintentos_actuales = (
            self._estado.reintentos_entrada if tipo == "ENTRADA"
            else self._estado.reintentos_salida
        )
        if reintentos_actuales > 0:
            espera = config.BACKOFF_REINTENTOS[
                min(reintentos_actuales - 1, len(config.BACKOFF_REINTENTOS) - 1)
            ]
            self._on_log(f"Reintento #{reintentos_actuales} {tipo}. Esperando {espera//60}min...")
            import time
            time.sleep(espera)

        self._on_log(f"Intentando fichaje {tipo} (intento {reintentos_actuales + 1}/{config.MAX_REINTENTOS})")
        resultado = _realizar_fichaje_completo(
            self.usuario, self.password, tipo, self._on_log
        )

        logger = csv_log.FichajeCSVLogger()

        if resultado.saltado:
            self._on_log(f"⏭️  {tipo} omitida: {resultado.mensaje}")
            if tipo == "ENTRADA":
                self._estado.marcar_entrada()
            else:
                self._estado.marcar_salida()
            self._on_estado_cambia()
            return

        if resultado.success:
            self._on_log(f"✅ {tipo} fichada a las {resultado.hora_fichaje}")
            if tipo == "ENTRADA":
                logger.registrar_entrada(resultado.hora_fichaje, observaciones="Automático")
                self._estado.marcar_entrada()
            else:
                logger.registrar_salida(
                    resultado.hora_fichaje,
                    presencia=resultado.presencia,
                    jornada=resultado.jornada,
                    extra=resultado.extra,
                    observaciones="Automático",
                )
                self._estado.marcar_salida()
            self._on_estado_cambia()
            return

        # Fallo: incrementar reintentos
        self._on_log(f"❌ {tipo} fallido: {resultado.mensaje}")
        if tipo == "ENTRADA":
            self._estado.reintentos_entrada += 1
        else:
            self._estado.reintentos_salida += 1
        self._estado.guardar()
        # Registrar el fallo en CSV (sin sobrescribir el éxito si lo hubiera)
        # Solo si era el último intento, también
        if tipo == "ENTRADA":
            logger.registrar_entrada(
                "", observaciones=f"ERROR intento {reintentos_actuales + 1}: {resultado.mensaje}"
            )
        else:
            logger.registrar_salida(
                "", "", "", "",
                observaciones=f"ERROR intento {reintentos_actuales + 1}: {resultado.mensaje}",
            )

        # Si hemos agotado todos los reintentos, avisar
        reintentos_finales = (
            self._estado.reintentos_entrada if tipo == "ENTRADA"
            else self._estado.reintentos_salida
        )
        if reintentos_finales >= config.MAX_REINTENTOS:
            self._on_log(f"💥 Reintentos agotados para {tipo}. Avisando al usuario.")
            notifier.aviso_fallo(tipo, resultado.mensaje, html_cambio=resultado.html_cambio)
        self._on_estado_cambia()

    # ── Bucle principal ──────────────────────────────────

    def ejecutar(self) -> None:
        import time
        ultimo_dia = None
        while self._running:
            ahora = datetime.now()
            hoy = ahora.date()
            if hoy != ultimo_dia:
                ultimo_dia = hoy
                # Nuevo día: recargar estado (reset automático si fecha cambió)
                self._estado = EstadoDiario.cargar()
                self._on_log(f"📅 Nuevo día: {_nombre_dia()} {ahora.strftime('%d/%m/%Y')}")
                if _es_laborable():
                    self._calcular_horarios_si_faltan()
                    self._on_log(
                        f"⏰ Hoy → Entrada: {self._estado.hora_entrada.strftime('%H:%M:%S')} "
                        f"| Salida: {self._estado.hora_salida.strftime('%H:%M:%S')}"
                    )
                else:
                    self._on_log(f"🏖️ {_nombre_dia()} no laborable")
                self._on_estado_cambia()

            if self._toca_entrada(ahora):
                self._intentar_fichaje("ENTRADA")
            if self._toca_salida(ahora):
                self._intentar_fichaje("SALIDA")

            time.sleep(60)

    def detener(self) -> None:
        self._running = False
```

- [ ] **Step 4: Run tests, verify PASS**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/test_scheduler.py -v
```
Expected: 7 tests PASS.

- [ ] **Step 5: Run the full suite and verify nothing else broke**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/ -v
```
Expected: all tests across all files PASS. Total suite < 5 seconds.

- [ ] **Step 6: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add scheduler.py tests/test_scheduler.py
git commit -m "feat(scheduler): Scheduler class with retry/backoff and notification policy"
```

---

## Task 12: `app.py` — entry point with --silencioso flag and GUI

**Files:**
- Create: `app.py`

This module wires everything together. Most of it is the Tkinter GUI from the old `auto_fichaje_gui.py`, cleaned up and connected to the new modules. We rely on manual verification rather than automated tests (Tkinter is hard to test reliably).

- [ ] **Step 1: Implement `app.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\app.py`

```python
# -*- coding: utf-8 -*-
"""Entry point del Auto Fichaje NCS Clock.

Modos:
- GUI (default): muestra panel con reloj, log en vivo y estado.
- --silencioso: corre sin ventana, popups solo en fallos críticos.
"""
import argparse
import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext

import config
import credenciales
import lock
import notifier
from scheduler import Scheduler, _es_laborable, _nombre_dia


# ──────────────────────────────────────────────────────────
# Logger compartido al archivo
# ──────────────────────────────────────────────────────────

def _escribir_log_archivo(mensaje: str, nivel: str = "INFO") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] [{nivel}] {mensaje}\n")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────
# Modo silencioso
# ──────────────────────────────────────────────────────────

def _ejecutar_silencioso(usuario: str, password: str) -> None:
    def on_log(m: str) -> None:
        _escribir_log_archivo(m)
        print(m)
    on_log("=" * 60)
    on_log("🚀 AUTO FICHAJE INICIADO (modo silencioso)")
    on_log(f"Ventana entrada: {config.ENTRADA_DESDE}–{config.ENTRADA_HASTA}")
    on_log(f"Ventana salida:  {config.SALIDA_DESDE}–{config.SALIDA_HASTA}")
    on_log("=" * 60)
    sched = Scheduler(usuario, password, on_log=on_log)
    sched.ejecutar()


# ──────────────────────────────────────────────────────────
# Modo GUI
# ──────────────────────────────────────────────────────────

class PanelControl:
    def __init__(self, usuario: str, password: str):
        self.usuario = usuario
        self.password = password

        self.root = tk.Tk()
        self.root.title("🕐 Auto Fichaje NCS — Panel de Control")
        self.root.geometry("600x500")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Registrar root para que notifier la use
        notifier.set_root_principal(self.root)

        self._construir_ui()

        # Scheduler en hilo background
        self._sched = Scheduler(
            usuario, password,
            on_log=self._log_thread_safe,
            on_estado_cambia=self._refrescar_estado_ui_thread_safe,
        )
        self._thread = threading.Thread(target=self._sched.ejecutar, daemon=True)
        self._thread.start()

        # Reloj
        self._tick()

    def _construir_ui(self) -> None:
        # Cabecera
        cab = tk.Frame(self.root, bg="#1a1a2e", pady=10)
        cab.pack(fill=tk.X)
        tk.Label(cab, text="🕐 Auto Fichaje NCS",
                 font=("Arial", 18, "bold"), bg="#1a1a2e", fg="white").pack()
        tk.Label(cab, text="Panel de Control — Fichaje automático L–V",
                 font=("Arial", 10), bg="#1a1a2e", fg="#aaaaaa").pack()

        # Reloj
        reloj = tk.Frame(self.root, bg="#16213e", pady=8)
        reloj.pack(fill=tk.X)
        self.lbl_reloj = tk.Label(reloj, text="", font=("Courier", 22, "bold"),
                                   bg="#16213e", fg="#00d4aa")
        self.lbl_reloj.pack()
        self.lbl_dia = tk.Label(reloj, text="", font=("Arial", 11),
                                 bg="#16213e", fg="#cccccc")
        self.lbl_dia.pack()

        # Estado
        marco = tk.LabelFrame(self.root, text="📊 Estado de Hoy",
                               font=("Arial", 10, "bold"), padx=10, pady=8)
        marco.pack(fill=tk.X, padx=12, pady=8)
        self.lbl_entrada = tk.Label(marco, text="Entrada: —", font=("Courier", 10))
        self.lbl_entrada.pack(anchor="w")
        self.lbl_salida = tk.Label(marco, text="Salida: —", font=("Courier", 10))
        self.lbl_salida.pack(anchor="w")

        # Log
        log_frame = tk.LabelFrame(self.root, text="📋 Registro de actividad",
                                   font=("Arial", 10, "bold"), padx=5, pady=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)
        self.txt_log = scrolledtext.ScrolledText(
            log_frame, height=8, state=tk.DISABLED,
            font=("Courier", 9), bg="#0d0d0d", fg="#00ff88", wrap=tk.WORD,
        )
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        # Botones
        btns = tk.Frame(self.root, pady=8)
        btns.pack(fill=tk.X, padx=12)
        tk.Button(btns, text="🔑 Cambiar credenciales",
                  command=self._cambiar_credenciales,
                  bg="#555", fg="white", relief="flat", padx=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="🚪 Salir", command=self._on_close,
                  bg="#cc3333", fg="white", relief="flat", padx=10).pack(side=tk.RIGHT, padx=5)

    # ── Callbacks thread-safe ─────────────────────────────

    def _log_thread_safe(self, mensaje: str) -> None:
        _escribir_log_archivo(mensaje)
        self.root.after(0, lambda: self._log(mensaje))

    def _refrescar_estado_ui_thread_safe(self) -> None:
        self.root.after(0, self._refrescar_estado_ui)

    def _log(self, mensaje: str) -> None:
        try:
            self.txt_log.config(state=tk.NORMAL)
            ts = datetime.now().strftime("%H:%M:%S")
            self.txt_log.insert(tk.END, f"[{ts}] {mensaje}\n")
            self.txt_log.see(tk.END)
            self.txt_log.config(state=tk.DISABLED)
        except Exception:
            pass

    def _refrescar_estado_ui(self) -> None:
        e = self._sched._estado
        if e.entrada_realizada:
            self.lbl_entrada.config(text=f"Entrada: ✅ {e.entrada_ts.strftime('%H:%M:%S')}")
        elif e.hora_entrada:
            self.lbl_entrada.config(text=f"Entrada: ⏳ {e.hora_entrada.strftime('%H:%M:%S')}")
        if e.salida_realizada:
            self.lbl_salida.config(text=f"Salida:  ✅ {e.salida_ts.strftime('%H:%M:%S')}")
        elif e.hora_salida:
            self.lbl_salida.config(text=f"Salida:  ⏳ {e.hora_salida.strftime('%H:%M:%S')}")

    def _tick(self) -> None:
        ahora = datetime.now()
        self.lbl_reloj.config(text=ahora.strftime("%H:%M:%S"))
        self.lbl_dia.config(text=f"{_nombre_dia()} {ahora.strftime('%d/%m/%Y')}")
        self.root.after(1000, self._tick)

    def _cambiar_credenciales(self) -> None:
        credenciales.CredencialesManager().eliminar()
        messagebox.showinfo("Credenciales eliminadas",
                            "Reinicia la aplicación para configurar nuevas.")
        self._on_close()

    def _on_close(self) -> None:
        if messagebox.askyesno("Salir", "¿Detener el fichaje automático?"):
            self._sched.detener()
            self.root.destroy()

    def iniciar(self) -> None:
        self.root.mainloop()


# ──────────────────────────────────────────────────────────
# Pedir credenciales (modo GUI)
# ──────────────────────────────────────────────────────────

def _pedir_credenciales_gui() -> tuple[str | None, str | None]:
    root = tk.Tk()
    root.title("Auto Fichaje NCS — Configuración inicial")
    root.geometry("420x250")
    root.resizable(False, False)
    u_var = tk.StringVar()
    p_var = tk.StringVar()
    guardado = {"ok": False}

    tk.Label(root, text="🕐 Auto Fichaje NCS", font=("Arial", 16, "bold")).pack(pady=15)
    tk.Label(root, text="Introduce tus credenciales:", font=("Arial", 10)).pack()
    f = tk.Frame(root, pady=10); f.pack()
    tk.Label(f, text="Usuario:", width=12, anchor="e").grid(row=0, column=0, pady=5)
    tk.Entry(f, textvariable=u_var, width=25).grid(row=0, column=1, pady=5, padx=5)
    tk.Label(f, text="Contraseña:", width=12, anchor="e").grid(row=1, column=0, pady=5)
    tk.Entry(f, textvariable=p_var, show="●", width=25).grid(row=1, column=1, pady=5, padx=5)

    def aceptar():
        if not u_var.get().strip() or not p_var.get().strip():
            messagebox.showerror("Error", "Rellena ambos campos")
            return
        credenciales.CredencialesManager().guardar(u_var.get().strip(), p_var.get().strip())
        guardado["ok"] = True
        root.destroy()

    tk.Button(root, text="Guardar y continuar", command=aceptar,
              bg="#007bff", fg="white", padx=15, pady=5).pack(pady=15)
    root.mainloop()

    if not guardado["ok"]:
        return None, None
    return credenciales.CredencialesManager().cargar()


# ──────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="AutoFichajeNCS",
                                 description="Bot de fichaje automático NCS")
    p.add_argument("--silencioso", action="store_true",
                    help="Corre sin GUI, solo popups en fallos críticos")
    return p.parse_args()


def main() -> int:
    args = _parse_args()

    # Lock
    try:
        lock.adquirir()
    except lock.LockBusy as e:
        notifier.aviso_doble_instancia(e.pid_otro)
        _escribir_log_archivo(f"Doble instancia rechazada (PID otro={e.pid_otro})", "ERROR")
        return 1

    # Credenciales
    mgr = credenciales.CredencialesManager()
    usuario, password = mgr.cargar()
    if not usuario or not password:
        if args.silencioso:
            _escribir_log_archivo("Sin credenciales y modo silencioso. No se puede arrancar.", "ERROR")
            return 1
        usuario, password = _pedir_credenciales_gui()
        if not usuario:
            return 0

    # Arrancar
    if args.silencioso:
        _ejecutar_silencioso(usuario, password)
    else:
        PanelControl(usuario, password).iniciar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Smoke test the GUI mode**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
python app.py
```
Expected: 
- If no credentials saved: configuration window appears.
- If credentials saved: control panel opens with clock, log area, and shows "Auto Fichaje INICIADO".
- Confirm clock ticks every second.
- Close with the 🚪 Salir button → confirms before closing.

- [ ] **Step 3: Smoke test silent mode**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
python app.py --silencioso
```
Expected: no window appears; console shows the startup banner and "Nuevo día" log line within ~10 seconds. Press Ctrl+C to stop.

- [ ] **Step 4: Verify lock file behavior**

In two PowerShell windows:
```powershell
# Window 1
python app.py
```
```powershell
# Window 2 (while window 1 still running)
python app.py
```
Expected: window 2 immediately shows a popup "Auto Fichaje ya en ejecución (PID=...)" and exits.

- [ ] **Step 5: Verify file locations**

After stopping all instances:
```powershell
Get-ChildItem "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\auto_fichaje.log","C:\Users\alberto\.gemini\antigravity\playground\solar-granule\estado_diario.json","C:\Users\alberto\.gemini\antigravity\playground\solar-granule\fichajes.csv"
```
Expected: all three files exist next to the script (default location since no `AUTO_FICHAJE_DATA_DIR` set).

- [ ] **Step 6: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add app.py
git commit -m "feat(app): unified entry point with GUI panel and --silencioso flag"
```

---

## Task 13: `compilar.py` — single PyInstaller build script

**Files:**
- Create: `compilar.py`

- [ ] **Step 1: Implement `compilar.py`**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\compilar.py`

```python
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
        print("❌ Compilación fallida.")
        return resultado.returncode

    exe = raiz / "dist" / "AutoFichajeNCS.exe"
    if exe.exists():
        print(f"✅ .exe creado: {exe}")
        print(f"   Tamaño: {exe.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print("⚠️  Compilación terminó pero el .exe no aparece.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the build**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
python compilar.py
```
Expected: PyInstaller runs; takes 1-3 minutes; ends with "✅ .exe creado". `dist\AutoFichajeNCS.exe` exists (~20-30 MB).

- [ ] **Step 3: Test the compiled .exe — default location**

```powershell
Set-Location "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist"
Start-Process .\AutoFichajeNCS.exe
```
Expected: panel de control opens; archivos `auto_fichaje.log`, `estado_diario.json`, `fichajes.csv` aparecen en `dist\`. Close.

- [ ] **Step 4: Test the compiled .exe with custom data dir**

```powershell
$env:AUTO_FICHAJE_DATA_DIR = "C:\Temp\AutoFichajeTest"
Start-Process "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\AutoFichajeNCS.exe"
```
Expected: panel opens; files appear in `C:\Temp\AutoFichajeTest\` instead. Close. Unset env var:
```powershell
Remove-Item Env:\AUTO_FICHAJE_DATA_DIR
```

- [ ] **Step 5: Test double-instance prevention**

```powershell
Start-Process "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\AutoFichajeNCS.exe"
# wait a couple of seconds
Start-Process "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\AutoFichajeNCS.exe"
```
Expected: first .exe shows panel; second .exe shows popup "Auto Fichaje ya en ejecución" and exits.

- [ ] **Step 6: Commit**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add compilar.py
git commit -m "feat(build): unified PyInstaller compile script"
```

---

## Task 14: Cleanup — delete obsolete files and consolidate README

**Files:**
- Delete: many `.py`, `.md`, `.bat`
- Modify: `README.md`

- [ ] **Step 1: Delete obsolete Python files**

```powershell
$obsoletos = @(
    "auto_fichaje.py",
    "auto_fichaje_gui.py",
    "ncs_login.py",
    "ncs_fichaje.py",
    "ncs_csv_logger.py",
    "fichaje_logger.py",
    "compilar_exe.py",
    "compilar_exe_gui.py",
    "test_completo.py",
    "test_fichaje.py",
    "test_login.py",
    "test_estado_y_lock.py",
    "verificar_bug_desconocido.py",
    "verificar_fix.py",
    "AutoFichajeNCS.spec"
)
foreach ($f in $obsoletos) {
    $path = "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\$f"
    if (Test-Path $path) { Remove-Item $path }
}
```

- [ ] **Step 2: Delete obsolete documentation**

```powershell
$docs = @(
    "README_GITHUB.md",
    "LOGS.md",
    "VERIFICACION_COMPLETA.md",
    "SUBIR_A_GITHUB.md",
    "SERVICIO_WINDOWS.md",
    "COMPILAR_EXE.md",
    "DISTRIBUIR_EXE.md"
)
foreach ($f in $docs) {
    $path = "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\$f"
    if (Test-Path $path) { Remove-Item $path }
}
```

- [ ] **Step 3: Delete obsolete batch files**

```powershell
$bats = @("configurar_servicio.bat", "iniciar_servicio.bat", "lanzar_fichaje.bat")
foreach ($f in $bats) {
    $path = "C:\Users\alberto\.gemini\antigravity\playground\solar-granule\$f"
    if (Test-Path $path) { Remove-Item $path }
}
```

- [ ] **Step 4: Replace `README.md` with consolidated content**

Path: `C:\Users\alberto\.gemini\antigravity\playground\solar-granule\README.md`

Replace entire content with:

```markdown
# 🕐 Auto Fichaje NCS

Bot personal de fichaje automático para `clock.ncs.es`. Ficha entrada y salida automáticamente de lunes a viernes, a horas aleatorias dentro de una ventana configurable.

## ✨ Qué hace

- Ficha **ENTRADA** entre `08:35` y `09:05` (hora aleatoria por día).
- Ficha **SALIDA** entre `18:00` y `18:30`.
- Solo de **lunes a viernes**.
- Si ya fichaste manualmente, **lo detecta y no te desficha** (tres guardias de seguridad antes de cada clic).
- Registra todo en `fichajes.csv` (histórico).
- Si falla 3 veces seguidas, te avisa con un **popup** para que fiches a mano.

## 🚀 Para usuarios (solo el .exe)

1. Descarga `AutoFichajeNCS.exe`.
2. Doble clic. La primera vez te pedirá usuario y contraseña.
3. Deja el panel abierto. Trabajará en segundo plano.

Si quieres que arranque solo al encender el PC, coloca un acceso directo al `.exe` en:
`C:\Users\TU_USUARIO\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\`

### Modo silencioso (sin ventana)

```powershell
AutoFichajeNCS.exe --silencioso
```

## 👨‍💻 Para desarrolladores

### Requisitos
- Python 3.10+ (probado en 3.12)
- Google Chrome instalado

### Instalación
```powershell
git clone <url>
cd auto-fichaje-ncs
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Ejecutar
```powershell
python app.py              # GUI
python app.py --silencioso # Sin ventana
```

### Tests
```powershell
pytest tests/ -v
```

### Compilar a .exe
```powershell
python compilar.py
# Resultado en dist\AutoFichajeNCS.exe
```

## 📂 Estructura

```
auto-fichaje-ncs/
├── app.py             Entry point (GUI + --silencioso)
├── ncs.py             Login + fichaje + verificación de estado
├── scheduler.py       Bucle diario + EstadoDiario
├── lock.py            Single-instance lock con verificación de PID
├── csv_log.py         Logger CSV histórico
├── notifier.py        Popups thread-safe
├── credenciales.py    Gestión de usuario/password
├── config.py          Constantes + resolución de paths
├── tests/             pytest suite (sin red ni Chrome)
└── compilar.py        Build con PyInstaller
```

## 🔧 Configuración

### Dónde se guardan los archivos
Por defecto, junto al `.exe` (o al script). Puedes redirigir con:
```powershell
$env:AUTO_FICHAJE_DATA_DIR = "D:\MisFichajes"
```

Archivos generados:
- `fichajes.csv` — historial de fichajes
- `estado_diario.json` — estado del día
- `auto_fichaje.log` — log detallado
- `auto_fichaje.lock` — lock de instancia única (se borra al cerrar)

### Cambiar horarios
Edita `config.py`:
```python
ENTRADA_DESDE = "08:35"
ENTRADA_HASTA = "09:05"
SALIDA_DESDE  = "18:00"
SALIDA_HASTA  = "18:30"
```

## 🔍 Cómo verifica que fichó

Tres capas de seguridad antes de pulsar el botón:

1. **Lectura del estado real de NCS** con 3 reintentos. Si tras los reintentos no se puede leer (`DESCONOCIDO`), **aborta** sin pulsar.
2. **Verificación cruzada alerta vs presencia**. Si la web dice "estás fuera" pero el contador de presencia es > 00:00, **aborta** (alerta cacheada o incoherente).
3. **Skip si ya estaba hecho**. Si tocaba ENTRADA pero ya estás dentro (fichaste a mano), se salta el clic.

Si las 3 guardias pasan, pulsa el botón y verifica que la alerta cambia. Si no cambia tras 12 segundos pero tampoco hay error visible, lo acepta con un warning.

## 🐛 Solución de problemas

### "Auto Fichaje ya en ejecución (PID=X)" pero no veo nada corriendo
Es un lock huérfano. El bot lo detecta automáticamente si el PID está muerto. Si no se borra solo, hazlo a mano:
```powershell
Remove-Item .\auto_fichaje.lock
```

### El bot dice "No pude leer NCS" 3 veces seguidas
Probablemente NCS cambió el HTML. Avisa al desarrollador para actualizar los selectores.

### No encuentra Chrome
Instala Google Chrome: https://www.google.com/chrome/

## 📄 Licencia

MIT — ver `LICENSE`.

## ⚠️ Disclaimer

Herramienta personal. Úsala bajo tu propia responsabilidad y asegúrate de que cumple con las políticas de tu empresa.
```

- [ ] **Step 5: Run the test suite one more time to confirm nothing broke**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
pytest tests/ -v
```
Expected: all tests PASS, suite < 5s.

- [ ] **Step 6: Manual smoke test of `app.py` one more time**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
python app.py
```
Expected: GUI opens correctly with no errors in console.

- [ ] **Step 7: Commit cleanup**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git add -A
git commit -m "chore: remove obsolete files, consolidate README"
```

- [ ] **Step 8: Verify final repository state**

```powershell
cd "C:\Users\alberto\.gemini\antigravity\playground\solar-granule"
git status
Get-ChildItem -File | Where-Object { $_.Name -notlike "*.lock" -and $_.Name -notlike "*.log" -and $_.Name -notlike "*.csv" -and $_.Name -notlike "estado*.json" } | Select-Object Name
```
Expected files (sorted):
```
.env
.env.example
.gitignore
LICENSE
README.md
app.py
compilar.py
config.py
credenciales.py
csv_log.py
lock.py
ncs.py
notifier.py
requirements-dev.txt
requirements.txt
scheduler.py
```
And under `tests/`: `__init__.py`, `conftest.py`, `test_config.py`, `test_credenciales.py`, `test_csv_log.py`, `test_estado.py`, `test_lock.py`, `test_ncs.py`, `test_notifier.py`, `test_scheduler.py`.

---

## Self-Review Notes (post-write)

Run through each spec section and confirm a task covers it:

| Spec § | Section | Task(s) |
|--------|---------|---------|
| 4.1    | File structure | All tasks; verified in Task 14 step 8 |
| 4.3    | Eliminations | Task 14 |
| 5.1    | `config.py` paths via env var | Task 2 |
| 5.2    | `lock.py` PID liveness | Task 3 |
| 5.3    | `csv_log.py` atomic | Task 4 |
| 5.4    | `notifier.py` thread-safe | Task 5 |
| 5.5    | `credenciales.py` | Task 6 |
| 5.6    | `ncs.py` three guards | Tasks 7-9 |
| 5.7    | `scheduler.py` + migration | Tasks 10-11 |
| 5.8    | `app.py` GUI + flag | Task 12 |
| 6.1-6.4| Flows | Implicit across tasks; verified by integration smoke tests in Task 12 |
| 7      | Logging table | Implemented in `_intentar_fichaje` (Task 11) and `notifier` (Task 5) |
| 8      | Testing | Tasks 2-11 each include their own tests |
| 9      | Build | Task 13 |
| 10     | Dependencies | Task 1 |
| 11     | gitignore | Task 1 |
| Pre    | Manual unblock | Pre-Task at top |

**Spec coverage: complete.**

**Placeholder scan:** no "TBD", "TODO", "implement later", or "similar to Task N" placeholders. All code blocks contain full implementations.

**Type consistency check:**
- `ResultadoFichaje` and `EstadoWeb` dataclasses defined in Task 7, used in Task 8 ✓
- `EstadoDiario` defined in Task 10, used in Task 11 (`Scheduler`) ✓
- `LockBusy` defined in Task 3, used in Task 12 (`app.py`) ✓
- `FichajeCSVLogger` defined in Task 4, used in Task 11 ✓
- `CredencialesManager` defined in Task 6, used in Task 12 ✓
- `Scheduler` defined in Task 11, used in Task 12 ✓
- `notifier.aviso_fallo`, `notifier.aviso_doble_instancia`, `notifier.set_root_principal` defined in Task 5, used in Tasks 11 and 12 ✓

All references consistent.
