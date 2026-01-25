# Script para hacer push a GitHub deshabilitando proxy temporalmente
# Plataforma Fenix

Write-Host "=== Push a GitHub - Plataforma Fenix ===" -ForegroundColor Cyan
Write-Host ""

# Limpiar lock files
if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
    Write-Host "[OK] Lock file eliminado" -ForegroundColor Green
}

# Detener procesos Git activos
Get-Process -Name "git*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Guardar variables de proxy actuales
$oldHttpProxy = $env:HTTP_PROXY
$oldHttpsProxy = $env:HTTPS_PROXY

# Deshabilitar proxy temporalmente para este comando
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null

Write-Host "Proxy deshabilitado temporalmente para este comando" -ForegroundColor Yellow
Write-Host ""

try {
    # Intentar hacer push
    Write-Host "Intentando hacer push a GitHub..." -ForegroundColor Yellow
    git push -u origin master
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] Push completado exitosamente!" -ForegroundColor Green
        Write-Host "Repositorio: https://github.com/Fenix2026-Pedidos/fenix-platform" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERROR] El push falló. Posibles causas:" -ForegroundColor Red
        Write-Host "  1. Problemas de autenticación (necesitas Personal Access Token)" -ForegroundColor Yellow
        Write-Host "  2. El repositorio remoto tiene cambios diferentes" -ForegroundColor Yellow
        Write-Host "  3. Problemas de red" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Ver GITHUB_CONNECTION.md para más información" -ForegroundColor Cyan
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Error al hacer push: $_" -ForegroundColor Red
} finally {
    # Restaurar variables de proxy (opcional, comentado para no afectar otras aplicaciones)
    # $env:HTTP_PROXY = $oldHttpProxy
    # $env:HTTPS_PROXY = $oldHttpsProxy
}

Write-Host ""
Write-Host "=== Fin ===" -ForegroundColor Cyan
