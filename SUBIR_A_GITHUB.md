# 📤 Subir Proyecto a GitHub

Guía paso a paso para subir el proyecto a GitHub.

---

## 📋 Pasos Previos

### 1. Crear Repositorio en GitHub

1. Ve a https://github.com
2. Clic en el botón **"New"** (verde, arriba a la derecha)
3. **Repository name**: `auto-fichaje-ncs` (o el nombre que prefieras)
4. **Description**: "Sistema automático de fichaje para NCS Clock"
5. **Visibility**: 
   - ✅ **Private** (recomendado si es para uso interno)
   - 🌐 **Public** (si quieres compartirlo públicamente)
6. ❌ **NO marcar** "Add a README file" (ya lo tienes)
7. ❌ **NO marcar** "Add .gitignore" (ya lo tienes)
8. ❌ **NO marcar** "Choose a license" (ya lo tienes)
9. Clic en **"Create repository"**

GitHub te mostrará la URL del repositorio, algo como:
```
https://github.com/TU_USUARIO/auto-fichaje-ncs.git
```

---

## 🚀 Subir el Proyecto

### Opción 1: Primera vez (Repositorio Nuevo)

Abre PowerShell en la carpeta del proyecto:

```powershell
cd C:\Users\alberto\.gemini\antigravity\playground\solar-granule

# Inicializar Git (solo si no existe)
git init

# Copiar README para GitHub
copy README_GITHUB.md README.md

# Agregar todos los archivos
git add .

# Hacer commit inicial
git commit -m "Initial commit: Auto Fichaje NCS Clock"

# Conectar con tu repositorio de GitHub
git remote add origin https://github.com/TU_USUARIO/auto-fichaje-ncs.git

# Configurar rama principal
git branch -M main

# Subir todo a GitHub
git push -u origin main
```

**Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.**

### Opción 2: Si ya tienes Git configurado

```powershell
cd C:\Users\alberto\.gemini\antigravity\playground\solar-granule

# Copiar README para GitHub
copy README_GITHUB.md README.md

# Agregar archivos
git add .

# Commit
git commit -m "Initial commit: Auto Fichaje NCS Clock"

# Conectar con GitHub
git remote add origin https://github.com/TU_USUARIO/auto-fichaje-ncs.git

# Subir
git push -u origin main
```

---

## 🔐 Autenticación en GitHub

### Método 1: HTTPS con Token (Recomendado)

Cuando te pida usuario/contraseña al hacer `git push`:

1. **Usuario**: Tu nombre de usuario de GitHub
2. **Contraseña**: NO uses tu contraseña real, usa un **Personal Access Token**

**Crear un Personal Access Token:**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" → "Generate new token (classic)"
3. **Note**: "Auto Fichaje Git"
4. **Expiration**: 90 days (o el que prefieras)
5. **Scopes**: Marca solo `repo` (acceso completo a repositorios)
6. "Generate token"
7. **Copia el token** (no podrás verlo de nuevo)

Usa ese token como contraseña cuando hagas `git push`.

### Método 2: SSH (Más Avanzado)

Si prefieres SSH, sigue la [guía de GitHub](https://docs.github.com/es/authentication/connecting-to-github-with-ssh).

---

## ✅ Verificar que se Subió

1. Ve a https://github.com/TU_USUARIO/auto-fichaje-ncs
2. Deberías ver todos los archivos
3. El README.md se mostrará en la página principal

---

## 📦 Crear Release (Opcional pero Recomendado)

Para que tus compañeros puedan descargar el .exe fácilmente:

### 1. Compilar el ejecutable

```powershell
python compilar_exe_gui.py
```

### 2. Crear Release en GitHub

1. En tu repositorio → **Releases** (barra derecha)
2. **"Create a new release"**
3. **Tag version**: `v1.0.0`
4. **Release title**: `v1.0.0 - Primera versión`
5. **Description**:
   ```
   ## Auto Fichaje NCS Clock v1.0.0
   
   Sistema automático de fichaje con interfaz gráfica.
   
   ### ✨ Características
   - Fichaje automático L-V
   - Entrada: 8:50 - 9:05
   - Salida: 18:05 - 18:30
   - Interfaz gráfica para configurar credenciales
   
   ### 📥 Descarga
   Descarga `AutoFichajeNCS.exe` y ejecútalo.
   ```
6. **Attach binaries**: Arrastra `dist\AutoFichajeNCS.exe`
7. **"Publish release"**

Ahora tus compañeros pueden descargar directamente desde:
```
https://github.com/TU_USUARIO/auto-fichaje-ncs/releases
```

---

## 🔄 Actualizar el Repositorio (Futuros Cambios)

Cuando hagas cambios:

```powershell
# Ver qué cambió
git status

# Agregar cambios
git add .

# Commit con mensaje descriptivo
git commit -m "Descripción de los cambios"

# Subir a GitHub
git push
```

---

## 🌿 Estructura Recomendada de Ramas

Para desarrollo más profesional:

```powershell
# Crear rama de desarrollo
git checkout -b develop

# Hacer cambios...
git add .
git commit -m "Nueva característica"

# Volver a main
git checkout main

# Fusionar cambios
git merge develop

# Subir
git push
```

---

## 📁 Qué se Sube vs Qué NO

### ✅ Se sube (incluido en Git):
- ✅ Código fuente (`.py`)
- ✅ Documentación (`.md`)
- ✅ Archivos de configuración (`requirements.txt`, `.gitignore`)
- ✅ Ejemplos (`.env.example`)
- ✅ Licencia (`LICENSE`)

### ❌ NO se sube (en `.gitignore`):
- ❌ Credenciales (`.env`, `config.dat`)
- ❌ Ejecutables compilados (`dist/`, `build/`)
- ❌ Datos personales (`fichajes.csv`)
- ❌ Logs y temporales
- ❌ Cache de Python (`__pycache__/`)

---

## ⚠️ IMPORTANTE: Seguridad

**NUNCA subas a GitHub:**
- ❌ El archivo `.env` con tus credenciales
- ❌ El archivo `config.dat`
- ❌ El archivo `fichajes.csv` con tus datos

Si accidentalmente subiste credenciales:

```powershell
# Eliminar del historial (PELIGROSO - consulta antes)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

**Mejor**: Cambia tus credenciales de NCS Clock inmediatamente.

---

## 🤝 Permitir que tus Compañeros Contribuyan

### Opción 1: Repositorio Privado con Colaboradores

1. Repositorio → Settings → Collaborators
2. "Add people"
3. Agregar a tus compañeros por email o usuario

### Opción 2: Repositorio Público

Cualquiera puede hacer fork y Pull Requests.

---

## 📧 Compartir con Compañeros

Una vez subido a GitHub:

**Si es PRIVADO:**
```
Hola equipo,

Repositorio del Auto Fichaje:
https://github.com/TU_USUARIO/auto-fichaje-ncs

Necesitáis acceso al repositorio. Enviadme vuestro usuario de GitHub.

Para descargar el .exe:
https://github.com/TU_USUARIO/auto-fichaje-ncs/releases

Saludos!
```

**Si es PÚBLICO:**
```
Hola equipo,

Auto Fichaje disponible en GitHub:
https://github.com/TU_USUARIO/auto-fichaje-ncs

Descarga directa del .exe:
https://github.com/TU_USUARIO/auto-fichaje-ncs/releases

Saludos!
```

---

## ✅ Checklist Final

Antes de compartir:

- [ ] ✅ `.gitignore` configurado correctamente
- [ ] ✅ `.env` NO está en el repositorio
- [ ] ✅ README_GITHUB.md copiado como README.md
- [ ] ✅ LICENSE incluida
- [ ] ✅ Código subido a GitHub
- [ ] ✅ Release creada con el .exe
- [ ] ✅ Repositorio probado (clonar en otra carpeta y probar)

---

## 🎉 ¡Listo!

Tu proyecto ya está en GitHub y listo para compartir. 🚀
