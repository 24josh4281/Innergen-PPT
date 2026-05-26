param(
  [Parameter(Mandatory = $true)]
  [string]$InputPdf,

  [string]$OutputDir = "",
  [string]$ClientName = "INNerGEN",
  [string]$ProjectTitle = "",
  [string]$DocumentType = "Kickoff Report",
  [string]$Purpose = "Kickoff Report",
  [string]$Audience = "Client stakeholders",
  [string]$Tone = "Professional consulting"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pdfPath = [System.IO.Path]::GetFullPath($InputPdf)
if (-not (Test-Path -LiteralPath $pdfPath)) {
  throw "Input PDF not found: $pdfPath"
}

if (-not $OutputDir -or -not $OutputDir.Trim()) {
  $OutputDir = Join-Path $root "docs\generated\pdf-runs"
}
$outDir = [System.IO.Path]::GetFullPath($OutputDir)
$tmpDir = Join-Path $root ".tmp-pdf-run"

if (-not $ProjectTitle -or -not $ProjectTitle.Trim()) {
  $ProjectTitle = [System.IO.Path]::GetFileNameWithoutExtension($pdfPath)
}

if (Test-Path -LiteralPath $tmpDir) {
  Remove-Item -LiteralPath $tmpDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Push-Location $root
try {
  npx tsc --outDir $tmpDir --module ES2022 --target ES2022 --moduleResolution bundler --noEmit false --rootDir src | Out-Host

  Get-ChildItem -LiteralPath $tmpDir -Filter *.js | ForEach-Object {
    $text = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
    $modules = @(
      "patterns",
      "types",
      "planner",
      "ppt",
      "qa",
      "templates",
      "pptxQa",
      "fileImport",
      "layoutKnowledge",
      "qualityPolicy",
      "oneShotQuality",
      "useCases",
      "promptGenerator",
      "iterativePptxQa"
    )
    foreach ($name in $modules) {
      $text = $text.Replace("from `"./$name`"", "from `"./$name.js`"")
      $text = $text.Replace("from './$name'", "from './$name.js'")
    }
    Set-Content -LiteralPath $_.FullName -Value $text -Encoding UTF8
  }

  $runner = Join-Path $tmpDir "run-pdf-deck.mjs"
  @'
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { basename, join } from "node:path";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import { planDeck } from "./planner.js";
import { buildPptxWithIterativeQa } from "./iterativePptxQa.js";

const [pdfPath, outDir, clientName, projectTitle, documentType, purpose, audience, tone] = process.argv.slice(2);
await mkdir(outDir, { recursive: true });

const bytes = await readFile(pdfPath);
const doc = await pdfjsLib.getDocument({ data: new Uint8Array(bytes), disableWorker: true }).promise;
const maxPages = Math.min(doc.numPages, 50);
const pageBlocks = [];
const extractedPages = [];

for (let pageNo = 1; pageNo <= maxPages; pageNo += 1) {
  const page = await doc.getPage(pageNo);
  const content = await page.getTextContent();
  const rawItems = content.items.map((item) => ("str" in item ? item.str : "")).filter(Boolean);
  const items = compactTexts(rawItems, false);
  const text = sanitizePdfText(items.join(" ").replace(/\s+/g, " ").trim(), pageNo);
  if (!text) continue;

    const title = firstSentence(text, `Source page ${pageNo}`);
  const bullets = sentenceChunks(text)
    .filter((item) => item !== title)
    .slice(0, 7)
    .map((item) => `- ${item}`);

  pageBlocks.push([`Slide ${pageNo}: ${title}`, ...bullets].join("\n"));
  extractedPages.push({ pageNo, title, textLength: [...text].length, bulletCount: bullets.length });
}

const input = pageBlocks.join("\n\n---\n");
const now = new Date();
const dateLabel = `${now.getFullYear()}. ${String(now.getMonth() + 1).padStart(2, "0")}. ${String(now.getDate()).padStart(2, "0")}`;
const meta = { clientName, projectTitle, documentType, dateLabel, purpose, audience, tone };
const slides = planDeck(input, meta);
const qaResult = await buildPptxWithIterativeQa(meta, slides, 3);

const baseName = safeFileName(`${clientName}_${projectTitle}_innergen`);
const pptxPath = join(outDir, `${baseName}.pptx`);
const qaPath = join(outDir, `${baseName}.qa.json`);
const textPath = join(outDir, `${baseName}.extracted.txt`);
const storyboardPath = join(outDir, `${baseName}.storyboard.json`);

await writeFile(pptxPath, Buffer.from(await qaResult.blob.arrayBuffer()));
await writeFile(textPath, input, "utf8");
await writeFile(storyboardPath, JSON.stringify({ meta, source: basename(pdfPath), extractedPages, slides: qaResult.slides }, null, 2), "utf8");
await writeFile(qaPath, JSON.stringify({
  sourcePdf: pdfPath,
  pptxPath,
  textPath,
  storyboardPath,
  meta,
  sourcePages: doc.numPages,
  importedPages: maxPages,
  plannedSlides: slides.length,
  finalSlides: qaResult.slides.length,
  qa: qaResult.qa,
  attempts: qaResult.attempts
}, null, 2), "utf8");

console.log(JSON.stringify({
  pptxPath,
  qaPath,
  textPath,
  storyboardPath,
  sourcePages: doc.numPages,
  importedPages: maxPages,
  plannedSlides: slides.length,
  finalSlides: qaResult.slides.length,
  qa: qaResult.qa,
  attempts: qaResult.attempts.map((attempt) => ({
    pass: attempt.pass,
    action: attempt.action,
    score: attempt.qa.score,
    status: attempt.qa.status,
    overflowRiskCount: attempt.qa.overflowRiskCount,
    overlapRiskCount: attempt.qa.overlapRiskCount,
    narrowTextRiskCount: attempt.qa.narrowTextRiskCount
  }))
}, null, 2));

function sentenceChunks(text) {
  return text
    .split(/(?<=[.!?])\s+|\s{2,}/)
    .map((item) => item.trim())
    .filter((item) => item.length >= 8);
}

function firstSentence(text, fallback) {
  const first = sentenceChunks(text)[0] ?? text.slice(0, 42);
  return first.length > 64 ? `${first.slice(0, 63)}...` : first || fallback;
}

function compactTexts(values, dedupe = true) {
  const seen = new Set();
  return values
    .map((value) => value.replace(/\s+/g, " ").trim())
    .filter((value) => value.length > 1)
    .filter((value) => {
      if (!dedupe) return true;
      if (seen.has(value)) return false;
      seen.add(value);
      return true;
    });
}

function safeFileName(name) {
  return name.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_").slice(0, 130);
}

function sanitizePdfText(text, pageNo) {
  let cleaned = text
    .replace(/Innovative Ideas Better Solution Copyright .*?All rights reserved\.?/gi, " ")
    .replace(/Innovative Ideas Better Solution/gi, " ")
    .replace(/Copyright ©? 20\d{2} INNerGEN Co Ltd\.?/gi, " ")
    .replace(/All rights reserved\.?/gi, " ")
    .replace(/\bContents\b\s*(?:I\.|II\.|III\.|IV\.)?/gi, " ")
    .replace(/\bonsulting\s+lient\b/gi, " ")
    .replace(/\bConsulting\s+Client\b/gi, " ")
    .replace(/\s+/g, " ")
    .trim();

  if (pageNo <= 2 && cleaned.length < 80) return "";
  if (/^(?:I\.|II\.|III\.|IV\.)\s+/i.test(cleaned) && cleaned.length < 120) return "";
  return cleaned;
}
'@ | Set-Content -LiteralPath $runner -Encoding UTF8

  node $runner $pdfPath $outDir $ClientName $ProjectTitle $DocumentType $Purpose $Audience $Tone
}
finally {
  Pop-Location
  if (Test-Path -LiteralPath $tmpDir) {
    Remove-Item -LiteralPath $tmpDir -Recurse -Force
  }
}
