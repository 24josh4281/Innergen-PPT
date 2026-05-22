import { createReadStream } from "node:fs";
import { mkdir, stat, writeFile } from "node:fs/promises";
import type { IncomingMessage, ServerResponse } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv, type Plugin } from "vite";
import { buildPptxBlob } from "./src/ppt";
import type { DeckMeta, PlannedSlide } from "./src/types";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const exportDir = path.join(rootDir, "docs", "generated", "user-exports");

function innergenPptExportPlugin(env: Record<string, string>): Plugin {
  return {
    name: "innergen-ppt-export",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = new URL(req.url ?? "/", "http://127.0.0.1");

        if (req.method === "POST" && url.pathname === "/api/export-pptx") {
          try {
            const payload = JSON.parse(await readRequestBody(req)) as { meta?: DeckMeta; slides?: PlannedSlide[] };
            if (!payload.meta || !Array.isArray(payload.slides) || !payload.slides.length) {
              sendJson(res, 400, { ok: false, error: "Storyboard 데이터가 없습니다." });
              return;
            }

            await mkdir(exportDir, { recursive: true });
            const { blob, fileName } = await buildPptxBlob(payload.meta, payload.slides);
            const buffer = Buffer.from(await blob.arrayBuffer());
            if (buffer.length < 10_000) {
              sendJson(res, 500, { ok: false, error: "PPTX 파일 크기가 비정상적으로 작습니다." });
              return;
            }

            const savedName = `${timestamp()}_${safeFileName(fileName)}`;
            const filePath = path.join(exportDir, savedName);
            await writeFile(filePath, buffer);

            sendJson(res, 200, {
              ok: true,
              fileName,
              savedName,
              bytes: buffer.length,
              localPath: filePath,
              url: `/api/export-pptx/${encodeURIComponent(savedName)}`
            });
          } catch (error) {
            sendJson(res, 500, { ok: false, error: error instanceof Error ? error.message : String(error) });
          }
          return;
        }

        if (req.method === "POST" && url.pathname === "/api/gpt-ppt") {
          try {
            const payload = JSON.parse(await readRequestBody(req)) as { prompt?: string; mode?: string };
            const prompt = payload.prompt?.trim() ?? "";
            if (prompt.length < 50) {
              sendJson(res, 400, { ok: false, error: "GPT에 보낼 프롬프트가 너무 짧습니다. Storyboard를 먼저 생성해 주세요." });
              return;
            }

            const gptApiEnabled = (env.ENABLE_GPT_API || process.env.ENABLE_GPT_API || "").toLowerCase() === "true";
            if (!gptApiEnabled) {
              sendJson(res, 503, {
                ok: false,
                error: "GPT API 직접 연결은 현재 보류 상태입니다. 앱에서 생성한 프롬프트를 복사해 ChatGPT 채팅창에서 사용해 주세요."
              });
              return;
            }

            const apiKey = env.OPENAI_API_KEY || process.env.OPENAI_API_KEY;
            if (!apiKey) {
              sendJson(res, 400, {
                ok: false,
                error: "OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일 또는 PowerShell 환경변수에 API 키를 설정한 뒤 dev server를 재시작해 주세요."
              });
              return;
            }

            const model = env.OPENAI_MODEL || process.env.OPENAI_MODEL || "gpt-5";
            const startedAt = Date.now();
            const openAiResponse = await fetch("https://api.openai.com/v1/responses", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${apiKey}`
              },
              body: JSON.stringify({
                model,
                instructions: buildGptInstructions(payload.mode),
                input: prompt,
                max_output_tokens: 3500
              })
            });

            const responseText = await openAiResponse.text();
            const parsed = safeJsonParse(responseText);
            if (!openAiResponse.ok) {
              sendJson(res, openAiResponse.status, {
                ok: false,
                error: extractOpenAiError(parsed) || responseText || "OpenAI API 호출에 실패했습니다.",
                requestId: openAiResponse.headers.get("x-request-id")
              });
              return;
            }

            const outputText = extractOpenAiOutputText(parsed);
            if (!outputText) {
              sendJson(res, 502, {
                ok: false,
                error: "OpenAI 응답에서 텍스트 결과를 찾지 못했습니다.",
                requestId: openAiResponse.headers.get("x-request-id")
              });
              return;
            }

            sendJson(res, 200, {
              ok: true,
              model,
              mode: payload.mode ?? "ppt-generation",
              outputText,
              elapsedMs: Date.now() - startedAt,
              requestId: openAiResponse.headers.get("x-request-id")
            });
          } catch (error) {
            sendJson(res, 500, { ok: false, error: error instanceof Error ? error.message : String(error) });
          }
          return;
        }

        if (req.method === "GET" && url.pathname.startsWith("/api/export-pptx/")) {
          const savedName = decodeURIComponent(url.pathname.replace("/api/export-pptx/", ""));
          const filePath = path.resolve(exportDir, savedName);
          if (!filePath.startsWith(exportDir) || path.extname(filePath).toLowerCase() !== ".pptx") {
            sendJson(res, 400, { ok: false, error: "잘못된 파일 요청입니다." });
            return;
          }

          try {
            const fileStat = await stat(filePath);
            res.statusCode = 200;
            res.setHeader("Content-Type", "application/vnd.openxmlformats-officedocument.presentationml.presentation");
            res.setHeader("Content-Length", String(fileStat.size));
            res.setHeader("Content-Disposition", `attachment; filename*=UTF-8''${encodeURIComponent(savedName)}`);
            createReadStream(filePath).pipe(res);
          } catch {
            sendJson(res, 404, { ok: false, error: "생성된 PPTX 파일을 찾을 수 없습니다." });
          }
          return;
        }

        next();
      });
    }
  };
}

function buildGptInstructions(mode?: string) {
  const action = mode === "qa-review" ? "review and improve the PPT storyboard" : "generate a PPT-ready consulting response";
  return [
    `You ${action} for ESG and climate consulting decks.`,
    "Follow the user's INNerGEN brand, layout, typography, and QA rules strictly.",
    "Do not invent facts, numbers, dates, sources, or regulatory obligations.",
    "When uncertain, flag the item as an assumption or required source check.",
    "Return practical output that can be copied into the deck generation workflow."
  ].join(" ");
}

function safeJsonParse(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function extractOpenAiError(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "";
  const error = (payload as { error?: { message?: string } }).error;
  return error?.message ?? "";
}

function extractOpenAiOutputText(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "";
  const direct = (payload as { output_text?: unknown }).output_text;
  if (typeof direct === "string" && direct.trim()) return direct.trim();

  const output = (payload as { output?: unknown }).output;
  if (!Array.isArray(output)) return "";

  const chunks: string[] = [];
  for (const item of output) {
    if (!item || typeof item !== "object") continue;
    const content = (item as { content?: unknown }).content;
    if (!Array.isArray(content)) continue;
    for (const part of content) {
      if (!part || typeof part !== "object") continue;
      const text = (part as { text?: unknown }).text;
      if (typeof text === "string" && text.trim()) chunks.push(text.trim());
    }
  }

  return chunks.join("\n\n").trim();
}

function readRequestBody(req: IncomingMessage) {
  return new Promise<string>((resolve, reject) => {
    let body = "";
    req.setEncoding("utf8");
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 25_000_000) {
        reject(new Error("요청 데이터가 너무 큽니다."));
        req.destroy();
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function sendJson(res: ServerResponse, statusCode: number, payload: unknown) {
  res.statusCode = statusCode;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.end(JSON.stringify(payload));
}

function safeFileName(name: string) {
  return name.replace(/[\\/:*?"<>|]/g, "_").replace(/\s+/g, "_");
}

function timestamp() {
  const now = new Date();
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, "");
  return {
    base: "./",
    plugins: [innergenPptExportPlugin(env)],
    server: {
      host: "127.0.0.1",
      port: 5177
    }
  };
});
