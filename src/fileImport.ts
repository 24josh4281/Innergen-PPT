import JSZip from "jszip";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf.mjs";
import pdfWorkerUrl from "pdfjs-dist/legacy/build/pdf.worker.mjs?url";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerUrl;

export interface FileImportResult {
  text: string;
  warnings: string[];
  files: string[];
}

type TextContentItem = { str?: string };

export async function extractTextFromFiles(fileList: FileList | File[]): Promise<FileImportResult> {
  const files = Array.from(fileList);
  const results = await Promise.all(files.map(extractTextFromFile));
  return {
    text: results.map((result) => result.text).filter(Boolean).join("\n\n---\n\n"),
    warnings: results.flatMap((result) => result.warnings),
    files: results.map((result) => result.fileName)
  };
}

async function extractTextFromFile(file: File): Promise<FileImportResult & { fileName: string }> {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  try {
    if (["txt", "md", "csv", "tsv"].includes(extension)) {
      return { fileName: file.name, files: [file.name], warnings: [], text: await file.text() };
    }
    if (extension === "pptx") {
      return { fileName: file.name, files: [file.name], warnings: [], text: await extractPptx(file) };
    }
    if (extension === "docx") {
      return { fileName: file.name, files: [file.name], warnings: [], text: await extractDocx(file) };
    }
    if (extension === "pdf") {
      return await extractPdf(file);
    }
    return {
      fileName: file.name,
      files: [file.name],
      warnings: [`${file.name}: 아직 지원하지 않는 파일 형식입니다. txt, md, pdf, pptx, docx를 우선 지원합니다.`],
      text: ""
    };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { fileName: file.name, files: [file.name], warnings: [`${file.name}: 텍스트 추출 실패 - ${message}`], text: "" };
  }
}

async function extractPptx(file: File) {
  const zip = await JSZip.loadAsync(await file.arrayBuffer());
  const slideNames = Object.keys(zip.files)
    .filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name))
    .sort((a, b) => slideNumber(a) - slideNumber(b));

  const slides: string[] = [];
  for (const [idx, name] of slideNames.entries()) {
    const xml = await zip.file(name)?.async("string");
    if (!xml) continue;
    const texts = extractXmlText(xml, /<a:t>([\s\S]*?)<\/a:t>/g);
    const cleaned = compactTexts(texts);
    const title = cleaned[0] || `원문 슬라이드 ${idx + 1}`;
    const bullets = cleaned.slice(1, 9).map((item) => `- ${item}`);
    slides.push([`슬라이드 ${idx + 1}: ${title}`, ...bullets].join("\n"));
  }

  return slides.join("\n\n---\n");
}

async function extractDocx(file: File) {
  const zip = await JSZip.loadAsync(await file.arrayBuffer());
  const xml = await zip.file("word/document.xml")?.async("string");
  if (!xml) return "";
  const paragraphs = xml
    .split(/<\/w:p>/)
    .map((paragraph) => compactTexts(extractXmlText(paragraph, /<w:t[^>]*>([\s\S]*?)<\/w:t>/g)).join(""))
    .filter(Boolean);
  return paragraphs.map((paragraph) => `- ${paragraph}`).join("\n");
}

async function extractPdf(file: File): Promise<FileImportResult & { fileName: string }> {
  const data = await file.arrayBuffer();
  const doc = await pdfjsLib.getDocument({ data }).promise;
  const maxPages = Math.min(doc.numPages, 50);
  const pages: string[] = [];

  for (let pageNo = 1; pageNo <= maxPages; pageNo += 1) {
    const page = await doc.getPage(pageNo);
    const content = await page.getTextContent();
    const text = compactTexts((content.items as TextContentItem[]).map((item) => item.str ?? ""), false).join(" ");
    if (!text) continue;
    const title = firstSentence(text, `원문 ${pageNo}페이지`);
    const bullets = sentenceChunks(text)
      .filter((item) => item !== title)
      .slice(0, 7)
      .map((item) => `- ${item}`);
    pages.push([`슬라이드 ${pageNo}: ${title}`, ...bullets].join("\n"));
  }

  const warnings = doc.numPages > maxPages ? [`${file.name}: PDF가 ${doc.numPages}페이지라서 앞 ${maxPages}페이지만 불러왔습니다.`] : [];
  return { fileName: file.name, files: [file.name], warnings, text: pages.join("\n\n---\n") };
}

function extractXmlText(xml: string, pattern: RegExp) {
  return [...xml.matchAll(pattern)].map((match) => decodeXml(match[1] ?? ""));
}

function compactTexts(values: string[], dedupe = true) {
  const seen = new Set<string>();
  return values
    .map((value) => value.replace(/\s+/g, " ").trim())
    .filter((value) => value.length > 1)
    .filter((value) => {
      if (!dedupe) return true;
      if (seen.has(value)) return false;
      seen.add(value);
      return true;
    });
}

function sentenceChunks(text: string) {
  return text
    .split(/(?<=[.!?。])\s+|(?<=다\.)\s+|(?<=요\.)\s+/)
    .map((item) => item.trim())
    .filter((item) => item.length >= 8);
}

function firstSentence(text: string, fallback: string) {
  const first = sentenceChunks(text)[0] ?? text.slice(0, 42);
  return first.length > 64 ? `${first.slice(0, 63)}…` : first || fallback;
}

function decodeXml(value: string) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'");
}

function slideNumber(name: string) {
  return Number(name.match(/slide(\d+)\.xml/)?.[1] ?? 0);
}
