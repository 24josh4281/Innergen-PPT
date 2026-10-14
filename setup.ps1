# Slide Master / INNerGEN skill set - Windows setup
# Creates .venv, installs dependencies, fonts and optional tools, syncs the Claude / GPT (Codex) / Gemini
# skill sets, and verifies with a self-test deck. Installs Python 3.12 through winget when none is found.
# Usage:  powershell -ExecutionPolicy Bypass -File .\setup.ps1 [--skip-fonts] [--skip-extras] [--recreate] [--check]

$ErrorActionPreference = 'Continue'
$script = Join-Path $PSScriptRoot '.claude\skills\ppt-master\scripts\setup_env.py'

function Invoke-Setup {
    # PATH entries first, then the per-user / launcher locations a fresh winget install
    # may not have put on this session's PATH yet.
    $candidates = @(
        @{ exe = 'py'; pre = @('-3') },
        @{ exe = 'python'; pre = @() },
        @{ exe = 'python3'; pre = @() },
        @{ exe = "$env:LOCALAPPDATA\Programs\Python\Launcher\py.exe"; pre = @('-3') },
        @{ exe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"; pre = @() },
        @{ exe = "$env:WINDIR\py.exe"; pre = @('-3') }
    )
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
        & $c.exe @($c.pre + @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)')) 2>$null
        if ($LASTEXITCODE -ne 0) { continue }
        & $c.exe @($c.pre + @($script) + $args)
        exit $LASTEXITCODE
    }
}

Invoke-Setup @args

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host '[setup] Python 3.10+ not found - installing Python 3.12 with winget'
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-source-agreements --accept-package-agreements --override '/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
    Invoke-Setup @args
}
Write-Error 'Python 3.10+ not found. Install it from https://www.python.org/downloads/ (check "Add to PATH") and re-run.'
exit 1
