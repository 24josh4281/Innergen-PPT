import type { ArchetypeId, DeckMeta } from "./types";

export type TemplateId = "proposal" | "kickoff" | "interim" | "final" | "executive" | "training";

export interface TemplateProfile {
  id: TemplateId;
  label: string;
  description: string;
  match: string[];
  sequence: ArchetypeId[];
  qualityRules: string[];
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
  const profile = getTemplateProfile(meta);
  return profile.sequence[slideIndex - 1] ?? profile.sequence.at(-1);
}
