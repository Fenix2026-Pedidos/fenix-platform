# Solución para el bloqueo de Git (index.lock)

## Problema

Cada vez que intentas hacer commit, aparece el error:
```
fatal: Unable to create '.../.git/index.lock': Permission denied
```

## Causas Comunes

1. **Proceso de git no terminado**: Un comando de git anterior no terminó correctamente
2. **IDE/Editor bloqueando**: Cursor, VS Code u otro editor puede estar bloqueando el archivo
3. **Múltiples procesos**: Varios procesos de git ejecutándose simultáneamente
4. **Antivirus**: Algunos antivirus bloquean archivos `.lock` en directorios `.git`

## Solución Rápida (Manual)

Si el error aparece, ejecuta:

```powershell
# En PowerShell
Remove-Item .git\index.lock -Force
```

O en CMD:
```cmd
del /f /q .git\index.lock
```

Luego intenta el commit de nuevo.

## Solución Automática (Recomendado)

He creado scripts que limpian el lock file automáticamente antes de cada commit:

### Opción 1: PowerShell (Recomendado)

```powershell
.\git-commit-safe.ps1 "Tu mensaje de commit aquí"
```

### Opción 2: Batch (CMD)

```cmd
git-commit-safe.bat "Tu mensaje de commit aquí"
```

Estos scripts:
- ✅ Eliminan automáticamente el lock file si existe
- ✅ Verifican procesos de git activos
- ✅ Muestran un resumen de cambios antes de commitear
- ✅ Manejan errores de forma clara

## Prevención

### 1. Cerrar programas antes de commitear

Si usas Cursor o VS Code:
- Cierra el editor antes de hacer commit desde la terminal
- O usa el commit desde la interfaz del editor (Ctrl+Shift+G en VS Code)

### 2. Verificar procesos de git

Antes de commitear, verifica que no haya procesos de git ejecutándose:

```powershell
Get-Process -Name "git*" -ErrorAction SilentlyContinue
```

Si hay procesos, ciérralos:
```powershell
Stop-Process -Name "git*" -Force
```

### 3. Usar un solo método de commit

- **O** commits desde la terminal
- **O** commits desde el editor
- **NO** ambos al mismo tiempo

## Configuración de Git (Opcional)

Puedes configurar git para que sea más tolerante:

```bash
git config core.preloadindex true
git config core.fscache true
```

## Si el problema persiste

1. **Reinicia el sistema**: A veces procesos zombie bloquean archivos
2. **Verifica permisos**: Asegúrate de tener permisos de escritura en `.git/`
3. **Desactiva antivirus temporalmente**: Algunos antivirus bloquean `.lock` files
4. **Usa el script automático**: `git-commit-safe.ps1` o `git-commit-safe.bat`

## Ejemplo de Uso

```powershell
# Cambiar al directorio del proyecto
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"

# Hacer commit de forma segura
.\git-commit-safe.ps1 "Mejoras en el catálogo y traducciones"
```

El script mostrará:
- ✅ Si elimina el lock file
- 📋 Resumen de cambios
- 💾 Confirmación del commit exitoso
