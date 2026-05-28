import { oneShotQaRules, oneShotStructureRules } from "./oneShotQuality";
import { getQualityRecommendations, qualityImprovementCycles } from "./qualityPolicy";
import { summarizeReferenceTopNProfileForPrompt } from "./referenceTopN";
import { summarizeReferenceProfileForPrompt } from "./referenceStructureDb";
import { summarizeStandardDeckFlowForPrompt } from "./standardDeckFlow";
import { getReferenceStructureProfileForMeta, getReferenceTopNProfileForMeta, getStandardDeckFlowForMeta } from "./templates";
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
  const standardFlow = getStandardDeckFlowForMeta(meta);
  const topNProfile = getReferenceTopNProfileForMeta(meta);
  const referenceProfile = getReferenceStructureProfileForMeta(meta);
  const standardFlowLines = summarizeStandardDeckFlowForPrompt(standardFlow);
  const topNProfileLines = summarizeReferenceTopNProfileForPrompt(topNProfile);
  const referenceProfileLines = summarizeReferenceProfileForPrompt(meta, referenceProfile);

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
    `- 사업 유형: ${safe(meta.businessType ?? "")}`,
    `- 회의 유형: ${safe(meta.meetingType ?? "")}`,
    `- 목적: ${safe(meta.purpose ?? "")}`,
    `- 대상 독자: ${safe(meta.audience ?? "")}`,
    `- 톤: ${safe(meta.tone ?? "")}`,
    `- 날짜: ${safe(meta.dateLabel)}`,
    "",
    "## 3. 입력 진단 절차",
    ...inputDiagnosisRules(mode),
    "",
    "## 4. 절대 지켜야 할 정보 보존 원칙",
    "- 숫자, 단위, 날짜, 기간, 기관명, 법정 제출기한, 규제명은 임의로 바꾸지 않습니다.",
    "- 원문에 없는 사실, 근거, 수치, 고객사 상황을 새로 만들지 않습니다.",
    "- 불확실한 내용은 '확인 필요' 또는 '가정'으로 표시합니다.",
    "- 문장은 요약해도 되지만, 의미와 책임 범위는 보존합니다.",
    "- 고객사 기밀, 미공개 배출량, 견적, 개인정보가 있으면 외부 공유 전 확인이 필요하다고 표시합니다.",
    "",
    "## 5. INNerGEN 디자인 시스템",
    "- 색상은 INNerGEN BI를 유지합니다: Navy #041E42, Sky Blue #00A9E0, White #FFFFFF, Light Gray #F2F2F2.",
    "- Red/Orange는 리스크, 경고, 매우 중요한 포인트에만 드물게 사용합니다.",
    "- 폰트는 한글이 깨지지 않는 기본 폰트 중심으로 통일합니다: 맑은 고딕 우선, Pretendard 또는 Arial 보조.",
    "- 본문 최소 글자 크기는 11pt 이상입니다. 가능하면 14pt 이상으로 키웁니다.",
    "- 제목, governing message, 본문, 캡션의 위계를 명확히 둡니다.",
    "- 슬라이드 제목은 상단에 따로 두고, governing message는 제목 아래 흰색 영역에 검은색 한 줄 주장으로 둡니다.",
    "",
    "## 5-A. 표준 Deck Flow 적용",
    ...standardFlowLines,
    "",
    "## 5-B. 승인 샘플 Top N 구조 적용",
    ...topNProfileLines,
    "",
    "## 5-C. 레퍼런스 구조 DB 적용",
    ...referenceProfileLines,
    "",
    "## 6. 좋은 컨설팅 PPT 판정 기준",
    ...consultingQualityRules(),
    "",
    "## 7. 레이아웃 QA 규칙",
    "- 텍스트 오버플로우, 개체 간 침범, 한글 글자 단위 줄바꿈을 절대 허용하지 않습니다.",
    "- '검토', '산출', '관리', '주의', 'L1', 'L2' 같은 짧은 단어와 라벨은 반드시 한 줄로 둡니다.",
    "- 박스 안에 여러 줄이 들어가야 하면 문단을 우겨 넣지 말고 bullet 또는 표로 바꿉니다.",
    "- 한 슬라이드의 본문 bullet은 최대 5개입니다.",
    "- 모든 화살표와 연결선은 텍스트 뒤로 보냅니다.",
    "- 카드형 박스 반복을 남발하지 말고, 내용 성격에 맞는 구조를 선택합니다.",
    "- 내부 작업 메모, source page view, original visual reference 같은 문구는 본문 장표에서 제거합니다.",
    "",
    "## 8. 슬라이드별 산출 계약",
    ...slideOutputContract(),
    "",
    "## 9. 문서 스토리라인",
    storylineRule
      ? `이 문서 유형에는 다음 흐름을 우선 적용합니다: ${storylineRule.storyline.join(" -> ")}.`
      : "기본 흐름은 Why it matters -> Current situation -> Key issues -> Recommended approach -> Deliverables -> Next steps 입니다.",
    "모든 장표는 '그래서 무엇을 판단하거나 실행해야 하는가'가 보이게 작성합니다.",
    "",
    "## 10. 현재 장표 구조 믹스",
    structureMix,
    "",
    "## 11. 슬라이드별 Storyboard",
    ...slides.flatMap((slide) => renderSlidePrompt(slide)),
    "",
    "## 12. QA 체크리스트",
    ...oneShotQaRules.map((rule) => `- ${rule.gate}: ${rule.rule} / 통과 기준: ${rule.pass}`),
    "",
    "## 13. 추가 개선 원칙",
    ...qualityImprovementCycles.map((cycle) => `- ${cycle.id.toUpperCase()} ${cycle.title}: ${cycle.act}`),
    ...(recommendations.length
      ? ["", "## 14. 이번 deck 전용 주의사항", ...recommendations.map((item) => `- ${item}`)]
      : []),
    "",
    "## 15. 최종 자기검수",
    ...finalSelfQaRules(mode),
    "",
    "## 16. 응답 형식",
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
      "- 구조가 반복되면 더 적합한 컨설팅 구조로 교체합니다.",
      "- 각 governing message는 단순 설명이 아니라 판단, 의미, 실행 방향이 담긴 'so what' 문장으로 바꿉니다."
    ];
  }

  if (mode === "qa-review") {
    return [
      "- 이번에는 새 PPT를 만들지 말고, 사용자가 붙여넣을 장표 캡처/텍스트를 리뷰합니다.",
      "- 오버플로우, 여백, 폰트 위계, 정렬, 한글 줄바꿈, 컨설팅 메시지 관점에서 문제를 찾아냅니다.",
      "- 각 문제는 슬라이드 번호, 문제, 수정 방향, 우선순위로 정리합니다.",
      "- '보기 좋다/나쁘다' 수준이 아니라, 왜 설득력이 떨어지는지와 어떤 구조로 바꿀지까지 제시합니다."
    ];
  }

  if (mode === "pptxgenjs-code") {
    return [
      "- 이번에는 실행 가능한 pptxgenjs 기반 TypeScript/JavaScript 구현 지시를 작성합니다.",
      "- PPTX 생성 후 렌더링 QA까지 수행하는 흐름을 포함합니다.",
      "- 한글 폰트, 최소 글자 크기, 박스 fit, bullet 전환 로직을 코드 설계에 반영합니다.",
      "- 생성 후 PPTX를 이미지로 렌더링하고 오버플로우, 겹침, 한글 단어 쪼개짐을 자동 감지하는 QA 절차를 포함합니다."
    ];
  }

  return [
    "- 이번에는 ChatGPT가 바로 최종 PPT 제작에 들어갈 수 있도록 장표별 제작 지시를 완성합니다.",
    "- 먼저 누락된 핵심 정보가 있으면 최대 3개까지만 질문하고, 치명적 누락이 아니면 바로 초안을 만듭니다.",
    "- 결과는 사용자가 그대로 PPT 생성 도구 또는 디자이너에게 전달할 수 있게 작성합니다.",
    "- 바로 본문 bullet을 만들기 전에 전체 스토리라인과 슬라이드 역할을 먼저 확정합니다."
  ];
}

function inputDiagnosisRules(mode: PromptMode): string[] {
  const base = [
    "- 먼저 입력 자료를 Complete / Partial / Risky 중 하나로 분류합니다.",
    "- Complete: 고객사, 목적, 독자, 핵심 내용, 산출물 형태가 충분한 상태입니다. 바로 장표화를 진행합니다.",
    "- Partial: 일부 정보가 부족하지만 합리적 가정으로 진행 가능한 상태입니다. 가정표를 만들고 진행합니다.",
    "- Risky: 숫자, 규제, 책임 범위, 제출기한처럼 틀리면 위험한 정보가 부족한 상태입니다. 최대 3개 질문을 먼저 합니다.",
    "- 원문 사실, 합리적 가정, 디자인 판단을 구분해서 표시합니다.",
    "- 질문이 필요한 경우에도 장표 방향을 멈추지 말고, 확인 전 임시안과 확인 후 보정 포인트를 함께 제시합니다."
  ];

  if (mode === "qa-review") {
    return [
      ...base,
      "- 리뷰 입력이 캡처라면 눈에 보이는 문제와 원문 확인이 필요한 문제를 분리합니다."
    ];
  }

  if (mode === "pptxgenjs-code") {
    return [
      ...base,
      "- 코드 구현 전 슬라이드 수, 구조 타입, 긴 텍스트 위험, 표/도형 필요 여부를 먼저 데이터 모델로 정리합니다."
    ];
  }

  return base;
}

function consultingQualityRules(): string[] {
  return [
    "- 1장표 1메시지를 지킵니다. 제목은 주제, governing message는 결론 또는 판단이어야 합니다.",
    "- 단순 요약형 bullet 나열을 피하고, 원인-결과, 비교, 단계, 의사결정, 리스크-대응 같은 구조로 바꿉니다.",
    "- 정보 밀도는 중상 수준으로 유지합니다. 비어 보이는 장표보다 정렬된 고밀도 장표를 우선합니다.",
    "- 같은 카드 구조가 3장 이상 반복되면 표, 로드맵, 매트릭스, 타임라인, 계층도 중 더 적합한 구조로 교체합니다.",
    "- 강조는 핵심 숫자, 의사결정 기준, 리스크, 산출물명에만 제한적으로 적용합니다.",
    "- 모든 장표는 독자가 5초 안에 핵심 판단을 이해하고, 30초 안에 근거를 읽을 수 있어야 합니다."
  ];
}

function slideOutputContract(): string[] {
  return [
    "- 각 슬라이드는 반드시 Role, Governing message, Evidence, Recommended layout, Body blocks, Visual treatment, QA risk를 포함합니다.",
    "- Role은 배경 설명, 문제 진단, 비교, 방법론, 일정, 산출물, 의사결정, Appendix 중 하나로 명시합니다.",
    "- Governing message는 한 줄로 작성하되, 길면 문장을 줄이는 것이 우선이고 글자를 무리하게 줄이지 않습니다.",
    "- Body blocks는 긴 문장 1개보다 짧은 bullet 3~5개, 표 3열, 프로세스 4~5단계 중 하나를 우선합니다.",
    "- Recommended layout은 카드형을 기본값으로 두지 말고, 내용 성격에 맞춰 매트릭스/타임라인/비교표/워크스트림/스윔레인/계층도를 선택합니다.",
    "- QA risk에는 오버플로우 가능성, 단어 쪼개짐 가능성, 근거 확인 필요, 시각자료 부족 중 해당 항목을 적습니다."
  ];
}

function finalSelfQaRules(mode: PromptMode): string[] {
  const rules = [
    "- 응답 전 모든 슬라이드에 제목과 governing message가 분리되어 있는지 확인합니다.",
    "- 본문 bullet이 5개를 넘는 슬라이드는 구조를 다시 나눕니다.",
    "- 짧은 한글 단어, L1/L2 라벨, 숫자 단위가 줄바꿈으로 쪼개질 위험이 있으면 한 줄 라벨로 바꿉니다.",
    "- 박스 안 긴 문장은 bullet 또는 표로 바꾸고, 최소 11pt 미만으로 줄이는 해결책은 쓰지 않습니다.",
    "- 동일 레이아웃 반복이 과하면 최소 2개 이상 다른 컨설팅 구조로 교체합니다.",
    "- 최종 답변 끝에 확인 필요 정보와 수정 필요 슬라이드를 별도 표로 정리합니다."
  ];

  if (mode === "qa-review") {
    return [
      ...rules,
      "- QA 리뷰에서는 심각도 High 항목을 먼저 제시하고, 바로 수정 가능한 문장/구조 대안을 함께 씁니다."
    ];
  }

  if (mode === "pptxgenjs-code") {
    return [
      ...rules,
      "- 코드 지시에서는 렌더링 이미지 QA를 통과하지 못하면 폰트 축소보다 레이아웃 재배치를 우선하도록 명시합니다."
    ];
  }

  return rules;
}

function responseFormat(mode: PromptMode): string[] {
  if (mode === "storyboard-upgrade") {
    return [
      "1. 입력 진단: Complete / Partial / Risky 및 가정표",
      "2. 전체 스토리라인 진단",
      "3. 슬라이드별 개선 Storyboard 표: No / Role / 제목 / governing message / 추천 구조 / 본문 그룹 / QA 리스크",
      "4. 구조 반복 또는 메시지 약점 수정안",
      "5. 최종 자기검수 결과와 사용자가 승인해야 할 변경사항"
    ];
  }

  if (mode === "qa-review") {
    return [
      "1. 입력 진단: 캡처/텍스트 기준 검토 범위와 한계",
      "2. 전체 품질 총평",
      "3. 슬라이드별 문제 목록: 심각도 / 위치 / 문제 / 수정 방향",
      "4. 오버플로우와 한글 줄바꿈 위험 목록",
      "5. 컨설팅 장표답게 보이기 위한 우선 수정 5개",
      "6. 최종 자기검수 결과"
    ];
  }

  if (mode === "pptxgenjs-code") {
    return [
      "1. 입력 진단과 구현 가정",
      "2. 구현 전략 요약",
      "3. 핵심 데이터 구조",
      "4. pptxgenjs 코드",
      "5. 렌더링 QA 방법",
      "6. 오버플로우 발생 시 자동 보정 로직",
      "7. 최종 자기검수 결과"
    ];
  }

  return [
    "1. 입력 진단: Complete / Partial / Risky 및 가정표",
    "2. 최종 deck storyline 요약",
    "3. 슬라이드별 제작 지시 표: No / Role / 제목 / governing message / 레이아웃 / 본문 / 시각요소 / QA 주의점",
    "4. 디자인 적용 지시",
    "5. 최종 QA 체크리스트",
    "6. 사용자가 확인해야 할 정보 보존 리스크와 수정 필요 슬라이드"
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
    "- 산출 계약: Role / Evidence / Recommended layout / Body blocks / Visual treatment / QA risk를 모두 채웁니다.",
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
