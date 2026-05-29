# Refactor de Auto Fichaje NCS: CSV configurable, aviso de fallo y unificación CLI+GUI

**Fecha**: 2026-05-29
**Estado**: Aprobado por el usuario, pendiente de plan de implementación
**Autor**: Brainstorming colaborativo (Claude + usuario)

## 1. Contexto y motivación

El proyecto `auto-fichaje-ncs` es un bot que ficha automáticamente en `clock.ncs.es` de lunes a viernes. Su estado actual presenta tres problemas que esta refactor aborda:

1. **El sistema lleva inoperativo desde el 2026-03-27**. Un archivo `auto_fichaje.lock` huérfano (PID 37820 ya muerto) bloquea cada arranque programado. El `fichajes.csv` solo registra 3 días en total y la última entrada es del 27/03. Verificado leyendo `auto_fichaje.log`: cada día desde el 28/03 contiene `[ERROR] Ya hay una instancia corriendo`.

2. **Bug crítico de "desfichaje"**. Cuando `ncs_fichaje.detectar_estado_fichaje()` no encuentra la alerta de NCS en la página tras el login, devuelve `"DESCONOCIDO"`. La lógica actual responde con `"se intentará fichar igualmente"` y pulsa `#btnTicar` a ciegas. Como NCS funciona en modo toggle, si el usuario ya había fichado a mano, el clic le **desficha** y el bot lo reporta como `success=True` ("Fichaje procesado sin cambio de estado visible"). Este bug ha sido reproducido empíricamente con un mock unitario (`verificar_bug_desconocido.py`).

3. **Deuda técnica acumulada**. Código duplicado entre CLI y GUI (dos `EstadoDiario` distintos que escriben el mismo JSON con esquemas incompatibles), paths relativos que rompen al lanzar desde Task Scheduler, threading inseguro en Tkinter, archivos muertos (`fichaje_logger.py`, `README_GITHUB.md`) y 6 documentos Markdown que describen versiones obsoletas del sistema.

A la vez, el usuario pide nuevas mejoras:
- Un CSV histórico con horas de entrada, salida y horas trabajadas, accesible aunque el `.exe` se mueva.
- Un aviso activo (popup) cuando el fichaje falla tras agotar reintentos.
- Entender y reforzar cómo el sistema verifica que ha fichado.

Esta refactor mata todo en un único cambio coherente.

## 2. Objetivos

- **No volver a desfichar al usuario nunca**. Verificación de estado a prueba de balas.
- **Reorganizar el código**: de 13 `.py` a 14 (8 de aplicación, 5 de test, 1 de build), eliminando duplicación de ~500 LOC entre CLI y GUI y dándole un único propósito claro a cada archivo. Documentación de 8 `.md` a 1.
- **Unificar CLI y GUI** en un único `.exe` con flag `--silencioso`.
- **Paths robustos**: el `.exe` debe encontrar sus archivos sin importar desde dónde se lance.
- **Aviso activo de fallos** mediante popup modal Tkinter, disparado solo tras agotar reintentos.
- **Tests automatizados** que ejecuten en menos de 5s sin red ni navegador.

## 3. No-objetivos

- No se reescriben las heurísticas de "comportamiento humano" (pausas aleatorias, escritura carácter a carácter): funcionan.
- No se cambia el formato del CSV salvo lo estrictamente necesario.
- No se añade rotación mensual del CSV (el usuario prefiere un único archivo histórico).
- No se sustituye Selenium por otra librería.
- No se hace el sistema multiusuario (queda como herramienta personal).
- No se añade integración con calendarios o festivos (queda para futuro, fuera de scope).

## 4. Arquitectura

### 4.1 Estructura de archivos final

```
auto-fichaje-ncs/
├── app.py             # Entry point: parser de args, modo GUI/silencioso, arranque
├── ncs.py             # Login + fichaje + verificación de estado de NCS (lo único que sabe del HTML)
├── scheduler.py       # Bucle diario, EstadoDiario, cálculo de horas aleatorias
├── lock.py            # Lock con verificación de PID vivo
├── csv_log.py         # FichajeCSVLogger histórico (sin rotación)
├── notifier.py        # Popup modal thread-safe
├── config.py          # Constantes + resolución de paths vía AUTO_FICHAJE_DATA_DIR
├── credenciales.py    # CredencialesManager (cifrado b64 en AppData)
├── tests/
│   ├── test_lock.py
│   ├── test_estado.py
│   ├── test_ncs.py
│   ├── test_csv_log.py
│   └── test_scheduler.py
├── compilar.py        # PyInstaller spec único
├── README.md          # Único documento, consolidando los 6 actuales
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── AutoFichajeNCS.spec
```

### 4.2 Dependencias entre módulos (sin ciclos)

```
                       config.py
                          ↑
       ┌──────────────────┼──────────────────────────┐
   lock.py            csv_log.py     notifier.py     ncs.py    credenciales.py
       ↑                  ↑              ↑             ↑              ↑
       └──────────────────┴──────────────┴─────────────┴──────────────┘
                                  │
                            scheduler.py
                                  ↑
                                app.py
```

`config.py` no depende de nada del proyecto. Los módulos de bajo nivel solo dependen de `config`. `scheduler.py` orquesta y `app.py` arranca.

### 4.3 Eliminaciones definitivas

**Borrados** (toda su funcionalidad cubierta en módulos nuevos o información obsoleta):

| Archivo                       | Razón |
|-------------------------------|-------|
| `auto_fichaje.py`             | Reemplazado por `app.py` + `scheduler.py` |
| `auto_fichaje_gui.py`         | Idem, GUI integrada en `app.py` |
| `ncs_login.py`                | Fusionado en `ncs.py` |
| `ncs_fichaje.py`              | Fusionado en `ncs.py` |
| `ncs_csv_logger.py`           | Renombrado `csv_log.py` |
| `fichaje_logger.py`           | No usado por nadie (verificado con grep) |
| `compilar_exe.py`             | Reemplazado por `compilar.py` único |
| `compilar_exe_gui.py`         | Idem |
| `README_GITHUB.md`            | Duplicado byte a byte de `README.md` |
| `LOGS.md`                     | Info obsoleta; lo esencial pasa al README |
| `VERIFICACION_COMPLETA.md`    | Describe una versión antigua del sistema |
| `SUBIR_A_GITHUB.md`           | Información ya en cualquier guía de git |
| `SERVICIO_WINDOWS.md`         | Sustituido por instrucción única en README (carpeta Inicio) |
| `COMPILAR_EXE.md`             | Reemplazado por sección en README |
| `DISTRIBUIR_EXE.md`           | Idem |
| `configurar_servicio.bat`     | Sustituido por instrucción de Task Scheduler en README |
| `iniciar_servicio.bat`        | Idem |
| `lanzar_fichaje.bat`          | El `.exe` se ejecuta solo, no necesita launcher |
| `test_completo.py`            | Reemplazado por suite en `tests/` |
| `test_fichaje.py`             | Idem |
| `test_login.py`               | Idem |
| `test_estado_y_lock.py`       | Idem |

**Conservados sin cambios**: `.env.example`, `LICENSE`, `requirements.txt` (con dos líneas añadidas), `.gitignore` (con tres entradas añadidas).

## 5. Detalle de cada módulo

### 5.1 `config.py`

**Qué hace**: define todas las constantes y resuelve dónde viven los archivos en tiempo de ejecución.

**Resolución de paths**:
```python
def _data_dir() -> Path:
    """
    1. AUTO_FICHAJE_DATA_DIR si está definido y es escribible.
    2. Si el proceso está congelado (PyInstaller): carpeta del .exe.
    3. Modo desarrollo: carpeta del script.
    """
    env = os.getenv("AUTO_FICHAJE_DATA_DIR")
    if env:
        p = Path(env).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent

DATA_DIR        = _data_dir()
CSV_FICHAJES    = DATA_DIR / "fichajes.csv"
ESTADO_FILE     = DATA_DIR / "estado_diario.json"
LOCK_FILE       = DATA_DIR / "auto_fichaje.lock"
LOG_FILE        = DATA_DIR / "auto_fichaje.log"
```

**Constantes que se quedan**: `ENTRADA_DESDE`, `ENTRADA_HASTA`, `SALIDA_DESDE`, `SALIDA_HASTA`, `DIAS_LABORABLES`, `MAX_REINTENTOS`, `BACKOFF_REINTENTOS`, `MARGEN_VENTANA_EXTRA`, `URL_FICHAJE`, selectores CSS.

**Constantes eliminadas**: `URL_LOGIN` (no usada por nadie tras inspección).

### 5.2 `lock.py`

**Qué hace**: garantiza una sola instancia y detecta locks huérfanos (el bug que tenías).

**API pública**:
```python
class LockBusy(Exception):
    """Otra instancia viva tiene el lock."""

def adquirir() -> None:
    """
    Si existe LOCK_FILE: lee el PID; si vive, raise LockBusy;
    si no, sobrescribe (log WARNING "lock huérfano detectado").
    Escribe el PID actual y registra atexit(liberar).
    """

def liberar() -> None:
    """Borra LOCK_FILE si existe. Idempotente."""

def _pid_vivo(pid: int) -> bool:
    """psutil.pid_exists(pid). Funciona en Windows."""
```

**Dependencia nueva**: `psutil` en `requirements.txt`.

**Detalle de la verificación de PID en Windows**: `psutil.pid_exists()` usa la API nativa `OpenProcess`. Si el PID está libre o asignado a otro proceso, devuelve False (en realidad puede haber reciclaje del PID; el riesgo es despreciable porque adicionalmente comprobaremos que el "iniciado" del lock no es de hace más de 24h: si lo es, también consideramos el lock como huérfano).

### 5.3 `csv_log.py`

**Qué hace**: gestión de `fichajes.csv` único histórico.

**API**:
```python
class FichajeCSVLogger:
    FIELDS = ["fecha", "hora_entrada", "hora_salida",
              "total_horas", "jornada", "extra_ausencia", "observaciones"]

    def __init__(self, path: Path = CSV_FICHAJES) -> None: ...
    def registrar_entrada(self, hora: str, observaciones: str = "") -> None: ...
    def registrar_salida(self, hora: str, presencia: str, jornada: str,
                          extra: str, observaciones: str = "") -> None: ...
    def obtener_registro_hoy(self) -> dict | None: ...
    def resumen_mes(self, mes: int, año: int) -> list[dict]: ...
```

**Cambios respecto a `ncs_csv_logger.py` actual**:
- Escritura atómica (`tmp` → `os.replace`).
- Path tomado de `config.CSV_FICHAJES`, no hardcoded.
- Sin emojis en `print()` (resuelve el bug de `charmap` reproducido en `auto_fichaje.log:14`).
- Si el archivo tiene cabeceras diferentes (proyecto migrado), se respeta y se añade con compatibilidad.

### 5.4 `notifier.py`

**Qué hace**: aísla los popups del scheduler. Funciona aunque la GUI principal esté cerrada (modo `--silencioso`).

**API**:
```python
def aviso_fallo(tipo: str, motivo: str, html_cambio: bool = False) -> None:
    """
    Lanza un popup modal de error.
    - Si hay una root Tk activa (modo GUI): usa root.after(0, ...)
      para mostrar el messagebox en el event loop principal.
    - Si no (modo --silencioso): crea una Tk root temporal en un
      hilo aparte, muestra el messagebox, la destruye.
    El messagebox es bloqueante para el usuario pero no para el scheduler.

    Si html_cambio=True, el mensaje incluye: "La web NCS pudo haber
    cambiado. Avisa al desarrollador."
    """

def aviso_doble_instancia(pid_otro: int) -> None:
    """Popup específico: 'Ya hay otra instancia (PID=X). Esta no arrancará.'"""
```

**Implementación del modo silencioso**:
```python
def _popup_aislado(titulo: str, mensaje: str, icono: str):
    """Tk root efímera en hilo aparte; no toca otras instancias Tk."""
    def _show():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(titulo, mensaje, parent=root, icon=icono)
        root.destroy()
    threading.Thread(target=_show, daemon=False).start()
```

`daemon=False` para que el popup no muera si el scheduler termina mientras está visible.

### 5.5 `credenciales.py`

**Qué hace**: persistencia de usuario/password en `%LOCALAPPDATA%\AutoFichajeNCS\config.dat`, cifrado base64.

Se extrae idéntico de `auto_fichaje_gui.py:142-170` (clase `CredencialesManager`). La carpeta `AppData\Local\AutoFichajeNCS\` se conserva para no romper las credenciales existentes de usuarios actuales.

**Nota**: el cifrado base64 NO es seguridad real (es ofuscación). Mantenemos la decisión actual del proyecto; un futuro endurecimiento queda fuera de scope.

### 5.6 `ncs.py` — el módulo crítico

**Qué hace**: fusiona `ncs_login.py` y `ncs_fichaje.py`. Todo lo que sabe del HTML de NCS vive aquí.

**API**:
```python
@dataclass
class EstadoWeb:
    accion_siguiente: Literal["ENTRADA", "SALIDA", "DESCONOCIDO"]
    presencia_actual: str   # "HH:MM"
    coherente: bool         # alerta y presencia concuerdan

@dataclass
class ResultadoFichaje:
    success: bool
    saltado: bool           # True si se omitió porque ya estaba hecho
    tipo: str               # "ENTRADA" | "SALIDA"
    hora_fichaje: str       # "HH:MM:SS" o ""
    presencia: str
    jornada: str
    extra: str
    mensaje: str
    html_cambio: bool       # True si pinta que NCS cambió el HTML

def crear_navegador() -> webdriver.Chrome: ...
def realizar_login(driver, usuario: str, password: str) -> bool: ...
def leer_estado_seguro(driver, intentos: int = 3, espera: float = 2.0) -> EstadoWeb: ...
def realizar_fichaje(driver, tipo_esperado: str) -> ResultadoFichaje: ...
```

**El cambio crítico — `realizar_fichaje` nunca pulsa a ciegas**:
```python
def realizar_fichaje(driver, tipo_esperado):
    estado = leer_estado_seguro(driver, intentos=3, espera=2.0)

    # GUARDIA 1: estado no leído tras 3 reintentos → abortar
    if estado.accion_siguiente == "DESCONOCIDO":
        return ResultadoFichaje(
            success=False, saltado=False, tipo=tipo_esperado,
            mensaje="No se pudo leer el estado en NCS tras 3 intentos. "
                    "Aborto por seguridad para no desfichar.",
            html_cambio=True,
            hora_fichaje="", presencia="", jornada="", extra="",
        )

    # GUARDIA 2: alerta y presencia incoherentes → abortar
    if not estado.coherente:
        return ResultadoFichaje(
            success=False, saltado=False, tipo=tipo_esperado,
            mensaje=f"Alerta y presencia no coinciden ({estado.accion_siguiente} "
                    f"vs presencia={estado.presencia_actual}). Aborto.",
            html_cambio=True,
            hora_fichaje="", presencia="", jornada="", extra="",
        )

    # GUARDIA 3: si tocaba ENTRADA pero ya estás dentro → skip (no es fallo)
    if tipo_esperado == "ENTRADA" and estado.accion_siguiente == "SALIDA":
        return ResultadoFichaje(
            success=True, saltado=True, tipo=tipo_esperado,
            mensaje="Ya estás DENTRO; entrada omitida.",
            hora_fichaje="", presencia=estado.presencia_actual,
            jornada="", extra="", html_cambio=False,
        )
    if tipo_esperado == "SALIDA" and estado.accion_siguiente == "ENTRADA":
        return ResultadoFichaje(
            success=True, saltado=True, tipo=tipo_esperado,
            mensaje="Ya estás FUERA; salida omitida.",
            hora_fichaje="", presencia=estado.presencia_actual,
            jornada="", extra="", html_cambio=False,
        )

    # SOLO AQUÍ se pulsa el botón
    return _pulsar_y_verificar(driver, tipo_esperado, estado)
```

**Coherencia alerta vs presencia** (tabla):

| `accion_siguiente` | `presencia` | Coherente |
|-------------------|-------------|-----------|
| ENTRADA           | `00:00`     | Sí        |
| ENTRADA           | `>00:00`    | **NO** (alerta dice fuera, presencia dice que estuviste) |
| SALIDA            | `>00:00`    | Sí        |
| SALIDA            | `00:00`     | **NO**    |

Esto se implementa en `leer_estado_seguro()`.

### 5.7 `scheduler.py`

**Qué hace**: bucle diario, persistencia de estado, decisión de cuándo fichar.

**API**:
```python
@dataclass
class EstadoDiario:
    fecha: str                    # "YYYY-MM-DD"
    hora_entrada: datetime | None
    hora_salida: datetime | None
    entrada_ts: datetime | None
    salida_ts: datetime | None
    reintentos_entrada: int
    reintentos_salida: int

    def guardar(self) -> None: ...                    # Atómico
    @classmethod
    def cargar(cls) -> "EstadoDiario": ...
    def es_dia_completado(self) -> bool: ...

class Scheduler:
    def __init__(self, usuario: str, password: str,
                  on_log: Callable[[str], None],
                  on_estado_cambia: Callable[[], None] | None = None) -> None: ...
    def ejecutar(self) -> None: ...
    def detener(self) -> None: ...
```

**`on_log`**: callback inyectado. La GUI usa una lambda que escribe en `ScrolledText` vía `root.after(0, ...)`; el modo silencioso usa una lambda que solo escribe al log file. Esto deja `scheduler.py` independiente de Tkinter.

**`on_estado_cambia`**: callback opcional para que la GUI refresque su panel cuando entrada/salida se marquen como hechas.

**Migración del JSON legacy** dentro de `EstadoDiario.cargar()`:
```python
LEGACY_KEY_MAPPINGS = {
    # CLI legacy
    "hora_entrada_random": "hora_entrada",
    "hora_salida_random": "hora_salida",
    "entrada_realizada_ts": "entrada_ts",
    "salida_realizada_ts": "salida_ts",
    # GUI legacy
    "entrada_realizada": "entrada_ts",  # bool → si True, usar 'ahora' como aprox.
    "salida_realizada": "salida_ts",
}

@classmethod
def cargar(cls):
    if not ESTADO_FILE.exists():
        return cls._vacio_hoy()
    raw = json.loads(ESTADO_FILE.read_text(encoding="utf-8"))
    if raw.get("fecha") != date.today().isoformat():
        return cls._vacio_hoy()
    migrado = cls._migrar_si_legacy(raw)
    if migrado != raw:
        log_info("Esquema de estado_diario.json migrado al formato nuevo")
        # Sobrescribir con el nuevo
        ESTADO_FILE.write_text(json.dumps(migrado, indent=2), encoding="utf-8")
    return cls(**migrado)
```

**Bucle principal** (similar al actual pero con la guardia de DESCONOCIDO integrada en `realizar_fichaje`):
```python
def ejecutar(self):
    while self._running:
        ahora = datetime.now()
        self._resetear_si_nuevo_dia(ahora)
        if not es_dia_laborable(): time.sleep(60); continue
        self._calcular_horarios_si_faltan()
        self._intentar_entrada_si_toca(ahora)
        self._intentar_salida_si_toca(ahora)
        time.sleep(60)
```

Cada `_intentar_*_si_toca()` mira ventana + reintentos, llama a `_fichaje_completo()`, gestiona reintentos y dispara `notifier.aviso_fallo()` cuando `reintentos == MAX_REINTENTOS`.

### 5.8 `app.py`

**Qué hace**: entry point. Parsea argumentos y arranca modo correspondiente.

```python
def main():
    args = _parse_args()
    try:
        lock.adquirir()
    except lock.LockBusy as e:
        notifier.aviso_doble_instancia(e.pid_otro)
        sys.exit(1)

    usuario, password = credenciales.cargar()
    if not usuario:
        if args.silencioso:
            sys.exit(1)  # no podemos pedirlas sin GUI
        usuario, password = _pedir_credenciales_gui()

    if args.silencioso:
        _ejecutar_sin_gui(usuario, password)
    else:
        _ejecutar_con_gui(usuario, password)
```

`_ejecutar_con_gui` instancia el panel Tkinter (similar al actual pero sin la clase `EstadoDiario` duplicada), arranca un hilo con `Scheduler.ejecutar()`, y los conecta con `on_log` y `on_estado_cambia` envueltos en `root.after(0, ...)`.

`_ejecutar_sin_gui` arranca `Scheduler.ejecutar()` directamente en el hilo principal.

## 6. Flujos clave

### 6.1 Día normal (caso feliz)

```
08:00  Scheduler.tick → laborable → calcula entrada=08:53, salida=18:18
08:53  Scheduler.tick → toca entrada
       → ncs.realizar_login → True
       → ncs.leer_estado_seguro → EstadoWeb(ENTRADA, "00:00", coherente=True)
       → click #btnTicar → alert cambia → ResultadoFichaje(success=True)
       → csv_log.registrar_entrada("08:53:12")
       → estado.entrada_ts = now() → guardar
18:18  idem para salida → csv_log.registrar_salida(...)
00:00  Scheduler detecta nuevo día → EstadoDiario.cargar reseteado
```

### 6.2 Usuario fichó manualmente, bot intenta ENTRADA

```
08:53  Scheduler.tick → toca entrada
       → ncs.leer_estado_seguro → EstadoWeb(SALIDA, "00:23", coherente=True)
                                  ↑ tú ya estás dentro hace 23 min
       → realizar_fichaje: tipo_esperado=ENTRADA pero estado=SALIDA → SKIP
       → ResultadoFichaje(success=True, saltado=True)
       → scheduler marca entrada como hecha, no incrementa reintentos
       → csv_log NO escribe (saltado, no hubo acción real)
```

### 6.3 NCS no responde con la alerta (el bug que rompía todo)

```
08:53  Scheduler.tick → toca entrada
       → ncs.leer_estado_seguro:
            intento 1: DESCONOCIDO  (espera 2s)
            intento 2: DESCONOCIDO  (espera 2s)
            intento 3: DESCONOCIDO
            → devuelve EstadoWeb(DESCONOCIDO, "", False)
       → realizar_fichaje: GUARDIA 1 dispara → ABORT, success=False, html_cambio=True
       → scheduler incrementa reintentos_entrada = 1
       → backoff: espera 5 minutos
08:58  Scheduler.tick → segundo intento → falla igual → reintentos=2
09:08  tercer intento → falla → reintentos=3
       → como reintentos==MAX_REINTENTOS:
            notifier.aviso_fallo("ENTRADA", "No se pudo leer NCS...", html_cambio=True)
       → POPUP MODAL: "No pude verificar tu estado en NCS. Ficha a mano."
```

**Punto crítico**: en ningún momento se pulsa `#btnTicar`. El usuario no es desfichado.

### 6.4 Lock huérfano tras crash anterior

```
Arranque del .exe el día 28 (proceso del día 27 murió con kill -9)
  → lock.adquirir():
       LOCK_FILE existe, PID=37820
       psutil.pid_exists(37820) → False
       → WARNING "lock huérfano (PID 37820 muerto), sobrescribiendo"
       → escribe LOCK_FILE con PID nuevo
  → Scheduler arranca normalmente (sin popup; entrada solo al log)
```

Decisión: el lock huérfano NO genera popup. Sería ruidoso en cada arranque tras corte de luz. Queda solo registrado en `auto_fichaje.log` con nivel WARNING. La función `notifier.aviso_lock_huerfano()` mencionada en la API de §5.4 queda eliminada del diseño final.

## 7. Logging y notificaciones

| Evento                                           | `auto_fichaje.log` | `fichajes.csv` | Popup |
|--------------------------------------------------|--------------------|----------------|-------|
| Arranque, configuración                          | INFO               | —              | —     |
| Cálculo de horarios del día                      | INFO               | —              | —     |
| Lock huérfano detectado y sobrescrito            | WARNING            | —              | INFO opcional |
| Migración de esquema JSON legacy                 | INFO               | —              | —     |
| Fichaje exitoso                                  | SUCCESS            | fila completa  | —     |
| Fichaje omitido (`saltado=True`)                 | WARNING            | (no escribe)   | —     |
| Login/click fallido (intento 1, 2 de 3)          | ERROR              | obs="ERROR..." | —     |
| Estado DESCONOCIDO tras reintentos (intento 1,2) | ERROR              | obs="ERROR..." | —     |
| Incoherencia alerta vs presencia                 | ERROR              | obs="ERROR..." | —     |
| 3er fallo (reintentos agotados)                  | ERROR              | obs="ERROR..." | **SÍ** |
| HTML cambió (botón no encontrado o DESCONOCIDO sostenido) | ERROR              | obs específica | **SÍ** (mensaje diferenciado: "Avisa al desarrollador") |
| Doble instancia detectada                        | ERROR              | —              | **SÍ** |

## 8. Testing

Suite en `tests/`, ejecutable con `pytest`. Sin red ni Chrome real.

### 8.1 `tests/test_lock.py`
```
test_lock_se_adquiere_si_no_existe
test_lock_rechaza_si_pid_vivo
test_lock_sobrescribe_si_pid_muerto       ← cierra el bug de 2 meses muerto
test_liberar_borra_archivo
test_atexit_libera_el_lock
test_lock_huerfano_si_iniciado_hace_mas_de_24h
```

### 8.2 `tests/test_estado.py`
```
test_estado_vacio_si_archivo_no_existe
test_estado_se_resetea_si_fecha_distinta
test_estado_persiste_horas_calculadas
test_marcar_entrada_y_salida
test_migracion_esquema_legacy_cli         ← lee tu estado_diario.json actual
test_migracion_esquema_legacy_gui
test_escritura_atomica_no_corrompe_si_falla
```

### 8.3 `tests/test_ncs.py` (los más críticos)
```
test_aborta_si_estado_desconocido_tras_reintentos    ← cierra bug DESFICHAJE
test_aborta_si_alerta_y_presencia_incoherentes        ← cierra bug DESFICHAJE
test_skip_si_ya_dentro_y_tipo_entrada
test_skip_si_ya_fuera_y_tipo_salida
test_ficha_normal_si_estado_coherente
test_no_se_pulsa_boton_si_login_falla
test_no_se_pulsa_boton_si_html_cambio
test_pulsa_boton_y_verifica_cambio_alerta
```

Los tres primeros tests críticos están **ya prototipados en `verificar_fix.py`** y verificados manualmente como PASS antes de aprobar este diseño.

### 8.4 `tests/test_csv_log.py`
```
test_crea_archivo_con_cabeceras_si_no_existe
test_registrar_entrada_crea_fila
test_registrar_salida_completa_fila_existente
test_salida_sin_entrada_crea_fila_con_aviso
test_resumen_mes_filtra_correctamente
test_escritura_atomica
```

### 8.5 `tests/test_scheduler.py`
```
test_no_actua_en_fin_de_semana
test_calcula_horas_solo_una_vez_al_dia
test_no_intenta_fichar_fuera_de_ventana_ampliada
test_dispara_notifier_solo_tras_max_reintentos
test_retoma_estado_tras_reinicio_del_proceso
test_marca_entrada_como_hecha_si_se_salta
```

### 8.6 Lo que NO se testea automáticamente

- Que NCS acepte el clic de verdad (requiere navegador real + credenciales).
- Que el popup Tkinter se renderice correctamente (verificación manual).
- Que el `.exe` compilado funcione (verificación manual tras `compilar.py`).

## 9. Build del `.exe`

```python
# compilar.py
import PyInstaller.__main__
import os

args = [
    "app.py",
    "--name=AutoFichajeNCS",
    "--onefile",
    "--windowed",
    "--add-data=.env.example;.",
    "--clean",
    "--noconfirm",
]
# Icono solo si el archivo existe (no se entrega como parte de este cambio)
if os.path.exists("icono.ico"):
    args.append("--icon=icono.ico")

PyInstaller.__main__.run(args)
```

Nota: `AutoFichajeNCS.spec` actual será regenerado por PyInstaller al primer `compilar.py`. Se borra del repo y se añade a `.gitignore`.

**Verificación manual post-build**:
1. `dist\AutoFichajeNCS.exe` se ejecuta → primera vez pide credenciales.
2. Mover el `.exe` a otra carpeta → `fichajes.csv` aparece junto al `.exe`.
3. `set AUTO_FICHAJE_DATA_DIR=C:\Temp\AF` → arranca, archivos en `C:\Temp\AF`.
4. Doble clic con instancia ya abierta → popup "Otra instancia corriendo (PID=X)".
5. Borrar `auto_fichaje.lock` y dejar uno falso con PID inventado → arranca, log WARNING.

## 10. Dependencias

**`requirements.txt`** (producción):
```
selenium
webdriver-manager
python-dotenv
psutil                ← NUEVA
```

**`requirements-dev.txt`** (nuevo):
```
pytest
pytest-mock
pyinstaller
```

## 11. Gitignore

Añadir:
```
auto_fichaje.lock
estado_diario.json
auto_fichaje.log
fichajes.csv
__pycache__/
build/
dist/
```

Los datos de runtime no deben versionarse (ya estaban siendo tracked por error).

## 12. Plan de orden y fases (alto nivel)

El plan de implementación detallado lo elaborará el siguiente paso (skill `writing-plans`). A alto nivel, esperamos una secuencia:

**Acción manual previa al plan**: borrar `auto_fichaje.lock` huérfano del repo para que el sistema actual vuelva a fichar mientras se hace el refactor. No requiere código; el usuario puede hacerlo en cuanto cierre el `.exe` actual.

1. **Fase 1 — Módulos sin estado**: `config.py`, `lock.py`, `csv_log.py`, `notifier.py`, `credenciales.py`. Cada uno con sus tests.
2. **Fase 2 — Módulo crítico**: `ncs.py` con `leer_estado_seguro` y guardias. Tests críticos (`test_ncs.py`).
3. **Fase 3 — Orquestación**: `scheduler.py` + migración JSON. Tests de scheduler.
4. **Fase 4 — Entry point**: `app.py` + GUI integrada. Verificación manual.
5. **Fase 5 — Build**: `compilar.py` + verificación manual del `.exe`.
6. **Fase 6 — Limpieza**: borrar archivos sustituidos, consolidar `README.md`, eliminar `verificar_*.py` ad-hoc.

Cada fase termina con commit verde y tests pasando antes de pasar a la siguiente.

## 13. Riesgos y mitigaciones

| Riesgo                                                            | Probabilidad | Mitigación |
|-------------------------------------------------------------------|--------------|-----------|
| La migración de JSON legacy pierde datos                          | Baja         | Tests específicos por esquema; los datos en juego son del día, no históricos |
| El usuario tiene un `fichajes.csv` "perdido" en otra carpeta      | Media        | README explica cómo localizar archivos con `where /R` y consolidar a mano |
| `psutil.pid_exists` da falso positivo por reciclaje de PID        | Muy baja     | Comprobación adicional: si "iniciado" del lock > 24h, también es huérfano |
| Tkinter en hilo background sigue siendo inestable a pesar de wrappers | Baja         | Tests manuales en sesiones largas; logging detallado para diagnóstico |
| El `.exe` no encuentra Chrome instalado                           | Baja         | `webdriver-manager` lo descarga al vuelo; mensaje claro si falla |
| El usuario olvida fichar a mano cuando salta el popup             | Media        | Mensaje del popup incluye instrucción explícita: "Abre clock.ncs.es y ficha" |

## 14. Métricas de éxito

- **Cero desfichajes accidentales** en producción tras el cambio (medible por ausencia de líneas "presencia inconsistente" en NCS).
- **Suite de tests < 5s** en CI o local.
- **Líneas duplicadas eliminadas**: ~500 LOC del par CLI/GUI desaparecen al unificar.
- **Documentación `.md` reducida** de 8 a 1.
- **Reintento exitoso tras crash**: matar el proceso con kill -9, relanzar, el sistema arranca sin intervención.
- **Portabilidad**: mover el `.exe` a otra carpeta → sigue funcionando con sus archivos junto a él.

## 15. Fuera de scope (para futuras iteraciones)

- Notificación por email o Telegram.
- Soporte para festivos nacionales/locales.
- Dashboard web del histórico.
- Cifrado real de credenciales (más allá de base64).
- Versión Linux/macOS.
- Auto-actualización del `.exe`.
- Resumen mensual automático.

## 16. Aprobación

Aprobado por el usuario en sesión de brainstorming del 2026-05-29 tras:
- Identificación empírica del bug de desfichaje (`verificar_bug_desconocido.py` → BUG CONFIRMADO).
- Verificación empírica del fix (`verificar_fix.py` → 3/3 PASS).
- Discusión de las 4 fases del diseño (arquitectura, módulos, flujos, testing/build).

Siguiente paso: invocar el skill `writing-plans` para generar el plan de implementación detallado con orden, dependencias y checkpoints.
