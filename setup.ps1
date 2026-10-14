# Slide Master / INNerGEN skill set - Windows setup
# Creates .venv, installs dependencies and fonts, and syncs the Claude / GPT (Codex) / Gemini skill sets.
# Usage:  powershell -ExecutionPolicy Bypass -File .\setup.ps1 [--skip-fonts] [--recreate] [--check]

$ErrorActionPreference = 'Continue'
$script = Join-Path $PSScriptRoot '.claude\skills\ppt-master\scripts\setup_env.py'

$candidates = @(
    @{ exe = 'py'; pre = @('-3') },
    @{ exe = 'python'; pre = @() },
    @{ exe = 'python3'; pre = @() }
)
foreach ($c in $candidates) {
    if (-not (Get-Command $c.exe -ErrorAction SilentlyContinue)) { continue }
    & $c.exe @($c.pre + @('-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)')) 2>$null
    if ($LASTEXITCODE -ne 0) { continue }
    & $c.exe @($c.pre + @($script) + $args)
    exit $LASTEXITCODE
}
Write-Error 'Python 3.10+ not found. Install it from https://www.python.org/downloads/ (check "Add to PATH") and re-run.'
exit 1
