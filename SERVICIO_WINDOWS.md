# 🚀 Configurar Auto Fichaje como Servicio de Windows

Instrucciones para ejecutar el script como servicio en segundo plano permanente.

---

## 🎯 Método 1: Programador de Tareas (RECOMENDADO - Más Fácil)

### Paso 1: Abrir el Programador de Tareas

1. Presiona `Win + R`
2. Escribe `taskschd.msc`
3. Presiona `Enter`

### Paso 2: Crear Tarea

1. Clic en **"Crear tarea básica..."**
2. **Nombre**: `Auto Fichaje NCS`
3. **Descripción**: `Fichaje automático en NCS Clock L-V`
4. Siguiente

### Paso 3: Desencadenador

1. Selecciona: **"Al iniciar sesión"**
2. Siguiente

### Paso 4: Acción

1. Selecciona: **"Iniciar un programa"**
2. Siguiente
3. **Programa o script**: 
   ```
   C:\Users\alberto\AppData\Local\Programs\Python\Python3XX\pythonw.exe
   ```
   > ⚠️ **IMPORTANTE**: Encuentra tu `pythonw.exe` ejecutando en CMD:
   > ```
   > where pythonw
   > ```

4. **Agregar argumentos**:
   ```
   auto_fichaje.py
   ```

5. **Iniciar en**:
   ```
   C:\Users\alberto\.gemini\antigravity\playground\solar-granule
   ```

6. Siguiente → Finalizar

### Paso 5: Configurar para Ejecución en Segundo Plano

1. En el Programador de Tareas, busca tu tarea **"Auto Fichaje NCS"**
2. Clic derecho → **Propiedades**
3. En la pestaña **"General"**:
   - ✅ Marcar: **"Ejecutar tanto si el usuario ha iniciado sesión como si no"**
   - ✅ Marcar: **"Ejecutar con los privilegios más altos"**
   - ✅ Marcar: **"Oculta"** (importante para segundo plano)

4. En la pestaña **"Condiciones"**:
   - ❌ Desmarcar: **"Iniciar la tarea solo si el equipo está con alimentación de CA"**
   - ✅ Marcar: **"Reactivar el equipo para ejecutar esta tarea"** (opcional)

5. En la pestaña **"Configuración"**:
   - ✅ Marcar: **"Si la tarea ya se está ejecutando, se aplicará la regla siguiente: No iniciar una nueva instancia"**

6. **Aceptar**

### Paso 6: Verificar que Funciona

1. Reinicia el ordenador
2. Abre el **Administrador de Tareas** (`Ctrl + Shift + Esc`)
3. Ve a la pestaña **"Detalles"**
4. Busca `pythonw.exe` → Debería estar ejecutándose
5. Verifica que se crea/actualiza `fichajes.csv`

---

## 🎯 Método 2: Servicio de Windows con NSSM (Avanzado)

NSSM (Non-Sucking Service Manager) convierte cualquier programa en un servicio real de Windows.

### Paso 1: Descargar NSSM

1. Ve a: https://nssm.cc/download
2. Descarga la versión estable (ej: `nssm-2.24.zip`)
3. Extrae el archivo
4. Copia `nssm.exe` a `C:\Windows\System32` (o úsalo directamente)

### Paso 2: Instalar el Servicio

Abre **PowerShell como Administrador** y ejecuta:

```powershell
# Navegar a la carpeta de NSSM
cd "C:\ruta\donde\extraiste\nssm\win64"

# Instalar el servicio
.\nssm.exe install AutoFichajeNCS
```

Se abrirá una ventana GUI. Configura:

**Pestaña "Application":**
- **Path**: Ruta a `pythonw.exe` (ejecuta `where pythonw` para encontrarla)
  ```
  C:\Users\alberto\AppData\Local\Programs\Python\Python3XX\pythonw.exe
  ```

- **Startup directory**:
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule
  ```

- **Arguments**:
  ```
  auto_fichaje.py
  ```

**Pestaña "Details":**
- **Display name**: `Auto Fichaje NCS`
- **Description**: `Fichaje automático en NCS Clock de Lunes a Viernes`
- **Startup type**: `Automatic`

**Pestaña "Log on":**
- Selecciona: **"This account"**
- Usuario: Tu usuario de Windows
- Contraseña: Tu contraseña de Windows

**Pestaña "I/O":**
- **Output (stdout)**: 
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule\logs\stdout.log
  ```
- **Error (stderr)**:
  ```
  C:\Users\alberto\.gemini\antigravity\playground\solar-granule\logs\stderr.log
  ```

Clic en **"Install service"**

### Paso 3: Iniciar el Servicio

En PowerShell (como Administrador):

```powershell
# Iniciar el servicio
Start-Service AutoFichajeNCS

# Verificar estado
Get-Service AutoFichajeNCS

# Ver que está ejecutándose
Get-Process pythonw
```

### Paso 4: Configurar Inicio Automático

```powershell
# Configurar para que inicie automáticamente
Set-Service AutoFichajeNCS -StartupType Automatic
```

### Comandos Útiles para NSSM

```powershell
# Ver estado del servicio
.\nssm.exe status AutoFichajeNCS

# Detener el servicio
.\nssm.exe stop AutoFichajeNCS

# Iniciar el servicio
.\nssm.exe start AutoFichajeNCS

# Reiniciar el servicio
.\nssm.exe restart AutoFichajeNCS

# Editar configuración
.\nssm.exe edit AutoFichajeNCS

# Desinstalar el servicio
.\nssm.exe remove AutoFichajeNCS confirm
```

---

## 🎯 Método 3: Script BAT en Inicio (Más Simple pero Menos Robusto)

### Paso 1: Usar el Script Incluido

Ya tienes el script `iniciar_servicio.bat` creado.

### Paso 2: Agregar al Inicio

1. Presiona `Win + R`
2. Escribe: `shell:startup`
3. Presiona `Enter`
4. **Copia** el archivo `iniciar_servicio.bat` a esa carpeta

O crea un **acceso directo**:
1. Clic derecho en `iniciar_servicio.bat` → Crear acceso directo
2. Mueve el acceso directo a la carpeta Startup
3. **Importante**: Clic derecho en el acceso directo → Propiedades → 
   - **Ejecutar**: Minimizada
   - **Aceptar**

### Limitaciones de este Método

- ❌ Se cierra si cierras sesión
- ❌ Visible en la bandeja del sistema
- ⚠️ Solo funciona si mantienes la sesión abierta

---

## ✅ Verificar que Está Funcionando

### Opción 1: Administrador de Tareas

1. `Ctrl + Shift + Esc`
2. Pestaña **"Detalles"**
3. Buscar `pythonw.exe`
4. Debería aparecer ejecutándose

### Opción 2: Verificar el CSV

```powershell
# Ver las últimas líneas del CSV
Get-Content fichajes.csv -Tail 5
```

### Opción 3: Ver Servicios (si usaste NSSM)

1. `Win + R` → `services.msc`
2. Buscar **"Auto Fichaje NCS"**
3. Estado debe ser **"En ejecución"**

---

## 🛑 Detener el Servicio

### Si usaste Programador de Tareas:

1. Abrir Administrador de Tareas
2. Pestaña "Detalles"
3. Buscar `pythonw.exe`
4. Clic derecho → Finalizar tarea

### Si usaste NSSM:

```powershell
# PowerShell como Administrador
Stop-Service AutoFichajeNCS
```

O:

```powershell
.\nssm.exe stop AutoFichajeNCS
```

### Si usaste script de inicio:

1. Administrador de Tareas
2. Buscar `pythonw.exe`
3. Finalizar tarea

---

## 📝 Recomendación Final

**Para la mayoría de usuarios:**
➡️ Usa **Método 1: Programador de Tareas**

**¿Por qué?**
- ✅ No requiere software adicional
- ✅ Fácil de configurar
- ✅ Se ejecuta en segundo plano
- ✅ Inicia automáticamente al encender el PC
- ✅ Funciona aunque cierres sesión

**Para usuarios avanzados:**
➡️ Usa **Método 2: NSSM**

**¿Por qué?**
- ✅ Servicio real de Windows
- ✅ Reinicio automático si falla
- ✅ Logs separados
- ✅ Mayor control

---

## 🐛 Solución de Problemas

**El servicio no inicia:**
- Verifica que la ruta a `pythonw.exe` sea correcta
- Verifica que el archivo `.env` exista y tenga las credenciales

**Aparece y desaparece rápidamente:**
- Revisa los logs (si usaste NSSM)
- Ejecuta `python auto_fichaje.py` manualmente para ver errores

**No ficha:**
- Verifica que las credenciales en `.env` sean correctas
- Ejecuta `python test_fichaje.py` para diagnosticar

---

## ✅ Resultado Esperado

Una vez configurado:

1. ✅ El script se inicia automáticamente al encender el PC
2. ✅ Se ejecuta en **segundo plano** (sin ventanas)
3. ✅ Ficha **automáticamente** todos los días laborables
4. ✅ Registra todo en `fichajes.csv`
5. ✅ Continúa ejecutándose incluso si cierras sesión (con Método 1 o 2)

🎉 **¡Completamente automatizado y en segundo plano!**
