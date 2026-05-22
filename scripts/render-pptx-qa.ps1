param(
  [Parameter(Mandatory=$true)]
  [string]$InputPptx,

  [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

function Resolve-OutputDir {
  param([string]$InputPptx, [string]$OutputDir)
  if ($OutputDir -and $OutputDir.Trim()) {
    return [System.IO.Path]::GetFullPath($OutputDir)
  }
  $base = [System.IO.Path]::GetFileNameWithoutExtension($InputPptx)
  return [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($InputPptx)), "$base-render-qa")
}

function Decode-XmlText {
  param([string]$Value)
  return [System.Net.WebUtility]::HtmlDecode($Value)
}

function Convert-EmuToInch {
  param([double]$Value)
  return $Value / 914400.0
}

function Get-PptxXmlQa {
  param([string]$PptxPath)

  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $zip = [System.IO.Compression.ZipFile]::OpenRead($PptxPath)
  try {
    $slideEntries = $zip.Entries |
      Where-Object { $_.FullName -match '^ppt/slides/slide\d+\.xml$' } |
      Sort-Object { [int]([regex]::Match($_.FullName, 'slide(\d+)\.xml').Groups[1].Value) }

    $fontSizes = New-Object System.Collections.Generic.List[double]
    $rawHyphenCount = 0
    $overflowRiskCount = 0
    $overlapRiskCount = 0
    $narrowTextRiskCount = 0

    foreach ($entry in $slideEntries) {
      $reader = New-Object System.IO.StreamReader($entry.Open())
      $xml = $reader.ReadToEnd()
      $reader.Close()

      foreach ($m in [regex]::Matches($xml, '\ssz="(\d+)"')) {
        $fontSizes.Add(([double]$m.Groups[1].Value) / 100.0)
      }
      $rawHyphenCount += [regex]::Matches($xml, '<a:t>\s*-\s+').Count

      $boxes = @()
      foreach ($shape in [regex]::Matches($xml, '<p:sp[\s\S]*?</p:sp>')) {
        $shapeXml = $shape.Value
        $textParts = @()
        foreach ($t in [regex]::Matches($shapeXml, '<a:t>([\s\S]*?)</a:t>')) {
          $textParts += Decode-XmlText $t.Groups[1].Value
        }
        $text = (($textParts -join ' ') -replace '\s+', ' ').Trim()
        if (-not $text) { continue }

        $x = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:off[^>]*\sx="(-?\d+)"')).Groups[1].Value))
        $y = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:off[^>]*\sy="(-?\d+)"')).Groups[1].Value))
        $w = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:ext[^>]*\scx="(\d+)"')).Groups[1].Value))
        $h = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:ext[^>]*\scy="(\d+)"')).Groups[1].Value))
        if ($w -le 0 -or $h -le 0) { continue }

        $sizes = @()
        foreach ($s in [regex]::Matches($shapeXml, '\ssz="(\d+)"')) { $sizes += ([double]$s.Groups[1].Value) / 100.0 }
        $fontSize = if ($sizes.Count) { ($sizes | Measure-Object -Maximum).Maximum } else { 12.0 }
        $fontFactor = [Math]::Max(0.75, 12.0 / [Math]::Max(8.0, $fontSize))
        $capacity = [Math]::Max(4, $w * 9.2 * $fontFactor) * [Math]::Max(1, $h * 3.65 * $fontFactor)
        if ($text.Length -gt $capacity * 1.35) { $overflowRiskCount++ }
        $singleWord = ($text -notmatch '\s') -and ($text.Length -le 10)
        $narrowCapacity = $w * [Math]::Max(10.0, $fontSize * 0.88)
        if ($singleWord -and $text.Length -gt $narrowCapacity) { $narrowTextRiskCount++ }

        $boxes += [pscustomobject]@{ X=$x; Y=$y; W=$w; H=$h; Text=$text }
      }

      for ($i = 0; $i -lt $boxes.Count; $i++) {
        for ($j = $i + 1; $j -lt $boxes.Count; $j++) {
          $a = $boxes[$i]; $b = $boxes[$j]
          $xOverlap = [Math]::Max(0, [Math]::Min($a.X + $a.W, $b.X + $b.W) - [Math]::Max($a.X, $b.X))
          $yOverlap = [Math]::Max(0, [Math]::Min($a.Y + $a.H, $b.Y + $b.H) - [Math]::Max($a.Y, $b.Y))
          $overlap = $xOverlap * $yOverlap
          $smaller = [Math]::Min($a.W * $a.H, $b.W * $b.H)
          if ($smaller -gt 0 -and ($overlap / $smaller) -gt 0.18) { $overlapRiskCount++ }
        }
      }
    }

    $belowMin = @($fontSizes | Where-Object { $_ -lt 11 }).Count
    $minFont = if ($fontSizes.Count) { ($fontSizes | Measure-Object -Minimum).Minimum } else { $null }
    $score = [Math]::Max(0, [Math]::Min(100, 100 - $belowMin * 7 - $rawHyphenCount * 8 - $overflowRiskCount * 8 - $overlapRiskCount * 10 - $narrowTextRiskCount * 4))
    $status = if ($belowMin -or $rawHyphenCount -or $overflowRiskCount -gt 2 -or $overlapRiskCount) { "fail" } elseif ($overflowRiskCount -or $narrowTextRiskCount) { "warn" } else { "pass" }

    return [pscustomobject]@{
      slideCount = @($slideEntries).Count
      minFontSize = $minFont
      belowMinFontCount = $belowMin
      rawHyphenCount = $rawHyphenCount
      overflowRiskCount = $overflowRiskCount
      overlapRiskCount = $overlapRiskCount
      narrowTextRiskCount = $narrowTextRiskCount
      score = $score
      status = $status
    }
  }
  finally {
    $zip.Dispose()
  }
}

function Export-PptxImages {
  param([string]$PptxPath, [string]$ImageDir)
  $powerPoint = $null
  $presentation = $null
  try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open($PptxPath, $true, $false, $false)
    New-Item -ItemType Directory -Force -Path $ImageDir | Out-Null
    foreach ($slide in $presentation.Slides) {
      $out = Join-Path $ImageDir ("slide-{0:D2}.png" -f $slide.SlideIndex)
      $slide.Export($out, "PNG", 1920, 1080) | Out-Null
    }
    return $true
  }
  catch {
    Write-Warning "PowerPoint PNG export failed: $($_.Exception.Message)"
    return $false
  }
  finally {
    if ($presentation) { $presentation.Close() | Out-Null }
    if ($powerPoint) { $powerPoint.Quit() | Out-Null }
  }
}

$pptxPath = [System.IO.Path]::GetFullPath($InputPptx)
if (-not (Test-Path -LiteralPath $pptxPath)) {
  throw "Input PPTX not found: $pptxPath"
}

$outDir = Resolve-OutputDir $pptxPath $OutputDir
$imageDir = Join-Path $outDir "slides"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$xmlQa = Get-PptxXmlQa $pptxPath
$rendered = Export-PptxImages $pptxPath $imageDir

$report = [pscustomobject]@{
  inputPptx = $pptxPath
  outputDir = $outDir
  imageDir = if ($rendered) { $imageDir } else { $null }
  imageRendered = $rendered
  qa = $xmlQa
  generatedAt = (Get-Date).ToString("s")
}

$reportPath = Join-Path $outDir "qa-report.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $reportPath -Encoding UTF8
$report
