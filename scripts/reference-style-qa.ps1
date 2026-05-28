param(
  [Parameter(Mandatory=$true)]
  [string]$CandidateImageDir,

  [Parameter(Mandatory=$true)]
  [string]$ReferenceImageDir,

  [string]$SlideMap = "",

  [string]$ProfileId = "",

  [string]$ProfileDbPath = "docs/reference-structure-db.json",

  [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

function Get-DarkRatio {
  param(
    [System.Drawing.Bitmap]$Bitmap,
    [int]$X0,
    [int]$Y0,
    [int]$X1,
    [int]$Y1
  )

  $dark = 0
  $total = 0
  $stepX = [Math]::Max(1, [Math]::Floor(($X1 - $X0) / 160))
  $stepY = [Math]::Max(1, [Math]::Floor(($Y1 - $Y0) / 90))
  for ($x = $X0; $x -lt $X1; $x += $stepX) {
    for ($y = $Y0; $y -lt $Y1; $y += $stepY) {
      $c = $Bitmap.GetPixel($x, $y)
      $brightness = ($c.R + $c.G + $c.B) / 3
      if ($brightness -lt 95) { $dark++ }
      $total++
    }
  }
  if ($total -eq 0) { return 0 }
  return [Math]::Round($dark / $total, 4)
}

function Get-InkRatio {
  param(
    [System.Drawing.Bitmap]$Bitmap,
    [int]$X0,
    [int]$Y0,
    [int]$X1,
    [int]$Y1
  )

  $ink = 0
  $total = 0
  $stepX = [Math]::Max(1, [Math]::Floor(($X1 - $X0) / 180))
  $stepY = [Math]::Max(1, [Math]::Floor(($Y1 - $Y0) / 100))
  for ($x = $X0; $x -lt $X1; $x += $stepX) {
    for ($y = $Y0; $y -lt $Y1; $y += $stepY) {
      $c = $Bitmap.GetPixel($x, $y)
      $distanceFromWhite = [Math]::Abs(255 - $c.R) + [Math]::Abs(255 - $c.G) + [Math]::Abs(255 - $c.B)
      if ($distanceFromWhite -gt 42) { $ink++ }
      $total++
    }
  }
  if ($total -eq 0) { return 0 }
  return [Math]::Round($ink / $total, 4)
}

function Measure-SlideImage {
  param([string]$Path)
  $bmp = [System.Drawing.Bitmap]::FromFile($Path)
  try {
    $w = $bmp.Width
    $h = $bmp.Height
    return [pscustomobject]@{
      path = $Path
      width = $w
      height = $h
      topDarkRatio = Get-DarkRatio $bmp 0 0 ([int]($w * 0.82)) ([int]($h * 0.105))
      bottomDarkRatio = Get-DarkRatio $bmp 0 ([int]($h * 0.915)) $w $h
      bodyInkRatio = Get-InkRatio $bmp ([int]($w * 0.025)) ([int]($h * 0.13)) ([int]($w * 0.975)) ([int]($h * 0.9))
    }
  }
  finally {
    $bmp.Dispose()
  }
}

$candidateDir = [System.IO.Path]::GetFullPath($CandidateImageDir)
$referenceDir = [System.IO.Path]::GetFullPath($ReferenceImageDir)
if (-not (Test-Path -LiteralPath $candidateDir)) { throw "Candidate image dir not found: $candidateDir" }
if (-not (Test-Path -LiteralPath $referenceDir)) { throw "Reference image dir not found: $referenceDir" }

if ((-not $SlideMap -or -not $SlideMap.Trim()) -and $ProfileId -and $ProfileId.Trim()) {
  $repoRoot = Split-Path -Parent $PSScriptRoot
  $resolvedProfileDbPath = if ([System.IO.Path]::IsPathRooted($ProfileDbPath)) {
    [System.IO.Path]::GetFullPath($ProfileDbPath)
  } else {
    [System.IO.Path]::GetFullPath((Join-Path $repoRoot $ProfileDbPath))
  }
  if (-not (Test-Path -LiteralPath $resolvedProfileDbPath)) { throw "Profile DB not found: $resolvedProfileDbPath" }
  $profileDb = Get-Content -LiteralPath $resolvedProfileDbPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $profile = @($profileDb.profiles | Where-Object { $_.id -eq $ProfileId } | Select-Object -First 1)
  if (-not $profile.Count) { throw "Profile not found in DB: $ProfileId" }
  $SlideMap = (($profile[0].referenceSlideMap.PSObject.Properties | Sort-Object { [int]$_.Name }) | ForEach-Object {
    "$($_.Name):$($_.Value)"
  }) -join ","
}

$candidateImages = @(Get-ChildItem -LiteralPath $candidateDir -Filter "slide-*.png" | Sort-Object Name)
$referenceImages = @(Get-ChildItem -LiteralPath $referenceDir -Filter "slide-*.png" | Sort-Object Name)
if (-not $candidateImages.Count) { throw "No candidate slide images found: $candidateDir" }
if (-not $referenceImages.Count) { throw "No reference slide images found: $referenceDir" }

$slideMapTable = @{}
if ($SlideMap -and $SlideMap.Trim()) {
  foreach ($pair in ($SlideMap -split ",")) {
    $parts = $pair.Trim() -split ":"
    if ($parts.Count -eq 2 -and $parts[0] -match '^\d+$' -and $parts[1] -match '^\d+$') {
      $slideMapTable[[int]$parts[0]] = [int]$parts[1]
    }
  }
}

$referenceMeasures = @($referenceImages | ForEach-Object {
  $m = Measure-SlideImage $_.FullName
  $m | Add-Member -NotePropertyName slide -NotePropertyValue ([int]([regex]::Match($_.Name, 'slide-(\d+)').Groups[1].Value))
  $m
})
$referenceBodyMeasures = @($referenceMeasures | Where-Object { $_.slide -gt 1 })
$referenceBodyInkAvg = [Math]::Round((($referenceMeasures | Measure-Object bodyInkRatio -Average).Average), 4)
$referenceTopDarkAvg = [Math]::Round((($referenceBodyMeasures | Measure-Object topDarkRatio -Average).Average), 4)
$referenceBottomDarkAvg = [Math]::Round((($referenceBodyMeasures | Measure-Object bottomDarkRatio -Average).Average), 4)

$slides = @()
$issues = New-Object System.Collections.Generic.List[string]
foreach ($img in $candidateImages) {
  $m = Measure-SlideImage $img.FullName
  $slideNo = [int]([regex]::Match($img.Name, 'slide-(\d+)').Groups[1].Value)
  $referenceSlideNo = if ($slideMapTable.ContainsKey($slideNo)) { [int]$slideMapTable[$slideNo] } else { $slideNo }
  $matchedReference = @($referenceMeasures | Where-Object { $_.slide -eq $referenceSlideNo } | Select-Object -First 1)
  $targetBodyInk = if ($matchedReference.Count) { [double]$matchedReference[0].bodyInkRatio } else { $referenceBodyInkAvg }
  $targetTopDark = if ($matchedReference.Count -and $slideNo -gt 1) { [double]$matchedReference[0].topDarkRatio } else { $referenceTopDarkAvg }
  $targetBottomDark = if ($matchedReference.Count) { [double]$matchedReference[0].bottomDarkRatio } else { $referenceBottomDarkAvg }
  $slideIssues = New-Object System.Collections.Generic.List[string]
  if ($slideNo -gt 1 -and $m.topDarkRatio -lt [Math]::Max(0.25, $targetTopDark * 0.65)) { $slideIssues.Add("top-brand-band-weak") }
  if ($m.bottomDarkRatio -lt [Math]::Max(0.20, $targetBottomDark * 0.55)) { $slideIssues.Add("footer-band-weak") }
  if ($slideNo -gt 1 -and $m.bodyInkRatio -lt [Math]::Max(0.055, $targetBodyInk * 0.62)) { $slideIssues.Add("content-density-low") }
  foreach ($issue in $slideIssues) { $issues.Add(("slide-{0:D2}:{1}" -f $slideNo, $issue)) }
  $slides += [pscustomobject]@{
    slide = $slideNo
    referenceSlide = $referenceSlideNo
    topDarkRatio = $m.topDarkRatio
    bottomDarkRatio = $m.bottomDarkRatio
    bodyInkRatio = $m.bodyInkRatio
    issues = @($slideIssues)
  }
}

$score = [Math]::Max(0, 100 - ($issues.Count * 7))
$status = if ($issues.Count -eq 0) { "pass" } elseif ($issues.Count -le 4) { "warn" } else { "fail" }
$report = [pscustomobject]@{
  reference = [pscustomobject]@{
    imageDir = $referenceDir
    bodyInkRatioAvg = $referenceBodyInkAvg
    topDarkRatioAvg = $referenceTopDarkAvg
    bottomDarkRatioAvg = $referenceBottomDarkAvg
  }
  candidate = [pscustomobject]@{
    imageDir = $candidateDir
    slides = $candidateImages.Count
    slideMap = $SlideMap
    profileId = $ProfileId
  }
  score = $score
  status = $status
  issues = @($issues)
  slideMetrics = $slides
  generatedAt = (Get-Date).ToString("s")
}

if (-not $OutputPath) {
  $OutputPath = Join-Path ([System.IO.Path]::GetDirectoryName($candidateDir)) "reference-style-qa.json"
}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
$report
