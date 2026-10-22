#!/usr/bin/env python3
"""
PPT Master - INNerGEN table of contents builder (v33)

Builds the TOC page from the deck itself instead of retyping it: chapters come
from the page titles ("Ⅱ. 장명 – 절명" / "Ⅱ. 장명 / 절명"), the footer chapter
label of a drawn page, or a `chapter` field in a JSON outline. Each chapter gets
its roman numeral, its section names as the description and its page range,
and the family's 02b_toc_pages_N template (N = 3–6) is filled. `--dividers`
also writes the re-inserted TOC per chapter with the current chapter
highlighted (content-principles-v32.md §3.3, reports with 16+ body pages).

Since 2026-10-22 the TOC templates hold one native table
(data-pptx-native="table"): tokens are filled in its metadata JSON as well as
in the fallback, rows beyond the chapter count are dropped and the remaining
rows share the zone, the current chapter is highlighted in the table cells,
and the SVG fallback is redrawn from the metadata (`table_fallback`). Export
with `svg_to_pptx.py --native-objects` to get a PowerPoint table.

Usage:
    python3 scripts/toc_builder.py chapters <project | outline.md | outline.json>
    python3 scripts/toc_builder.py build <project | outline> --family <family> -o <svg_output/02_목차.svg>
        [--lead "핵심 메시지"] [--title 목차] [--page 2] [--dividers <dir>] [--start-page N]

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional
from xml.sax.saxutils import escape

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from report_diagrams import FAMILIES, DiagramError, _copy_chrome_images, find_template  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"
ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"
ASCII_ROMAN = {"I": "Ⅰ", "II": "Ⅱ", "III": "Ⅲ", "IV": "Ⅳ", "V": "Ⅴ", "VI": "Ⅵ", "VII": "Ⅶ", "VIII": "Ⅷ", "IX": "Ⅸ", "X": "Ⅹ"}
CRUMB = re.compile(r"^\s*([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[IVX]{1,4}|\d{1,2})\s*[.)]\s*([^–\-|/:]+?)\s*(?:[–\-|/:]\s*(.+))?$")
SKIP_ROLES = {"cover", "toc", "ending", "backup", "divider"}
NAME_MAX = 20
DESC_MAX = 44


class TocError(Exception):
    pass


def _page_rows(src: Path) -> list[dict[str, Any]]:
    """[{page, role, title, chapter}] from a project, a JSON outline or a Markdown outline."""
    import innergen_story_check as story
    rules = json.loads(story.RULES_PATH.read_text(encoding="utf-8"))
    hints: dict[int, str] = {}
    if src.is_dir():
        pages = story.pages_from_project(src, rules)
        import innergen_qaqc as qaqc
        folder = src / "svg_output" if any((src / "svg_output").glob("*.svg")) else src / "svg_final"
        for i, f in enumerate(sorted(folder.glob("*.svg")), 1):
            page = qaqc.Page(f, i)
            label = page.footer_label["text"] if page.footer_label else _footer_fallback(f, page.texts)
            if label:
                hints[i] = label
    else:
        pages = story.pages_from_outline(src)
        if src.suffix.lower() == ".json":
            data = json.loads(src.read_text(encoding="utf-8"))
            rows = data.get("pages", data) if isinstance(data, dict) else data
            for i, r in enumerate(rows, 1):
                if r.get("chapter"):
                    hints[int(r.get("page", i))] = str(r["chapter"])
    return [{"page": p.index, "role": p.role, "title": p.title, "chapter": hints.get(p.index, "")} for p in pages]


def _footer_fallback(svg: Path, texts: list[dict[str, Any]]) -> str:
    """Hand-drawn pages: the short left text in the bottom band ("고객 · 장명")."""
    m = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', svg.read_text(encoding="utf-8")[:600])
    if not m:
        return ""
    w, h = float(m.group(1)), float(m.group(2))
    for t in texts:
        txt = (t.get("text") or "").strip()
        if t["y"] > h * 0.93 and t["x"] < w * 0.5 and 2 <= len(txt) <= 40 and not re.search(r"\d+\s*/\s*\d+|출처|Source", txt):
            return re.split(r"\s[·|]\s", txt)[-1].strip()
    return ""


def _norm_no(no: str) -> str:
    if no in ASCII_ROMAN:
        return ASCII_ROMAN[no]
    if no.isdigit() and 1 <= int(no) <= len(ROMAN):
        return ROMAN[int(no) - 1]
    return no


def chapters(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pending: list[int] = []
    for r in rows:
        if r["role"] == "divider":
            pending.append(r["page"])
            continue
        if r["role"] in SKIP_ROLES:
            continue
        m = CRUMB.match(r["title"]) or (CRUMB.match(r["chapter"]) if r["chapter"] else None)
        if m:
            no, name, section = _norm_no(m.group(1)), m.group(2).strip(), (m.group(3) or "").strip()
            if m.string is r["chapter"]:
                section = r["title"]
        elif r["chapter"]:
            no, name, section = "", r["chapter"].strip(), r["title"]
        elif out:
            out[-1]["pages"].append(r["page"])
            continue
        else:
            continue
        if out and out[-1]["name"] == name:
            ch = out[-1]
        else:
            ch = {"no": no, "name": name, "pages": [], "sections": []}
            out.append(ch)
        ch["pages"] += pending + [r["page"]]
        pending = []
        if section and section not in ch["sections"]:
            ch["sections"].append(section)
    if any(ch["no"] for ch in out):  # numbered chapters exist: unnumbered ones are intro pages (deck-name footer)
        out = [ch for ch in out if ch["no"]]
    for i, ch in enumerate(out):
        ch["no"] = ch["no"] or (ROMAN[i] if i < len(ROMAN) else str(i + 1))
        a, b = min(ch["pages"]), max(ch["pages"])
        ch["range"] = f"{a}쪽" if a == b else f"{a}–{b}쪽"
        ch["desc"] = _desc(ch["sections"])
    return out


def _desc(sections: list[str]) -> str:
    parts: list[str] = []
    for s in sections:
        s = re.sub(r"\s*\(.*?\)\s*$", "", s).strip()
        if len(" · ".join(parts + [s])) > DESC_MAX:
            return " · ".join(parts) + " 등" if parts else s[:DESC_MAX - 1] + "…"
        parts.append(s)
    return " · ".join(parts)


def validate(chs: list[dict[str, Any]]) -> list[tuple[str, str]]:
    issues = []
    if not 2 <= len(chs) <= 6:
        issues.append(("ERROR", f"장 수 {len(chs)}개 — 목차는 2–6개 장이어야 합니다(원칙 §3)"))
    nos = [c["no"] for c in chs]
    if nos != [ROMAN[i] for i in range(len(chs))] and all(n in ROMAN for n in nos):
        issues.append(("WARN", f"장 번호가 순서대로가 아닙니다: {' '.join(nos)}"))
    for c in chs:
        if len(c["name"]) > NAME_MAX:
            issues.append(("WARN", f"장명 '{c['name']}'이 {NAME_MAX}자를 넘습니다"))
        if re.search(r"(니다|하라|할까|\?)$", c["name"]):
            issues.append(("WARN", f"장명 '{c['name']}'은 문장입니다 — 명사구로"))
    seen: dict[str, int] = {}
    for c in chs:
        seen[c["name"]] = seen.get(c["name"], 0) + 1
    for name, k in seen.items():
        if k > 1:
            issues.append(("WARN", f"장 '{name}'이 떨어진 위치에 {k}번 나옵니다 — 장표 순서를 확인하세요"))
    return issues


# ---------------------------------------------------------------------------
# Native-table TOC (data-pptx-native="table")
# ---------------------------------------------------------------------------
# The TOC templates hold one native table: its <metadata> JSON is the source
# of truth (rows share the zone down to the footer, cells valign ctr) and the
# visible SVG children are its fallback, regenerated here after every change.
# `data-toc-cols` on the table group names the column roles (no/title/pages)
# and `data-toc-prefix` the row id prefix, so QA can find `toc-1-title` etc.

LINE_HEIGHT = 1.2      # PowerPoint single spacing, as a multiple of the font size
BASELINE = 0.92        # first baseline below the line top, as a multiple of the size


def _font_stack(family: str) -> str:
    name = f'"{family}"' if " " in family else family
    return f'{name}, "Malgun Gothic", sans-serif'


def _cell_paragraphs(cell: dict[str, Any], default_size: float) -> list[dict[str, Any]]:
    """[{text, size, bold, color}] for a cell (`text` or one-run `paragraphs`)."""
    base = {"size": float(cell.get("font_size", default_size)), "bold": bool(cell.get("bold", False)),
            "color": cell.get("color", "#000000")}
    if "paragraphs" not in cell:
        return [dict(base, text=str(cell.get("text", "")))]
    out = []
    for para in cell["paragraphs"]:
        runs = para.get("runs") if isinstance(para, dict) else None
        run = runs[0] if runs else {}
        text = "".join(r.get("text", "") for r in runs) if runs else (para.get("text", "") if isinstance(para, dict) else str(para))
        out.append({"text": text, "size": float(run.get("font_size", base["size"])),
                    "bold": bool(run.get("bold", base["bold"])), "color": run.get("color", base["color"])})
    return out


def _scaled(total: float, weights: list[float]) -> list[float]:
    s = sum(weights)
    return [total * w / s for w in weights]


def table_fallback(meta: dict[str, Any], roles: list[str], prefix: str) -> list[ET.Element]:
    """SVG fallback for a native-table payload: cell fills, borders and centered text."""
    q = "{%s}" % SVG_NS
    style = meta.get("style", {})
    stack = _font_stack(style.get("font_family", "Pretendard"))
    default_size = float(style.get("font_size", 16))
    rows = ([meta["columns"]] if meta.get("columns") else []) + list(meta["rows"])
    header_rows = int(meta.get("header_rows", 1 if meta.get("columns") else 0))
    widths = _scaled(meta["width"], meta.get("column_widths") or [1] * len(rows[0]))
    heights = _scaled(meta["height"], meta.get("row_heights") or [1] * len(rows))
    fills: list[ET.Element] = []
    rules: list[ET.Element] = []
    texts: list[ET.Element] = []
    y = float(meta["y"])
    for r, row in enumerate(rows):
        h = heights[r]
        row_id = f"{prefix}head" if r < header_rows else f"{prefix}{r - header_rows + 1}"
        x = float(meta["x"])
        for c, cell in enumerate(row):
            cell = cell if isinstance(cell, dict) else {"text": str(cell)}
            w = widths[c]
            if cell.get("fill"):
                fills.append(ET.Element(q + "rect", {"x": f"{x:g}", "y": f"{y:.1f}", "width": f"{w:.1f}",
                                                     "height": f"{h:.1f}", "fill": cell["fill"]}))
            for side, (x1, y1, x2, y2) in {"top": (x, y, x + w, y), "bottom": (x, y + h, x + w, y + h),
                                           "left": (x, y, x, y + h), "right": (x + w, y, x + w, y + h)}.items():
                b = (cell.get("borders") or {}).get(side)
                if b and b.get("style") == "solid":
                    rules.append(ET.Element(q + "line", {"x1": f"{x1:.1f}", "y1": f"{y1:.1f}", "x2": f"{x2:.1f}",
                                                         "y2": f"{y2:.1f}", "stroke": b["color"],
                                                         "stroke-width": f"{b['width']:g}"}))
            pad = cell.get("padding", 0)
            pad = pad if isinstance(pad, dict) else {"left": pad, "right": pad, "top": pad, "bottom": pad}
            paras = [p for p in _cell_paragraphs(cell, default_size) if p["text"]]
            block = sum(LINE_HEIGHT * p["size"] for p in paras)
            top = y + (h - block) / 2 if cell.get("valign", "ctr") in ("ctr", "middle") else y + float(pad.get("top", 0))
            align = cell.get("align", "l")
            tx, anchor = {"l": (x + float(pad.get("left", 0)), None), "ctr": (x + w / 2, "middle"),
                          "r": (x + w - float(pad.get("right", 0)), "end")}[align]
            role = roles[c] if c < len(roles) else f"c{c + 1}"
            for k, p in enumerate(paras):
                name = role if k == 0 else ("desc" if role == "title" and k == 1 else f"{role}{k + 1}")
                attrs = {"id": f"{row_id}-{name}",
                         "x": f"{tx:.1f}", "y": f"{top + BASELINE * p['size']:.1f}", "font-family": stack,
                         "font-size": f"{p['size']:g}", "font-weight": "700" if p["bold"] else "400", "fill": p["color"]}
                if anchor:
                    attrs["text-anchor"] = anchor
                el = ET.Element(q + "text", attrs)
                el.text = p["text"]
                texts.append(el)
                top += LINE_HEIGHT * p["size"]
            x += w
        y += h
    return fills + rules + texts


def _table_group(root: ET.Element) -> Optional[ET.Element]:
    for el in root.iter():
        if el.get("data-pptx-native") == "table" and el.get("data-toc-cols"):
            return el
    return None


def _fill_table(group: ET.Element, n: int, current: Optional[int]) -> None:
    """Keep n chapter rows (the rest share their height), highlight `current`, redraw the fallback."""
    q = "{%s}" % SVG_NS
    meta_el = group.find(q + "metadata")
    meta = json.loads(meta_el.text or "{}")
    roles = group.get("data-toc-cols", "").split()
    body = meta["rows"]
    header = 1 if meta.get("columns") else 0
    heights = meta.get("row_heights") or [1] * (header + len(body))
    body_total = sum(heights[header:])
    on, off = json.loads(json.dumps(body[0])), json.loads(json.dumps(body[1] if len(body) > 1 else body[0]))
    meta["rows"] = body = body[:n]
    meta["row_heights"] = heights[:header] + [round(body_total / n, 2)] * n
    if current:
        muted = None
        for cell in off:
            for para in cell.get("paragraphs", [])[1:2]:
                muted = para["runs"][0].get("color")
        for i, row in enumerate(body, 1):
            src = on if i == current else off
            for c, cell in enumerate(row):
                for key in ("fill", "color"):
                    if key in src[c]:
                        cell[key] = src[c][key]
                if i != current and muted and roles[c] in ("title", "pages"):
                    if "paragraphs" in cell:
                        cell["paragraphs"][0]["runs"][0]["color"] = muted
                    else:
                        cell["color"] = muted
    meta_el.text = json.dumps(meta, ensure_ascii=False)
    for child in list(group):
        if child is not meta_el:
            group.remove(child)
    group.extend(table_fallback(meta, roles, group.get("data-toc-prefix", "toc-")))


def _fill_tokens(raw: str, values: dict[str, str]) -> str:
    """Replace {{TOKENS}}: JSON-escaped inside <metadata>, XML-escaped elsewhere."""
    def sub(text: str, json_safe: bool) -> str:
        def one(m: re.Match) -> str:
            if m.group(1) not in values:
                return m.group(0)
            v = values[m.group(1)]
            return escape(json.dumps(v, ensure_ascii=False)[1:-1] if json_safe else v)
        return re.sub(r"\{\{([A-Z0-9_]+)\}\}", one, text)
    parts = re.split(r"(<metadata\b[^>]*>.*?</metadata>)", raw, flags=re.S)
    return "".join(sub(p, p.startswith("<metadata")) for p in parts)


# ---------------------------------------------------------------------------
# Fill
# ---------------------------------------------------------------------------

def _template(family: str, n: int, near: Optional[Path] = None) -> Path:
    for name in ([f"02b_toc_pages_{max(3, n)}.svg"] if n <= 5 else []) + ["02b_toc_pages.svg"]:
        try:
            return find_template(family, name, near)
        except DiagramError:
            continue
    raise TocError(f"{family}: 02b_toc_pages 템플릿이 없습니다")


def _slots(text: str) -> int:
    return len(set(re.findall(r"\{\{TOC_(\d+)_TITLE\}\}", text)))


def render(chs: list[dict[str, Any]], family: str, title: str, lead: str, page: str,
           current: Optional[int] = None, section: str = "", near: Optional[Path] = None) -> str:
    path = _template(family, len(chs), near)
    raw = path.read_text(encoding="utf-8")
    slots = _slots(raw)
    if slots < len(chs):
        raise TocError(f"{path.name}: 칸 {slots}개 < 장 {len(chs)}개")
    values = {"PAGE_TITLE": title, "KEY_MESSAGE": lead, "PAGE_NUM": page, "SECTION_NAME": section or title}
    for i, c in enumerate(chs, 1):
        values.update({f"TOC_{i}_NO": c["no"], f"TOC_{i}_TITLE": c["name"], f"TOC_{i}_DESC": c["desc"],
                       f"TOC_{i}_PAGES": c["range"]})
    raw = _fill_tokens(raw, values)
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(raw)
    table = _table_group(root)
    if table is not None:
        _fill_table(table, len(chs), current)
        try:  # fallback baseline, so a later hand edit of the fallback is caught as stale
            from pptx_shapes import NATIVE_FALLBACK_SHA256_ATTR, svg_native_fallback_fingerprint
            table.set(NATIVE_FALLBACK_SHA256_ATTR, svg_native_fallback_fingerprint(table, document_root=root))
        except ImportError:
            pass
        if current:
            root.set("data-toc-current", str(current))
        root.set("data-toc-builder", "v33")
        return ET.tostring(root, encoding="unicode")
    parents = {ch: p for p in root.iter() for ch in p}
    by_id = {str(el.get("id")): el for el in root.iter() if el.get("id")}
    for k in range(len(chs) + 1, slots + 1):  # drop unused slots (2 chapters on the 3-slot page)
        for eid, el in list(by_id.items()):
            if eid.startswith(f"toc-{k}-") and el in parents and el in list(parents[el]):
                parents[el].remove(el)
    if current:
        def fill(*ids: str) -> str:
            return next((str(by_id[i].get("fill")) for i in ids if i in by_id and by_id[i].get("fill")), "#999999")
        accent, pale = fill("toc-1-badge"), fill("toc-2-badge", "toc-1-badge")
        on_no, off_no = fill("toc-1-no-carrier"), fill("toc-2-no-carrier", "toc-1-no-carrier")
        muted = fill("toc-1-desc-carrier")
        for i in range(1, len(chs) + 1):
            here = i == current
            if f"toc-{i}-badge" in by_id:
                by_id[f"toc-{i}-badge"].set("fill", accent if here else pale)
            if f"toc-{i}-no-carrier" in by_id:
                by_id[f"toc-{i}-no-carrier"].set("fill", on_no if here else off_no)
            if not here and f"toc-{i}-title-carrier" in by_id:
                by_id[f"toc-{i}-title-carrier"].set("fill", muted)
            if not here and f"toc-{i}-pages-carrier" in by_id:
                by_id[f"toc-{i}-pages-carrier"].set("fill", muted)
        root.set("data-toc-current", str(current))
    root.set("data-toc-builder", "v33")
    return ET.tostring(root, encoding="unicode")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description="Build the INNerGEN TOC page from page titles.")
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("chapters", help="print the chapters found")
    c.add_argument("source", type=Path)
    b = sub.add_parser("build", help="fill the TOC template")
    b.add_argument("source", type=Path)
    b.add_argument("--family", required=True, choices=sorted(FAMILIES))
    b.add_argument("-o", "--output", type=Path, required=True)
    b.add_argument("--title", default="목차")
    b.add_argument("--lead", default="")
    b.add_argument("--page", default="2")
    b.add_argument("--dividers", type=Path, default=None, help="also write one highlighted TOC per chapter here")
    args = ap.parse_args(argv)
    try:
        chs = chapters(_page_rows(args.source))
    except FileNotFoundError as exc:
        print(f"ERROR  {exc}")
        return 1
    if not chs:
        print("ERROR  장을 찾지 못했습니다 — 본문 제목을 'Ⅰ. 장명 – 절명' 형식으로 쓰거나, 꼬리말 장 표시 또는 outline의 chapter 필드를 채우세요")
        return 1
    issues = validate(chs)
    for c_ in chs:
        print(f"{c_['no']:>3}  {c_['name']:<20} {c_['range']:>8}  {c_['desc']}")
    for level, msg in issues:
        print(f"{level}  {msg}")
    if args.command == "chapters":
        return 1 if any(lv == "ERROR" for lv, _ in issues) else 0
    if any(lv == "ERROR" for lv, _ in issues):
        return 1
    if not args.lead:
        print("WARN  --lead 없음: 목차 거버닝(이 덱의 답을 한 문장으로)을 비워 두었습니다")
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        near = args.output.parent
        svg = render(chs, args.family, args.title, args.lead, args.page, near=near)
        args.output.write_text(svg, encoding="utf-8")
        _copy_chrome_images(svg, _template(args.family, len(chs), near), args.output)
        print(f"OK  {args.output}")
        if args.dividers:
            args.dividers.mkdir(parents=True, exist_ok=True)
            for i, ch in enumerate(chs, 1):
                page = str(min(ch["pages"]) - 1)
                out = args.dividers / f"toc_{i}_{re.sub(r'[^0-9A-Za-z가-힣]+', '_', ch['name']).strip('_')}.svg"
                svg = render(chs, args.family, args.title, args.lead, page, current=i, section=f"{ch['no']}. {ch['name']}", near=near)
                out.write_text(svg, encoding="utf-8")
                _copy_chrome_images(svg, _template(args.family, len(chs), near), out)
                print(f"OK  {out}  (장 {ch['no']} 강조, {ch['range']} 앞에 삽입)")
    except TocError as exc:
        print(f"ERROR  {exc}")
        return 1
    if args.source.is_dir():  # the TOC carries the "여러 도식 후보 보기" checklist
        import content_diagrams
        import innergen_story_check as story
        sel = args.source / "analysis" / content_diagrams.SELECT_FILE
        if not sel.exists():
            rules = json.loads(story.RULES_PATH.read_text(encoding="utf-8"))
            ranked = content_diagrams.plan(story.pages_from_project(args.source, rules), 6)
            content_diagrams.write_select(args.source, args.source, {r["page"]: r["why"] for r in ranked}, set())
        print(f"목차 체크리스트: {sel} — 여러 도식 후보를 볼 장·장표에 [x]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
