# Conexión con GitHub - Plataforma Fenix

## ✅ Estado Actual

El repositorio remoto **ya está configurado correctamente**:

```
origin: https://github.com/Fenix2026-Pedidos/fenix-platform.git
```

## 📋 Commits Locales Pendientes

Tienes **7 commits** locales que aún no se han subido a GitHub:

1. `82d4a8d` - Fix: Corregir traducción automática ES→中文 usando código de idioma correcto (zh-CN)
2. `3e5e394` - Mejora UI: carrito header estilo Amazon, espaciado y reordenación de elementos
3. `6d8ba48` - Mejora UI: Referencia visible, precio destacado e imagen más grande en catálogo
4. `c2665bd` - Refactor: Mover categorías de productos del sidebar al panel de filtros
5. `7096a87` - Mejoras frontend: catálogo responsive, traducciones chino completas y sidebar con estados activos mejorados
6. `30322ac` - feat: Implementar diseño moderno estilo HR Talent con sidebar, topbar y sistema de diseño completo
7. `0d05d5e` - Initial commit: Plataforma Fenix - Sistema completo de gestión de pedidos B2B con interfaz web

## 🚀 Cómo Subir los Cambios a GitHub

### Opción 1: Push Directo (si el repositorio remoto está vacío o es nuevo)

```bash
git push -u origin master
```

O si la rama principal se llama `main`:

```bash
git push -u origin master:main
```

### Opción 2: Si el repositorio remoto ya tiene contenido

Primero, sincroniza con el remoto:

```bash
git fetch origin
git pull origin main --allow-unrelated-histories
```

Luego haz push:

```bash
git push -u origin master
```

## ⚠️ Problemas Comunes y Soluciones

### Problema 0: Error de proxy (127.0.0.1:9) ⚠️ ACTUAL

Si ves el error: `Failed to connect to github.com port 443 via 127.0.0.1`

**Solución Rápida: Usar el script automático**
```powershell
.\push-to-github.ps1
```

**Solución Manual: Deshabilitar proxy temporalmente**
```powershell
# ⚠️ IMPORTANTE: Sin espacios después de $env:
# ❌ INCORRECTO: $env: HTTP_PROXY = $null
# ✅ CORRECTO:   $env:HTTP_PROXY = $null

# En PowerShell, ejecuta estos comandos (cada uno en una línea):
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
git push -u origin master
```

**O usa el script simplificado:**
```powershell
.\fix-proxy-and-push.ps1
```

**Solución Permanente: Configurar proxy correctamente o deshabilitarlo**
```powershell
# Ver proxy actual
$env:HTTP_PROXY
$env:HTTPS_PROXY

# Deshabilitar permanentemente (en tu perfil de PowerShell)
# Edita: $PROFILE y añade:
# $env:HTTP_PROXY = $null
# $env:HTTPS_PROXY = $null
```

### Problema 1: Error de autenticación

Si GitHub te pide autenticación, tienes dos opciones:

**Opción A: Usar Personal Access Token (recomendado)**
1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Genera un nuevo token con permisos `repo`
3. Cuando Git te pida la contraseña, usa el token en lugar de tu contraseña

**Opción B: Usar SSH en lugar de HTTPS**
```bash
# Cambiar el remoto a SSH
git remote set-url origin git@github.com:Fenix2026-Pedidos/fenix-platform.git
```

### Problema 2: Error de proxy

Si ves errores como "Failed to connect to github.com port 443 via 127.0.0.1":

**Solución A: Deshabilitar proxy temporalmente**
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

**Solución B: Configurar proxy correctamente**
```bash
git config --global http.proxy http://proxy:puerto
git config --global https.proxy http://proxy:puerto
```

### Problema 3: El repositorio remoto tiene cambios diferentes

Si el repositorio remoto tiene commits que no tienes localmente:

```bash
# Ver diferencias
git fetch origin
git log HEAD..origin/main

# Fusionar cambios
git pull origin main --allow-unrelated-histories

# Resolver conflictos si los hay, luego:
git push -u origin master
```

## 📝 Comandos Útiles

### Verificar estado del remoto
```bash
git remote -v
```

### Ver commits locales no subidos
```bash
git log origin/master..HEAD
```

### Ver diferencias con el remoto
```bash
git fetch origin
git diff master origin/main
```

### Forzar push (⚠️ solo si es necesario y tienes permiso)
```bash
git push -u origin master --force
```

## ✅ Verificación Final

Después de hacer push, verifica que todo esté sincronizado:

```bash
git fetch origin
git status
```

Deberías ver: "Your branch is up to date with 'origin/master'"

## 🔗 Enlaces Útiles

- Repositorio: https://github.com/Fenix2026-Pedidos/fenix-platform
- Documentación Git: https://git-scm.com/doc
- GitHub Docs: https://docs.github.com
