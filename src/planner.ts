import { archetypeRules } from "./patterns";
import { buildAllStructureSampleInput, buildLayoutFamilySampleInput } from "./layoutKnowledge";
import { getTemplateArchetype } from "./templates";
import type { ArchetypeId, DeckMeta, PlannedSlide, RawSlide } from "./types";

const sampleDeck = `슬라이드 1: 컨설팅 목적
- 글로벌 공시 및 이해관계자 요구 강화로 Scope 1/2/3 배출량, 감축목표, 검증 체계를 함께 정비해야 합니다.
- SBTi 검증, CDP 평가, 기후리스크 분석을 분리 대응하면 자료 중복과 일정 리스크가 커집니다.
- 초기 4주 안에 기준연도, 조직경계, 담당부서, 증빙 위치를 확정하는 것이 전체 프로젝트의 핵심입니다.

---
슬라이드 2: 통합 수행 범위
- Scope 1/2/3 인벤토리 정합성 검토와 배출계수 적용 기준을 정리합니다.
- SBTi 목표 개발, Target Submission Form 작성, 검증 질의 대응을 지원합니다.
- CDP 문항 분석, 증빙 수집, 답변 작성, ORS 제출 QA를 수행합니다.
- 물리/전환 리스크 시나리오 분석 결과를 공시 대응 논리와 연결합니다.

---
슬라이드 3 [archetype:method-chevron]: 프로젝트 수행 방법론
- 진단: 기준연도, 조직경계, 데이터 보유 현황을 확인합니다.
- 설계: SBTi, CDP, 기후리스크 요구사항을 하나의 업무 흐름으로 통합합니다.
- 실행: 자료 취합, 계산 검토, 답변 초안, 리스크 분석을 병행합니다.
- 검증: 내부 QA와 고객 검토를 거쳐 제출 가능한 산출물로 정리합니다.

---
슬라이드 4 [archetype:data-request-tracker]: 자료 요청 관리
- 배출량 원천자료: 전력, 연료, 냉매, 공정가스 사용량과 계산 근거를 확인합니다.
- 조직 자료: 법인, 사업장, 연결범위, 담당부서 정보를 확인합니다.
- 증빙 자료: 청구서, 계측기록, 내부 승인 이력, 제출본을 연결합니다.
- 상태 관리: 누락, 보완, 검토완료 자료를 담당자와 기한 기준으로 추적합니다.`;

const allStructureSamples: Partial<Record<ArchetypeId, { title: string; bullets: string[] }>> = {
  "consulting-executive-summary": {
    title: "경영진 보고 요약",
    bullets: ["배출량 산정 체계와 공시 대응은 동일한 데이터 기반에서 관리되어야 합니다.", "현재 핵심 리스크는 자료 중복, 담당 불명확, 증빙 누락입니다.", "초기 진단에서 기준연도와 조직경계를 확정하면 전체 일정 리스크를 줄일 수 있습니다."]
  },
  "why-what-how-logic": {
    title: "공시 기준 변화 대응 방향",
    bullets: ["Why: 투자자와 고객사의 기후정보 요구가 정량 데이터 중심으로 바뀌고 있습니다.", "What: 배출량, 목표, 리스크, 거버넌스를 하나의 설명 체계로 정리해야 합니다.", "How: 데이터 소유자, 증빙 위치, 검토 기준을 표준화합니다."]
  },
  "proposal-need-three-cards": {
    title: "통합 자문 추진 필요성",
    bullets: ["규제 요구: 공시 기준과 평가기관의 증빙 요구가 확대되고 있습니다.", "이해관계자 요구: 고객사와 투자자는 비교 가능한 데이터와 관리 체계를 요구합니다.", "내부 대응: 중복 작업을 줄이고 제출 일정을 안정화해야 합니다."]
  }
};

export function getSampleInput(): string {
  return sampleDeck;
}

export function getAllStructureSampleInput(): string {
  return buildAllStructureSampleInput();
}

export function getLayoutFamilySampleInput(): string {
  return buildLayoutFamilySampleInput();
}

export function parseSlides(input: string): RawSlide[] {
  const normalized = input.replace(/\r\n/g, "\n").trim();
  if (!normalized) return [];

  const hasExplicitSeparator = /^-{3,}\s*$/m.test(normalized);
  const hasSlideMarkers = /^(?:#{1,3}\s+)?(?:슬라이드|slide)\s*\d+\s*[:.)-]?\s*/im.test(normalized);

  if (!hasExplicitSeparator && !hasSlideMarkers) {
    return parseFreeformInput(normalized);
  }

  const chunks = hasExplicitSeparator ? normalized.split(/^-{3,}\s*$/m) : splitBySlideMarkers(normalized);

  return chunks
    .map((chunk, index) => parseChunk(chunk, index + 1))
    .filter((slide) => slide.title || slide.body);
}

function splitBySlideMarkers(input: string): string[] {
  const lines = input.split("\n");
  const chunks: string[] = [];
  let current: string[] = [];
  const marker = /^(?:#{1,3}\s+)?(?:슬라이드|slide)\s*\d+\s*[:.)-]?\s*/i;

  for (const line of lines) {
    if (marker.test(line.trim()) && current.length) {
      chunks.push(current.join("\n"));
      current = [line];
    } else {
      current.push(line);
    }
  }
  if (current.length) chunks.push(current.join("\n"));
  return chunks.length > 1 ? chunks : [input];
}

function parseFreeformInput(input: string): RawSlide[] {
  const lines = input
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const grouped = groupByHeadings(lines);
  if (grouped.length >= 2) {
    return grouped.map((group, index) => rawFromGroup(group.title, group.items, index + 1));
  }

  const sentences = lines.flatMap((line) => splitSentences(line)).filter(Boolean);
  const chunks = chunk(sentences.length ? sentences : lines, 4);
  return chunks.map((items, index) => rawFromGroup(inferFreeformTitle(items, index + 1), items, index + 1));
}

function groupByHeadings(lines: string[]) {
  const groups: { title: string; items: string[] }[] = [];
  let currentTitle = "";
  let currentItems: string[] = [];

  for (const line of lines) {
    const cleaned = line.replace(/^[\-*•·‣]\s*/, "").trim();
    if (isHeadingLine(line) && currentItems.length) {
      groups.push({ title: currentTitle || inferFreeformTitle(currentItems, groups.length + 1), items: currentItems });
      currentTitle = cleaned;
      currentItems = [];
    } else if (isHeadingLine(line) && !currentTitle) {
      currentTitle = cleaned;
    } else {
      currentItems.push(cleaned);
    }
  }

  if (currentItems.length) {
    groups.push({ title: currentTitle || inferFreeformTitle(currentItems, groups.length + 1), items: currentItems });
  }

  return groups.filter((group) => group.items.length);
}

function isHeadingLine(line: string) {
  const trimmed = line.trim();
  const withoutMarker = trimmed.replace(/^[\-*•·‣]\s*/, "").trim();
  if (withoutMarker !== trimmed) return false;
  if (/^[0-9]+[.)]\s+/.test(withoutMarker)) return true;
  if (/^[가-힣A-Za-z0-9 /&·]{2,34}$/.test(withoutMarker) && !/[.。]$/.test(withoutMarker)) return true;
  return /^[#]{1,3}\s+/.test(trimmed);
}

function rawFromGroup(title: string, items: string[], index: number): RawSlide {
  const bullets = items
    .map((item) => item.replace(/^[0-9]+[.)]\s*/, "").replace(/^[\-*•·‣]\s*/, "").trim())
    .filter(Boolean)
    .slice(0, 6);
  return {
    index,
    title: normalizeTitle(title || `핵심 내용 ${index}`),
    body: bullets.join("\n"),
    bullets: bullets.length ? bullets : [`핵심 내용을 ${index}번 장표에서 구조화합니다.`]
  };
}

function inferFreeformTitle(items: string[], index: number) {
  const first = cleanSentence(items[0] ?? "");
  const beforeColon = first.split(":")[0]?.trim();
  if (beforeColon && beforeColon.length >= 3 && beforeColon.length <= 28) return beforeColon;
  if (first.length >= 4 && first.length <= 30) return first;
  return `핵심 내용 ${index}`;
}

function chunk<T>(items: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < items.length; i += size) chunks.push(items.slice(i, i + size));
  return chunks;
}

function parseChunk(chunk: string, index: number): RawSlide {
  const lines = chunk
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
  const first = lines[0] ?? `슬라이드 ${index}`;
  const forcedArchetypeId = parseForcedArchetype(first);
  const title = cleanTitle(first, index);
  const bodyLines = lines.slice(1);
  const body = bodyLines.join("\n");
  const bullets = bodyLines
    .map((line) => line.replace(/^[\-*•·‣]\s*/, "").trim())
    .filter(Boolean);

  return {
    index,
    title,
    body,
    bullets: bullets.length ? bullets : splitSentences(body || title),
    forcedArchetypeId
  };
}

function cleanTitle(value: string, index: number): string {
  const removed = value
    .replace(/^#{1,3}\s*/, "")
    .replace(/^(?:슬라이드|slide)\s*\d+\s*[:.)-]?\s*/i, "")
    .replace(/\[archetype:[^\]]+\]/i, "")
    .replace(/^[:.)-]\s*/, "")
    .trim();
  return removed || `슬라이드 ${index}`;
}

function parseForcedArchetype(value: string): ArchetypeId | undefined {
  const match = value.match(/\[archetype:([a-z0-9-]+)\]/i);
  const id = match?.[1] as ArchetypeId | undefined;
  return id && archetypeRules.some((rule) => rule.id === id) ? id : undefined;
}

function splitSentences(text: string): string[] {
  return text
    .split(/[.!?。]\s+|\n+/)
    .map((part) => part.replace(/^[\-*•·‣]\s*/, "").trim())
    .filter(Boolean)
    .slice(0, 5);
}

export function planDeck(input: string, meta: DeckMeta): PlannedSlide[] {
  return parseSlides(input).map((slide) => {
    const archetype = inferArchetype(slide, meta);
    const claimTitle = normalizeTitle(slide.title || archetype.label);
    const governingMessage = makeClaimTitle(slide, meta, archetype.id);
    const sections = makeSections(slide, archetype.structure);
    const bodyLength = slide.bullets.join(" ").length;
    const density = bodyLength > 600 || slide.bullets.length > 6 ? "high" : bodyLength > 320 || slide.bullets.length > 4 ? "medium" : "low";
    return {
      ...slide,
      archetype,
      claimTitle,
      governingMessage,
      sections,
      density,
      rationale: `${matchedKeywords(slide, archetype.keywords).join(", ") || "입력 문맥"} 기준으로 ${archetype.label} 구조가 적합합니다.`
    };
  });
}

function inferArchetype(slide: RawSlide, meta: DeckMeta) {
  if (slide.forcedArchetypeId) {
    return archetypeRules.find((rule) => rule.id === slide.forcedArchetypeId) ?? archetypeRules[0];
  }

  const text = `${slide.title}\n${slide.body}\n${meta.purpose ?? ""}\n${meta.audience ?? ""}\n${meta.tone ?? ""}`.toLowerCase();
  const preferred = preferredByContext(meta, slide.index);
  let best = archetypeRules.find((rule) => rule.id === preferred) ?? archetypeRules[0];
  let bestScore = slide.index === 1 ? 2 : 0;

  for (const rule of archetypeRules) {
    let score = 0;
    for (const keyword of rule.keywords) {
      if (text.includes(keyword.toLowerCase())) score += keyword.length >= 5 ? 3 : 2;
    }
    if (rule.id === preferred) score += 8;
    if (rule.id.includes("summary") && slide.index === 1) score += 2;
    if (score > bestScore) {
      best = rule;
      bestScore = score;
    }
  }
  return best;
}

function preferredByContext(meta: DeckMeta, slideIndex: number): ArchetypeId {
  const templateChoice = getTemplateArchetype(meta, slideIndex);
  if (templateChoice) return templateChoice;

  const context = `${meta.purpose ?? ""} ${meta.documentType ?? ""} ${meta.audience ?? ""}`.toLowerCase();
  if (slideIndex === 1 && /(임원|executive|요약|보고)/i.test(context)) return "consulting-executive-summary";
  if (/(제안|proposal|입찰|tender)/i.test(context)) return slideIndex <= 2 ? "why-what-how-logic" : "proposal-scope-integrated";
  if (/(착수|kick|kickoff|수행|프로젝트)/i.test(context)) return slideIndex <= 2 ? "proposal-need-three-cards" : "method-chevron";
  if (/(최종|성과|대시보드|진척)/i.test(context)) return slideIndex <= 2 ? "dashboard-kpi-takeaway" : "evidence-to-action-strip";
  if (/(교육|워크숍|training)/i.test(context)) return "training-curriculum-agenda";
  return slideIndex === 1 ? "consulting-executive-summary" : "why-what-how-logic";
}

function matchedKeywords(slide: RawSlide, keywords: string[]): string[] {
  const text = `${slide.title}\n${slide.body}`.toLowerCase();
  return keywords.filter((keyword) => text.includes(keyword.toLowerCase())).slice(0, 4);
}

function makeClaimTitle(slide: RawSlide, meta: DeckMeta, id: ArchetypeId): string {
  const title = normalizeTitle(slide.title);
  if (isClaimLike(title)) return title;

  const first = cleanSentence(slide.bullets[0] ?? title);
  const client = meta.clientName || "고객사";

  const claims: Partial<Record<ArchetypeId, string>> = {
    "consulting-executive-summary": `${client} 의사결정에 필요한 핵심 메시지를 먼저 정리해야 합니다`,
    "proposal-scope-integrated": `${client} 과업은 범위, 방법, 산출물을 하나의 실행 체계로 고정해야 합니다`,
    "method-chevron": `${title}은 단계별 활동과 산출물을 함께 보여야 실행력이 생깁니다`,
    "data-request-tracker": `요청자료는 담당, 기한, 상태를 함께 관리해야 누락을 줄일 수 있습니다`,
    "schedule-gantt": `일정은 업무 기간보다 검토 마일스톤 중심으로 관리해야 합니다`,
    "traffic-light-scorecard": `상태 평가는 현재 수준과 보완 조치를 함께 보여야 의미가 있습니다`,
    "cycle-loop-pdca": `반복 업무는 실행, 점검, 개선, 기록이 끊기지 않아야 합니다`,
    "staircase-maturity-evolution": `성숙도 고도화는 단계별 진입 조건과 필요 역량을 명확히 해야 합니다`
  };

  return claims[id] ?? (first.length > 18 ? first : `${title}은 핵심 이슈와 실행 방향을 함께 제시해야 합니다`);
}

function isClaimLike(text: string) {
  return /(필요합니다|해야 합니다|중요합니다|가능합니다|줄일 수 있습니다|확보합니다|관리합니다|제시합니다)$/.test(text);
}

function normalizeTitle(text: string) {
  return text.replace(/[.。]$/, "").replace(/\s+/g, " ").trim();
}

function cleanSentence(text: string) {
  return text
    .replace(/^[^:]{1,16}:\s*/, "")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[.。]$/, "");
}

function makeSections(slide: RawSlide, structure: string[]): string[] {
  const bullets = slide.bullets.length ? slide.bullets : [slide.body || slide.title];
  return structure.map((label, idx) => {
    const source = bullets[idx] ?? bullets[idx % bullets.length] ?? "";
    return `${label}: ${stripRepeatedLabel(source, label)}`;
  });
}

function stripRepeatedLabel(value: string, label: string) {
  return value
    .replace(new RegExp(`^${escapeRegExp(label)}\\s*[:>\\-]\\s*`, "i"), "")
    .replace(/^[^:]{1,16}:\s*/, "")
    .trim();
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function fallbackSample(label: string, structure: string[]) {
  return {
    title: `${label} 샘플`,
    bullets: structure.slice(0, 5).map((item, idx) => `${item}: ${idx + 1}단계에서 확인할 핵심 내용과 산출물을 정리합니다.`)
  };
}
