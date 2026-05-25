param(
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check($Name, $Status, $Detail) {
  $checks.Add([pscustomobject]@{
    Name = $Name
    Status = $Status
    Detail = $Detail
  })
}

function Test-Command($Name) {
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  return $null -ne $cmd
}

try {
  if (Test-Command "node") {
    $nodeVersion = (& node --version).Trim()
    Add-Check "Node.js" "PASS" $nodeVersion
  } else {
    Add-Check "Node.js" "FAIL" "Node.js is not installed or not on PATH."
  }

  if (Test-Command "npm") {
    $npmVersion = (& npm --version).Trim()
    Add-Check "npm" "PASS" $npmVersion
  } else {
    Add-Check "npm" "FAIL" "npm is not installed or not on PATH."
  }

  $requiredFiles = @(
    "AGENTS.md",
    "README.md",
    "docs\codex-onboarding.md",
    "docs\gpt-ppt-prompt-generator.md",
    "docs\one-shot-structure-qa-rules.md",
    "package.json",
    "vite.config.ts",
    "src\main.ts",
    "src\ppt.ts",
    "src\promptGenerator.ts"
  )

  foreach ($file in $requiredFiles) {
    if (Test-Path -LiteralPath $file) {
      Add-Check "Required file: $file" "PASS" "Found."
    } else {
      Add-Check "Required file: $file" "FAIL" "Missing."
    }
  }

  $gitignore = Get-Content -LiteralPath ".gitignore" -Raw
  foreach ($pattern in @(".env", "docs/generated/", "docs/backups/", "node_modules/", "dist/")) {
    if ($gitignore -like "*$pattern*") {
      Add-Check "Ignore rule: $pattern" "PASS" "Protected from accidental commit."
    } else {
      Add-Check "Ignore rule: $pattern" "FAIL" "Missing from .gitignore."
    }
  }

  if (Test-Path -LiteralPath ".env") {
    Add-Check "Local .env" "PASS" ".env exists locally and is ignored by git."
  } else {
    Add-Check "Local .env" "WARN" "Optional. Copy .env.example only if API mode is intentionally enabled."
  }

  if ($SkipBuild) {
    Add-Check "Build" "WARN" "Skipped by -SkipBuild."
  } else {
    & npm run build
    if ($LASTEXITCODE -eq 0) {
      Add-Check "Build" "PASS" "npm run build completed."
    } else {
      Add-Check "Build" "FAIL" "npm run build failed with exit code $LASTEXITCODE."
    }
  }
} catch {
  Add-Check "Script error" "FAIL" $_.Exception.Message
}

$checks | Format-Table -AutoSize

$failed = @($checks | Where-Object { $_.Status -eq "FAIL" })
if ($failed.Count -gt 0) {
  Write-Host ""
  Write-Host "Setup verification failed. Fix the FAIL items above before sharing this repo." -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "Setup verification passed. This repo is ready for Codex onboarding." -ForegroundColor Green
