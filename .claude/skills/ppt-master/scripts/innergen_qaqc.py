#!/usr/bin/env python3
"""
PPT Master - INNerGEN QA/QC gate (uniformity + writing rules)

Checks a finished (or in-progress) SVG deck against the INNerGEN design rules
in docs/styles/innergen: chrome geometry (v17), governing grammar (v11/v20),
title system (v4/v5/v20), TOC ↔ chapter consistency (v5/v20), structure and
closing set per deck type (v20), font sizes (v18), citation line (v16).
It complements svg_quality_checker.py (SVG/PPTX contract) with the
*content* and *uniformity* layer that otherwise needs a human review.

Usage:
    python3 scripts/innergen_qaqc.py <project_path> [--deck-type lecture] [--register auto|external|internal]
                                     [--family innergen_lecture] [--strict] [--json <out.json>]

Outputs:
    <project>/analysis/innergen_qaqc_report.md and .json
    exit 1 on ERROR (or WARN with --strict)

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from console_encoding import configure_utf8_stdio  # noqa: E402

REPO = _SCRIPTS_DIR.parents[3]
RULES_PATH = REPO / "docs/styles/innergen/qaqc-v21.json"
V17_PATH = REPO / "docs/styles/innergen/design-standard-v17.json"
V20_PATH = REPO / "docs/styles/innergen/content-architecture-v20.json"
SVG_NS = "{http://www.w3.org/2000/svg}"


# ---------------------------------------------------------------- helpers
def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _num(v, default=None):
    try:
        return float(str(v).strip().split()[0].rstrip("px"))
    except (TypeError, ValueError, AttributeError):
        return default


def _text_lines(el: ET.Element) -> list[str]:
    """Visible lines of a <text>: a tspan with x/dy starts a new line."""
    lines: list[str] = []
    cur = (el.text or "").strip()
    for ch in el:
        if _local(ch.tag) != "tspan":
            continue
        starts_line = ch.get("x") is not None or (ch.get("dy") is not None and _num(ch.get("dy"), 0) > 0)
        piece = "".join(ch.itertext()).strip()
        if starts_line:
            if cur:
                lines.append(cur)
            cur = piece
        else:
            cur = (cur + " " + piece).strip() if cur else piece
        tail = (ch.tail or "").strip()
        if tail:
            cur = (cur + " " + tail).strip()
    if cur:
        lines.append(cur)
    return [l for l in lines if l]


def _full_text(el: ET.Element) -> str:
    return re.sub(r"\s+", " ", " ".join(_text_lines(el))).strip()


def _glyph_width(s: str, size: float) -> float:
    w = 0.0
    for ch in s:
        if ch == " ":
            w += 0.25 * size
        elif ord(ch) < 128:
            w += 0.55 * size
        else:
            w += 1.0 * size
    return w


def _norm(s: str) -> str:
    return re.sub(r"[\s·,.:;!?()\[\]{}「」『』“”‘’\"'/\-–—]", "", s).lower()


def _similar(a: str, b: str) -> float:
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    sa, sb = set(a[i:i + 2] for i in range(len(a) - 1)), set(b[i:i + 2] for i in range(len(b) - 1))
    return len(sa & sb) / max(1, len(sa | sb))


# ---------------------------------------------------------------- page model
class Page:
    def __init__(self, path: Path, index: int):
        self.path, self.index = path, index
        self.root = ET.parse(str(path)).getroot()
        self.layout = self.root.get("data-pptx-layout") or ""
        self.role = self.root.get("data-pptx-page-role") or ""
        self.texts: list[dict] = []
        self.rects: list[dict] = []
        self.images: list[dict] = []
        self.lines: list[dict] = []
        self._walk(self.root, {})
        self.title = self._pick(lambda t: abs(t["y"] - 50) <= 3 and abs(t["size"] - 32) <= 1)
        self.governing = self._pick(lambda t: 90 <= t["y"] <= 136 and abs(t["size"] - 24) <= 1 and t["x"] >= 60)
        self.source = self._pick(lambda t: 618 <= t["y"] <= 642 and t["size"] <= 18)
        self.footer_label = self._pick(lambda t: 680 <= t["y"] <= 692 and t["x"] < 400)
        self.page_number = self._pick(lambda t: 680 <= t["y"] <= 692 and t["anchor"] == "end")

    def _walk(self, el, inherited):
        tag = _local(el.tag)
        style = dict(inherited)
        for k in ("font-family", "font-size", "font-weight", "fill", "text-anchor"):
            if el.get(k) is not None:
                style[k] = el.get(k)
        if tag == "text":
            lines = _text_lines(el)
            self.texts.append({
                "el": el, "id": el.get("id") or "", "x": _num(el.get("x"), 0.0), "y": _num(el.get("y"), 0.0),
                "size": _num(style.get("font-size"), 0.0), "weight": str(style.get("font-weight", "400")),
                "fill": (style.get("fill") or "").upper(), "family": style.get("font-family", ""),
                "anchor": style.get("text-anchor", "start"), "lines": lines, "text": " ".join(lines),
                "group": self._group_id(el),
            })
            return
        if tag == "rect":
            self.rects.append({"x": _num(el.get("x"), 0.0), "y": _num(el.get("y"), 0.0), "w": _num(el.get("width"), 0.0), "h": _num(el.get("height"), 0.0), "fill": (el.get("fill") or "").upper(), "id": el.get("id") or ""})
        elif tag == "image":
            self.images.append({"x": _num(el.get("x"), 0.0), "y": _num(el.get("y"), 0.0), "w": _num(el.get("width"), 0.0), "h": _num(el.get("height"), 0.0), "href": el.get("href") or el.get("{http://www.w3.org/1999/xlink}href") or ""})
        elif tag == "line":
            self.lines.append({"y1": _num(el.get("y1"), 0.0), "y2": _num(el.get("y2"), 0.0), "x1": _num(el.get("x1"), 0.0), "x2": _num(el.get("x2"), 0.0)})
        for ch in el:
            if _local(ch.tag) in ("metadata", "defs", "style"):
                continue
            self._walk(ch, style)

    _parent_map = None

    def _group_id(self, el):
        if self._parent_map is None:
            self._parent_map = {c: p for p in self.root.iter() for c in p}
        cur = el
        while cur is not None and cur is not self.root:
            cur = self._parent_map.get(cur)
            if cur is not None and _local(cur.tag) == "g" and cur.get("id"):
                return cur.get("id")
        return ""

    def _pick(self, pred):
        cands = [t for t in self.texts if t["text"] and pred(t)]
        return cands[0] if cands else None

    def is_exempt(self, keywords):
        key = (self.layout + " " + self.role).lower()
        return any(k in key for k in keywords)

    def slot_text(self, gid: str):
        for t in self.texts:
            if t["group"] == gid:
                return t
        return None


# ---------------------------------------------------------------- checks
class Report:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, level, code, page, msg):
        self.items.append({"level": level, "code": code, "page": page, "message": msg})

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)


def detect_register(ending: str, rules: dict) -> str:
    if any(ending.endswith(p) for p in rules["registers"]["promise_endings"]):
        return "promise"
    if ending.endswith("니다") or ending.endswith("다") or ending.endswith("다."):
        return "external"
    for e in rules["registers"]["internal"]["endings"]:
        if ending.endswith(e) or ending.endswith(e + "."):
            return "internal"
    return "noun"


def run(project: Path, deck_type: str | None, register: str, family: str | None, rules: dict) -> tuple[Report, dict]:
    rep = Report()
    svg_dir = project / "svg_output"
    pages = [Page(p, i + 1) for i, p in enumerate(sorted(svg_dir.glob("*.svg")))]
    if not pages:
        rep.add("ERROR", "P00", 0, "svg_output/ 에 SVG가 없습니다")
        return rep, {}

    # family / deck type from project files when not given
    prof_file = project / "design_profile_v17.json"
    if family is None and prof_file.exists():
        try:
            family = json.loads(prof_file.read_text(encoding="utf-8")).get("family")
        except Exception:  # noqa: BLE001
            family = None
    family = family or "innergen_lecture"
    fam = rules["families"].get(family) or rules["families"]["innergen_lecture"]
    if deck_type is None:
        spec = (project / "design_spec.md")
        if spec.exists():
            m = re.search(r"deck_type:\s*(\w+)", spec.read_text(encoding="utf-8"))
            deck_type = m.group(1) if m else None
    exempt = fam["exempt_layout_keywords"]
    content = [p for p in pages if not p.is_exempt(exempt)]

    # ---- spec_lock colors
    lock = project / "spec_lock.md"
    palette = set()
    if lock.exists():
        palette = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}", lock.read_text(encoding="utf-8"))}
    palette |= {"#FFFFFF", "NONE", ""}

    # ---- C: chrome / geometry
    tol = fam["title"]["tolerance"]
    for p in content:
        if not any(abs(r["y"]) < 1 and r["h"] <= 4 and r["w"] >= fam["canvas"][0] - 1 for r in p.rects):
            rep.add("ERROR", "C01", p.index, "상단 블루 선(0,0,1040,3)이 없습니다")
        if p.title is None:
            rep.add("ERROR", "C02", p.index, "제목(x48, 기준선 50, 32px)을 찾지 못했습니다")
        else:
            t = p.title
            if abs(t["x"] - fam["title"]["x"]) > tol or t["fill"] != fam["title"]["fill"].upper() or t["weight"] not in ("700", "bold"):
                rep.add("WARN", "C02", p.index, f"제목 위치·색·굵기가 기준과 다릅니다 (x={t['x']:g}, fill={t['fill']}, weight={t['weight']})")
        gb = fam["governing"]["box"]
        if not any(abs(r["x"] - gb[0]) <= 1 and abs(r["y"] - gb[1]) <= 1 and abs(r["w"] - gb[2]) <= 1 and abs(r["h"] - gb[3]) <= 1 for r in p.rects):
            rep.add("ERROR", "C03", p.index, "거버닝 박스(48,70,944,80)가 없습니다")
        if p.governing is not None:
            g = p.governing
            n = len(g["lines"])
            exp = fam["governing"]["baseline_one_line"] if n == 1 else fam["governing"]["baseline_two_lines"][0]
            if abs(g["y"] - exp) > fam["governing"]["tolerance"]:
                rep.add("WARN", "C03", p.index, f"거버닝 기준선 y={g['y']:g} (기준 {exp}, {n}줄)")
            if g["fill"] != fam["governing"]["fill"].upper() or g["weight"] not in ("700", "bold"):
                rep.add("WARN", "C03", p.index, "거버닝은 블루(#2F62F0) 볼드여야 합니다")
        if p.source is None:
            key = p.layout.lower()
            if any(k in key for k in rules["source_line"]["required_on_layouts_with"]):
                rep.add("WARN", "C04", p.index, "근거·표·차트 장표인데 출처 줄(y630)이 없습니다")
        else:
            if not re.match(rules["source_line"]["format_regex"], p.source["text"]):
                rep.add("WARN", "C04", p.index, f"출처 줄은 '출처:'로 시작해야 합니다: {p.source['text'][:40]}")
            if abs(p.source["y"] - fam["source"]["baseline"]) > fam["source"]["tolerance"] or abs(p.source["size"] - fam["source"]["size"]) > 1:
                rep.add("WARN", "C04", p.index, f"출처 줄 위치·크기 (y={p.source['y']:g}, {p.source['size']:g}px)")
        if not any(abs(l["y1"] - fam["footer"]["line_y"]) <= 1 and abs(l["y2"] - fam["footer"]["line_y"]) <= 1 for l in p.lines):
            rep.add("ERROR", "C05", p.index, "푸터 선(y648)이 없습니다")
        if not any(abs(i["x"] - 48) <= 1 and abs(i["y"] - 660) <= 1 for i in p.images):
            rep.add("ERROR", "C05", p.index, "푸터 로고(48,660)가 없습니다")
        if p.page_number is None:
            rep.add("ERROR", "C05", p.index, "페이지 번호가 없습니다")
        elif p.page_number["text"].strip() != str(p.index):
            rep.add("ERROR", "C05", p.index, f"페이지 번호 '{p.page_number['text']}' ≠ 실제 순번 {p.index}")
    labels = Counter(p.footer_label["text"] for p in content if p.footer_label)
    if len(labels) > 1:
        rep.add("WARN", "C05", 0, f"푸터 라벨이 여러 종류입니다: {dict(labels)}")

    # ---- fonts & colors
    for p in pages:
        for t in p.texts:
            if t["family"] and rules["font"]["required_family"] not in t["family"]:
                rep.add("ERROR", "C08", p.index, f"글꼴 '{t['family'][:30]}' — Pretendard 아님")
                break
        small = [t for t in p.texts if t["text"] and 0 < t["size"] < rules["font"]["min_px_content"] and t["y"] < 648]
        for t in small[:3]:
            rep.add("WARN", "C06", p.index, f"본문 글자 {t['size']:g}px < {rules['font']['min_px_content']}px: '{t['text'][:24]}'")
        tiny = [t for t in p.texts if t["text"] and 0 < t["size"] < rules["font"]["min_px_footer"]]
        for t in tiny[:2]:
            rep.add("ERROR", "C06", p.index, f"글자 {t['size']:g}px < {rules['font']['min_px_footer']}px: '{t['text'][:24]}'")
        if palette:
            off = sorted({t["fill"] for t in p.texts if t["fill"] and t["fill"] not in palette} | {r["fill"] for r in p.rects if r["fill"] and r["fill"] not in palette})
            if off:
                rep.add("WARN", "C07", p.index, f"spec_lock 밖의 색: {', '.join(off[:5])}")

    # ---- G: governing
    gov_pages = [(p, p.governing) for p in content]
    regs = Counter()
    seen: list[tuple[int, str]] = []
    gr = rules["governing"]
    for p, g in gov_pages:
        if g is None:
            rep.add("ERROR", "G01", p.index, "본문 장표에 거버닝 문장이 없습니다")
            continue
        text = g["text"]
        if p.title and _similar(text, p.title["text"]) >= gr["duplicate_similarity"]:
            rep.add("ERROR", "G02", p.index, "거버닝이 제목을 그대로 반복합니다")
        for idx, prev in seen:
            if _similar(text, prev) >= gr["duplicate_similarity"]:
                rep.add("ERROR", "G03", p.index, f"P{idx:02d}의 거버닝과 같은 문장입니다")
                break
        seen.append((p.index, text))
        n = len(g["lines"])
        if n > gr["max_lines"]:
            rep.add("ERROR", "G04", p.index, f"거버닝이 {n}줄입니다(최대 {gr['max_lines']}줄)")
        lim = gr["chars_no_space"].get(str(int(g["size"])), gr["chars_no_space"]["24"])
        cnt = len(text.replace(" ", ""))
        if cnt > lim["two_lines"]:
            rep.add("WARN", "G04", p.index, f"거버닝 {cnt}자 > 두 줄 상한 {lim['two_lines']}자")
        for ln in g["lines"]:
            if _glyph_width(ln, g["size"]) > fam["governing"]["inner_width"]:
                rep.add("WARN", "G04", p.index, f"거버닝 한 줄이 박스 폭을 넘습니다: '{ln[:30]}…'")
        if cnt < gr["min_chars"]:
            rep.add("WARN", "G08", p.index, f"거버닝이 너무 짧습니다({cnt}자) — 명사구가 아닌 판단 문장으로")
        if any(text.startswith(s) for s in gr["forbidden_starts"]):
            rep.add("WARN", "G06", p.index, "거버닝이 지시어로 시작합니다 — 주어로 시작")
        for ph in gr["forbidden_phrases"]:
            if ph in text:
                rep.add("WARN", "G06", p.index, f"행동 없는 구호 '{ph}' — 확인 대상·기준·행동을 붙이세요")
        if gr["question_mark_warn"] and "?" in text:
            rep.add("WARN", "G06", p.index, "거버닝이 질문형입니다 — 질문은 자가진단 장표(s20)로")
        if not re.search(gr["number_pattern"], text):
            rep.add("INFO", "G07", p.index, "거버닝에 수치가 없습니다(현황·판단 장표면 핵심 수치 1개 권장)")
        regs[(p.index, detect_register(text.rstrip(" ."), gr))] = 1
    reg_counts = Counter(r for (_, r) in regs)
    main_reg = register
    if register == "auto":
        core = {k: v for k, v in reg_counts.items() if k in ("external", "internal")}
        main_reg = max(core, key=core.get) if core else "external"
    for (idx, r) in regs:
        if r in ("external", "internal") and r != main_reg:
            rep.add("WARN", "G05", idx, f"거버닝 문체가 덱 기준({main_reg})과 다릅니다({r}). 한 덱에 한 문체")
        if r == "noun":
            rep.add("WARN", "G05", idx, "거버닝이 명사로 끝납니다 — 완결 문장(외부) 또는 개조식(내부)으로")

    # ---- T: title
    tr = rules["title"]
    titles = [(p, p.title["text"]) for p in content if p.title]
    numbered = 0
    for p, t in titles:
        body = re.sub(tr["numbering_regex"], "", t).strip(" ./-–")
        if re.match(tr["numbering_regex"], t):
            numbered += 1
        n = len(body.replace(" ", ""))
        if n < tr["min_chars"] or n > tr["max_chars"]:
            rep.add("WARN", "T01", p.index, f"제목 길이 {n}자 (권장 {tr['min_chars']}–{tr['max_chars']}): '{t[:30]}'")
        if any(body.endswith(e) for e in tr["sentence_endings"]) or body.endswith("?"):
            rep.add("WARN", "T02", p.index, f"제목은 주제 명사구로: '{t[:30]}'")
    if titles and 0 < numbered < len(titles):
        rep.add("WARN", "T03", 0, f"제목 번호가 일부 장표에만 있습니다 ({numbered}/{len(titles)})")
    tc = Counter(_norm(re.sub(r"\(\d+/\d+\)|\(계속\)", "", t)) for _, t in titles)
    for key, c in tc.items():
        if c >= tr["repeat_limit"]:
            pages_ = [p.index for p, t in titles if _norm(re.sub(r"\(\d+/\d+\)|\(계속\)", "", t)) == key]
            marks = [t for p, t in titles if p.index in pages_ and re.search(r"\(\d+/\d+\)", t)]
            if len(marks) < c:
                rep.add("WARN", "T04", pages_[0], f"같은 제목이 {c}장 반복됩니다(P{pages_}) — (n/N) 표기 또는 거버닝 차별화")

    # ---- O: TOC ↔ chapters
    def _is_toc(layout):
        return any(layout.startswith(x) for x in rules["toc"]["layouts"])

    toc_pages = [p for p in pages if _is_toc(p.layout)]
    if toc_pages:
        toc = toc_pages[0]
        items = [t["text"] for t in toc.texts if re.match(r"toc-\d+-title", t["group"] or t["id"] or "")]
        chapter_titles = [t for _, t in titles]
        for item in items:
            core = re.sub(tr["numbering_regex"], "", item).strip(" ./-–")
            if len(core) < rules["toc"]["match_min_chars"]:
                continue
            cands = chapter_titles + [t["text"] for p in pages for t in p.texts
                                      if (p.layout in rules["toc"]["divider_layouts"] and t["size"] >= 40)
                                      or (p.is_exempt(exempt) and not _is_toc(p.layout) and t["size"] >= 20)]
            if not any(core[:6] in ct or _similar(core, ct.split("/")[0]) > 0.5 for ct in cands):
                rep.add("WARN", "O01", toc.index, f"목차 항목 '{item}'에 대응하는 장 제목·장 구분을 찾지 못했습니다")
        ranges = [t["text"] for t in toc.texts if re.match(r"toc-\d+-pages", t["group"] or "")]
        last = 0
        for r in ranges:
            m = re.findall(r"\d+", r)
            if not m:
                continue
            a, b = int(m[0]), int(m[-1])
            if a < last or b > len(pages) or a > b:
                rep.add("WARN", "O02", toc.index, f"목차 쪽 범위 '{r}'가 순서·총 장수({len(pages)})와 맞지 않습니다")
            last = b
    elif deck_type in ("lecture", "handout", "kickoff", "final", "seminar", "insight"):
        rep.add("WARN", "O01", 0, "목차 장표가 없습니다(교육·착수·최종·세미나·리포트는 목차 필수)")

    # ---- S: structure
    st = rules["structure"]
    layouts = [p.layout for p in content]
    run_len, prev = 0, None
    for p in content:
        run_len = run_len + 1 if p.layout == prev else 1
        prev = p.layout
        if run_len == st["max_consecutive_same_layout"] + 1:
            rep.add("INFO", "S01", p.index, f"같은 레이아웃이 {run_len}장 연속입니다({p.layout}) — 리듬 점검")
    if layouts:
        top, c = Counter(layouts).most_common(1)[0]
        if c / len(layouts) > st["max_share_single_layout"] and len(layouts) >= 6:
            rep.add("WARN", "S01", 0, f"본문의 {c/len(layouts):.0%}가 한 레이아웃({top})입니다")
    if deck_type:
        req = st["required_layouts"].get(deck_type, [])
        all_layouts = set(p.layout for p in pages)
        for group in req:
            if not any(l.startswith(x) for x in group.split("|") for l in all_layouts):
                rep.add("WARN", "S03", 0, f"{deck_type} 덱 필수 레이아웃 없음: {group.replace('|', ' 또는 ')}")
        closing = st["closing_layouts"].get(deck_type, [])
        tail = [p.layout for p in content[-3:]]
        if closing and not any(l.startswith(c) for l in tail for c in closing):
            rep.add("WARN", "S02", content[-1].index if content else 0, f"{deck_type} 마무리 세트({', '.join(closing)}) 중 하나가 마지막 3장에 없습니다")
    for p in content:
        fm = p.slot_text("final-message") or p.slot_text("synthesis") or p.slot_text("conclusion") or p.slot_text("next-action")
        if fm and p.governing and _similar(fm["text"], p.governing["text"]) >= 0.6:
            rep.add("WARN", "S04", p.index, "결론 박스가 거버닝과 거의 같습니다 — '그래서 무엇을 할지'만")

    summary = {
        "project": str(project), "family": family, "deck_type": deck_type, "register": main_reg,
        "pages": len(pages), "content_pages": len(content),
        "errors": rep.count("ERROR"), "warnings": rep.count("WARN"), "infos": rep.count("INFO"),
        "layouts": dict(Counter(p.layout for p in pages)),
    }
    return rep, summary


def write_report(project: Path, rep: Report, summary: dict, json_out: Path | None):
    out_dir = project / "analysis"
    out_dir.mkdir(exist_ok=True)
    md = [f"# INNerGEN QA/QC 보고 — {project.name}", "",
          f"- 계열: {summary.get('family')} · 덱 유형: {summary.get('deck_type') or '미지정'} · 거버닝 문체 기준: {summary.get('register')}",
          f"- 장수 {summary.get('pages')} (본문 {summary.get('content_pages')}) · ERROR {summary.get('errors')} · WARN {summary.get('warnings')} · INFO {summary.get('infos')}", "",
          "| 수준 | 코드 | 장 | 내용 |", "|---|---|---|---|"]
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for it in sorted(rep.items, key=lambda i: (order[i["level"]], i["page"], i["code"])):
        md.append(f"| {it['level']} | {it['code']} | {('P%02d' % it['page']) if it['page'] else '덱'} | {it['message']} |")
    md += ["", "코드: C 화면 고정 요소 · G 거버닝 · T 제목 · O 목차 · S 구조. 규칙표: docs/styles/innergen/qaqc-v21.json, 설명: qaqc-v21.md"]
    (out_dir / "innergen_qaqc_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    data = {"summary": summary, "items": rep.items}
    (out_dir / "innergen_qaqc_report.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if json_out:
        json_out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("--deck-type", default=None, help="lecture|handout|seminar|proposal|kickoff|weekly|biweekly|monthly|diagnosis|interim|final|briefing|benchmark|insight")
    ap.add_argument("--register", default="auto", choices=["auto", "external", "internal"])
    ap.add_argument("--family", default=None)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args(argv)
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    rep, summary = run(args.project, args.deck_type, args.register, args.family, rules)
    write_report(args.project, rep, summary, args.json)
    for it in rep.items:
        if it["level"] == "INFO":
            continue
        print(f"[{it['level']}] {it['code']} P{it['page']:02d} {it['message']}")
    print(f"[innergen_qaqc] {summary.get('pages')} pages · ERROR {summary.get('errors')} · WARN {summary.get('warnings')} · INFO {summary.get('infos')} · report: {args.project / 'analysis/innergen_qaqc_report.md'}")
    if summary.get("errors") or (args.strict and summary.get("warnings")):
        print("[innergen_qaqc] FAIL")
        return 1
    print("[innergen_qaqc] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
