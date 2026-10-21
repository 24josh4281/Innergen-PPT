#!/usr/bin/env python3
"""
INNerGEN content gate - table of contents and must-have content per report type
(deck_type) and business type.

Reads references/content-requirements-v25.json and checks either an outline
(the numbered page plan written before any page is drawn) or a finished SVG deck
(through innergen_qaqc.py, which calls check()). Codes:

    R00  report type not given (TOC check skipped)
    R01  required TOC section missing                     ERROR
    R02  sections out of the expected order               WARN
    R03  report type must-have content missing            ERROR/WARN per spec
    R04  page count outside the type's usual range        INFO
    B00  business type not given
    B01  business type must-have content missing          ERROR/WARN per spec
    Q01  placeholder or draft residue                     ERROR
    Q02  forbidden pattern (stage name in a body title, Q&A slide in a seminar)  WARN

Usage:
    python3 scripts/innergen_content_check.py --outline plan.md --deck-type kickoff --business-type inventory
    python3 scripts/innergen_content_check.py --list                # report and business type ids

Outline format: a Markdown table whose rows start with the page number, then
layout id, page title, governing message, and any further columns (body notes,
must-have content); or a JSON list of {page, layout, title, governing, body}.
At outline stage an ERROR item becomes WARN (body text is not written yet), but
missing TOC sections stay ERROR.

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

REPO = _SCRIPTS_DIR.parents[min(3, len(_SCRIPTS_DIR.parents) - 1)]
SPEC_PATH = REPO / "docs/styles/innergen/content-requirements-v25.json"
# Standalone skill bundles ship the spec beside the skill.
if not SPEC_PATH.is_file():
    SPEC_PATH = _SCRIPTS_DIR.parent / "references/content-requirements-v25.json"

FRAME_TOKENS = ("cover", "toc", "section-divider", "ending")


def load_spec(path: Path | None = None) -> dict | None:
    p = path or SPEC_PATH
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def layout_from_stem(stem: str) -> str:
    """`05_s24_project_overview` -> `s24-project-overview`, `02_02b_toc_pages` -> `toc-pages`."""
    m = re.match(r"^\d+_((?:0\d[a-z]?|s\d{2})_[a-z0-9_]+?)(?:__.*)?$", stem)
    if not m:
        return ""
    return re.sub(r"^(?:0\d[a-z]?)_", "", m.group(1)).replace("_", "-")


class PlanPage:
    """What the content gate needs from one page, whether planned or drawn."""

    def __init__(self, index: int, layout: str, title: str = "", governing: str = "",
                 headings: list[str] | None = None, texts: list[str] | None = None):
        self.index, self.layout = index, (layout or "").lower()
        self.title, self.governing = title or "", governing or ""
        self.headings = [h for h in ([self.title, self.governing] + (headings or [])) if h]
        self.texts = [t for t in ([self.title, self.governing] + (texts or [])) if t]

    @property
    def is_frame(self) -> bool:
        return any(tok in self.layout for tok in FRAME_TOKENS)

    @property
    def is_toc(self) -> bool:
        return "toc" in self.layout


def pages_from_svg(pages) -> list[PlanPage]:
    """Adapt innergen_qaqc.Page objects. Footer label and page number repeat on
    every page, so they are left out of the text the gate searches."""
    out = []
    for p in pages:
        skip = {id(x) for x in (p.footer_label, p.page_number) if x is not None}
        body = [t for t in p.texts if t["text"] and id(t) not in skip]
        out.append(PlanPage(
            p.index, p.layout + " " + (p.role or ""),
            p.title["text"] if p.title else "", p.governing["text"] if p.governing else "",
            headings=[t["text"] for t in body if t["size"] >= 20],
            texts=[t["text"] for t in body],
        ))
    return out


def load_outline(path: Path) -> list[PlanPage]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        rows = data.get("pages", data) if isinstance(data, dict) else data
        out = []
        for i, r in enumerate(rows, 1):
            n = int(r.get("page", i))
            layout = _outline_layout(n, str(r.get("layout", "")))
            body = r.get("body", "")
            body = body if isinstance(body, list) else [body]
            out.append(PlanPage(n, layout, r.get("title", ""), r.get("governing", ""), texts=[str(b) for b in body if b]))
        return out
    out = []
    for line in raw.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("`").strip() for c in s.strip("|").split("|")]
        if not cells or not re.fullmatch(r"P?\d{1,3}", cells[0]):
            continue
        n = int(cells[0].lstrip("P"))
        cells += [""] * (4 - len(cells))
        out.append(PlanPage(n, _outline_layout(n, cells[1]), cells[2], cells[3], texts=cells[4:]))
    return out


def _outline_layout(n: int, cell: str) -> str:
    cell = cell.strip().strip("`").removesuffix(".svg")
    cell = re.sub(r"^\d+_(?=(?:0\d[a-z]?|s\d{2})_)", "", cell)
    return layout_from_stem(f"{n:02d}_{cell}") or cell.lower().replace("_", "-")


def resolve(spec: dict, deck_type: str | None, business_type: str | None) -> tuple[str | None, str | None]:
    dt = (deck_type or "").strip().lower() or None
    if dt:
        dt = spec.get("aliases", {}).get("deck_type", {}).get(dt, dt)
    bt = (business_type or "").strip().lower() or None
    if bt and bt not in spec["business_types"]:
        for key, b in spec["business_types"].items():
            if bt in b.get("aliases", []):
                bt = key
                break
    return dt, bt


def _rx(p: str) -> re.Pattern:
    return re.compile(p, re.IGNORECASE | re.MULTILINE)


def _section_pages(sec: dict, pages: list[PlanPage]) -> list[int]:
    hits = []
    kw = _rx(sec["keywords"]) if sec.get("keywords") else None
    for p in pages:
        if any(tok in p.layout for tok in sec.get("layouts", [])):
            hits.append(p.index)
        elif kw and not p.is_frame and any(kw.search(h) for h in p.headings):
            hits.append(p.index)
    return hits


def _item_hit(item: dict, texts: list[str]) -> bool:
    blob = "\n".join(texts)
    if item.get("all_of"):
        return all(_rx(p).search(blob) for p in item["all_of"])
    return bool(_rx(item["pattern"]).search(blob))


def _scope_texts(item: dict, pages: list[PlanPage], sections: dict[str, list[int]]) -> list[str] | None:
    where = item.get("where", "deck")
    if where == "titles":
        return [p.title for p in pages if not p.is_frame and p.title]
    if where.startswith("section:"):
        idx = set(sections.get(where.split(":", 1)[1], []))
        if not idx:
            return None  # section itself is missing; R01 already reports it
        return [t for p in pages if p.index in idx for t in p.texts]
    return [t for p in pages if not p.is_toc for t in p.texts]


def _run_items(items, code, pages, sections, add, outline, prefix=""):
    for it in items:
        if it["level"] == "FORBID":
            rx = _rx(it["pattern"])
            scope = [p for p in pages if not p.is_frame] if it.get("where") == "titles" else pages
            for p in scope:
                txt = p.title if it.get("where") == "titles" else "\n".join(p.texts)
                m = rx.search(txt or "")
                if m:
                    add("WARN", "Q02", p.index, f"{prefix}{it['label']}: '{m.group(0)}' ({it.get('basis', '')})")
            continue
        texts = _scope_texts(it, pages, sections)
        if texts is None or _item_hit(it, texts):
            continue
        level = it["level"]
        if outline and level == "ERROR":
            level = "WARN"
        where = it.get("where", "deck")
        loc = "" if where == "deck" else f" [{where.replace('section:', '절 ')}]"
        add(level, code, 0, f"{prefix}꼭 들어갈 내용 없음: {it['label']}{loc} — {it.get('basis', '')}")


def check(pages: list[PlanPage], deck_type: str | None, business_type: str | None, spec: dict, add,
          outline: bool = False) -> dict:
    """Run R/B/Q checks; `add(level, code, page, message)` records each finding."""
    dt, bt = resolve(spec, deck_type, business_type)
    rt = spec["report_types"].get(dt) if dt else None
    sections: dict[str, list[int]] = {}

    if dt is None:
        add("WARN", "R00", 0, "보고 유형(--deck-type 또는 design_spec.md deck_type)이 없어 목차·필수 내용 검사를 건너뜁니다")
    elif rt is None:
        add("INFO", "R00", 0, f"보고 유형 '{dt}'은 content-requirements 대상이 아닙니다({', '.join(spec.get('not_covered', []))} 포함)")
    else:
        for sec in rt["sections"]:
            sections[sec["id"]] = _section_pages(sec, pages)
            if sec["required"] and not sections[sec["id"]]:
                hint = " / ".join(x for x in ("·".join(sec.get("layouts", [])), sec.get("keywords", "")) if x)
                add("ERROR", "R01", 0, f"{rt['label_ko']} 목차 필수 절 없음: {sec['label']} (레이아웃 또는 제목·거버닝 키워드: {hint})")
        firsts = [(sid, min(sections[sid])) for sid in rt.get("order", []) if sections.get(sid)]
        for (a, pa), (b, pb) in zip(firsts, firsts[1:]):
            if pb < pa:
                la = next(s["label"] for s in rt["sections"] if s["id"] == a)
                lb = next(s["label"] for s in rt["sections"] if s["id"] == b)
                add("WARN", "R02", pb, f"목차 순서: '{lb}'(P{pb:02d})가 '{la}'(P{pa:02d})보다 앞에 있습니다 — {rt['basis']}")
        _run_items(rt.get("items", []), "R03", pages, sections, add, outline)
        lo, hi = rt.get("pages", [0, 999])
        n = len(pages)
        if n and not (lo * 0.5 <= n <= hi * 1.5):
            add("INFO", "R04", 0, f"{rt['label_ko']} 기본 장수 {lo}–{hi}장 대비 {n}장입니다")

    if bt is None:
        lvl = "WARN" if dt in (None, "proposal", "kickoff", "weekly", "biweekly", "monthly", "diagnosis", "interim", "final", "briefing", "benchmark") else "INFO"
        msg = f"사업 성격 '{business_type}'을 알 수 없습니다" if business_type else "사업 성격(--business-type 또는 design_spec.md innergen_business_type)이 없어 업무별 필수 내용 검사를 건너뜁니다"
        add(lvl, "B00", 0, msg + f" (선택지: {', '.join(spec['business_types'])})")
    elif bt not in spec["business_types"]:
        add("WARN", "B00", 0, f"사업 성격 '{bt}'을 알 수 없습니다 (선택지: {', '.join(spec['business_types'])})")
        bt = None
    else:
        b = spec["business_types"][bt]
        items = [it for it in b["items"] if not it.get("stages") or (dt and dt in it["stages"])]
        _run_items(items, "B01", pages, sections, add, outline, prefix=f"[{b['label_ko']}] ")

    for it in spec.get("hygiene", []):
        if it["level"] == "FORBID":
            _run_items([it], "Q02", pages, sections, add, outline)
            continue
        rx = _rx(it["pattern"])
        for p in pages:
            m = next((m for m in (rx.search(t) for t in p.texts) if m), None)
            if m:
                add(it["level"], "Q01", p.index, f"{it['label']}: '{m.group(0)}'")

    return {"deck_type": dt, "business_type": bt,
            "sections_found": {k: v for k, v in sections.items() if v},
            "sections_missing": [k for k, v in sections.items() if not v]}


def main(argv=None) -> int:
    try:
        from console_encoding import configure_utf8_stdio
        configure_utf8_stdio()
    except ImportError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outline", type=Path, help="page plan (.md table or .json)")
    ap.add_argument("--deck-type", default=None)
    ap.add_argument("--business-type", default=None)
    ap.add_argument("--list", action="store_true", help="print report and business type ids")
    ap.add_argument("--strict", action="store_true", help="fail on WARN too")
    args = ap.parse_args(argv)
    spec = load_spec()
    if spec is None:
        print(f"[content_check] spec not found: {SPEC_PATH}")
        return 2
    if args.list:
        print("report types (--deck-type):")
        for k, v in spec["report_types"].items():
            req = [s["label"] for s in v["sections"] if s["required"]]
            print(f"  {k:10s} {v['label_ko']}: {' → '.join(req)}")
        print("business types (--business-type):")
        for k, v in spec["business_types"].items():
            print(f"  {k:18s} {v['label_ko']}: {', '.join(i['label'] for i in v['items'])}")
        return 0
    if not args.outline:
        ap.error("--outline is required (finished decks are checked by innergen_qaqc.py)")
    pages = load_outline(args.outline)
    if not pages:
        print("[content_check] no page rows found (rows must start with a page number)")
        return 2
    found: list[tuple] = []
    res = check(pages, args.deck_type, args.business_type, spec, lambda *a: found.append(a), outline=True)
    for lvl, code, page, msg in sorted(found, key=lambda x: ({"ERROR": 0, "WARN": 1, "INFO": 2}[x[0]], x[2])):
        print(f"[{lvl}] {code} {'P%02d' % page if page else '덱'} {msg}")
    errs = sum(1 for f in found if f[0] == "ERROR")
    warns = sum(1 for f in found if f[0] == "WARN")
    print(f"[content_check] {res['deck_type']} × {res['business_type']} · {len(pages)} pages · ERROR {errs} · WARN {warns}")
    print("[content_check] " + ("FAIL" if errs or (args.strict and warns) else "PASS"))
    return 1 if errs or (args.strict and warns) else 0


if __name__ == "__main__":
    raise SystemExit(main())
