# Script PowerShell para compilar traducciones
$env:PATH = $env:PATH + ";C:\Program Files\gettext-iconv\bin"

# Verificar que msgfmt está disponible
$msgfmtPath = "C:\Program Files\gettext-iconv\bin\msgfmt.exe"
if (Test-Path $msgfmtPath) {
    Write-Host "gettext encontrado en: $msgfmtPath" -ForegroundColor Green
    & $msgfmtPath --version
    Write-Host ""
} else {
    Write-Host "ERROR: gettext no encontrado en $msgfmtPath" -ForegroundColor Red
    exit 1
}

# Cambiar al directorio del proyecto
Set-Location $PSScriptRoot

# Compilar traducciones manualmente (solo del proyecto)
Write-Host "Compilando traducciones del proyecto..." -ForegroundColor Yellow
$msgfmtExe = "C:\Program Files\gettext-iconv\bin\msgfmt.exe"

# Compilar español
$esPo = Join-Path $PSScriptRoot "locale\es\LC_MESSAGES\django.po"
$esMo = Join-Path $PSScriptRoot "locale\es\LC_MESSAGES\django.mo"
if (Test-Path $esPo) {
    & $msgfmtExe -o $esMo $esPo
    Write-Host "  [OK] Español compilado" -ForegroundColor Green
}

# Compilar chino
$zhPo = Join-Path $PSScriptRoot "locale\zh_Hans\LC_MESSAGES\django.po"
$zhMo = Join-Path $PSScriptRoot "locale\zh_Hans\LC_MESSAGES\django.mo"
if (Test-Path $zhPo) {
    & $msgfmtExe -o $zhMo $zhPo
    Write-Host "  [OK] Chino compilado" -ForegroundColor Green
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Traducciones compiladas correctamente!" -ForegroundColor Green
    Write-Host "Recarga el servidor Django para ver los cambios." -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Error al compilar traducciones" -ForegroundColor Red
}
