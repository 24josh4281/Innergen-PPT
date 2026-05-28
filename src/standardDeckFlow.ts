import standardFlowData from "../docs/standard-deck-flows.json";
import type { ArchetypeId } from "./types";

export interface StandardDeckFlowProfile {
  id: string;
  label: string;
  businessType: string;
  meetingType: string;
  sourceTopNProfileId: string;
  recommendedSlideCount: number;
  rhythm: string;
  standardSequence: ArchetypeId[];
  stageRoles: string[];
  generationRules: string[];
  qaValidation?: {
    samplePptx: string;
    sampleQaReport: string;
    renderQaReport: string;
    lastValidatedAt: string;
    status: string;
    requiredGates: string[];
    flowRuleUpdates: string[];
  };
  userInputValidation?: {
    samplePptx: string;
    manifest: string;
    renderQaReports: string[];
    lastValidatedAt: string;
    status: string;
    observedImprovements: string[];
  };
}

const profiles = standardFlowData.profiles as StandardDeckFlowProfile[];

export function findStandardDeckFlow(
  businessType: string | undefined,
  meetingType: string | undefined
): StandardDeckFlowProfile | undefined {
  if (!businessType || !meetingType) return undefined;
  return profiles.find((profile) => profile.businessType === businessType && profile.meetingType === meetingType);
}

export function getStandardDeckFlowArchetype(profile: StandardDeckFlowProfile | undefined, slideIndex: number): ArchetypeId | undefined {
  if (!profile?.standardSequence.length) return undefined;
  const sequence = profile.standardSequence.filter((id) => id !== "cover-kickoff" && id !== "contents-isometric");
  if (slideIndex <= sequence.length) return sequence[slideIndex - 1];
  const repeatableBody = sequence;
  if (!repeatableBody.length) return sequence.at(-1);
  return repeatableBody[(slideIndex - sequence.length - 1) % repeatableBody.length];
}

export function summarizeStandardDeckFlowForPrompt(profile: StandardDeckFlowProfile | undefined): string[] {
  if (!profile) return ["표준 deck flow 매칭 없음: 승인 Top N 구조와 기본 구조 DB를 사용합니다."];
  return [
    `표준 Deck Flow: ${profile.label}`,
    `권장 장수: ${profile.recommendedSlideCount}장`,
    `고정 rhythm: ${profile.rhythm}`,
    `표준 구조 순서: ${profile.standardSequence.join(" -> ")}`,
    "슬라이드 역할:",
    ...profile.stageRoles.map((role, index) => `- ${index + 1}. ${role}`),
    "생성 규칙:",
    ...profile.generationRules.map((rule) => `- ${rule}`),
    ...(profile.qaValidation
      ? [
          "검증된 샘플 QA 기준:",
          `- 샘플: ${profile.qaValidation.samplePptx}`,
          `- 최종 검증일: ${profile.qaValidation.lastValidatedAt} / 상태: ${profile.qaValidation.status}`,
          ...profile.qaValidation.requiredGates.map((gate) => `- ${gate}`)
        ]
      : []),
    ...(profile.userInputValidation
      ? [
          "실제 사용자 입력 샘플 검증 결과:",
          `- 샘플: ${profile.userInputValidation.samplePptx}`,
          `- 최종 검증일: ${profile.userInputValidation.lastValidatedAt} / 상태: ${profile.userInputValidation.status}`,
          ...profile.userInputValidation.observedImprovements.map((item) => `- ${item}`)
        ]
      : [])
  ];
}

export function describeStandardDeckFlow(profile: StandardDeckFlowProfile | undefined): string[] {
  if (!profile) return [];
  return [
    profile.label,
    `${profile.recommendedSlideCount} slides recommended`,
    profile.standardSequence.join(" -> ")
  ];
}
