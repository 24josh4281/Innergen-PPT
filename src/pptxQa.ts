import JSZip from "jszip";
import { hasNarrowSingleWordRisk } from "./qualityPolicy";

export interface PptxLayoutQaReport {
  score: number;
  status: "pass" | "warn" | "fail";
  slideCount: number;
  minFontSize: number | null;
  belowMinFontCount: number;
  rawHyphenCount: number;
  ellipsisCount: number;
  overflowRiskCount: number;
  overlapRiskCount: number;
  narrowTextRiskCount: number;
  sparseContainerCount: number;
  tableWhitespaceRiskCount: number;
  alignmentRiskCount: number;
  warnings: string[];
  issues: PptxQaIssue[];
}

export interface PptxQaIssue {
  type:
    | "below-min-font"
    | "raw-hyphen"
    | "ellipsis"
    | "overflow"
    | "overlap"
    | "narrow-text"
    | "sparse-container"
    | "table-whitespace"
    | "alignment";
  severity: "warn" | "fail";
  slide: number;
  objectId?: string;
  objectName?: string;
  relatedObjectId?: string;
  relatedObjectName?: string;
  x?: number;
  y?: number;
  w?: number;
  h?: number;
  relatedX?: number;
  relatedY?: number;
  relatedW?: number;
  relatedH?: number;
  textPreview?: string;
  reason: string;
  remediation: string;
}

interface TextBox {
  slide: number;
  objectId?: string;
  objectName?: string;
  x: number;
  y: number;
  w: number;
  h: number;
  text: string;
  fontSize: number;
}

type ShapeBox = TextBox;

export async function analyzePptxPackage(blob: Blob, minFontSize = 11): Promise<PptxLayoutQaReport> {
  const zip = await JSZip.loadAsync(await blob.arrayBuffer());
  const slideNames = Object.keys(zip.files)
    .filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name))
    .sort((a, b) => slideNumber(a) - slideNumber(b));

  const fontSizes: number[] = [];
  let rawHyphenCount = 0;
  let ellipsisCount = 0;
  let overflowRiskCount = 0;
  let overlapRiskCount = 0;
  let narrowTextRiskCount = 0;
  let sparseContainerCount = 0;
  let tableWhitespaceRiskCount = 0;
  let alignmentRiskCount = 0;
  const warnings: string[] = [];
  const issues: PptxQaIssue[] = [];

  for (const name of slideNames) {
    const xml = await zip.file(name)?.async("string");
    if (!xml) continue;
    const slideNo = slideNumber(name);
    const slideFonts = [...xml.matchAll(/\ssz="(\d+)"/g)].map((match) => Number(match[1]) / 100);
    fontSizes.push(...slideFonts);
    rawHyphenCount += [...xml.matchAll(/<a:t>\s*-\s+/g)].length;
    ellipsisCount += countTruncatedTextMarkers(xml);

    const shapeBoxes = extractShapeBoxes(xml, slideNo);
    const boxes = shapeBoxes.filter((box) => box.text);
    const tableIssues = collectTableWhitespaceIssues(xml, slideNo);
    const overflowIssues = boxes.filter(hasOverflowRisk).map((box) => shapeIssue("overflow", box, "Text is likely to overflow the object.", "Split into bullets, widen the object, or move detail into a supporting row."));
    const overlapIssues = collectOverlapIssues(boxes);
    const narrowIssues = boxes
      .filter((box) => hasNarrowSingleWordRisk(box.text, box.w, box.fontSize))
      .map((box) => shapeIssue("narrow-text", box, "A short Korean/label word is in a box that is too narrow.", "Keep one-word labels on one line by widening the box or lowering label density."));
    const sparseIssues = collectSparseContainerRisks(shapeBoxes);
    const alignmentIssues = collectAlignmentRisks(shapeBoxes);

    tableWhitespaceRiskCount += tableIssues.length;
    overflowRiskCount += overflowIssues.length;
    overlapRiskCount += overlapIssues.length;
    narrowTextRiskCount += narrowIssues.length;
    sparseContainerCount += sparseIssues.length;
    alignmentRiskCount += alignmentIssues.length;
    issues.push(...tableIssues, ...overflowIssues, ...overlapIssues, ...narrowIssues, ...sparseIssues, ...alignmentIssues);
  }

  const belowMinFontCount = fontSizes.filter((size) => size < minFontSize).length;
  if (belowMinFontCount) warnings.push(`${minFontSize}pt 미만 텍스트가 ${belowMinFontCount}개 있습니다.`);
  if (rawHyphenCount) warnings.push(`raw '- 내용' 형태 텍스트가 ${rawHyphenCount}개 있습니다.`);
  if (ellipsisCount) warnings.push(`말줄임표로 잘린 텍스트가 ${ellipsisCount}개 있습니다. 문구를 줄이거나 bullet로 분리해야 합니다.`);
  if (overflowRiskCount) warnings.push(`텍스트 박스 넘침 추정 위험이 ${overflowRiskCount}개 있습니다.`);
  if (overlapRiskCount) warnings.push(`텍스트/개체 겹침 추정 위험이 ${overlapRiskCount}개 있습니다.`);
  if (narrowTextRiskCount) warnings.push(`한 단어가 좁은 박스에서 깨질 위험이 ${narrowTextRiskCount}개 있습니다.`);
  if (sparseContainerCount) {
    warnings.push(
      `큰 박스 대비 본문 밀도가 낮은 컨테이너가 ${sparseContainerCount}개 있습니다. 판단칩, 근거 행, 요약바 등으로 구조를 보강해야 합니다.`
    );
  }
  if (tableWhitespaceRiskCount) {
    warnings.push(
      `표 셀 내부 여백이 과도한 행이 ${tableWhitespaceRiskCount}개 있습니다. 행 높이를 낮추거나 폰트/정보량을 키워야 합니다.`
    );
  }
  if (alignmentRiskCount) {
    warnings.push(
      `번호, 라벨, 칩, 본문 기준선 정렬이 어긋난 위험이 ${alignmentRiskCount}개 있습니다. 같은 rowY/rowH와 세로 중앙 정렬을 적용해야 합니다.`
    );
  }

  const rawScore =
    100 -
    belowMinFontCount * 7 -
    rawHyphenCount * 8 -
    ellipsisCount * 6 -
    overflowRiskCount * 8 -
    overlapRiskCount * 10 -
    narrowTextRiskCount * 4 -
    sparseContainerCount * 8 -
    tableWhitespaceRiskCount * 8 -
    alignmentRiskCount * 9;
  const score = Math.max(0, Math.min(100, rawScore));
  const status =
    belowMinFontCount ||
      rawHyphenCount ||
      ellipsisCount ||
      overflowRiskCount > 2 ||
      overlapRiskCount ||
      sparseContainerCount ||
      tableWhitespaceRiskCount ||
      alignmentRiskCount
      ? "fail"
      : overflowRiskCount || narrowTextRiskCount
        ? "warn"
        : "pass";

  return {
    score,
    status,
    slideCount: slideNames.length,
    minFontSize: fontSizes.length ? Math.min(...fontSizes) : null,
    belowMinFontCount,
    rawHyphenCount,
    ellipsisCount,
    overflowRiskCount,
    overlapRiskCount,
    narrowTextRiskCount,
    sparseContainerCount,
    tableWhitespaceRiskCount,
    alignmentRiskCount,
    warnings,
    issues
  };
}

function collectAlignmentRisks(boxes: ShapeBox[]) {
  return [...collectNumberedRowAlignmentRisks(boxes), ...collectChipLabelAlignmentRisks(boxes)];
}

function collectNumberedRowAlignmentRisks(boxes: ShapeBox[]) {
  const issues: PptxQaIssue[] = [];
  const textBoxes = boxes.filter((box) => box.text && box.y > 1.0 && box.y < 6.9);
  const numberedBoxes = textBoxes.filter((box) => isNumberLikeLabel(box.text));

  for (const numberBox of numberedBoxes) {
    const bodyBox = textBoxes
      .filter((box) => box !== numberBox)
      .filter((box) => !isNumberLikeLabel(box.text))
      .filter((box) => box.x > numberBox.x + numberBox.w && box.x - (numberBox.x + numberBox.w) < 0.95)
      .filter((box) => Math.abs(centerY(box) - centerY(numberBox)) < 0.42)
      .sort((a, b) => a.x - b.x || Math.abs(centerY(a) - centerY(numberBox)) - Math.abs(centerY(b) - centerY(numberBox)))[0];

    if (!bodyBox) continue;

    const baselineMismatch = Math.abs(centerY(numberBox) - centerY(bodyBox)) > 0.12;
    const numberTooShallow = numberBox.h < 0.22;
    const bodyLikelyWraps = meaningfulTextLength(bodyBox.text) > Math.max(10, bodyBox.w * 10.5);
    const bodyTooShallowForWrap = bodyLikelyWraps && bodyBox.h < 0.34;
    if (baselineMismatch || numberTooShallow || bodyTooShallowForWrap) {
      issues.push(pairIssue(
        "alignment",
        numberBox,
        bodyBox,
        "Number label and body text baseline are not aligned.",
        "Use the same rowY/rowH for number and body text, then apply vertical middle alignment."
      ));
    }
  }

  return issues;
}

function collectChipLabelAlignmentRisks(boxes: ShapeBox[]) {
  const issues: PptxQaIssue[] = [];
  const textBoxes = boxes.filter((box) => box.text);
  const containers = boxes.filter(
    (box) => !box.text && box.y > 0.72 && box.y < 6.95 && box.w >= 0.45 && box.w <= 3.5 && box.h >= 0.28 && box.h <= 0.85
  );

  for (const container of containers) {
    const contained = textBoxes.filter((box) => isCenterInside(container, box));
    if (contained.length !== 1) continue;
    const textBox = contained[0];
    const centerMismatch = Math.abs(centerY(container) - centerY(textBox)) > 0.09;
    const textBoxTooShallow = textBox.h < Math.min(0.18, container.h * 0.45);
    if (centerMismatch || textBoxTooShallow) {
      issues.push(pairIssue(
        "alignment",
        container,
        textBox,
        "Chip, label, or badge text is not vertically centered in its container.",
        "Set the text box to the same y/h as the container and use vertical middle alignment."
      ));
    }
  }

  return issues;
}

function isNumberLikeLabel(text: string) {
  const cleaned = text.trim();
  return /^(?:0?[1-9]|[1-9][0-9]|L\d{1,2}|STEP\s*\d{1,2})$/i.test(cleaned);
}

function centerY(box: ShapeBox) {
  return box.y + box.h / 2;
}

function isCenterInside(container: ShapeBox, item: ShapeBox) {
  const centerX = item.x + item.w / 2;
  const itemCenterY = item.y + item.h / 2;
  return centerX >= container.x && centerX <= container.x + container.w && itemCenterY >= container.y && itemCenterY <= container.y + container.h;
}

function collectTableWhitespaceIssues(xml: string, slideNo: number) {
  const issues: PptxQaIssue[] = [];
  const frames = [...xml.matchAll(/<p:graphicFrame[\s\S]*?<\/p:graphicFrame>/g)].map((match) => match[0]);
  frames.forEach((frame, frameIndex) => {
    if (!frame.includes("<a:tbl")) return;
    const frameBox = parseGraphicFrameBox(frame, slideNo, frameIndex + 1);
    const rows = [...frame.matchAll(/<a:tr[^>]*\sh="(\d+)"[\s\S]*?<\/a:tr>/g)];
    rows.slice(1).forEach((rowMatch) => {
      const rowXml = rowMatch[0];
      const rowH = emuToInch(Number(rowMatch[1] ?? 0));
      const rowText = [...rowXml.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)]
        .map((match) => decodeXml(match[1] ?? ""))
        .join(" ")
        .replace(/\s+/g, " ")
        .trim();
      const rowFonts = [...rowXml.matchAll(/\ssz="(\d+)"/g)].map((match) => Number(match[1]) / 100);
      const maxFont = rowFonts.length ? Math.max(...rowFonts) : 12;
      const textWeight = meaningfulTextLength(rowText);
      if (rowH >= 1.03 && maxFont < 12.3 && textWeight / Math.max(0.1, rowH) < 96) {
        issues.push({
          type: "table-whitespace",
          severity: "fail",
          slide: slideNo,
          objectId: frameBox.objectId,
          objectName: frameBox.objectName,
          x: frameBox.x,
          y: frameBox.y,
          w: frameBox.w,
          h: frameBox.h,
          textPreview: preview(rowText),
          reason: "Table row height is large compared with body font size and text density.",
          remediation: "Reduce row height, increase body font to 12-14pt, or add judgment/evidence/implication content."
        });
      }
    });
  });
  return issues;
}

function extractShapeBoxes(xml: string, slideNo: number): ShapeBox[] {
  return [...xml.matchAll(/<p:sp[\s\S]*?<\/p:sp>/g)]
    .map((match) => parseShapeBox(match[0], slideNo))
    .filter((box): box is ShapeBox => Boolean(box));
}

function parseShapeBox(shapeXml: string, slideNo: number): ShapeBox | null {
  const text = [...shapeXml.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)]
    .map((match) => decodeXml(match[1] ?? ""))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();

  const x = emuToInch(numberAttr(shapeXml, /<a:off[^>]*\sx="(-?\d+)"/));
  const y = emuToInch(numberAttr(shapeXml, /<a:off[^>]*\sy="(-?\d+)"/));
  const w = emuToInch(numberAttr(shapeXml, /<a:ext[^>]*\scx="(\d+)"/));
  const h = emuToInch(numberAttr(shapeXml, /<a:ext[^>]*\scy="(\d+)"/));
  const sizes = [...shapeXml.matchAll(/\ssz="(\d+)"/g)].map((match) => Number(match[1]) / 100);
  const fontSize = sizes.length ? Math.max(...sizes) : 12;
  if (!w || !h) return null;
  const objectId = shapeXml.match(/<p:cNvPr[^>]*\sid="([^"]+)"/)?.[1];
  const objectName = decodeXml(shapeXml.match(/<p:cNvPr[^>]*\sname="([^"]+)"/)?.[1] ?? "");

  return { slide: slideNo, objectId, objectName, x, y, w, h, text, fontSize };
}

function collectSparseContainerRisks(boxes: ShapeBox[]) {
  const issues: PptxQaIssue[] = [];
  const meaningfulBoxes = boxes.filter((box) => box.text && box.y > 1.0 && box.y < 6.9);

  for (const container of boxes) {
    if (!isLargeBodyContainer(container)) continue;

    const contained = meaningfulBoxes.filter((box) => box !== container && isInsideOrMostlyContained(container, box));
    const ownText = container.text ? [container] : [];
    const contents = [...ownText, ...contained].filter((box) => meaningfulTextLength(box.text) >= 2);
    if (!contents.length) continue;
    if (contents.length === 1 && contents[0] === container) continue;

    const area = container.w * container.h;
    const totalTextWeight = contents.reduce((sum, box) => sum + meaningfulTextLength(box.text), 0);
    const structureUnitCount = contents.reduce((sum, box) => sum + estimateStructureUnits(box.text), 0);
    const densityScore = totalTextWeight + structureUnitCount * 12;
    if (contents.length >= 3 || (structureUnitCount >= 4 && densityScore >= area * 5.2)) continue;

    if (densityScore < area * 7.5 || (area >= 6.2 && structureUnitCount < 3 && totalTextWeight < area * 10)) {
      issues.push(shapeIssue(
        "sparse-container",
        container,
        "Large container has too little structured text for its visual size.",
        "Do not leave a large empty box. Add judgment/evidence/implication/status rows, or shrink the container."
      ));
    }
  }

  return issues;
}

function isLargeBodyContainer(box: ShapeBox) {
  const area = box.w * box.h;
  return box.y > 1.05 && box.y < 6.85 && box.w >= 2.25 && box.h >= 1.3 && area >= 3.5 && box.w <= 12.4 && box.h <= 5.65;
}

function isInsideOrMostlyContained(container: ShapeBox, item: ShapeBox) {
  const centerX = item.x + item.w / 2;
  const centerY = item.y + item.h / 2;
  const centerInside =
    centerX >= container.x &&
    centerX <= container.x + container.w &&
    centerY >= container.y &&
    centerY <= container.y + container.h;
  return centerInside || overlapRatio(container, item) > 0.55;
}

function meaningfulTextLength(text: string) {
  return [...text.replace(/\s+/g, " ").trim()].reduce((sum, char) => sum + (/[A-Za-z0-9]/.test(char) ? 0.65 : 1), 0);
}

function estimateStructureUnits(text: string) {
  let count = 1;
  const lines = text.split(/\r\n|\n|\r/).filter((part) => meaningfulTextLength(part) >= 2);
  count += Math.max(0, lines.length - 1);
  const markerSet = new Set(["•", "①", "②", "③", "④", "⑤", "⑥"]);
  count += [...text].filter((char) => markerSet.has(char)).length;
  return Math.max(1, count);
}

function countTruncatedTextMarkers(xml: string) {
  return [...xml.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)]
    .map((match) => decodeXml(match[1] ?? ""))
    .filter((text) => text.includes("…") || text.includes("..."))
    .length;
}

function hasOverflowRisk(box: TextBox) {
  const fontFactor = Math.max(0.75, 12 / Math.max(8, box.fontSize));
  const charsPerLine = Math.max(4, box.w * 9.2 * fontFactor);
  const lineCount = Math.max(1, box.h * 3.65 * fontFactor);
  const capacity = charsPerLine * lineCount;
  return [...box.text].length > capacity * 1.35;
}

function collectOverlapIssues(boxes: TextBox[]) {
  const issues: PptxQaIssue[] = [];
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      if (boxes[i].slide !== boxes[j].slide) continue;
      if (overlapRatio(boxes[i], boxes[j]) > 0.18) {
        issues.push(pairIssue(
          "overlap",
          boxes[i],
          boxes[j],
          "Two text-bearing objects overlap visually.",
          "Move one object to a separate row/column, reduce container width, or send decorative connectors behind text."
        ));
      }
    }
  }
  return issues;
}

function shapeIssue(type: PptxQaIssue["type"], box: ShapeBox, reason: string, remediation: string): PptxQaIssue {
  return {
    type,
    severity: type === "narrow-text" ? "warn" : "fail",
    slide: box.slide,
    objectId: box.objectId,
    objectName: box.objectName,
    x: round(box.x),
    y: round(box.y),
    w: round(box.w),
    h: round(box.h),
    textPreview: preview(box.text),
    reason,
    remediation
  };
}

function pairIssue(type: PptxQaIssue["type"], primary: ShapeBox, related: ShapeBox, reason: string, remediation: string): PptxQaIssue {
  return {
    ...shapeIssue(type, primary, reason, remediation),
    relatedObjectId: related.objectId,
    relatedObjectName: related.objectName,
    relatedX: round(related.x),
    relatedY: round(related.y),
    relatedW: round(related.w),
    relatedH: round(related.h),
    textPreview: [preview(primary.text), preview(related.text)].filter(Boolean).join(" | ")
  };
}

function parseGraphicFrameBox(frameXml: string, slideNo: number, fallbackIndex: number): ShapeBox {
  const x = emuToInch(numberAttr(frameXml, /<a:off[^>]*\sx="(-?\d+)"/));
  const y = emuToInch(numberAttr(frameXml, /<a:off[^>]*\sy="(-?\d+)"/));
  const w = emuToInch(numberAttr(frameXml, /<a:ext[^>]*\scx="(\d+)"/));
  const h = emuToInch(numberAttr(frameXml, /<a:ext[^>]*\scy="(\d+)"/));
  const objectId = frameXml.match(/<p:cNvPr[^>]*\sid="([^"]+)"/)?.[1];
  const objectName = decodeXml(frameXml.match(/<p:cNvPr[^>]*\sname="([^"]+)"/)?.[1] ?? `Table ${fallbackIndex}`);
  return { slide: slideNo, objectId, objectName, x, y, w, h, text: "", fontSize: 12 };
}

function preview(text: string) {
  return text.replace(/\s+/g, " ").trim().slice(0, 80);
}

function round(value: number) {
  return Math.round(value * 1000) / 1000;
}

function overlapRatio(a: TextBox, b: TextBox) {
  const xOverlap = Math.max(0, Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x));
  const yOverlap = Math.max(0, Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y));
  const overlap = xOverlap * yOverlap;
  const smallerArea = Math.min(a.w * a.h, b.w * b.h);
  return smallerArea ? overlap / smallerArea : 0;
}

function numberAttr(xml: string, pattern: RegExp) {
  return Number(xml.match(pattern)?.[1] ?? 0);
}

function emuToInch(value: number) {
  return value / 914400;
}

function decodeXml(value: string) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

function slideNumber(name: string) {
  return Number(name.match(/slide(\d+)\.xml/)?.[1] ?? 0);
}
