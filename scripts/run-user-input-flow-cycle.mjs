import { execFileSync } from "node:child_process";
import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { join, relative, resolve } from "node:path";

const root = resolve(".");
const sampleId = process.argv[2] ?? "cdp-disclosure-proposal";
const outRoot = join(root, "docs", "generated", "user-input-samples", sampleId);
const generatedFlowDir = join(outRoot, "matched-flow-generation");
const selectedFlowId = "disclosure-proposal-standard-flow";

const sampleInput = {
  sampleId,
  businessType: "disclosure",
  meetingType: "proposal",
  clientName: "Sample Client",
  projectTitle: "CDP and Climate Disclosure Response Proposal",
  documentType: "Proposal",
  purpose: "Win a consulting proposal by showing evidence-driven disclosure response capability",
  contentSignals: ["CDP", "Scope 3", "climate disclosure", "evidence pack", "response strategy"],
  requiredQaLoop: "flow auto-match -> PPT generation -> render QA pass 1 -> render QA pass 2 -> flow rule update"
};

await main();

async function main() {
  await mkdir(outRoot, { recursive: true });
  await writeFile(join(outRoot, "input.json"), JSON.stringify(sampleInput, null, 2), "utf8");

  const flowDataPath = join(root, "docs", "standard-deck-flows.json");
  const flowData = JSON.parse(await readFile(flowDataPath, "utf8"));
  const matchedFlow = flowData.profiles.find(
    (profile) => profile.businessType === sampleInput.businessType && profile.meetingType === sampleInput.meetingType
  );
  if (!matchedFlow) {
    throw new Error(`No standard flow matched ${sampleInput.businessType}/${sampleInput.meetingType}`);
  }
  if (matchedFlow.id !== selectedFlowId) {
    throw new Error(`Unexpected flow match: ${matchedFlow.id}`);
  }

  execFileSync(process.execPath, [join(root, "scripts", "build-standard-flow-sample-decks.mjs"), generatedFlowDir], {
    cwd: root,
    stdio: "inherit"
  });

  const sourcePptx = join(generatedFlowDir, "disclosure-proposal.pptx");
  const sourceQa = join(generatedFlowDir, "disclosure-proposal.qa.json");
  const targetPptx = join(outRoot, "cdp_disclosure_proposal_innergen.pptx");
  const targetQa = join(outRoot, "cdp_disclosure_proposal_innergen.qa.json");
  await copyFile(sourcePptx, targetPptx);
  await copyFile(sourceQa, targetQa);

  const renderReports = [];
  for (let pass = 1; pass <= 2; pass += 1) {
    const renderDir = join(outRoot, `render-qa-pass-${pass}`);
    execFileSync(
      "powershell",
      [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        join(root, "scripts", "render-pptx-qa.ps1"),
        "-InputPptx",
        targetPptx,
        "-OutputDir",
        renderDir
      ],
      { cwd: root, stdio: "inherit" }
    );
    renderReports.push(join(renderDir, "qa-report.json"));
  }

  const qaReports = [];
  for (const reportPath of renderReports) {
    const raw = await readFile(reportPath, "utf8");
    qaReports.push(JSON.parse(raw.replace(/^\uFEFF/, "")));
  }

  const allPass = qaReports.every((report) => report.qa?.status === "pass" && report.imageRendered);
  const latestQa = qaReports.at(-1)?.qa;
  const manifest = {
    generatedAt: new Date().toISOString(),
    sampleInput,
    matchedFlowId: matchedFlow.id,
    matchedFlowLabel: matchedFlow.label,
    pptx: toRepoPath(targetPptx),
    qaReport: toRepoPath(targetQa),
    renderQaReports: renderReports.map(toRepoPath),
    finalStatus: allPass ? "pass" : "fail",
    latestQa,
    issueDetailSchema: [
      "type",
      "severity",
      "slide",
      "objectId",
      "objectName",
      "x/y/w/h",
      "relatedObjectId",
      "relatedObjectName",
      "relatedX/relatedY/relatedW/relatedH",
      "textPreview",
      "reason",
      "remediation"
    ]
  };
  const manifestPath = join(outRoot, "cycle-manifest.json");
  await writeFile(manifestPath, JSON.stringify(manifest, null, 2), "utf8");

  matchedFlow.userInputValidation = {
    samplePptx: toRepoPath(targetPptx),
    manifest: toRepoPath(manifestPath),
    renderQaReports: renderReports.map(toRepoPath),
    lastValidatedAt: manifest.generatedAt,
    status: allPass ? "pass" : "fail",
    observedImprovements: [
      "disclosure/proposal input was automatically matched to disclosure-proposal-standard-flow.",
      "Render QA was repeated twice and must pass both imageRendered and QA gates.",
      "QA report now records issues[] with slide number, object id/name, coordinates, related object, reason, and remediation.",
      "If issues[] is non-empty, the generator must adjust layout before treating the deck as final."
    ]
  };

  matchedFlow.generationRules = unique([
    ...matchedFlow.generationRules,
    "QA report issues[] must be inspected after render QA. Each issue includes slide, object name, coordinates, reason, and remediation.",
    "If issues[] is non-empty, do not accept the output as final even when a screenshot looks acceptable.",
    "For proposal decks, avoid repeated card-only layouts by alternating executive summary, taxonomy map, workplan, scope table, workflow, and action strip."
  ]);

  await writeFile(flowDataPath, JSON.stringify(flowData, null, 2), "utf8");

  console.log(JSON.stringify({
    sampleId,
    matchedFlowId: matchedFlow.id,
    pptx: targetPptx,
    manifestPath,
    renderQaReports: renderReports,
    finalStatus: manifest.finalStatus,
    latestQa
  }, null, 2));
}

function toRepoPath(filePath) {
  return relative(root, filePath).replaceAll("\\", "/");
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}
