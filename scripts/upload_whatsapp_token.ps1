$ErrorActionPreference = 'Stop'

$project = 'project-8ec7876a-62b7-4e0b-82d'
$account = 'fenixdelamancha2026@gmail.com'
$secretName = 'fenix-whatsapp-access-token'
$tempFile = Join-Path $env:TEMP "fenix-whatsapp-token-$PID.tmp"

$secureValue = Read-Host 'Pega el nuevo token de WhatsApp (la entrada permanecera oculta)' -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
$plainValue = $null

try {
    $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if (-not $plainValue.StartsWith('EAA') -or $plainValue.Length -lt 50) {
        throw 'El valor no parece un token valido de Meta.'
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
    Write-Host 'Token almacenado correctamente en Secret Manager.' -ForegroundColor Green
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
