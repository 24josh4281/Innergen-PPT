import pptxgen from "pptxgenjs";
import { mkdir, writeFile } from "node:fs/promises";
import { join } from "node:path";

const pptx = new pptxgen();
pptx.author = "INNerGEN";
pptx.company = "INNerGEN";
pptx.subject = "Starstech carbon reduction methodology phase 1 report";
pptx.title = "스타스테크 폐산 재활용 기술 온실가스 감축 방법론 개발 1단계 결과 보고";
pptx.lang = "ko-KR";
pptx.defineLayout({ name: "INNERGEN_27_5X19_05", width: 10.833, height: 7.5 });
pptx.layout = "INNERGEN_27_5X19_05";
pptx.theme = {
  headFontFace: "Malgun Gothic",
  bodyFontFace: "Malgun Gothic",
  lang: "ko-KR"
};
pptx.margin = 0;

const C = {
  navy: "1A2B5F",
  navy2: "12214B",
  sky: "4A90D9",
  pale: "EAF3FC",
  gray: "F4F6F8",
  lightGray: "F4F6F8",
  line: "D7DEE8",
  text: "1F2937",
  ink: "1F2937",
  muted: "667085",
  white: "FFFFFF",
  lightBlue: "EAF3FC",
  green: "18A058",
  red: "D92D20"
};

const W = 10.833;
const H = 7.5;
const FONT = "Malgun Gothic";
const OUT_DIR = "docs/generated/starstech";
const OUT = join(OUT_DIR, "starstech_phase1_carbon_methodology_report_innergen.pptx");
const TEMPLATE_ASSET_DIR = "docs/template-assets/starstech";
const STAR_LOGO = join(TEMPLATE_ASSET_DIR, "stars-logo.png");
const INNERGEN_COLOR = join(TEMPLATE_ASSET_DIR, "innergen-color.png");
const INNERGEN_WHITE = join(TEMPLATE_ASSET_DIR, "innergen-white.png");
const PAGE_ICON = join(TEMPLATE_ASSET_DIR, "page-icon-white.png");
const INNERGEN_ILLUSTRATION = join(TEMPLATE_ASSET_DIR, "innergen-illustration.png");

function addGridBand(slide, x, y, w, h, fill = C.navy2) {
  slide.addShape("rect", { x, y, w, h, fill: { color: fill }, line: { color: fill } });
  for (let gx = x; gx <= x + w + 0.01; gx += 0.18) {
    slide.addShape("line", { x: gx, y, w: 0, h, line: { color: "315070", transparency: 28, width: 0.45 } });
  }
  for (let gy = y; gy <= y + h + 0.01; gy += 0.18) {
    slide.addShape("line", { x, y: gy, w, h: 0, line: { color: "315070", transparency: 28, width: 0.45 } });
  }
}

function addHeader(slide, title, section = "") {
  slide.background = { color: C.white };
  addGridBand(slide, 0, 0, 8.65, 0.72, C.navy2);
  slide.addShape("rect", { x: 8.65, y: 0, w: W - 8.65, h: 0.72, fill: { color: C.white }, line: { color: C.white } });
  slide.addImage({ path: STAR_LOGO, x: 9.25, y: 0.18, w: 1.05, h: 0.32 });
  slide.addText(title, {
    x: 0.38,
    y: 0.12,
    w: 8.05,
    h: 0.36,
    fontFace: FONT,
    fontSize: 19.5,
    bold: true,
    color: C.white,
    breakLine: false,
    margin: 0
  });
  if (section) {
    slide.addShape("ellipse", { x: 0.16, y: 0.93, w: 0.19, h: 0.19, fill: { color: "B8B8B8" }, line: { color: "B8B8B8" } });
    slide.addShape("ellipse", { x: 0.28, y: 0.9, w: 0.22, h: 0.22, fill: { color: C.navy }, line: { color: C.navy } });
    slide.addText(section, { x: 0.56, y: 0.91, w: 7.8, h: 0.24, fontFace: FONT, fontSize: 12.8, bold: true, color: "000000", margin: 0 });
  }
}

function footer(slide, page) {
  addGridBand(slide, 0, 6.92, W, 0.58, C.navy2);
  slide.addImage({ path: INNERGEN_WHITE, x: 0.22, y: 7.02, w: 0.72, h: 0.36 });
  slide.addText("Innovative Ideas  |  Better Solution", { x: 1.18, y: 7.17, w: 2.7, h: 0.1, fontFace: FONT, fontSize: 6.5, color: C.white, margin: 0 });
  slide.addText("Copyright © 2026 INNerGEN Co Ltd.\nAll rights reserved.", { x: 4.35, y: 7.08, w: 2.2, h: 0.22, fontFace: FONT, fontSize: 6.0, color: C.white, align: "center", margin: 0 });
  slide.addImage({ path: PAGE_ICON, x: 9.88, y: 7.06, w: 0.43, h: 0.28 });
  slide.addShape("ellipse", { x: 10.18, y: 7.0, w: 0.38, h: 0.38, fill: { color: C.navy2, transparency: 100 }, line: { color: C.white, width: 1.2 } });
  slide.addText(String(page), { x: 10.29, y: 7.1, w: 0.14, h: 0.12, fontFace: FONT, fontSize: 10, bold: true, color: C.white, align: "center", margin: 0 });
}

function labelBox(slide, text, x, y, w, color = C.navy) {
  slide.addShape("roundRect", { x, y, w, h: 0.33, rectRadius: 0.03, fill: { color }, line: { color } });
  slide.addText(text, { x: x + 0.08, y: y + 0.1, w: w - 0.16, h: 0.1, fontFace: FONT, fontSize: 8.2, bold: true, color: C.white, align: "center", margin: 0 });
}

function addNote(slide, text, x, y, w, h = 0.34, fill = C.pale, border = C.sky) {
  slide.addShape("roundRect", { x, y, w, h, rectRadius: 0.03, fill: { color: fill }, line: { color: border, width: 1 } });
  slide.addText(text, { x: x + 0.12, y: y + 0.11, w: w - 0.24, h: h - 0.15, fontFace: FONT, fontSize: 8.4, bold: true, color: C.navy, margin: 0 });
}

function addBulletBlock(slide, title, bullets, x, y, w, h, opts = {}) {
  if (title) {
    slide.addText(title, { x, y, w, h: 0.22, fontFace: FONT, fontSize: opts.titleSize ?? 10.5, bold: true, color: opts.titleColor ?? C.navy, margin: 0 });
  }
  slide.addText(bullets.map((b) => `• ${b}`).join("\n"), {
    x,
    y: y + (title ? 0.35 : 0),
    w,
    h: h - (title ? 0.35 : 0),
    fontFace: FONT,
    fontSize: opts.size ?? 8.6,
    color: opts.color ?? C.text,
    breakLine: false,
    margin: [1, 2, 1, 2],
    valign: "top",
    paraSpaceAfterPt: 2,
    breakLine: false
  });
}

function table(slide, rows, x, y, w, h, colW, opts = {}) {
  const headerFill = opts.headerFill ?? C.navy;
  const header = rows[0].map((text) => ({
    text,
    options: {
      fill: { color: headerFill },
      color: C.white,
      bold: true,
      fontFace: FONT,
      fontSize: opts.headerSize ?? 7.6,
      align: "center",
      valign: "middle",
      margin: 3
    }
  }));
  const body = rows.slice(1).map((r, i) =>
    r.map((text, j) => ({
      text,
      options: {
        fill: { color: i % 2 === 0 ? C.white : C.gray },
        color: opts.lastColColor && j === r.length - 1 ? opts.lastColColor : C.text,
        bold: (opts.boldLastCol && j === r.length - 1) || (opts.boldFirstCol && j === 0),
        fontFace: FONT,
        fontSize: opts.bodySize ?? 6.6,
        align: j === r.length - 1 || opts.centerCols?.includes(j) ? "center" : "left",
        valign: "middle",
        margin: 3,
        breakLine: false
      }
    }))
  );
  slide.addTable([header, ...body], {
    x,
    y,
    w,
    h,
    colW,
    rowH: opts.rowH,
    border: { type: "solid", color: C.line, pt: 0.6 },
    fontFace: FONT,
    fontSize: opts.bodySize ?? 6.6,
    margin: 3,
    breakLine: false
  });
}

function processSlide() {
  const slide = pptx.addSlide();
  addHeader(slide, "(공통) 과업 프로세스", "과업 추진 전체 프로세스 (요약)");
  const steps = [
    ["1단계", "사전 타당성 검토", "현재 진행", ["법적·제도적 추가성 검토", "베이스라인 시나리오 설정", "예상 감축량 산정", "방법론 개발 방향 확정"]],
    ["2단계", "방법론 및 사업계획 개발", "", ["KCS 신규 방법론 문서 작성", "PDD(사업계획서) 작성", "내부 검토 및 보완"]],
    ["3단계", "제3자 검증 (Validation)", "", ["외부 검증기관 선정", "Validation 대응 및 보완", "최종 검증 완료"]],
    ["4단계", "제출 및 인증기관 대응", "", ["KCS 등록 신청서 제출", "적합성 심의 대응", "최종 등록 완료"]]
  ];
  slide.addText("▪ 이너젠은 스타스테크 폐산 재활용 기술 및 제품에 대하여, 온실가스 감축 평가 방법을 도출하고 탄소시장 등록 가능성에 대한 타당성 검토를 진행함.", {
    x: 0.55, y: 1.38, w: 9.7, h: 0.35, fontFace: FONT, fontSize: 12.6, color: "000000", margin: 0, breakLine: false
  });
  slide.addText("▪ ①사전 타당성 검토 완료 후, ‘②방법론 및 사업계획서 개발, ③제3자 검증, ④제출 및 인증기관 대응’ 일체를 지원 예정임.", {
    x: 0.55, y: 1.86, w: 9.7, h: 0.32, fontFace: FONT, fontSize: 12.2, bold: true, color: "000000", margin: 0, breakLine: false
  });
  slide.addText("※ 단, ‘①사전 타당성 검토’ 이후 후속 업무 추진 여부 상호 협의 결정", {
    x: 0.55, y: 2.22, w: 8.8, h: 0.18, fontFace: FONT, fontSize: 9.5, color: "7A7A7A", margin: 0
  });
  slide.addShape("line", { x: 0.58, y: 3.22, w: 9.55, h: 0, line: { color: "D8D8D8", width: 10, beginArrowType: "none", endArrowType: "triangle" } });
  const x0 = 0.75;
  const y = 2.88;
  const boxW = 2.22;
  steps.forEach((s, i) => {
    const x = x0 + i * 2.36;
    const headerColor = i === 0 ? C.sky : i === 1 ? C.navy : i === 2 ? "9A9360" : "E66A00";
    slide.addShape("rect", { x, y, w: boxW, h: 0.48, fill: { color: headerColor }, line: { color: headerColor } });
    slide.addText(`${i === 0 ? "1-1)" : i === 1 ? "2-1)" : i === 2 ? "2-2)" : "2-3)"} ${s[1]}`, { x: x + 0.08, y: y + 0.15, w: boxW - 0.16, h: 0.13, fontFace: FONT, fontSize: 10.2, bold: true, color: C.white, align: "center", margin: 0 });
    slide.addShape("rect", { x, y: y + 0.55, w: boxW, h: 2.9, fill: { color: C.white }, line: { color: "B8B8B8", width: 0.8 } });
    if (s[2]) {
      slide.addShape("rect", { x: x + 1.34, y: y - 0.48, w: 0.86, h: 0.42, fill: { color: "F04438" }, line: { color: "F04438" } });
      slide.addText(`★ ${s[2]}`, { x: x + 1.42, y: y - 0.33, w: 0.66, h: 0.1, fontFace: FONT, fontSize: 6.8, bold: true, color: C.white, align: "center", margin: 0 });
    }
    slide.addText(i === 0 ? "2~3개월" : i === 1 ? "약 2~3개월" : i === 2 ? "약 1개월" : "대관상의: 약 1~3개월", {
      x: x + 0.28, y: y + 0.9, w: boxW - 0.56, h: 0.18, fontFace: FONT, fontSize: 10.5, italic: true, bold: true, color: C.sky, align: "center", margin: 0
    });
    addBulletBlock(slide, "", s[3], x + 0.18, y + 1.35, boxW - 0.35, 1.75, { size: 8.8, color: "000000" });
  });
  slide.addShape("rect", { x: 0.72, y: 2.4, w: 2.23, h: 0.35, fill: { color: "D99595" }, line: { color: "D99595" } });
  slide.addText("1단계", { x: 1.64, y: 2.52, w: 0.48, h: 0.1, fontFace: FONT, fontSize: 8.8, bold: true, color: C.white, margin: 0 });
  slide.addShape("rect", { x: 3.12, y: 2.4, w: 6.95, h: 0.35, fill: { color: "D99595" }, line: { color: "D99595" } });
  slide.addText("2단계", { x: 6.55, y: 2.52, w: 0.48, h: 0.1, fontFace: FONT, fontSize: 8.8, bold: true, color: C.white, margin: 0 });
  footer(slide, 2);
}

function cover() {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };
  slide.addImage({ path: STAR_LOGO, x: 0.27, y: 0.32, w: 1.55, h: 0.47 });
  slide.addText("2026.03.\n회의 자료", { x: 9.15, y: 0.32, w: 1.05, h: 0.42, fontFace: FONT, fontSize: 12.5, bold: true, color: "000000", align: "right", margin: 0, breakLine: false });
  slide.addShape("line", { x: 0, y: 0.92, w: W, h: 0, line: { color: C.navy2, width: 2.2 } });
  slide.addText("스타스테크 폐산 재활용 기술에 의한\n온실가스 감축 방법론 개발\n1단계 결과 보고", {
    x: 1.6, y: 2.12, w: 7.65, h: 1.28, fontFace: FONT, fontSize: 24.5, bold: true, color: "000000", align: "center", margin: 0, breakLine: false
  });
  slide.addText("사전 타당성 평가 결과 보고 회의 자료", { x: 2.8, y: 3.72, w: 5.15, h: 0.24, fontFace: FONT, fontSize: 12.2, bold: true, color: C.navy, align: "center", margin: 0 });
  slide.addImage({ path: INNERGEN_COLOR, x: 4.46, y: 4.55, w: 1.9, h: 0.92 });
  addGridBand(slide, 0, 6.82, W, 0.68, C.navy2);
  slide.addText("CO₂   |   Consulting   |   Client", { x: 3.35, y: 7.03, w: 4.35, h: 0.25, fontFace: FONT, fontSize: 13.5, bold: true, color: C.white, align: "center", margin: 0, breakLine: false });
}

function contents() {
  const slide = pptx.addSlide();
  addHeader(slide, "Contents");
  slide.addImage({ path: INNERGEN_ILLUSTRATION, x: 0.15, y: 1.35, w: 5.25, h: 4.55 });
  const items = [
    ["I.", "사전 타당성 검토 상황"],
    ["II.", "평가 컨셉 설정 상황  ※ 진행 중"],
    ["III.", "협조 요청 및 향후 계획"]
  ];
  items.forEach((item, i) => {
    const y = 1.85 + i * 1.42;
    const active = i === 0;
    slide.addText(`${item[0]} ${item[1]}`, { x: 5.45, y, w: 4.6, h: 0.34, fontFace: FONT, fontSize: active ? 18.5 : 17.5, bold: true, color: active ? C.navy : "CFCFCF", margin: 0 });
    slide.addShape("line", { x: 5.35, y: y + 0.52, w: 4.85, h: 0, line: { color: active ? C.navy : "D7D7D7", width: active ? 1.2 : 0.8 } });
  });
  slide.addShape("rect", { x: 5.25, y: 1.72, w: 0.08, h: 4.1, fill: { color: C.navy }, line: { color: C.navy } });
  footer(slide, 3);
}

function slide4() {
  const slide = pptx.addSlide();
  addHeader(slide, "I. 사전 타당성 검토 상황 | 종합 평가", "I. 사전 타당성 검토");
  table(slide, [
    ["평가항목", "판정기준", "스타스테크 폐산 재활용 사업", "판정"],
    ["추가성 입증", "법적 의무 부재 및 현실적 투자 장벽 존재", "「폐기물관리법」상 의무 없음 / 기존 분리 정제 방식으로 저순도 폐혼산 처리 불가 → 자발적 투자", "○"],
    ["감축 기술 적합성", "온실가스 감축에 직·간접 기여하는 기술", "물리·화학적 재활용 공정으로 제3의 원료(CIC) 생산 → 수입 신품 원료 대체", "○"],
    ["기술 보급 현황", "산업 내 보편적 관행 초과 수준", "국내 234개 폐산 재활용 업체 대비 저순도 폐혼산 100% 자원화는 보편적 관행 초과", "○"],
    ["온실가스 감축 효과", "정량적 감축 효과 산출 가능 여부", "수입 원료(SHMP) 대체 회피 배출 + 폐수처리 억제 효과로 정량 산출 가능", "○"],
    ["방법론 존재 여부", "기존 KCS 방법론 적용 가능 여부", "기존 유사 방법론 적용 불가 → 수입 물류 대체, 폐혼산 복합 공정 반영 신규 개발 필요", "신규개발"],
    ["예상 감축량", "사업 등록 최소 기준 충족 여부", "연간 약 3,550 tCO₂eq 예상 (기준 초과)", "○"]
  ], 0.25, 1.24, 10.35, 5.12, [1.6, 2.85, 5.0, 0.9], { bodySize: 8.2, headerSize: 10.4, boldFirstCol: true, boldLastCol: true, lastColColor: C.navy, centerCols: [3] });
  addNote(slide, "종합 판정: 6개 평가항목 중 5개 ○ 판정, 방법론 신규 개발 조건 하에 KCS 사업 등록 추진 타당", 0.55, 6.42, 9.75, 0.36);
  footer(slide, 4);
}

function slide5() {
  const slide = pptx.addSlide();
  addHeader(slide, "I. 사전 타당성 검토 상황 | 사업 요건 상세", "Business Requirements");
  table(slide, [
    ["항목", "검토 사항", "검토 결과"],
    ["방법론명(안)", "KCS 신규 방법론 제안명", "사업장 폐산의 화학적 재활용을 통한 신품 화학원료 대체 감축 방법론"],
    ["사업 시작일", "파리협정 발효일(2016.11.04) 이후 설비 가동 또는 감축 효과 최초 발생일", "R&D 시작일 2024.07.01 / 설비 설치 예상일 2025.02.09 / 품질규격 최초 달성일 2025.02.16 → 실제 감축 효과 발생 시점인 2025.02.16을 사업 시작일로 설정 타당"],
    ["인증유효기간", "KCS 기준 인증 유효기간", "승인연도 기준 5년"],
    ["감축사업 유형", "KCS 감축사업 분류", "물질 재활용(Material Recycling) 유형"],
    ["적용 기준선", "베이스라인 설정 방식", "폐수처리 + 수입 신품 원료 사용 관행 (대안 2)"]
  ], 0.55, 1.16, 9.75, 5.55, [1.6, 3.15, 5.0], { bodySize: 7.8, headerSize: 8.7, rowH: [0.46, 0.72, 1.42, 0.68, 0.68, 0.78] });
  footer(slide, 5);
}

function slide6() {
  const slide = pptx.addSlide();
  addHeader(slide, "I. 사전 타당성 검토 상황 | 추가성 입증 ① 법적·제도적 추가성", "Additionality");
  labelBox(slide, "[참고] 법적·제도적 추가성 상세 내용", 0.55, 0.98, 2.85);
  [
    [0.68, 1.52, 9.45, 1.18],
    [0.68, 3.0, 9.45, 1.08],
    [0.68, 4.38, 9.45, 1.08]
  ].forEach(([x, y, w, h]) => {
    slide.addShape("rect", { x, y, w, h, fill: { color: "F8FAFC" }, line: { color: "D7DEE8", width: 0.6 } });
    slide.addShape("rect", { x, y, w: 0.08, h, fill: { color: C.navy }, line: { color: C.navy } });
  });
  addBulletBlock(slide, "■ 관련 법령 검토", [
    "스타스테크는 「폐기물관리법」에 따라 1일 16.5톤 처리, 346.5톤 보관시설 인허가를 득하여 적법 운영 중",
    "동법 및 시행령·시행규칙에 저순도 폐혼산을 반드시 전처리·축합하여 제3의 화학제품(CIC)으로 물질 재활용해야 한다는 의무 규정 없음"
  ], 0.85, 1.68, 9.05, 0.86, { size: 9.6, titleSize: 11.0 });
  addBulletBlock(slide, "■ 합법적 대안 존재 확인", [
    "폐수 위탁 처리는 현행법상 허용되는 합법적 관행이며 저순도 폐혼산 처리의 일반적 방식",
    "본 사업은 합법적 대안(폐수처리)이 존재함에도 자발적 R&D 투자로 고도화 재활용 공정을 구축"
  ], 0.85, 3.12, 9.05, 0.78, { size: 9.6, titleSize: 11.0 });
  addBulletBlock(slide, "■ KCS 법적·제도적 추가성 요건 충족 여부", [
    "KCS 추가성 판단기준: '법적 의무가 아닌 자발적 행위일 것' → 완벽 충족",
    "결론: 법적 강제 없이 자발적 투자로 추진되어 KCS의 법적·제도적 추가성 요건 완벽 충족"
  ], 0.85, 4.5, 9.05, 0.78, { size: 9.6, titleSize: 11.0 });
  addNote(slide, "판단: 현행 법령상 의무가 아닌 자발적 투자이며, 합법적 대안 대비 추가적 감축 행위로 해석 가능", 0.72, 6.08, 9.35, 0.42);
  footer(slide, 6);
}

function slide7() {
  const slide = pptx.addSlide();
  addHeader(slide, "I. 사전 타당성 검토 상황 | 추가성 입증 ② 보편적 추가성 및 베이스라인 대안", "Baseline Alternatives");
  slide.addShape("roundRect", { x: 0.45, y: 1.05, w: 4.8, h: 4.9, rectRadius: 0.03, fill: { color: C.gray }, line: { color: C.line } });
  addBulletBlock(slide, "■ 보편적 추가성 검토", [
    "국내 폐산 재활용 업체 234개 가동 중",
    "기존 재활용 방식은 단일 산 성분(HF, HCl, H₂SO₄ 등) 회수 중심의 단순 분리 정제 방식",
    "반도체·디스플레이 발 저순도 폐혼산은 복합 이물질 다량 함유로 기존 기술 처리 불가",
    "산업 관행은 전량 폐수 위탁 처리이며, 스타스테크는 화학적 전처리 + 축합 공정으로 보편적 한계를 극복"
  ], 0.7, 1.35, 4.3, 4.15, { size: 8.1 });
  table(slide, [
    ["구분", "대안 내용", "채택 여부"],
    ["대안 1", "본 사업 진행 (CIC 제조 및 SHMP 수입 대체)", "사업 시나리오"],
    ["대안 2", "기존 관행 유지 (저순도 폐산 전량 폐수처리 + 중국산 신품 SHMP 지속 수입)", "최종 베이스라인 선정"],
    ["대안 3", "타 업체를 통한 폐산 재활용 위탁 처리", "기각 (기존 업체 기술적 한계)"]
  ], 5.55, 1.28, 4.85, 3.5, [0.75, 2.85, 1.25], { bodySize: 7.4, headerSize: 8.1, boldLastCol: true });
  addNote(slide, "결론: 가장 보수적이고 현실적인 '대안 2(폐수처리 + 수입 원료 관행 유지)'를 최종 베이스라인 시나리오로 선정", 5.55, 5.18, 4.85, 0.55);
  footer(slide, 7);
}

function slide8() {
  const slide = pptx.addSlide();
  addHeader(slide, "II. 평가 컨셉 설정 상황 | 감축량 평가 범위 (사업 전·후 비교)", "II. 평가 컨셉 설정");
  const colW = 4.7;
  slide.addShape("roundRect", { x: 0.55, y: 1.32, w: colW, h: 4.35, rectRadius: 0.03, fill: { color: C.gray }, line: { color: C.line } });
  slide.addShape("roundRect", { x: 5.58, y: 1.32, w: colW, h: 4.35, rectRadius: 0.03, fill: { color: C.pale }, line: { color: C.sky } });
  slide.addText("사업 前 (베이스라인)", { x: 0.85, y: 1.68, w: 3.9, h: 0.18, fontFace: FONT, fontSize: 11.2, bold: true, color: C.red, margin: 0 });
  slide.addText("사업 後 (프로젝트)", { x: 5.88, y: 1.68, w: 3.9, h: 0.18, fontFace: FONT, fontSize: 11.2, bold: true, color: C.green, margin: 0 });
  const baseline = [
    ["01", "중국 웨이팡 SHMP 공장", "원료 채굴·정제·중합 과정 CO₂ 배출"],
    ["02", "장거리 수입 물류", "해상·육상 운송 연료 연소 CO₂ 배출"],
    ["03", "국내 사용", "수입 SHMP를 제설제 등으로 사용"],
    ["04", "폐혼산 폐수처리", "위탁 처리 과정 N₂O·CH₄ 배출"]
  ];
  const project = [
    ["01", "폐산 단거리 수거", "국내 반도체·디스플레이 공장 폐산 운반"],
    ["02", "전처리·축합 공정", "당진공장 전력·LNG 소비 발생"],
    ["03", "CIC 생산 및 대체", "복합무기인산염 생산 → SHMP 대체 사용"]
  ];
  baseline.forEach((row, i) => {
    const y = 2.1 + i * 0.72;
    slide.addShape("roundRect", { x: 0.86, y, w: 3.85, h: 0.48, rectRadius: 0.03, fill: { color: C.white }, line: { color: "D7DEE8", width: 0.6 } });
    slide.addShape("ellipse", { x: 1.02, y: y + 0.12, w: 0.25, h: 0.25, fill: { color: C.red }, line: { color: C.red } });
    slide.addText(row[0], { x: 1.055, y: y + 0.18, w: 0.18, h: 0.07, fontFace: FONT, fontSize: 6.4, bold: true, color: C.white, align: "center", margin: 0 });
    slide.addText(row[1], { x: 1.42, y: y + 0.08, w: 2.95, h: 0.11, fontFace: FONT, fontSize: 9.3, bold: true, color: C.ink, margin: 0 });
    slide.addText(row[2], { x: 1.42, y: y + 0.3, w: 2.95, h: 0.09, fontFace: FONT, fontSize: 7.2, color: C.muted, margin: 0 });
  });
  project.forEach((row, i) => {
    const y = 2.18 + i * 0.9;
    slide.addShape("roundRect", { x: 5.9, y, w: 3.85, h: 0.56, rectRadius: 0.03, fill: { color: C.white }, line: { color: "B7D7F4", width: 0.8 } });
    slide.addShape("ellipse", { x: 6.08, y: y + 0.15, w: 0.26, h: 0.26, fill: { color: C.green }, line: { color: C.green } });
    slide.addText(row[0], { x: 6.115, y: y + 0.21, w: 0.18, h: 0.07, fontFace: FONT, fontSize: 6.4, bold: true, color: C.white, align: "center", margin: 0 });
    slide.addText(row[1], { x: 6.48, y: y + 0.11, w: 2.85, h: 0.11, fontFace: FONT, fontSize: 9.5, bold: true, color: C.ink, margin: 0 });
    slide.addText(row[2], { x: 6.48, y: y + 0.34, w: 2.85, h: 0.09, fontFace: FONT, fontSize: 7.3, color: C.muted, margin: 0 });
  });
  slide.addShape("line", { x: 4.95, y: 3.22, w: 0.45, h: 0, line: { color: C.navy, width: 2, endArrowType: "triangle" } });
  slide.addShape("roundRect", { x: 1.15, y: 5.95, w: 8.55, h: 0.78, rectRadius: 0.03, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("평가 경계 핵심: 효과 1) 수입 원료(SHMP) 제조 및 장거리 수입 물류 배출 회피   효과 2) 기존 폐혼산 폐수처리 배출 회피", {
    x: 1.35, y: 6.22, w: 8.15, h: 0.2, fontFace: FONT, fontSize: 8.7, bold: true, color: C.white, align: "center", margin: 0
  });
  footer(slide, 8);
}

function slide9() {
  const slide = pptx.addSlide();
  addHeader(slide, "II. 평가 컨셉 설정 상황 | 온실가스 감축량 산정식 컨셉", "Calculation Concept");
  slide.addText("▪ 감축 방법론 대상 기술을 합리적·보수적으로 평가하기 위해 BE, PE, LE 산정 항목을 구분하여 산정", {
    x: 0.55, y: 1.26, w: 9.75, h: 0.2, fontFace: FONT, fontSize: 10.8, color: "000000", margin: 0
  });
  slide.addShape("roundRect", { x: 0.85, y: 1.62, w: 9.15, h: 0.54, rectRadius: 0.03, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("ER (감축량) = BE (베이스라인 배출량) − PE (사업 배출량) − LE (누출량)", {
    x: 1.02, y: 1.82, w: 8.8, h: 0.13, fontFace: FONT, fontSize: 13.5, bold: true, color: C.white, align: "center", margin: 0
  });

  const blocks = [
    {
      key: "BE",
      title: "① 베이스라인 배출량",
      fill: "FCEBDD",
      items: ["SHMP 신품 제조 배출량", "SHMP 수입 장거리 물류 배출량", "폐혼산 폐수처리 배출량"],
      note: "기존 관행 유지 시 발생하는 제조·물류·처리 배출량"
    },
    {
      key: "PE",
      title: "② 사업 배출량",
      fill: "FCEBDD",
      items: ["폐산 국내 수거 물류 배출량", "CIC 생산 공정 전력 배출량", "CIC 생산 공정 LNG 배출량"],
      note: "프로젝트 수행 과정에서 실제 발생하는 에너지·물류 배출량"
    },
    {
      key: "LE",
      title: "③ 누출량",
      fill: "FCEBDD",
      items: ["시장 내 원료 누출 평가", "폐기물 원료 활용 구조", "2차 누출량 0 적용"],
      note: "원료 공급량을 줄이거나 대체 생산을 유발하지 않음"
    }
  ];
  blocks.forEach((b, i) => {
    const x = 0.75 + i * 3.35;
    slide.addShape("rect", { x, y: 2.55, w: 3.0, h: 0.42, fill: { color: i === 2 ? "91D050" : "2F8AA0" }, line: { color: i === 2 ? "6CA92F" : "2F8AA0" } });
    slide.addText(i === 2 ? "존재 시, 규명 필요" : "메인 평가 내용", { x, y: 2.68, w: 3.0, h: 0.1, fontFace: FONT, fontSize: 8.6, bold: true, color: C.white, align: "center", margin: 0 });
    slide.addShape("rect", { x, y: 3.02, w: 3.0, h: 0.56, fill: { color: b.fill }, line: { color: "A8A8A8", width: 0.6 } });
    slide.addText(`${b.title}`, { x: x + 0.16, y: 3.23, w: 2.68, h: 0.1, fontFace: FONT, fontSize: 10.8, bold: true, color: "000000", align: "center", margin: 0 });
    slide.addShape("rect", { x, y: 3.72, w: 3.0, h: 1.55, fill: { color: C.white }, line: { color: "B7B7B7", transparency: 20, width: 0.8, dash: "dash" } });
    slide.addText(b.items.map((item) => `• ${item}`).join("\n"), { x: x + 0.24, y: 4.0, w: 2.52, h: 0.52, fontFace: FONT, fontSize: 8.4, bold: true, color: C.navy, margin: 0, breakLine: false });
    slide.addText(b.note, { x: x + 0.24, y: 4.68, w: 2.52, h: 0.32, fontFace: FONT, fontSize: 7.5, color: C.muted, align: "center", margin: 0, breakLine: false });
    if (i < 2) {
      slide.addText("−", { x: x + 3.06, y: 3.17, w: 0.25, h: 0.15, fontFace: FONT, fontSize: 20, bold: true, color: "000000", margin: 0 });
    }
  });

  slide.addShape("roundRect", { x: 0.55, y: 5.6, w: 9.75, h: 0.78, rectRadius: 0.03, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("평가 경계 핵심", { x: 0.92, y: 5.87, w: 1.25, h: 0.12, fontFace: FONT, fontSize: 9.5, bold: true, color: C.sky, margin: 0 });
  slide.addShape("roundRect", { x: 2.32, y: 5.79, w: 3.45, h: 0.33, rectRadius: 0.03, fill: { color: "34477B" }, line: { color: "4A5F95", width: 0.6 } });
  slide.addShape("roundRect", { x: 6.05, y: 5.79, w: 3.45, h: 0.33, rectRadius: 0.03, fill: { color: "34477B" }, line: { color: "4A5F95", width: 0.6 } });
  slide.addText("효과 1: SHMP 제조·수입 물류 배출 회피", { x: 2.48, y: 5.91, w: 3.1, h: 0.08, fontFace: FONT, fontSize: 7.7, bold: true, color: C.white, margin: 0 });
  slide.addText("효과 2: 기존 폐혼산 폐수처리 배출 회피", { x: 6.22, y: 5.91, w: 3.05, h: 0.08, fontFace: FONT, fontSize: 7.7, bold: true, color: C.white, margin: 0 });
  footer(slide, 9);
}

function smallTable(slide, title, rows, x, y, w, h, colW) {
  slide.addText(title, { x, y, w, h: 0.18, fontFace: FONT, fontSize: 8.2, bold: true, color: C.navy, margin: 0 });
  table(slide, rows, x, y + 0.25, w, h - 0.25, colW, { bodySize: 6.35, headerSize: 7.0, boldLastCol: true });
}

function slide10() {
  const slide = pptx.addSlide();
  addHeader(slide, "II. 평가 컨셉 설정 상황 | 정량적 감축량 시뮬레이션 (연간 기준)", "ER Simulation");
  slide.addText("※ 본 시뮬레이션은 사전 타당성 평가 단계의 개략 추정치이며, 방법론 확정 후 정밀 산정 예정", {
    x: 0.55, y: 0.86, w: 9.8, h: 0.18, fontFace: FONT, fontSize: 7.5, color: C.muted, margin: 0
  });
  smallTable(slide, "[표 1] 사업 기초 데이터 가정", [
    ["인자", "단위", "가정값", "비고"],
    ["연간 폐산 처리량", "톤/yr", "6,000", "당진공장 설계 용량 기준"],
    ["연간 CIC 생산량", "톤/yr", "1,400", "폐산 대비 CIC 전환율 적용"],
    ["연간 전력 소비량", "MWh/yr", "1,470.18", "공정 계측 기준"],
    ["연간 LNG 소비량", "Nm³/yr", "623,440", "공정 계측 기준"]
  ], 0.42, 1.15, 4.95, 2.0, [1.45, 0.65, 0.8, 2.05]);
  smallTable(slide, "[표 2] 사업 배출량(PE) 시뮬레이션", [
    ["배출원", "산정식 (개략)", "배출량"],
    ["전력 소비", "1,470.18 MWh × 0.4594 tCO₂/MWh", "약 675"],
    ["LNG 연소", "623,440 Nm³ × 2.198 kgCO₂/Nm³ ÷ 1,000", "약 1,371"],
    ["국내 물류", "탱크로리 수거 운송 거리·중량 기반 산정", "약 54"],
    ["소계 (PE)", "", "약 2,100"]
  ], 5.62, 1.15, 4.78, 2.0, [1.25, 2.55, 0.98]);
  smallTable(slide, "[표 3] 베이스라인 배출량(BE) 시뮬레이션", [
    ["배출원", "산정식 (개략)", "배출량"],
    ["SHMP 제조 회피", "1,400톤 × 3.5 tCO₂/톤", "약 4,900"],
    ["장거리 수입 물류 회피", "중국→한국 해상운송 거리·중량 기반", "약 150"],
    ["폐수처리 회피", "6,000톤 × 0.1 tCO₂/톤", "약 600"],
    ["소계 (BE)", "", "약 5,650"]
  ], 0.42, 3.55, 6.25, 2.0, [1.6, 3.45, 1.2]);
  slide.addShape("roundRect", { x: 6.95, y: 3.88, w: 3.45, h: 1.45, rectRadius: 0.03, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("예상 연간 감축량 (ER)\n= BE 5,650 − PE 2,100\n= 약 3,550 tCO₂eq/yr", {
    x: 7.13, y: 4.18, w: 3.08, h: 0.78, fontFace: FONT, fontSize: 12.5, bold: true, color: C.white, align: "center", margin: 0, breakLine: false
  });
  footer(slide, 10);
}

function slide11() {
  const slide = pptx.addSlide();
  addHeader(slide, "III. 협조 요청 및 향후 계획 | 타당성 검토를 위한 요청 자료 (1차)", "Data Request");
  table(slide, [
    ["No.", "구분", "요청 항목", "세부 내용", "제출 기한"],
    ["1", "베이스라인 관련", "중국산 SHMP 제조 공정 LCA 데이터", "MSDS 외 투입 에너지·원료 기반 제조 공정 LCA 데이터 또는 유사 EPD 자료", "협의 후 결정"],
    ["2", "사업 배출 관련", "당진공장 에너지 모니터링 체계 점검표", "전력·LNG 계측기 검교정 여부, 모니터링 주기·방식 확인을 위한 현장 점검표", "협의 후 결정"],
    ["3", "사업시작일 증빙", "양산 최초 달성 공식 증빙 문서", "2025.02.16 품질규격 최초 달성 관련 품질 성적서, 시험 검사 성적서 등 공식 문서", "협의 후 결정"]
  ], 0.55, 1.36, 9.75, 4.08, [0.55, 1.25, 2.45, 4.35, 1.15], { bodySize: 7.55, headerSize: 8.2, centerCols: [0, 4] });
  addNote(slide, "※ 상기 자료는 방법론 개발 및 PDD 작성의 핵심 근거 자료로 활용됩니다. 자료 제출 지연 시 전체 일정에 영향을 줄 수 있으므로 조속한 협조를 요청드립니다.", 0.75, 6.05, 9.35, 0.48);
  footer(slide, 11);
}

function slide12() {
  const slide = pptx.addSlide();
  addHeader(slide, "III. 협조 요청 및 향후 계획 | 향후 추진 일정 (계약서 기준)", "향후 추진 일정");
  slide.addText("▪ 기준일: 업무위임계약서 체결일(2025.12.15) 기준으로 1단계 완료 후 방법론 개발·검증·등록 절차를 연계 추진", {
    x: 0.55, y: 1.34, w: 9.85, h: 0.22, fontFace: FONT, fontSize: 10.8, color: "000000", margin: 0
  });

  const phases = [
    {
      title: "1단계: 사전 타당성 검토",
      period: "2025.12.15 ~ 2026.04.30",
      output: "1단계 결과 보고서 (본 자료)",
      bullets: ["법적·제도적 추가성 검토", "베이스라인 시나리오 설정", "예상 감축량 산정 및 방법론 방향 확정"],
      barX: 2.0,
      barW: 2.55,
      active: true
    },
    {
      title: "2단계: 방법론 개발 및 사업계획 등록",
      period: "1단계 완료 후 ~ 2026.06.30",
      output: "KCS 방법론 / PDD / 등록 완료 확인서",
      bullets: ["KCS 신규 방법론 문서 작성", "PDD 작성 및 제3자 검증 대응", "KCS 적합성 검토·심의 대응"],
      barX: 4.58,
      barW: 1.72
    },
    {
      title: "3단계: 모니터링 및 1차 인증 대응",
      period: "2단계 완료 후 지정 유효기간 내",
      output: "모니터링 보고서 / 인증 완료 확인서",
      bullets: ["모니터링 보고서(MR) 작성", "제3자 검증(Verification) 대응", "1차 감축량 인증 신청 및 완료"],
      barX: 6.35,
      barW: 2.7
    }
  ];

  slide.addShape("rect", { x: 0.55, y: 1.82, w: 9.75, h: 0.38, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("단계", { x: 0.75, y: 1.95, w: 1.15, h: 0.1, fontFace: FONT, fontSize: 8.6, bold: true, color: C.white, align: "center", margin: 0 });
  slide.addText("주요 활동", { x: 2.45, y: 1.95, w: 2.4, h: 0.1, fontFace: FONT, fontSize: 8.6, bold: true, color: C.white, align: "center", margin: 0 });
  slide.addText("기간", { x: 6.95, y: 1.95, w: 1.25, h: 0.1, fontFace: FONT, fontSize: 8.6, bold: true, color: C.white, align: "center", margin: 0 });
  slide.addText("주요 산출물", { x: 8.5, y: 1.95, w: 1.25, h: 0.1, fontFace: FONT, fontSize: 8.6, bold: true, color: C.white, align: "center", margin: 0 });

  phases.forEach((p, idx) => {
    const y = 2.2 + idx * 1.05;
    const fill = p.active ? C.lightBlue : C.lightGray;
    slide.addShape("rect", { x: 0.55, y, w: 9.75, h: 1.05, fill: { color: idx % 2 === 0 ? C.white : "F1F6FB" }, line: { color: C.line, width: 0.6 } });
    slide.addShape("rect", { x: 0.55, y, w: 1.65, h: 1.05, fill: { color: p.active ? C.navy : C.white }, line: { color: C.line, width: 0.6 } });
    slide.addText(`${idx + 1}단계`, { x: 0.72, y: y + 0.22, w: 1.28, h: 0.16, fontFace: FONT, fontSize: 10.5, bold: true, color: p.active ? C.white : C.navy, align: "center", margin: 0 });
    slide.addText(p.title.replace(`${idx + 1}단계: `, ""), { x: 0.68, y: y + 0.55, w: 1.36, h: 0.15, fontFace: FONT, fontSize: 7.6, bold: true, color: p.active ? C.white : C.navy, align: "center", margin: 0, breakLine: false });
    slide.addText(p.bullets.map((b) => `• ${b}`).join("\n"), { x: 2.35, y: y + 0.17, w: 4.1, h: 0.62, fontFace: FONT, fontSize: 9.0, color: C.ink, breakLine: false, margin: 0 });
    const periodText = p.period.replace(" ~ ", "\n~ ");
    slide.addText(periodText, { x: 6.72, y: y + 0.24, w: 1.55, h: 0.34, fontFace: FONT, fontSize: 7.7, bold: true, color: C.navy, align: "center", valign: "middle", margin: 0, breakLine: false });
    slide.addText(p.output, { x: 8.42, y: y + 0.27, w: 1.54, h: 0.3, fontFace: FONT, fontSize: 7.7, bold: idx === 0, color: C.ink, align: "center", margin: 0, breakLine: false });
  });

  slide.addShape("roundRect", { x: 0.55, y: 5.62, w: 9.75, h: 0.62, rectRadius: 0.03, fill: { color: C.pale }, line: { color: C.sky, width: 1 } });
  slide.addText("현재 위치", { x: 0.83, y: 5.85, w: 0.8, h: 0.1, fontFace: FONT, fontSize: 8.3, bold: true, color: C.navy, margin: 0 });
  slide.addShape("line", { x: 1.8, y: 5.94, w: 7.25, h: 0, line: { color: C.line, width: 5 } });
  phases.forEach((p) => {
    slide.addShape("line", { x: p.barX - 0.2, y: 5.94, w: p.barW, h: 0, line: { color: p.active ? C.sky : C.navy, width: 5, transparency: p.active ? 0 : 35 } });
  });
  slide.addText("▶ 1단계 진행 중 (2025.12.15 ~ 2026.04.30)", { x: 1.86, y: 6.06, w: 3.0, h: 0.12, fontFace: FONT, fontSize: 7.8, bold: true, color: C.navy, margin: 0 });
  slide.addText("2025.12", { x: 1.65, y: 5.72, w: 0.65, h: 0.1, fontFace: FONT, fontSize: 6.4, color: C.muted, margin: 0 });
  slide.addText("2026.04", { x: 4.05, y: 5.72, w: 0.65, h: 0.1, fontFace: FONT, fontSize: 6.4, color: C.muted, margin: 0 });
  slide.addText("2026.06", { x: 5.75, y: 5.72, w: 0.65, h: 0.1, fontFace: FONT, fontSize: 6.4, color: C.muted, margin: 0 });
  slide.addText("추후 협의", { x: 8.42, y: 5.72, w: 0.72, h: 0.1, fontFace: FONT, fontSize: 6.4, color: C.muted, margin: 0 });
  footer(slide, 12);
}

cover();
processSlide();
contents();
slide4();
slide5();
slide6();
slide7();
slide8();
slide9();
slide10();
slide11();
slide12();

await mkdir(OUT_DIR, { recursive: true });
const buffer = await pptx.write({ outputType: "nodebuffer" });
await writeFile(OUT, buffer);
console.log(JSON.stringify({ output: OUT, slides: pptx._slides.length }, null, 2));
