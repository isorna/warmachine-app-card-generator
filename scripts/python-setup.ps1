param([switch]$CheckOnly, [switch]$Library)

function Test-CompatiblePython([string]$Executable, [string[]]$Prefix = @()) {
    if (!$Executable -or $Executable -match '\\WindowsApps\\python[0-9.]*\.exe$') { return $null }
    try {
        $result = & $Executable @Prefix -I -c 'import sys,struct,json,venv,ensurepip; print(json.dumps(dict(path=sys.executable,version=sys.version.split()[0],ok=sys.version_info >= (3,11) and struct.calcsize(chr(80))==8 and (sys.hexversion & 240)==240)))' 2>$null
        if ($LASTEXITCODE -ne 0) { return $null }
        $info = ($result -join "`n") | ConvertFrom-Json
        if ($info.ok) { return $info }
    } catch {}
    return $null
}

function Find-CompatiblePython {
    $root = Split-Path $PSScriptRoot -Parent
    $found = Test-CompatiblePython (Join-Path $root '.venv\Scripts\python.exe')
    if ($found) { return $found }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($version in @('-3.13', '-3.12', '-3.11', '-3')) {
            $found = Test-CompatiblePython $py.Source @($version)
            if ($found) { return $found }
        }
    }
    foreach ($command in @('python.exe','python3.exe')) {
        foreach ($candidate in @(Get-Command $command -All -ErrorAction SilentlyContinue)) {
            $found = Test-CompatiblePython $candidate.Source
            if ($found) { return $found }
        }
    }
    # Registry discovery also works immediately after installation, before PATH refresh.
    foreach ($key in @('HKCU:\Software\Python\PythonCore','HKLM:\Software\Python\PythonCore','HKLM:\Software\WOW6432Node\Python\PythonCore')) {
        foreach ($version in @(Get-ChildItem -LiteralPath $key -ErrorAction SilentlyContinue)) {
            $install = Get-Item -LiteralPath ($version.PSPath + '\InstallPath') -ErrorAction SilentlyContinue
            if ($install) {
                $exe = $install.GetValue('ExecutablePath')
                if (!$exe) { $exe = Join-Path $install.GetValue('') 'python.exe' }
                $found = Test-CompatiblePython $exe
                if ($found) { return $found }
            }
        }
    }
    return $null
}

function Get-RequiredPython([switch]$CheckOnly) {
    $found = Find-CompatiblePython
    if ($found) {
        Write-Host "Python $($found.version) de 64 bits: $($found.path)" -ForegroundColor Green
        return $found.path
    }
    Write-Host 'Se necesita Python estable 3.11 o posterior de 64 bits, con venv y pip.' -ForegroundColor Yellow
    if ($CheckOnly) { throw 'No se ha encontrado Python compatible. Ejecuta Comprobar-Python.cmd para recibir ayuda.' }
    Write-Host '1. Instalar Python 3.13 de 64 bits para este usuario con WinGet (requiere Internet).'
    Write-Host '2. Abrir la descarga oficial para instalarlo manualmente.'
    Write-Host '0. Salir sin instalar.'
    $choice = Read-Host 'Elige una opcion [0]'
    if ($choice -eq '1') {
        $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if ($winget) {
            & $winget.Source install --id Python.Python.3.13 --exact --source winget --scope user --architecture x64 --interactive | Out-Host
            $installExit = $LASTEXITCODE
            $found = Find-CompatiblePython
            if ($found) { Write-Host "Python $($found.version) instalado y verificado."; return $found.path }
            Write-Host "WinGet no ha dejado un Python compatible disponible (codigo $installExit)."
        } else { Write-Host 'WinGet no esta disponible en este equipo.' }
        Write-Host 'Descarga: https://www.python.org/downloads/windows/'
        Write-Host 'Elige Windows installer (64-bit), incluye pip y activa Add Python to PATH. Despues vuelve a ejecutar Comprobar-Python.cmd.'
    } elseif ($choice -eq '2') {
        Start-Process 'https://www.python.org/downloads/windows/'
        Write-Host 'Elige Windows installer (64-bit), incluye pip y activa Add Python to PATH. Despues vuelve a ejecutar Comprobar-Python.cmd.'
    }
    throw 'No se ha completado la comprobacion de Python. Puedes volver a ejecutar el asistente.'
}

if (!$Library) {
    $ErrorActionPreference = 'Stop'
    try { $null = Get-RequiredPython -CheckOnly:$CheckOnly; exit 0 }
    catch { Write-Host "ERROR: $_" -ForegroundColor Red; exit 1 }
}

