# Solución: Error de Permisos en GitHub (403)

## 🔴 Problema Actual

```
remote: Permission to Fenix2026-Pedidos/fenix-platform.git denied to Synerg-IA.
fatal: unable to access 'https://github.com/Fenix2026-Pedidos/fenix-platform.git/': 
The requested URL returned error: 403
```

**Causa**: Git está usando la cuenta "Synerg-IA" que no tiene permisos para hacer push al repositorio `Fenix2026-Pedidos/fenix-platform`.

## ✅ Soluciones

### Opción 1: Usar Personal Access Token (Recomendado)

Esta es la forma más segura y recomendada por GitHub.

#### Paso 1: Crear un Personal Access Token

1. Ve a GitHub: https://github.com/settings/tokens
2. O navega: **GitHub → Tu perfil → Settings → Developer settings → Personal access tokens → Tokens (classic)**
3. Haz clic en **"Generate new token" → "Generate new token (classic)"**
4. Configura el token:
   - **Note**: "Fenix Platform - Push Access"
   - **Expiration**: Elige una duración (90 días, 1 año, etc.)
   - **Scopes**: Marca **`repo`** (esto da acceso completo a repositorios)
5. Haz clic en **"Generate token"**
6. **⚠️ IMPORTANTE**: Copia el token inmediatamente (solo se muestra una vez)
   - Ejemplo: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### Paso 2: Usar el token al hacer push

Cuando Git te pida credenciales:

```powershell
# Deshabilitar proxy primero
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null

# Hacer push (te pedirá usuario y contraseña)
git push -u origin master
```

**Cuando te pida:**
- **Username**: Tu usuario de GitHub (el que tiene acceso al repo)
- **Password**: Pega el **Personal Access Token** (NO tu contraseña de GitHub)

#### Paso 3: Guardar credenciales (opcional)

Para no tener que escribir el token cada vez:

```powershell
# Configurar Git Credential Manager (Windows)
git config --global credential.helper manager-core
```

Luego, la primera vez que hagas push, Windows guardará el token de forma segura.

---

### Opción 2: Cambiar a cuenta correcta en Git

Si necesitas cambiar la cuenta de GitHub que usa Git:

```powershell
# Ver cuenta actual
git config --global user.name
git config --global user.email

# Cambiar a la cuenta correcta (la que tiene acceso al repo)
git config --global user.name "TuUsuarioGitHub"
git config --global user.email "tu-email@ejemplo.com"
```

**Nota**: Esto solo cambia el nombre que aparece en los commits. Para autenticación, necesitas el Personal Access Token.

---

### Opción 3: Usar SSH en lugar de HTTPS

Si prefieres usar SSH (más seguro y no requiere token cada vez):

#### Paso 1: Generar clave SSH (si no tienes una)

```powershell
# Generar nueva clave SSH
ssh-keygen -t ed25519 -C "tu-email@ejemplo.com"

# Presiona Enter para usar la ubicación por defecto
# Opcional: añade una frase de contraseña para mayor seguridad
```

#### Paso 2: Añadir la clave SSH a GitHub

```powershell
# Copiar la clave pública al portapapeles
cat ~/.ssh/id_ed25519.pub | clip
```

O manualmente:
1. Abre el archivo: `C:\Users\Solutio\.ssh\id_ed25519.pub`
2. Copia todo el contenido

Luego:
1. Ve a GitHub → Settings → SSH and GPG keys
2. Haz clic en **"New SSH key"**
3. **Title**: "Fenix Platform - Windows"
4. **Key**: Pega la clave pública
5. Haz clic en **"Add SSH key"**

#### Paso 3: Cambiar el remoto a SSH

```powershell
# Cambiar de HTTPS a SSH
git remote set-url origin git@github.com:Fenix2026-Pedidos/fenix-platform.git

# Verificar
git remote -v

# Hacer push (ahora usará SSH)
git push -u origin master
```

---

### Opción 4: Solicitar acceso al repositorio

Si no eres el dueño del repositorio y necesitas permisos:

1. Contacta al dueño del repositorio: `Fenix2026-Pedidos`
2. Pide que te añadan como colaborador con permisos de **Write** o **Admin**
3. Acepta la invitación cuando llegue por email
4. Luego podrás hacer push normalmente

---

## 🔍 Verificar la Solución

Después de aplicar cualquiera de las soluciones:

```powershell
# Deshabilitar proxy
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null

# Intentar push
git push -u origin master
```

Si funciona, deberías ver:
```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
...
To https://github.com/Fenix2026-Pedidos/fenix-platform.git
 * [new branch]      master -> master
Branch 'master' set up to track remote branch 'master' from 'origin'.
```

---

## 📝 Resumen Rápido

**Para la mayoría de usuarios, la mejor opción es:**

1. ✅ Crear Personal Access Token en GitHub
2. ✅ Deshabilitar proxy: `$env:HTTP_PROXY = $null; $env:HTTPS_PROXY = $null`
3. ✅ Hacer push: `git push -u origin master`
4. ✅ Usar el token como contraseña cuando Git lo pida
5. ✅ Configurar credential helper para guardar el token

---

## ⚠️ Notas de Seguridad

- **Nunca compartas tu Personal Access Token**
- **No subas el token a Git** (está en `.gitignore` por defecto)
- Si el token se compromete, revócalo inmediatamente en GitHub
- Los tokens tienen expiración, renueva cuando sea necesario

---

## 🔗 Enlaces Útiles

- Crear token: https://github.com/settings/tokens
- SSH keys: https://github.com/settings/keys
- Documentación GitHub: https://docs.github.com/en/authentication
