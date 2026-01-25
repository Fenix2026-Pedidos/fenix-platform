# Solucionar PATH de gettext

## Problema
gettext está instalado en `C:\Program Files\gettext-iconv\bin\` pero no está en el PATH del sistema.

## Solución Rápida (Solo para esta sesión)

Abre PowerShell o CMD y ejecuta:
```powershell
$env:PATH += ";C:\Program Files\gettext-iconv\bin"
```

Luego verifica:
```powershell
msgfmt --version
```

## Solución Permanente (Recomendado)

### Opción 1: Añadir al PATH del sistema (Windows 10/11)

1. Presiona `Win + X` y selecciona "Sistema"
2. Haz clic en "Configuración avanzada del sistema"
3. En la pestaña "Opciones avanzadas", haz clic en "Variables de entorno"
4. En "Variables del sistema", busca y selecciona "Path", luego haz clic en "Editar"
5. Haz clic en "Nuevo" y añade: `C:\Program Files\gettext-iconv\bin`
6. Haz clic en "Aceptar" en todas las ventanas
7. **Cierra y vuelve a abrir todas las terminales** (PowerShell, CMD, etc.)

### Opción 2: Usando PowerShell (como Administrador)

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "Machine") + ";C:\Program Files\gettext-iconv\bin",
    "Machine"
)
```

Luego cierra y vuelve a abrir la terminal.

### Opción 3: Usar ruta completa (temporal)

Mientras tanto, puedes usar la ruta completa:
```bash
"C:\Program Files\gettext-iconv\bin\msgfmt.exe" --version
```

O configurar Django para usar esta ruta específica.

## Verificar después de añadir al PATH

1. Cierra todas las terminales abiertas
2. Abre una nueva terminal
3. Ejecuta:
   ```bash
   msgfmt --version
   ```
4. Deberías ver algo como: `msgfmt (GNU gettext-tools) 0.26`

## Compilar traducciones

### Opción 1: Usar el script proporcionado (Más fácil)

He creado un script que añade gettext al PATH automáticamente:

**En PowerShell:**
```powershell
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
.\compile_translations.ps1
```

**O en CMD:**
```cmd
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
compile_translations.bat
```

### Opción 2: Manualmente (después de añadir al PATH permanentemente)

Una vez que `msgfmt` funcione globalmente, ejecuta:
```bash
cd "c:\Users\Solutio\Desktop\Vladimir Personal\Ofertas\Fenix\Plataforma Fenix"
python manage.py compilemessages
```
