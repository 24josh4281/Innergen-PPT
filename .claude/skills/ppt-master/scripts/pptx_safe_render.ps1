# Export PPTX slides to PNG through PowerPoint without touching the user's work.
# The deck opens read-only and windowless; only that presentation is closed.
# PowerPoint is quit only when this script started it and nothing else is open,
# so decks the user has open (or opens during the render) stay open.
# Exit codes: 0 ok, 3 PowerPoint unavailable, 4 render failed.
param(
    [Parameter(Mandatory = $true)][string]$Pptx,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Pages = "",
    [int]$Width = 1600
)

$ErrorActionPreference = "Stop"
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
