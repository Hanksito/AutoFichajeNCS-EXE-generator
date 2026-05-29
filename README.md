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
