# 🚀 Crear Ejecutable (.exe) - Auto Fichaje

Guía para compilar el script en un **ejecutable standalone** (.exe) que no requiere tener Python instalado.

---

## 🎯 Ventajas del Ejecutable

✅ **No requiere Python instalado** en el PC  
✅ **Más fácil de configurar** como servicio de Windows  
✅ **Portable** - Puedes copiarlo a otro PC  
✅ **Archivo único** - Todo incluido en un solo .exe  
✅ **Se ejecuta en segundo plano** automáticamente  

---

## 📦 Compilar el Ejecutable

### Paso 1: Instalar PyInstaller

```bash
pip install pyinstaller
```

O simplemente:

```bash
pip install -r requirements.txt
```

### Paso 2: Ejecutar el Compilador

```bash
python compilar_exe.py
```

El script hará todo automáticamente:
1. ✅ Verifica que PyInstaller esté instalado
2. ✅ Compila `auto_fichaje.py` en un .exe
3. ✅ Empaqueta todas las dependencias
4. ✅ Configura para ejecución sin consola (segundo plano)

### Paso 3: Resultado

El ejecutable estará en:

```
dist/AutoFichajeNCS.exe
```

---

## 🔧 Configurar como Servicio con el .exe

### Opción 1: NSSM (Recomendado para .exe)

NSSM es perfecto para convertir el .exe en un servicio real de Windows.

#### Descargar NSSM

1. Ve a: https://nssm.cc/download
2. Descarga `nssm-2.24.zip` (o la versión más reciente)
3. Extrae el archivo
4. Copia `nssm.exe` a `C:\Windows\System32` (opcional)

#### Instalar el Servicio

Abre **PowerShell como Administrador**:

```powershell
# Instalar el servicio
C:\ruta\a\nssm.exe install AutoFichajeNCS
```

Se abrirá una ventana GUI. Configura:

**Pestaña "Application":**
- **Path**: 
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\AutoFichajeNCS.exe
  ```

- **Startup directory**:
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist
  ```

- **Arguments**: (dejar vacío)

**Pestaña "Details":**
- **Display name**: `Auto Fichaje NCS`
- **Description**: `Fichaje automático en NCS Clock de Lunes a Viernes`
- **Startup type**: `Automatic`

**Pestaña "Log on":**
- Selecciona: **"This account"**
- Usuario: Tu usuario de Windows
- Contraseña: Tu contraseña

**Pestaña "I/O"** (opcional, para ver logs):
- **Output (stdout)**: 
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\logs\stdout.log
  ```
- **Error (stderr)**:
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\logs\stderr.log
  ```

Clic en **"Install service"**

#### Iniciar el Servicio

```powershell
# Iniciar
Start-Service AutoFichajeNCS

# Verificar estado
Get-Service AutoFichajeNCS

# Ver que está ejecutándose
Get-Process AutoFichajeNCS
```

#### Comandos Útiles

```powershell
# Estado
nssm status AutoFichajeNCS

# Detener
nssm stop AutoFichajeNCS

# Iniciar
nssm start AutoFichajeNCS

# Reiniciar
nssm restart AutoFichajeNCS

# Editar configuración
nssm edit AutoFichajeNCS

# Desinstalar
nssm remove AutoFichajeNCS confirm
```

---

### Opción 2: Programador de Tareas (Más Simple)

1. `Win + R` → `taskschd.msc` → Enter
2. **Crear tarea básica...**
3. Nombre: `Auto Fichaje NCS`
4. Desencadenador: **"Al iniciar sesión"**
5. Acción: **"Iniciar un programa"**
   - **Programa**: 
     ```
     C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist\AutoFichajeNCS.exe
     ```
   - **Iniciar en**: 
     ```
     C:\Users\alberto\.gemini\antigravity\playground\solar-granule\dist
     ```

6. Clic derecho en la tarea → **Propiedades** → General:
   - ✅ **"Oculta"**
   - ✅ **"Ejecutar tanto si el usuario ha iniciado sesión como si no"**

---

## 📁 Estructura de Archivos para el .exe

El ejecutable necesita el archivo `.env` en la **misma carpeta**:

```
dist/
├── AutoFichajeNCS.exe     # ⭐ Ejecutable
├── .env                   # ⚠️ Debes copiarlo aquí
└── fichajes.csv           # Se creará automáticamente
```

**IMPORTANTE**: Copia el archivo `.env` a la carpeta `dist`:

```bash
copy .env dist\.env
```

O crea un nuevo `.env` en `dist` con:

```
NCS_USUARIO=tu_usuario
NCS_PASSWORD=tu_contraseña
```

---

## ✅ Verificar que Funciona

### Prueba Manual

```bash
cd dist
AutoFichajeNCS.exe
```

Debería iniciarse en segundo plano (sin ventana).

### Verificar en Administrador de Tareas

1. `Ctrl + Shift + Esc`
2. Pestaña **"Detalles"**
3. Buscar `AutoFichajeNCS.exe`
4. Debe aparecer ejecutándose

### Verificar CSV

```bash
type dist\fichajes.csv
```

Debe aparecer el registro de fichajes.

---

## 🛑 Detener el Servicio

### Si usaste NSSM:

```powershell
nssm stop AutoFichajeNCS
```

O:

```powershell
Stop-Service AutoFichajeNCS
```

### Si usaste Programador de Tareas:

1. Administrador de Tareas
2. Buscar `AutoFichajeNCS.exe`
3. Finalizar tarea

---

## 🐛 Solución de Problemas

**El .exe no se crea:**
- Ejecuta: `pip install pyinstaller`
- Vuelve a ejecutar: `python compilar_exe.py`

**El .exe no encuentra las credenciales:**
- Asegúrate de que `.env` esté en la carpeta `dist`
- Verifica que contenga `NCS_USUARIO` y `NCS_PASSWORD`

**El .exe se cierra inmediatamente:**
- Abre el ejecutable desde CMD para ver errores:
  ```bash
  cd dist
  AutoFichajeNCS.exe
  ```

**Selenium no encuentra Chrome:**
- El .exe usa tu instalación de Chrome normal
- Asegúrate de tener Chrome instalado

---

## 📝 Compilación Manual (Avanzado)

Si quieres personalizar la compilación:

```bash
pyinstaller --onefile --noconsole --name=AutoFichajeNCS auto_fichaje.py
```

Opciones:
- `--onefile` - Crea un solo .exe
- `--noconsole` - Sin ventana (segundo plano)
- `--name` - Nombre del ejecutable
- `--icon=icono.ico` - Agregar icono personalizado

---

## 🎉 Resultado Final

✅ Ejecutable standalone (.exe)  
✅ No requiere Python instalado  
✅ Funciona en segundo plano  
✅ Configurable como servicio  
✅ Fácil de desplegar  

**Simplemente ejecuta:**

```bash
python compilar_exe.py
```

Y obtendrás `dist\AutoFichajeNCS.exe` listo para usar. 🚀
