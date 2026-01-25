# Script para verificar el token de GitHub
Write-Host "=== Verificación de Token GitHub ===" -ForegroundColor Cyan
Write-Host ""

$token = "[TU_TOKEN_AQUI]"

# Deshabilitar proxy
$env:HTTP_PROXY = $null
$env:HTTPS_PROXY = $null
$env:http_proxy = $null
$env:https_proxy = $null

Write-Host "1. Verificando token con GitHub API..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $token"
        "Accept" = "application/vnd.github.v3+json"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -Method Get
    Write-Host "   [OK] Token válido" -ForegroundColor Green
    Write-Host "   Usuario: $($response.login)" -ForegroundColor Gray
    Write-Host "   Nombre: $($response.name)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "2. Verificando acceso al repositorio..." -ForegroundColor Yellow
    $repoResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/Fenix2026-Pedidos/fenix-platform" -Headers $headers -Method Get
    Write-Host "   [OK] Repositorio accesible" -ForegroundColor Green
    Write-Host "   Repo: $($repoResponse.full_name)" -ForegroundColor Gray
    Write-Host "   Permisos del usuario:" -ForegroundColor Gray
    
    # Verificar permisos del usuario en el repo
    $permsResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/Fenix2026-Pedidos/fenix-platform/collaborators/$($response.login)/permission" -Headers $headers -Method Get
    Write-Host "   Permiso: $($permsResponse.permission)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "3. El token parece válido. El problema podría ser:" -ForegroundColor Yellow
    Write-Host "   - El token no tiene el scope 'repo' completo" -ForegroundColor White
    Write-Host "   - El token es 'fine-grained' y tiene restricciones específicas" -ForegroundColor White
    Write-Host "   - Necesitas verificar los permisos del token en GitHub" -ForegroundColor White
    
} catch {
    Write-Host "   [ERROR] No se pudo verificar el token" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Posibles causas:" -ForegroundColor Yellow
    Write-Host "   1. El token es inválido o fue revocado" -ForegroundColor White
    Write-Host "   2. El token no tiene los permisos necesarios" -ForegroundColor White
    Write-Host "   3. Problemas de red o proxy" -ForegroundColor White
}

Write-Host ""
Write-Host "=== Fin ===" -ForegroundColor Cyan
