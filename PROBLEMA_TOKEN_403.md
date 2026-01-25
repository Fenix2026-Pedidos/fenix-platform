# Problema: Error 403 con Token de GitHub

## 🔴 Situación Actual

- ✅ Token clásico proporcionado: `[TOKEN_OCULTO_POR_SEGURIDAD]`
- ✅ Repositorio remoto configurado correctamente
- ✅ Proxy deshabilitado
- ❌ Error 403: "Permission denied to Fenix2026-Pedidos"

## 🔍 Posibles Causas

### 1. Token sin scope `repo` completo

El token puede no tener todos los permisos necesarios. Verifica:

1. Ve a: https://github.com/settings/tokens
2. Busca el token que creaste
3. Verifica que tenga marcado **`repo`** (acceso completo a repositorios)
   - No solo `public_repo`
   - Debe ser `repo` completo

### 2. Restricciones de rama protegida

El repositorio puede tener la rama `main` protegida. Verifica:

1. Ve a: https://github.com/Fenix2026-Pedidos/fenix-platform/settings/branches
2. Verifica si `main` tiene reglas de protección
3. Si está protegida, necesitas:
   - Desactivar temporalmente la protección
   - O añadir el token como excepción
   - O hacer push a otra rama primero

### 3. Token necesita permisos específicos

Si el token es "fine-grained", verifica:

1. Ve a: https://github.com/settings/tokens
2. Edita el token
3. Verifica:
   - **Repository access**: Debe incluir `Fenix2026-Pedidos/fenix-platform`
   - **Permissions**: 
     - `Contents: Write` ✅
     - `Metadata: Read` ✅
     - `Pull requests: Write` (opcional)

## ✅ Soluciones a Probar

### Solución 1: Verificar y recrear el token

1. Ve a: https://github.com/settings/tokens
2. **Elimina el token actual**
3. Crea uno nuevo:
   - **Note**: "Fenix Platform - Push"
   - **Expiration**: Elige duración
   - **Scopes**: Marca **SOLO `repo`** (esto incluye todo)
4. Copia el nuevo token
5. Intenta push de nuevo

### Solución 2: Verificar restricciones del repositorio

1. Ve a: https://github.com/Fenix2026-Pedidos/fenix-platform/settings
2. Ve a **"Branches"** en el menú lateral
3. Si `main` está protegida:
   - Haz clic en "Edit" o "Delete" en la regla
   - Temporalmente desactiva la protección
   - O añade una excepción para tu usuario

### Solución 3: Push a rama diferente primero

```powershell
# Crear rama nueva
git checkout -b develop

# Push a develop
git push -u origin develop

# Luego crear Pull Request desde develop a main
```

### Solución 4: Usar SSH en lugar de HTTPS

Si el problema persiste, prueba con SSH:

```powershell
# Cambiar a SSH
git remote set-url origin git@github.com:Fenix2026-Pedidos/fenix-platform.git

# Hacer push
git push -u origin master:main
```

## 📝 Comandos para Probar

### Verificar token manualmente

```powershell
$token = "[TU_TOKEN_AQUI]"
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null

# Verificar usuario
$headers = @{
    "Authorization" = "Bearer $token"
    "Accept" = "application/vnd.github.v3+json"
}
$user = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers
Write-Host "Usuario: $($user.login)"
```

### Intentar push con token en URL

```powershell
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
$token = "[TU_TOKEN_AQUI]"
git remote set-url origin "https://$token@github.com/Fenix2026-Pedidos/fenix-platform.git"
git push -u origin master:main
```

## ⚠️ Recomendación

**Lo más probable es que el token no tenga el scope `repo` completo.**

1. Ve a GitHub Settings → Tokens
2. Verifica que el token tenga **`repo`** marcado (no solo `public_repo`)
3. Si no lo tiene, crea uno nuevo con `repo` completo
4. Intenta push de nuevo

---

## 🔗 Enlaces Útiles

- Tokens: https://github.com/settings/tokens
- Repositorio: https://github.com/Fenix2026-Pedidos/fenix-platform
- Configuración de ramas: https://github.com/Fenix2026-Pedidos/fenix-platform/settings/branches
