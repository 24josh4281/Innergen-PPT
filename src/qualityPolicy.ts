import type { DeckMeta, PlannedSlide } from "./types";

export interface QualityImprovementCycle {
  id: string;
  title: string;
  plan: string;
  do: string;
  check: string;
  act: string;
}

export const qualityImprovementCycles: QualityImprovementCycle[] = [
  {
    id: "pdca-01",
    title: "긴 박스 텍스트 bullet 전환",
    plan: "여러 줄 문장형 박스가 overflow와 AI식 문단감을 만들지 않도록 기준을 세웁니다.",
    do: "박스 폭, 높이, 글자 수를 추정해 긴 문장은 bullet로 자동 전환합니다.",
    check: "PPTX XML QA와 PowerPoint 렌더링 QA에서 overflow 0건을 확인합니다.",
    act: "향후 모든 신규 레이아웃은 동일한 박스 텍스트 정책을 사용합니다."
  },
  {
    id: "pdca-02",
    title: "한글 단어/짧은 라벨 한 줄 유지",
    plan: "검토, 산출, 관리, L1 같은 짧은 라벨이 글자 단위로 깨지는 문제를 막습니다.",
    do: "라벨은 single-line 처리하고, 좁은 박스 위험을 QA 지표로 추적합니다.",
    check: "최소 폰트와 좁은 텍스트 위험 건수를 확인합니다.",
    act: "라벨 박스는 폭을 줄이기보다 텍스트를 줄이는 방향으로 운영합니다."
  },
  {
    id: "pdca-03",
    title: "Governing message 주장성 강화",
    plan: "장표 제목 아래 메시지가 단순 설명이 아니라 의사결정 문장이 되도록 합니다.",
    do: "필요, 핵심, 리스크, 개선, 우선 같은 주장 신호를 QA에서 확인합니다.",
    check: "주장성이 약한 메시지는 Storyboard 단계에서 경고합니다.",
    act: "사용자가 PPT 생성 전에 메시지를 먼저 다듬도록 합니다."
  },
  {
    id: "pdca-04",
    title: "문서 유형별 스토리라인 고정",
    plan: "제안서, 착수보고, 중간보고, 최종보고가 서로 다른 흐름을 갖도록 합니다.",
    do: "문서 유형별 권장 구조와 활용 시나리오를 연결합니다.",
    check: "Storyboard QA에서 유형별 핵심 장표가 빠졌는지 확인합니다.",
    act: "사용자는 템플릿을 직접 고르지 않아도 목적 기반으로 시작합니다."
  },
  {
    id: "pdca-05",
    title: "레이아웃 반복 방지",
    plan: "슬라이드 수만 많고 구조가 반복되는 문제를 방지합니다.",
    do: "동일 archetype이 과도하게 반복되면 deck-level QA에서 경고합니다.",
    check: "샘플북 전체 구조 다양성 점검을 통과해야 합니다.",
    act: "반복 경고가 뜨면 Storyboard에서 구조를 교체합니다."
  },
  {
    id: "pdca-06",
    title: "본문 분량과 항목 수 제어",
    plan: "한 장에 너무 많은 내용을 넣어 글자가 작아지는 문제를 줄입니다.",
    do: "bullet 수, section 길이, box fit risk를 사전 QA로 확인합니다.",
    check: "긴 항목은 split 또는 bullet화하도록 경고합니다.",
    act: "고밀도 장표는 분리 또는 Appendix 이동 후보로 관리합니다."
  },
  {
    id: "pdca-07",
    title: "QA 개선 제안 표시",
    plan: "점수만 보여주는 QA는 사용자가 무엇을 고쳐야 할지 알기 어렵습니다.",
    do: "Deck-level 추천 조치를 Storyboard 상단에 표시합니다.",
    check: "QA summary에 바로 실행 가능한 개선 문장이 표시되는지 확인합니다.",
    act: "사용자는 수정 반영/QA 버튼으로 반복 개선합니다."
  },
  {
    id: "pdca-08",
    title: "실제 업무 활용 시나리오 제품화",
    plan: "모든 사용자가 제안서/착수/중간/최종/증빙/교육 흐름을 바로 시작해야 합니다.",
    do: "업무 시나리오 버튼, 샘플 입력, 산출물 안내를 UI에 구현합니다.",
    check: "로컬 앱 화면에서 시나리오 패널과 자동 분석을 확인합니다.",
    act: "향후 업로드 파일도 시나리오별로 다르게 요약하도록 확장합니다."
  },
  {
    id: "pdca-09",
    title: "샘플북 기반 렌더링 회귀검증",
    plan: "새 구조를 추가할 때마다 실제 PowerPoint 이미지로 깨짐을 확인해야 합니다.",
    do: "전체 archetype 샘플북과 layout-family 샘플북을 재생성합니다.",
    check: "PowerPoint COM 렌더링 QA에서 overflow, overlap, 최소 폰트를 확인합니다.",
    act: "새 레이아웃은 샘플북 통과 후 기본 DB에 편입합니다."
  },
  {
    id: "pdca-10",
    title: "개선 이력 문서화",
    plan: "품질 개선이 일회성 수정이 아니라 운영 기준으로 남아야 합니다.",
    do: "10회 PDCA 개선 결과와 검증 값을 문서로 남깁니다.",
    check: "최종 보고서에서 개선사항과 남은 리스크를 확인합니다.",
    act: "다음 개선 주기는 실제 사용자 PPT 실패 사례를 입력으로 삼습니다."
  }
];

export function shouldUseBulletsForBox(text: string, widthIn: number, heightIn: number, fontPt: number, maxChars = 64) {
  const normalized = cleanQualityText(text);
  if (!normalized) return false;
  if (heightIn < 0.62) return false;

  const estimatedLines = estimateBoxLineCount(normalized, widthIn, fontPt);
  const hasMultipleClauses = /[:;,.]|,| 그리고 | 또한 | 다만 | 단, |\/|\s-\s/.test(normalized);
  return estimatedLines > 1.15 || normalized.length > maxChars * 0.82 || (hasMultipleClauses && estimatedLines > 0.9);
}

export function splitBoxTextToBullets(text: string, maxItems = 3) {
  const normalized = cleanQualityText(text)
    .replace(/\b(Before|After|Delta|Issue|Action|Risk|Output|Owner)\s*:/gi, "$1: ")
    .replace(/\s+/g, " ");

  const sentenceParts = normalized
    .split(/(?<=[.!?。])\s+|;\s+|·\s+|\s+\|\s+/)
    .map((part) => part.trim())
    .filter(Boolean);
  if (sentenceParts.length > 1) return sentenceParts.slice(0, maxItems);

  const keyedParts = normalized
    .split(/\s+(?=(?:Before|After|Delta|Issue|Action|Risk|Output|Owner|결론|시사점|대응|근거|산출물)\s*:)/i)
    .map((part) => part.trim())
    .filter(Boolean);
  if (keyedParts.length > 1) return keyedParts.slice(0, maxItems);

  const commaParts = normalized
    .split(/,\s+| 그리고 | 또한 | 다만 | 단, /)
    .map((part) => part.trim())
    .filter((part) => part.length > 4);
  if (commaParts.length > 1) return commaParts.slice(0, maxItems);

  return [normalized];
}

export function estimateBoxLineCount(text: string, widthIn: number, fontPt: number) {
  const capacity = Math.max(8, Math.floor((widthIn * 9.4 * 12) / Math.max(fontPt, 11)));
  return weightedTextLength(cleanQualityText(text)) / capacity;
}

export function hasConsultingClaimSignal(text: string) {
  return /(해야|필요|핵심|우선|리스크|개선|확정|연결|관리|줄일 수|높일 수|확보|의사결정|실행)/.test(text);
}

export function hasNarrowSingleWordRisk(text: string, widthIn: number, fontPt: number) {
  const normalized = cleanQualityText(text);
  if (!normalized || /\s/.test(normalized)) return false;
  if ([...normalized].length > 10) return false;
  return weightedTextLength(normalized) > widthIn * Math.max(10, fontPt * 0.88);
}

export function getQualityRecommendations(slides: PlannedSlide[], meta: DeckMeta): string[] {
  const actions: string[] = [];
  const repeated = mostRepeatedLayout(slides);
  if (repeated.count >= Math.max(3, Math.ceil(slides.length * 0.45))) {
    actions.push(`반복 구조가 많습니다: '${repeated.label}' 구조를 일부 다른 구조로 바꾸세요.`);
  }

  const weakMessages = slides.filter((slide) => !hasConsultingClaimSignal(slide.governingMessage)).length;
  if (weakMessages) actions.push(`Governing message ${weakMessages}건은 주장성이 약합니다. '무엇을 해야 하는지'가 보이게 고치세요.`);

  const denseSlides = slides.filter((slide) => slide.density === "high").length;
  if (denseSlides) actions.push(`고밀도 장표 ${denseSlides}건은 글자가 작아질 수 있습니다. 본문을 5개 bullet 이하로 나누세요.`);

  const context = `${meta.documentType} ${meta.purpose}`.toLowerCase();
  if (/(제안|입찰|proposal|rfp)/.test(context) && slides.length >= 4) {
    const deckText = slides
      .map((slide) => `${slide.archetype.id} ${slide.claimTitle} ${slide.sections.join(" ")}`)
      .join(" ")
      .toLowerCase();
    const hasScope = /scope|범위|과업|산출/.test(deckText);
    const hasMethod = /method|process|방법|수행|절차|단계/.test(deckText);
    if (!hasScope || !hasMethod) actions.push("제안서는 Scope와 수행방법론 장표가 모두 있어야 설득력이 생깁니다.");
  }

  return actions.slice(0, 4);
}

export function mostRepeatedLayout(slides: PlannedSlide[]) {
  const counts = new Map<string, { label: string; count: number }>();
  for (const slide of slides) {
    const current = counts.get(slide.archetype.id) ?? { label: slide.archetype.label, count: 0 };
    current.count += 1;
    counts.set(slide.archetype.id, current);
  }
  return [...counts.values()].sort((a, b) => b.count - a.count)[0] ?? { label: "-", count: 0 };
}

function weightedTextLength(text: string) {
  return [...text].reduce((sum, char) => sum + (/[A-Za-z0-9]/.test(char) ? 0.62 : char === " " ? 0.28 : 1), 0);
}

function cleanQualityText(text: string) {
  return text.replace(/\s+/g, " ").replace(/^[\-*•·‣]\s*/, "").trim();
}
