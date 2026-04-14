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
    Write-Host "[WAIT] Encontrado archivo .git/index.lock, eliminandolo..." -ForegroundColor Yellow
    try {
        Remove-Item $lockFile -Force -ErrorAction Stop
        Write-Host "[OK] Lock file eliminado correctamente" -ForegroundColor Green
        Start-Sleep -Milliseconds 500
    } catch {
        Write-Host "[ERROR] Error al eliminar lock file: $_" -ForegroundColor Red
        Write-Host "TIP: Intenta cerrar Cursor/VS Code y otros programas que puedan estar usando git" -ForegroundColor Cyan
        exit 1
    }
}

# Verificar procesos git
$gitProcesses = Get-Process -Name "git*" -ErrorAction SilentlyContinue
if ($gitProcesses) {
    Write-Host "[WARNING] Advertencia: Hay procesos de git ejecutandose:" -ForegroundColor Yellow
    $gitProcesses | ForEach-Object { Write-Host "   - PID $($_.Id): $($_.ProcessName)" -ForegroundColor Yellow }
    Start-Sleep -Seconds 2
}

# Add changes
Write-Host "`n[GIT] Anadiendo cambios..." -ForegroundColor Cyan
git add -A
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Error al anadir cambios" -ForegroundColor Red
    exit 1
}

# Status check
$status = git status --short
if (-not $status) {
    Write-Host "[INFO] No hay cambios para commitear" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n[STATUS] Cambios a commitear:" -ForegroundColor Cyan
git status --short

# Commit
Write-Host "`n[GIT] Haciendo commit..." -ForegroundColor Cyan
git commit -m $CommitMessage

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Commit realizado correctamente!" -ForegroundColor Green
    Write-Host "Mensaje: $CommitMessage" -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Error al hacer commit" -ForegroundColor Red
    exit 1
}
