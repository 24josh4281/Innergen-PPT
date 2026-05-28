import { existsSync } from "node:fs";
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { basename, dirname, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import JSZip from "jszip";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");
const workspaceRoot = resolve(repoRoot, "..");
const inputReferenceRoots = [
  join(workspaceRoot, "INPUTS", "PPT 장표 레퍼런스"),
  join(workspaceRoot, "INPUTS", "PPT 장표 참고(구조화)")
];
const defaultOutputPath = join(repoRoot, "docs", "reference-source-index.json");

const outputPath = argValue("--output", defaultOutputPath);
const dryRun = process.argv.includes("--dry-run");
const approvedReviewStatus = "approved-sample";

const conversationSources = [
  source("hyundai_transys_sbti_cdp_climate_risk_proposal", String.raw`C:\Users\24jos\Downloads\(제안서) 현대트랜시스 SBTi 검증, CDP 평가 및 기후리스크 평가 통합 자문 컨설팅 제안서_v1.0.pptx`, {
    businessType: "disclosure",
    meetingType: "proposal",
    sourceRole: "proposal-reference",
    consultingFirm: "INNerGEN",
    topic: "SBTi/CDP/기후리스크 통합 자문"
  }),
  source("innergen_design_template", String.raw`C:\Users\24jos\Downloads\템플릿.pptx`, {
    businessType: "design-template",
    meetingType: "design-template",
    sourceRole: "design-template",
    consultingFirm: "INNerGEN",
    topic: "INNerGEN BI 및 템플릿"
  }),
  source("newrizen_filter_methodology_260203", String.raw`C:\Users\24jos\OneDrive\문서\바탕 화면\(회의) 뉴라이즌 필터기술에 의한 온실가스 감축 방법론 개발_260203.pptx`, {
    businessType: "reduction",
    meetingType: "review",
    sourceRole: "primary-reference",
    consultingFirm: "INNerGEN",
    topic: "감축방법론 개발 회의"
  }),
  source("newrizen_filter_methodology_260406", String.raw`C:\Users\24jos\OneDrive\문서\바탕 화면\(회의) 뉴라이즌 필터기술에 의한 온실가스 감축 방법론 개발_260406_v2.pptx`, {
    businessType: "reduction",
    meetingType: "review",
    sourceRole: "primary-reference",
    consultingFirm: "INNerGEN",
    topic: "감축방법론 개발 회의"
  }),
  source("samsung_ds_reduction_methodology_240909", String.raw`C:\Users\24jos\OneDrive\문서\바탕 화면\착수보고자료_삼성전자 DS부문 감축방법론 개발 용역(이너젠)_240909_v1.2.pptx`, {
    businessType: "reduction",
    meetingType: "kickoff",
    sourceRole: "primary-reference",
    consultingFirm: "INNerGEN",
    topic: "반도체 감축방법론 착수보고"
  }),
  source("innergen_semiconductor_scope3_methodology_240724", String.raw`C:\Users\24jos\OneDrive\문서\바탕 화면\이너젠_제안서_반도체 Scope3 자발적 감축 방법론 개발_240724.pptx`, {
    businessType: "reduction",
    meetingType: "proposal",
    sourceRole: "proposal-reference",
    consultingFirm: "INNerGEN",
    topic: "반도체 Scope3 자발적 감축 방법론"
  }),
  source("deloitte_daewoo_sustainability_cdp_proposal", String.raw`B:\25년\25년\25년 5월~ 11월 다운로드\[Deloitte] 2026년 대우건설 지속가능경영보고서 제작 및 CDP 대응 용역_제안서_최종_F__25년 실적 추가.pdf`, {
    businessType: "disclosure",
    meetingType: "proposal",
    sourceRole: "proposal-reference",
    consultingFirm: "Deloitte",
    topic: "지속가능경영보고서/CDP 대응 제안"
  }),
  source("ecovadis_esg_proposal", String.raw`B:\25년\25년\25년 5월~ 11월 다운로드\(제안서) EcoVadis 평가 대응 및 ESG 체계 구축 컨설팅_20250902_v2.0.pptx`, {
    businessType: "disclosure",
    meetingType: "proposal",
    sourceRole: "proposal-reference",
    consultingFirm: "INNerGEN",
    topic: "EcoVadis 평가 대응 및 ESG 체계 구축"
  }),
  source("kakao_cdp_scope3_proposal", String.raw`B:\25년\25년\카카오 받은 파일 25년\카카오_2025년 CDP 및 온실가스 Scope 3 대응 제안서_250107_v1.0_세진씨 이력.pptx`, {
    businessType: "disclosure",
    meetingType: "proposal",
    sourceRole: "proposal-reference",
    consultingFirm: "INNerGEN",
    topic: "CDP 및 Scope 3 대응"
  }),
  source("mbi_selangor_tender_briefing_carbon", String.raw`C:\Users\24jos\OneDrive\문서\카카오톡 받은 파일\MBI Selangor TENDER BRIEFING_SUSTAINABILITY CARBON_260417_194241.pdf`, {
    businessType: "reduction",
    meetingType: "proposal",
    sourceRole: "tender-source",
    consultingFirm: "Client source",
    topic: "Sustainability carbon tender briefing"
  }),
  source("starstech_methodology_260410", String.raw`C:\Users\24jos\Downloads\(회의) 스타스테크 폐산 재활용 기술에 대한 온실가스 감축 방법론 개발_260410_ver1.3.pptx`, {
    businessType: "reduction",
    meetingType: "kickoff",
    sourceRole: "primary-reference",
    consultingFirm: "INNerGEN",
    topic: "폐산 재활용 감축방법론 개발"
  }),
  source("starstech_phase1_pdf_user_sample", String.raw`C:\Users\24jos\OneDrive\문서\바탕 화면\착수보고_’26년 온실가스 배출량 산정계획서 및 명세서 컨설팅_ver1.pdf`, {
    businessType: "regulatory",
    meetingType: "kickoff",
    sourceRole: "user-sample",
    consultingFirm: "INNerGEN",
    topic: "온실가스 배출량 산정계획서 및 명세서 컨설팅"
  }),
  source("sk_siltron_ghg_inventory_kickoff", String.raw`B:\이너젠 Dropbox\김세진\2026\2026_02_SK실트론 온실가스 배출권거래제 대응\01 착수회의\착수보고_’26년 온실가스 배출량 산정계획서 및 명세서 컨설팅.pptx`, {
    businessType: "regulatory",
    meetingType: "kickoff",
    sourceRole: "primary-reference",
    consultingFirm: "INNerGEN",
    topic: "온실가스 배출권거래제 대응 착수보고"
  })
];

const inputFiles = (await Promise.all(inputReferenceRoots.map((root) => collectFiles(root, [".pdf", ".pptx"])))).flat();
const inputSources = inputFiles.map((filePath) => ({ path: filePath }));
const allSources = dedupeSources([...inputSources, ...conversationSources]);

const files = [];
let extractedSlideCount = 0;
for (const item of allSources) {
  const classified = classifySource(item.path, item);
  const fileRecord = {
    id: classified.id,
    path: classified.path,
    exists: existsSync(classified.path),
    extension: extname(classified.path).toLowerCase(),
    businessType: classified.businessType,
    meetingType: classified.meetingType,
    sourceRole: classified.sourceRole,
    consultingFirm: classified.consultingFirm,
    topic: classified.topic,
    recommendedUse: classified.recommendedUse,
    categoryPath: classified.categoryPath,
    sourceRootType: classified.sourceRootType,
    learningPolicy: classified.learningPolicy,
    status: "missing",
    slides: []
  };

  if (fileRecord.exists) {
    try {
      const slides = await extractSlides(classified.path);
      fileRecord.slides = slides.map((slide) => {
        const inference = inferArchetype(`${slide.title}\n${slide.text}`);
        return {
          slideNo: slide.slideNo,
          title: slide.title,
          inferredArchetype: inference.id,
          confidence: inference.confidence,
          tags: unique([classified.businessType, classified.meetingType, classified.sourceRole, ...inference.tags]),
          reviewStatus: approvedReviewStatus
        };
      });
      fileRecord.status = approvedReviewStatus;
      extractedSlideCount += fileRecord.slides.length;
    } catch (error) {
      fileRecord.status = "extraction-failed";
      fileRecord.extractionError = error instanceof Error ? error.message : String(error);
    }
  }
  files.push(fileRecord);
}

const index = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  dryRun,
  policy: {
    copiesSourceFiles: false,
    storesFullSlideText: false,
    excludesNonInnergenLogos: true,
    allowedBrandIdentity: "INNerGEN only",
    learnsFromReferences: ["slide structure", "layout pattern", "logic flow", "storyline", "proof-object placement", "information hierarchy"],
    doesNotLearnFromReferences: ["external company logos", "external brand marks", "client-specific identity systems"],
    reviewFlow: "all accessible INPUT references are approved samples for structure learning",
    approvedByUser: true,
    approvedReviewStatus
  },
  sourceRoots: {
    inputReferenceRoots,
    workspaceRoot
  },
  summary: {
    files: files.length,
    existingFiles: files.filter((file) => file.exists).length,
    missingFiles: files.filter((file) => !file.exists).length,
    extractedSlides: extractedSlideCount,
    extractionFailed: files.filter((file) => file.status === "extraction-failed").length
  },
  files
};

if (dryRun) {
  console.log(JSON.stringify(index.summary, null, 2));
} else {
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, JSON.stringify(index, null, 2), "utf8");
  console.log(`Wrote ${outputPath}`);
  console.log(JSON.stringify(index.summary, null, 2));
}

function argValue(flag, fallback) {
  const index = process.argv.indexOf(flag);
  if (index === -1 || index + 1 >= process.argv.length) return fallback;
  return process.argv[index + 1];
}

function source(id, path, overrides) {
  return { id, path, ...overrides };
}

async function collectFiles(dirPath, extensions) {
  if (!existsSync(dirPath)) return [];
  const result = [];
  const entries = await readdir(dirPath, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dirPath, entry.name);
    if (entry.isDirectory()) {
      result.push(...await collectFiles(fullPath, extensions));
    } else if (extensions.includes(extname(entry.name).toLowerCase())) {
      result.push(fullPath);
    }
  }
  return result;
}

function dedupeSources(sources) {
  const map = new Map();
  for (const item of sources) {
    const normalized = normalizePath(item.path);
    map.set(normalized, { ...(map.get(normalized) ?? {}), ...item, path: normalized });
  }
  return [...map.values()].sort((a, b) => a.path.localeCompare(b.path, "ko"));
}

function normalizePath(filePath) {
  return resolve(filePath);
}

function classifySource(filePath, overrides = {}) {
  const fileName = basename(filePath);
  const lower = `${filePath} ${fileName}`.toLowerCase();
  const curated = detectCuratedReferencePath(filePath);
  const detected = detectByName(lower, fileName);
  return {
    id: overrides.id ?? curated.id ?? detected.id ?? stableId(fileName),
    path: normalizePath(filePath),
    businessType: overrides.businessType ?? curated.businessType ?? detected.businessType,
    meetingType: overrides.meetingType ?? curated.meetingType ?? detected.meetingType,
    sourceRole: overrides.sourceRole ?? curated.sourceRole ?? detected.sourceRole,
    consultingFirm: overrides.consultingFirm ?? detected.consultingFirm,
    topic: overrides.topic ?? curated.topic ?? detected.topic,
    recommendedUse: overrides.recommendedUse ?? curated.recommendedUse ?? detected.recommendedUse,
    categoryPath: curated.categoryPath ?? "",
    sourceRootType: overrides.sourceRootType ?? curated.sourceRootType ?? detectSourceRootType(filePath),
    learningPolicy: curated.learningPolicy ?? referenceLearningPolicy()
  };
}

function detectCuratedReferencePath(filePath) {
  const normalized = normalizePath(filePath);
  const marker = `${workspaceRoot}${/\\/.test(normalized) ? "\\" : "/"}INPUTS`;
  const afterInputs = normalized.includes(marker) ? normalized.slice(marker.length + 1) : normalized;
  const parts = afterInputs.split(/[\\/]+/);
  if (parts[0] !== "PPT 장표 레퍼런스") return {};

  const businessFolder = parts[1] ?? "";
  const fileName = basename(filePath);
  const fileStem = fileName.replace(/\.[^.]+$/, "");
  const extension = extname(filePath).toLowerCase().replace(".", "");
  const business = mapBusinessFolder(businessFolder);
  const report = mapReportType(fileStem);
  const variant = variantSuffix(fileStem);
  const extensionSuffix = extension === "pdf" ? "_pdf" : "";
  return {
    id: `${business.slug}_${report.slug}${variant}${extensionSuffix}`,
    businessType: business.businessType,
    meetingType: report.meetingType,
    sourceRole: report.sourceRole,
    topic: `${business.label} ${report.label}`,
    recommendedUse: `${business.label} ${report.label} 레퍼런스의 구조, 슬라이드 형식, 논리 흐름, 정보 위계를 학습`,
    categoryPath: `${businessFolder}/${fileStem}`,
    sourceRootType: "business-report-reference",
    learningPolicy: referenceLearningPolicy()
  };
}

function detectSourceRootType(filePath) {
  const normalized = normalizePath(filePath);
  const afterInputs = normalized.split(/[\\/]+INPUTS[\\/]+/)[1] ?? "";
  if (afterInputs.startsWith("PPT 장표 레퍼런스")) return "business-report-reference";
  if (afterInputs.startsWith("PPT 장표 참고(구조화)")) return "structure-benchmark";
  return "conversation-source";
}

function mapBusinessFolder(folderName) {
  if (folderName === "CDP") return { slug: "cdp", label: "CDP·기후공시", businessType: "disclosure" };
  if (folderName === "감축사업") return { slug: "reduction", label: "감축사업", businessType: "reduction" };
  if (folderName === "규제대응사업") return { slug: "regulatory", label: "규제대응사업", businessType: "regulatory" };
  if (folderName === "온실가스 인벤토리") return { slug: "ghg_inventory", label: "온실가스 인벤토리", businessType: "regulatory" };
  return { slug: slugify(folderName) || "reference", label: folderName || "레퍼런스", businessType: "benchmark" };
}

function mapReportType(fileStem) {
  const text = fileStem.toLowerCase();
  if (/제안서|proposal/.test(text)) return { slug: "proposal", label: "제안서", meetingType: "proposal", sourceRole: "proposal-reference" };
  if (/착수보고|kick/.test(text)) return { slug: "kickoff", label: "착수보고", meetingType: "kickoff", sourceRole: "primary-reference" };
  if (/중간보고|interim|w2|monthly|biweekly/.test(text)) return { slug: "interim", label: "중간보고", meetingType: "interim", sourceRole: "primary-reference" };
  if (/최종보고|final/.test(text)) return { slug: "final", label: "최종보고", meetingType: "final", sourceRole: "primary-reference" };
  if (/방법론/.test(text)) return { slug: "methodology_report", label: "방법론 개발 보고", meetingType: "review", sourceRole: "primary-reference" };
  return { slug: slugify(fileStem) || "reference", label: fileStem, meetingType: "review", sourceRole: "primary-reference" };
}

function variantSuffix(fileStem) {
  const match = fileStem.match(/(?:\s|_)(\d+|v\d+)$/i);
  return match ? `_${match[1].toLowerCase()}` : "";
}

function referenceLearningPolicy() {
  return {
    learn: ["structure", "slideFormat", "logicFlow", "storyline", "layoutPattern", "proofObjectPlacement", "informationHierarchy"],
    exclude: ["externalCompanyLogo", "externalBrandMark", "externalCorporateIdentity", "clientLogo"],
    keep: ["innergenLogo", "innergenBI", "innergenFontPolicy", "innergenColorPolicy"]
  };
}

function detectByName(lower, fileName) {
  const firm = detectFirm(lower);
  const base = {
    businessType: "benchmark",
    meetingType: "benchmark",
    sourceRole: "thought-leadership",
    consultingFirm: firm,
    topic: inferTopic(lower, fileName),
    recommendedUse: "구조화 방식과 proof-object 배치 학습용"
  };

  const rules = [
    [/starstech|스타스테크/, { id: "starstech_methodology_260410", businessType: "reduction", meetingType: "kickoff", sourceRole: "primary-reference", recommendedUse: "감축사업 착수/방법론 보고 구조" }],
    [/newrizen|뉴라이즌/, { id: lower.includes("260406") ? "newrizen_filter_methodology_260406" : "newrizen_filter_methodology_260203", businessType: "reduction", meetingType: "review", sourceRole: "primary-reference", recommendedUse: "감축방법론 검토회의 구조" }],
    [/삼성전자|samsung/, { id: "samsung_ds_reduction_methodology_240909", businessType: "reduction", meetingType: "kickoff", sourceRole: "primary-reference", recommendedUse: "감축방법론 착수보고 구조" }],
    [/반도체 scope3|scope3 자발적 감축/, { id: "innergen_semiconductor_scope3_methodology_240724", businessType: "reduction", meetingType: "proposal", sourceRole: "proposal-reference", recommendedUse: "감축사업 제안서 구조" }],
    [/jb금융|re100.*vf|\[kick-off\]/, { id: lower.includes("[w2]") ? "jb_re100_w2" : "jb_re100_kickoff", businessType: "reduction", meetingType: lower.includes("[w2]") ? "review" : "kickoff", sourceRole: "primary-reference", recommendedUse: "RE100 컨설팅 회의자료 구조" }],
    [/재생에너지/, { id: "renewable_energy_new_business", businessType: "reduction", meetingType: "benchmark", sourceRole: "benchmark", recommendedUse: "에너지/감축사업 구조 벤치마크" }],
    [/sk실트론|산정계획서|명세서/, { id: "sk_siltron_ghg_inventory_kickoff", businessType: "regulatory", meetingType: "kickoff", sourceRole: "primary-reference", recommendedUse: "규제대응 착수보고 구조" }],
    [/hyundai|현대트랜시스|sbti/, { id: "hyundai_transys_sbti_cdp_climate_risk_proposal", businessType: "disclosure", meetingType: "proposal", sourceRole: "proposal-reference", recommendedUse: "기후공시/평가 통합 제안서 구조" }],
    [/daewoo|대우건설/, { id: "deloitte_daewoo_sustainability_cdp_proposal", businessType: "disclosure", meetingType: "proposal", sourceRole: "proposal-reference", recommendedUse: "지속가능경영보고서/CDP 제안서 구조" }],
    [/ecovadis/, { id: "ecovadis_esg_proposal", businessType: "disclosure", meetingType: "proposal", sourceRole: "proposal-reference", recommendedUse: "ESG 평가 대응 제안서 구조" }],
    [/카카오|kakao/, { id: "kakao_cdp_scope3_proposal", businessType: "disclosure", meetingType: "proposal", sourceRole: "proposal-reference", recommendedUse: "CDP/Scope 3 대응 제안서 구조" }],
    [/sk chemical|tcfd response/, { id: "ey_sk_chemical_tcfd", businessType: "disclosure", meetingType: "final", sourceRole: "benchmark", recommendedUse: "TCFD 대응 보고 구조" }],
    [/tnfd/, { id: "pwc_tnfd_standard_strategy", businessType: "disclosure", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "TNFD 표준/전략 구조" }],
    [/csrd.*benchmark|insurance-csrd/, { id: "deloitte_insurance_csrd_benchmark_2024", businessType: "disclosure", meetingType: "benchmark", sourceRole: "benchmark", recommendedUse: "CSRD 벤치마크 구조" }],
    [/csrd/, { id: "pwc_csrd_disclosure_response", businessType: "disclosure", meetingType: "training", sourceRole: "thought-leadership", recommendedUse: "CSRD 대응 세미나 구조" }],
    [/sk가스.*tcfd/, { id: "sk_gas_tcfd_draft_220818", businessType: "disclosure", meetingType: "final", sourceRole: "benchmark", recommendedUse: "TCFD 보고서 구조" }],
    [/sktelecom|annualreport/, { id: "sk_telecom_annual_report_2021", businessType: "disclosure", meetingType: "final", sourceRole: "benchmark", recommendedUse: "Annual report 정보 구조" }],
    [/220603_sk_tcfd교육_프로젝트|프로젝트 공유/, { id: "sk_tcfd_project_share_220603", businessType: "disclosure", meetingType: "training", sourceRole: "training", recommendedUse: "교육/프로젝트 공유 구조" }],
    [/220603_sk그룹 tcfd|1차 교육자료/, { id: "sk_tcfd_training_220603", businessType: "disclosure", meetingType: "training", sourceRole: "training", recommendedUse: "TCFD 교육 구조" }],
    [/220729.*monthly/, { id: "sk_tcfd_monthly_220729", businessType: "disclosure", meetingType: "interim", sourceRole: "benchmark", recommendedUse: "월간 진행보고 구조" }],
    [/220811/, { id: "sk_tcfd_response_diagnosis_220811", businessType: "disclosure", meetingType: "review", sourceRole: "benchmark", recommendedUse: "대응체계 진단 구조" }],
    [/220817.*biweekly/, { id: "sk_tcfd_biweekly_220817", businessType: "disclosure", meetingType: "interim", sourceRole: "benchmark", recommendedUse: "Biweekly 보고 구조" }],
    [/mckinsey|맥킨지|metaverse/, { id: "mckinsey_metaverse_value_creation", businessType: "benchmark", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "컨설팅 보고서 구조 벤치마크" }],
    [/kpmg-kr-bf|디지털금융/, { id: "kpmg_digital_finance_2025", businessType: "benchmark", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "산업 이슈 구조 벤치마크" }],
    [/호텔산업/, { id: "kpmg_hotel_business_trend_20250720", businessType: "benchmark", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "산업 트렌드 구조 벤치마크" }],
    [/kpmg\.pdf|kpmg$/, { id: "kpmg_esg_reference", businessType: "benchmark", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "컨설팅 장표 구조 벤치마크" }],
    [/ey-ces/, { id: "ey_ces_2025_preview", businessType: "benchmark", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "전망/트렌드 보고 구조" }],
    [/ey한영/, { id: "ey_hanyoung_reference", businessType: "disclosure", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "EY 기후/ESG 구조 벤치마크" }],
    [/딜로이트|deloitte\.pdf/, { id: "deloitte_esg_reference", businessType: "disclosure", meetingType: "benchmark", sourceRole: "thought-leadership", recommendedUse: "Deloitte ESG 구조 벤치마크" }],
    [/01\._최종보고서/, { id: "research_final_report_public", businessType: "reduction", meetingType: "final", sourceRole: "benchmark", recommendedUse: "최종보고서 구조" }],
    [/02\._연구결과/, { id: "research_evaluation_report", businessType: "reduction", meetingType: "final", sourceRole: "benchmark", recommendedUse: "연구결과 평가 구조" }],
    [/한국환경산업기술원|지원사업/, { id: "keiti_esg_disclosure_support", businessType: "disclosure", meetingType: "proposal", sourceRole: "benchmark", recommendedUse: "지원사업/공시 대응 구조" }],
    [/템플릿/, { id: "innergen_design_template", businessType: "design-template", meetingType: "design-template", sourceRole: "design-template", recommendedUse: "BI, 폰트, 색상, 마스터 스타일 확인" }]
  ];

  const match = rules.find(([regex]) => regex.test(lower));
  return { ...base, ...(match?.[1] ?? {}) };
}

function detectFirm(lower) {
  if (/deloitte|딜로이트/.test(lower)) return "Deloitte";
  if (/pwc|삼일pwc/.test(lower)) return "PwC";
  if (/ey|ey한영/.test(lower)) return "EY";
  if (/kpmg|삼정kpmg/.test(lower)) return "KPMG";
  if (/mckinsey|맥킨지/.test(lower)) return "McKinsey";
  if (/에코네트워크/.test(lower)) return "EcoNetwork";
  if (/이너젠|innergen/.test(lower)) return "INNerGEN";
  if (/sk|삼성|카카오|현대|jb금융|스타스테크/.test(lower)) return "Client/Industry";
  return "Unknown";
}

function inferTopic(lower, fileName) {
  if (/tcfd/.test(lower)) return "TCFD/기후공시";
  if (/tnfd/.test(lower)) return "TNFD/자연공시";
  if (/csrd/.test(lower)) return "CSRD 공시";
  if (/cdp/.test(lower)) return "CDP 대응";
  if (/re100/.test(lower)) return "RE100";
  if (/감축|방법론|reduction|carbon/.test(lower)) return "온실가스 감축사업";
  if (/명세서|배출권|산정계획/.test(lower)) return "온실가스 규제대응";
  if (/esg/.test(lower)) return "ESG 공시/평가";
  return fileName.replace(/\.[^.]+$/, "");
}

async function extractSlides(filePath) {
  const extension = extname(filePath).toLowerCase();
  if (extension === ".pptx") return extractPptxSlides(filePath);
  if (extension === ".pdf") return extractPdfPages(filePath);
  return [];
}

async function extractPptxSlides(filePath) {
  const zip = await JSZip.loadAsync(await readFile(filePath));
  const slideNames = Object.keys(zip.files)
    .filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name))
    .sort((a, b) => slideNumber(a) - slideNumber(b));

  const slides = [];
  for (const name of slideNames) {
    const xml = await zip.files[name].async("string");
    const textRuns = [...xml.matchAll(/<a:t[^>]*>([\s\S]*?)<\/a:t>/g)]
      .map((match) => cleanText(decodeXml(match[1])))
      .filter(Boolean);
    const text = textRuns.join("\n");
    slides.push({
      slideNo: slideNumber(name),
      title: extractTitle(text, slideNumber(name)),
      text
    });
  }
  return slides;
}

async function extractPdfPages(filePath) {
  const bytes = await readFile(filePath);
  const doc = await pdfjsLib.getDocument({ data: new Uint8Array(bytes), disableWorker: true }).promise;
  const pages = [];
  for (let pageNo = 1; pageNo <= doc.numPages; pageNo++) {
    const page = await doc.getPage(pageNo);
    const content = await page.getTextContent();
    const text = content.items.map((item) => cleanText(item.str ?? "")).filter(Boolean).join("\n");
    pages.push({
      slideNo: pageNo,
      title: extractTitle(text, pageNo),
      text
    });
  }
  return pages;
}

function extractTitle(text, slideNo) {
  const lines = cleanText(text)
    .split(/\n+/)
    .map((line) => cleanText(line))
    .filter((line) => line.length >= 2 && !/^\d+$/.test(line))
    .filter((line) => !/^copyright|^all rights reserved/i.test(line));
  const title = lines.find((line) => line.length <= 90) ?? lines[0] ?? `Slide ${slideNo}`;
  return title.slice(0, 120);
}

function inferArchetype(text) {
  const lower = text.toLowerCase();
  const rules = [
    ["contents-isometric", 0.88, ["contents", "agenda", "목차", "순서"]],
    ["cover-kickoff", 0.75, ["보고", "제안", "회의 자료", "title"]],
    ["integrated-process-map", 0.86, ["프로세스", "process", "방법론", "단계", "추진 절차"]],
    ["schedule-gantt", 0.86, ["일정", "schedule", "gantt", "기간", "월", "마일스톤"]],
    ["data-request-tracker", 0.84, ["요청자료", "요청 자료", "data request", "제출 기한", "담당"]],
    ["inventory-boundary-flow", 0.86, ["baseline", "boundary", "베이스라인", "경계", "사업 전", "사업 후"]],
    ["reduction-roadmap-analysis", 0.86, ["감축량", "산정식", "er", "be", "pe", "le", "배출량"]],
    ["comparison-matrix", 0.82, ["비교", "대안", "matrix", "판정", "채택", "기각"]],
    ["work-scope-table", 0.82, ["scope", "범위", "과업", "산출물", "검토 결과", "평가항목"]],
    ["tcfd-pillar-diagnosis", 0.84, ["tcfd", "governance", "strategy", "risk management", "metrics"]],
    ["cdp-response-strategy", 0.82, ["cdp", "ors", "score", "scoring", "문항"]],
    ["score-improvement-levers", 0.8, ["점수", "등급", "감점", "개선 레버", "ecovadis"]],
    ["regulatory-timeline-radar", 0.8, ["규제", "시행", "법령", "공시 기준", "제도"]],
    ["double-materiality-or-risk-map", 0.8, ["risk", "materiality", "위험", "중요성", "기회"]],
    ["consulting-executive-summary", 0.78, ["요약", "summary", "executive", "종합", "결론"]],
    ["impact-factoid-big-number", 0.76, ["tco2", "%", "톤", "억원", "kpi", "핵심 숫자"]],
    ["evidence-grid", 0.72, ["증빙", "evidence", "근거", "스크린샷", "출처"]],
    ["consulting-one-page-memo", 0.68, ["검토", "판단", "쟁점", "리스크", "의견"]]
  ];

  for (const [id, confidence, keywords] of rules) {
    const matched = keywords.filter((keyword) => lower.includes(keyword.toLowerCase()));
    if (matched.length) return { id, confidence, tags: matched.slice(0, 5) };
  }
  return { id: "why-what-how-logic", confidence: 0.55, tags: ["auto-default"] };
}

function slideNumber(name) {
  return Number(name.match(/slide(\d+)\.xml/)?.[1] ?? 0);
}

function decodeXml(value) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, "\"")
    .replace(/&apos;/g, "'");
}

function cleanText(value) {
  return String(value ?? "")
    .replace(/\u0000/g, "")
    .replace(/[ \t]+/g, " ")
    .replace(/\r/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function stableId(fileName) {
  const ascii = slugify(fileName.replace(/\.[^.]+$/, "")).slice(0, 48);
  const hash = [...fileName].reduce((acc, char) => ((acc << 5) - acc + char.charCodeAt(0)) >>> 0, 0).toString(16);
  return ascii ? `${ascii}_${hash}` : `reference_${hash}`;
}

function slugify(value) {
  const known = [
    [/cdp/i, "cdp"],
    [/감축사업/, "reduction"],
    [/규제대응사업/, "regulatory"],
    [/온실가스\s*인벤토리/, "ghg_inventory"],
    [/제안서|proposal/i, "proposal"],
    [/착수보고|kickoff|kick/i, "kickoff"],
    [/중간보고|interim/i, "interim"],
    [/최종보고|final/i, "final"],
    [/방법론\s*개발\s*보고/, "methodology_report"],
    [/방법론/, "methodology"],
    [/보고/, "report"]
  ];
  let result = String(value ?? "").toLowerCase();
  for (const [regex, replacement] of known) result = result.replace(regex, replacement);
  return result
    .replace(/v(\d+)/gi, "v$1")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}
