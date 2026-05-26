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
  extractedPages.push({ pageNo, title, text, textLength: [...text].length, bulletCount: bullets.length });
}

const input = buildConsultingDeckInput(extractedPages) || pageBlocks.join("\n\n---\n");
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

function buildConsultingDeckInput(pages) {
  if (!pages.length) return "";
  const topics = [
    {
      title: "Kickoff Key Messages",
      archetype: "consulting-executive-summary",
      queries: ["2026.02", "2026.12.15", "Risk", "Scope"],
      fallback: [8, 14, 16, 18]
    },
    {
      title: "Consultant Capability",
      archetype: "why-what-how-logic",
      queries: ["Scope 1", "Scope 2", "Scope 3", "LCA", "CDP", "SBTi"],
      fallback: [4, 5, 6, 13]
    },
    {
      title: "Scope and Deliverables",
      archetype: "proposal-scope-integrated",
      queries: ["2026.02", "2026.12.15", "NGMS", "ORS", "ETRS"],
      fallback: [8, 16, 18, 21]
    },
    {
      title: "Regulatory Context",
      archetype: "regulatory-timeline-radar",
      queries: ["125,000", "50,000", "25,000", "15,000", "2015", "2010"],
      fallback: [9, 10, 19]
    },
    {
      title: "Statement Preparation Method",
      archetype: "method-chevron",
      queries: ["2025", "3.31", "Scope 1", "Scope 2"],
      fallback: [16]
    },
    {
      title: "Facility Change and Boundary Flow",
      archetype: "inventory-boundary-flow",
      queries: ["15%", "Boundary", "Baseline"],
      fallback: [17, 18]
    },
    {
      title: "Allocation Change Criteria",
      archetype: "comparison-matrix",
      queries: ["15%", "2025", "KAU25"],
      fallback: [19, 20]
    },
    {
      title: "Allowance Market Risk",
      archetype: "impact-factoid-big-number",
      queries: ["KAU25", "2025", "2026"],
      fallback: [20]
    },
    {
      title: "NGMS ORS ETRS System Response",
      archetype: "disclosure-taxonomy-map",
      queries: ["NGMS", "ORS", "ETRS"],
      fallback: [21]
    },
    {
      title: "Data Request and Evidence Control",
      archetype: "data-request-tracker",
      queries: ["NGMS", "ORS", "ETRS", "2025"],
      fallback: [16, 17, 18, 21]
    },
    {
      title: "Assurance Readiness",
      archetype: "assurance-evidence-pack",
      queries: ["3.31", "10.31", "2026"],
      fallback: [8, 16, 18]
    },
    {
      title: "Workplan Milestones",
      archetype: "report-production-workflow",
      queries: ["2026.02", "2026.12.15", "3.31", "10.31"],
      fallback: [8, 16, 18]
    },
    {
      title: "Governance and Communication",
      archetype: "communication-management",
      queries: ["NGMS", "ORS", "ETRS", "Scope"],
      fallback: [8, 21]
    },
    {
      title: "Immediate Next Actions",
      archetype: "evidence-to-action-strip",
      queries: ["Risk", "15%", "2025", "2026"],
      fallback: [10, 14, 16, 19]
    }
  ];

  const slides = topics
    .map((topic, index) => makeTopicSlide(topic, pages, index + 1))
    .filter(Boolean);
  return slides.join("\n\n---\n");
}

function makeTopicSlide(topic, pages, index) {
  const matched = findTopicPages(topic, pages);
  const sourceText = matched.map((page) => page.text).join(" ");
  const bullets = extractTopicBullets(sourceText, topic.queries, 4);
  if (!bullets.length) return "";

  const sourcePages = matched.map((page) => page.pageNo).join(", ");
  return [
    `Slide ${index} [archetype:${topic.archetype}]: ${topic.title}`,
    ...bullets.map((bullet) => `- ${bullet}`),
    `- Source pages: ${sourcePages}`
  ].join("\n");
}

function findTopicPages(topic, pages) {
  const scored = pages
    .map((page) => ({
      page,
      score: topic.queries.reduce((sum, query) => sum + (page.text.includes(query) || page.title.includes(query) ? query.length : 0), 0)
    }))
    .filter((item) => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .map((item) => item.page);

  if (scored.length) return scored.slice(0, 3);
  return topic.fallback
    .map((pageNo) => pages.find((page) => page.pageNo === pageNo))
    .filter(Boolean)
    .slice(0, 3);
}

function extractTopicBullets(text, queries, maxItems) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  const candidates = [];

  for (const query of queries) {
    const idx = cleaned.indexOf(query);
    if (idx < 0) continue;
    const start = Math.max(0, idx - 35);
    const end = Math.min(cleaned.length, idx + 155);
    candidates.push(compactBullet(cleaned.slice(start, end)));
  }

  for (const sentence of sentenceChunks(cleaned)) {
    if (queries.some((query) => sentence.includes(query))) candidates.push(compactBullet(sentence));
  }

  const seen = new Set();
  return candidates
    .map((item) => item.replace(/^Source pages?:.*$/i, "").trim())
    .filter((item) => item.length >= 12)
    .filter((item) => {
      const key = item.slice(0, 32);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, maxItems);
}

function compactBullet(text) {
  const value = text
    .replace(/\s+/g, " ")
    .replace(/^[,.;:)\]]+/, "")
    .trim();
  if (value.length <= 60) return value;
  const sliced = value.slice(0, 59);
  const cut = Math.max(sliced.lastIndexOf(" "), sliced.lastIndexOf(","), sliced.lastIndexOf("/"));
  return `${sliced.slice(0, cut > 34 ? cut : 59).trim()}...`;
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
