# Script seguro para hacer commit limpiando el lock file si existe
# Uso: .\git-commit-safe.ps1 "mensaje del commit"

param(
    [Parameter(Mandatory=$true)]
    [string]$CommitMessage
)

# Cambiar al directorio del proyecto
Set-Location $PSScriptRoot

# Verificar y limpiar lock file si existe
$lockFile = Join-Path $PSScriptRoot ".git\index.lock"
if (Test-Path $lockFile) {
    Write-Host "⚠️  Encontrado archivo .git/index.lock, eliminándolo..." -ForegroundColor Yellow
    try {
        Remove-Item $lockFile -Force -ErrorAction Stop
        Write-Host "✅ Lock file eliminado correctamente" -ForegroundColor Green
        Start-Sleep -Milliseconds 500  # Pequeña pausa para asegurar que se liberó
    } catch {
        Write-Host "❌ Error al eliminar lock file: $_" -ForegroundColor Red
        Write-Host "💡 Intenta cerrar Cursor/VS Code y otros programas que puedan estar usando git" -ForegroundColor Cyan
        exit 1
    }
}

# Verificar que no hay procesos de git ejecutándose
$gitProcesses = Get-Process -Name "git*" -ErrorAction SilentlyContinue
if ($gitProcesses) {
    Write-Host "⚠️  Advertencia: Hay procesos de git ejecutándose:" -ForegroundColor Yellow
    $gitProcesses | ForEach-Object { Write-Host "   - PID $($_.Id): $($_.ProcessName)" -ForegroundColor Yellow }
    Write-Host "💡 Esperando 2 segundos antes de continuar..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
}

# Añadir todos los cambios
Write-Host "`n📦 Añadiendo cambios al staging area..." -ForegroundColor Cyan
git add -A
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al añadir cambios" -ForegroundColor Red
    exit 1
}

# Verificar que hay cambios para commitear
$status = git status --short
if (-not $status) {
    Write-Host "ℹ️  No hay cambios para commitear" -ForegroundColor Yellow
    exit 0
}

# Mostrar resumen de cambios
Write-Host "`n📋 Cambios a commitear:" -ForegroundColor Cyan
git status --short

# Hacer commit
Write-Host "`n💾 Haciendo commit..." -ForegroundColor Cyan
git commit -m $CommitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Commit realizado correctamente!" -ForegroundColor Green
    Write-Host "📝 Mensaje: $CommitMessage" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Error al hacer commit" -ForegroundColor Red
    Write-Host "💡 Verifica que no haya otro proceso usando git" -ForegroundColor Cyan
    exit 1
}
