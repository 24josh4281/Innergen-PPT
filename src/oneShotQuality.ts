import { hasConsultingClaimSignal, mostRepeatedLayout } from "./qualityPolicy";
import type { DeckMeta, PlannedSlide } from "./types";

export interface OneShotQaRule {
  id: string;
  gate: string;
  rule: string;
  pass: string;
  fail: string;
}

export interface OneShotStructureRule {
  documentType: string;
  storyline: string[];
  requiredRoles: string[];
  preferredLayouts: string[];
}

export interface OneShotReadinessCheck {
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
}

export interface OneShotReadinessReport {
  score: number;
  status: "pass" | "warn" | "fail";
  checks: OneShotReadinessCheck[];
  actions: string[];
}

export const oneShotBriefTemplate = `# 한큐 PPT 생성 브리프

## 1. 기본 조건
문서 유형: 컨설팅 제안서 / 착수보고 / 중간보고 / 최종보고 / 교육자료 중 선택
대상 독자: 고객사 임원 / 실무진 / 검증기관 / 내부 검토자
목표: 이 PPT를 본 사람이 어떤 의사결정을 해야 하는지 한 문장으로 작성
톤: 이너젠 BI 유지, 고급 컨설팅 장표, 과도한 장식 금지

## 2. 반드시 유지할 원문/수치
- 수치, 단위, 기준연도, 기간, 기관명은 원문 그대로 유지
- 추정/가정/미확인 내용은 확정 표현 금지
- 출처가 필요한 내용은 "출처:"로 표시

## 3. 슬라이드별 내용
슬라이드 1: 제목
핵심 메시지: 이 장표에서 말하고 싶은 결론 1문장
근거/내용:
- 첫 번째 근거
- 두 번째 근거
- 세 번째 근거
원하는 구조: 자동 추천 / 프로세스 / 표 / 비교 / 로드맵 / 이슈트리 / 대시보드 중 선택 가능

---
슬라이드 2: 제목
핵심 메시지:
근거/내용:
-
-
-

## 4. 디자인/품질 요구
- 제목과 governing message는 분리
- 한 슬라이드 본문 bullet은 최대 5개
- 박스 안 긴 문장은 bullet로 분리
- 한글 단어는 글자 단위로 줄바꿈 금지
- 최소 폰트 11pt 이상
- 이너젠 navy/sky/white 중심 색상 유지
- 내부 작업 메모, 원문 보존 같은 문구는 본문 장표에서 제외`;

export const oneShotStructureRules: OneShotStructureRule[] = [
  {
    documentType: "컨설팅 제안서",
    storyline: ["Why this matters", "Value at stake", "Scope", "Methodology", "Deliverables", "Team/Governance", "Schedule", "Next step"],
    requiredRoles: ["문제 정의", "고객 가치", "업무 범위", "수행 방법", "산출물"],
    preferredLayouts: ["Why / What / How", "3 Reasons", "Integrated Scope", "Method Chevron", "Work Scope Table", "Schedule Gantt"]
  },
  {
    documentType: "착수보고",
    storyline: ["Project objective", "Scope alignment", "Workplan", "Data request", "R&R", "Risk/issue", "Communication"],
    requiredRoles: ["목표", "범위", "일정", "자료요청", "담당/기한"],
    preferredLayouts: ["Executive Summary", "Integrated Scope", "Method Chevron", "Data Request Tracker", "Team / Governance"]
  },
  {
    documentType: "중간보고",
    storyline: ["Progress snapshot", "Key findings", "Issues", "Decision required", "Next actions"],
    requiredRoles: ["진행 현황", "발견사항", "이슈", "의사결정", "다음 조치"],
    preferredLayouts: ["KPI Dashboard", "Traffic-Light Scorecard", "Issue Tree", "Evidence to Action", "Meeting / Decision Log"]
  },
  {
    documentType: "최종보고",
    storyline: ["Executive conclusion", "Evidence", "Before/After", "Implications", "Roadmap", "Operating model"],
    requiredRoles: ["핵심 결론", "근거", "변화", "시사점", "로드맵"],
    preferredLayouts: ["Executive Summary", "Impact Factoid", "Before / After", "As-Is / To-Be Gap", "Reduction Logic"]
  },
  {
    documentType: "교육자료",
    storyline: ["Learning objective", "Concept", "Case", "Practice", "Checklist", "Q&A"],
    requiredRoles: ["학습 목표", "핵심 개념", "사례", "실습", "체크리스트"],
    preferredLayouts: ["Training Curriculum", "Case Study", "Evidence Grid", "Traffic-Light Scorecard"]
  }
];

export const oneShotQaRules: OneShotQaRule[] = [
  {
    id: "brief-completeness",
    gate: "Input",
    rule: "문서 유형, 대상 독자, 목표 의사결정, 유지해야 할 수치/원문을 입력한다.",
    pass: "생성기가 장표 목적과 보존해야 할 정보를 구분할 수 있다.",
    fail: "자료를 예쁘게 옮긴 요약 PPT가 된다."
  },
  {
    id: "single-message",
    gate: "Story",
    rule: "각 슬라이드는 제목과 별도의 governing message 1문장을 가진다.",
    pass: "장표가 읽는 문서가 아니라 설득하는 장표로 보인다.",
    fail: "본문 요약처럼 보이고 컨설팅 장표의 주장이 약해진다."
  },
  {
    id: "slide-role",
    gate: "Structure",
    rule: "각 슬라이드는 문제 정의, 근거, 비교, 방법론, 산출물, 의사결정 중 하나의 역할을 가진다.",
    pass: "슬라이드 간 흐름이 생긴다.",
    fail: "비슷한 카드형 장표가 반복된다."
  },
  {
    id: "layout-match",
    gate: "Structure",
    rule: "내용 성격에 맞는 구조를 선택한다. 절차는 process, 선택지는 matrix, 변화는 before/after, 이슈는 issue tree로 배치한다.",
    pass: "정보가 한눈에 들어온다.",
    fail: "모든 내용이 bullet/card로만 나열된다."
  },
  {
    id: "density",
    gate: "Content",
    rule: "본문 bullet은 5개 이하, 박스 안 문장은 2줄 위험 시 bullet로 분리한다.",
    pass: "글자 크기와 여백이 안정적이다.",
    fail: "작은 글씨, 넘침, 비어 보이는 장표가 생긴다."
  },
  {
    id: "korean-readability",
    gate: "Typography",
    rule: "검토, 산출, 관리, L1 같은 짧은 단어는 반드시 한 줄로 유지한다.",
    pass: "한글 단어가 글자 단위로 깨지지 않는다.",
    fail: "전문성이 크게 떨어져 보인다."
  },
  {
    id: "brand",
    gate: "Design",
    rule: "이너젠 navy/sky/white 기반 색상, Malgun Gothic 계열, 최소 11pt를 유지한다.",
    pass: "브랜드 일관성이 유지된다.",
    fail: "레퍼런스와 다른 색감/폰트가 된다."
  },
  {
    id: "render-qa",
    gate: "Final QA",
    rule: "PPTX 생성 후 XML QA와 PowerPoint 렌더링 QA를 모두 통과해야 한다.",
    pass: "overflow, overlap, raw hyphen, 단어 깨짐 위험을 정량 확인한다.",
    fail: "겉으로만 생성되고 실제 PowerPoint에서 깨질 수 있다."
  }
];

export function analyzeOneShotReadiness(slides: PlannedSlide[], meta: DeckMeta): OneShotReadinessReport {
  const checks: OneShotReadinessCheck[] = [
    checkBriefMeta(meta),
    checkSlideCount(slides),
    checkMessageStrength(slides),
    checkSlideRoles(slides),
    checkDensity(slides),
    checkLayoutRepetition(slides),
    checkStructureLabels(slides),
    checkDocumentStoryline(slides, meta)
  ];
  const failCount = checks.filter((check) => check.status === "fail").length;
  const warnCount = checks.filter((check) => check.status === "warn").length;
  const score = Math.max(0, Math.min(100, 100 - failCount * 18 - warnCount * 6));
  const status = failCount ? "fail" : warnCount ? "warn" : "pass";
  const actions = checks
    .filter((check) => check.status !== "pass")
    .map((check) => `${check.label}: ${check.detail}`)
    .slice(0, 4);
  return { score, status, checks, actions };
}

function checkBriefMeta(meta: DeckMeta): OneShotReadinessCheck {
  const missing = [
    ["문서 유형", meta.documentType],
    ["대상", meta.audience],
    ["목적", meta.purpose],
    ["톤", meta.tone]
  ].filter(([, value]) => !String(value ?? "").trim());
  if (missing.length) return fail("입력 브리프", `${missing.map(([label]) => label).join(", ")} 정보가 필요합니다.`);
  return pass("입력 브리프", "문서 유형, 대상, 목적, 톤이 설정되어 있습니다.");
}

function checkSlideCount(slides: PlannedSlide[]): OneShotReadinessCheck {
  if (slides.length < 3) return warn("스토리 분량", "한큐 생성에는 최소 3장 이상의 흐름이 안정적입니다.");
  if (slides.length > 35) return warn("스토리 분량", "35장 이상은 한 번에 만들기보다 챕터별 생성이 안정적입니다.");
  return pass("스토리 분량", "한 번에 생성하기 좋은 슬라이드 수입니다.");
}

function checkMessageStrength(slides: PlannedSlide[]): OneShotReadinessCheck {
  const weak = slides.filter((slide) => !hasConsultingClaimSignal(slide.governingMessage) || slide.governingMessage.length < 18).length;
  if (weak) return warn("Governing message", `${weak}개 장표는 주장형 메시지가 약합니다.`);
  return pass("Governing message", "모든 장표가 주장형 메시지를 갖고 있습니다.");
}

function checkSlideRoles(slides: PlannedSlide[]): OneShotReadinessCheck {
  const roleSignals = /why|scope|method|process|table|matrix|issue|dashboard|evidence|summary|범위|방법|이슈|근거|요약|산출/;
  const matched = slides.filter((slide) => roleSignals.test(`${slide.archetype.id} ${slide.archetype.label} ${slide.sections.join(" ")}`.toLowerCase())).length;
  if (matched / Math.max(1, slides.length) < 0.65) return warn("슬라이드 역할", "역할이 불명확한 장표가 많습니다. 문제/근거/방법/산출물 역할을 분리하세요.");
  return pass("슬라이드 역할", "대부분의 장표가 명확한 정보 역할을 갖고 있습니다.");
}

function checkDensity(slides: PlannedSlide[]): OneShotReadinessCheck {
  const dense = slides.filter((slide) => slide.density === "high" || slide.bullets.length > 6).length;
  if (dense) return warn("본문 밀도", `${dense}개 장표는 한 번에 넣을 정보가 많아 분할 후보입니다.`);
  return pass("본문 밀도", "슬라이드별 정보량이 안정적입니다.");
}

function checkLayoutRepetition(slides: PlannedSlide[]): OneShotReadinessCheck {
  const repeated = mostRepeatedLayout(slides);
  if (slides.length >= 6 && repeated.count >= Math.ceil(slides.length * 0.5)) {
    return warn("레이아웃 반복", `${repeated.label} 구조가 ${repeated.count}회 반복됩니다.`);
  }
  return pass("레이아웃 반복", "구조 반복이 과도하지 않습니다.");
}

function checkStructureLabels(slides: PlannedSlide[]): OneShotReadinessCheck {
  const unlabeled = slides.filter((slide) => slide.sections.some((section) => !/^.{1,24}:\s*\S+/.test(section))).length;
  if (unlabeled) return warn("구조 라벨", `${unlabeled}개 장표는 라벨: 내용 형태가 약합니다.`);
  return pass("구조 라벨", "구조 항목이 라벨과 내용으로 분리되어 있습니다.");
}

function checkDocumentStoryline(slides: PlannedSlide[], meta: DeckMeta): OneShotReadinessCheck {
  const rule = oneShotStructureRules.find((item) => meta.documentType.includes(item.documentType));
  if (!rule) return pass("문서 흐름", "일반 문서 흐름으로 생성합니다.");
  const deckText = slides.map((slide) => `${slide.claimTitle} ${slide.sections.join(" ")} ${slide.archetype.label}`).join(" ");
  const matched = rule.requiredRoles.filter((role) => deckText.includes(role) || roleRelated(role, deckText)).length;
  if (matched < Math.min(3, rule.requiredRoles.length)) return warn("문서 흐름", `${meta.documentType} 핵심 역할(${rule.requiredRoles.join(", ")}) 중 일부가 약합니다.`);
  return pass("문서 흐름", `${meta.documentType}에 필요한 기본 흐름을 포함합니다.`);
}

function roleRelated(role: string, text: string) {
  const aliases: Record<string, RegExp> = {
    "문제 정의": /why|필요|배경|문제|목적/i,
    "고객 가치": /value|효과|기대|개선|가치/i,
    "업무 범위": /scope|범위|과업|대상/i,
    "수행 방법": /method|방법|수행|절차|단계/i,
    "산출물": /deliverable|산출|결과물/i,
    "자료요청": /자료|데이터|요청|증빙/i,
    "담당/기한": /담당|기한|일정|raci|역할/i,
    "의사결정": /의사결정|결정|승인|판단/i
  };
  return aliases[role]?.test(text) ?? false;
}

function pass(label: string, detail: string): OneShotReadinessCheck {
  return { label, detail, status: "pass" };
}

function warn(label: string, detail: string): OneShotReadinessCheck {
  return { label, detail, status: "warn" };
}

function fail(label: string, detail: string): OneShotReadinessCheck {
  return { label, detail, status: "fail" };
}
