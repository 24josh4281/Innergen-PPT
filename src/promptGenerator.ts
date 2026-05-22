import { oneShotQaRules, oneShotStructureRules } from "./oneShotQuality";
import { getQualityRecommendations, qualityImprovementCycles } from "./qualityPolicy";
import type { DeckMeta, PlannedSlide } from "./types";

export type PromptMode = "one-shot-deck" | "storyboard-upgrade" | "qa-review" | "pptxgenjs-code";

export interface PromptModeProfile {
  id: PromptMode;
  label: string;
  description: string;
}

export interface GptPromptSummary {
  slideCount: number;
  structureCount: number;
  qaRuleCount: number;
  recommendationCount: number;
  modeLabel: string;
}

export const promptModes: PromptModeProfile[] = [
  {
    id: "one-shot-deck",
    label: "한큐 PPT 생성",
    description: "ChatGPT 채팅창에서 바로 PPT 제작 지시를 내릴 때 사용합니다."
  },
  {
    id: "storyboard-upgrade",
    label: "Storyboard 고도화",
    description: "PPT 생성 전 제목, governing message, 장표 구조만 먼저 다듬을 때 사용합니다."
  },
  {
    id: "qa-review",
    label: "PPT QA 리뷰",
    description: "생성된 장표 캡처나 PPT를 다시 검토하고 개선 지시를 받을 때 사용합니다."
  },
  {
    id: "pptxgenjs-code",
    label: "PPTX 코드 구현",
    description: "개발형 GPT에게 pptxgenjs 코드와 렌더링 QA까지 맡길 때 사용합니다."
  }
];

export function buildGptPromptSummary(meta: DeckMeta, slides: PlannedSlide[], mode: PromptMode = "one-shot-deck"): GptPromptSummary {
  return {
    slideCount: slides.length,
    structureCount: new Set(slides.map((slide) => slide.archetype.id)).size,
    qaRuleCount: oneShotQaRules.length,
    recommendationCount: getQualityRecommendations(slides, meta).length,
    modeLabel: getPromptMode(mode).label
  };
}

export function buildGptPptPrompt(meta: DeckMeta, slides: PlannedSlide[], mode: PromptMode = "one-shot-deck"): string {
  const recommendations = getQualityRecommendations(slides, meta);
  const storylineRule = matchStorylineRule(meta.documentType);
  const structureMix = summarizeStructureMix(slides);
  const profile = getPromptMode(mode);

  return [
    `# ${profile.label} 프롬프트`,
    "",
    "아래 지시문은 ChatGPT 채팅창에 그대로 붙여넣기 위한 프롬프트입니다.",
    "API 호출 없이 대화창 안에서 진행한다고 가정하고, 결과물은 사용자가 바로 검토하거나 PPT 제작에 활용할 수 있는 형태로 작성해 주세요.",
    "",
    "## 0. 역할",
    "당신은 ESG / 기후변화 컨설팅 제안서와 보고서를 만드는 시니어 컨설팅 PPT 디렉터입니다.",
    "목표는 원문 정보를 보존하면서도, 자동 변환 자료가 아니라 컨설팅사 수준의 설득형 장표로 재구성하는 것입니다.",
    "",
    "## 1. 이번 작업 모드",
    `- 모드: ${profile.label}`,
    `- 설명: ${profile.description}`,
    ...modeSpecificInstructions(mode),
    "",
    "## 2. 프로젝트 기본 정보",
    `- 고객사: ${safe(meta.clientName)}`,
    `- 프로젝트명: ${safe(meta.projectTitle)}`,
    `- 문서 유형: ${safe(meta.documentType)}`,
    `- 목적: ${safe(meta.purpose ?? "")}`,
    `- 대상 독자: ${safe(meta.audience ?? "")}`,
    `- 톤: ${safe(meta.tone ?? "")}`,
    `- 날짜: ${safe(meta.dateLabel)}`,
    "",
    "## 3. 절대 지켜야 할 정보 보존 원칙",
    "- 숫자, 단위, 날짜, 기간, 기관명, 법정 제출기한, 규제명은 임의로 바꾸지 않습니다.",
    "- 원문에 없는 사실, 근거, 수치, 고객사 상황을 새로 만들지 않습니다.",
    "- 불확실한 내용은 '확인 필요' 또는 '가정'으로 표시합니다.",
    "- 문장은 요약해도 되지만, 의미와 책임 범위는 보존합니다.",
    "- 고객사 기밀, 미공개 배출량, 견적, 개인정보가 있으면 외부 공유 전 확인이 필요하다고 표시합니다.",
    "",
    "## 4. INNerGEN 디자인 시스템",
    "- 색상은 INNerGEN BI를 유지합니다: Navy #041E42, Sky Blue #00A9E0, White #FFFFFF, Light Gray #F2F2F2.",
    "- Red/Orange는 리스크, 경고, 매우 중요한 포인트에만 드물게 사용합니다.",
    "- 폰트는 한글이 깨지지 않는 기본 폰트 중심으로 통일합니다: 맑은 고딕 우선, Pretendard 또는 Arial 보조.",
    "- 본문 최소 글자 크기는 11pt 이상입니다. 가능하면 14pt 이상으로 키웁니다.",
    "- 제목, governing message, 본문, 캡션의 위계를 명확히 둡니다.",
    "- 슬라이드 제목은 상단에 따로 두고, governing message는 제목 아래 흰색 영역에 검은색 한 줄 주장으로 둡니다.",
    "",
    "## 5. 레이아웃 QA 규칙",
    "- 텍스트 오버플로우, 개체 간 침범, 한글 글자 단위 줄바꿈을 절대 허용하지 않습니다.",
    "- '검토', '산출', '관리', '주의', 'L1', 'L2' 같은 짧은 단어와 라벨은 반드시 한 줄로 둡니다.",
    "- 박스 안에 여러 줄이 들어가야 하면 문단을 우겨 넣지 말고 bullet 또는 표로 바꿉니다.",
    "- 한 슬라이드의 본문 bullet은 최대 5개입니다.",
    "- 모든 화살표와 연결선은 텍스트 뒤로 보냅니다.",
    "- 카드형 박스 반복을 남발하지 말고, 내용 성격에 맞는 구조를 선택합니다.",
    "- 내부 작업 메모, source page view, original visual reference 같은 문구는 본문 장표에서 제거합니다.",
    "",
    "## 6. 문서 스토리라인",
    storylineRule
      ? `이 문서 유형에는 다음 흐름을 우선 적용합니다: ${storylineRule.storyline.join(" -> ")}.`
      : "기본 흐름은 Why it matters -> Current situation -> Key issues -> Recommended approach -> Deliverables -> Next steps 입니다.",
    "모든 장표는 '그래서 무엇을 판단하거나 실행해야 하는가'가 보이게 작성합니다.",
    "",
    "## 7. 현재 장표 구조 믹스",
    structureMix,
    "",
    "## 8. 슬라이드별 Storyboard",
    ...slides.flatMap((slide) => renderSlidePrompt(slide)),
    "",
    "## 9. QA 체크리스트",
    ...oneShotQaRules.map((rule) => `- ${rule.gate}: ${rule.rule} / 통과 기준: ${rule.pass}`),
    "",
    "## 10. 추가 개선 원칙",
    ...qualityImprovementCycles.map((cycle) => `- ${cycle.id.toUpperCase()} ${cycle.title}: ${cycle.act}`),
    ...(recommendations.length
      ? ["", "## 11. 이번 deck 전용 주의사항", ...recommendations.map((item) => `- ${item}`)]
      : []),
    "",
    "## 12. 응답 형식",
    ...responseFormat(mode),
    "",
    "중요: 결과물은 단순 요약이 아니라, 실제 제안서/착수보고/중간보고/최종보고에 들어갈 수 있는 컨설팅 장표 품질이어야 합니다."
  ].join("\n");
}

export function getPromptMode(mode: PromptMode): PromptModeProfile {
  return promptModes.find((item) => item.id === mode) ?? promptModes[0];
}

function modeSpecificInstructions(mode: PromptMode): string[] {
  if (mode === "storyboard-upgrade") {
    return [
      "- 이번에는 PPT 파일이나 코드를 만들지 말고, Storyboard만 고도화합니다.",
      "- 각 장표의 제목, governing message, 추천 구조, 본문 그룹, 근거/리스크를 표로 재정리합니다.",
      "- 구조가 반복되면 더 적합한 컨설팅 구조로 교체합니다."
    ];
  }

  if (mode === "qa-review") {
    return [
      "- 이번에는 새 PPT를 만들지 말고, 사용자가 붙여넣을 장표 캡처/텍스트를 리뷰합니다.",
      "- 오버플로우, 여백, 폰트 위계, 정렬, 한글 줄바꿈, 컨설팅 메시지 관점에서 문제를 찾아냅니다.",
      "- 각 문제는 슬라이드 번호, 문제, 수정 방향, 우선순위로 정리합니다."
    ];
  }

  if (mode === "pptxgenjs-code") {
    return [
      "- 이번에는 실행 가능한 pptxgenjs 기반 TypeScript/JavaScript 구현 지시를 작성합니다.",
      "- PPTX 생성 후 렌더링 QA까지 수행하는 흐름을 포함합니다.",
      "- 한글 폰트, 최소 글자 크기, 박스 fit, bullet 전환 로직을 코드 설계에 반영합니다."
    ];
  }

  return [
    "- 이번에는 ChatGPT가 바로 최종 PPT 제작에 들어갈 수 있도록 장표별 제작 지시를 완성합니다.",
    "- 먼저 누락된 핵심 정보가 있으면 최대 3개까지만 질문하고, 치명적 누락이 아니면 바로 초안을 만듭니다.",
    "- 결과는 사용자가 그대로 PPT 생성 도구 또는 디자이너에게 전달할 수 있게 작성합니다."
  ];
}

function responseFormat(mode: PromptMode): string[] {
  if (mode === "storyboard-upgrade") {
    return [
      "1. 전체 스토리라인 진단",
      "2. 슬라이드별 개선 Storyboard 표: No / 제목 / governing message / 추천 구조 / 본문 그룹 / QA 리스크",
      "3. 구조 반복 또는 메시지 약점 수정안",
      "4. 사용자가 승인해야 할 변경사항"
    ];
  }

  if (mode === "qa-review") {
    return [
      "1. 전체 품질 총평",
      "2. 슬라이드별 문제 목록: 심각도 / 위치 / 문제 / 수정 방향",
      "3. 오버플로우와 한글 줄바꿈 위험 목록",
      "4. 컨설팅 장표답게 보이기 위한 우선 수정 5개"
    ];
  }

  if (mode === "pptxgenjs-code") {
    return [
      "1. 구현 전략 요약",
      "2. 핵심 데이터 구조",
      "3. pptxgenjs 코드",
      "4. 렌더링 QA 방법",
      "5. 오버플로우 발생 시 자동 보정 로직"
    ];
  }

  return [
    "1. 최종 deck storyline 요약",
    "2. 슬라이드별 제작 지시 표: No / 제목 / governing message / 레이아웃 / 본문 / 시각요소 / QA 주의점",
    "3. 디자인 적용 지시",
    "4. 최종 QA 체크리스트",
    "5. 사용자가 확인해야 할 정보 보존 리스크"
  ];
}

function renderSlidePrompt(slide: PlannedSlide): string[] {
  return [
    "",
    `### Slide ${String(slide.index).padStart(2, "0")} - ${safe(slide.claimTitle || slide.title)}`,
    `- Governing message: ${safe(slide.governingMessage)}`,
    `- 추천 구조: ${safe(slide.archetype.label)} (${slide.archetype.id})`,
    `- 구조 요소: ${slide.archetype.structure.map(safe).join(" | ")}`,
    `- 레이아웃 힌트: ${safe(slide.archetype.layoutHint)}`,
    `- 안전 규칙: ${safe(slide.archetype.safetyRule)}`,
    `- 정보 밀도: ${slide.density}`,
    "- 본문 블록:",
    ...slide.sections.map((section, index) => `  ${index + 1}. ${safe(section)}`),
    "- 제작 지시: 제목과 governing message를 분리하고, 본문은 표/프로세스/비교/로드맵 등 추천 구조에 맞게 배치합니다."
  ];
}

function matchStorylineRule(documentType: string) {
  const normalized = safe(documentType);
  return oneShotStructureRules.find((rule) => normalized.includes(rule.documentType) || rule.documentType.includes(normalized));
}

function summarizeStructureMix(slides: PlannedSlide[]): string {
  const counts = new Map<string, number>();
  slides.forEach((slide) => counts.set(slide.archetype.label, (counts.get(slide.archetype.label) ?? 0) + 1));
  if (!counts.size) return "- 아직 계획된 슬라이드가 없습니다. Storyboard를 먼저 생성하세요.";
  return Array.from(counts.entries())
    .map(([label, count]) => `- ${label}: ${count}장`)
    .join("\n");
}

function safe(value: string): string {
  return value.replace(/\s+/g, " ").trim();
}
