# Slide Master / INNerGEN skill set - Windows setup
# Creates .venv, installs dependencies, fonts and optional tools, syncs the Claude / GPT (Codex) / Gemini
# skill sets, and verifies with a self-test deck. Installs Python 3.12 through winget when none is found.
# Usage:  powershell -ExecutionPolicy Bypass -File .\setup.ps1 [--skip-fonts] [--skip-extras] [--recreate] [--check]

$ErrorActionPreference = 'Continue'
$setupScript = Join-Path $PSScriptRoot '.claude\skills\ppt-master\scripts\setup_env.py'

function Invoke-Setup {
    $ErrorActionPreference = 'Stop'
    # Prefer the existing environment, except when it is about to be recreated.
    # Then try PATH and per-user locations that a fresh install may not expose yet.
    $candidates = @(
        @{ exe = 'py'; pre = @('-3') },
        @{ exe = 'python'; pre = @() },
        @{ exe = 'python3'; pre = @() },
        @{ exe = "$env:LOCALAPPDATA\Programs\Python\Launcher\py.exe"; pre = @('-3') },
        @{ exe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"; pre = @() },
        @{ exe = "$env:WINDIR\py.exe"; pre = @('-3') }
    )
    if ($args -notcontains '--recreate') {
        $candidates = @(@{ exe = (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'); pre = @() }) + $candidates
    }
    foreach ($c in $candidates) {
        if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
        try {
            & $c.exe @($c.pre + @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)')) 2>$null
            if ($LASTEXITCODE -ne 0) { continue }
        } catch {
            # Windows App Execution Aliases may exist without a runnable Python.
            continue
        }
        & $c.exe @($c.pre + @($setupScript) + $args)
        exit $LASTEXITCODE
    }
}

Invoke-Setup @args

# Diagnostics must never install software on a PC that has no usable Python.
if (($args -contains '--check') -or ($args -contains '--help') -or ($args -contains '-h')) {
    Write-Error 'Python 3.10+ not found. Run setup.ps1 without --check to install, or ask IT to install Python.'
    exit 1
}

if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host '[setup] Python 3.10+ not found - installing Python 3.12 with winget'
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-source-agreements --accept-package-agreements --override '/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1'
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
    Invoke-Setup @args
}
Write-Error 'Python 3.10+ not found. Install it from https://www.python.org/downloads/ (check "Add to PATH") and re-run.'
exit 1
