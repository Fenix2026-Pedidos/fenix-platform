# Script para deshabilitar proxy y hacer push a GitHub
# Plataforma Fenix

Write-Host "=== Deshabilitar Proxy y Push a GitHub ===" -ForegroundColor Cyan
Write-Host ""

# IMPORTANTE: Sin espacios después de $env:
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null

Write-Host "[OK] Variables de proxy deshabilitadas" -ForegroundColor Green
Write-Host "  HTTP_PROXY: $env:HTTP_PROXY" -ForegroundColor Gray
Write-Host "  HTTPS_PROXY: $env:HTTPS_PROXY" -ForegroundColor Gray
Write-Host ""

# Limpiar lock files
if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
    Write-Host "[OK] Lock file eliminado" -ForegroundColor Green
}

# Detener procesos Git activos
Get-Process -Name "git*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Intentando hacer push a GitHub..." -ForegroundColor Yellow
Write-Host ""

try {
    git push -u origin master
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[OK] Push completado exitosamente!" -ForegroundColor Green
        Write-Host "Repositorio: https://github.com/Fenix2026-Pedidos/fenix-platform" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "[ERROR] El push falló. Código de salida: $LASTEXITCODE" -ForegroundColor Red
        Write-Host ""
        Write-Host "Posibles causas:" -ForegroundColor Yellow
        Write-Host "  1. Problemas de autenticación (necesitas Personal Access Token)" -ForegroundColor White
        Write-Host "  2. El repositorio remoto tiene cambios diferentes" -ForegroundColor White
        Write-Host "  3. Problemas de red o firewall" -ForegroundColor White
        Write-Host ""
        Write-Host "Ver GITHUB_CONNECTION.md para más información" -ForegroundColor Cyan
    }
} catch {
    Write-Host ""
    Write-Host "[ERROR] Error al hacer push: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Fin ===" -ForegroundColor Cyan
