import pptxgen from "pptxgenjs";
import { INNGEN_COLORS } from "./patterns";
import { shouldUseBulletsForBox, splitBoxTextToBullets } from "./qualityPolicy";
import type { DeckMeta, PlannedSlide } from "./types";

const W = 13.333;
const H = 7.5;
const FONT = "Malgun Gothic";
const MIN_FONT_SIZE = 11;
const BODY_X = 0.62;
const BODY_W = 12.1;
const BODY_TOP = 1.55;
const BODY_BOTTOM = 6.78;
const FOOTER_Y = 7.12;

type Slide = pptxgen.Slide;

export async function exportPptx(meta: DeckMeta, slides: PlannedSlide[]) {
  const { blob, fileName } = await buildPptxBlob(meta, slides);
  downloadBlob(blob, fileName);
  return { blob, fileName };
}

export async function buildPptxBlob(meta: DeckMeta, slides: PlannedSlide[]) {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "INNerGEN Slide Studio";
  pptx.subject = "INNerGEN ESG/Climate consulting deck draft";
  pptx.title = meta.projectTitle || "이너젠 자동화 PPT";
  pptx.company = "INNerGEN";
  pptx.theme = { headFontFace: FONT, bodyFontFace: FONT };

  addCover(pptx, meta);
  addContents(pptx, meta, slides);
  slides.forEach((slide, index) => addContentSlide(pptx, meta, slide, index + 3));

  const fileName = safeFileName(`${meta.clientName || "고객사"}_${meta.projectTitle || "이너젠_PPT"}_draft.pptx`);
  const blob = (await pptx.write({ outputType: "blob" })) as Blob;
  return { blob, fileName };
}

export function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

function addCover(pptx: pptxgen, meta: DeckMeta) {
  const slide = pptx.addSlide();
  slide.background = { color: INNGEN_COLORS.white };
  addText(slide, "INNerGEN", 0.55, 0.34, 1.45, 0.28, { size: 14, bold: true, color: INNGEN_COLORS.blue });
  line(slide, 0.5, 0.78, 12.3, INNGEN_COLORS.navy, 1.2);
  addText(slide, meta.projectTitle || "슬라이드 자동화 제안서", 1.0, 2.0, 11.3, 1.05, {
    size: 32,
    bold: true,
    color: INNGEN_COLORS.black,
    align: "center",
    valign: "middle"
  });
  addText(slide, meta.documentType || "컨설팅 제안서 초안", 3.1, 3.38, 7.1, 0.32, {
    size: 16,
    color: INNGEN_COLORS.muted,
    align: "center"
  });
  addText(slide, meta.dateLabel || todayLabel(), 4.2, 3.92, 4.9, 0.26, {
    size: 14,
    bold: true,
    color: INNGEN_COLORS.navy,
    align: "center"
  });
  rect(slide, 0, 6.24, W, 0.68, INNGEN_COLORS.navy, INNGEN_COLORS.navy);
  addText(slide, ["CO2", "Consulting", meta.clientName || "Client"].join("   |   "), 3.1, 6.43, 7.2, 0.24, {
    size: 15,
    bold: true,
    color: INNGEN_COLORS.white,
    align: "center"
  });
}

function addContents(pptx: pptxgen, meta: DeckMeta, slides: PlannedSlide[]) {
  const slide = pptx.addSlide();
  addHeader(slide, pptx, "Contents");
  addText(slide, meta.projectTitle || "이너젠 PPT 자동화", BODY_X, 1.15, 7.8, 0.36, {
    size: 19,
    bold: true,
    color: INNGEN_COLORS.navy
  });

  const items = slides.slice(0, 8).map((item, idx) => `${String(idx + 1).padStart(2, "0")}. ${singleLine(item.claimTitle, 34)}`);
  const colCount = items.length > 4 ? 2 : 1;
  const colW = colCount === 2 ? 5.75 : 8.6;
  const startX = colCount === 2 ? 0.8 : 2.0;
  const startY = 2.05;
  items.forEach((item, idx) => {
    const col = colCount === 2 ? idx % 2 : 0;
    const row = colCount === 2 ? Math.floor(idx / 2) : idx;
    const x = startX + col * 6.05;
    const y = startY + row * 0.82;
    rect(slide, x, y, colW, 0.58, idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.white, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.line);
    addText(slide, item, x + 0.22, y + 0.17, colW - 0.44, 0.18, {
      size: 14,
      bold: true,
      color: idx === 0 ? INNGEN_COLORS.blue : INNGEN_COLORS.navy
    });
  });
  addFooter(slide, 2);
}

function addContentSlide(pptx: pptxgen, meta: DeckMeta, item: PlannedSlide, pageNo: number) {
  const slide = pptx.addSlide();
  addHeader(slide, pptx, `${item.index}. ${item.claimTitle}`);
  addGoverningMessage(slide, item);

  if (item.archetype.id === "impact-factoid-big-number" || item.archetype.id === "dashboard-kpi-takeaway") {
    renderMetric(slide, pptx, item);
  } else if (item.archetype.id === "cycle-loop-pdca") {
    renderCycle(slide, pptx, item);
  } else if (item.archetype.id === "staircase-maturity-evolution") {
    renderStaircase(slide, pptx, item);
  } else if (item.archetype.id === "issue-tree-to-workplan") {
    renderIssueTree(slide, pptx, item);
  } else if (processIds.has(item.archetype.id)) {
    renderProcess(slide, pptx, item);
  } else if (tableIds.has(item.archetype.id)) {
    renderTable(slide, item);
  } else if (matrixIds.has(item.archetype.id)) {
    renderMatrix(slide, pptx, item);
  } else if (flowIds.has(item.archetype.id)) {
    renderFlow(slide, pptx, item);
  } else if (memoIds.has(item.archetype.id)) {
    renderEvidenceAction(slide, pptx, item);
  } else {
    renderCards(slide, pptx, item);
  }

  addFooter(slide, pageNo);
}

const processIds = new Set([
  "method-chevron",
  "sbti-process",
  "cdp-response-strategy",
  "climate-scenario-framework",
  "integrated-process-map",
  "report-production-workflow",
  "regulatory-timeline-radar",
  "funnel-conversion-pipeline"
]);

const tableIds = new Set([
  "work-scope-table",
  "proposal-scope-integrated",
  "team-management",
  "communication-management",
  "data-request-tracker",
  "training-curriculum-agenda",
  "assurance-evidence-pack",
  "score-improvement-levers",
  "tcfd-pillar-diagnosis"
]);

const matrixIds = new Set([
  "benchmark-readiness-summary",
  "comparison-matrix",
  "peer-good-practice-benchmark",
  "double-materiality-or-risk-map",
  "iro-register-map",
  "traffic-light-scorecard",
  "bubble-priority-portfolio",
  "waterfall-bridge-analysis",
  "scenario-financial-impact",
  "before-after-delta-bridge",
  "forecast-trend-chart"
]);

const flowIds = new Set([
  "inventory-boundary-flow",
  "reduction-roadmap-analysis",
  "disclosure-taxonomy-map",
  "value-chain-hotspot-map",
  "house-framework",
  "asis-tobe-gap-roadmap"
]);

const memoIds = new Set(["consulting-one-page-memo", "evidence-grid", "evidence-to-action-strip", "case-study-good-practice"]);

function renderCards(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, item.archetype.id === "proposal-need-three-cards" ? 3 : 4);
  const count = pairs.length;
  const gap = 0.18;
  const cardW = (BODY_W - gap * (count - 1)) / count;
  pairs.forEach(([label, value], idx) => {
    const x = BODY_X + idx * (cardW + gap);
    rect(slide, x, BODY_TOP, cardW, 4.55, idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.white, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.line);
    rect(slide, x, BODY_TOP, cardW, 0.48, idx === 0 ? INNGEN_COLORS.navy : INNGEN_COLORS.blue, idx === 0 ? INNGEN_COLORS.navy : INNGEN_COLORS.blue);
    addText(slide, `${String(idx + 1).padStart(2, "0")} ${singleLine(label, 14)}`, x + 0.16, BODY_TOP + 0.14, cardW - 0.32, 0.18, {
      size: 12.5,
      bold: true,
      color: INNGEN_COLORS.white,
      align: "center"
    });
    addText(slide, keyPhrase(value, 18), x + 0.24, BODY_TOP + 0.88, cardW - 0.48, 0.34, {
      size: 14.2,
      bold: true,
      color: INNGEN_COLORS.navy,
      align: "center",
      valign: "middle"
    });
    line(slide, x + 0.24, BODY_TOP + 1.78, cardW - 0.48, INNGEN_COLORS.line, 0.8);
    addText(slide, "검토 포인트", x + 0.24, BODY_TOP + 2.02, cardW - 0.48, 0.16, {
      size: 11.5,
      bold: true,
      color: INNGEN_COLORS.sky
    });
    addBulletList(slide, uniqueItems([value, item.bullets[idx + 1] ?? ""]), x + 0.24, BODY_TOP + 2.34, cardW - 0.48, 1.28, {
      size: 11.5,
      maxChars: 54,
      maxItems: 2
    });
    addText(slide, singleLine(actionCue(item, idx), 24), x + 0.24, BODY_TOP + 3.88, cardW - 0.48, 0.26, {
      size: 12,
      bold: true,
      color: idx === 0 ? INNGEN_COLORS.red : INNGEN_COLORS.blue,
      align: "center"
    });
  });
  addImplication(slide, item);
}

function renderProcess(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, 5);
  const gap = 0.08;
  const stepW = (BODY_W - gap * (pairs.length - 1)) / pairs.length;
  pairs.forEach(([label, value], idx) => {
    const x = BODY_X + idx * (stepW + gap);
    rect(slide, x, BODY_TOP, stepW, 0.62, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.navy, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.navy);
    addText(slide, singleLine(label, 12), x + 0.08, BODY_TOP + 0.19, stepW - 0.16, 0.16, {
      size: 12.3,
      bold: true,
      color: INNGEN_COLORS.white,
      align: "center"
    });
    rect(slide, x, BODY_TOP + 0.9, stepW, 3.58, INNGEN_COLORS.white, INNGEN_COLORS.line);
    addText(slide, `STEP ${idx + 1}`, x + 0.16, BODY_TOP + 1.12, stepW - 0.32, 0.18, {
      size: 11.5,
      bold: true,
      color: INNGEN_COLORS.sky,
      align: "center"
    });
    addText(slide, keyPhrase(value, 16), x + 0.18, BODY_TOP + 1.58, stepW - 0.36, 0.36, {
      size: 13.3,
      bold: true,
      color: INNGEN_COLORS.navy,
      align: "center",
      valign: "middle"
    });
    addMiniRow(slide, pptx, x + 0.14, BODY_TOP + 2.35, stepW - 0.28, "검토", reviewCue(item, idx), idx === 0);
    addMiniRow(slide, pptx, x + 0.14, BODY_TOP + 2.88, stepW - 0.28, "산출", outputCue(item, idx), false);
    addMiniRow(slide, pptx, x + 0.14, BODY_TOP + 3.41, stepW - 0.28, "관리", "담당/기한", false);
  });
  addImplication(slide, item);
}

function renderTable(slide: Slide, item: PlannedSlide) {
  const pairs = sectionPairs(item, 5);
  const rows = pairs.map(([label, value], idx) => [
    { text: singleLine(label, 16), options: { bold: true, color: INNGEN_COLORS.navy, fill: { color: idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.gray }, fontSize: pt(12.5), align: "center" as const, valign: "middle" as const } },
    { text: sentence(value, 82), options: { color: INNGEN_COLORS.text, fontSize: pt(12.2), valign: "middle" as const, margin: 5 } },
    { text: singleLine(outputCue(item, idx), 22), options: { color: INNGEN_COLORS.blue, bold: true, fontSize: pt(12.0), align: "center" as const, valign: "middle" as const } }
  ]);

  slide.addTable(
    [
      [
        { text: "구분", options: headerCell() },
        { text: "핵심 내용", options: headerCell() },
        { text: "산출/관리", options: headerCell() }
      ],
      ...rows
    ],
    {
      x: BODY_X,
      y: BODY_TOP,
      w: BODY_W,
      h: 4.75,
      border: { type: "solid", color: INNGEN_COLORS.line, pt: 0.8 },
      fontFace: FONT,
      fontSize: pt(12),
      margin: 5,
      colW: [2.25, 7.1, 2.75],
      rowH: [0.56, ...rows.map(() => 0.78)]
    }
  );
  addImplication(slide, item);
}

function renderMatrix(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, 4);
  rect(slide, BODY_X, BODY_TOP, 7.75, 4.55, INNGEN_COLORS.white, INNGEN_COLORS.line);
  rect(slide, BODY_X, BODY_TOP, 7.75, 0.48, INNGEN_COLORS.navy, INNGEN_COLORS.navy);
  addText(slide, "평가 구조", BODY_X + 0.24, BODY_TOP + 0.15, 2.0, 0.16, { size: 12.5, bold: true, color: INNGEN_COLORS.white });
  pairs.forEach(([label, value], idx) => {
    const y = BODY_TOP + 0.85 + idx * 0.82;
    rect(slide, BODY_X + 0.28, y, 1.95, 0.55, idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.gray, INNGEN_COLORS.line);
    addText(slide, singleLine(label, 13), BODY_X + 0.44, y + 0.18, 1.63, 0.14, { size: 11.8, bold: true, color: INNGEN_COLORS.navy, align: "center" });
    addText(slide, sentence(value, 54), BODY_X + 2.55, y + 0.1, 4.65, 0.28, { size: 12.2, bold: idx === 0, color: INNGEN_COLORS.text });
    rect(slide, BODY_X + 2.55, y + 0.46, Math.min(4.3, 1.6 + idx * 0.7), 0.07, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.blue, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.blue);
  });
  drawSidePanel(slide, pptx, 8.65, BODY_TOP, 4.07, 4.55, "우선 조치", item.bullets.slice(0, 5));
  addImplication(slide, item);
}

function renderFlow(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, 5);
  const gap = 0.22;
  const boxW = (BODY_W - gap * 4) / 5;
  line(slide, BODY_X + 0.4, BODY_TOP + 1.8, BODY_W - 0.8, INNGEN_COLORS.line, 1.2);
  pairs.forEach(([label, value], idx) => {
    const x = BODY_X + idx * (boxW + gap);
    rect(slide, x, BODY_TOP + 0.86, boxW, 2.18, idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.white, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.line);
    addText(slide, singleLine(label, 13), x + 0.12, BODY_TOP + 1.12, boxW - 0.24, 0.2, { size: 12.5, bold: true, color: INNGEN_COLORS.navy, align: "center" });
    addBoxBodyText(slide, value, x + 0.18, BODY_TOP + 1.54, boxW - 0.36, 0.88, {
      size: 11.8,
      maxChars: 38,
      maxItems: 2,
      align: "center"
    });
    if (idx < pairs.length - 1) {
      addText(slide, ">", x + boxW + 0.02, BODY_TOP + 1.57, 0.2, 0.24, { size: 16, bold: true, color: INNGEN_COLORS.sky, align: "center" });
    }
  });
  rect(slide, BODY_X, BODY_TOP + 3.72, BODY_W, 0.8, INNGEN_COLORS.paleBlue, INNGEN_COLORS.sky);
  addText(slide, "핵심 관리 기준", BODY_X + 0.28, BODY_TOP + 3.95, 2.4, 0.18, {
    size: 13.2,
    bold: true,
    color: INNGEN_COLORS.navy,
    align: "center"
  });
  addText(slide, singleLine(item.bullets[0] ?? item.governingMessage, 78), BODY_X + 2.95, BODY_TOP + 3.95, BODY_W - 3.35, 0.18, {
    size: 12.2,
    color: INNGEN_COLORS.text,
    align: "center"
  });
  addImplication(slide, item);
}

function renderCycle(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, 5);
  const cx = 6.55;
  const cy = 3.65;
  const nodes = [
    { x: cx, y: 1.8 },
    { x: 9.3, y: 3.25 },
    { x: cx, y: 4.7 },
    { x: 3.8, y: 3.25 }
  ];
  line(slide, cx - 2.0, cy, 4.0, INNGEN_COLORS.sky, 1.3);
  line(slide, cx, cy - 1.35, 0, INNGEN_COLORS.sky, 1.3, 0, 2.7);
  rect(slide, cx - 1.05, cy - 0.48, 2.1, 0.96, INNGEN_COLORS.paleBlue, INNGEN_COLORS.sky);
  addText(slide, "관리 기록", cx - 0.85, cy - 0.12, 1.7, 0.2, { size: 15, bold: true, color: INNGEN_COLORS.navy, align: "center" });
  nodes.forEach((node, idx) => {
    const [label, value] = pairs[idx];
    slide.addShape("ellipse", { x: node.x - 0.58, y: node.y - 0.58, w: 1.16, h: 1.16, fill: { color: idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.navy }, line: { color: INNGEN_COLORS.white, width: 1 } });
    addText(slide, singleLine(label, 9), node.x - 0.5, node.y - 0.08, 1.0, 0.18, { size: 13.5, bold: true, color: INNGEN_COLORS.white, align: "center" });
    const descX = idx === 1 ? node.x + 0.65 : idx === 3 ? node.x - 2.75 : node.x - 1.2;
    const descY = idx === 0 ? node.y + 0.75 : idx === 2 ? node.y + 0.75 : node.y - 0.2;
    addText(slide, sentence(value, 28), descX, descY, 2.4, 0.44, { size: 12.4, color: INNGEN_COLORS.text, align: "center" });
  });
  addImplication(slide, item);
}

function renderStaircase(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, 5);
  const stepW = 2.32;
  const gap = 0.34;
  const baseY = 5.18;
  pairs.forEach(([label, value], idx) => {
    const h = 1.0 + idx * 0.36;
    const x = BODY_X + idx * (stepW + gap);
    const y = baseY - h;
    const isLast = idx === pairs.length - 1;
    rect(slide, x, y, stepW, h, isLast ? INNGEN_COLORS.navy : idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.white, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.line);
    addText(slide, `L${idx + 1}`, x + 0.18, y + 0.18, 0.6, 0.2, { size: 13, bold: true, color: isLast ? INNGEN_COLORS.white : INNGEN_COLORS.sky });
    addText(slide, singleLine(label, 10), x + 0.34, y + 0.52, stepW - 0.68, 0.24, { size: 13.4, bold: true, color: isLast ? INNGEN_COLORS.white : INNGEN_COLORS.navy, align: "center" });
    addText(slide, singleLine(keyPhrase(value, 16), 16), x + 0.25, y + 0.9, stepW - 0.5, Math.max(0.28, h - 1.08), { size: 11.4, color: isLast ? INNGEN_COLORS.white : INNGEN_COLORS.text, align: "center", valign: "middle" });
  });
  line(slide, BODY_X, baseY + 0.16, BODY_W, INNGEN_COLORS.navy, 1.1);
  addImplication(slide, item);
}

function renderIssueTree(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const pairs = sectionPairs(item, 4);
  rect(slide, BODY_X, BODY_TOP + 1.65, 2.45, 0.76, INNGEN_COLORS.navy, INNGEN_COLORS.navy);
  addText(slide, singleLine(item.claimTitle, 18), BODY_X + 0.18, BODY_TOP + 1.9, 2.09, 0.16, { size: 12, bold: true, color: INNGEN_COLORS.white, align: "center" });
  pairs.forEach(([label, value], idx) => {
    const y = BODY_TOP + 0.35 + idx * 0.88;
    line(slide, BODY_X + 2.45, y + 0.36, 0.82, INNGEN_COLORS.line, 1);
    rect(slide, BODY_X + 3.27, y, 2.25, 0.72, idx === 0 ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.white, idx === 0 ? INNGEN_COLORS.sky : INNGEN_COLORS.line);
    addText(slide, singleLine(label, 13), BODY_X + 3.45, y + 0.25, 1.89, 0.14, { size: 11.8, bold: true, color: INNGEN_COLORS.navy, align: "center" });
    rect(slide, BODY_X + 6.1, y - 0.04, 6.15, 0.8, INNGEN_COLORS.white, INNGEN_COLORS.line);
    addBoxBodyText(slide, value, BODY_X + 6.35, y + 0.1, 5.65, 0.48, { size: 12.1, maxChars: 72, maxItems: 2 });
  });
  addImplication(slide, item);
}

function renderMetric(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  const metric = extractMetric(item.bullets.join(" ") || item.governingMessage);
  rect(slide, BODY_X, BODY_TOP, 4.25, 4.55, INNGEN_COLORS.paleBlue, INNGEN_COLORS.sky);
  addText(slide, metric.value, BODY_X + 0.35, BODY_TOP + 1.3, 3.55, 0.72, { size: 38, bold: true, color: INNGEN_COLORS.navy, align: "center" });
  addText(slide, sentence(metric.context, 54), BODY_X + 0.45, BODY_TOP + 2.35, 3.35, 0.72, { size: 14, bold: true, color: INNGEN_COLORS.text, align: "center" });
  drawSidePanel(slide, pptx, 5.25, BODY_TOP, 7.47, 4.55, "관리 해석", item.bullets.slice(0, 5));
  addImplication(slide, item);
}

function renderEvidenceAction(slide: Slide, pptx: pptxgen, item: PlannedSlide) {
  rect(slide, BODY_X, BODY_TOP, 7.65, 4.55, INNGEN_COLORS.white, INNGEN_COLORS.line);
  addText(slide, "근거 / 해석", BODY_X + 0.32, BODY_TOP + 0.32, 2.0, 0.2, { size: 14, bold: true, color: INNGEN_COLORS.navy });
  addBulletList(slide, item.bullets.slice(0, 5), BODY_X + 0.42, BODY_TOP + 0.82, 6.85, 3.25, { size: 12.6, maxItems: 5, maxChars: 86 });
  drawSidePanel(slide, pptx, 8.68, BODY_TOP, 4.04, 4.55, "Action", [item.archetype.layoutHint, item.archetype.safetyRule, item.governingMessage]);
  addImplication(slide, item);
}

function addHeader(slide: Slide, pptx: pptxgen, title: string) {
  slide.background = { color: INNGEN_COLORS.white };
  rect(slide, 0, 0, W, 0.72, INNGEN_COLORS.navy, INNGEN_COLORS.navy);
  for (let x = 0.2; x < W; x += 0.3) line(slide, x, 0, 0, "1A3A5B", 0.35, 60, 0.72);
  for (let y = 0.14; y < 0.72; y += 0.18) line(slide, 0, y, W, "1A3A5B", 0.35, 60);
  addText(slide, singleLine(title, 38), 0.55, 0.18, 12.2, 0.28, { size: 19.2, bold: true, color: INNGEN_COLORS.white });
}

function addGoverningMessage(slide: Slide, item: PlannedSlide) {
  addText(slide, singleLine(item.governingMessage, 74), BODY_X, 0.88, 9.15, 0.32, {
    size: 15.2,
    bold: true,
    color: INNGEN_COLORS.black
  });
  rect(slide, 10.08, 0.86, 2.64, 0.36, INNGEN_COLORS.paleBlue, INNGEN_COLORS.sky);
  addText(slide, singleLine(item.archetype.label, 20), 10.2, 0.96, 2.4, 0.12, {
    size: 11.5,
    bold: true,
    color: INNGEN_COLORS.blue,
    align: "center"
  });
  line(slide, BODY_X, 1.28, BODY_W, INNGEN_COLORS.line, 0.8);
}

function addFooter(slide: Slide, pageNo: number) {
  line(slide, BODY_X, FOOTER_Y - 0.12, BODY_W, INNGEN_COLORS.line, 0.7);
  addText(slide, "INNerGEN", BODY_X, FOOTER_Y, 1.1, 0.14, { size: 11, bold: true, color: INNGEN_COLORS.navy });
  addText(slide, "Innovative Ideas | Better Solution", BODY_X + 1.22, FOOTER_Y, 3.4, 0.14, { size: 11, color: INNGEN_COLORS.muted });
  addText(slide, String(pageNo).padStart(2, "0"), 12.1, FOOTER_Y, 0.6, 0.14, { size: 11, bold: true, color: INNGEN_COLORS.muted, align: "right" });
}

function addImplication(slide: Slide, item: PlannedSlide) {
  rect(slide, BODY_X, 6.32, BODY_W, 0.44, INNGEN_COLORS.paleBlue, INNGEN_COLORS.sky);
  addText(slide, `→ ${singleLine(item.bullets.at(-1) ?? item.governingMessage, 82)}`, BODY_X + 0.24, 6.45, BODY_W - 0.48, 0.16, {
    size: 12.8,
    bold: true,
    color: INNGEN_COLORS.red
  });
}

function addMiniRow(slide: Slide, pptx: pptxgen, x: number, y: number, w: number, label: string, value: string, active: boolean) {
  rect(slide, x, y, w, 0.38, active ? INNGEN_COLORS.paleBlue : INNGEN_COLORS.gray, active ? INNGEN_COLORS.sky : INNGEN_COLORS.line);
  addText(slide, `${label}: ${singleLine(value, 10)}`, x + 0.08, y + 0.11, w - 0.16, 0.14, {
    size: 11.2,
    bold: true,
    color: active ? INNGEN_COLORS.blue : INNGEN_COLORS.text,
    align: "center"
  });
}

function drawSidePanel(slide: Slide, pptx: pptxgen, x: number, y: number, w: number, h: number, title: string, rows: string[], wide = false) {
  rect(slide, x, y, w, h, INNGEN_COLORS.paleBlue, INNGEN_COLORS.sky);
  addText(slide, singleLine(title, 24), x + 0.25, y + 0.24, w - 0.5, 0.24, { size: 14.2, bold: true, color: INNGEN_COLORS.navy, align: "center" });
  addBulletList(slide, rows, x + 0.34, y + 0.78, w - 0.68, Math.max(0.28, h - 1.18), {
    size: wide ? 12.2 : 12,
    maxItems: wide ? 3 : 5,
    maxChars: wide ? 92 : 58
  });
}

function addBulletList(slide: Slide, items: string[], x: number, y: number, w: number, h: number, opt: { size?: number; color?: string; maxItems?: number; maxChars?: number } = {}) {
  const visible = items.map(clean).filter(Boolean).slice(0, opt.maxItems ?? 5);
  if (!visible.length) return;
  const fontSize = pt(opt.size ?? bulletFontSize(visible, w, h));
  const bulletText = visible.map((item) => `• ${sentence(item, opt.maxChars ?? 72)}`).join("\n");
  slide.addText(bulletText, {
    x,
    y,
    w,
    h,
    fontFace: FONT,
    fontSize,
    color: opt.color ?? INNGEN_COLORS.text,
    margin: [2, 4, 2, 4],
    breakLine: false,
    valign: "top",
    paraSpaceAfter: 4,
    lineSpacingMultiple: 1.08
  });
}

function addBoxBodyText(
  slide: Slide,
  value: string,
  x: number,
  y: number,
  w: number,
  h: number,
  opt: {
    size?: number;
    color?: string;
    maxChars?: number;
    maxItems?: number;
    align?: "left" | "center" | "right";
  } = {}
) {
  const cleaned = clean(value);
  if (!cleaned) return;
  const size = pt(opt.size ?? 12.2);
  if (shouldBulletizeBox(cleaned, w, h, size, opt.maxChars ?? 64)) {
    addBulletList(slide, splitBoxBullets(cleaned, opt.maxItems ?? 3), x, y, w, h, {
      size: Math.max(MIN_FONT_SIZE, size - 0.2),
      color: opt.color ?? INNGEN_COLORS.text,
      maxItems: opt.maxItems ?? 3,
      maxChars: opt.maxChars ?? 64
    });
    return;
  }
  addText(slide, sentence(cleaned, opt.maxChars ?? 64), x, y + Math.max(0, h * 0.22), w, Math.max(0.16, h * 0.56), {
    size,
    color: opt.color ?? INNGEN_COLORS.text,
    align: opt.align ?? "left",
    valign: "middle"
  });
}

function addText(slide: Slide, value: string, x: number, y: number, w: number, h: number, opt: { size?: number; bold?: boolean; color?: string; align?: "left" | "center" | "right"; valign?: "top" | "middle" | "bottom"; margin?: number | [number, number, number, number] } = {}) {
  slide.addText(value, {
    x,
    y,
    w,
    h,
    fontFace: FONT,
    fontSize: pt(opt.size ?? 12.5),
    bold: opt.bold ?? false,
    color: opt.color ?? INNGEN_COLORS.text,
    align: opt.align ?? "left",
    valign: opt.valign ?? "top",
    margin: opt.margin ?? 0,
    breakLine: false
  });
}

function rect(slide: Slide, x: number, y: number, w: number, h: number, fill: string, border = fill) {
  slide.addShape("roundRect", {
    x,
    y,
    w,
    h,
    rectRadius: 0.04,
    fill: { color: fill },
    line: { color: border, width: 0.8 }
  });
}

function line(slide: Slide, x: number, y: number, w: number, color: string, width = 0.8, transparency = 0, h = 0) {
  slide.addShape("line", { x, y, w, h, line: { color, width, transparency } });
}

function headerCell() {
  return { bold: true, color: INNGEN_COLORS.white, fill: { color: INNGEN_COLORS.navy }, fontSize: pt(13.4), align: "center" as const, valign: "middle" as const };
}

function sectionPairs(item: PlannedSlide, count: number): [string, string][] {
  const pairs = item.sections.slice(0, count).map(splitSection);
  while (pairs.length < count) {
    const idx = pairs.length;
    pairs.push([item.archetype.structure[idx] ?? `항목 ${idx + 1}`, item.bullets[idx] ?? item.title]);
  }
  return pairs;
}

function splitSection(section: string): [string, string] {
  const [label, ...rest] = section.split(":");
  return [clean(label || "항목"), clean(rest.join(":") || section)];
}

function actionCue(item: PlannedSlide, idx: number) {
  const cues = ["우선 확인", "담당 지정", "기준 정리", "산출물 연결", "일정 관리"];
  return item.archetype.id === "proposal-need-three-cards" ? ["대응 필요성 명확화", "요구사항 반영", "실행 범위 확정"][idx] ?? cues[idx] : cues[idx] ?? "실행 관리";
}

function outputCue(item: PlannedSlide, idx: number) {
  const defaults = ["검토 메모", "분석 표", "산출물 초안", "QA 로그", "최종본"];
  const byType: Record<string, string[]> = {
    "data-request-tracker": ["자료 목록", "담당/기한", "제출 상태", "보완 이슈", "QA 로그"],
    "work-scope-table": ["업무 범위", "분석 대상", "방법론", "산출물", "검토 기준"],
    "sbti-process": ["진단 결과", "목표 경계", "제출 양식", "검증 대응", "공개 지침"],
    "cdp-response-strategy": ["문항 Gap", "증빙 목록", "답변 초안", "제출 QA", "보완 메모"]
  };
  return byType[item.archetype.id]?.[idx] ?? defaults[idx] ?? "산출물";
}

function reviewCue(item: PlannedSlide, idx: number) {
  const defaults = ["범위", "단위", "증빙", "담당", "기한"];
  return defaults[idx] ?? outputCue(item, idx);
}

function uniqueItems(items: string[]) {
  const seen = new Set<string>();
  return items
    .map(clean)
    .filter(Boolean)
    .filter((item) => {
      if (seen.has(item)) return false;
      seen.add(item);
      return true;
    });
}

function extractMetric(text: string) {
  const match = text.match(/[-+]?\d+(?:[.,]\d+)?\s*(?:%|pt|tCO2e|톤|억원|개|건|년|월)?/);
  const value = match?.[0]?.trim() || "3";
  const context = clean(text.replace(value, "")) || "핵심 지표를 기준으로 관리 방향을 판단합니다.";
  return { value, context };
}

function bulletFontSize(items: string[], w: number, h: number) {
  const chars = items.join("").length;
  if (chars < w * h * 12) return 12.8;
  if (chars < w * h * 16) return 12;
  return 11.2;
}

function shouldBulletizeBox(text: string, w: number, h: number, fontSize: number, maxChars: number) {
  return shouldUseBulletsForBox(text, w, h, fontSize, maxChars);
}

function splitBoxBullets(text: string, maxItems: number) {
  return splitBoxTextToBullets(text, maxItems);
}

function pt(size: number) {
  return Math.max(size, MIN_FONT_SIZE);
}

function clean(text: string) {
  return text.replace(/\s+/g, " ").replace(/^[\-*•·‣]\s*/, "").trim();
}

function singleLine(text: string, maxChars: number) {
  return truncate(clean(text).replace(/\s*\/\s*/g, "/"), maxChars);
}

function keyPhrase(text: string, maxChars: number) {
  const cleaned = clean(text)
    .replace(/^[^:]{1,16}:\s*/, "")
    .replace(/(입니다|합니다|됩니다|했습니다|합니다\.)$/g, "")
    .replace(/[.。]$/g, "");
  const firstClause = cleaned.split(/[,;·]| 그리고 | 또한 | 때문에 /)[0]?.trim() || cleaned;
  return truncate(firstClause, maxChars);
}

function sentence(text: string, maxChars: number) {
  return truncate(clean(text), maxChars);
}

function truncate(text: string, maxChars: number) {
  const chars = [...text];
  if (chars.length <= maxChars) return text;
  const sliced = chars.slice(0, Math.max(1, maxChars - 1)).join("");
  const lastSpace = sliced.lastIndexOf(" ");
  if (lastSpace > Math.floor(maxChars * 0.55)) return `${sliced.slice(0, lastSpace)}…`;
  return `${sliced}…`;
}

function safeFileName(name: string) {
  return name.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_");
}

function todayLabel() {
  const now = new Date();
  return `${now.getFullYear()}. ${String(now.getMonth() + 1).padStart(2, "0")}. ${String(now.getDate()).padStart(2, "0")}`;
}
