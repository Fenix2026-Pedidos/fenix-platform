$ErrorActionPreference = 'Stop'

$project = 'project-8ec7876a-62b7-4e0b-82d'
$account = 'fenixdelamancha2026@gmail.com'
$secretName = 'fenix-whatsapp-app-secret'
$tempFile = Join-Path $env:TEMP "fenix-meta-app-secret-$PID.tmp"

$secureValue = Read-Host 'Pega el secreto de Fenix APP (la entrada permanecera oculta)' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
$plainValue = $null

try {
    $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ($plainValue -notmatch '^[A-Fa-f0-9]{32,128}$') {
        throw 'El valor no tiene el formato esperado para un secreto de aplicacion de Meta.'
    }

    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($tempFile, $plainValue, $utf8)

    & gcloud.cmd secrets versions add $secretName `
        --project=$project `
        --account=$account `
        --data-file=$tempFile `
        --quiet

    if ($LASTEXITCODE -ne 0) {
        throw 'Google Cloud no pudo crear la version del secreto.'
    }

    Write-Host ''
    Write-Host 'Secreto de Meta almacenado correctamente en Secret Manager.' -ForegroundColor Green
}
finally {
    if (Test-Path -LiteralPath $tempFile) {
        Remove-Item -LiteralPath $tempFile -Force
    }
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $plainValue = $null
    $secureValue.Dispose()
}

Read-Host 'Pulsa Enter para cerrar'
