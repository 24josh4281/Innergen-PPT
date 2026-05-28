import type { ArchetypeId, DeckMeta } from "./types";
import type { BusinessTypeId, MeetingTypeId } from "./templates";

export interface ReferenceStructureProfile {
  id: string;
  label: string;
  description: string;
  businessType: BusinessTypeId;
  meetingType: MeetingTypeId;
  referenceDeck: string;
  sourceFileIds: string[];
  referenceSlideMap: Record<number, number>;
  sequence: ArchetypeId[];
  densityPolicy: {
    target: "medium-high" | "high";
    sparseSlideAction: string;
    minimumBodyFillRatio: number;
  };
  qaRules: string[];
}

export const referenceStructureProfiles: ReferenceStructureProfile[] = [
  {
    id: "reduction-kickoff-starstech",
    label: "감축사업 착수/방법론 보고형",
    description: "스타스테크 감축방법론 레퍼런스처럼 브랜드 크롬, 프로세스, 평가표, 산정식, 향후 일정 중심으로 구성합니다.",
    businessType: "reduction",
    meetingType: "kickoff",
    referenceDeck: "starstech-methodology-reference",
    sourceFileIds: [
      "starstech_methodology_260410",
      "newrizen_filter_methodology_260203",
      "newrizen_filter_methodology_260406",
      "samsung_ds_reduction_methodology_240909",
      "innergen_semiconductor_scope3_methodology_240724",
      "jb_re100_kickoff",
      "jb_re100_w2",
      "renewable_energy_new_business",
      "reduction_kickoff",
      "reduction_kickoff_2",
      "reduction_methodology_report",
      "reduction_methodology_report_2",
      "reduction_methodology_report_3"
    ],
    referenceSlideMap: {
      1: 1,
      2: 2,
      3: 3,
      4: 4,
      5: 5,
      6: 7,
      7: 8,
      8: 12,
      9: 12,
      10: 13,
      11: 20,
      12: 9
    },
    sequence: [
      "cover-kickoff",
      "integrated-process-map",
      "contents-isometric",
      "comparison-matrix",
      "work-scope-table",
      "consulting-one-page-memo",
      "comparison-matrix",
      "inventory-boundary-flow",
      "reduction-roadmap-analysis",
      "impact-factoid-big-number",
      "data-request-tracker",
      "schedule-gantt"
    ],
    densityPolicy: {
      target: "high",
      sparseSlideAction: "글자가 적으면 빈 카드가 아니라 큰 표, 단계 카드, 결론 밴드, 수식/흐름도를 확장해 본문 면적을 채웁니다.",
      minimumBodyFillRatio: 0.16
    },
    qaRules: [
      "상단 네이비 격자 헤더와 하단 네이비 격자 푸터를 유지합니다.",
      "표/도형은 본문 영역의 70% 이상을 사용하고, 빈 박스 안에 작은 글자만 두지 않습니다.",
      "각 본문 슬라이드는 제목 아래에 굵은 섹션 라벨 또는 governing message를 둡니다.",
      "요약형 카드가 비어 보이면 단계 카드, 비교표, 산정식 블록, 결론 밴드 중 하나로 전환합니다."
    ]
  },
  {
    id: "reduction-final-methodology",
    label: "감축사업 최종보고형",
    description: "최종 감축량, 산정 근거, 검증 대응, 등록 로드맵을 큰 숫자와 근거 표 중심으로 제시합니다.",
    businessType: "reduction",
    meetingType: "final",
    referenceDeck: "starstech-methodology-reference",
    sourceFileIds: [
      "starstech_methodology_260410",
      "research_final_report_public",
      "research_evaluation_report",
      "mbi_selangor_tender_briefing_carbon",
      "reduction_methodology_report",
      "reduction_methodology_report_2",
      "reduction_methodology_report_3",
      "reduction_proposal",
      "reduction_proposal_pdf"
    ],
    referenceSlideMap: { 1: 1, 2: 4, 3: 9, 4: 12, 5: 13, 6: 20, 7: 22, 8: 24 },
    sequence: [
      "cover-kickoff",
      "consulting-executive-summary",
      "impact-factoid-big-number",
      "reduction-roadmap-analysis",
      "assurance-evidence-pack",
      "schedule-gantt",
      "evidence-to-action-strip"
    ],
    densityPolicy: {
      target: "high",
      sparseSlideAction: "핵심 숫자와 결론 밴드를 크게 배치하고, 상세 근거는 표로 하단을 채웁니다.",
      minimumBodyFillRatio: 0.15
    },
    qaRules: [
      "최종 결론을 1장 앞쪽에 배치합니다.",
      "수치에는 단위와 기준기간을 함께 표기합니다.",
      "검증/등록 잔여 리스크를 action table로 정리합니다."
    ]
  },
  {
    id: "regulatory-review-evidence",
    label: "규제대응 검토회의형",
    description: "명세서·산정계획서·검증 대응 쟁점을 자료 요청, 상태, 보완 조치 중심으로 정리합니다.",
    businessType: "regulatory",
    meetingType: "review",
    referenceDeck: "innergen-regulatory-review",
    sourceFileIds: [
      "sk_siltron_ghg_inventory_kickoff",
      "sk_tcfd_project_share_220603",
      "sk_tcfd_training_220603",
      "regulatory_kickoff",
      "regulatory_final",
      "ghg_inventory_kickoff",
      "ghg_inventory_final",
      "ghg_inventory_final_2",
      "ghg_inventory_proposal",
      "ghg_inventory_proposal_v2"
    ],
    referenceSlideMap: { 1: 1, 2: 2, 3: 4, 4: 6, 5: 9, 6: 12 },
    sequence: [
      "consulting-one-page-memo",
      "traffic-light-scorecard",
      "data-request-tracker",
      "assurance-evidence-pack",
      "comparison-matrix",
      "evidence-to-action-strip"
    ],
    densityPolicy: {
      target: "medium-high",
      sparseSlideAction: "상태표와 요청자료 표를 확대하고, 각 이슈별 담당·기한·보완사항을 함께 채웁니다.",
      minimumBodyFillRatio: 0.13
    },
    qaRules: [
      "검토/산출/관리 같은 단어형 라벨은 한 줄로 유지합니다.",
      "상태표 셀 내부 텍스트는 중앙 정렬하고 충분한 폭을 확보합니다.",
      "오류·누락·보완 조치는 색상만이 아니라 텍스트로도 설명합니다."
    ]
  },
  {
    id: "disclosure-interim-score",
    label: "CDP·기후공시 중간보고형",
    description: "문항별 진행률, 증빙 확보 현황, 점수 개선 레버를 컨설팅식 scorecard와 action table로 구성합니다.",
    businessType: "disclosure",
    meetingType: "interim",
    referenceDeck: "consulting-disclosure-reference",
    sourceFileIds: [
      "hyundai_transys_sbti_cdp_climate_risk_proposal",
      "deloitte_daewoo_sustainability_cdp_proposal",
      "ecovadis_esg_proposal",
      "kakao_cdp_scope3_proposal",
      "ey_sk_chemical_tcfd",
      "pwc_tnfd_standard_strategy",
      "pwc_csrd_disclosure_response",
      "deloitte_insurance_csrd_benchmark_2024",
      "cdp_proposal",
      "cdp_proposal_2",
      "cdp_proposal_3",
      "cdp_kickoff",
      "cdp_final",
      "cdp_final_2"
    ],
    referenceSlideMap: { 1: 1, 2: 3, 3: 5, 4: 8, 5: 10, 6: 12 },
    sequence: [
      "dashboard-kpi-takeaway",
      "tcfd-pillar-diagnosis",
      "score-improvement-levers",
      "evidence-grid",
      "issue-tree-to-workplan",
      "evidence-to-action-strip"
    ],
    densityPolicy: {
      target: "medium-high",
      sparseSlideAction: "점수, 문항, 증빙, 담당 부서 정보를 한 장 안에서 연결해 빈 카드 반복을 피합니다.",
      minimumBodyFillRatio: 0.13
    },
    qaRules: [
      "governing message는 점수 영향 또는 의사결정 포인트로 씁니다.",
      "문항 설명은 짧게, 증빙/담당/기한은 표로 정리합니다.",
      "동일 카드 레이아웃을 2장 이상 연속 사용하지 않습니다."
    ]
  }
];

export function findReferenceStructureProfile(
  businessType: BusinessTypeId | undefined,
  meetingType: MeetingTypeId | undefined
): ReferenceStructureProfile | undefined {
  if (!businessType || !meetingType) return undefined;
  return referenceStructureProfiles.find((profile) => profile.businessType === businessType && profile.meetingType === meetingType);
}

export function slideMapToString(profile: ReferenceStructureProfile | undefined): string {
  if (!profile) return "";
  return Object.entries(profile.referenceSlideMap)
    .map(([candidate, reference]) => `${candidate}:${reference}`)
    .join(",");
}

export function describeReferenceProfile(profile: ReferenceStructureProfile | undefined): string[] {
  if (!profile) return [];
  return [
    `레퍼런스 구조: ${profile.label}`,
    `레퍼런스 deck: ${profile.referenceDeck}`,
    `Reference source IDs: ${profile.sourceFileIds.join(", ")}`,
    `본문 밀도 목표: ${profile.densityPolicy.target}, 최소 fill ratio ${profile.densityPolicy.minimumBodyFillRatio}`,
    `여백 보정: ${profile.densityPolicy.sparseSlideAction}`,
    `QA slide map: ${slideMapToString(profile)}`
  ];
}

export function summarizeReferenceProfileForPrompt(meta: DeckMeta, profile: ReferenceStructureProfile | undefined): string[] {
  if (!profile) return [`레퍼런스 구조 DB 매칭 없음: ${meta.businessType ?? ""} / ${meta.meetingType ?? ""}`];
  return [
    ...describeReferenceProfile(profile),
    "참조 소스는 구조, 슬라이드 형식, 논리 흐름, 증거 배치 방식만 참고하고, INNerGEN BI 색상과 폰트는 유지합니다.",
    "로고 정책: INNerGEN 외 기업/컨설팅사/고객사 로고와 브랜드 마크는 절대 복제하거나 재사용하지 않습니다.",
    "반복 금지: 같은 카드형 레이아웃을 2장 이상 연속 사용하지 말고, 표/흐름도/산정식/일정표를 내용 성격에 맞춰 교차 적용합니다.",
    "레퍼런스 QA 규칙:",
    ...profile.qaRules.map((rule) => `- ${rule}`)
  ];
}
