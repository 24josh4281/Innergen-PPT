import { readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const root = resolve(".");
const filePath = join(root, "docs", "standard-deck-flows.json");
const data = JSON.parse(await readFile(filePath, "utf8"));

const commonRules = [
  "Governing message는 제목 아래 흰색 영역에 1문장으로 두고, 38자 안팎으로 압축합니다.",
  "구조 라벨과 badge는 짧은 명칭으로 변환하여 말줄임표가 나오지 않게 합니다.",
  "박스 내부 긴 문장은 한 문단으로 밀어 넣지 않고 2개 이하 bullet 또는 행 구조로 분리합니다.",
  "생성 후 PPTX 패키지 QA와 PowerPoint 렌더 QA를 모두 통과해야 합니다."
];

const commonRequiredGates = [
  "minFontSize >= 11",
  "belowMinFontCount = 0",
  "rawHyphenCount = 0",
  "ellipsisCount = 0",
  "overflowRiskCount = 0",
  "overlapRiskCount = 0",
  "narrowTextRiskCount = 0",
  "sparseContainerCount = 0",
  "tableWhitespaceRiskCount = 0",
  "alignmentRiskCount = 0",
  "imageRendered = true"
];

const profileText = {
  "reduction-kickoff-standard-flow": {
    label: "감축사업 / 착수·결과보고 표준 Deck Flow",
    rhythm: "표지 -> 목차 -> 핵심 판단 -> 사업 경계 -> 추가성/대안 -> 산정식/시뮬레이션 -> 요청자료 -> 일정/의사결정",
    stageRoles: [
      "표지: 프로젝트명, 회의 목적, 기간, INNerGEN BI만 표시",
      "목차: 3~5개 챕터를 회의 흐름으로 제시",
      "종합 메시지: 이번 회의에서 합의해야 할 범위와 판단 사인을 제시",
      "Why/What/How: 감축사업 필요성과 등록 가능성 질문 정렬",
      "Boundary: 사업 전·후, 베이스라인, 프로젝트 경계 구분",
      "Option Matrix: 추가성 대안과 방법론 적용 가능성 판단",
      "Process: 방법론, PDD, 검증, 제출 단계와 책임 연결",
      "Quantification: 감축량 산정식, 데이터, 모니터링 항목 정리",
      "Scope Table: 업무 범위, 산출물, 검토 기준 명확화",
      "Data Request: 요청자료, 담당, 기한, 상태 관리",
      "Schedule: 주요 마일스톤과 의사결정 일정",
      "Next Action: 회의 후 결정사항과 즉시 조치"
    ],
    generationRules: [
      "초반 3장은 회의 목적과 판단 프레임을 빠르게 고정합니다.",
      "본문은 카드 반복보다 경계도, 비교표, 프로세스, 산정식, 자료요청표를 교차 사용합니다.",
      "감축량·인증·검증 수치는 단위와 기준기간을 반드시 병기합니다.",
      "INNerGEN 외 로고는 사용하지 않습니다.",
      "사용자 입력에 표가 길게 들어오면 원문 핵심값은 보존하되 셀 문장은 판단·근거 중심으로 압축합니다.",
      "사업 전·후 비교는 큰 빈 박스가 아니라 번호 행 구조로 채워 여백을 줄입니다.",
      "감축량 시뮬레이션은 기초가정, PE, BE, 최종 ER을 한 장에서 읽히도록 배치합니다.",
      "근거 카드형 장표는 단순 bullet 배치를 금지하고 핵심 판단, 근거 행, 의미 바를 포함합니다.",
      "카드 내부 텍스트가 부족하면 박스 크기를 줄이거나 행 구조와 판단칩으로 시각 밀도를 보완합니다.",
      "사용자 입력 문장은 임의 삭제하지 않고, 화면 구조화와 발표자 노트/manifest 원문 보존을 함께 적용합니다.",
      "sparseContainerCount가 1건 이상이면 QA fail로 보고, judgment chip·evidence row·summary bar 중 하나 이상을 추가합니다.",
      "표 셀 내부 여백이 커 보이면 행 높이를 낮추거나 본문 12.5~14pt로 키우고, 핵심 판단/근거/의미처럼 추가 정보 열을 넣어 시각 밀도를 높입니다.",
      "번호형 행 구조는 번호 칼럼 폭을 고정하고 번호·본문 텍스트박스를 같은 rowY/rowH 기준으로 세로 중앙 정렬합니다.",
      "배지·칩 텍스트는 도형과 동일한 높이의 텍스트박스를 사용하고 valign=middle을 적용해 박스 내부 중앙에서 벗어나지 않게 합니다.",
      "줄바꿈이 필요한 긴 문장은 번호 옆 좁은 박스에 억지로 넣지 않고 행 높이를 0.55in 이상 확보해 기준선을 유지합니다.",
      "alignmentRiskCount가 1건 이상이면 QA fail로 보고, 번호·라벨·칩·본문의 rowY/rowH를 재정렬합니다.",
      "레퍼런스 Top N 샘플의 심미 균형을 적용해 표 본문 12~14pt, 행 높이 0.55~0.95in, category/evidence/judgment 열 폭 균형을 우선합니다."
    ]
  },
  "disclosure-proposal-standard-flow": {
    label: "CDP·기후공시 / 제안서 표준 Deck Flow",
    rhythm: "표지 -> 목차 -> 제안 요약 -> 고객 과제 -> 평가/공시 요구 -> 대응전략 -> 업무범위 -> 산출물 -> 일정/차별성",
    stageRoles: [
      "표지: 제안명, 고객사, 제출일, INNerGEN BI만 표시",
      "목차: 제안 논리와 수행 범위를 4개 이하 챕터로 구성",
      "Executive Summary: 제안의 핵심 가치와 기대 효과",
      "Why/What/How: CDP·기후공시 대응 필요성과 제안 방향",
      "Readiness: 현재 수준, gap, 우선 대응 영역",
      "CDP Strategy: 문항 분석, 증빙 확보, 답변 작성, 제출 대응",
      "Taxonomy Map: 공시 기준, 문항, 필요 데이터, 담당 부서 연결",
      "Score Levers: 점수 개선 레버와 증빙 보완 포인트",
      "Issue Tree: 핵심 질문을 업무 과제로 분해",
      "Scope: 업무 범위, 방법, 산출물을 한 장에서 연결",
      "Workflow: 자료 취합, 원고, 검토, 제출 프로세스",
      "Schedule: 주차별 과업과 고객 협조 시점",
      "Closing Action: 제안 채택 후 즉시 착수할 next step"
    ],
    generationRules: [
      "제안서는 단순 업무 나열이 아니라 고객 과제 -> 해결 구조 -> 산출물 가치 흐름으로 작성합니다.",
      "CDP/공시 문항 설명은 길게 쓰지 말고 score lever와 증빙 체계로 구조화합니다.",
      "업무범위와 산출물은 반드시 연결해 고객이 구매 대상을 바로 이해하게 합니다.",
      "외부 컨설팅사 로고나 BI는 차용하지 않습니다."
    ]
  },
  "ghg-inventory-final-standard-flow": {
    label: "온실가스 인벤토리 / 최종보고 표준 Deck Flow",
    rhythm: "표지 -> 목차 -> 최종 결론 -> 산정 범위 -> 배출량 결과 -> 증감 요인 -> 검증 보완 -> 관리체계 -> 향후 일정",
    stageRoles: [
      "표지: 최종보고명, 기준연도, INNerGEN BI만 표시",
      "목차: 산정 결과, 검증 쟁점, 관리 과제를 구분",
      "Executive Summary: 최종 결론과 의사결정 필요사항",
      "Big Number: 총 배출량, 주요 배출원, 전년 대비 핵심 변화",
      "Boundary: 조직경계, 운영경계, 산정 대상 시설/활동",
      "Scope Table: Scope 1/2/3 또는 배출원별 산정 기준",
      "Waterfall: 전년 대비 증감 요인과 배출원별 영향",
      "Dashboard: 주요 KPI, 사업장/부문별 결과와 해석",
      "Evidence Pack: 검증 증빙, 산정근거, 원본자료 상태",
      "Scorecard: 보완 필요 항목, 담당, 조치 상태",
      "Timeline: 명세서, 검증, 제출, 내부관리 일정",
      "Action: 최종보고 후 관리체계와 다음 보고 준비사항"
    ],
    generationRules: [
      "최종보고는 결과 숫자와 검증 가능성을 먼저 보여줍니다.",
      "수치 변경은 절대 임의 수정하지 않고, 단위·기준연도·범위를 함께 표시합니다.",
      "잔여 리스크는 비판이 아니라 보완 조치와 담당/기한으로 표현합니다.",
      "고객사 로고와 외부 브랜드 요소는 재사용하지 않습니다."
    ]
  }
};

for (const profile of data.profiles) {
  const patch = profileText[profile.id];
  if (!patch) continue;
  Object.assign(profile, patch);
  profile.generationRules = Array.from(new Set([...profile.generationRules, ...commonRules]));
  if (profile.qaValidation?.requiredGates) {
    profile.qaValidation.requiredGates = Array.from(new Set([...profile.qaValidation.requiredGates, ...commonRequiredGates]));
  }
}

const reduction = data.profiles.find((profile) => profile.id === "reduction-kickoff-standard-flow");
if (reduction) {
  reduction.userInputValidation = {
    samplePptx: "docs/generated/user-input-samples/starstech-phase1/starstech_phase1_result_report_innergen.pptx",
    manifest: "docs/generated/user-input-samples/starstech-phase1/starstech_phase1_result_report_innergen.manifest.json",
    renderQaReports: [
      "docs/generated/user-input-samples/starstech-phase1/render-qa-pass-1/qa-report.json",
      "docs/generated/user-input-samples/starstech-phase1/render-qa-pass-2/qa-report.json"
    ],
    lastValidatedAt: "2026-05-27",
    status: "pass",
    requiredGates: commonRequiredGates,
    observedImprovements: [
      "감축사업 결과보고 입력은 reduction-kickoff-standard-flow로 자동 매칭해도 적합합니다.",
      "표 슬라이드는 원문을 그대로 장문 삽입하지 않고 핵심 판단, 근거, 수치로 압축해야 합니다.",
      "사업 전·후 비교는 번호 행 구조를 사용하면 여백과 줄바꿈 문제가 줄어듭니다.",
      "시뮬레이션 장표는 4개 표를 모두 같은 크기로 넣기보다 기초가정, PE, BE, ER 결과 박스로 재구성하는 편이 안정적입니다."
      ,
      "법적 추가성처럼 근거가 짧은 장표는 naked bullet 대신 판단칩, 근거 행, 의미 바 구조를 사용해야 비어 보이지 않습니다."
    ]
  };
}

await writeFile(filePath, JSON.stringify(data, null, 2), "utf8");
console.log(JSON.stringify({ updated: filePath, profiles: data.profiles.length }, null, 2));
