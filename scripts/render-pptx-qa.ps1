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

function Get-MeaningfulTextLength {
  param([string]$Text)
  $clean = (($Text -replace '\s+', ' ').Trim())
  $sum = 0.0
  foreach ($ch in $clean.ToCharArray()) {
    if ($ch -match '[A-Za-z0-9]') { $sum += 0.65 } else { $sum += 1.0 }
  }
  return $sum
}

function Get-StructureUnitCount {
  param([string]$Text)
  $count = 1
  $count += @($Text -split "(`r`n|`n|`r)" | Where-Object { (Get-MeaningfulTextLength $_) -ge 2 }).Count - 1
  foreach ($marker in @([char]0x2022, [char]0x2460, [char]0x2461, [char]0x2462, [char]0x2463, [char]0x2464, [char]0x2465)) {
    $count += @($Text.ToCharArray() | Where-Object { $_ -eq $marker }).Count
  }
  return [Math]::Max(1, $count)
}

function Get-OverlapRatio {
  param($A, $B)
  $xOverlap = [Math]::Max(0, [Math]::Min($A.X + $A.W, $B.X + $B.W) - [Math]::Max($A.X, $B.X))
  $yOverlap = [Math]::Max(0, [Math]::Min($A.Y + $A.H, $B.Y + $B.H) - [Math]::Max($A.Y, $B.Y))
  $overlap = $xOverlap * $yOverlap
  $smaller = [Math]::Min($A.W * $A.H, $B.W * $B.H)
  if ($smaller -le 0) { return 0 }
  return $overlap / $smaller
}

function Test-LargeBodyContainer {
  param($Box)
  $area = $Box.W * $Box.H
  return ($Box.Y -gt 1.05 -and $Box.Y -lt 6.85 -and $Box.W -ge 2.25 -and $Box.H -ge 1.3 -and $area -ge 3.5 -and $Box.W -le 12.4 -and $Box.H -le 5.65)
}

function Test-InsideOrContained {
  param($Container, $Item)
  $centerX = $Item.X + $Item.W / 2.0
  $centerY = $Item.Y + $Item.H / 2.0
  $centerInside = ($centerX -ge $Container.X -and $centerX -le ($Container.X + $Container.W) -and $centerY -ge $Container.Y -and $centerY -le ($Container.Y + $Container.H))
  return $centerInside -or ((Get-OverlapRatio $Container $Item) -gt 0.55)
}

function Count-SparseContainers {
  param($Boxes)
  $count = 0
  $meaningfulBoxes = @($Boxes | Where-Object { $_.Text -and $_.Y -gt 1.0 -and $_.Y -lt 6.9 })

  foreach ($container in $Boxes) {
    if (-not (Test-LargeBodyContainer $container)) { continue }

    $contents = @()
    if ($container.Text -and (Get-MeaningfulTextLength $container.Text) -ge 2) { $contents += $container }
    foreach ($box in $meaningfulBoxes) {
      if ([object]::ReferenceEquals($box, $container)) { continue }
      if (Test-InsideOrContained $container $box) {
        if ((Get-MeaningfulTextLength $box.Text) -ge 2) { $contents += $box }
      }
    }
    if (-not $contents.Count) { continue }
    if ($contents.Count -eq 1 -and [object]::ReferenceEquals($contents[0], $container)) { continue }

    $area = $container.W * $container.H
    $totalTextWeight = 0.0
    $structureUnitCount = 0
    foreach ($box in $contents) {
      $totalTextWeight += Get-MeaningfulTextLength $box.Text
      $structureUnitCount += Get-StructureUnitCount $box.Text
    }
    $densityScore = $totalTextWeight + $structureUnitCount * 12.0
    if ($contents.Count -ge 3 -or ($structureUnitCount -ge 4 -and $densityScore -ge $area * 5.2)) {
      continue
    }
    if ($densityScore -lt $area * 7.5 -or ($area -ge 6.2 -and $structureUnitCount -lt 3 -and $totalTextWeight -lt $area * 10.0)) {
      $count++
    }
  }

  return $count
}

function Get-SparseContainerIssues {
  param($Boxes)
  $issues = @()
  $meaningfulBoxes = @($Boxes | Where-Object { $_.Text -and $_.Y -gt 1.0 -and $_.Y -lt 6.9 })

  foreach ($container in $Boxes) {
    if (-not (Test-LargeBodyContainer $container)) { continue }

    $contents = @()
    if ($container.Text -and (Get-MeaningfulTextLength $container.Text) -ge 2) { $contents += $container }
    foreach ($box in $meaningfulBoxes) {
      if ([object]::ReferenceEquals($box, $container)) { continue }
      if (Test-InsideOrContained $container $box) {
        if ((Get-MeaningfulTextLength $box.Text) -ge 2) { $contents += $box }
      }
    }
    if (-not $contents.Count) { continue }
    if ($contents.Count -eq 1 -and [object]::ReferenceEquals($contents[0], $container)) { continue }

    $area = $container.W * $container.H
    $totalTextWeight = 0.0
    $structureUnitCount = 0
    foreach ($box in $contents) {
      $totalTextWeight += Get-MeaningfulTextLength $box.Text
      $structureUnitCount += Get-StructureUnitCount $box.Text
    }
    $densityScore = $totalTextWeight + $structureUnitCount * 12.0
    if ($contents.Count -ge 3 -or ($structureUnitCount -ge 4 -and $densityScore -ge $area * 5.2)) {
      continue
    }
    if ($densityScore -lt $area * 7.5 -or ($area -ge 6.2 -and $structureUnitCount -lt 3 -and $totalTextWeight -lt $area * 10.0)) {
      $issues += New-QaIssue -Type "sparse-container" -Severity "fail" -Slide $container.Slide -Box $container -Reason "Large container has too little structured text for its visual size." -Remediation "Add judgment/evidence/implication/status rows, or shrink the container."
    }
  }

  return $issues
}

function Count-TableWhitespaceRisks {
  param([string]$Xml)
  $count = 0
  foreach ($frame in [regex]::Matches($Xml, '<p:graphicFrame[\s\S]*?</p:graphicFrame>')) {
    $frameXml = $frame.Value
    if (-not $frameXml.Contains('<a:tbl')) { continue }
    $rows = @([regex]::Matches($frameXml, '<a:tr[^>]*\sh="(\d+)"[\s\S]*?</a:tr>'))
    if ($rows.Count -le 1) { continue }
    for ($ri = 1; $ri -lt $rows.Count; $ri++) {
      $rowXml = $rows[$ri].Value
      $rowH = Convert-EmuToInch ([double]$rows[$ri].Groups[1].Value)
      $parts = @()
      foreach ($t in [regex]::Matches($rowXml, '<a:t>([\s\S]*?)</a:t>')) {
        $parts += Decode-XmlText $t.Groups[1].Value
      }
      $textWeight = Get-MeaningfulTextLength (($parts -join ' ') -replace '\s+', ' ')
      $sizes = @()
      foreach ($s in [regex]::Matches($rowXml, '\ssz="(\d+)"')) {
        $sizes += ([double]$s.Groups[1].Value) / 100.0
      }
      $maxFont = if ($sizes.Count) { ($sizes | Measure-Object -Maximum).Maximum } else { 12.0 }
      if ($rowH -ge 1.03 -and $maxFont -lt 12.3 -and ($textWeight / [Math]::Max(0.1, $rowH)) -lt 96.0) {
        $count++
      }
    }
  }
  return $count
}

function Get-GraphicFrameBox {
  param([string]$FrameXml, [int]$Slide, [int]$Index)
  $off = [regex]::Match($FrameXml, '<a:off[^>]*\sx="(-?\d+)"[^>]*\sy="(-?\d+)"')
  $ext = [regex]::Match($FrameXml, '<a:ext[^>]*\scx="(\d+)"[^>]*\scy="(\d+)"')
  $nameMatch = [regex]::Match($FrameXml, '<p:cNvPr[^>]*\sname="([^"]+)"')
  $idMatch = [regex]::Match($FrameXml, '<p:cNvPr[^>]*\sid="([^"]+)"')
  return ([pscustomobject]@{
    Slide = $Slide
    ObjectId = $(if ($idMatch.Success) { $idMatch.Groups[1].Value } else { $null })
    ObjectName = $(if ($nameMatch.Success) { Decode-XmlText $nameMatch.Groups[1].Value } else { "Table $Index" })
    X = $(if ($off.Success) { Convert-EmuToInch ([double]$off.Groups[1].Value) } else { 0.0 })
    Y = $(if ($off.Success) { Convert-EmuToInch ([double]$off.Groups[2].Value) } else { 0.0 })
    W = $(if ($ext.Success) { Convert-EmuToInch ([double]$ext.Groups[1].Value) } else { 0.0 })
    H = $(if ($ext.Success) { Convert-EmuToInch ([double]$ext.Groups[2].Value) } else { 0.0 })
    Text = ""
    FontSize = 12.0
  })
}

function Get-TableWhitespaceIssues {
  param([string]$Xml, [int]$Slide)
  $issues = @()
  $frameIndex = 0
  foreach ($frame in [regex]::Matches($Xml, '<p:graphicFrame[\s\S]*?</p:graphicFrame>')) {
    $frameIndex++
    $frameXml = $frame.Value
    if (-not $frameXml.Contains('<a:tbl')) { continue }
    $frameBox = Get-GraphicFrameBox $frameXml $Slide $frameIndex
    $rows = @([regex]::Matches($frameXml, '<a:tr[^>]*\sh="(\d+)"[\s\S]*?</a:tr>'))
    if ($rows.Count -le 1) { continue }
    for ($ri = 1; $ri -lt $rows.Count; $ri++) {
      $rowXml = $rows[$ri].Value
      $rowH = Convert-EmuToInch ([double]$rows[$ri].Groups[1].Value)
      $parts = @()
      foreach ($t in [regex]::Matches($rowXml, '<a:t>([\s\S]*?)</a:t>')) {
        $parts += Decode-XmlText $t.Groups[1].Value
      }
      $rowText = (($parts -join ' ') -replace '\s+', ' ').Trim()
      $textWeight = Get-MeaningfulTextLength $rowText
      $sizes = @()
      foreach ($s in [regex]::Matches($rowXml, '\ssz="(\d+)"')) {
        $sizes += ([double]$s.Groups[1].Value) / 100.0
      }
      $maxFont = if ($sizes.Count) { ($sizes | Measure-Object -Maximum).Maximum } else { 12.0 }
      if ($rowH -ge 1.03 -and $maxFont -lt 12.3 -and ($textWeight / [Math]::Max(0.1, $rowH)) -lt 96.0) {
        $issue = New-QaIssue -Type "table-whitespace" -Severity "fail" -Slide $Slide -Box $frameBox -Reason "Table row height is large compared with body font size and text density." -Remediation "Reduce row height, increase body font to 12-14pt, or add judgment/evidence/implication content."
        $issue.textPreview = Get-TextPreview $rowText
        $issue | Add-Member -NotePropertyName rowIndex -NotePropertyValue ($ri + 1)
        $issue | Add-Member -NotePropertyName rowHeight -NotePropertyValue ([Math]::Round($rowH, 3))
        $issue | Add-Member -NotePropertyName maxFontSize -NotePropertyValue ([Math]::Round($maxFont, 2))
        $issues += $issue
      }
    }
  }
  return $issues
}

function Test-NumberLikeLabel {
  param([string]$Text)
  return $Text.Trim() -match '^(0?[1-9]|[1-9][0-9]|L\d{1,2}|STEP\s*\d{1,2})$'
}

function Get-CenterY {
  param($Box)
  return $Box.Y + $Box.H / 2.0
}

function Test-CenterInside {
  param($Container, $Item)
  $centerX = $Item.X + $Item.W / 2.0
  $centerY = $Item.Y + $Item.H / 2.0
  return ($centerX -ge $Container.X -and $centerX -le ($Container.X + $Container.W) -and $centerY -ge $Container.Y -and $centerY -le ($Container.Y + $Container.H))
}

function Get-TextPreview {
  param([string]$Text)
  $clean = (($Text -replace '\s+', ' ').Trim())
  if ($clean.Length -gt 80) { return $clean.Substring(0, 80) }
  return $clean
}

function New-QaIssue {
  param(
    [string]$Type,
    [string]$Severity,
    [int]$Slide,
    $Box,
    [string]$Reason,
    [string]$Remediation,
    $Related = $null
  )
  $objectId = $null
  $objectName = $null
  $relatedObjectId = $null
  $relatedObjectName = $null
  if ($Box -and ($Box.PSObject.Properties.Name -contains "ObjectId")) { $objectId = $Box.ObjectId }
  if ($Box -and ($Box.PSObject.Properties.Name -contains "ObjectName")) { $objectName = $Box.ObjectName }
  if ($Related -and ($Related.PSObject.Properties.Name -contains "ObjectId")) { $relatedObjectId = $Related.ObjectId }
  if ($Related -and ($Related.PSObject.Properties.Name -contains "ObjectName")) { $relatedObjectName = $Related.ObjectName }

  [pscustomobject]@{
    type = $Type
    severity = $Severity
    slide = $Slide
    objectId = $objectId
    objectName = $objectName
    x = $(if ($Box) { [Math]::Round($Box.X, 3) } else { $null })
    y = $(if ($Box) { [Math]::Round($Box.Y, 3) } else { $null })
    w = $(if ($Box) { [Math]::Round($Box.W, 3) } else { $null })
    h = $(if ($Box) { [Math]::Round($Box.H, 3) } else { $null })
    relatedObjectId = $relatedObjectId
    relatedObjectName = $relatedObjectName
    relatedX = $(if ($Related) { [Math]::Round($Related.X, 3) } else { $null })
    relatedY = $(if ($Related) { [Math]::Round($Related.Y, 3) } else { $null })
    relatedW = $(if ($Related) { [Math]::Round($Related.W, 3) } else { $null })
    relatedH = $(if ($Related) { [Math]::Round($Related.H, 3) } else { $null })
    textPreview = $(if ($Box -and $Related) { "$(Get-TextPreview $Box.Text) | $(Get-TextPreview $Related.Text)" } elseif ($Box) { Get-TextPreview $Box.Text } else { $null })
    reason = $Reason
    remediation = $Remediation
  }
}

function Get-NumberedRowAlignmentIssues {
  param($Boxes)
  $issues = @()
  $textBoxes = @($Boxes | Where-Object { $_.Text -and $_.Y -gt 1.0 -and $_.Y -lt 6.9 })
  $numberedBoxes = @($textBoxes | Where-Object { Test-NumberLikeLabel $_.Text })

  foreach ($numberBox in $numberedBoxes) {
    $bodyCandidates = @($textBoxes |
      Where-Object { -not [object]::ReferenceEquals($_, $numberBox) } |
      Where-Object { -not (Test-NumberLikeLabel $_.Text) } |
      Where-Object { $_.X -gt ($numberBox.X + $numberBox.W) -and ($_.X - ($numberBox.X + $numberBox.W)) -lt 0.95 } |
      Where-Object { [Math]::Abs((Get-CenterY $_) - (Get-CenterY $numberBox)) -lt 0.42 } |
      Sort-Object @{ Expression = { $_.X } }, @{ Expression = { [Math]::Abs((Get-CenterY $_) - (Get-CenterY $numberBox)) } })
    if (-not $bodyCandidates.Count) { continue }
    $bodyBox = $bodyCandidates[0]

    $baselineMismatch = [Math]::Abs((Get-CenterY $numberBox) - (Get-CenterY $bodyBox)) -gt 0.12
    $numberTooShallow = $numberBox.H -lt 0.22
    $bodyLikelyWraps = (Get-MeaningfulTextLength $bodyBox.Text) -gt [Math]::Max(10.0, $bodyBox.W * 10.5)
    $bodyTooShallowForWrap = $bodyLikelyWraps -and $bodyBox.H -lt 0.34
    if ($baselineMismatch -or $numberTooShallow -or $bodyTooShallowForWrap) {
      $issues += New-QaIssue -Type "alignment" -Severity "fail" -Slide $numberBox.Slide -Box $numberBox -Reason "Number label and body text baseline are not aligned." -Remediation "Use the same rowY/rowH for number and body text, then apply vertical middle alignment." -Related $bodyBox
    }
  }

  return $issues
}

function Get-ChipLabelAlignmentIssues {
  param($Boxes)
  $issues = @()
  $textBoxes = @($Boxes | Where-Object { $_.Text })
  $containers = @($Boxes | Where-Object { -not $_.Text -and $_.Y -gt 0.72 -and $_.Y -lt 6.95 -and $_.W -ge 0.45 -and $_.W -le 3.5 -and $_.H -ge 0.28 -and $_.H -le 0.85 })

  foreach ($container in $containers) {
    $contained = @($textBoxes | Where-Object { Test-CenterInside $container $_ })
    if ($contained.Count -ne 1) { continue }
    $textBox = $contained[0]
    $centerMismatch = [Math]::Abs((Get-CenterY $container) - (Get-CenterY $textBox)) -gt 0.09
    $textBoxTooShallow = $textBox.H -lt [Math]::Min(0.18, $container.H * 0.45)
    if ($centerMismatch -or $textBoxTooShallow) {
      $issues += New-QaIssue -Type "alignment" -Severity "fail" -Slide $container.Slide -Box $container -Reason "Chip, label, or badge text is not vertically centered in its container." -Remediation "Set the text box to the same y/h as the container and use vertical middle alignment." -Related $textBox
    }
  }

  return $issues
}

function Get-AlignmentIssues {
  param($Boxes)
  $items = @()
  $items += @(Get-NumberedRowAlignmentIssues -Boxes $Boxes)
  $items += @(Get-ChipLabelAlignmentIssues -Boxes $Boxes)
  return $items
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
    $ellipsisCount = 0
    $ellipsisMarker = [string][char]0x2026
    $overflowRiskCount = 0
    $overlapRiskCount = 0
    $narrowTextRiskCount = 0
    $sparseContainerCount = 0
    $tableWhitespaceRiskCount = 0
    $alignmentRiskCount = 0
    $issues = @()

    foreach ($entry in $slideEntries) {
      $slideNo = [int]([regex]::Match($entry.FullName, 'slide(\d+)\.xml').Groups[1].Value)
      $reader = New-Object System.IO.StreamReader($entry.Open())
      $xml = $reader.ReadToEnd()
      $reader.Close()

      foreach ($m in [regex]::Matches($xml, '\ssz="(\d+)"')) {
        $fontSizes.Add(([double]$m.Groups[1].Value) / 100.0)
      }
      $rawHyphenCount += [regex]::Matches($xml, '<a:t>\s*-\s+').Count
      foreach ($t in [regex]::Matches($xml, '<a:t>([\s\S]*?)</a:t>')) {
        $textMarker = Decode-XmlText $t.Groups[1].Value
        if ($textMarker.Contains($ellipsisMarker) -or $textMarker.Contains("...")) { $ellipsisCount++ }
      }
      $tableIssues = @(Get-TableWhitespaceIssues $xml $slideNo)
      $tableWhitespaceRiskCount += $tableIssues.Count
      $issues += $tableIssues

      $shapeBoxes = @()
      $boxes = @()
      foreach ($shape in [regex]::Matches($xml, '<p:sp[\s\S]*?</p:sp>')) {
        $shapeXml = $shape.Value
        $textParts = @()
        foreach ($t in [regex]::Matches($shapeXml, '<a:t>([\s\S]*?)</a:t>')) {
          $textParts += Decode-XmlText $t.Groups[1].Value
        }
        $text = (($textParts -join ' ') -replace '\s+', ' ').Trim()

        $x = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:off[^>]*\sx="(-?\d+)"')).Groups[1].Value))
        $y = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:off[^>]*\sy="(-?\d+)"')).Groups[1].Value))
        $w = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:ext[^>]*\scx="(\d+)"')).Groups[1].Value))
        $h = Convert-EmuToInch ([double](([regex]::Match($shapeXml, '<a:ext[^>]*\scy="(\d+)"')).Groups[1].Value))
        if ($w -le 0 -or $h -le 0) { continue }

        $sizes = @()
        foreach ($s in [regex]::Matches($shapeXml, '\ssz="(\d+)"')) { $sizes += ([double]$s.Groups[1].Value) / 100.0 }
        $fontSize = if ($sizes.Count) { ($sizes | Measure-Object -Maximum).Maximum } else { 12.0 }
        $nameMatch = [regex]::Match($shapeXml, '<p:cNvPr[^>]*\sname="([^"]+)"')
        $idMatch = [regex]::Match($shapeXml, '<p:cNvPr[^>]*\sid="([^"]+)"')
        $shapeBox = [pscustomobject]@{
          Slide=$slideNo
          ObjectId=$(if ($idMatch.Success) { $idMatch.Groups[1].Value } else { $null })
          ObjectName=$(if ($nameMatch.Success) { Decode-XmlText $nameMatch.Groups[1].Value } else { $null })
          X=$x
          Y=$y
          W=$w
          H=$h
          Text=$text
          FontSize=$fontSize
        }
        $shapeBoxes += $shapeBox
        if (-not $text) { continue }

        $fontFactor = [Math]::Max(0.75, 12.0 / [Math]::Max(8.0, $fontSize))
        $capacity = [Math]::Max(4, $w * 9.2 * $fontFactor) * [Math]::Max(1, $h * 3.65 * $fontFactor)
        if ($text.Length -gt $capacity * 1.35) {
          $overflowRiskCount++
          $issues += New-QaIssue -Type "overflow" -Severity "fail" -Slide $slideNo -Box $shapeBox -Reason "Text is likely to overflow the object." -Remediation "Split into bullets, widen the object, or move detail into a supporting row."
        }
        $singleWord = ($text -notmatch '\s') -and ($text.Length -le 10)
        $narrowCapacity = $w * [Math]::Max(10.0, $fontSize * 0.88)
        if ($singleWord -and $text.Length -gt $narrowCapacity) {
          $narrowTextRiskCount++
          $issues += New-QaIssue -Type "narrow-text" -Severity "warn" -Slide $slideNo -Box $shapeBox -Reason "A short Korean/label word is in a box that is too narrow." -Remediation "Keep one-word labels on one line by widening the box or lowering label density."
        }

        $boxes += $shapeBox
      }

      $sparseIssues = @(Get-SparseContainerIssues -Boxes $shapeBoxes)
      $alignmentIssues = @(Get-AlignmentIssues -Boxes $shapeBoxes)
      $sparseContainerCount += $sparseIssues.Count
      $alignmentRiskCount += $alignmentIssues.Count
      $issues += $sparseIssues + $alignmentIssues

      for ($i = 0; $i -lt $boxes.Count; $i++) {
        for ($j = $i + 1; $j -lt $boxes.Count; $j++) {
          $a = $boxes[$i]; $b = $boxes[$j]
          if ((Get-OverlapRatio $a $b) -gt 0.18) {
            $overlapRiskCount++
            $issues += New-QaIssue -Type "overlap" -Severity "fail" -Slide $slideNo -Box $a -Reason "Two text-bearing objects overlap visually." -Remediation "Move one object to a separate row/column, reduce container width, or send decorative connectors behind text." -Related $b
          }
        }
      }
    }

    $belowMin = @($fontSizes | Where-Object { $_ -lt 11 }).Count
    $minFont = if ($fontSizes.Count) { ($fontSizes | Measure-Object -Minimum).Minimum } else { $null }
    $score = [Math]::Max(0, [Math]::Min(100, 100 - $belowMin * 7 - $rawHyphenCount * 8 - $ellipsisCount * 6 - $overflowRiskCount * 8 - $overlapRiskCount * 10 - $narrowTextRiskCount * 4 - $sparseContainerCount * 8 - $tableWhitespaceRiskCount * 8 - $alignmentRiskCount * 9))
    $status = if ($belowMin -or $rawHyphenCount -or $ellipsisCount -or $overflowRiskCount -gt 2 -or $overlapRiskCount -or $sparseContainerCount -or $tableWhitespaceRiskCount -or $alignmentRiskCount) { "fail" } elseif ($overflowRiskCount -or $narrowTextRiskCount) { "warn" } else { "pass" }

    return [pscustomobject]@{
      slideCount = @($slideEntries).Count
      minFontSize = $minFont
      belowMinFontCount = $belowMin
      rawHyphenCount = $rawHyphenCount
      ellipsisCount = $ellipsisCount
      overflowRiskCount = $overflowRiskCount
      overlapRiskCount = $overlapRiskCount
      narrowTextRiskCount = $narrowTextRiskCount
      sparseContainerCount = $sparseContainerCount
      tableWhitespaceRiskCount = $tableWhitespaceRiskCount
      alignmentRiskCount = $alignmentRiskCount
      score = $score
      status = $status
      issues = @($issues)
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
