# Push Manual a GitHub - Instrucciones

## ✅ Token Verificado

El token es **válido** y puede acceder al repositorio. El problema puede ser que el token es "fine-grained" y necesita configuración específica.

## 🚀 Solución: Push Manual

### Paso 1: Abre PowerShell en la carpeta del proyecto

```powershell
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
```

### Paso 2: Deshabilitar proxy

```powershell
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
```

### Paso 3: Hacer push

```powershell
git push -u origin master
```

### Paso 4: Cuando Git pida credenciales

**Username:** `Fenix2026-Pedidos`

**Password:** Pega este token:
```
[TU_TOKEN_AQUI]
```

⚠️ **IMPORTANTE:** Usa el token como contraseña, NO tu contraseña de GitHub.

---

## 🔍 Si Sigue Fallando

### Verificar permisos del token

1. Ve a: https://github.com/settings/tokens
2. Busca el token que creaste
3. Verifica que tenga:
   - ✅ Scope `repo` completo
   - ✅ Acceso al repositorio `Fenix2026-Pedidos/fenix-platform`
   - ✅ Permisos de **Write** o **Admin**

### Si el token es "Fine-grained"

Los tokens fine-grained pueden tener restricciones. Verifica:
- **Repository access**: Debe incluir `Fenix2026-Pedidos/fenix-platform`
- **Permissions**: Debe tener `Contents: Write` y `Metadata: Read`

---

## 📝 Comandos Completos (Copia y Pega)

```powershell
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
git push -u origin master
```

Luego, cuando pida credenciales:
- Username: `Fenix2026-Pedidos`
- Password: `[TU_TOKEN_AQUI]`

---

## ✅ Verificación

Si el push funciona, verás algo como:

```
Enumerating objects: X, done.
Counting objects: 100% (X/X), done.
...
To https://github.com/Fenix2026-Pedidos/fenix-platform.git
 * [new branch]      master -> master
Branch 'master' set up to track remote branch 'master' from 'origin'.
```
