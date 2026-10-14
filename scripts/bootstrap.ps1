param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv\Scripts\python.exe'
try {
    if (!(Test-Path -LiteralPath $python)) {
        $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($launcher) {
            & $launcher.Source -3 -c "import sys; assert sys.version_info >= (3, 11), 'Se requiere Python 3.11 o posterior'"
            if ($LASTEXITCODE -ne 0) { throw 'Instala Python 3.11 o posterior de 64 bits desde python.org.' }
            & $launcher.Source -3 -m venv (Join-Path $root '.venv')
        } else {
            $launcher = Get-Command python.exe -ErrorAction SilentlyContinue
            if (!$launcher) { throw 'Instala Python 3.11 o posterior de 64 bits desde python.org y activa Add Python to PATH.' }
            & $launcher.Source -c "import sys; assert sys.version_info >= (3, 11), 'Se requiere Python 3.11 o posterior'"
            if ($LASTEXITCODE -ne 0) { throw 'No se ha encontrado un Python compatible.' }
            & $launcher.Source -m venv (Join-Path $root '.venv')
        }
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
