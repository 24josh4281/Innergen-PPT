import pptxgen from "pptxgenjs";
import { mkdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const root = resolve(".");
const outDir = join(root, "docs", "generated", "user-input-samples", "starstech-phase1");
const outPptx = join(outDir, "starstech_phase1_result_report_innergen.pptx");
const manifestPath = join(outDir, "starstech_phase1_result_report_innergen.manifest.json");

const pptx = new pptxgen();
pptx.author = "INNerGEN";
pptx.company = "INNerGEN";
pptx.subject = "Starstech phase 1 carbon reduction methodology result report";
pptx.title = "스타스테크 폐산 재활용 기술 온실가스 감축 방법론 개발 1단계 결과 보고";
pptx.lang = "ko-KR";
pptx.defineLayout({ name: "INNERGEN_WIDE_CM", width: 10.833, height: 7.5 });
pptx.layout = "INNERGEN_WIDE_CM";
pptx.theme = {
  headFontFace: "Malgun Gothic",
  bodyFontFace: "Malgun Gothic",
  lang: "ko-KR"
};

const W = 10.833;
const H = 7.5;
const FONT = "Malgun Gothic";
const MIN_FONT = 11;
const C = {
  navy: "1A2B5F",
  navy2: "102047",
  sky: "4A90D9",
  pale: "EAF3FC",
  pale2: "F3F8FD",
  gray: "F4F6F8",
  line: "D7DEE8",
  text: "1F2937",
  muted: "667085",
  white: "FFFFFF",
  black: "000000",
  red: "E30613",
  green: "18A058",
  amber: "FFB81C"
};

const slidesManifest = [];

await mkdir(outDir, { recursive: true });

cover();
processSlide();
contentsSlide();
summaryEvaluation();
businessRequirements();
legalAdditionality();
commonPracticeAndBaseline();
assessmentBoundary();
formulaConcept();
quantSimulation();
dataRequest();
scheduleSlide();

await pptx.writeFile({ fileName: outPptx });
await writeFile(manifestPath, JSON.stringify({
  generatedAt: new Date().toISOString(),
  flowMatched: "reduction-kickoff-standard-flow",
  reason: "감축사업 방법론 개발 1단계 결과 보고이며, 경계/추가성/베이스라인/감축량/자료요청/일정을 다룸",
  designSystem: {
    brand: "INNerGEN only",
    colors: ["#1A2B5F", "#FFFFFF", "#4A90D9"],
    font: FONT,
    minFontSize: MIN_FONT
  },
  qaGates: [
    "minFontSize >= 11",
    "rawHyphenCount = 0",
    "ellipsisCount = 0",
    "overflowRiskCount = 0",
    "overlapRiskCount = 0",
    "narrowTextRiskCount = 0",
    "sparseContainerCount = 0",
    "tableWhitespaceRiskCount = 0",
    "alignmentRiskCount = 0",
    "imageRendered = true"
  ],
  densityPolicy: [
    "큰 카드 안에는 단순 bullet만 배치하지 않습니다.",
    "카드형 근거 장표는 제목, 핵심 판단, 근거 행, 의미 바를 모두 포함합니다.",
    "본문 텍스트가 적은 경우 박스 크기를 줄이거나 행 구조, 판단칩, 요약바로 시각 밀도를 보완합니다.",
    "원문 문장이 긴 경우 셀 안에 그대로 넣지 않고 판단, 근거, 영향으로 분리합니다.",
    "사용자 입력 문장은 임의 삭제하지 않고, 화면 구조화와 발표자 노트/manifest 원문 보존을 함께 적용합니다.",
    "번호, 라벨, 칩, 본문은 같은 rowY/rowH 기준으로 맞추고 세로 중앙 정렬합니다.",
    "표는 내용량, 행 높이, 폰트 크기, 열 폭이 균형을 이루도록 레퍼런스 기반 compact table rhythm을 적용합니다."
  ],
  slides: slidesManifest
}, null, 2), "utf8");

console.log(JSON.stringify({ outPptx, manifestPath, slideCount: slidesManifest.length }, null, 2));

function cover() {
  const s = pptx.addSlide();
  s.background = { color: C.navy };
  grid(s, 0, 0, W, H, C.navy2, 75);
  s.addText("INNerGEN | 이너젠", tx(0.55, 0.45, 2.2, 0.24, { size: 11.5, bold: true, color: C.white }));
  s.addText("2026년 3월", tx(8.95, 0.45, 1.25, 0.24, { size: 11.5, color: C.white, align: "right" }));
  s.addShape("line", { x: 0.55, y: 0.9, w: 9.7, h: 0, line: { color: C.sky, width: 1.1, transparency: 10 } });
  s.addText("스타스테크 폐산 재활용 기술에 의한\n온실가스 감축 방법론 개발 1단계 결과 보고", tx(0.9, 2.18, 9.05, 1.18, {
    size: 25.5,
    bold: true,
    color: C.white,
    align: "center",
    valign: "middle"
  }));
  s.addText("사전 타당성 평가 결과 보고 회의 자료", tx(2.35, 3.78, 6.1, 0.28, {
    size: 15,
    bold: true,
    color: C.sky,
    align: "center"
  }));
  s.addShape("rect", { x: 0, y: 6.62, w: W, h: 0.48, fill: { color: C.navy2 }, line: { color: C.navy2 } });
  s.addText("CO2 Consulting for Client", tx(7.55, 6.78, 2.65, 0.18, { size: 11, color: C.white, align: "right" }));
  s.addText("INNerGEN │ 이너젠", tx(0.55, 6.78, 2.2, 0.18, { size: 11, bold: true, color: C.white }));
  noteSlide("표지", "Cover");
}

function processSlide() {
  const s = bodySlide("과업 추진 전체 프로세스", "본 보고는 1단계 사전 타당성 검토 결과를 기준으로 다음 단계 의사결정을 지원합니다.", "Process");
  const steps = [
    ["1단계", "사전 타당성 검토", "현재 진행", ["법적·제도적 추가성 검토", "베이스라인 시나리오 설정", "예상 감축량 산정", "방법론 개발 방향 확정"]],
    ["2단계", "방법론 및 사업계획 개발", "", ["KCS 신규 방법론 문서 작성", "PDD 사업계획서 작성", "내부 검토 및 보완"]],
    ["3단계", "제3자 검증", "", ["외부 검증기관 선정", "Validation 대응 및 보완", "최종 검증 완료"]],
    ["4단계", "제출 및 인증기관 대응", "", ["KCS 등록 신청서 제출", "적합성 심의 대응", "최종 등록 완료"]]
  ];
  const x0 = 0.55;
  const y = 1.55;
  const gap = 0.16;
  const cardW = (9.75 - gap * 3) / 4;
  steps.forEach(([no, title, badge, bullets], i) => {
    const x = x0 + i * (cardW + gap);
    s.addShape("roundRect", { x, y, w: cardW, h: 4.72, rectRadius: 0.04, fill: { color: i === 0 ? C.pale : C.white }, line: { color: i === 0 ? C.sky : C.line, width: 1 } });
    s.addShape("rect", { x, y, w: cardW, h: 0.58, fill: { color: i === 0 ? C.sky : C.navy }, line: { color: i === 0 ? C.sky : C.navy } });
    s.addText(`${no} | ${title}`, tx(x + 0.12, y, cardW - 0.24, 0.58, { size: 11.5, bold: true, color: C.white, align: "center", valign: "middle" }));
    if (badge) {
      s.addShape("roundRect", { x: x + 0.5, y: y + 0.86, w: cardW - 1.0, h: 0.34, rectRadius: 0.03, fill: { color: C.red }, line: { color: C.red } });
      s.addText(badge, tx(x + 0.62, y + 0.86, cardW - 1.24, 0.34, { size: 11, bold: true, color: C.white, align: "center", valign: "middle" }));
    }
    bulletsText(s, bullets, x + 0.22, y + 1.45, cardW - 0.44, 2.25, { size: 11.2, gap: 4 });
    s.addText(i === 0 ? "1단계 결과 보고" : i === 1 ? "문서화" : i === 2 ? "검증 대응" : "등록 완료", tx(x + 0.25, y + 4.15, cardW - 0.5, 0.22, {
      size: 12,
      bold: true,
      color: i === 0 ? C.red : C.navy,
      align: "center"
    }));
    if (i < 3) {
      s.addText("›", tx(x + cardW + 0.02, y + 2.08, 0.12, 0.28, { size: 22, bold: true, color: C.sky, align: "center" }));
    }
  });
  callout(s, "본 보고는 1단계 진행 결과를 중간 보고하는 자료임", 0.75, 6.48, 9.35, 0.34);
  footer(s, 2);
  noteSlide("과업 추진 전체 프로세스", "4-step process");
}

function contentsSlide() {
  const s = bodySlide("Contents", "보고 흐름은 타당성 판단, 평가 컨셉, 협조 요청 순서로 정리합니다.", "Contents");
  s.addShape("rect", { x: 1.05, y: 1.55, w: 0.08, h: 4.58, fill: { color: C.navy }, line: { color: C.navy } });
  const items = [
    ["I.", "사전 타당성 검토 상황"],
    ["II.", "평가 컨셉 설정 상황", "진행 중"],
    ["III.", "협조 요청 및 향후 계획"]
  ];
  items.forEach(([roman, title, badge], i) => {
    const y = 1.78 + i * 1.38;
    s.addText(roman, tx(1.42, y, 0.58, 0.32, { size: 19, bold: true, color: C.sky }));
    s.addText(title, tx(2.08, y, 5.6, 0.32, { size: 19, bold: true, color: C.navy }));
    if (badge) {
      s.addShape("roundRect", { x: 6.1, y: y + 0.02, w: 0.72, h: 0.26, rectRadius: 0.03, fill: { color: C.pale }, line: { color: C.sky, width: 0.8 } });
      s.addText(badge, tx(6.2, y + 0.1, 0.52, 0.08, { size: 11, bold: true, color: C.sky, align: "center" }));
    }
    s.addShape("line", { x: 1.42, y: y + 0.62, w: 7.7, h: 0, line: { color: C.line, width: 0.8 } });
  });
  footer(s, 3);
  noteSlide("Contents", "chapter contents");
}

function summaryEvaluation() {
  const s = bodySlide("I. 사전 타당성 검토 상황 | 종합 평가", "6개 평가항목 중 5개가 적합하며, 신규 방법론 개발 조건에서 KCS 추진이 타당합니다.", "Evaluation");
  label(s, "I. 사전 타당성 검토", 0.55, 1.3, 1.85, C.navy);
  const rows = [
    ["평가항목", "판정기준", "스타스테크 폐산 재활용 사업", "판정"],
    ["추가성", "법적 의무 부재", "의무 규정 없음, 자발적 R&D 투자", "○"],
    ["감축 기술", "직·간접 감축 기여", "CIC 생산으로 수입 SHMP 대체", "○"],
    ["보급 현황", "보편 관행 초과", "234개 업체 대비 저순도 폐혼산 100% 자원화", "○"],
    ["감축 효과", "정량 산출 가능", "수입 원료와 폐수처리 배출 회피", "○"],
    ["방법론", "기존 KCS 적용", "수입 물류·복합 공정 반영 필요", "신규"],
    ["예상 감축량", "등록 기준 충족", "연간 약 3,550 tCO₂eq 예상", "○"]
  ];
  table(s, rows, 0.55, 1.78, 9.74, 4.42, [1.45, 2.05, 5.15, 1.09], { body: 11.0, header: 11.4, rowH: [0.42, 0.58, 0.58, 0.66, 0.58, 0.58, 0.58] });
  callout(s, "종합 판정: 5개 항목 적합, 방법론 신규 개발 조건 하에 사업 등록 추진 타당", 0.75, 6.46, 9.35, 0.34);
  footer(s, 4);
  noteSlide("종합 평가표", "full-width evaluation table");
}

function businessRequirements() {
  const s = bodySlide("I. 사전 타당성 검토 상황 | 사업 요건 상세", "사업 시작일, 유효기간, 유형, 기준선은 방법론 개발 전 우선 고정해야 합니다.", "Requirements");
  table(s, [
    ["항목", "검토 사항", "검토 결과"],
    ["방법론명(안)", "KCS 신규 방법론 제안명", "사업장 폐산의 화학적 재활용을 통한 신품 화학원료 대체 감축 방법론"],
    ["사업 시작일", "감축 효과 최초 발생일", "2025.02.16 품질규격 최초 달성일을 사업 시작일로 설정 타당"],
    ["인증유효기간", "KCS 기준 유효기간", "승인연도 기준 5년"],
    ["감축사업 유형", "KCS 감축사업 분류", "물질 재활용(Material Recycling) 유형"],
    ["적용 기준선", "베이스라인 설정 방식", "폐수처리 + 수입 신품 원료 사용 관행(대안 2)"]
  ], 0.65, 1.55, 9.54, 4.7, [1.65, 2.65, 5.24], { body: 11.1, header: 11.8, rowH: [0.46, 0.72, 0.78, 0.62, 0.62, 0.62] });
  callout(s, "핵심: 사업 시작일과 기준선은 감축량 산정식의 전제가 되므로 증빙으로 고정 필요", 0.78, 6.45, 9.22, 0.34);
  footer(s, 5);
  noteSlide("사업 요건 상세", "requirements table");
}

function legalAdditionality() {
  const s = bodySlide("I. 사전 타당성 검토 상황 | 추가성 입증 ① 법적·제도적 추가성", "법적 의무가 없는 자발적 투자 구조이므로 KCS 법적·제도적 추가성 요건을 충족합니다.", "Additionality");
  label(s, "참고 | 법적·제도적 추가성 상세", 0.65, 1.35, 2.45, C.navy);
  const cards = [
    ["관련 법령 검토", ["폐기물관리법상 1일 16.5톤 처리, 346.5톤 보관시설 인허가 득", "저순도 폐혼산을 CIC로 물질 재활용해야 한다는 의무 규정 없음"]],
    ["합법적 대안 존재", ["폐수 위탁 처리는 현행법상 허용되는 일반 관행", "본 사업은 합법적 대안이 있음에도 자발적 R&D 투자로 추진"]],
    ["KCS 요건 충족", ["판단 기준: 법적 의무가 아닌 자발적 행위", "결론: 법적 강제 없이 추진되어 추가성 요건 충족"]]
  ];
  table(s, [
    ["검토 영역", "핵심 판단", "주요 근거", "의미"],
    ...cards.map(([title, bullets]) => [
      title,
      inferPanelJudgment(title),
      bullets.map((bullet) => `• ${bullet}`).join("\n"),
      inferPanelImplication(title)
    ])
  ], 0.58, 1.76, 9.72, 3.35, [1.7, 1.18, 5.32, 1.52], {
    body: 12.6,
    header: 12.8,
    rowH: [0.42, 0.92, 0.92, 0.92],
    margin: 2,
    lastCol: true
  });
  callout(s, "판단: 법적 강제 없이 고도화 재활용 공정을 구축한 자발적 사업", 0.78, 5.82, 9.22, 0.52);
  addSourceNotes(s, "슬라이드 6 원문 보존", cards);
  footer(s, 6);
  noteSlide("법적·제도적 추가성", "judgment-evidence row table");
}

function commonPracticeAndBaseline() {
  const s = bodySlide("I. 사전 타당성 검토 상황 | 추가성 입증 ② 보편적 추가성 및 베이스라인 대안", "기존 분리 정제 관행으로 처리 불가하므로 폐수처리와 수입 원료 유지를 기준선으로 설정합니다.", "Baseline");
  panel(s, "보편적 추가성 검토", [
    "국내 폐산 재활용 업체 234개 가동 중",
    "기존 방식은 단일 산 성분 회수 중심의 단순 분리 정제",
    "저순도 폐혼산은 복합 이물질로 기존 기술 처리 한계",
    "스타스테크는 전처리와 축합 공정으로 한계를 극복"
  ], 0.58, 1.55, 4.55, 4.62, { fill: C.pale });
  table(s, [
    ["구분", "대안 내용", "채택"],
    ["대안 1", "본 사업 진행: CIC 제조 및 SHMP 수입 대체", "사업"],
    ["대안 2", "기존 관행 유지: 폐수처리 + 중국산 SHMP 수입", "선정"],
    ["대안 3", "타 업체 폐산 재활용 위탁 처리", "기각"]
  ], 5.38, 1.68, 4.85, 2.75, [1.0, 2.95, 0.9], { body: 11.0, header: 11.4, rowH: [0.44, 0.68, 0.76, 0.62] });
  callout(s, "최종 기준선: 가장 보수적이고 현실적인 대안 2를 베이스라인 시나리오로 선정", 5.38, 5.0, 4.85, 0.68, C.pale2);
  footer(s, 7);
  noteSlide("보편적 추가성 및 대안 평가", "left evidence and right option table");
}

function assessmentBoundary() {
  const s = bodySlide("II. 평가 컨셉 설정 상황 | 감축량 평가 범위", "감축 효과는 수입 원료 제조·물류 회피와 기존 폐수처리 회피로 구분합니다.", "Boundary");
  label(s, "II. 평가 컨셉 설정 | 진행 중", 0.62, 1.32, 2.3, C.sky);
  scenarioBox(s, "사업 前 | 베이스라인", [
    "중국 웨이팡 SHMP 공장: 원료 채굴·정제·중합 배출",
    "해상·육상 장거리 수입 물류 배출",
    "수입 SHMP 국내 사용",
    "저순도 폐혼산은 폐수처리업체 위탁 처리"
  ], 0.55, 1.78, 4.82, C.gray);
  scenarioBox(s, "사업 後 | 프로젝트", [
    "국내 반도체·디스플레이 공장 폐산 단거리 수거",
    "당진공장 전처리·축합 공정 운영",
    "전력·LNG 소비 배출 반영",
    "CIC 생산 후 SHMP 대체 사용"
  ], 5.46, 1.78, 4.82, C.pale);
  s.addShape("roundRect", { x: 1.25, y: 5.78, w: 8.35, h: 0.72, rectRadius: 0.04, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("평가 경계 핵심", tx(1.52, 5.97, 1.55, 0.22, { size: 12.6, bold: true, color: C.sky, align: "center", valign: "middle" }));
  s.addText("SHMP 제조·수입 물류 회피  +  폐혼산 폐수처리 회피", tx(3.2, 5.95, 6.05, 0.26, { size: 13.2, bold: true, color: C.white, align: "center", valign: "middle" }));
  footer(s, 8);
  noteSlide("감축량 평가 범위", "before-after boundary");
}

function formulaConcept() {
  const s = bodySlide("II. 평가 컨셉 설정 상황 | 온실가스 감축량 산정식 컨셉", "감축량은 베이스라인 배출량에서 사업 배출량과 누출량을 차감해 산정합니다.", "Formula");
  s.addShape("roundRect", { x: 0.85, y: 1.45, w: 9.13, h: 0.58, rectRadius: 0.04, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("ER = BE − PE − LE", tx(0.85, 1.65, 9.13, 0.16, { size: 18, bold: true, color: C.white, align: "center" }));
  table(s, [
    ["구분", "산정 항목", "상세 내용"],
    ["BE", "SHMP 신품 제조", "중국 공장 생산 에너지·원료 배출"],
    ["BE", "SHMP 수입 물류", "중국→한국 해상·육상 운송 배출"],
    ["BE", "폐혼산 폐수처리", "기존 처리 공정의 N₂O·CH₄ 포함"],
    ["PE", "국내 수거 물류", "탱크로리 단거리 수거 운송"],
    ["PE", "CIC 생산 전력·LNG", "전처리·축합 공정 에너지 사용"],
    ["LE", "시장 내 원료 누출", "폐기물 활용 구조로 2차 누출량 0 평가"]
  ], 0.75, 2.28, 9.33, 3.7, [1.05, 2.45, 5.83], { body: 11.1, header: 11.5, rowH: [0.4, 0.5, 0.5, 0.5, 0.5, 0.54, 0.54] });
  callout(s, "LE = 0 적용 근거: 폐기물을 원료로 활용해 시장 내 원료 부족이나 대체 생산을 유발하지 않음", 0.9, 6.38, 9.0, 0.34);
  footer(s, 9);
  noteSlide("산정식 컨셉", "formula plus components");
}

function quantSimulation() {
  const s = bodySlide("II. 평가 컨셉 설정 상황 | 정량적 감축량 시뮬레이션", "사전 추정 기준 예상 연간 감축량은 약 3,550 tCO₂eq이며, 방법론 확정 후 정밀 산정합니다.", "Simulation");
  s.addText("본 시뮬레이션은 사전 타당성 단계의 개략 추정치입니다.", tx(0.65, 1.3, 7.6, 0.16, { size: 11, color: C.muted }));
  table(s, [
    ["기초 인자", "단위", "가정값"],
    ["폐산 처리량", "톤/yr", "6,000"],
    ["CIC 생산량", "톤/yr", "1,400"],
    ["전력 소비량", "MWh/yr", "1,470.18"],
    ["LNG 소비량", "Nm³/yr", "623,440"]
  ], 0.6, 1.65, 3.15, 2.2, [1.35, 0.82, 0.98], { body: 11.0, header: 11.2, rowH: [0.4, 0.42, 0.42, 0.42, 0.42] });
  table(s, [
    ["PE 항목", "배출량"],
    ["전력 소비", "약 675"],
    ["LNG 연소", "약 1,371"],
    ["국내 물류", "약 54"],
    ["소계 PE", "약 2,100"]
  ], 4.0, 1.65, 2.9, 2.2, [1.7, 1.2], { body: 11.0, header: 11.2, rowH: [0.4, 0.42, 0.42, 0.42, 0.42], lastCol: true });
  table(s, [
    ["BE 항목", "회피 배출량"],
    ["SHMP 제조", "약 4,900"],
    ["수입 물류", "약 150"],
    ["폐수처리", "약 600"],
    ["소계 BE", "약 5,650"]
  ], 7.12, 1.65, 3.05, 2.2, [1.78, 1.27], { body: 11.0, header: 11.2, rowH: [0.4, 0.42, 0.42, 0.42, 0.42], lastCol: true });
  s.addShape("roundRect", { x: 0.6, y: 4.28, w: 9.57, h: 1.18, rectRadius: 0.04, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("예상 연간 감축량", tx(0.95, 4.55, 2.2, 0.18, { size: 12, bold: true, color: C.sky }));
  s.addText("ER = BE 5,650 − PE 2,100 = 약 3,550 tCO₂eq/yr", tx(2.85, 4.47, 6.8, 0.32, { size: 18.5, bold: true, color: C.white, align: "center" }));
  callout(s, "정밀 산정 시 SHMP 제조 배출계수, 물류 거리, 폐수처리 배출계수의 출처와 적용성을 검증해야 함", 0.78, 6.12, 9.22, 0.34);
  footer(s, 10);
  noteSlide("정량적 감축량 시뮬레이션", "multi-table simulation");
}

function dataRequest() {
  const s = bodySlide("III. 협조 요청 및 향후 계획 | 타당성 검토 요청 자료", "방법론 개발과 PDD 작성에 필요한 핵심 증빙은 제조 LCA, 에너지 모니터링, 사업시작일 자료입니다.", "Data Request");
  label(s, "III. 협조 요청 및 향후 계획", 0.65, 1.32, 2.25, C.navy);
  table(s, [
    ["No.", "구분", "요청 항목", "세부 내용", "기한"],
    ["1", "베이스라인", "중국산 SHMP 제조 LCA", "MSDS 외 에너지·원료 기반 LCA 또는 유사 EPD", "협의"],
    ["2", "사업 배출", "당진공장 에너지 모니터링", "전력·LNG 계측기, 검교정, 모니터링 주기 확인", "협의"],
    ["3", "사업시작일", "양산 최초 달성 공식 증빙", "2025.02.16 품질 성적서, 시험 검사 성적서 등", "협의"]
  ], 0.55, 1.78, 9.75, 3.75, [0.58, 1.35, 2.25, 4.4, 1.17], { body: 11.0, header: 11.3, rowH: [0.46, 0.78, 0.78, 0.78] });
  callout(s, "자료 제출 지연 시 방법론 확정과 검증 일정에 직접 영향을 줄 수 있음", 0.78, 6.22, 9.22, 0.44);
  footer(s, 11);
  noteSlide("요청 자료", "data request tracker");
}

function scheduleSlide() {
  const s = bodySlide("III. 협조 요청 및 향후 계획 | 향후 추진 일정", "현재 1단계 결과를 기준으로 방법론 개발, 등록, 모니터링 인증 대응으로 전환합니다.", "Schedule");
  s.addText("기준일: 업무위임계약서 체결일(2025.12.15)", tx(0.65, 1.3, 5.4, 0.16, { size: 11, color: C.muted }));
  table(s, [
    ["단계", "과업 내용", "기간", "주요 산출물"],
    ["1단계", "법적 추가성, 기준선, 예상 감축량, 개발 방향 확정", "2025.12.15 ~ 2026.04.30", "1단계 결과 보고서"],
    ["2단계", "KCS 방법론, PDD, Validation, 적합성 심의 대응", "1단계 완료 후 ~ 2026.06.30", "KCS 방법론 / PDD / 등록 확인서"],
    ["3단계", "MR 작성, Verification 대응, 1차 감축량 인증", "2단계 완료 후 협의", "MR / 인증 완료 확인서"]
  ], 0.55, 1.72, 9.75, 3.75, [1.15, 4.0, 2.48, 2.12], { body: 11.0, header: 11.3, rowH: [0.46, 0.82, 0.82, 0.82] });
  s.addShape("line", { x: 0.78, y: 6.05, w: 9.25, h: 0, line: { color: C.line, width: 7 } });
  s.addShape("line", { x: 0.78, y: 6.05, w: 3.15, h: 0, line: { color: C.sky, width: 7 } });
  s.addShape("ellipse", { x: 3.75, y: 5.89, w: 0.32, h: 0.32, fill: { color: C.red }, line: { color: C.red } });
  s.addText("현재 위치: 1단계 진행 중", tx(0.78, 6.28, 3.2, 0.16, { size: 11.5, bold: true, color: C.red }));
  footer(s, 12);
  noteSlide("향후 추진 일정", "schedule table and progress bar");
}

function bodySlide(title, message, badge) {
  const s = pptx.addSlide();
  s.background = { color: C.white };
  grid(s, 0, 0, W, 0.72, C.navy2, 70);
  s.addText(title, tx(0.55, 0.18, 7.9, 0.28, { size: 18.2, bold: true, color: C.white }));
  s.addText(message, tx(0.55, 0.92, 7.95, 0.26, { size: 13.6, bold: true, color: C.black }));
  s.addShape("roundRect", { x: 8.24, y: 0.82, w: 2.02, h: 0.4, rectRadius: 0.03, fill: { color: C.pale }, line: { color: C.sky, width: 1 } });
  s.addText(badge, tx(8.34, 0.82, 1.82, 0.4, { size: 11.8, bold: true, color: C.navy, align: "center", valign: "middle" }));
  s.addShape("line", { x: 0.55, y: 1.25, w: 9.75, h: 0, line: { color: C.line, width: 0.8 } });
  return s;
}

function grid(s, x, y, w, h, fill, transparency) {
  s.addShape("rect", { x, y, w, h, fill: { color: fill }, line: { color: fill } });
  for (let gx = x; gx <= x + w + 0.01; gx += 0.28) {
    s.addShape("line", { x: gx, y, w: 0, h, line: { color: C.sky, transparency, width: 0.35 } });
  }
  for (let gy = y + 0.14; gy <= y + h + 0.01; gy += 0.18) {
    s.addShape("line", { x, y: gy, w, h: 0, line: { color: C.sky, transparency, width: 0.35 } });
  }
}

function footer(s, page) {
  s.addShape("line", { x: 0.55, y: 7.02, w: 9.75, h: 0, line: { color: C.line, width: 0.8 } });
  s.addText("INNerGEN", tx(0.55, 7.12, 1.0, 0.12, { size: 11, bold: true, color: C.navy }));
  s.addText("Innovative Ideas | Better Solution", tx(1.55, 7.12, 2.7, 0.12, { size: 11, color: C.muted }));
  s.addText(String(page).padStart(2, "0"), tx(9.8, 7.12, 0.45, 0.12, { size: 11, bold: true, color: C.muted, align: "right" }));
}

function label(s, text, x, y, w, fill) {
  s.addShape("roundRect", { x, y, w, h: 0.3, rectRadius: 0.03, fill: { color: fill }, line: { color: fill } });
  s.addText(text, tx(x + 0.08, y, w - 0.16, 0.3, { size: 11, bold: true, color: C.white, align: "center", valign: "middle" }));
}

function panel(s, title, bullets, x, y, w, h, opt = {}) {
  const fill = opt.fill ?? C.white;
  const judgment = opt.judgment ?? inferPanelJudgment(title);
  const implication = opt.implication ?? inferPanelImplication(title);
  const rows = bullets;
  const rowTop = y + 1.34;
  const rowBottom = y + h - 0.88;
  const rowGap = 0.08;
  const rowH = Math.max(0.42, (rowBottom - rowTop - rowGap * Math.max(0, rows.length - 1)) / Math.max(1, rows.length));
  s.addShape("roundRect", { x, y, w, h, rectRadius: 0.04, fill: { color: fill }, line: { color: opt.border ?? C.line, width: 0.9 } });
  s.addText(title, tx(x + 0.2, y + 0.22, w - 0.4, 0.2, { size: 13.4, bold: true, color: C.navy, align: "center" }));
  s.addShape("roundRect", { x: x + 0.26, y: y + 0.62, w: w - 0.52, h: 0.58, rectRadius: 0.03, fill: { color: C.navy }, line: { color: C.navy } });
  s.addText("핵심 판단", tx(x + 0.42, y + 0.76, 0.86, 0.1, { size: 11, bold: true, color: C.sky, align: "center" }));
  s.addText(judgment, tx(x + 1.3, y + 0.75, w - 1.76, 0.12, { size: 12.2, bold: true, color: C.white, align: "center" }));

  rows.forEach((bullet, i) => {
    const rowY = rowTop + i * (rowH + rowGap);
    s.addShape("roundRect", {
      x: x + 0.26,
      y: rowY,
      w: w - 0.52,
      h: rowH,
      rectRadius: 0.03,
      fill: { color: i % 2 === 0 ? C.white : C.pale2 },
      line: { color: C.line, width: 0.5 }
    });
    s.addText(`근거 ${i + 1}`, tx(x + 0.36, rowY + rowH / 2 - 0.04, 0.56, 0.08, { size: 11, bold: true, color: C.sky, align: "center" }));
    s.addText(bullet, tx(x + 0.96, rowY + 0.08, w - 1.34, rowH - 0.14, { size: rowH >= 0.62 ? 11.2 : 11, color: C.text, valign: "middle" }));
  });

  s.addShape("roundRect", { x: x + 0.26, y: y + h - 0.72, w: w - 0.52, h: 0.44, rectRadius: 0.03, fill: { color: C.pale }, line: { color: C.sky, width: 0.8 } });
  s.addText("의미", tx(x + 0.44, y + h - 0.57, 0.46, 0.08, { size: 11, bold: true, color: C.sky, align: "center" }));
  s.addText(implication, tx(x + 1.02, y + h - 0.58, w - 1.5, 0.12, { size: 11.3, bold: true, color: C.navy, align: "center" }));
}

function inferPanelJudgment(title) {
  if (title.includes("법령")) return "의무 없음";
  if (title.includes("대안")) return "대안 존재";
  if (title.includes("KCS")) return "요건 충족";
  if (title.includes("보편")) return "관행 초과";
  return "판단 가능";
}

function inferPanelImplication(title) {
  if (title.includes("법령")) return "법적 추가성 근거";
  if (title.includes("대안")) return "자발성 입증";
  if (title.includes("KCS")) return "등록 추진 가능";
  if (title.includes("보편")) return "기준선 설정 근거";
  return "후속 검토 연결";
}

function panelEvidenceText(value) {
  if (value.includes("16.5톤")) return "처리 16.5톤/일, 보관 346.5톤";
  if (value.includes("저순도 폐혼산")) return "CIC 물질 재활용 의무 규정 없음";
  if (value.includes("폐수 위탁")) return "폐수 위탁 처리는 합법적 일반 관행";
  if (value.includes("자발적 R&D")) return "합법 대안 있어도 R&D 투자";
  if (value.includes("법적 의무")) return "법적 의무가 아닌 자발적 행위";
  if (value.includes("법적 강제")) return "법적 강제 없이 추진되어 요건 충족";
  return value
    .replace("스타스테크는 ", "")
    .replace("동법 및 시행령·시행규칙 어디에도 ", "")
    .replace("반도체·디스플레이 공정 발생 ", "")
    .replace("반드시 ", "")
    .replace("현행법상 허용되는 ", "")
    .replace("본 사업은 ", "")
    .replace("결론: ", "")
    .replace("KCS 추가성 판단기준: ", "")
    .trim();
}

function scenarioBox(s, title, bullets, x, y, w, fill) {
  const boxH = 3.72;
  const rowH = 0.58;
  const rowGap = 0.11;
  s.addShape("roundRect", { x, y, w, h: boxH, rectRadius: 0.04, fill: { color: fill }, line: { color: fill === C.pale ? C.sky : C.line, width: 1 } });
  s.addText(title, tx(x + 0.25, y + 0.25, w - 0.5, 0.28, { size: 14.5, bold: true, color: C.navy, align: "center", valign: "middle" }));
  bullets.forEach((bullet, i) => {
    const rowY = y + 0.82 + i * (rowH + rowGap);
    s.addShape("roundRect", {
      x: x + 0.26,
      y: rowY,
      w: w - 0.52,
      h: rowH,
      rectRadius: 0.03,
      fill: { color: i % 2 === 0 ? C.white : C.pale2 },
      line: { color: C.line, width: 0.5 }
    });
    s.addText(String(i + 1).padStart(2, "0"), tx(x + 0.37, rowY, 0.42, rowH, { size: 11.6, bold: true, color: C.sky, align: "center", valign: "middle" }));
    s.addShape("line", { x: x + 0.91, y: rowY + 0.12, w: 0, h: rowH - 0.24, line: { color: C.line, width: 0.5 } });
    s.addText(bullet, tx(x + 1.03, rowY + 0.07, w - 1.42, rowH - 0.14, { size: 11.5, color: C.text, valign: "middle", fit: "shrink" }));
  });
}

function callout(s, text, x, y, w, h, fill = C.pale) {
  s.addShape("roundRect", { x, y, w, h, rectRadius: 0.03, fill: { color: fill }, line: { color: C.sky, width: 1 } });
  s.addText(text, tx(x + 0.14, y + 0.11, w - 0.28, h - 0.14, { size: 11.2, bold: true, color: C.navy, align: "center", valign: "middle" }));
}

function table(s, rows, x, y, w, h, colW, opt = {}) {
  const bodySize = opt.body ?? 11;
  const header = rows[0].map((text) => ({
    text,
    options: {
      fill: { color: C.navy },
      color: C.white,
      bold: true,
      fontFace: FONT,
      fontSize: opt.header ?? 11.4,
      align: "center",
      valign: "middle",
      margin: opt.margin ?? 3
    }
  }));
  const body = rows.slice(1).map((r, i) =>
    r.map((text, j) => ({
      text,
      options: {
        fill: { color: i % 2 === 0 ? C.white : C.gray },
        color: opt.lastCol && j === r.length - 1 ? C.navy : C.text,
        bold: j === 0 || (opt.lastCol && j === r.length - 1),
        fontFace: FONT,
        fontSize: bodySize,
        align: j === 0 || j === r.length - 1 ? "center" : "left",
      valign: "middle",
      margin: opt.margin ?? 3,
      breakLine: false
      }
    }))
  );
  s.addTable([header, ...body], {
    x,
    y,
    w,
    h,
    colW,
    rowH: opt.rowH,
    border: { type: "solid", color: C.line, pt: 0.6 },
    fontFace: FONT,
    fontSize: bodySize,
    margin: opt.margin ?? 3,
    breakLine: false
  });
}

function bulletsText(s, bullets, x, y, w, h, opt = {}) {
  const text = bullets.map((bullet) => `• ${bullet}`).join("\n");
  s.addText(text, {
    x,
    y,
    w,
    h,
    fontFace: FONT,
    fontSize: Math.max(MIN_FONT, opt.size ?? 11.1),
    color: opt.color ?? C.text,
    margin: [1, 3, 1, 3],
    fit: "shrink",
    breakLine: false,
    valign: "top",
    paraSpaceAfterPt: opt.gap ?? 2,
    lineSpacingMultiple: 0.94
  });
}

function tx(x, y, w, h, opt = {}) {
  return {
    x,
    y,
    w,
    h,
    fontFace: FONT,
    fontSize: Math.max(MIN_FONT, opt.size ?? 11),
    bold: opt.bold ?? false,
    color: opt.color ?? C.text,
    align: opt.align ?? "left",
    valign: opt.valign ?? "top",
    margin: opt.margin ?? 0,
    breakLine: false,
    fit: opt.fit ?? "shrink"
  };
}

function noteSlide(title, layout) {
  slidesManifest.push({ slideNo: slidesManifest.length + 1, title, layout });
}

function addSourceNotes(s, title, sections) {
  const lines = [title, ""];
  sections.forEach(([heading, items]) => {
    lines.push(`[${heading}]`);
    items.forEach((item) => lines.push(`- ${item}`));
    lines.push("");
  });
  s.addNotes(lines.join("\n"));
}
