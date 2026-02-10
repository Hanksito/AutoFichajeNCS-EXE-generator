# 🎁 Distribuir Ejecutable a Compañeros

Guía para crear y distribuir el ejecutable con interfaz gráfica a tus compañeros de trabajo.

---

## 🎯 Lo que Conseguirás

✅ **Un solo archivo .exe** que tus compañeros pueden ejecutar  
✅ **Primera ejecución** muestra ventana para introducir credenciales  
✅ **Credenciales guardadas** automáticamente (no necesitan .env)  
✅ **Funciona hasta apagar** el PC  
✅ **Fácil de usar** - Solo doble clic  

---

## 📦 Crear el Ejecutable Distribuible

### Paso 1: Compilar

```bash
python compilar_exe_gui.py
```

Esto creará: `dist\AutoFichajeNCS.exe`

### Paso 2: Probar

```bash
cd dist
AutoFichajeNCS.exe
```

Debe aparecer una ventana así:

```
┌───────────────────────────────────────┐
│  🕐 Auto Fichaje - NCS Clock         │
│  Configura tus credenciales          │
├───────────────────────────────────────┤
│                                       │
│  Usuario:     [________________]     │
│                                       │
│  Contraseña:  [________________]     │
│               ☐ Mostrar contraseña   │
│                                       │
│  📋 Información:                     │
│  • Fichaje automático L-V            │
│  • Entrada: 8:50 - 9:05              │
│  • Salida: 18:05 - 18:30             │
│                                       │
│  [Guardar y Continuar]  [Cancelar]   │
└───────────────────────────────────────┘
```

---

## 🎁 Distribuir a Compañeros

### Opción 1: Enviar Solo el .exe

1. Comparte el archivo `dist\AutoFichajeNCS.exe` por:
   - Email
   - Carpeta compartida de red
   - USB
   - Chat corporativo

2. Instrucciones para tus compañeros:

```
📧 INSTRUCCIONES PARA USAR AUTO FICHAJE:

1. Descarga el archivo AutoFichajeNCS.exe
2. Guárdalo en cualquier carpeta (ej: Escritorio)
3. Haz doble clic en AutoFichajeNCS.exe
4. Introduce tu usuario y contraseña de NCS Clock
5. Clic en "Guardar y Continuar"
6. ¡Listo! Ya está funcionando en segundo plano

El programa fichará automáticamente:
• De Lunes a Viernes
• Entrada entre 8:50 - 9:05
• Salida entre 18:05 - 18:30

El fichaje se registra en fichajes.csv (misma carpeta del .exe)
```

### Opción 2: Crear Instalador (Opcional)

Si quieres ser más profesional, puedes:
1. Usar **Inno Setup** para crear un instalador
2. El instalador puede:
   - Copiar el .exe a `C:\Program Files\AutoFichajeNCS`
   - Crear acceso directo en el escritorio
   - Configurar para iniciar automáticamente con Windows

---

## ⚙️ Configuración Automática al Inicio (Para Compañeros)

### Opción Simple: Carpeta Inicio

Diles que:

1. Presionen `Win + R`
2. Escriban: `shell:startup`
3. Copien el .exe a esa carpeta

Ahora se iniciará automáticamente al encender el PC.

### Opción Avanzada: Programador de Tareas

1. `Win + R` → `taskschd.msc`
2. Crear tarea básica
3. Desencadenador: Al iniciar sesión
4. Acción: Iniciar programa → Ruta del .exe
5. Propiedades → ✅ "Oculta"

---

## 🔒 Seguridad de las Credenciales

### ¿Dónde se guardan?

Las credenciales se almacenan en:

```
C:\Users\[USUARIO]\AppData\Local\AutoFichajeNCS\config.dat
```

### ¿Son seguras?

- ✅ Almacenadas en Base64 (ofuscación básica)
- ✅ Solo accesibles por el usuario del PC
- ✅ No se envían a ningún servidor externo
- ⚠️ No están cifradas con clave maestra (para versión simple)

### Cambiar credenciales

Para cambiar las credenciales:

**Opción 1: Eliminar config.dat**
```bash
del C:\Users\[USUARIO]\AppData\Local\AutoFichajeNCS\config.dat
```
Al ejecutar de nuevo el .exe, pedirá las credenciales otra vez.

**Opción 2: Editar config.dat** (no recomendado)

---

## 📊 Ver el Registro de Fichajes

El archivo `fichajes.csv` se crea en la misma carpeta que el .exe:

```csv
fecha,hora_entrada,hora_salida,total_horas,jornada,extra_ausencia,observaciones
2026-02-10,08:52:34,18:12:45,09:20,08:00,Extr. 01:20,Fichaje automático
```

Puede abrirse con Excel.

---

## 🛑 Desinstalar / Detener

### Detener temporalmente:

1. `Ctrl + Shift + Esc` (Administrador de Tareas)
2. Buscar `AutoFichajeNCS.exe`
3. Finalizar tarea

### Eliminar completamente:

1. Borrar el archivo `AutoFichajeNCS.exe`
2. Borrar carpeta de configuración:
   ```
   C:\Users\[USUARIO]\AppData\Local\AutoFichajeNCS
   ```
3. Si está en Inicio, borrarlo de `shell:startup`

---

## ❓ FAQ para Compañeros

**P: ¿Necesito instalar Python?**  
R: No, el .exe es totalmente independiente.

**P: ¿Necesito estar conectado a Internet?**  
R: Sí, para acceder a NCS Clock.

**P: ¿Funciona en mi Mac?**  
R: No, solo Windows. Para Mac necesitarías compilar en macOS.

**P: ¿Mis credenciales están seguras?**  
R: Se guardan localmente en tu PC, no se envían a ningún servidor nuestro.

**P: ¿Puedo cambiar los horarios?**  
R: Solo si tienes acceso al código fuente y recompilas.

**P: ¿Consume muchos recursos?**  
R: No, solo se activa a las horas de fichaje.

**P: ¿Funciona con escritorio remoto?**  
R: Sí, siempre que puedas acceder a NCS Clock desde ahí.

---

## 📧 Plantilla de Email para Compañeros

```
Asunto: 🕐 Auto Fichaje NCS - Herramienta Automática

Hola equipo,

Os comparto una herramienta que automatiza el fichaje en NCS Clock:

🔗 Descarga: [adjunto: AutoFichajeNCS.exe]

✨ Características:
• Ficha automáticamente de Lunes a Viernes
• Entrada aleatoria entre 8:50 - 9:05
• Salida aleatoria entre 18:05 - 18:30
• Se ejecuta en segundo plano

📋 Cómo usar:
1. Descarga el archivo AutoFichajeNCS.exe
2. Colócalo en cualquier carpeta
3. Ejecuta el .exe (doble clic)
4. Introduce tu usuario y contraseña de NCS Clock
5. ¡Listo!

💡 Recomendación:
Copia el .exe a la carpeta de Inicio (Win+R → shell:startup)
para que se ejecute automáticamente al encender el PC.

📝 El registro de fichajes se guarda en "fichajes.csv"

¿Dudas? Preguntadme sin problema.

Saludos!
```

---

## ✅ Checklist de Distribución

Antes de compartir el .exe:

- [ ] ✅ Compilado correctamente con `compilar_exe_gui.py`
- [ ] ✅ Probado en tu PC (aparece ventana de configuración)
- [ ] ✅ Verificado que guarda credenciales
- [ ] ✅ Verificado que ficha correctamente
- [ ] ✅ Verificado que se ejecuta en segundo plano
- [ ] ✅ Preparadas instrucciones para compañeros
- [ ] ✅ Probado en otro PC (opcional pero recomendado)

---

## 🎉 ¡Listo para Distribuir!

Simplemente ejecuta:

```bash
python compilar_exe_gui.py
```

Y comparte `dist\AutoFichajeNCS.exe` con tus compañeros. 🚀
