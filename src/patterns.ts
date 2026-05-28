import type { ArchetypeId, ArchetypeRule } from "./types";

export const INNGEN_COLORS = {
  navy: "041E42",
  navy2: "0B2344",
  blue: "13387B",
  sky: "00A9E0",
  paleBlue: "EAF6FC",
  gray: "F2F4F7",
  line: "D9E2EC",
  text: "1E293B",
  muted: "667085",
  red: "E30613",
  yellow: "FFB81C",
  green: "12B76A",
  white: "FFFFFF",
  black: "000000"
};

function rule(
  id: ArchetypeId,
  label: string,
  structure: string[],
  keywords: string[],
  layoutHint: string,
  safetyRule: string,
  description = "입력 내용을 컨설팅 장표의 주장, 근거, 시사점 구조로 재배치합니다."
): ArchetypeRule {
  return { id, label, description, structure, keywords, layoutHint, safetyRule };
}

export const archetypeRules: ArchetypeRule[] = [
  rule("cover-kickoff", "Reference Cover", ["고객/프로젝트명", "회의 목적", "날짜", "INNerGEN BI"], ["cover", "표지", "kickoff", "착수", "보고"], "레퍼런스형 네이비 표지 + 좌측 정보 블록 + 우측 여백/심볼", "표지는 본문 규칙을 적용하지 않고 제목을 크게 유지"),
  rule("contents-isometric", "Contents / Roadmap", ["섹션 1", "섹션 2", "섹션 3", "진행 흐름"], ["contents", "목차", "agenda", "순서", "로드맵"], "목차를 단순 목록이 아니라 아이콘/일러스트/단계 흐름으로 구성", "목차 항목은 한 줄 유지, 세부 설명은 넣지 않음"),
  rule("consulting-executive-summary", "Executive Summary", ["핵심 주장", "근거", "영향", "우선 실행"], ["요약", "summary", "executive", "결론", "핵심"], "상단 주장 + 3개 메시지 카드 + 하단 implication", "각 메시지는 1문장, 세부 근거는 본문 또는 Appendix로 분리"),
  rule("why-what-how-logic", "Why / What / How", ["Why", "What", "Who", "How", "So what"], ["why", "what", "how", "배경", "필요", "목적", "요구"], "5개 논리 버킷 + 결론 배너", "단순 정의가 아니라 의사결정 메시지로 작성"),
  rule("proposal-need-three-cards", "3 Reasons", ["규제 요구", "이해관계자 요구", "내부 대응", "결론"], ["필요", "목적", "제안", "대응", "추진"], "3개 이유 카드 + 하단 제안 메시지", "카드 제목은 짧게, 본문은 2줄 이하"),
  rule("proposal-scope-integrated", "Integrated Scope", ["업무 범위", "분석 대상", "수행 방법", "산출물"], ["scope", "범위", "과업", "수행", "산출물"], "범위-방법-산출물 테이블", "범위와 산출물을 한 셀에 섞지 않음"),
  rule("benchmark-readiness-summary", "Benchmark / Readiness", ["비교 기준", "현재 수준", "Gap", "우선 조치"], ["benchmark", "readiness", "벤치마크", "성숙도", "수준", "gap"], "좌측 평가 매트릭스 + 우측 우선 조치", "수치와 해석을 분리"),
  rule("double-materiality-or-risk-map", "Risk / Materiality Map", ["평가 기준", "주요 이슈", "우선 영역", "대응 방향"], ["risk", "materiality", "위험", "중요성", "영향", "기회"], "2축 우선순위 맵 + takeaways", "축 의미와 우선 영역을 명확히 표기"),
  rule("issue-tree-to-workplan", "Issue Tree", ["핵심 질문", "하위 이슈", "분석 과제", "산출물"], ["issue", "문제", "질문", "workplan", "과제"], "이슈트리 + 실행 과제 매핑", "이슈는 MECE하게 3~4개로 제한"),
  rule("tcfd-pillar-diagnosis", "TCFD Pillars", ["Governance", "Strategy", "Risk Management", "Metrics & Targets"], ["tcfd", "issb", "governance", "strategy", "metrics", "targets"], "4개 pillar 진단", "pillar별 현재상태와 보완 방향을 함께 표시"),
  rule("scenario-financial-impact", "Scenario Impact", ["시나리오", "영향 경로", "재무/운영 영향", "대응 전략"], ["scenario", "시나리오", "재무영향", "민감도", "기후리스크"], "영향 경로 + 우측 해석 패널", "가정, 기준연도, 단위를 분리"),
  rule("sbti-process", "SBTi Process", ["진단", "목표 개발", "제출/검증", "공개/관리"], ["sbti", "sbt", "target", "목표", "검증"], "4단계 gated process", "각 단계별 산출물과 검토 포인트를 연결"),
  rule("cdp-response-strategy", "CDP Response", ["문항 분석", "자료 수집", "답변 작성", "제출/보완"], ["cdp", "ors", "score", "scoring", "답변", "평가"], "4단계 대응 프로세스", "문항, 증빙, 답변 논리를 분리"),
  rule("climate-scenario-framework", "Climate Scenario", ["준비", "설계", "분석", "내재화"], ["physical", "transition", "기후리스크", "물리", "전환", "적응"], "시나리오 분석 프레임워크", "체크리스트형 장표는 Appendix로 분리"),
  rule("method-chevron", "Method Chevron", ["Step 1", "Step 2", "Step 3", "Step 4"], ["process", "method", "절차", "방법론", "단계"], "수평 chevron + 단계별 핵심 활동", "단계명은 12자 내외로 압축"),
  rule("integrated-process-map", "Methodology Development", ["타당성", "방법론/PDD", "검증", "제출/인증", "MRV"], ["방법론", "PDD", "MRV", "검증", "인증", "감축"], "5단계 방법론 개발 맵", "검증기관/제출 일정은 별도 행으로 분리"),
  rule("inventory-boundary-flow", "Boundary / Baseline Flow", ["경계 설정", "Baseline", "Project", "Leakage", "조건"], ["baseline", "boundary", "경계", "베이스라인", "사업배출", "누출"], "좌-우 흐름도 + 조건 패널", "계산식보다 경계와 조건을 먼저 고정"),
  rule("reduction-roadmap-analysis", "Reduction Logic", ["산정식", "모니터링", "모델링", "보수성", "데이터"], ["감축량", "산정", "모니터링", "모델", "계수"], "산정 방식 비교 매트릭스", "수치는 단위와 출처를 함께 표기"),
  rule("schedule-gantt", "Schedule Gantt", ["업무", "기간", "마일스톤", "검토"], ["schedule", "gantt", "일정", "월", "주차", "기간"], "업무 행 + 월별 bar", "셀 안 설명은 줄이고 바깥 주석으로 분리"),
  rule("team-management", "Team / Governance", ["역할", "담당", "책임", "관리 방식"], ["team", "governance", "조직", "인력", "담당", "관리", "raci"], "RACI형 역할 테이블", "개인정보는 제공된 범위 안에서만 사용"),
  rule("communication-management", "Meeting / Decision Log", ["결정사항", "요청자료", "담당", "기한"], ["회의", "요청", "결정", "후속", "커뮤니케이션"], "결정 로그 + next action 테이블", "결정/요청/오픈 이슈를 섞지 않음"),
  rule("evidence-grid", "Evidence Grid", ["근거 1", "근거 2", "근거 3", "근거 4"], ["evidence", "근거", "스크린샷", "샘플", "참고"], "2x2 근거 패널", "근거 캡션은 짧게 유지"),
  rule("work-scope-table", "Work Scope Table", ["업무", "대상", "방법", "산출물"], ["table", "목록", "자료", "deliverable", "요건"], "범위/방법/산출물 테이블", "본문은 11pt 이상, 셀 여백은 균일하게"),
  rule("comparison-matrix", "Option Matrix", ["옵션", "장점", "제약", "추천"], ["option", "matrix", "비교", "대안", "시장", "인증"], "옵션 비교표 + 추천 영역", "추천 기준을 명확히 표기"),
  rule("consulting-one-page-memo", "One-page Memo", ["질문", "근거", "판단", "잔여 리스크"], ["memo", "검토", "판단", "근거", "리스크"], "메모형 요약 + 검토 질문", "긴 문단은 3개 문장 이하로 압축"),
  rule("regulatory-timeline-radar", "Regulatory Timeline", ["이벤트", "대상", "영향", "우선 조치"], ["regulation", "timeline", "규제", "제도", "시행", "공시"], "연도/월 timeline + 대응 카드", "날짜는 사실 기준으로만 표기"),
  rule("disclosure-taxonomy-map", "Disclosure Taxonomy", ["기준 체계", "요구 항목", "필요 데이터", "담당/산출물"], ["taxonomy", "공시", "esrs", "issb", "gri", "tnfd"], "공시 기준 분류 맵", "항목을 5~7개 묶음으로 압축"),
  rule("peer-good-practice-benchmark", "Peer Good Practice", ["비교 대상", "관찰 포인트", "차이", "적용 방향"], ["peer", "best practice", "사례", "동종", "벤치마크"], "사례 카드 + 적용 포인트", "사실과 해석을 구분"),
  rule("asis-tobe-gap-roadmap", "As-Is / To-Be Gap", ["As-Is", "To-Be", "Gap", "개선 과제"], ["as-is", "to-be", "gap", "현황", "목표", "개선"], "현재/목표 비교 + gap bridge", "Gap은 비판보다 실행 조건으로 표현"),
  rule("iro-register-map", "IRO Register", ["IRO 항목", "가치사슬 위치", "영향/기회", "대응"], ["iro", "impact", "risk", "opportunity", "영향", "기회"], "IRO register + 대응 방향", "메인 슬라이드는 핵심 IRO만 표시"),
  rule("data-request-tracker", "Data Request Tracker", ["요청자료", "담당", "기간", "상태", "이슈"], ["data request", "자료요청", "담당", "상태", "기한"], "상태 색상표 + 요청자료 테이블", "실제 담당자명은 확인 후 사용"),
  rule("report-production-workflow", "Report Production", ["기획", "자료 취합", "원고 작성", "검토/디자인", "제출"], ["보고서", "원고", "제작", "공시", "제출"], "보고서 제작 workflow", "디자인/검토/제출 리드타임 분리"),
  rule("score-improvement-levers", "Score Improvement", ["평가 문항", "현재 수준", "감점 요인", "개선 레버", "증빙"], ["score", "rating", "ecovadis", "점수", "등급", "개선"], "점수 개선 lever 테이블", "점수 예측은 확정 표현 금지"),
  rule("training-curriculum-agenda", "Training Curriculum", ["모듈", "핵심 내용", "실습", "산출물"], ["training", "교육", "워크숍", "커리큘럼", "agenda"], "교육 agenda 테이블", "설명보다 학습 질문 중심"),
  rule("case-study-good-practice", "Case Study", ["사례", "관찰 포인트", "해석", "적용", "주의점"], ["case", "사례", "example", "good practice"], "사례 요약 + 적용 포인트", "출처 없는 이미지는 사용하지 않음"),
  rule("value-chain-hotspot-map", "Value Chain Hotspot", ["Upstream", "Operations", "Downstream", "Hotspot", "관리"], ["value chain", "scope 3", "공급망", "upstream", "downstream"], "가치사슬 흐름 + hotspot", "정량 근거가 없으면 우선 검토 후보로 표기"),
  rule("assurance-evidence-pack", "Evidence Pack", ["검증 쟁점", "필요 증빙", "자료 위치", "상태", "담당/기한"], ["assurance", "검증", "증빙", "audit", "QA"], "검증 증빙 패키지 표", "원본값은 수정하지 않고 상태만 관리"),
  rule("impact-factoid-big-number", "Impact Factoid", ["핵심 숫자", "비교 기준", "의미", "관리 시사점"], ["kpi", "metric", "숫자", "%", "tco2", "factoid"], "큰 숫자 + 보조 해석", "모든 숫자는 단위와 기준기간 표기"),
  rule("traffic-light-scorecard", "Traffic-Light Scorecard", ["평가 항목", "목표", "현재", "상태", "보완"], ["traffic", "status", "rag", "상태", "진척", "점검"], "RAG 상태표", "색상만으로 의미를 전달하지 않음"),
  rule("bubble-priority-portfolio", "Priority Portfolio", ["X축", "Y축", "크기", "우선 영역", "해석"], ["bubble", "portfolio", "priority", "우선순위", "2축"], "2축 우선순위 맵", "임의 위치처럼 보이지 않게 축 정의 포함"),
  rule("forecast-trend-chart", "Forecast Trend", ["실적", "전망/목표", "변곡점", "성장률", "해석"], ["forecast", "trend", "cagr", "전망", "추세", "목표"], "actual vs target trend", "가정과 실제를 시각적으로 구분"),
  rule("funnel-conversion-pipeline", "Funnel Pipeline", ["대상군", "1차 필터", "정밀 검토", "선정 결과", "실행 과제"], ["funnel", "pipeline", "후보", "필터", "선정"], "단계별 funnel", "탈락 사유와 선정 기준을 함께 표기"),
  rule("stakeholder-influence-map", "Stakeholder Map", ["이해관계자", "영향력", "요구", "메시지", "대응"], ["stakeholder", "이해관계자", "커뮤니케이션", "요구"], "영향력/관심도 맵", "민감한 평가는 완화된 표현 사용"),
  rule("house-framework", "House Framework", ["상위 목표", "핵심 축", "운영 원칙", "기반 역량", "성과 지표"], ["house", "framework", "pillar", "체계", "전략"], "roof-pillar-foundation 구조", "pillar는 3~4개로 제한"),
  rule("cycle-loop-pdca", "Cycle / Loop", ["Plan", "Do", "Check", "Act", "기록"], ["pdca", "cycle", "loop", "mrv", "반복", "개선"], "PDCA 순환 구조", "책임/기록 산출물을 반드시 연결"),
  rule("before-after-delta-bridge", "Before / After", ["Before", "After", "Delta", "변화 요인", "결론"], ["before", "after", "delta", "개선", "전후"], "전후 비교 + delta bridge", "비교 기준기간을 명시"),
  rule("dashboard-kpi-takeaway", "KPI Dashboard", ["KPI", "추세", "상태", "원인", "대응"], ["dashboard", "kpi", "성과", "관리지표"], "KPI 카드 + 차트 + takeaway", "숫자보다 해석을 먼저 보이게 구성"),
  rule("staircase-maturity-evolution", "Maturity Staircase", ["현재 단계", "다음 단계", "고도화 단계", "목표 단계", "필요 조건"], ["staircase", "maturity", "성숙도", "고도화", "로드맵"], "성숙도 계단", "단계명은 한 줄로 유지"),
  rule("waterfall-bridge-analysis", "Waterfall Bridge", ["기준값", "증가 요인", "감소 요인", "최종값", "핵심 원인"], ["waterfall", "bridge", "증감", "요인", "차이"], "waterfall bridge + 원인 패널", "합계와 단위 정합성을 확인"),
  rule("evidence-to-action-strip", "Evidence to Action", ["근거", "해석", "Gap", "Action"], ["evidence", "action", "gap", "조치", "보완"], "근거-해석-조치 strip", "한 슬라이드의 결론은 하나만 유지")
];

export function getRule(id: string): ArchetypeRule {
  return archetypeRules.find((rule) => rule.id === id) ?? archetypeRules[0];
}
