import JSZip from "jszip";
import { hasNarrowSingleWordRisk } from "./qualityPolicy";

export interface PptxLayoutQaReport {
  score: number;
  status: "pass" | "warn" | "fail";
  slideCount: number;
  minFontSize: number | null;
  belowMinFontCount: number;
  rawHyphenCount: number;
  overflowRiskCount: number;
  overlapRiskCount: number;
  narrowTextRiskCount: number;
  warnings: string[];
}

interface TextBox {
  slide: number;
  x: number;
  y: number;
  w: number;
  h: number;
  text: string;
  fontSize: number;
}

export async function analyzePptxPackage(blob: Blob, minFontSize = 11): Promise<PptxLayoutQaReport> {
  const zip = await JSZip.loadAsync(await blob.arrayBuffer());
  const slideNames = Object.keys(zip.files)
    .filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name))
    .sort((a, b) => slideNumber(a) - slideNumber(b));

  const fontSizes: number[] = [];
  let rawHyphenCount = 0;
  let overflowRiskCount = 0;
  let overlapRiskCount = 0;
  let narrowTextRiskCount = 0;
  const warnings: string[] = [];

  for (const name of slideNames) {
    const xml = await zip.file(name)?.async("string");
    if (!xml) continue;
    const slideNo = slideNumber(name);
    const slideFonts = [...xml.matchAll(/\ssz="(\d+)"/g)].map((match) => Number(match[1]) / 100);
    fontSizes.push(...slideFonts);
    rawHyphenCount += [...xml.matchAll(/<a:t>\s*-\s+/g)].length;

    const boxes = extractTextBoxes(xml, slideNo);
    overflowRiskCount += boxes.filter(hasOverflowRisk).length;
    overlapRiskCount += countOverlapRisks(boxes);
    narrowTextRiskCount += boxes.filter((box) => hasNarrowSingleWordRisk(box.text, box.w, box.fontSize)).length;
  }

  const belowMinFontCount = fontSizes.filter((size) => size < minFontSize).length;
  if (belowMinFontCount) warnings.push(`${minFontSize}pt 미만 텍스트가 ${belowMinFontCount}개 있습니다.`);
  if (rawHyphenCount) warnings.push(`raw '- 내용' 텍스트가 ${rawHyphenCount}개 남아 있습니다.`);
  if (overflowRiskCount) warnings.push(`텍스트 박스 넘침 추정 위험이 ${overflowRiskCount}개 있습니다.`);
  if (overlapRiskCount) warnings.push(`텍스트 개체 겹침 추정 위험이 ${overlapRiskCount}개 있습니다.`);
  if (narrowTextRiskCount) warnings.push(`짧은 단어가 좁은 박스에서 깨질 위험이 ${narrowTextRiskCount}개 있습니다.`);

  const rawScore = 100 - belowMinFontCount * 7 - rawHyphenCount * 8 - overflowRiskCount * 8 - overlapRiskCount * 10 - narrowTextRiskCount * 4;
  const score = Math.max(0, Math.min(100, rawScore));
  const status = belowMinFontCount || rawHyphenCount || overflowRiskCount > 2 || overlapRiskCount ? "fail" : overflowRiskCount || narrowTextRiskCount ? "warn" : "pass";

  return {
    score,
    status,
    slideCount: slideNames.length,
    minFontSize: fontSizes.length ? Math.min(...fontSizes) : null,
    belowMinFontCount,
    rawHyphenCount,
    overflowRiskCount,
    overlapRiskCount,
    narrowTextRiskCount,
    warnings
  };
}

function extractTextBoxes(xml: string, slideNo: number): TextBox[] {
  return [...xml.matchAll(/<p:sp[\s\S]*?<\/p:sp>/g)]
    .map((match) => parseTextBox(match[0], slideNo))
    .filter((box): box is TextBox => Boolean(box && box.text));
}

function parseTextBox(shapeXml: string, slideNo: number): TextBox | null {
  const text = [...shapeXml.matchAll(/<a:t>([\s\S]*?)<\/a:t>/g)]
    .map((match) => decodeXml(match[1] ?? ""))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  if (!text) return null;

  const x = emuToInch(numberAttr(shapeXml, /<a:off[^>]*\sx="(-?\d+)"/));
  const y = emuToInch(numberAttr(shapeXml, /<a:off[^>]*\sy="(-?\d+)"/));
  const w = emuToInch(numberAttr(shapeXml, /<a:ext[^>]*\scx="(\d+)"/));
  const h = emuToInch(numberAttr(shapeXml, /<a:ext[^>]*\scy="(\d+)"/));
  const sizes = [...shapeXml.matchAll(/\ssz="(\d+)"/g)].map((match) => Number(match[1]) / 100);
  const fontSize = sizes.length ? Math.max(...sizes) : 12;
  if (!w || !h) return null;

  return { slide: slideNo, x, y, w, h, text, fontSize };
}

function hasOverflowRisk(box: TextBox) {
  const fontFactor = Math.max(0.75, 12 / Math.max(8, box.fontSize));
  const charsPerLine = Math.max(4, box.w * 9.2 * fontFactor);
  const lineCount = Math.max(1, box.h * 3.65 * fontFactor);
  const capacity = charsPerLine * lineCount;
  return [...box.text].length > capacity * 1.35;
}

function countOverlapRisks(boxes: TextBox[]) {
  let count = 0;
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      if (boxes[i].slide !== boxes[j].slide) continue;
      if (overlapRatio(boxes[i], boxes[j]) > 0.18) count += 1;
    }
  }
  return count;
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
