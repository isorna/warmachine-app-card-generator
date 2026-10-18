param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
try {
    . (Join-Path $PSScriptRoot 'python-setup.ps1') -Library
    if (Test-Path -LiteralPath $python) {
        if (!(Test-CompatiblePython $python)) {
            throw 'El entorno .venv no funciona o no es compatible. Renombra la carpeta .venv y vuelve a ejecutar para recrearla.'
        }
    } else {
        $basePython = Get-RequiredPython
        & $basePython -m venv (Join-Path $root '.venv')
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
    }
    $requirements = Join-Path $root 'requirements.txt'
    $stamp = Join-Path $root '.venv\requirements.sha256'
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($hasher.ComputeHash([IO.File]::ReadAllBytes($requirements))).Replace('-', '') } finally { $hasher.Dispose() }
    if (!(Test-Path -LiteralPath $stamp) -or (Get-Content -LiteralPath $stamp -Raw).Trim() -ne $hash) {
        & $python -m pip install -r $requirements
        if ($LASTEXITCODE -ne 0) { throw 'Fallo al instalar dependencias. Comprueba Internet y vuelve a ejecutar.' }
        Set-Content -LiteralPath $stamp -Value $hash -Encoding ascii
    }
    & $python (Join-Path $PSScriptRoot 'generate-warmachine-cards.py') @Arguments
    exit $LASTEXITCODE
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
