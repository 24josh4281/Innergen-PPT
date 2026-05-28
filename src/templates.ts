import type { ArchetypeId, DeckMeta } from "./types";
import { findStandardDeckFlow, getStandardDeckFlowArchetype, type StandardDeckFlowProfile } from "./standardDeckFlow";
import { findReferenceTopNProfile, getReferenceTopNArchetype, type ReferenceTopNProfile } from "./referenceTopN";
import { findReferenceStructureProfile, type ReferenceStructureProfile } from "./referenceStructureDb";

export type TemplateId = "proposal" | "kickoff" | "interim" | "final" | "executive" | "training";
export type BusinessTypeId = "reduction" | "regulatory" | "disclosure";
export type MeetingTypeId = "proposal" | "kickoff" | "interim" | "final" | "review" | "benchmark" | "training" | "design-template";

export interface TemplateProfile {
  id: TemplateId;
  label: string;
  description: string;
  match: string[];
  sequence: ArchetypeId[];
  qualityRules: string[];
}

export interface BusinessMeetingProfile {
  id: string;
  label: string;
  businessType: BusinessTypeId;
  meetingType: MeetingTypeId;
  description: string;
  sequence: ArchetypeId[];
  qualityRules: string[];
}

export const businessTypeOptions: { id: BusinessTypeId; label: string; description: string }[] = [
  { id: "reduction", label: "감축사업", description: "감축량 산정, 방법론, MRV, 인증/검증, 사업화 가능성을 중심으로 구성합니다." },
  { id: "regulatory", label: "규제대응사업", description: "배출권거래제, 목표관리제, 명세서, 산정계획서, 검증 대응을 중심으로 구성합니다." },
  { id: "disclosure", label: "CDP·기후공시사업", description: "CDP, ISSB/TCFD, 기후리스크, 공시 데이터, 답변·증빙 체계를 중심으로 구성합니다." }
];

export const meetingTypeOptions: { id: MeetingTypeId; label: string; description: string }[] = [
  { id: "proposal", label: "제안서", description: "입찰, 제안, 과업 범위, 차별화 포인트, 산출물을 설득형 흐름으로 구성합니다." },
  { id: "kickoff", label: "착수회의", description: "목표, 범위, 일정, 자료 요청, 협업 방식을 정렬합니다." },
  { id: "interim", label: "중간보고", description: "진행 현황, 이슈, 의사결정, 다음 조치를 압축합니다." },
  { id: "final", label: "최종보고", description: "결과, 근거, 시사점, 로드맵을 완결 구조로 정리합니다." },
  { id: "review", label: "검토 회의", description: "검토 쟁점, 보완 요청, 의사결정 사항, 후속 조치를 정리합니다." }
];

const businessMeetingProfiles: BusinessMeetingProfile[] = [
  profile("reduction-kickoff", "감축사업 착수회의", "reduction", "kickoff", "감축사업의 경계, 방법론, MRV, 자료 요청을 초기에 고정합니다.", [
    "consulting-executive-summary",
    "inventory-boundary-flow",
    "integrated-process-map",
    "reduction-roadmap-analysis",
    "data-request-tracker",
    "assurance-evidence-pack",
    "schedule-gantt",
    "communication-management"
  ]),
  profile("reduction-interim", "감축사업 중간보고", "reduction", "interim", "감축량 산정 가정, 데이터 이슈, 방법론 보완사항을 의사결정 중심으로 정리합니다.", [
    "dashboard-kpi-takeaway",
    "waterfall-bridge-analysis",
    "issue-tree-to-workplan",
    "comparison-matrix",
    "assurance-evidence-pack",
    "evidence-to-action-strip"
  ]),
  profile("reduction-final", "감축사업 최종보고", "reduction", "final", "최종 감축량, 산정 논리, 인증 가능성, 사업화 로드맵을 제시합니다.", [
    "consulting-executive-summary",
    "impact-factoid-big-number",
    "waterfall-bridge-analysis",
    "integrated-process-map",
    "reduction-roadmap-analysis",
    "evidence-to-action-strip"
  ]),
  profile("reduction-review", "감축사업 검토 회의", "reduction", "review", "산정식, 경계, 보수성, 증빙 쟁점을 빠르게 검토하고 보완 조치를 확정합니다.", [
    "consulting-one-page-memo",
    "inventory-boundary-flow",
    "comparison-matrix",
    "assurance-evidence-pack",
    "evidence-to-action-strip"
  ]),
  profile("regulatory-kickoff", "규제대응 착수회의", "regulatory", "kickoff", "명세서·산정계획서·검증 대응을 일정, 자료, 책임 기준으로 정렬합니다.", [
    "consulting-executive-summary",
    "regulatory-timeline-radar",
    "proposal-scope-integrated",
    "data-request-tracker",
    "assurance-evidence-pack",
    "schedule-gantt",
    "communication-management"
  ]),
  profile("regulatory-interim", "규제대응 중간보고", "regulatory", "interim", "자료 취합 현황, 오류 유형, 검증 리스크, 제출 준비도를 점검합니다.", [
    "traffic-light-scorecard",
    "data-request-tracker",
    "issue-tree-to-workplan",
    "assurance-evidence-pack",
    "communication-management",
    "evidence-to-action-strip"
  ]),
  profile("regulatory-final", "규제대응 최종보고", "regulatory", "final", "제출본, 검증 결과, 잔여 리스크, 차기 대응 과제를 정리합니다.", [
    "consulting-executive-summary",
    "traffic-light-scorecard",
    "before-after-delta-bridge",
    "assurance-evidence-pack",
    "report-production-workflow",
    "evidence-to-action-strip"
  ]),
  profile("regulatory-review", "규제대응 검토 회의", "regulatory", "review", "명세서/산정계획서의 쟁점, 보완자료, 제출 리스크를 검토합니다.", [
    "consulting-one-page-memo",
    "data-request-tracker",
    "assurance-evidence-pack",
    "comparison-matrix",
    "evidence-to-action-strip"
  ]),
  profile("disclosure-kickoff", "CDP·기후공시 착수회의", "disclosure", "kickoff", "공시 범위, 문항, 데이터 소유자, 증빙 체계를 초기에 설계합니다.", [
    "consulting-executive-summary",
    "disclosure-taxonomy-map",
    "cdp-response-strategy",
    "data-request-tracker",
    "tcfd-pillar-diagnosis",
    "schedule-gantt",
    "communication-management"
  ]),
  profile("disclosure-interim", "CDP·기후공시 중간보고", "disclosure", "interim", "문항별 진척, Gap, 증빙 부족, 답변 품질을 점검합니다.", [
    "dashboard-kpi-takeaway",
    "tcfd-pillar-diagnosis",
    "score-improvement-levers",
    "evidence-grid",
    "issue-tree-to-workplan",
    "evidence-to-action-strip"
  ]),
  profile("disclosure-final", "CDP·기후공시 최종보고", "disclosure", "final", "최종 답변, 공시 메시지, 개선 과제, 차년도 운영 체계를 정리합니다.", [
    "consulting-executive-summary",
    "score-improvement-levers",
    "before-after-delta-bridge",
    "disclosure-taxonomy-map",
    "asis-tobe-gap-roadmap",
    "evidence-to-action-strip"
  ]),
  profile("disclosure-review", "CDP·기후공시 검토 회의", "disclosure", "review", "문항 해석, 답변 논리, 증빙 적합성, 보완 조치를 빠르게 확정합니다.", [
    "consulting-one-page-memo",
    "cdp-response-strategy",
    "evidence-grid",
    "comparison-matrix",
    "evidence-to-action-strip"
  ])
];

function profile(
  id: string,
  label: string,
  businessType: BusinessTypeId,
  meetingType: MeetingTypeId,
  description: string,
  sequence: ArchetypeId[]
): BusinessMeetingProfile {
  return {
    id,
    label,
    businessType,
    meetingType,
    description,
    sequence,
    qualityRules: ["사업 유형과 회의 목적에 맞는 구조 사용", "동일 카드 반복 금지", "의사결정 메시지와 실행 조치 연결"]
  };
}

export const templateProfiles: TemplateProfile[] = [
  {
    id: "proposal",
    label: "컨설팅 제안서",
    description: "고객의 문제를 정의하고, 수행 범위·방법론·산출물을 설득형 흐름으로 제시합니다.",
    match: ["제안", "proposal", "입찰", "tender", "rfp"],
    sequence: [
      "why-what-how-logic",
      "proposal-need-three-cards",
      "proposal-scope-integrated",
      "method-chevron",
      "work-scope-table",
      "team-management",
      "schedule-gantt",
      "evidence-to-action-strip"
    ],
    qualityRules: ["첫 3장은 문제-가치-해법 흐름을 유지", "과업과 산출물을 반드시 연결", "고객 가치 문장을 하단 implication에 배치"]
  },
  {
    id: "kickoff",
    label: "착수보고",
    description: "프로젝트 착수 시점의 목표, 범위, 일정, 자료 요청, 협업 방식을 정렬합니다.",
    match: ["착수", "kickoff", "kick-off", "수행계획", "개시"],
    sequence: [
      "consulting-executive-summary",
      "proposal-scope-integrated",
      "method-chevron",
      "data-request-tracker",
      "team-management",
      "communication-management",
      "schedule-gantt",
      "assurance-evidence-pack"
    ],
    qualityRules: ["역할·일정·자료 요청을 분리", "고객이 바로 실행할 수 있는 next action 명시", "검토 마일스톤 중심으로 일정 표현"]
  },
  {
    id: "interim",
    label: "중간보고",
    description: "현재까지의 진행, 발견 이슈, 의사결정 필요사항, 향후 조치를 압축합니다.",
    match: ["중간", "interim", "progress", "진척", "현황"],
    sequence: [
      "dashboard-kpi-takeaway",
      "traffic-light-scorecard",
      "issue-tree-to-workplan",
      "evidence-grid",
      "comparison-matrix",
      "communication-management",
      "evidence-to-action-strip"
    ],
    qualityRules: ["현황보다 해석을 먼저 제시", "이슈와 조치를 같은 장표에서 연결", "의사결정 필요사항을 분리 표시"]
  },
  {
    id: "final",
    label: "최종보고",
    description: "결과, 근거, 시사점, 실행 로드맵을 임원도 이해할 수 있는 완결 구조로 정리합니다.",
    match: ["최종", "final", "완료", "결과", "성과"],
    sequence: [
      "consulting-executive-summary",
      "impact-factoid-big-number",
      "before-after-delta-bridge",
      "benchmark-readiness-summary",
      "asis-tobe-gap-roadmap",
      "reduction-roadmap-analysis",
      "evidence-to-action-strip"
    ],
    qualityRules: ["결론을 첫 장에 선명하게 배치", "숫자는 단위와 기준기간 표시", "향후 실행 과제를 마지막에 정리"]
  },
  {
    id: "executive",
    label: "임원보고",
    description: "핵심 의사결정에 필요한 결론, 영향, 선택지를 짧고 강하게 제시합니다.",
    match: ["임원", "executive", "ceo", "cfo", "의사결정", "보고"],
    sequence: [
      "consulting-executive-summary",
      "impact-factoid-big-number",
      "double-materiality-or-risk-map",
      "comparison-matrix",
      "evidence-to-action-strip"
    ],
    qualityRules: ["한 장표 한 메시지 유지", "선택지와 추천안을 분리", "세부 근거는 Appendix로 이동"]
  },
  {
    id: "training",
    label: "교육자료",
    description: "학습자가 이해해야 할 개념, 절차, 실습, 체크리스트를 순차적으로 제시합니다.",
    match: ["교육", "training", "워크숍", "세미나", "agenda"],
    sequence: [
      "training-curriculum-agenda",
      "why-what-how-logic",
      "method-chevron",
      "case-study-good-practice",
      "traffic-light-scorecard",
      "evidence-to-action-strip"
    ],
    qualityRules: ["개념 설명보다 학습 질문 중심", "실습 산출물을 명확히 표시", "체크리스트는 5개 이하로 유지"]
  }
];

const fallbackProfile = templateProfiles[0];

export function getTemplateProfile(meta: DeckMeta): TemplateProfile {
  const context = `${meta.documentType ?? ""} ${meta.purpose ?? ""} ${meta.audience ?? ""} ${meta.tone ?? ""}`.toLowerCase();
  const matched = templateProfiles.find((profile) => profile.match.some((keyword) => context.includes(keyword.toLowerCase())));
  return matched ?? fallbackProfile;
}

export function getTemplateArchetype(meta: DeckMeta, slideIndex: number): ArchetypeId | undefined {
  const standardFlow = getStandardDeckFlowForMeta(meta);
  const standardArchetype = getStandardDeckFlowArchetype(standardFlow, slideIndex);
  if (standardArchetype) return standardArchetype;

  const topNProfile = getReferenceTopNProfileForMeta(meta);
  const topNArchetype = getReferenceTopNArchetype(topNProfile, slideIndex);
  if (topNArchetype) return topNArchetype;

  const referenceProfile = getReferenceStructureProfileForMeta(meta);
  if (referenceProfile) return referenceProfile.sequence[slideIndex - 1] ?? referenceProfile.sequence.at(-1);

  const businessMeetingProfile = getBusinessMeetingProfile(meta);
  if (businessMeetingProfile) return businessMeetingProfile.sequence[slideIndex - 1] ?? businessMeetingProfile.sequence.at(-1);

  const profile = getTemplateProfile(meta);
  return profile.sequence[slideIndex - 1] ?? profile.sequence.at(-1);
}

export function getBusinessMeetingProfile(meta: DeckMeta): BusinessMeetingProfile | undefined {
  const businessType = normalizeBusinessType(meta.businessType);
  const meetingType = normalizeMeetingType(meta.meetingType ?? meta.documentType);
  if (!businessType || !meetingType) return undefined;
  const standardFlow = findStandardDeckFlow(businessType, meetingType);
  if (standardFlow) {
    return {
      id: standardFlow.id,
      label: standardFlow.label,
      businessType,
      meetingType,
      description: `${standardFlow.recommendedSlideCount}장 권장 표준 흐름입니다: ${standardFlow.rhythm}`,
      sequence: standardFlow.standardSequence,
      qualityRules: standardFlow.generationRules
    };
  }
  const topNProfile = findReferenceTopNProfile(businessType, meetingType);
  if (topNProfile) {
    return {
      id: topNProfile.id,
      label: topNProfile.label,
      businessType,
      meetingType,
      description: `${topNProfile.totalFiles}개 승인 레퍼런스 파일과 ${topNProfile.totalSlides}개 승인 샘플 슬라이드에서 도출한 대표 구조입니다.`,
      sequence: topNProfile.representativeSequence,
      qualityRules: topNProfile.generationRules
    };
  }
  const referenceProfile = findReferenceStructureProfile(businessType, meetingType);
  if (referenceProfile) {
    return {
      id: referenceProfile.id,
      label: referenceProfile.label,
      businessType,
      meetingType,
      description: referenceProfile.description,
      sequence: referenceProfile.sequence,
      qualityRules: referenceProfile.qaRules
    };
  }
  return businessMeetingProfiles.find((profile) => profile.businessType === businessType && profile.meetingType === meetingType);
}

export function getReferenceStructureProfileForMeta(meta: DeckMeta): ReferenceStructureProfile | undefined {
  const businessType = normalizeBusinessType(meta.businessType);
  const meetingType = normalizeMeetingType(meta.meetingType ?? meta.documentType);
  return findReferenceStructureProfile(businessType, meetingType);
}

export function getReferenceTopNProfileForMeta(meta: DeckMeta): ReferenceTopNProfile | undefined {
  const businessType = normalizeBusinessType(meta.businessType);
  const meetingType = normalizeMeetingType(meta.meetingType ?? meta.documentType);
  return findReferenceTopNProfile(businessType, meetingType);
}

export function getStandardDeckFlowForMeta(meta: DeckMeta): StandardDeckFlowProfile | undefined {
  const businessType = normalizeBusinessType(meta.businessType);
  const meetingType = normalizeMeetingType(meta.meetingType ?? meta.documentType);
  return findStandardDeckFlow(businessType, meetingType);
}

export function normalizeBusinessType(value?: string): BusinessTypeId | undefined {
  const text = (value ?? "").toLowerCase();
  if (/감축|reduction|mrv|방법론|carbon project/.test(text)) return "reduction";
  if (/규제|ets|배출권|명세서|산정계획|인벤토리|inventory|regulatory|allowance/.test(text)) return "regulatory";
  if (/cdp|공시|tcfd|issb|기후공시|disclosure|climate/.test(text)) return "disclosure";
  return undefined;
}

export function normalizeMeetingType(value?: string): MeetingTypeId | undefined {
  const text = (value ?? "").toLowerCase();
  if (/제안|proposal|입찰|tender|rfp/.test(text)) return "proposal";
  if (/착수|kickoff|kick-off|개시/.test(text)) return "kickoff";
  if (/중간|interim|progress|현황/.test(text)) return "interim";
  if (/최종|final|완료|결과/.test(text)) return "final";
  if (/검토|review|회의|쟁점/.test(text)) return "review";
  if (/교육|training|세미나|seminar/.test(text)) return "training";
  if (/benchmark|벤치마크|참고|레퍼런스/.test(text)) return "benchmark";
  return undefined;
}
