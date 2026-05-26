import { buildPptxBlob } from "./ppt";
import { analyzePptxPackage, type PptxLayoutQaReport } from "./pptxQa";
import type { DeckMeta, PlannedSlide } from "./types";

export interface PptxQaAttempt {
  pass: number;
  action: string;
  qa: PptxLayoutQaReport;
}

export interface IterativePptxQaResult {
  blob: Blob;
  fileName: string;
  qa: PptxLayoutQaReport;
  slides: PlannedSlide[];
  attempts: PptxQaAttempt[];
}

const DEFAULT_MAX_PASSES = 3;

export async function buildPptxWithIterativeQa(
  meta: DeckMeta,
  slides: PlannedSlide[],
  maxPasses = DEFAULT_MAX_PASSES
): Promise<IterativePptxQaResult> {
  let workingSlides = cloneSlides(slides);
  let best: IterativePptxQaResult | null = null;
  const attempts: PptxQaAttempt[] = [];

  for (let pass = 1; pass <= maxPasses; pass += 1) {
    const { blob, fileName } = await buildPptxBlob(meta, workingSlides);
    const qa = await analyzePptxPackage(blob);
    const action = pass === 1 ? "원본 생성본 QA" : `자동 보정 ${pass - 1}차 후 QA`;
    attempts.push({ pass, action, qa });

    const candidate: IterativePptxQaResult = {
      blob,
      fileName,
      qa,
      slides: cloneSlides(workingSlides),
      attempts: [...attempts]
    };

    if (!best || qa.score > best.qa.score || (qa.status === "pass" && best.qa.status !== "pass")) {
      best = candidate;
    }

    if (qa.status === "pass") return candidate;
    if (pass < maxPasses) workingSlides = applyPptxQaRemediation(workingSlides, qa, pass);
  }

  return best ?? (await buildFallback(meta, workingSlides, attempts));
}

function applyPptxQaRemediation(slides: PlannedSlide[], qa: PptxLayoutQaReport, pass: number): PlannedSlide[] {
  const aggressive = pass >= 2 || qa.status === "fail" || qa.overflowRiskCount + qa.overlapRiskCount > 2;
  const sectionLimit = aggressive ? 4 : 5;
  const sectionValueMax = aggressive ? 68 : 82;
  const bulletMax = aggressive ? 4 : 5;
  const bulletTextMax = aggressive ? 72 : 88;

  return cloneSlides(slides).map((slide) => {
    const sections = slide.sections
      .slice(0, sectionLimit)
      .map((section) => compactSection(section, sectionValueMax, aggressive));

    const bullets = slide.bullets
      .map((bullet) => compactText(bullet, bulletTextMax))
      .filter(Boolean)
      .slice(0, bulletMax);

    return {
      ...slide,
      claimTitle: compactText(slide.claimTitle, aggressive ? 40 : 48),
      governingMessage: compactText(slide.governingMessage, aggressive ? 62 : 72),
      body: compactText(slide.body, aggressive ? 320 : 420),
      bullets,
      sections,
      density: aggressive && slide.density === "high" ? "medium" : slide.density,
      rationale: `${slide.rationale} / PPTX QA 자동 보정 ${pass}차: 긴 문장 축약, 섹션 수 ${sectionLimit}개 이하, 라벨 한 줄 유지`
    };
  });
}

function compactSection(section: string, valueMax: number, aggressive: boolean) {
  const [rawLabel, ...rest] = section.split(":");
  const hasLabel = rest.length > 0;
  const label = compactLabel(hasLabel ? rawLabel : "핵심", aggressive ? 10 : 14);
  const value = hasLabel ? rest.join(":") : section;
  return `${label}: ${compactText(value, valueMax)}`;
}

function compactLabel(text: string, maxChars: number) {
  return compactText(text.replace(/\s*\/\s*/g, "/"), maxChars).replace(/\s+/g, " ");
}

function compactText(text: string, maxChars: number) {
  const cleaned = clean(text)
    .replace(/\s*-\s+/g, " ")
    .replace(/\s*•\s*/g, " ")
    .replace(/\s+/g, " ");
  const chars = [...cleaned];
  if (chars.length <= maxChars) return cleaned;

  const sliced = chars.slice(0, Math.max(1, maxChars - 1)).join("");
  const breakPoint = Math.max(sliced.lastIndexOf(" "), sliced.lastIndexOf(","), sliced.lastIndexOf("·"), sliced.lastIndexOf("/"));
  if (breakPoint > Math.floor(maxChars * 0.55)) return `${sliced.slice(0, breakPoint).trim()}…`;
  return `${sliced.trim()}…`;
}

function cloneSlides(slides: PlannedSlide[]) {
  return slides.map((slide) => ({
    ...slide,
    bullets: [...slide.bullets],
    sections: [...slide.sections]
  }));
}

async function buildFallback(meta: DeckMeta, slides: PlannedSlide[], attempts: PptxQaAttempt[]): Promise<IterativePptxQaResult> {
  const { blob, fileName } = await buildPptxBlob(meta, slides);
  const qa = await analyzePptxPackage(blob);
  return { blob, fileName, qa, slides: cloneSlides(slides), attempts: [...attempts, { pass: attempts.length + 1, action: "fallback QA", qa }] };
}

function clean(text: string) {
  return text.replace(/\s+/g, " ").replace(/^[\-*•·‣]\s*/, "").trim();
}
