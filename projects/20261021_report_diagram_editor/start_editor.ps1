$ErrorActionPreference='Stop'
$projectRoot=$PSScriptRoot
$python=Join-Path $projectRoot '../../.venv/Scripts/python.exe'
if(-not(Test-Path -LiteralPath $python)){throw 'Repository .venv Python was not found.'}
Write-Host 'INNerGEN report editor: http://127.0.0.1:8088/'
Write-Host 'Press Ctrl+C in this window to stop.'
& $python -m http.server 8088 --bind 127.0.0.1 --directory (Join-Path $projectRoot 'dist')
