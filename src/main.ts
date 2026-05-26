import "./style.css";
import { downloadBlob } from "./ppt";
import { archetypeRules, getRule } from "./patterns";
import { extractTextFromFiles } from "./fileImport";
import { getAllStructureSampleInput, getLayoutFamilySampleInput, getSampleInput, planDeck } from "./planner";
import { buildPptxWithIterativeQa, type IterativePptxQaResult } from "./iterativePptxQa";
import { oneShotBriefTemplate, oneShotQaRules, oneShotStructureRules } from "./oneShotQuality";
import { qualityImprovementCycles } from "./qualityPolicy";
import { analyzeDeckQuality, type DeckQaReport, type QaStatus } from "./qa";
import { getTemplateProfile } from "./templates";
import { getUseCase, productUseCases } from "./useCases";
import { buildGptPptPrompt, buildGptPromptSummary, promptModes, type PromptMode } from "./promptGenerator";
import type { ArchetypeId, ArchetypeRule, DeckMeta, PlannedSlide } from "./types";

const app = document.querySelector<HTMLDivElement>("#app");
if (!app) throw new Error("App root not found");

let plannedSlides: PlannedSlide[] = [];
let currentDownloadUrl = "";
let storyboardApproved = false;
let currentPromptMode: PromptMode = "one-shot-deck";

interface ServerPptxExportResult {
  ok: true;
  fileName: string;
  savedName: string;
  bytes: number;
  localPath: string;
  url: string;
}

app.innerHTML = `
  <main class="shell">
    <section class="topbar">
      <div>
        <p class="eyebrow">INNerGEN Slide Studio</p>
        <h1>내용을 컨설팅 storyboard로 소화한 뒤 PPTX로 생성</h1>
        <p class="topbar-copy">사용자는 내용을 붙여넣고, AI가 제목·거버닝 메시지·장표 구조·QA 기준을 먼저 제안합니다.</p>
      </div>
      <div class="status-pill">Storyboard MVP</div>
    </section>

    <section class="flow">
      <div class="flow-step active"><strong>1</strong><span>자료 입력</span></div>
      <div class="flow-step active"><strong>2</strong><span>구조 자동 매칭</span></div>
      <div class="flow-step"><strong>3</strong><span>Storyboard 확인</span></div>
      <div class="flow-step"><strong>4</strong><span>QA 후 PPTX</span></div>
    </section>

    <section class="workspace">
      <aside class="panel input-panel">
        <div class="panel-head">
          <div>
            <h2>입력 조건</h2>
            <p>일반 사용자는 아래 조건만 정하면 됩니다.</p>
          </div>
          <div class="button-row">
            <button id="sampleBtn" type="button">샘플</button>
            <button id="oneShotBriefBtn" type="button">한큐 입력</button>
            <button id="allSampleBtn" type="button">구조 샘플북</button>
            <button id="layoutSampleBtn" type="button">렌더링 샘플북</button>
          </div>
        </div>

        <label>
          고객사
          <input id="clientName" value="고객사" />
        </label>
        <label>
          프로젝트명
          <input id="projectTitle" value="SBTi 검증, CDP 평가 및 기후리스크 통합 자문" />
        </label>
        <div class="two">
          <label>
            문서 유형
            <select id="documentType">
              <option>컨설팅 제안서</option>
              <option>착수보고</option>
              <option>중간보고</option>
              <option>최종보고</option>
              <option>임원보고</option>
              <option>교육자료</option>
            </select>
          </label>
          <label>
            날짜
            <input id="dateLabel" value="${formatLocalDate()}" />
          </label>
        </div>
        <div class="three">
          <label>
            목적
            <select id="purpose">
              <option>제안·입찰 대응</option>
              <option>프로젝트 착수</option>
              <option>현황 진단</option>
              <option>의사결정 보고</option>
              <option>실행계획 수립</option>
            </select>
          </label>
          <label>
            대상
            <select id="audience">
              <option>고객사 실무진</option>
              <option>고객사 임원</option>
              <option>검증기관</option>
              <option>내부 검토자</option>
            </select>
          </label>
          <label>
            톤
            <select id="tone">
              <option>고급 컨설팅 제안서</option>
              <option>실무 보고서</option>
              <option>임원 요약</option>
              <option>워크숍 자료</option>
            </select>
          </label>
        </div>

        <div id="templateInfo" class="template-info"></div>

        <section class="use-case-panel">
          <div class="use-case-head">
            <strong>활용 시나리오</strong>
            <span>업무 목적을 고르면 입력 예시와 PPT 구조가 함께 맞춰집니다.</span>
          </div>
          <div class="use-case-grid">
            ${productUseCases.map((useCase) => `<button class="use-case-option" type="button" data-use-case="${useCase.id}">${useCase.shortLabel}</button>`).join("")}
          </div>
          <div id="useCaseInfo" class="use-case-info"></div>
        </section>

        <section class="pdca-board">
          <div class="use-case-head">
            <strong>PDCA 품질 개선판</strong>
            <span>생성기는 아래 10개 품질 기준을 따라 Storyboard와 PPTX를 점검합니다.</span>
          </div>
          <ol>
            ${qualityImprovementCycles.map((cycle) => `<li><strong>${cycle.id.toUpperCase()}</strong><span>${cycle.title}</span></li>`).join("")}
          </ol>
        </section>

        <section class="one-shot-panel">
          <div class="use-case-head">
            <strong>한큐 생성 구조화 규칙</strong>
            <span>한 번에 원하는 수준까지 가려면 입력, 구조, QA가 동시에 잠겨야 합니다.</span>
          </div>
          <div class="one-shot-grid">
            ${oneShotQaRules.slice(0, 6).map((rule) => `<div><strong>${rule.gate}</strong><span>${rule.rule}</span></div>`).join("")}
          </div>
          <details>
            <summary>문서 유형별 권장 흐름 보기</summary>
            ${oneShotStructureRules.map((rule) => `<p><strong>${rule.documentType}</strong> ${rule.storyline.join(" → ")}</p>`).join("")}
          </details>
        </section>

        <label>
          원본 파일 업로드
          <input id="fileInput" type="file" multiple accept=".txt,.md,.csv,.tsv,.pdf,.pptx,.docx" />
          <span id="fileStatus" class="file-status">PDF, PPTX, DOCX, TXT를 업로드하면 텍스트를 자동으로 불러옵니다.</span>
        </label>

        <label>
          내용 입력
          <textarea id="slideInput" spellcheck="false" placeholder="슬라이드 구분 없이 붙여넣어도 됩니다.&#10;가능하면 핵심 문장과 근거를 줄 단위로 넣어주세요."></textarea>
        </label>

        <div class="actions">
          <button id="analyzeBtn" class="primary" type="button">1. Storyboard 설계</button>
          <button id="refreshBtn" type="button" disabled>2. 수정 반영 / QA</button>
          <button id="exportBtn" type="button" disabled>3. PPTX 생성</button>
          <button id="promptBtn" type="button">GPT 프롬프트 생성</button>
        </div>
        <label class="approval">
          <input id="approveStoryboard" type="checkbox" />
          <span>Storyboard를 확인했고 이 구조로 PPTX를 생성합니다.</span>
        </label>
        <div id="downloadArea" class="download-area" hidden></div>
      </aside>

      <section class="panel output-panel">
        <div class="panel-head">
          <div>
            <h2>Storyboard & QA</h2>
            <p>제목, governing message, 구조, 본문 항목을 확인한 뒤 PPTX를 생성합니다.</p>
          </div>
          <span id="summaryText">아직 분석 전입니다.</span>
        </div>
        <div id="result" class="empty">
          내용을 입력하면 장표별 추천 구조와 QA 결과가 표시됩니다.
        </div>
        <section id="promptPanel" class="prompt-panel" hidden>
          <div class="prompt-panel-head">
            <div>
              <strong>ChatGPT 채팅창용 프롬프트</strong>
              <span id="promptSummary">Storyboard를 먼저 생성하면 목적별 프롬프트가 만들어집니다.</span>
            </div>
            <div class="prompt-actions">
              <button id="copyPromptBtn" class="primary" type="button">복사</button>
              <button id="downloadPromptBtn" type="button">MD 저장</button>
              <button id="closePromptBtn" type="button">닫기</button>
            </div>
          </div>
          <div class="prompt-mode-bar">
            ${promptModes.map((mode) => `<button class="prompt-mode-option" type="button" data-prompt-mode="${mode.id}"><strong>${mode.label}</strong><span>${mode.description}</span></button>`).join("")}
          </div>
          <textarea id="promptOutput" spellcheck="false"></textarea>
        </section>
      </section>
    </section>
  </main>
`;

const sampleBtn = document.querySelector<HTMLButtonElement>("#sampleBtn")!;
const oneShotBriefBtn = document.querySelector<HTMLButtonElement>("#oneShotBriefBtn")!;
const allSampleBtn = document.querySelector<HTMLButtonElement>("#allSampleBtn")!;
const layoutSampleBtn = document.querySelector<HTMLButtonElement>("#layoutSampleBtn")!;
const analyzeBtn = document.querySelector<HTMLButtonElement>("#analyzeBtn")!;
const refreshBtn = document.querySelector<HTMLButtonElement>("#refreshBtn")!;
const exportBtn = document.querySelector<HTMLButtonElement>("#exportBtn")!;
const promptBtn = document.querySelector<HTMLButtonElement>("#promptBtn")!;
const slideInput = document.querySelector<HTMLTextAreaElement>("#slideInput")!;
const fileInput = document.querySelector<HTMLInputElement>("#fileInput")!;
const fileStatus = document.querySelector<HTMLSpanElement>("#fileStatus")!;
const templateInfo = document.querySelector<HTMLDivElement>("#templateInfo")!;
const useCaseInfo = document.querySelector<HTMLDivElement>("#useCaseInfo")!;
const result = document.querySelector<HTMLDivElement>("#result")!;
const summaryText = document.querySelector<HTMLSpanElement>("#summaryText")!;
const downloadArea = document.querySelector<HTMLDivElement>("#downloadArea")!;
const approveStoryboard = document.querySelector<HTMLInputElement>("#approveStoryboard")!;
const promptPanel = document.querySelector<HTMLElement>("#promptPanel")!;
const promptOutput = document.querySelector<HTMLTextAreaElement>("#promptOutput")!;
const promptSummary = document.querySelector<HTMLSpanElement>("#promptSummary")!;
const copyPromptBtn = document.querySelector<HTMLButtonElement>("#copyPromptBtn")!;
const downloadPromptBtn = document.querySelector<HTMLButtonElement>("#downloadPromptBtn")!;
const closePromptBtn = document.querySelector<HTMLButtonElement>("#closePromptBtn")!;

slideInput.value = getSampleInput();
renderUseCaseInfo(productUseCases[0].id);
setUseCaseActive(productUseCases[0].id);
setPromptModeActive(currentPromptMode);

sampleBtn.addEventListener("click", () => {
  slideInput.value = getSampleInput();
  valueInto("projectTitle", "SBTi 검증, CDP 평가 및 기후리스크 통합 자문");
  selectValue("documentType", "컨설팅 제안서");
  selectValue("purpose", "제안·입찰 대응");
  runAnalyze();
});

oneShotBriefBtn.addEventListener("click", () => {
  slideInput.value = oneShotBriefTemplate;
  setStoryboardApproved(false);
  runAnalyze();
});

allSampleBtn.addEventListener("click", () => {
  slideInput.value = getAllStructureSampleInput();
  valueInto("projectTitle", "이너젠 컨설팅 장표 구조 샘플북");
  selectValue("documentType", "컨설팅 제안서");
  selectValue("purpose", "의사결정 보고");
  runAnalyze();
});

layoutSampleBtn.addEventListener("click", () => {
  slideInput.value = getLayoutFamilySampleInput();
  valueInto("projectTitle", "이너젠 레이아웃 렌더링 샘플북");
  selectValue("documentType", "컨설팅 제안서");
  selectValue("purpose", "의사결정 보고");
  runAnalyze();
});

document.querySelectorAll<HTMLButtonElement>(".use-case-option").forEach((button) => {
  button.addEventListener("click", () => applyUseCase(button.dataset.useCase ?? productUseCases[0].id));
});

document.querySelectorAll<HTMLButtonElement>(".prompt-mode-option").forEach((button) => {
  button.addEventListener("click", () => {
    currentPromptMode = (button.dataset.promptMode as PromptMode | undefined) ?? "one-shot-deck";
    setPromptModeActive(currentPromptMode);
    if (!promptPanel.hidden) renderPromptGenerator();
  });
});

fileInput.addEventListener("change", async () => {
  if (!fileInput.files?.length) return;
  fileStatus.textContent = "파일에서 텍스트를 추출하는 중입니다...";
  try {
    const imported = await extractTextFromFiles(fileInput.files);
    if (imported.text) {
      slideInput.value = imported.text;
      fileStatus.textContent = `${imported.files.join(", ")} 불러오기 완료${imported.warnings.length ? ` / 주의 ${imported.warnings.length}건` : ""}`;
      runAnalyze();
    } else {
      fileStatus.textContent = imported.warnings.join(" ") || "불러올 텍스트가 없습니다.";
    }
  } catch (error) {
    fileStatus.textContent = error instanceof Error ? error.message : String(error);
  }
});

analyzeBtn.addEventListener("click", runAnalyze);
refreshBtn.addEventListener("click", () => {
  readStoryboardEdits();
  setStoryboardApproved(false);
  renderResults(plannedSlides);
});

approveStoryboard.addEventListener("change", () => {
  storyboardApproved = approveStoryboard.checked;
  updateExportState();
});

result.addEventListener("input", (event) => {
  const target = event.target as HTMLElement;
  if (target.closest(".slide-card")) setStoryboardApproved(false);
});

for (const id of ["documentType", "purpose", "audience", "tone"]) {
  document.querySelector<HTMLSelectElement>(`#${id}`)?.addEventListener("change", () => {
    updateTemplateInfo();
    setStoryboardApproved(false);
  });
}

exportBtn.addEventListener("click", async () => {
  if (!plannedSlides.length) return;
  readStoryboardEdits();
  renderResults(plannedSlides);
  exportBtn.disabled = true;
  exportBtn.textContent = "생성 중...";
  try {
    const meta = readMeta();
    const qaResult = await buildPptxWithIterativeQa(meta, plannedSlides, 3);
    const { blob, fileName } = qaResult;
    plannedSlides = qaResult.slides;
    const serverExport = await exportPptxToServer(meta, plannedSlides);
    showDownloadLink(blob, fileName, qaResult, serverExport);
    if (serverExport) {
      tryServerDownload(serverExport.url);
    } else {
      tryAutoDownload(blob, fileName);
    }
  } catch (error) {
    showExportError(error);
  } finally {
    exportBtn.disabled = false;
    exportBtn.textContent = "3. PPTX 생성";
    updateExportState();
  }
});

promptBtn.addEventListener("click", () => {
  if (!plannedSlides.length) runAnalyze();
  readStoryboardEdits();
  renderPromptGenerator();
});

copyPromptBtn.addEventListener("click", async () => {
  await copyPromptToClipboard();
});

downloadPromptBtn.addEventListener("click", () => {
  downloadPromptAsMarkdown();
});

closePromptBtn.addEventListener("click", () => {
  promptPanel.hidden = true;
});

runAnalyze();

function runAnalyze() {
  plannedSlides = planDeck(slideInput.value, readMeta());
  refreshBtn.disabled = !plannedSlides.length;
  setStoryboardApproved(false);
  updateTemplateInfo();
  renderResults(plannedSlides);
}

function readMeta(): DeckMeta {
  return {
    clientName: valueOf("clientName"),
    projectTitle: valueOf("projectTitle"),
    documentType: valueOf("documentType"),
    dateLabel: valueOf("dateLabel"),
    purpose: valueOf("purpose"),
    audience: valueOf("audience"),
    tone: valueOf("tone")
  };
}

function valueOf(id: string): string {
  const element = document.querySelector<HTMLInputElement | HTMLSelectElement>(`#${id}`);
  return element?.value.trim() ?? "";
}

function valueInto(id: string, value: string) {
  const input = document.querySelector<HTMLInputElement>(`#${id}`);
  if (input) input.value = value;
}

function selectValue(id: string, value: string) {
  const select = document.querySelector<HTMLSelectElement>(`#${id}`);
  if (select) select.value = value;
}

function setStoryboardApproved(value: boolean) {
  storyboardApproved = value;
  approveStoryboard.checked = value;
  updateExportState();
}

function updateExportState() {
  exportBtn.disabled = !plannedSlides.length || !storyboardApproved;
}

function updateTemplateInfo() {
  const profile = getTemplateProfile(readMeta());
  templateInfo.innerHTML = `
    <strong>${escapeHtml(profile.label)} 템플릿 적용</strong>
    <span>${escapeHtml(profile.description)}</span>
    <em>${escapeHtml(profile.sequence.slice(0, 5).map((id) => getRule(id).label).join(" → "))}</em>
  `;
}

function applyUseCase(id: string) {
  const useCase = getUseCase(id);
  valueInto("projectTitle", useCase.projectTitle);
  selectValue("documentType", useCase.documentType);
  selectValue("purpose", useCase.purpose);
  selectValue("audience", useCase.audience);
  selectValue("tone", useCase.tone);
  slideInput.value = useCase.sampleInput;
  renderUseCaseInfo(useCase.id);
  setUseCaseActive(useCase.id);
  runAnalyze();
}

function renderUseCaseInfo(id: string) {
  const useCase = getUseCase(id);
  useCaseInfo.innerHTML = `
    <strong>${escapeHtml(useCase.label)}</strong>
    <span>${escapeHtml(useCase.workflow.join(" → "))}</span>
    <em>산출물: ${escapeHtml(useCase.outputs.join(" · "))}</em>
  `;
}

function setUseCaseActive(id: string) {
  document.querySelectorAll<HTMLButtonElement>(".use-case-option").forEach((button) => {
    button.classList.toggle("active", button.dataset.useCase === id);
  });
}

function setPromptModeActive(mode: PromptMode) {
  document.querySelectorAll<HTMLButtonElement>(".prompt-mode-option").forEach((button) => {
    button.classList.toggle("active", button.dataset.promptMode === mode);
  });
}

function renderResults(slides: PlannedSlide[]) {
  if (!slides.length) {
    result.className = "empty";
    result.textContent = "분석할 내용이 없습니다.";
    summaryText.textContent = "아직 분석 전입니다.";
    updateExportState();
    return;
  }

  const qa = analyzeDeckQuality(slides, readMeta());
  summaryText.textContent = `${slides.length}개 슬라이드 / QA ${qa.score}점 / ${statusText(qa.status)}`;
  result.className = "result-list";
  result.innerHTML = `
    ${renderQaSummary(qa)}
    ${slides.map((slide, index) => renderSlideCard(slide, index, qa)).join("")}
  `;
  updateExportState();
}

function renderPromptGenerator() {
  if (!plannedSlides.length) return;
  const meta = readMeta();
  const prompt = buildGptPptPrompt(meta, plannedSlides, currentPromptMode);
  const summary = buildGptPromptSummary(meta, plannedSlides, currentPromptMode);
  promptOutput.value = prompt;
  promptSummary.textContent = `${summary.modeLabel} / ${summary.slideCount}장 / 구조 ${summary.structureCount}종 / QA 규칙 ${summary.qaRuleCount}개 / 개선 경고 ${summary.recommendationCount}개`;
  promptPanel.hidden = false;
  promptOutput.focus();
  promptOutput.setSelectionRange(0, 0);
}

async function copyPromptToClipboard() {
  if (!promptOutput.value) return;
  try {
    await navigator.clipboard.writeText(promptOutput.value);
    copyPromptBtn.textContent = "복사 완료";
  } catch {
    promptOutput.select();
    document.execCommand("copy");
    copyPromptBtn.textContent = "복사 완료";
  } finally {
    window.setTimeout(() => {
      copyPromptBtn.textContent = "복사";
    }, 1400);
  }
}

function downloadPromptAsMarkdown() {
  if (!promptOutput.value) renderPromptGenerator();
  if (!promptOutput.value) return;
  const meta = readMeta();
  const fileName = `${formatLocalDate()}_${safeFilePart(meta.clientName)}_${safeFilePart(meta.projectTitle)}_${currentPromptMode}_prompt.md`;
  const blob = new Blob([promptOutput.value], { type: "text/markdown;charset=utf-8" });
  downloadBlob(blob, fileName);
}

function safeFilePart(value: string) {
  return (value || "innergen")
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, "_")
    .replace(/_+/g, "_")
    .slice(0, 80);
}

function renderQaSummary(qa: DeckQaReport) {
  return `
    <section class="qa-summary qa-${qa.status}">
      <div>
        <strong>품질 점수 ${qa.score}점</strong>
        <span>${qa.passCount}개 통과 · ${qa.warnCount}개 주의 · ${qa.failCount}개 수정 필요 · 한큐 준비도 ${qa.oneShot.score}점</span>
      </div>
      <p>이 검사는 PPT 생성 전 논리/분량/나열식 표현을 점검합니다. 최종 다운로드 전 수정 반영 / QA 버튼으로 다시 확인하세요.</p>
      <div class="qa-global">
        ${qa.globalChecks.map((check) => `<span class="qa-chip qa-${check.status}">${escapeHtml(check.label)} · ${escapeHtml(check.detail)}</span>`).join("")}
      </div>
      <div class="one-shot-score one-shot-${qa.oneShot.status}">
        <strong>한큐 생성 준비도 ${qa.oneShot.score}점</strong>
        <span>${qa.oneShot.checks.filter((check) => check.status === "pass").length}개 통과 · ${qa.oneShot.checks.filter((check) => check.status === "warn").length}개 주의 · ${qa.oneShot.checks.filter((check) => check.status === "fail").length}개 수정 필요</span>
      </div>
      ${qa.improvementActions.length ? `<ul class="qa-actions">${qa.improvementActions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>` : ""}
    </section>
  `;
}

function renderSlideCard(slide: PlannedSlide, index: number, qa: DeckQaReport) {
  const slideQa = qa.slideResults[index];
  return `
    <article class="slide-card" data-slide-idx="${index}">
      <div class="slide-num">${String(slide.index).padStart(2, "0")}</div>
      <div class="slide-body">
        <div class="card-top">
          <div>
            <label class="compact-label">
              상단 제목
              <input class="story-title" value="${escapeAttr(slide.claimTitle)}" />
            </label>
          </div>
          <label class="compact-label structure-select">
            추천 구조
            <select class="story-archetype">${renderArchetypeOptions(slide.archetype.id)}</select>
          </label>
        </div>

        <label class="compact-label">
          Governing message
          <textarea class="story-governing" rows="2">${escapeHtml(slide.governingMessage)}</textarea>
        </label>

        <div class="grid">
          <div>
            <strong>구조</strong>
            <p>${escapeHtml(slide.archetype.structure.join(" → "))}</p>
          </div>
          <div>
            <strong>레이아웃</strong>
            <p>${escapeHtml(slide.archetype.layoutHint)}</p>
          </div>
          <div>
            <strong>검토 포인트</strong>
            <p>${escapeHtml(slide.archetype.safetyRule)}</p>
          </div>
        </div>

        <label class="compact-label">
          본문 구조화 항목
          <textarea class="story-sections" rows="5">${escapeHtml(slide.sections.join("\n"))}</textarea>
        </label>

        <div class="qa-lines">
          ${slideQa.checks.map((check) => `<span class="qa-line qa-${check.status}">${escapeHtml(check.label)}: ${escapeHtml(check.detail)}</span>`).join("")}
        </div>
        <p class="rationale">${escapeHtml(slide.rationale)}</p>
      </div>
    </article>
  `;
}

function renderArchetypeOptions(selectedId: ArchetypeId) {
  return archetypeRules
    .map((rule) => `<option value="${rule.id}" ${rule.id === selectedId ? "selected" : ""}>${escapeHtml(rule.label)}</option>`)
    .join("");
}

function readStoryboardEdits() {
  const cards = Array.from(result.querySelectorAll<HTMLElement>(".slide-card[data-slide-idx]"));
  if (!cards.length) return;

  plannedSlides = cards.map((card, index) => {
    const current = plannedSlides[index];
    const title = card.querySelector<HTMLInputElement>(".story-title")?.value.trim() || current.claimTitle;
    const governing = card.querySelector<HTMLTextAreaElement>(".story-governing")?.value.trim() || current.governingMessage;
    const archetypeId = card.querySelector<HTMLSelectElement>(".story-archetype")?.value as ArchetypeId | undefined;
    const archetype = getRule(archetypeId ?? current.archetype.id) as ArchetypeRule;
    const sectionText = card.querySelector<HTMLTextAreaElement>(".story-sections")?.value ?? "";
    const sections = normalizeSectionLines(sectionText, archetype, current);

    return {
      ...current,
      archetype,
      claimTitle: title,
      governingMessage: governing,
      sections
    };
  });
}

function normalizeSectionLines(text: string, archetype: ArchetypeRule, slide: PlannedSlide) {
  const lines = text
    .split("\n")
    .map((line) => line.replace(/^[\-*•·‣]\s*/, "").trim())
    .filter(Boolean)
    .slice(0, 6);

  if (!lines.length) return slide.sections;
  return lines.map((line, index) => (line.includes(":") ? line : `${archetype.structure[index] ?? `항목 ${index + 1}`}: ${line}`));
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    const map: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    };
    return map[char] ?? char;
  });
}

function escapeAttr(value: string): string {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

function statusText(status: QaStatus) {
  if (status === "pass") return "통과";
  if (status === "warn") return "주의";
  return "수정 필요";
}

async function exportPptxToServer(meta: DeckMeta, slides: PlannedSlide[]): Promise<ServerPptxExportResult | null> {
  try {
    const response = await fetch("/api/export-pptx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ meta, slides })
    });
    const payload = (await response.json()) as ServerPptxExportResult | { ok: false; error?: string };
    if (!response.ok || !payload.ok) {
      throw new Error("error" in payload ? payload.error || "서버 저장 실패" : "서버 저장 실패");
    }
    return payload;
  } catch (error) {
    console.warn("Server PPTX export failed; falling back to browser download.", error);
    return null;
  }
}

function showDownloadLink(blob: Blob, fileName: string, qaResult: IterativePptxQaResult, serverExport: ServerPptxExportResult | null) {
  const pptxQa = qaResult.qa;
  if (currentDownloadUrl) URL.revokeObjectURL(currentDownloadUrl);
  currentDownloadUrl = URL.createObjectURL(blob);
  const downloadUrl = serverExport?.url ?? currentDownloadUrl;
  const downloadName = serverExport?.savedName ?? fileName;
  const attemptRows = qaResult.attempts
    .map(
      (attempt) =>
        `<small>QA ${attempt.pass}차 · ${escapeHtml(attempt.action)} · ${attempt.qa.score}점/${statusText(attempt.qa.status)} · 넘침 ${attempt.qa.overflowRiskCount} · 겹침 ${attempt.qa.overlapRiskCount} · 단어깨짐 ${attempt.qa.narrowTextRiskCount}</small>`
    )
    .join("");
  downloadArea.hidden = false;
  downloadArea.className = "download-area";
  downloadArea.innerHTML = `
    <div>
      <strong>PPTX 생성 완료</strong>
      <span>PPTX QA ${qaResult.attempts.length}회 수행 · 최종 ${pptxQa.score}점 / ${statusText(pptxQa.status)} · ${(serverExport?.bytes ?? blob.size).toLocaleString()} bytes</span>
      <small>슬라이드 ${pptxQa.slideCount}장 · 최소 폰트 ${pptxQa.minFontSize ?? "-"}pt · 넘침 위험 ${pptxQa.overflowRiskCount}건 · 겹침 위험 ${pptxQa.overlapRiskCount}건 · 단어 깨짐 위험 ${pptxQa.narrowTextRiskCount}건</small>
      ${attemptRows}
      <small>${serverExport ? `실제 파일 저장 완료: ${escapeHtml(serverExport.localPath)}` : "서버 저장을 사용할 수 없어 브라우저 다운로드 방식으로 전환했습니다."}</small>
    </div>
    <div class="download-buttons">
      <button id="manualDownloadBtn" class="primary" type="button">PPTX 다운로드</button>
      <button id="saveAsBtn" type="button">다른 이름으로 저장</button>
      <a id="downloadAnchor" href="${downloadUrl}" download="${escapeHtml(downloadName)}">링크로 받기</a>
    </div>
  `;
  downloadArea.querySelector<HTMLButtonElement>("#manualDownloadBtn")?.addEventListener("click", () => {
    if (serverExport) {
      window.location.href = serverExport.url;
      return;
    }
    downloadBlob(blob, fileName);
  });
  downloadArea.querySelector<HTMLButtonElement>("#saveAsBtn")?.addEventListener("click", async () => {
    await saveWithFilePicker(blob, fileName);
  });
}

function tryServerDownload(url: string) {
  setTimeout(() => {
    const link = document.createElement("a");
    link.href = url;
    link.download = "";
    document.body.appendChild(link);
    link.click();
    link.remove();
  }, 0);
}

function tryAutoDownload(blob: Blob, fileName: string) {
  setTimeout(() => {
    try {
      downloadBlob(blob, fileName);
    } catch {
      // The manual buttons remain available when the browser blocks automatic downloads.
    }
  }, 0);
}

async function saveWithFilePicker(blob: Blob, fileName: string) {
  const picker = (window as unknown as {
    showSaveFilePicker?: (options: {
      suggestedName: string;
      types: Array<{ description: string; accept: Record<string, string[]> }>;
    }) => Promise<{
      createWritable: () => Promise<{ write: (data: Blob) => Promise<void>; close: () => Promise<void> }>;
    }>;
  }).showSaveFilePicker;

  if (!picker) {
    downloadBlob(blob, fileName);
    return;
  }

  const handle = await picker({
    suggestedName: fileName,
    types: [{ description: "PowerPoint Presentation", accept: { "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"] } }]
  });
  const writable = await handle.createWritable();
  await writable.write(blob);
  await writable.close();
}

function showExportError(error: unknown) {
  downloadArea.hidden = false;
  downloadArea.className = "download-area download-error";
  downloadArea.innerHTML = `
    <div>
      <strong>PPTX 생성 중 오류가 발생했습니다</strong>
      <span>${escapeHtml(error instanceof Error ? error.message : String(error))}</span>
      <small>Storyboard를 다시 QA한 뒤 재시도하세요.</small>
    </div>
  `;
}

function formatLocalDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
