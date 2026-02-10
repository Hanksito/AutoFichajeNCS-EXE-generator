# 🕐 Auto Fichaje - NCS Clock

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Sistema automático de fichaje para NCS Clock con interfaz gráfica, registro CSV y ejecución en segundo plano.

## ✨ Características

- 🔐 **Interfaz gráfica** para configurar credenciales (primera ejecución)
- ⏰ **Fichaje automático** de Lunes a Viernes
  - Entrada aleatoria: 8:50 - 9:05
  - Salida aleatoria: 18:05 - 18:30
- 📊 **Registro CSV** completo de todos los fichajes
- 👻 **Modo invisible** (navegador headless)
- 🚀 **Ejecutable standalone** (.exe) - no requiere Python instalado
- 🔄 **Funciona en segundo plano** hasta apagar el PC

## 🎁 Para Usuarios Finales (Compañeros de Trabajo)

Si solo quieres **usar** el programa:

1. **Descarga** el ejecutable desde [Releases](../../releases)
2. **Ejecuta** `AutoFichajeNCS.exe`
3. **Introduce** tu usuario y contraseña en la ventana
4. **¡Listo!** Ya está funcionando

👉 Ver [DISTRIBUIR_EXE.md](DISTRIBUIR_EXE.md) para más información

## 👨‍💻 Para Desarrolladores

Si quieres **modificar** o **compilar** el código:

### Requisitos

- Python 3.8 o superior
- Google Chrome instalado

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/auto-fichaje-ncs.git
cd auto-fichaje-ncs

# Instalar dependencias
pip install -r requirements.txt
```

### Uso

#### Opción 1: Versión con Interfaz Gráfica (Recomendado)

```bash
python auto_fichaje_gui.py
```

- Primera ejecución: Muestra ventana para configurar credenciales
- Siguientes ejecuciones: Usa credenciales guardadas

#### Opción 2: Versión con archivo .env

```bash
# Crear archivo .env
copy .env.example .env
notepad .env  # Editar con tus credenciales

# Ejecutar
python auto_fichaje.py
```

### Compilar Ejecutable

```bash
# Versión con GUI (recomendada para distribución)
python compilar_exe_gui.py

# Versión sin GUI
python compilar_exe.py
```

El ejecutable estará en `dist/AutoFichajeNCS.exe`

## 📖 Documentación

- [README.md](README.md) - Documentación general y uso
- [DISTRIBUIR_EXE.md](DISTRIBUIR_EXE.md) - Guía para distribuir a compañeros
- [COMPILAR_EXE.md](COMPILAR_EXE.md) - Compilación detallada
- [SERVICIO_WINDOWS.md](SERVICIO_WINDOWS.md) - Configurar como servicio de Windows

## 🗂️ Estructura del Proyecto

```
auto-fichaje-ncs/
├── auto_fichaje.py           # Script principal (requiere .env)
├── auto_fichaje_gui.py       # Script con interfaz gráfica
├── ncs_login.py              # Módulo de login
├── ncs_fichaje.py            # Módulo de fichaje
├── ncs_csv_logger.py         # Registro CSV
├── test_login.py             # Test de login
├── test_fichaje.py           # Test completo
├── compilar_exe.py           # Compilador (sin GUI)
├── compilar_exe_gui.py       # Compilador (con GUI)
├── requirements.txt          # Dependencias
├── .env.example              # Plantilla de credenciales
└── fichajes.csv              # Registro (generado automáticamente)
```

## ⚙️ Configuración

### Horarios

Edita las variables en `auto_fichaje.py` o `auto_fichaje_gui.py`:

```python
ENTRADA_DESDE = "08:50"
ENTRADA_HASTA = "09:05"
SALIDA_DESDE = "18:05"
SALIDA_HASTA = "18:30"
```

### Credenciales

**Versión .env:**
```
NCS_USUARIO=tu_usuario
NCS_PASSWORD=tu_contraseña
```

**Versión GUI:**
Se configuran en la primera ejecución y se guardan en:
```
C:\Users\[USUARIO]\AppData\Local\AutoFichajeNCS\config.dat
```

## 🧪 Testing

```bash
# Probar solo el login
python test_login.py

# Probar fichaje completo
python test_fichaje.py
```

## 📊 Formato del CSV

```csv
fecha,hora_entrada,hora_salida,total_horas,jornada,extra_ausencia,observaciones
2026-02-10,08:52:34,18:12:45,09:20,08:00,Extr. 01:20,Fichaje automático
```

## 🔒 Seguridad

- ⚠️ **No subas el archivo `.env`** a GitHub (incluido en `.gitignore`)
- ⚠️ **No compartas el archivo `config.dat`** con nadie
- ✅ Las credenciales se almacenan localmente (ofuscadas en base64)
- ✅ El navegador se ejecuta en modo headless (invisible)

## 🐛 Solución de Problemas

**El login falla:**
- Verifica que las credenciales sean correctas
- Comprueba que puedes acceder manualmente a https://clock.ncs.es

**No encuentra Chrome:**
- Asegúrate de tener Google Chrome instalado

**El ejecutable no se crea:**
- Ejecuta: `pip install -r requirements.txt`
- Vuelve a intentar compilar

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la [Licencia MIT](LICENSE).

## ⚠️ Disclaimer

Este proyecto es una herramienta personal de automatización. Úsalo bajo tu propia responsabilidad y asegúrate de que cumple con las políticas de tu empresa.

## 🙏 Agradecimientos

- [Selenium](https://www.selenium.dev/) - Automatización web
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) - Gestión de drivers
- [PyInstaller](https://www.pyinstaller.org/) - Empaquetado de ejecutables

---

Hecho con ❤️ para automatizar el fichaje y tener más tiempo para lo importante.
