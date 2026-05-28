import topNData from "../docs/reference-structure-topn.json";
import type { ArchetypeId } from "./types";

export interface ReferenceTopNArchetype {
  id: ArchetypeId;
  count: number;
  fileSpread: number;
  averageConfidence: number;
  score: number;
  topTags: string[];
  examples: { fileId: string; slideNo: number; title: string }[];
}

export interface ReferenceTopNProfile {
  id: string;
  label: string;
  businessType: string;
  meetingType: string;
  totalFiles: number;
  totalSlides: number;
  sourceFileIds: string[];
  categoryPaths: string[];
  sourceRootTypes: string[];
  representativeSequence: ArchetypeId[];
  topArchetypes: ReferenceTopNArchetype[];
  generationRules: string[];
}

const profiles = topNData.profiles as ReferenceTopNProfile[];

export function findReferenceTopNProfile(
  businessType: string | undefined,
  meetingType: string | undefined
): ReferenceTopNProfile | undefined {
  if (!businessType || !meetingType) return undefined;
  return profiles.find((profile) => profile.businessType === businessType && profile.meetingType === meetingType);
}

export function getReferenceTopNArchetype(profile: ReferenceTopNProfile | undefined, slideIndex: number): ArchetypeId | undefined {
  if (!profile?.representativeSequence.length) return undefined;
  const sequence = profile.representativeSequence.filter((id) => id !== "cover-kickoff" && id !== "contents-isometric");
  if (slideIndex <= sequence.length) return sequence[slideIndex - 1];
  const repeatableBody = sequence;
  if (!repeatableBody.length) return sequence.at(-1);
  return repeatableBody[(slideIndex - sequence.length - 1) % repeatableBody.length];
}

export function summarizeReferenceTopNProfileForPrompt(profile: ReferenceTopNProfile | undefined): string[] {
  if (!profile) return ["승인 샘플 Top N 매칭 없음: 기본 구조 DB를 사용합니다."];
  return [
    `승인 샘플 Top N: ${profile.label}`,
    `승인 파일/슬라이드: ${profile.totalFiles}개 파일 / ${profile.totalSlides}개 슬라이드`,
    `대표 구조 흐름: ${profile.representativeSequence.join(" -> ")}`,
    `주요 구조 Top 5: ${profile.topArchetypes.slice(0, 5).map((item) => `${item.id}(${item.count})`).join(", ")}`,
    `참조 소스 그룹: ${profile.sourceRootTypes.join(", ") || "approved references"}`,
    "로고 정책: INNerGEN 외 기업/컨설팅사/고객사 로고와 브랜드 마크는 복제하지 않습니다.",
    ...profile.generationRules.map((rule) => `- ${rule}`)
  ];
}

export function describeReferenceTopNProfile(profile: ReferenceTopNProfile | undefined): string[] {
  if (!profile) return [];
  return [
    `${profile.label}`,
    `${profile.totalFiles} files / ${profile.totalSlides} slides`,
    profile.representativeSequence.join(" -> ")
  ];
}
