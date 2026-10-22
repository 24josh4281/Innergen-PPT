/** Deterministic card stacks. Coordinates are inches, font sizes are points.
 * Plan everything before drawing; overflow never truncates text or shrinks fonts.
 */
export interface CardItem {
  id: string;
  text?: string;
  size?: number;
  height?: number; // fixed native separator/icon, not a text frame
  gapAfter?: number;
  bold?: boolean;
  color?: string;
  align?: "left" | "center" | "right";
}
export interface CardFrame { x: number; y: number; w: number; h: number }
export interface CardPlacement extends CardItem, CardFrame { lines: string[] }

function advance(char: string): number {
  if (/\p{Mark}/u.test(char)) return 0;
  if (/\s/u.test(char)) return 0.35;
  if (/[\u2e80-\uffef]|\p{Extended_Pictographic}/u.test(char)) return 1;
  if (/[MWmw@#%]/u.test(char)) return 0.95;
  return 0.65;
}
export function wrapCardText(text: string, width: number, size: number): string[] {
  if (!Number.isFinite(width) || width <= 0 || !Number.isFinite(size) || size <= 0) throw new Error("카드 텍스트 폭과 글꼴 크기 확인 필요");
  const capacity = width * 72 / (size * 1.08);
  const measure = (s: string) => [...s].reduce((sum, c) => sum + advance(c), 0);
  const lines: string[] = [];
  for (const paragraph of text.replace(/\r\n?/g, "\n").split("\n")) {
    let line = "";
    for (const word of paragraph.trim().split(/\s+/).filter(Boolean)) {
      if (measure(word) > capacity) throw new Error(`카드 단어 폭 초과: ${word}. 카드 폭 확대 또는 명시적 줄바꿈 필요`);
      const next = line ? `${line} ${word}` : word;
      if (line && measure(next) > capacity) { lines.push(line); line = word; }
      else line = next;
    }
    lines.push(line); // preserve explicit and blank lines
  }
  return lines;
}
export function layoutCard(frame: CardFrame, items: CardItem[], padding = 0.18, gap = 0.12): CardPlacement[] {
  if (![frame.x, frame.y, frame.w, frame.h, padding, gap].every(Number.isFinite) || frame.w <= 2 * padding || frame.h <= 2 * padding || padding < 0 || gap < 0) throw new Error("카드 컨테이너 크기·최소 여백 확인 필요");
  if (new Set(items.map(i => i.id)).size !== items.length) throw new Error("카드 개체 ID 중복");
  const visible = items.filter(i => i.text?.trim() || i.height !== undefined);
  const measured = visible.map(item => {
    const size = item.size ?? 12;
    if (size < 11 || !Number.isFinite(size)) throw new Error(`${item.id}: 최소 11pt 필요`);
    const lines = item.text?.trim() ? wrapCardText(item.text, frame.w - padding * 2, size) : [];
    const h = lines.length ? lines.length * size * 1.5 / 72 : item.height!;
    if (!Number.isFinite(h) || h < 0 || !Number.isFinite(item.gapAfter ?? gap) || (item.gapAfter ?? gap) < 0) throw new Error(`${item.id}: 높이·간격 확인 필요`);
    return { ...item, lines, h };
  });
  const total = measured.reduce((sum, i, idx) => sum + i.h + (idx < measured.length - 1 ? i.gapAfter ?? gap : 0), 0);
  if (total > frame.h - 2 * padding + 1e-9) throw new Error(`카드 콘텐츠 높이 초과 (${total.toFixed(2)}in / ${(frame.h - 2 * padding).toFixed(2)}in): ${items.map(i => i.id).join(", ")}. 카드 확대 또는 내용 분리 필요`);
  let y = frame.y + (frame.h - total) / 2;
  return measured.map(item => {
    const placed = { ...item, x: frame.x + padding, y, w: frame.w - padding * 2 };
    y += item.h + (item.gapAfter ?? gap);
    return placed;
  });
}
