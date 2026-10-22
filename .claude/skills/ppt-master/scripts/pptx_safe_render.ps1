# Export PPTX slides to PNG through PowerPoint without touching the user's work.
# The deck opens read-only and windowless; only that presentation is closed.
# PowerPoint is quit only when this script started it and nothing else is open,
# so decks the user has open (or opens during the render) stay open.
# -LinesOut also writes, per text frame, the authored line count (paragraphs
# plus a:br breaks) and the line count PowerPoint actually lays out.
# Exit codes: 0 ok, 3 PowerPoint unavailable, 4 render failed.
param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Pages = "",
    [int]$Width = 1600,
    [string]$LinesOut = ""
)

$ErrorActionPreference = "Stop"

function Measure-Frame($slide, $name, $frame, $rows, $cell = $false) {
    if (-not $frame.HasText) { return }
    $range = $frame.TextRange
    $text = [string]$range.Text
    if (-not $text.Trim()) { return }
    # PowerPoint reports paragraphs as CR and a:br line breaks as VT (char 11).
    $authored = ($text.TrimEnd([char]13, [char]11) -split "[`r`v]").Count
    $lines = @()
    $count = $range.Lines().Count
    for ($i = 1; $i -le $count; $i++) { $lines += [string]$range.Lines($i, 1).Text }
    $rows.Add([ordered]@{
        slide = $slide; shape = $name; cell = $cell; wrap = [bool]($frame.WordWrap -eq -1)
        authored = $authored; rendered = $count; lines = $lines
    }) | Out-Null
}

function Measure-Shape($slide, $shape, $rows) {
    if ($shape.Type -eq 6) {  # msoGroup
        foreach ($child in $shape.GroupItems) { Measure-Shape $slide $child $rows }
    } elseif ($shape.HasTable -eq -1) {
        $table = $shape.Table
        for ($r = 1; $r -le $table.Rows.Count; $r++) {
            for ($c = 1; $c -le $table.Columns.Count; $c++) {
                Measure-Frame $slide "$($shape.Name) r$r c$c" $table.Cell($r, $c).Shape.TextFrame $rows $true
            }
        }
    } elseif ($shape.HasTextFrame -eq -1) {
        Measure-Frame $slide $shape.Name $shape.TextFrame $rows
    }
}

$wasRunning = [bool](Get-Process -Name POWERPNT -ErrorAction SilentlyContinue)

try {
    $app = New-Object -ComObject PowerPoint.Application
} catch {
    [Console]::Error.WriteLine("PowerPoint unavailable: $($_.Exception.Message)")
    exit 3
}

$pres = $null
$code = 0
try {
    # Open(FileName, ReadOnly, Untitled, WithWindow): msoTrue = -1, msoFalse = 0
    $pres = $app.Presentations.Open($Pptx, -1, -1, 0)
    $count = $pres.Slides.Count
    $height = [int][Math]::Round($Width * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
    $wanted = if ($Pages) { $Pages -split "," | ForEach-Object { [int]$_ } } else { 1..$count }
    foreach ($k in $wanted) {
        if ($k -lt 1 -or $k -gt $count) { continue }
        $pres.Slides.Item($k).Export((Join-Path $OutDir "p$k.png"), "PNG", $Width, $height)
    }
    if ($LinesOut) {
        $rows = New-Object System.Collections.ArrayList
        foreach ($k in $wanted) {
            if ($k -lt 1 -or $k -gt $count) { continue }
            foreach ($shape in $pres.Slides.Item($k).Shapes) { Measure-Shape $k $shape $rows }
        }
        $json = ConvertTo-Json -InputObject @($rows) -Depth 4
        [IO.File]::WriteAllText($LinesOut, $json, (New-Object Text.UTF8Encoding $false))
    }
    Write-Output "slides=$count"
} catch {
    [Console]::Error.WriteLine("render failed: $($_.Exception.Message)")
    $code = 4
} finally {
    if ($pres) {
        try { $pres.Close() } catch {}
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($pres)
    }
    try {
        if (-not $wasRunning -and $app.Presentations.Count -eq 0) { $app.Quit() }
    } catch {}
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
exit $code
