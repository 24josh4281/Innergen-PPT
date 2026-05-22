import { estimateBoxLineCount, getQualityRecommendations, hasConsultingClaimSignal, mostRepeatedLayout } from "./qualityPolicy";
import { analyzeOneShotReadiness, type OneShotReadinessReport } from "./oneShotQuality";
import type { DeckMeta, PlannedSlide } from "./types";

export type QaStatus = "pass" | "warn" | "fail";

export interface QaCheck {
  label: string;
  status: QaStatus;
  detail: string;
}

export interface SlideQaResult {
  slideIndex: number;
  status: QaStatus;
  checks: QaCheck[];
}

export interface DeckQaReport {
  score: number;
  status: QaStatus;
  passCount: number;
  warnCount: number;
  failCount: number;
  globalChecks: QaCheck[];
  improvementActions: string[];
  oneShot: OneShotReadinessReport;
  slideResults: SlideQaResult[];
}

export function analyzeDeckQuality(slides: PlannedSlide[], meta: DeckMeta): DeckQaReport {
  const slideResults = slides.map(analyzeSlide);
  const globalChecks = analyzeDeck(slides, meta);
  const checks = [...globalChecks, ...slideResults.flatMap((slide) => slide.checks)];
  const failCount = checks.filter((check) => check.status === "fail").length;
  const warnCount = checks.filter((check) => check.status === "warn").length;
  const passCount = checks.filter((check) => check.status === "pass").length;
  const rawScore = 100 - failCount * 16 - warnCount * 5;
  const score = Math.max(0, Math.min(100, rawScore));
  const status: QaStatus = failCount ? "fail" : warnCount ? "warn" : "pass";
  const oneShot = analyzeOneShotReadiness(slides, meta);
  const improvementActions = [...oneShot.actions, ...getQualityRecommendations(slides, meta)].slice(0, 5);

  return { score, status, passCount, warnCount, failCount, globalChecks, improvementActions, oneShot, slideResults };
}

function analyzeSlide(slide: PlannedSlide): SlideQaResult {
  const texts = [
    slide.claimTitle,
    slide.governingMessage,
    slide.rationale,
    ...slide.bullets,
    ...slide.sections
  ].filter(Boolean);

  const checks: QaCheck[] = [
    checkTitle(slide.claimTitle),
    checkGoverningMessage(slide.governingMessage),
    checkClaimSignal(slide.governingMessage),
    checkBulletVolume(slide.bullets),
    checkRawHyphen(texts),
    checkSectionLength(slide.sections),
    checkBoxFitRisk(slide.sections),
    checkSectionLabels(slide.sections),
    checkStructureDiversity(slide)
  ];

  const status: QaStatus = checks.some((check) => check.status === "fail")
    ? "fail"
    : checks.some((check) => check.status === "warn")
      ? "warn"
      : "pass";

  return { slideIndex: slide.index, status, checks };
}

function analyzeDeck(slides: PlannedSlide[], meta: DeckMeta): QaCheck[] {
  return [checkDeckSize(slides), checkDeckLayoutDiversity(slides), checkTemplateCoverage(slides, meta)];
}

function checkDeckSize(slides: PlannedSlide[]): QaCheck {
  if (!slides.length) return fail("Deck 구성", "장표가 없습니다.");
  if (slides.length < 3) return warn("Deck 구성", "3장 미만 deck은 제안서/보고서 흐름이 약할 수 있습니다.");
  return pass("Deck 구성", "Storyboard 단위로 검토 가능한 장표 수입니다.");
}

function checkDeckLayoutDiversity(slides: PlannedSlide[]): QaCheck {
  const repeated = mostRepeatedLayout(slides);
  if (slides.length >= 6 && repeated.count >= Math.ceil(slides.length * 0.55)) {
    return warn("구조 다양성", `'${repeated.label}' 구조가 ${repeated.count}회 반복됩니다. 일부 장표 구조를 바꾸세요.`);
  }
  return pass("구조 다양성", "동일 구조 반복이 과도하지 않습니다.");
}

function checkTemplateCoverage(slides: PlannedSlide[], meta: DeckMeta): QaCheck {
  const context = `${meta.documentType} ${meta.purpose}`.toLowerCase();
  if (!/(제안|입찰|proposal|rfp|착수|중간|최종|교육|검증)/.test(context)) {
    return pass("문서 유형", "일반 deck으로 처리합니다.");
  }

  const deckText = slides
    .map((slide) => `${slide.archetype.id} ${slide.claimTitle} ${slide.sections.join(" ")}`)
    .join(" ")
    .toLowerCase();
  if (/(제안|입찰|proposal|rfp)/.test(context) && slides.length >= 4) {
    const hasScope = /scope|work-scope|proposal-scope|범위|과업|산출/.test(deckText);
    const hasMethod = /method|process|workflow|schedule|방법|수행|절차|단계/.test(deckText);
    if (!hasScope || !hasMethod) return warn("스토리라인", "제안서에는 Scope와 수행방법론 흐름이 함께 필요합니다.");
  }
  return pass("스토리라인", "문서 유형에 맞는 핵심 흐름을 포함합니다.");
}

function checkTitle(title: string): QaCheck {
  const length = [...title].length;
  if (!title.trim()) return fail("제목", "슬라이드 제목이 비어 있습니다.");
  if (length > 58) return warn("제목 길이", "상단 제목이 길어 PPT에서 잘릴 수 있습니다. 45자 안팎을 권장합니다.");
  return pass("제목 길이", "상단 제목으로 사용 가능한 길이입니다.");
}

function checkGoverningMessage(message: string): QaCheck {
  const length = [...message].length;
  if (!message.trim()) return fail("Governing message", "컨설팅 장표의 한 줄 메시지가 없습니다.");
  if (length < 18) return warn("Governing message", "메시지가 너무 짧아 주장성이 약합니다.");
  if (length > 110) return warn("Governing message", "메시지가 길어 본문처럼 보일 수 있습니다. 한 문장으로 압축하세요.");
  return pass("Governing message", "주장형 한 줄 메시지가 설정되어 있습니다.");
}

function checkClaimSignal(message: string): QaCheck {
  if (hasConsultingClaimSignal(message)) return pass("메시지 주장성", "실행/판단 방향이 드러납니다.");
  return warn("메시지 주장성", "단순 설명처럼 보일 수 있습니다. 필요, 핵심, 우선 조치 등 판단 문장을 넣으세요.");
}

function checkBulletVolume(bullets: string[]): QaCheck {
  if (bullets.length > 6) return warn("본문량", "한 장에 들어갈 내용이 많습니다. 5개 이하 근거로 압축하는 것이 좋습니다.");
  if (bullets.some((bullet) => [...bullet].length > 180)) return warn("본문 길이", "긴 문장이 있어 표/카드 안에서 넘칠 수 있습니다.");
  return pass("본문량", "한 장표에 들어갈 수 있는 분량입니다.");
}

function checkRawHyphen(texts: string[]): QaCheck {
  const hasRawList = texts.some((text) => /^\s*-\s+/.test(text) || /\n\s*-\s+/.test(text));
  if (hasRawList) return fail("글머리 처리", "raw '- 내용' 문자열이 남아 있습니다. PPT 기본 bullet이나 구조형 개체로 바꿔야 합니다.");
  return pass("글머리 처리", "raw 하이픈 나열 없이 구조화되었습니다.");
}

function checkSectionLength(sections: string[]): QaCheck {
  const longSection = sections.find((section) => [...section].length > 145);
  if (longSection) return warn("구조 텍스트", "구조화 항목 중 긴 문장이 있어 PPT에서는 요약 표시됩니다.");
  if (!sections.length) return fail("구조 텍스트", "본문 구조화 항목이 없습니다.");
  return pass("구조 텍스트", "구조화 항목 길이가 안정적입니다.");
}

function checkBoxFitRisk(sections: string[]): QaCheck {
  const risky = sections.filter((section) => {
    const [, value = section] = section.split(":");
    return estimateBoxLineCount(value, 2.25, 12) > 2.4;
  }).length;
  if (risky) return warn("박스 적합성", `${risky}개 항목은 박스 안에서 여러 줄이 될 수 있어 bullet 처리가 필요합니다.`);
  return pass("박스 적합성", "박스 안에 들어갈 수 있는 분량입니다.");
}

function checkSectionLabels(sections: string[]): QaCheck {
  if (!sections.length) return fail("구조 라벨", "구조화 항목이 없습니다.");
  const labeled = sections.filter((section) => /^.{1,24}:\s*\S+/.test(section)).length;
  if (labeled < sections.length) return warn("구조 라벨", "일부 항목은 '라벨: 내용' 형태가 아니라 구조 매칭이 약해질 수 있습니다.");
  return pass("구조 라벨", "모든 항목이 라벨과 내용으로 분리되어 있습니다.");
}

function checkStructureDiversity(slide: PlannedSlide): QaCheck {
  if (slide.archetype.id === "consulting-executive-summary" && slide.index > 3) {
    return warn("구조 다양성", "요약형 구조가 반복되면 AI식 나열처럼 보일 수 있습니다.");
  }
  return pass("구조 다양성", `${slide.archetype.label} 구조를 적용합니다.`);
}

function pass(label: string, detail: string): QaCheck {
  return { label, detail, status: "pass" };
}

function warn(label: string, detail: string): QaCheck {
  return { label, detail, status: "warn" };
}

function fail(label: string, detail: string): QaCheck {
  return { label, detail, status: "fail" };
}
