$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\python-setup.ps1') -Library
if (Test-CompatiblePython 'C:\does-not-exist\python.exe') { throw 'Missing interpreter accepted' }
if (Test-CompatiblePython 'C:\Users\Example\AppData\Local\Microsoft\WindowsApps\python.exe') { throw 'Store alias accepted' }
$actual = Find-CompatiblePython
if (!$actual) { throw 'Installed test interpreter not found' }
function Find-CompatiblePython { return $null }
function Read-Host { throw 'Unexpected prompt in CheckOnly mode' }
$failed = $false
try { Get-RequiredPython -CheckOnly } catch { $failed = $_ -match 'No se ha encontrado Python compatible' }
if (!$failed) { throw 'Missing Python must fail without prompting in CheckOnly mode' }
function Read-Host { return '0' }
function Start-Process { throw 'Unexpected browser/installer execution' }
$failed = $false
try { Get-RequiredPython } catch { $failed = $_ -match 'No se ha completado' }
if (!$failed) { throw 'Cancellation must fail cleanly without installation' }
function Find-CompatiblePython { return [pscustomobject]@{path='C:\Test Python\python.exe';version='3.13.0'} }
if ((Get-RequiredPython) -ne 'C:\Test Python\python.exe') { throw 'Compatible interpreter path lost' }
Write-Host 'Python setup checks passed.'
