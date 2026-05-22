import { archetypeRules } from "./patterns";
import type { ArchetypeId } from "./types";

export interface LayoutSample {
  title: string;
  bullets: string[];
  governingHint?: string;
}

export interface LayoutFamily {
  id: string;
  label: string;
  renderGroup: string;
  archetypes: ArchetypeId[];
  sample: LayoutSample;
  qaRules: string[];
}

export const layoutFamilies: LayoutFamily[] = [
  {
    id: "message-cards",
    label: "Message Cards",
    renderGroup: "cards",
    archetypes: ["consulting-executive-summary", "why-what-how-logic", "proposal-need-three-cards"],
    sample: {
      title: "경영진 의사결정 요약",
      bullets: [
        "핵심 판단: 공시 대응은 배출량 산정, 증빙 관리, 제출 QA를 하나의 체계로 통합해야 합니다.",
        "근거: 기준연도와 조직경계가 늦게 확정되면 SBTi, CDP, 검증 대응 일정이 동시에 지연됩니다.",
        "영향: 자료 중복과 담당 불명확성이 커질수록 제출 전 보완 비용이 증가합니다.",
        "우선 실행: 착수 2주 안에 데이터 소유자와 증빙 위치를 확정합니다."
      ]
    },
    qaRules: ["카드 제목은 12자 내외", "카드 본문은 2줄 이하", "하단 implication은 하나의 결론만 사용"]
  },
  {
    id: "scope-table",
    label: "Scope / Deliverable Table",
    renderGroup: "table",
    archetypes: ["proposal-scope-integrated", "work-scope-table", "data-request-tracker", "assurance-evidence-pack"],
    sample: {
      title: "업무 범위와 산출물 연결",
      bullets: [
        "업무 범위: Scope 1/2/3 인벤토리 검토, CDP 답변 작성, 기후리스크 분석을 포함합니다.",
        "분석 대상: 법인, 사업장, 공급망, 공시 문항, 검증 증빙을 구분합니다.",
        "수행 방법: 자료 취합, 계산 검토, 답변 초안, 내부 QA를 병행합니다.",
        "산출물: 인벤토리 검토 메모, CDP 답변 초안, 증빙 목록, 제출 QA 로그를 제공합니다."
      ]
    },
    qaRules: ["행 높이는 균일하게 유지", "셀 안 문장은 1문장 중심", "산출물과 검토 기준을 분리"]
  },
  {
    id: "process-roadmap",
    label: "Process / Roadmap",
    renderGroup: "process",
    archetypes: ["method-chevron", "sbti-process", "cdp-response-strategy", "climate-scenario-framework", "integrated-process-map", "report-production-workflow", "regulatory-timeline-radar", "funnel-conversion-pipeline"],
    sample: {
      title: "5단계 프로젝트 수행 로드맵",
      bullets: [
        "진단: 기준연도, 조직경계, 데이터 보유 현황을 확인합니다.",
        "설계: 요구사항을 업무 흐름과 산출물 체계로 전환합니다.",
        "실행: 자료 취합, 계산 검토, 답변 작성, 리스크 분석을 병행합니다.",
        "검증: 내부 QA와 고객 검토를 통해 보완 이슈를 정리합니다.",
        "제출: 최종본, 증빙 패키지, 후속 관리 기준을 확정합니다."
      ]
    },
    qaRules: ["단계명은 한 줄 유지", "각 단계에 검토/산출/관리 행 포함", "화살표는 텍스트 뒤로 배치"]
  },
  {
    id: "matrix-diagnosis",
    label: "Matrix / Diagnosis",
    renderGroup: "matrix",
    archetypes: ["benchmark-readiness-summary", "comparison-matrix", "peer-good-practice-benchmark", "double-materiality-or-risk-map", "iro-register-map", "traffic-light-scorecard", "bubble-priority-portfolio", "waterfall-bridge-analysis", "scenario-financial-impact", "before-after-delta-bridge", "forecast-trend-chart"],
    sample: {
      title: "진단 결과와 우선 조치",
      bullets: [
        "평가 기준: 데이터 완전성, 산정 로직, 증빙 추적성, 제출 준비도를 기준으로 봅니다.",
        "현재 수준: 일부 자료는 취합됐지만 담당, 단위, 증빙 위치가 완전히 연결되지 않았습니다.",
        "Gap: 검증 대응에 필요한 원본 링크와 내부 승인 이력이 부족합니다.",
        "우선 조치: 고위험 항목부터 담당자와 보완 기한을 지정합니다."
      ]
    },
    qaRules: ["축과 평가 기준을 명시", "색상만으로 상태를 전달하지 않음", "추천 조치를 우측 패널에 고정"]
  },
  {
    id: "flow-map",
    label: "Flow / Map",
    renderGroup: "flow",
    archetypes: ["inventory-boundary-flow", "reduction-roadmap-analysis", "disclosure-taxonomy-map", "value-chain-hotspot-map", "house-framework", "asis-tobe-gap-roadmap"],
    sample: {
      title: "데이터 흐름과 관리 경계",
      bullets: [
        "경계 설정: 법인, 사업장, 운영통제 범위를 먼저 고정합니다.",
        "원천자료: 전력, 연료, 냉매, 공정가스 자료를 담당 부서별로 취합합니다.",
        "산정 로직: 단위, 배출계수, 계산식을 표준 검토 기준으로 관리합니다.",
        "검증 증빙: 원본 파일, 승인 이력, 제출본을 하나의 증빙 체계로 연결합니다.",
        "관리 기준: 누락, 중복, 단위 오류를 제출 전 단계에서 차단합니다."
      ]
    },
    qaRules: ["선과 박스가 겹치지 않게 배치", "조건 패널은 3개 이하", "계산식보다 흐름을 먼저 보여줌"]
  },
  {
    id: "evidence-action",
    label: "Evidence to Action",
    renderGroup: "memo",
    archetypes: ["consulting-one-page-memo", "evidence-grid", "evidence-to-action-strip", "case-study-good-practice"],
    sample: {
      title: "근거에서 실행 조치로 전환",
      bullets: [
        "근거: 제출 자료의 일부는 원본 출처와 산정 파일이 분리되어 있습니다.",
        "해석: 검증기관 질의가 발생하면 근거 추적 시간이 길어질 수 있습니다.",
        "Gap: 담당자, 자료 위치, 검토 상태가 한 화면에서 확인되지 않습니다.",
        "Action: 증빙 목록과 QA 로그를 연결해 제출 전 검토 체계를 만듭니다."
      ]
    },
    qaRules: ["근거와 해석을 분리", "Action은 동사로 시작", "본문은 5개 bullet 이하"]
  },
  {
    id: "cycle-loop",
    label: "Cycle / Loop",
    renderGroup: "cycle",
    archetypes: ["cycle-loop-pdca"],
    sample: {
      title: "PDCA 기반 상시 관리체계",
      bullets: [
        "Plan: 공시 기준과 요청자료 범위를 확정합니다.",
        "Do: 부서별 데이터를 수집하고 산정 파일에 반영합니다.",
        "Check: 단위, 누락, 중복, 증빙 정합성을 검토합니다.",
        "Act: 보완 요청과 다음 보고기간 개선과제를 반영합니다.",
        "기록: 모든 판단 근거와 변경 이력을 관리합니다."
      ]
    },
    qaRules: ["중앙 기록 객체를 배치", "화살표는 노드 뒤로 배치", "한 단어 라벨은 한 줄 유지"]
  },
  {
    id: "staircase",
    label: "Maturity Staircase",
    renderGroup: "staircase",
    archetypes: ["staircase-maturity-evolution"],
    sample: {
      title: "공시 대응 성숙도 고도화",
      bullets: [
        "현재 단계: 수작업 취합과 사후 검토 중심입니다.",
        "다음 단계: 표준 양식과 담당부서 기반의 정기 취합 체계로 전환합니다.",
        "고도화 단계: 자동 검토 규칙과 증빙팩 관리를 적용합니다.",
        "목표 단계: 평가, 검증, 보고서 제작을 하나의 데이터 체계로 운영합니다.",
        "필요 조건: 기준 정의서, 데이터 룸, 승인 이력, 교육 체계가 필요합니다."
      ]
    },
    qaRules: ["L1, L2 라벨은 한 줄", "단계명은 박스 안 중앙 정렬", "긴 설명은 박스 아래가 아니라 내부에 수용"]
  },
  {
    id: "issue-tree",
    label: "Issue Tree",
    renderGroup: "issue-tree",
    archetypes: ["issue-tree-to-workplan"],
    sample: {
      title: "핵심 이슈를 실행 과제로 분해",
      bullets: [
        "핵심 질문: 제출 가능한 수준의 데이터와 증빙을 확보했는가.",
        "하위 이슈: 기준연도, 조직경계, 배출계수, 증빙 위치가 불명확합니다.",
        "분석 과제: 원천자료와 계산 파일을 대조하고 오류 유형을 분류합니다.",
        "산출물: 이슈 로그, 보완 요청 목록, 제출 전 QA 체크리스트를 제공합니다."
      ]
    },
    qaRules: ["MECE한 이슈 3~4개", "좌측 질문은 짧게", "우측 실행 과제와 산출물을 연결"]
  },
  {
    id: "metric-dashboard",
    label: "Metric / Dashboard",
    renderGroup: "metric",
    archetypes: ["impact-factoid-big-number", "dashboard-kpi-takeaway"],
    sample: {
      title: "핵심 지표 기반 관리 포인트",
      bullets: [
        "72% 자료가 취합됐지만 검증 가능한 증빙 연결률은 더 낮습니다.",
        "미제출 자료는 특정 사업장과 구매 부문에 집중되어 있습니다.",
        "제출 전에는 취합률보다 증빙 연결률과 오류 재발률을 관리해야 합니다.",
        "우선 조치: 고위험 항목부터 담당자와 보완 기한을 확정합니다."
      ]
    },
    qaRules: ["큰 숫자는 단위와 기준기간 표시", "숫자보다 해석을 크게 배치", "KPI와 Action을 연결"]
  },
  {
    id: "governance-learning",
    label: "Governance / Learning",
    renderGroup: "governance",
    archetypes: ["team-management", "communication-management", "score-improvement-levers", "training-curriculum-agenda", "stakeholder-influence-map"],
    sample: {
      title: "운영 거버넌스와 교육 체계",
      bullets: [
        "역할: ESG, 재무, 구매, 사업부의 자료 책임과 검토 책임을 분리합니다.",
        "회의체: 주간 이슈 회의와 월간 의사결정 회의를 구분합니다.",
        "교육: 담당자별 자료 제출 기준과 증빙 보관 기준을 안내합니다.",
        "관리: 결정사항, 요청자료, 오픈 이슈, 후속 조치를 하나의 로그로 관리합니다."
      ]
    },
    qaRules: ["역할과 책임을 같은 셀에 섞지 않음", "회의 목적과 산출물을 연결", "교육은 학습 질문 중심"]
  }
];

export const archetypeSamples: Partial<Record<ArchetypeId, LayoutSample>> = {
  "consulting-executive-summary": {
    title: "경영진 보고 요약",
    bullets: ["핵심 주장: 공시 대응은 배출량, 목표, 리스크, 증빙을 하나의 데이터 체계로 묶어야 합니다.", "근거: 분리 대응 시 동일 자료를 반복 요청하고 검토 기준이 달라집니다.", "영향: 제출 지연과 검증 질의 증가가 동시에 발생할 수 있습니다.", "우선 실행: 착수 단계에서 기준연도, 조직경계, 담당자를 확정합니다."]
  },
  "why-what-how-logic": {
    title: "공시 기준 변화 대응 방향",
    bullets: ["Why: 투자자와 고객사는 정량 데이터와 검증 가능한 증빙을 요구합니다.", "What: 배출량, 목표, 리스크, 거버넌스를 하나의 설명 체계로 정리합니다.", "Who: ESG, 재무, 구매, 사업부의 데이터 책임을 명확히 나눕니다.", "How: 원천자료, 산정 파일, 승인 이력, 제출본을 연결합니다.", "So what: 제출 전 QA 시간을 줄이고 검증 대응력을 높입니다."]
  },
  "proposal-need-three-cards": {
    title: "통합 자문 추진 필요성",
    bullets: ["규제 요구: 공시 기준과 평가기관의 증빙 요구가 확대되고 있습니다.", "이해관계자 요구: 고객사와 투자자는 비교 가능한 데이터와 관리 체계를 요구합니다.", "내부 대응: 중복 작업을 줄이고 제출 일정을 안정화해야 합니다.", "결론: SBTi, CDP, 기후리스크를 통합 흐름으로 운영해야 합니다."]
  },
  "proposal-scope-integrated": {
    title: "통합 수행 범위",
    bullets: ["업무 범위: GHG 인벤토리, SBTi, CDP, 기후리스크 대응을 포함합니다.", "분석 대상: 법인, 사업장, 공급망, 공시 문항, 검증 증빙을 구분합니다.", "수행 방법: 자료 취합, 계산 검토, 답변 작성, 제출 QA를 병행합니다.", "산출물: 검토 메모, 답변 초안, 증빙 목록, QA 로그를 제공합니다."]
  },
  "benchmark-readiness-summary": {
    title: "공시 대응 준비도 진단",
    bullets: ["비교 기준: 데이터 완전성, 산정 로직, 증빙 추적성, 제출 준비도를 평가합니다.", "현재 수준: 일부 자료는 취합됐지만 담당과 증빙 위치가 연결되지 않았습니다.", "Gap: 검증 대응에 필요한 원본 링크와 승인 이력이 부족합니다.", "우선 조치: 고위험 항목부터 보완 담당자와 기한을 지정합니다."]
  },
  "double-materiality-or-risk-map": {
    title: "기후 리스크 우선순위 맵",
    bullets: ["평가 기준: 재무 영향도와 대응 시급성을 기준으로 리스크를 구분합니다.", "주요 이슈: 에너지 비용, 공급망 규제, 고객 요구, 물리적 피해 가능성이 확인됩니다.", "우선 영역: 비용 영향과 대응 시급성이 모두 높은 항목을 선별합니다.", "대응 방향: 정량화 가능한 근거와 실행 부서를 먼저 연결합니다."]
  },
  "issue-tree-to-workplan": {
    title: "검증 대응 이슈트리",
    bullets: ["핵심 질문: 제출 가능한 수준의 데이터와 증빙을 확보했는가.", "하위 이슈: 기준연도, 조직경계, 배출계수, 증빙 위치가 불명확합니다.", "분석 과제: 원천자료와 계산 파일을 대조하고 오류 유형을 분류합니다.", "산출물: 이슈 로그, 보완 요청 목록, 제출 전 QA 체크리스트를 제공합니다."]
  },
  "tcfd-pillar-diagnosis": {
    title: "TCFD 4대 축 진단",
    bullets: ["Governance: 이사회와 경영진 보고 체계를 확인합니다.", "Strategy: 물리/전환 리스크가 사업 전략에 미치는 영향을 정리합니다.", "Risk Management: 리스크 식별, 평가, 관리 프로세스를 연결합니다.", "Metrics & Targets: 배출량, 감축목표, 리스크 지표를 공시 체계로 묶습니다."]
  },
  "scenario-financial-impact": {
    title: "시나리오별 재무 영향 경로",
    bullets: ["시나리오: 기준, 강화, 고위험 시나리오를 구분합니다.", "영향 경로: 탄소가격, 전력단가, 공급망 비용, 매출 리스크를 연결합니다.", "재무/운영 영향: 비용 증가, 투자 필요, 고객 요구 대응 부담을 산정합니다.", "대응 전략: 민감도가 높은 항목부터 관리지표와 실행 과제를 설정합니다."]
  },
  "sbti-process": {
    title: "SBTi 검증 대응 프로세스",
    bullets: ["진단: 기준연도, 조직경계, Scope 3 범주와 데이터 보유 현황을 확인합니다.", "목표 개발: 감축경로, 기준연도 재산정, 목표 범위를 정리합니다.", "제출/검증: Target Submission Form과 검증 질의 대응 논리를 준비합니다.", "공개/관리: 승인 이후 공개 문구와 연간 관리 체계를 정비합니다."]
  },
  "cdp-response-strategy": {
    title: "CDP 응답 고도화 전략",
    bullets: ["문항 분석: 점수 영향이 큰 문항과 필수 증빙을 먼저 분류합니다.", "자료 수집: 부서별 원천자료와 답변 근거를 연결합니다.", "답변 작성: 정량 수치와 정책 문구를 문항별 논리로 정리합니다.", "제출/보완: ORS 제출 전 오류, 누락, 불일치를 점검합니다."]
  },
  "climate-scenario-framework": {
    title: "기후 시나리오 분석 프레임워크",
    bullets: ["준비: 분석 범위, 기준연도, 사업장, 자산 목록을 확정합니다.", "설계: 물리 리스크와 전환 리스크의 시나리오를 정의합니다.", "분석: 재무 영향, 운영 영향, 민감도 결과를 도출합니다.", "내재화: 공시 문구, 리스크 관리, 투자 의사결정에 연결합니다."]
  },
  "method-chevron": {
    title: "프로젝트 수행 방법론",
    bullets: ["진단: 기준연도, 조직경계, 데이터 보유 현황을 확인합니다.", "설계: 요구사항을 업무 흐름과 산출물 체계로 전환합니다.", "실행: 자료 취합, 계산 검토, 답변 작성, 리스크 분석을 병행합니다.", "검증: 내부 QA와 고객 검토를 통해 보완 이슈를 정리합니다."]
  },
  "integrated-process-map": {
    title: "감축 방법론 개발 절차",
    bullets: ["타당성: 사업 경계, 베이스라인, 추가성, 데이터 가용성을 확인합니다.", "방법론/PDD: 산정식, 모니터링 계획, 보수성 기준을 문서화합니다.", "검증: 제3자 검증기관 질의와 보완 이슈를 관리합니다.", "제출/인증: 제출본, 증빙팩, 승인 이력을 연결합니다.", "MRV: 모니터링, 보고, 검증 운영 기준을 확정합니다."]
  },
  "inventory-boundary-flow": {
    title: "조직경계와 산정 흐름",
    bullets: ["경계 설정: 법인, 사업장, 운영통제 범위를 먼저 고정합니다.", "Baseline: 기준연도 배출량과 재산정 조건을 정리합니다.", "Project: 산정 대상 활동자료와 배출계수를 연결합니다.", "Leakage: 누락 가능성과 중복 산정 위험을 점검합니다.", "조건: 제출 전 단위, 증빙, 승인 이력을 확인합니다."]
  },
  "reduction-roadmap-analysis": {
    title: "감축량 산정 로직",
    bullets: ["산정식: 활동자료와 배출계수를 기준으로 감축량을 산정합니다.", "모니터링: 계측자료, 청구서, 운영기록의 수집 주기를 정합니다.", "모델링: 기준선과 프로젝트 배출량의 차이를 계산합니다.", "보수성: 불확실성이 큰 항목은 보수적 가정을 적용합니다.", "데이터: 원천 파일, 계산 파일, 검토 로그를 연결합니다."]
  },
  "schedule-gantt": {
    title: "프로젝트 추진 일정",
    bullets: ["업무: 진단, 자료 취합, 분석, 검토, 제출 준비를 구분합니다.", "기간: 각 업무의 수행 기간과 고객 검토 기간을 분리합니다.", "마일스톤: 착수, 중간보고, 검토회의, 최종보고 일정을 고정합니다.", "검토: 제출 전 QA와 보완 반영 시간을 별도로 확보합니다."]
  },
  "team-management": {
    title: "프로젝트 역할분담",
    bullets: ["역할: PM, 분석 담당, 데이터 담당, 고객 검토자를 구분합니다.", "담당: ESG, 재무, 구매, 사업부별 자료 책임을 지정합니다.", "책임: 원천자료 제공, 계산 검토, 답변 승인 책임을 분리합니다.", "관리 방식: 주간 이슈 회의와 결정 로그로 진행 상황을 추적합니다."]
  },
  "communication-management": {
    title: "회의체와 의사결정 로그",
    bullets: ["결정사항: 기준연도, 조직경계, 제출 범위를 회의별로 확정합니다.", "요청자료: 신규 요청과 보완 요청을 구분해 관리합니다.", "담당: 자료 소유자와 검토 책임자를 함께 지정합니다.", "기한: 제출 전 검토 가능 일정을 기준으로 역산합니다."]
  },
  "evidence-grid": {
    title: "검증 근거 패널",
    bullets: ["근거 1: 원천자료와 산정 파일의 연결성을 확인합니다.", "근거 2: 단위와 배출계수 적용 기준을 점검합니다.", "근거 3: 내부 승인 이력과 최종 제출본을 대조합니다.", "근거 4: 보완 요청과 반영 결과를 QA 로그로 관리합니다."]
  },
  "work-scope-table": {
    title: "업무 범위 상세표",
    bullets: ["업무: 배출량 산정 검토, CDP 답변, 리스크 분석, 보고서화를 수행합니다.", "대상: 사업장, 법인, 공급망, 공시 문항, 검증 증빙을 포함합니다.", "방법: 자료 대조, 기준 검토, 문항 분석, 제출 전 QA를 적용합니다.", "산출물: 검토 결과표, 보완 요청 목록, 최종 답변, 증빙팩을 제공합니다."]
  },
  "comparison-matrix": {
    title: "대안 비교와 추천안",
    bullets: ["옵션: 내부 자체 대응, 부분 자문, 통합 자문을 비교합니다.", "장점: 통합 자문은 일정, 품질, 증빙 관리 일관성이 높습니다.", "제약: 초기 자료 정리와 부서 협조가 선행되어야 합니다.", "추천: 제출 리스크가 큰 경우 통합 대응 체계가 적합합니다."]
  },
  "consulting-one-page-memo": {
    title: "검토 메모 요약",
    bullets: ["질문: 현재 자료 체계로 제출과 검증 대응이 가능한가.", "근거: 일부 원천자료는 산정 파일과 연결되지 않았습니다.", "판단: 제출 전 증빙팩과 QA 로그를 먼저 정비해야 합니다.", "잔여 리스크: 담당자 변경과 자료 누락 가능성을 관리해야 합니다."]
  },
  "regulatory-timeline-radar": {
    title: "규제 일정과 대응 과제",
    bullets: ["이벤트: 공시 기준 개정, 평가 제출, 검증 대응 일정이 중첩됩니다.", "대상: 법인, 사업장, 공급망, 고객 요구자료를 포함합니다.", "영향: 자료 취합과 내부 승인 일정이 앞당겨질 수 있습니다.", "우선 조치: 기준 변경 사항과 제출 마감일을 월별로 관리합니다."]
  },
  "disclosure-taxonomy-map": {
    title: "공시 요구항목 분류체계",
    bullets: ["기준 체계: ISSB, ESRS, GRI, CDP 요구사항을 분류합니다.", "요구 항목: 거버넌스, 전략, 리스크 관리, 지표/목표로 묶습니다.", "필요 데이터: 배출량, 에너지, 공급망, 재무 영향, 정책 자료를 연결합니다.", "담당/산출물: 부서별 담당과 제출 산출물을 지정합니다."]
  },
  "peer-good-practice-benchmark": {
    title: "동종사 우수사례 벤치마크",
    bullets: ["비교 대상: 동종업계 선도 기업의 공시 구조를 비교합니다.", "관찰 포인트: 데이터 범위, 목표 설명, 리스크 대응, 증빙 수준을 봅니다.", "차이: 현재 자료는 일부 정량 근거와 관리 체계 설명이 부족합니다.", "적용 방향: 이너젠 스타일로 구조만 참고하고 내용은 고객 자료로 재구성합니다."]
  },
  "asis-tobe-gap-roadmap": {
    title: "As-Is / To-Be 개선 로드맵",
    bullets: ["As-Is: 자료 취합과 사후 검토 중심으로 운영됩니다.", "To-Be: 기준 정의, 담당 지정, 증빙 추적을 표준 프로세스로 전환합니다.", "Gap: 데이터 소유자, 승인 이력, 보완 기준이 명확하지 않습니다.", "개선 과제: 양식 표준화, QA 규칙, 교육, 정기 보고 체계를 도입합니다."]
  },
  "iro-register-map": {
    title: "IRO 등록부 구성",
    bullets: ["IRO 항목: 기후 영향, 재무 리스크, 시장 기회, 규제 대응을 식별합니다.", "가치사슬 위치: upstream, operations, downstream으로 구분합니다.", "영향/기회: 발생 가능성, 영향 규모, 대응 시급성을 평가합니다.", "대응: 주요 IRO별 담당 부서와 관리 지표를 지정합니다."]
  },
  "data-request-tracker": {
    title: "자료 요청 관리표",
    bullets: ["요청자료: 전력, 연료, 냉매, 공정가스 사용량과 계산 근거를 확인합니다.", "담당: 사업장, 재무, 구매, ESG 담당자를 구분합니다.", "기간: 자료 기준기간과 제출 기한을 함께 관리합니다.", "상태: 요청, 제출, 검토, 보완, 완료를 색상과 텍스트로 표시합니다.", "이슈: 누락, 중복, 단위 오류를 별도 로그로 관리합니다."]
  },
  "report-production-workflow": {
    title: "보고서 제작 워크플로우",
    bullets: ["기획: 목차, 메시지, 자료 요청 범위를 확정합니다.", "자료 취합: 원천자료와 증빙을 항목별로 수집합니다.", "원고 작성: 데이터 해석과 공시 문구를 작성합니다.", "검토/디자인: 내부 QA, 고객 검토, 디자인 반영을 병행합니다.", "제출: 최종본, 근거자료, 변경 이력을 함께 관리합니다."]
  },
  "score-improvement-levers": {
    title: "평가 점수 개선 레버",
    bullets: ["평가 문항: 점수 영향이 큰 문항을 우선 분류합니다.", "현재 수준: 정책, 실적, 목표, 증빙 수준을 진단합니다.", "감점 요인: 정량 근거 부족, 증빙 누락, 문항 간 불일치를 확인합니다.", "개선 레버: 답변 논리 보강, 자료 연결, 내부 승인 이력을 보완합니다.", "증빙: 원본 파일과 제출 문구를 함께 관리합니다."]
  },
  "training-curriculum-agenda": {
    title: "담당자 교육 커리큘럼",
    bullets: ["모듈: 공시 기준, 자료 제출, 산정 로직, 증빙 관리, QA 기준을 다룹니다.", "핵심 내용: 담당자가 제출해야 할 자료와 검토 기준을 설명합니다.", "실습: 샘플 자료로 단위 오류와 증빙 누락을 점검합니다.", "산출물: 부서별 자료 제출 체크리스트와 FAQ를 제공합니다."]
  },
  "case-study-good-practice": {
    title: "우수사례 적용 포인트",
    bullets: ["사례: 선도 기업은 공시 기준과 내부 데이터 체계를 연결해 설명합니다.", "관찰 포인트: 목표, 지표, 리스크, 거버넌스가 같은 논리로 이어집니다.", "해석: 단순 나열보다 의사결정 메시지가 먼저 제시됩니다.", "적용: 고객 자료를 기반으로 구조만 참고해 이너젠 스타일로 재구성합니다.", "주의점: 출처 없는 수치와 이미지는 사용하지 않습니다."]
  },
  "value-chain-hotspot-map": {
    title: "Scope 3 가치사슬 핫스팟",
    bullets: ["Upstream: 구매 원재료와 물류에서 배출량 비중이 높을 수 있습니다.", "Operations: 에너지 사용과 공정가스가 직접 관리 대상입니다.", "Downstream: 제품 사용, 폐기, 고객 요구자료를 확인합니다.", "Hotspot: 정량 근거가 있는 범주부터 우선순위를 설정합니다.", "관리: 공급망 자료 요청과 배출계수 적용 기준을 표준화합니다."]
  },
  "assurance-evidence-pack": {
    title: "검증 증빙 패키지",
    bullets: ["검증 쟁점: 산정 경계, 단위, 배출계수, 원천자료의 정합성을 확인합니다.", "필요 증빙: 청구서, 계측 기록, 승인 이력, 산정 파일을 포함합니다.", "자료 위치: 데이터 룸 내 폴더와 파일명을 표준화합니다.", "상태: 제출, 검토, 보완, 완료를 추적합니다.", "담당/기한: 보완 담당자와 회신 기한을 명확히 지정합니다."]
  },
  "impact-factoid-big-number": {
    title: "핵심 수치 기반 시사점",
    bullets: ["72% 자료가 취합됐지만 검증 가능한 증빙 연결률은 더 낮습니다.", "비교 기준은 전년 제출 자료와 현재 취합 자료입니다.", "의미: 단순 취합률보다 증빙 연결률이 제출 준비도를 결정합니다.", "관리 시사점: 고위험 항목부터 보완 요청과 검토 로그를 연결합니다."]
  },
  "traffic-light-scorecard": {
    title: "제출 준비도 상태표",
    bullets: ["평가 항목: 자료 취합, 산정 로직, 증빙 연결, 내부 승인, 제출 준비도를 봅니다.", "목표: 제출 전 모든 핵심 항목을 검토 완료 상태로 전환합니다.", "현재: 일부 항목은 보완 또는 주의 상태입니다.", "상태: 빨강, 노랑, 초록과 함께 텍스트 상태를 표시합니다.", "보완: 담당자와 기한을 지정해 미완료 항목을 닫습니다."]
  },
  "bubble-priority-portfolio": {
    title: "우선순위 포트폴리오",
    bullets: ["X축: 실행 난이도를 기준으로 구분합니다.", "Y축: 제출 영향도와 검증 리스크를 기준으로 구분합니다.", "크기: 보완 작업량 또는 관련 부서 수를 표시합니다.", "우선 영역: 영향도는 높고 난이도는 낮은 항목부터 실행합니다.", "해석: 고위험 고난이도 항목은 별도 의사결정이 필요합니다."]
  },
  "forecast-trend-chart": {
    title: "실적과 목표 추세",
    bullets: ["실적: 기준연도 이후 배출량과 에너지 사용 추이를 정리합니다.", "전망/목표: 감축목표와 예상 배출경로를 비교합니다.", "변곡점: 설비 투자, 재생에너지 전환, 생산량 변화 시점을 표시합니다.", "성장률: 활동량 증가와 배출량 변화의 관계를 해석합니다.", "해석: 목표 달성 Gap을 실행 과제로 전환합니다."]
  },
  "funnel-conversion-pipeline": {
    title: "감축수단 후보 선정 퍼널",
    bullets: ["대상군: 에너지 효율, 재생에너지, REC, PPA, 공정 개선 후보를 수집합니다.", "1차 필터: 적용 가능성, 데이터 가용성, 비용 수준을 검토합니다.", "정밀 검토: 감축량, 투자비, 인증 가능성, 실행 리스크를 평가합니다.", "선정 결과: 우선 실행 후보와 보류 후보를 구분합니다.", "실행 과제: 담당 부서와 검토 일정, 필요 자료를 지정합니다."]
  },
  "stakeholder-influence-map": {
    title: "이해관계자 요구 맵",
    bullets: ["이해관계자: 고객사, 투자자, 검증기관, 내부 경영진, 사업부를 구분합니다.", "영향력: 의사결정 영향과 정보 요구 수준을 함께 봅니다.", "요구: 정량 데이터, 증빙, 일정, 리스크 설명을 분류합니다.", "메시지: 이해관계자별로 필요한 핵심 메시지를 정리합니다.", "대응: 우선순위가 높은 이해관계자부터 커뮤니케이션 계획을 수립합니다."]
  },
  "house-framework": {
    title: "공시 대응 운영체계",
    bullets: ["상위 목표: 신뢰 가능한 기후 정보와 검증 가능한 증빙 체계를 구축합니다.", "핵심 축: 데이터, 산정, 공시, 검증, 거버넌스로 구성합니다.", "운영 원칙: 원본 보존, 단위 일관성, 변경 이력, 담당 책임을 유지합니다.", "기반 역량: 데이터 룸, 표준 양식, QA 규칙, 교육 체계가 필요합니다.", "성과 지표: 제출 준비도, 증빙 연결률, 보완 완료율을 관리합니다."]
  },
  "cycle-loop-pdca": {
    title: "PDCA 기반 관리 루프",
    bullets: ["Plan: 공시 기준과 요청자료 범위를 확정합니다.", "Do: 부서별 데이터를 수집하고 산정 파일에 반영합니다.", "Check: 단위, 누락, 중복, 증빙 정합성을 검토합니다.", "Act: 보완 요청과 다음 보고기간 개선과제를 반영합니다.", "기록: 모든 판단 근거와 변경 이력을 관리합니다."]
  },
  "before-after-delta-bridge": {
    title: "개선 전후 변화 요인",
    bullets: ["Before: 자료 취합과 검토가 부서별로 분산되어 있습니다.", "After: 기준, 담당, 증빙, 제출본이 하나의 흐름으로 연결됩니다.", "Delta: 보완 요청 감소, 검토 시간 단축, 제출 안정성이 개선됩니다.", "변화 요인: 표준 양식, QA 규칙, 증빙팩, 회의체 운영이 핵심입니다.", "결론: 반복 제출 업무는 체계화할수록 품질과 속도가 동시에 개선됩니다."]
  },
  "dashboard-kpi-takeaway": {
    title: "프로젝트 관리 대시보드",
    bullets: ["KPI: 자료 취합률, 증빙 연결률, 오류 재발률, 보완 완료율을 관리합니다.", "추세: 취합률은 높아져도 증빙 연결률이 낮으면 제출 리스크가 남습니다.", "상태: 빨강, 노랑, 초록과 함께 보완 조치를 표시합니다.", "원인: 담당 불명확, 단위 오류, 원본 누락이 주요 원인입니다.", "대응: 고위험 항목부터 보완 요청을 닫습니다."]
  },
  "staircase-maturity-evolution": {
    title: "공시 대응 성숙도 단계",
    bullets: ["현재 단계: 수작업 취합과 사후 검토 중심입니다.", "다음 단계: 표준 양식과 담당부서 기반의 정기 취합 체계로 전환합니다.", "고도화 단계: 자동 검토 규칙과 증빙팩 관리를 적용합니다.", "목표 단계: 평가, 검증, 보고서 제작을 하나의 데이터 체계로 운영합니다.", "필요 조건: 기준 정의서, 데이터 룸, 승인 이력, 교육 체계가 필요합니다."]
  },
  "waterfall-bridge-analysis": {
    title: "배출량 증감 요인 분석",
    bullets: ["기준값: 전년 배출량 또는 기준연도 배출량을 출발점으로 둡니다.", "증가 요인: 생산량 증가, 신규 사업장, 에너지 사용 증가를 반영합니다.", "감소 요인: 효율화, 재생에너지, 연료 전환 효과를 반영합니다.", "최종값: 당해연도 배출량과 차이를 계산합니다.", "핵심 원인: 관리 가능한 요인과 외부 요인을 구분합니다."]
  },
  "evidence-to-action-strip": {
    title: "근거 기반 실행 조치",
    bullets: ["근거: 자료 취합은 완료됐지만 일부 증빙과 산정 파일이 분리되어 있습니다.", "해석: 제출 전 검증 질의 대응 시간이 길어질 수 있습니다.", "Gap: 담당자, 자료 위치, 검토 상태가 한 화면에서 확인되지 않습니다.", "Action: 증빙 목록과 QA 로그를 연결해 제출 전 보완 체계를 만듭니다."]
  }
};

export function getArchetypeSample(id: ArchetypeId, fallbackLabel: string, fallbackStructure: string[]): LayoutSample {
  return archetypeSamples[id] ?? {
    title: `${fallbackLabel} 샘플`,
    bullets: fallbackStructure.slice(0, 5).map((item, idx) => `${item}: ${idx + 1}단계에서 확인할 핵심 내용과 산출물을 정리합니다.`)
  };
}

export function buildAllStructureSampleInput() {
  return archetypeRules
    .map((rule, index) => {
      const sample = getArchetypeSample(rule.id, rule.label, rule.structure);
      return [`슬라이드 ${index + 1} [archetype:${rule.id}]: ${sample.title}`, ...sample.bullets.map((bullet) => `- ${bullet}`)].join("\n");
    })
    .join("\n\n---\n");
}

export function buildLayoutFamilySampleInput() {
  return layoutFamilies
    .map((family, index) => {
      const archetype = family.archetypes[0];
      return [
        `슬라이드 ${index + 1} [archetype:${archetype}]: ${family.sample.title}`,
        ...family.sample.bullets.map((bullet) => `- ${bullet}`),
        `- 품질 기준: ${family.qaRules[0]}`
      ].join("\n");
    })
    .join("\n\n---\n");
}
