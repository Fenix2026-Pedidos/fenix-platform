@echo off
REM Script seguro para hacer commit limpiando el lock file si existe
REM Uso: git-commit-safe.bat "mensaje del commit"

if "%~1"=="" (
    echo Error: Debes proporcionar un mensaje de commit
    echo Uso: git-commit-safe.bat "mensaje del commit"
    exit /b 1
)

cd /d "%~dp0"

REM Verificar y limpiar lock file si existe
if exist ".git\index.lock" (
    echo Eliminando archivo .git/index.lock...
    del /f /q ".git\index.lock" 2>nul
    if errorlevel 1 (
        echo Error: No se pudo eliminar el lock file
        echo Cierra Cursor/VS Code y otros programas que puedan estar usando git
        exit /b 1
    )
    echo Lock file eliminado correctamente
    timeout /t 1 /nobreak >nul
)

REM Añadir todos los cambios
echo.
echo Añadiendo cambios al staging area...
git add -A
if errorlevel 1 (
    echo Error al añadir cambios
    exit /b 1
)

REM Verificar que hay cambios para commitear
git status --short >nul 2>&1
if errorlevel 1 (
    echo No hay cambios para commitear
    exit /b 0
)

REM Mostrar resumen de cambios
echo.
echo Cambios a commitear:
git status --short

REM Hacer commit
echo.
echo Haciendo commit...
git commit -m "%~1"

if errorlevel 1 (
    echo.
    echo Error al hacer commit
    echo Verifica que no haya otro proceso usando git
    exit /b 1
) else (
    echo.
    echo Commit realizado correctamente!
    echo Mensaje: %~1
)
