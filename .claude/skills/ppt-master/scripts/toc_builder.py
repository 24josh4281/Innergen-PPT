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
    raw = re.sub(r"\{\{([A-Z0-9_]+)\}\}", lambda m: escape(values.get(m.group(1), m.group(0))), raw)
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(raw)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
