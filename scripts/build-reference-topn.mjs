import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..");
const sourceIndexPath = argValue("--source", join(repoRoot, "docs", "reference-source-index.json"));
const outputPath = argValue("--output", join(repoRoot, "docs", "reference-structure-topn.json"));
const topN = Number(argValue("--top", "10"));
const sequenceLength = Number(argValue("--sequence", "12"));

const index = JSON.parse(await readFile(sourceIndexPath, "utf8"));
const approvedFiles = index.files.filter((file) => file.status === "approved-sample" && file.slides?.length);
const groups = groupApprovedSlides(approvedFiles);
const profiles = [...groups.entries()]
  .map(([key, group]) => buildProfile(key, group))
  .sort((a, b) => a.id.localeCompare(b.id));

const output = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  sourceIndex: sourceIndexPath,
  sourceSummary: index.summary,
  policy: {
    usesApprovedSamplesOnly: true,
    topN,
    sequenceLength,
    excludesNonInnergenLogos: true,
    allowedBrandIdentity: "INNerGEN only",
    learnsFromReferences: index.policy?.learnsFromReferences ?? [],
    doesNotLearnFromReferences: index.policy?.doesNotLearnFromReferences ?? []
  },
  profiles
};

await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, JSON.stringify(output, null, 2), "utf8");
console.log(`Wrote ${outputPath}`);
console.log(JSON.stringify({
  profiles: profiles.length,
  approvedFiles: approvedFiles.length,
  approvedSlides: approvedFiles.reduce((sum, file) => sum + file.slides.length, 0),
  pairs: profiles.map((profile) => `${profile.businessType}/${profile.meetingType}:${profile.totalSlides}`)
}, null, 2));

function argValue(flag, fallback) {
  const index = process.argv.indexOf(flag);
  if (index === -1 || index + 1 >= process.argv.length) return fallback;
  return process.argv[index + 1];
}

function groupApprovedSlides(files) {
  const groups = new Map();
  for (const file of files) {
    const key = `${file.businessType}/${file.meetingType}`;
    if (!groups.has(key)) {
      groups.set(key, {
        businessType: file.businessType,
        meetingType: file.meetingType,
        files: [],
        slides: []
      });
    }
    const group = groups.get(key);
    group.files.push(file);
    for (const slide of file.slides) {
      group.slides.push({ ...slide, fileId: file.id, sourceRootType: file.sourceRootType, categoryPath: file.categoryPath });
    }
  }
  return groups;
}

function buildProfile(key, group) {
  const [businessType, meetingType] = key.split("/");
  const stats = new Map();
  for (const slide of group.slides) {
    const id = slide.inferredArchetype;
    if (!stats.has(id)) {
      stats.set(id, {
        id,
        count: 0,
        confidenceSum: 0,
        files: new Set(),
        tags: new Map(),
        examples: []
      });
    }
    const row = stats.get(id);
    row.count += 1;
    row.confidenceSum += Number(slide.confidence ?? 0.5);
    row.files.add(slide.fileId);
    for (const tag of slide.tags ?? []) row.tags.set(tag, (row.tags.get(tag) ?? 0) + 1);
    if (row.examples.length < 5) {
      row.examples.push({
        fileId: slide.fileId,
        slideNo: slide.slideNo,
        title: slide.title
      });
    }
  }

  const topArchetypes = [...stats.values()]
    .map((row) => {
      const averageConfidence = round(row.confidenceSum / Math.max(1, row.count));
      const fileSpread = row.files.size;
      const score = round(row.count * averageConfidence + fileSpread * 2);
      return {
        id: row.id,
        count: row.count,
        fileSpread,
        averageConfidence,
        score,
        topTags: [...row.tags.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6).map(([tag]) => tag),
        examples: row.examples
      };
    })
    .sort((a, b) => b.score - a.score || b.count - a.count || a.id.localeCompare(b.id))
    .slice(0, topN);

  const topSet = new Set(topArchetypes.map((item) => item.id));
  const representativeSequence = buildRepresentativeSequence(group, topSet, topArchetypes);
  const sourceFileIds = [...new Set(group.files.map((file) => file.id))].sort();
  const categoryPaths = [...new Set(group.files.map((file) => file.categoryPath).filter(Boolean))].sort();
  const sourceRootTypes = [...new Set(group.files.map((file) => file.sourceRootType).filter(Boolean))].sort();

  return {
    id: `${businessType}-${meetingType}-approved-topn`,
    label: `${labelBusiness(businessType)} / ${labelMeeting(meetingType)} 대표 구조 Top ${topN}`,
    businessType,
    meetingType,
    totalFiles: group.files.length,
    totalSlides: group.slides.length,
    sourceFileIds,
    categoryPaths,
    sourceRootTypes,
    representativeSequence,
    topArchetypes,
    generationRules: [
      "approved-sample 구조를 우선 적용합니다.",
      "INNerGEN 외 기업/컨설팅사/고객사 로고와 브랜드 마크는 복제하지 않습니다.",
      "동일한 카드형 구조가 반복되면 Top N 내 표, 프로세스, 산정식, 일정표, scorecard 구조로 교차 적용합니다.",
      "사용자 원문 수치와 의미는 보존하고, 레퍼런스에서는 논리 구조와 정보 배치 방식만 차용합니다.",
      "표 장표는 approved-sample의 compact rhythm을 따릅니다: 본문 12~14pt, 행 높이 0.55~0.95in, 내부 padding 최소화, category/evidence/judgment 열 폭 균형.",
      "번호형 행은 고정 번호 칼럼, 세로 중앙 정렬, 본문 wrap을 고려한 row height를 사용합니다.",
      "칩, 라벨, 배지, 요약바는 도형과 텍스트박스의 y/h를 맞춰 기준선이 흔들리지 않게 합니다.",
      "한 장 안에서 내용량이 부족하면 박스만 키우지 말고 judgment, evidence, implication, owner/status 중 하나를 추가합니다."
    ]
  };
}

function buildRepresentativeSequence(group, topSet, topArchetypes) {
  const sequence = [];
  const seen = new Set();
  const sortedFiles = [...group.files].sort((a, b) => sourcePriority(b) - sourcePriority(a) || b.slides.length - a.slides.length || a.id.localeCompare(b.id));
  if (topSet.has("cover-kickoff")) {
    sequence.push("cover-kickoff");
    seen.add("cover-kickoff");
  }
  if (topSet.has("contents-isometric")) {
    sequence.push("contents-isometric");
    seen.add("contents-isometric");
  }
  for (const file of sortedFiles) {
    for (const slide of file.slides) {
      const id = slide.inferredArchetype;
      if (!topSet.has(id)) continue;
      if (seen.has(id)) continue;
      if (sequence.at(-1) === id) continue;
      sequence.push(id);
      seen.add(id);
      if (sequence.length >= sequenceLength) return sequence;
    }
  }
  for (const item of topArchetypes) {
    if (sequence.length >= sequenceLength) break;
    if (!seen.has(item.id)) {
      sequence.push(item.id);
      seen.add(item.id);
    }
  }
  return sequence.length ? sequence : ["consulting-executive-summary", "why-what-how-logic", "evidence-to-action-strip"];
}

function sourcePriority(file) {
  if (file.sourceRootType === "business-report-reference") return 3;
  if (file.sourceRootType === "conversation-source") return 2;
  if (file.sourceRootType === "structure-benchmark") return 1;
  return 0;
}

function labelBusiness(value) {
  const labels = {
    reduction: "감축사업",
    regulatory: "규제대응/인벤토리",
    disclosure: "CDP·기후공시",
    benchmark: "벤치마크",
    "design-template": "디자인 템플릿"
  };
  return labels[value] ?? value;
}

function labelMeeting(value) {
  const labels = {
    proposal: "제안서",
    kickoff: "착수보고",
    interim: "중간보고",
    final: "최종보고",
    review: "검토회의/방법론 보고",
    benchmark: "구조 벤치마크",
    training: "교육/세미나",
    "design-template": "디자인 템플릿"
  };
  return labels[value] ?? value;
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}
