import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const root = resolve(scriptDir, "..");
const outDir = resolve(process.argv[2] ?? join(root, "docs", "generated", "standard-flow-samples"));
const tmpDir = join(root, ".tmp-standard-flow-samples");

async function main() {
  await rm(tmpDir, { recursive: true, force: true });
  await mkdir(outDir, { recursive: true });
  await mkdir(tmpDir, { recursive: true });

  try {
    runTsc();
    await patchCompiledImports(tmpDir);

    const { getRule } = await import(pathToFileURL(join(tmpDir, "patterns.js")).href);
    const { buildPptxWithIterativeQa } = await import(pathToFileURL(join(tmpDir, "iterativePptxQa.js")).href);
    const flowData = JSON.parse(await readFile(join(root, "docs", "standard-deck-flows.json"), "utf8"));
    const targetIds = ["reduction-kickoff-standard-flow", "disclosure-proposal-standard-flow", "ghg-inventory-final-standard-flow"];
    const outputs = [];

    for (const flowId of targetIds) {
      const flow = flowData.profiles.find((profile) => profile.id === flowId);
      const meta = flowInputs[flowId];
      const bodySequence = flow.standardSequence.filter((id) => id !== "cover-kickoff" && id !== "contents-isometric");
      const bodyRoles = flow.stageRoles.slice(2);
      const slides = bodySequence.map((archetypeId, idx) =>
        makeSlide(getRule, idx + 1, archetypeId, flow, meta, bodyRoles[idx] ?? flow.stageRoles[idx] ?? meta.topic)
      );

      const result = await buildPptxWithIterativeQa(meta, slides, 3);
      const bytes = Buffer.from(await result.blob.arrayBuffer());
      const fileStem = flow.id.replace("-standard-flow", "");
      const pptxPath = join(outDir, `${fileStem}.pptx`);
      const qaPath = join(outDir, `${fileStem}.qa.json`);

      await writeFile(pptxPath, bytes);
      await writeFile(qaPath, JSON.stringify({
        flowId,
        label: flow.label,
        meta,
        standardSequence: flow.standardSequence,
        generatedBodySequence: bodySequence,
        slides: result.slides.map((slide) => ({
          index: slide.index,
          archetype: slide.archetype.id,
          claimTitle: slide.claimTitle,
          governingMessage: slide.governingMessage
        })),
        qa: result.qa,
        attempts: result.attempts
      }, null, 2), "utf8");

      outputs.push({ flowId, pptxPath, qaPath, slides: result.slides.length + 2, qa: result.qa });
    }

    const summaryPath = join(outDir, "standard-flow-sample-summary.json");
    await writeFile(summaryPath, JSON.stringify({ generatedAt: new Date().toISOString(), outputs }, null, 2), "utf8");
    console.log(JSON.stringify({ outDir, summaryPath, outputs }, null, 2));
  } finally {
    await rm(tmpDir, { recursive: true, force: true });
  }
}

function runTsc() {
  const tsc = join(root, "node_modules", "typescript", "bin", "tsc");
  if (!existsSync(tsc)) {
    throw new Error(`TypeScript compiler not found: ${tsc}`);
  }
  execFileSync(process.execPath, [
    tsc,
    "--outDir",
    tmpDir,
    "--module",
    "ES2022",
    "--target",
    "ES2022",
    "--moduleResolution",
    "bundler",
    "--noEmit",
    "false",
    "--rootDir",
    "src"
  ], { cwd: root, stdio: "inherit" });
}

async function patchCompiledImports(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const moduleNames = [
    "patterns", "types", "planner", "ppt", "qa", "templates", "pptxQa", "fileImport",
    "layoutKnowledge", "qualityPolicy", "oneShotQuality", "useCases", "iterativePptxQa",
    "referenceStructureDb", "referenceTopN", "standardDeckFlow"
  ];

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      await patchCompiledImports(fullPath);
      continue;
    }
    if (!entry.name.endsWith(".js")) continue;
    let text = await readFile(fullPath, "utf8");
    for (const name of moduleNames) {
      text = text.replaceAll(`from "./${name}"`, `from "./${name}.js"`);
      text = text.replaceAll(`from './${name}'`, `from './${name}.js'`);
    }
    await writeFile(fullPath, text, "utf8");
  }
}

const flowInputs = {
  "reduction-kickoff-standard-flow": {
    clientName: "샘플 고객사",
    projectTitle: "감축사업 방법론 개발 착수보고",
    documentType: "착수보고",
    businessType: "reduction",
    meetingType: "kickoff",
    purpose: "프로젝트 착수",
    audience: "고객사 실무진",
    tone: "고급 컨설팅 보고",
    dateLabel: "2026.05",
    topic: "폐자원 재활용 기반 온실가스 감축사업",
    numbers: ["3,500 tCO2e/yr", "2개 사업장", "자료 12건"],
    bullets: [
      "사업 경계와 베이스라인을 먼저 고정해야 방법론 개발 리스크를 줄일 수 있음",
      "추가성, 대안 시나리오, 모니터링 가능성을 착수 단계에서 병행 검토",
      "법적 의무 여부와 보편적 관행 초과 여부를 핵심 판단 축으로 설정",
      "자료 제출 지연은 산정식 확정과 제3자 검증 일정에 직접 영향"
    ]
  },
  "disclosure-proposal-standard-flow": {
    clientName: "샘플 고객사",
    projectTitle: "CDP 및 기후공시 대응 컨설팅 제안",
    documentType: "제안서",
    businessType: "disclosure",
    meetingType: "proposal",
    purpose: "제안 및 입찰 대응",
    audience: "고객사 의사결정자",
    tone: "고급 컨설팅 제안서",
    dateLabel: "2026.05",
    topic: "CDP, Scope 3, 기후리스크, 공시 데이터 체계",
    numbers: ["핵심 대응 문항 45개", "우선 증빙 18개", "예상 수행기간 12주"],
    bullets: [
      "평가 점수 개선은 답변 작성보다 증빙 체계와 내부 책임 정렬이 선행되어야 함",
      "CDP 문항, 공시 기준, 고객 내부 데이터를 하나의 workstream으로 연결",
      "점수 영향도가 높은 문항부터 gap을 줄이는 방식으로 프로젝트 효율화",
      "산출물은 답변서뿐 아니라 차년도 반복 대응 가능한 운영체계까지 포함"
    ]
  },
  "ghg-inventory-final-standard-flow": {
    clientName: "샘플 고객사",
    projectTitle: "온실가스 인벤토리 최종보고",
    documentType: "최종보고",
    businessType: "inventory regulatory",
    meetingType: "final",
    purpose: "최종 결과 보고",
    audience: "고객사 실무진 및 검토자",
    tone: "실무 보고서",
    dateLabel: "2026.05",
    topic: "Scope 1, Scope 2, 배출량 산정 및 검증 대응",
    numbers: ["총 배출량 128,400 tCO2eq", "주요 배출원 6개", "보완 필요 항목 9개"],
    bullets: [
      "최종 배출량은 산정 경계와 활동자료 완전성 검토를 전제로 확정",
      "전년 대비 증감은 생산량, 연료 사용량, 전력 사용량 변화로 구분",
      "검증 대응을 위해 원천자료, 산정식, 배출계수 근거를 패키지화",
      "최종보고 이후에는 월별 모니터링과 자료 보관 체계로 전환 필요"
    ]
  }
};

function makeSlide(getRule, index, archetypeId, flow, meta, role) {
  const archetype = getRule(archetypeId);
  const roleText = role.replace(/^[^:]+:\s*/, "");
  const title = titleFor(archetypeId, roleText, meta);
  const sections = archetype.structure.map((label, idx) => `${label}: ${sectionValue(archetypeId, idx, meta)}`);
  const bullets = meta.bullets.slice(0, 4);
  return {
    index,
    title,
    body: `${roleText}\n${bullets.join("\n")}`,
    bullets,
    forcedArchetypeId: archetypeId,
    archetype,
    claimTitle: title,
    governingMessage: messageFor(archetypeId, meta),
    sections,
    rationale: `${flow.label}의 표준 deck flow에서 ${archetype.label} 구조를 적용`,
    density: "high"
  };
}

function titleFor(archetypeId, roleText, meta) {
  const map = {
    "consulting-executive-summary": "종합 판단 및 핵심 메시지",
    "why-what-how-logic": "추진 필요성과 접근 방향",
    "inventory-boundary-flow": "산정 경계 및 기준 시나리오",
    "comparison-matrix": "대안 및 판단 기준 비교",
    "integrated-process-map": "수행 프로세스 및 단계별 역할",
    "reduction-roadmap-analysis": "산정 로직 및 데이터 검토",
    "work-scope-table": "업무 범위와 산출물",
    "data-request-tracker": "요청자료 및 협조사항",
    "schedule-gantt": "향후 추진 일정",
    "evidence-to-action-strip": "결정사항 및 Next Action",
    "benchmark-readiness-summary": "현재 대응 수준 및 Gap",
    "cdp-response-strategy": "CDP 대응 전략",
    "disclosure-taxonomy-map": "공시 기준과 데이터 연결",
    "score-improvement-levers": "점수 개선 레버",
    "issue-tree-to-workplan": "핵심 이슈와 실행 과제",
    "proposal-scope-integrated": "제안 업무 범위",
    "report-production-workflow": "자료 취합 및 보고서 제작 흐름",
    "impact-factoid-big-number": "최종 배출량 핵심 결과",
    "waterfall-bridge-analysis": "전년 대비 증감 요인",
    "dashboard-kpi-takeaway": "배출량 KPI 대시보드",
    "assurance-evidence-pack": "검증 증빙 패키지",
    "traffic-light-scorecard": "보완 필요 항목",
    "regulatory-timeline-radar": "제출 및 검증 일정"
  };
  return map[archetypeId] ?? roleText.slice(0, 26) ?? meta.topic;
}

function messageFor(archetypeId, meta) {
  if (archetypeId.includes("schedule") || archetypeId.includes("timeline")) return "협조 시점과 결정 기준을 먼저 고정해야 일정 리스크가 줄어듭니다.";
  if (archetypeId.includes("data") || archetypeId.includes("evidence") || archetypeId.includes("assurance")) return "원천자료, 증빙, 담당 책임이 연결되어야 산출물 품질이 안정됩니다.";
  if (archetypeId.includes("reduction") || archetypeId.includes("boundary") || archetypeId.includes("inventory")) return "경계와 기준 시나리오가 명확해야 산정 결과를 신뢰할 수 있습니다.";
  if (archetypeId.includes("score") || archetypeId.includes("cdp") || archetypeId.includes("disclosure")) return "점수 개선은 증빙 체계와 실행 책임 정렬에서 결정됩니다.";
  return "핵심 판단 기준을 먼저 정렬해야 실행 과제로 전환됩니다.";
}

function sectionValue(archetypeId, idx, meta) {
  const values = [
    "핵심 판단 기준 정렬",
    `${meta.numbers[idx % meta.numbers.length]} 기준 연결`,
    "담당 부서와 제출 시점 고정",
    "보고서와 검증 대응에 재사용",
    "보완 요청, 담당, 기한 분리"
  ];
  if (archetypeId === "traffic-light-scorecard") return ["양호 항목은 유지", "점검 항목은 보완자료 필요", "주의 항목은 담당자 확인", "보완 항목은 기한 관리"][idx % 4];
  if (archetypeId === "impact-factoid-big-number") return meta.numbers[idx % meta.numbers.length];
  return values[idx % values.length];
}

await main();
