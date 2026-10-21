$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$source=Join-Path $root 'exports/20261021_innergen_report_examples_v31_ver6.pptx'
$review=Join-Path $root 'analysis/office-proof/report_equation_edit_review_v6.pptx'
$proof=Join-Path $root 'analysis/office-proof'
$before=(Get-FileHash -LiteralPath $source).Hash
if(Test-Path -LiteralPath $review){throw 'Review copy already exists'}
Copy-Item -LiteralPath $source -Destination $review
function MathShapes($items){foreach($shape in $items){if($shape.Type -eq 6){MathShapes $shape.GroupItems}elseif($shape.HasTextFrame){try{$zones=$shape.TextFrame2.TextRange.MathZones();if($zones.Length -gt 0){$shape}}catch{}}}}
$app=New-Object -ComObject PowerPoint.Application
$deck=$null
$result=@{sourceHashBefore=$before}
try{
  $deck=$app.Presentations.Open($review,0,0,0)
  $shapes=@(MathShapes $deck.Slides.Item(3).Shapes)
  $result.mathShapesBefore=$shapes.Count
  if($shapes.Count -lt 6){throw 'Native MathZones not recognized'}
  $target=$shapes | Where-Object {$_.Name -eq 'Equation reduction'} | Select-Object -First 1
  if($null -eq $target){throw 'Reduction equation missing'}
  $zone=$target.TextFrame2.TextRange.MathZones(1,1)
  $result.textBefore=$zone.Text
  $zone.Characters(1,1).Text='Q'
  $result.textEdited=$target.TextFrame2.TextRange.MathZones(1,1).Text
  $deck.Save();$deck.Close();$deck=$null
  $deck=$app.Presentations.Open($review,-1,0,0)
  $shapes=@(MathShapes $deck.Slides.Item(3).Shapes)
  $result.mathShapesReopened=$shapes.Count
  $target=$shapes | Where-Object {$_.Name -eq 'Equation reduction'} | Select-Object -First 1
  $result.textReopened=$target.TextFrame2.TextRange.MathZones(1,1).Text
  $deck.Close();$deck=$null
  $deck=$app.Presentations.Open($source,-1,0,0)
  for($i=1;$i -le 3;$i++){$deck.Slides.Item($i).Export((Join-Path $proof "slide-$i-v6.png"),'PNG',1560,1080)}
  $deck.Close();$deck=$null
  $result.sourceHashAfter=(Get-FileHash -LiteralPath $source).Hash
  $result.sourceUnchanged=($result.sourceHashAfter -eq $before)
  $result.editPersisted=($result.textEdited -eq $result.textReopened)
  $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $proof 'ppt-edit-proof-v6.json') -Encoding utf8
  $result | ConvertTo-Json -Depth 6
}finally{if($null -ne $deck){$deck.Close()}}
