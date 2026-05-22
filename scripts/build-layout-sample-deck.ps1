param(
  [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
if (-not $OutputDir -or -not $OutputDir.Trim()) {
  $OutputDir = Join-Path $root "docs\generated\layout-samples"
}
$outDir = [System.IO.Path]::GetFullPath($OutputDir)
$tmpDir = Join-Path $root ".tmp-layout-samples"

if (Test-Path -LiteralPath $tmpDir) {
  Remove-Item -LiteralPath $tmpDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Push-Location $root
try {
  npx tsc --outDir $tmpDir --module ES2022 --target ES2022 --moduleResolution bundler --noEmit false --rootDir src | Out-Host

  Get-ChildItem -LiteralPath $tmpDir -Filter *.js | ForEach-Object {
    $text = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
    $modules = @("patterns", "types", "planner", "ppt", "qa", "templates", "pptxQa", "fileImport", "layoutKnowledge", "qualityPolicy", "oneShotQuality", "useCases")
    foreach ($name in $modules) {
      $text = $text.Replace("from `"./$name`"", "from `"./$name.js`"")
      $text = $text.Replace("from './$name'", "from './$name.js'")
    }
    Set-Content -LiteralPath $_.FullName -Value $text -Encoding UTF8
  }

  $runner = Join-Path $tmpDir "run-layout-samples.mjs"
  @'
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { getAllStructureSampleInput, getLayoutFamilySampleInput, planDeck } from "./planner.js";
import { buildPptxBlob } from "./ppt.js";
import { analyzePptxPackage } from "./pptxQa.js";

const outDir = process.argv[2];
await mkdir(outDir, { recursive: true });

const dateLabel = new Date().toISOString().slice(0, 10);
const decks = [
  {
    id: "layout-family-sample-book",
    input: getLayoutFamilySampleInput(),
    meta: {
      clientName: "INNerGEN",
      projectTitle: "Innergen Layout Rendering Sample Book",
      documentType: "Consulting Proposal",
      dateLabel,
      purpose: "Executive Report",
      audience: "Internal Reviewer",
      tone: "Premium Consulting"
    }
  },
  {
    id: "all-archetype-sample-book",
    input: getAllStructureSampleInput(),
    meta: {
      clientName: "INNerGEN",
      projectTitle: "Innergen All Archetype Sample Book",
      documentType: "Consulting Proposal",
      dateLabel,
      purpose: "Executive Report",
      audience: "Internal Reviewer",
      tone: "Premium Consulting"
    }
  }
];

const summaries = [];
for (const deck of decks) {
  const slides = planDeck(deck.input, deck.meta);
  const { blob } = await buildPptxBlob(deck.meta, slides);
  const qa = await analyzePptxPackage(blob);
  const bytes = Buffer.from(await blob.arrayBuffer());
  const pptxPath = join(outDir, `${deck.id}.pptx`);
  const qaPath = join(outDir, `${deck.id}.qa.json`);
  await writeFile(pptxPath, bytes);
  await writeFile(qaPath, JSON.stringify({ id: deck.id, slides: slides.length, bytes: bytes.length, qa }, null, 2), "utf8");
  summaries.push({ id: deck.id, slides: slides.length, bytes: bytes.length, pptxPath, qaPath, qa });
}

const summaryPath = join(outDir, "sample-generation-summary.json");
await writeFile(summaryPath, JSON.stringify({ generatedAt: new Date().toISOString(), summaries }, null, 2), "utf8");
console.log(JSON.stringify({ outDir, summaryPath, summaries }, null, 2));
'@ | Set-Content -LiteralPath $runner -Encoding UTF8

  node $runner $outDir
}
finally {
  Pop-Location
  if (Test-Path -LiteralPath $tmpDir) {
    Remove-Item -LiteralPath $tmpDir -Recurse -Force
  }
}
