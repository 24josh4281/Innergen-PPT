#!/usr/bin/env python3
"""
PPT Master - INNerGEN QA/QC gate (uniformity + writing rules)

Checks a finished (or in-progress) SVG deck against the INNerGEN design rules
in docs/styles/innergen: family chrome geometry (v17/v22), governing grammar
(v11/v20, one line since v22), title system (v4/v5/v20), TOC ↔ chapter
consistency (v5/v20) and the TOC built as one native table (O03, ERROR), structure and closing set per deck type (v20), minimum
text sizes (v18/v22), citation line (v16), and - since v25 - the table of
contents and must-have content per report type and business type
(content-requirements-v25.json, via innergen_content_check.py). It complements
svg_quality_checker.py (SVG/PPTX contract) with the *content* and *uniformity* layer.

Usage:
    python3 scripts/innergen_qaqc.py <project_path> [--deck-type lecture] [--business-type inventory]
                                     [--register auto|external|internal]
                                     [--family innergen_lecture|innergen_lecture_v20|innergen_business|innercarry]
                                     [--strict] [--json <out.json>]

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
import innergen_content_check as content_check  # noqa: E402
from omml_math import FORMULA_LIKE, WORD_FORMULA, EquationError, parse_latex  # noqa: E402

REPO = _SCRIPTS_DIR.parents[min(3, len(_SCRIPTS_DIR.parents) - 1)]
RULES_PATH = REPO / "docs/styles/innergen/qaqc-v21.json"
# Standalone skill bundles (build_chat_skill.py) ship the rule table beside the skill.
if not RULES_PATH.is_file():
    RULES_PATH = _SCRIPTS_DIR.parent / "references/qaqc-v21.json"


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


def _near(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def _layout_from_filename(stem: str) -> str:
    """Flat (chat) edition: SVGs carry no data-pptx-layout, so read the layout id
    from the page file name `NN_<layout_id>.svg` (e.g. `05_s24_project_overview`)
    and return it hyphenated (`s24-project-overview`) for substring matching."""
    m = re.match(r"^\d+_((?:0\d[a-z]?|s\d{2})_[a-z0-9_]+?)(?:__.*)?$", stem)
    if not m:
        return ""
    return re.sub(r"^(?:0\d[a-z]?)_", "", m.group(1)).replace("_", "-")


# ---------------------------------------------------------------- page model
class Page:
    def __init__(self, path: Path, index: int, fam: dict | None = None):
        self.path, self.index = path, index
        self.root = ET.parse(str(path)).getroot()
        self.layout = self.root.get("data-pptx-layout") or _layout_from_filename(path.stem)
        self.role = self.root.get("data-pptx-page-role") or ""
        self.texts: list[dict] = []
        self.rects: list[dict] = []
        self.images: list[dict] = []
        self.lines: list[dict] = []
        self._parent_map = None
        self._walk(self.root, {})
        self.title = self.governing = self.source = self.footer_label = self.page_number = None
        if fam:
            self.bind(fam)

    def bind(self, fam: dict):
        t, gv, src, ft = fam["title"], fam["governing"], fam["source"], fam["footer"]
        tol = t.get("tolerance", 3)
        self.title = self._pick(lambda x: _near(x["y"], t["baseline"], tol) and _near(x["size"], t["size"], 1.5) and x["x"] < fam["canvas"][0] * 0.6)
        g_baselines = [gv["baseline"]] + ([gv["baseline_two_lines"]] if gv.get("baseline_two_lines") else [])
        self.governing = self._pick(lambda x: any(_near(x["y"], b, gv.get("tolerance", 3)) for b in g_baselines) and _near(x["size"], gv["size"], 1.5) and x["x"] >= gv["text_x"] - 4)
        self.source = self._pick(lambda x: _near(x["y"], src["baseline"], src.get("tolerance", 3)) and x["size"] <= src["size"] + 2)
        self.footer_label = self._pick(lambda x: _near(x["y"], ft["label"]["baseline"], 3) and _near(x["x"], ft["label"]["x"], 6))
        self.page_number = self._pick(lambda x: _near(x["y"], ft["page_number"]["baseline"], 3) and x["anchor"] == ft["page_number"].get("anchor", "end") and _near(x["x"], ft["page_number"]["x"], 6))

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
            self.images.append({"x": _num(el.get("x"), 0.0), "y": _num(el.get("y"), 0.0), "w": _num(el.get("width"), 0.0), "h": _num(el.get("height"), 0.0)})
        elif tag == "line":
            self.lines.append({"y1": _num(el.get("y1"), 0.0), "y2": _num(el.get("y2"), 0.0), "x1": _num(el.get("x1"), 0.0), "x2": _num(el.get("x2"), 0.0)})
        for ch in el:
            if _local(ch.tag) in ("metadata", "defs", "style"):
                continue
            self._walk(ch, style)

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

    def has_atom(self, atom: dict, tol=1.5) -> bool:
        kind = atom["type"]
        if kind == "rect":
            return any(_near(r["x"], atom["x"], tol) and _near(r["y"], atom["y"], tol) and _near(r["w"], atom["w"], tol) and _near(r["h"], atom["h"], tol) for r in self.rects)
        if kind == "line":
            return any(_near(l["y1"], atom["y"], tol) and _near(l["y2"], atom["y"], tol) for l in self.lines)
        if kind == "image":
            return any(_near(i["x"], atom["x"], tol) and _near(i["y"], atom["y"], tol) for i in self.images)
        return True


# ---------------------------------------------------------------- report
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


def detect_family(pages: list[Page], declared: str | None, rules: dict) -> str:
    fams = rules["families"]
    if declared in fams and declared != "innergen_lecture":
        return declared
    # innergen_lecture: tell the v22 compact chrome from the v20 two-line chrome by the title baseline.
    content = [p for p in pages if not p.is_exempt(fams["innergen_lecture"]["exempt_layout_keywords"])]
    sample = content[:3] or pages[:3]
    for key in ("innergen_lecture", "innergen_lecture_v20"):
        det = fams[key]["detect"]
        hits = sum(1 for p in sample if any(_near(t["y"], det["title_baseline"], 3) and _near(t["size"], det["title_size"], 1.5) for t in p.texts))
        if hits >= max(1, len(sample) // 2):
            return key
    return declared or "innergen_lecture"


def _layout_in(layout: str, group: str) -> bool:
    return any(x in layout for x in group.split("|"))


def run(project: Path, deck_type: str | None, register: str, family: str | None, rules: dict,
        business_type: str | None = None) -> tuple[Report, dict]:
    rep = Report()
    svg_dir = project / "svg_output"
    pages = [Page(p, i + 1) for i, p in enumerate(sorted(svg_dir.glob("*.svg")))]
    if not pages:
        rep.add("ERROR", "P00", 0, "svg_output/ 에 SVG가 없습니다")
        return rep, {}

    prof_file = project / "design_profile_v17.json"
    if family is None and prof_file.exists():
        try:
            family = json.loads(prof_file.read_text(encoding="utf-8")).get("family")
        except Exception:  # noqa: BLE001
            family = None
    family = detect_family(pages, family, rules)
    fam = rules["families"][family]
    for p in pages:
        p.bind(fam)
    spec = project / "design_spec.md"
    spec_text = spec.read_text(encoding="utf-8") if spec.exists() else ""
    if deck_type is None and spec_text:
        m = (re.search(r"deck_type\*{0,2}\s*\|?\s*[:|]\s*\**(\w+)", spec_text)
             or re.search(r"innergen_report_type\*{0,2}\s*\|?\s*[:|]\s*`?\**(\w+)", spec_text))
        deck_type = m.group(1) if m else None
    if business_type is None and spec_text:
        m = re.search(r"innergen_business_type\*{0,2}\s*\|?\s*[:|]\s*`?\**(\w+)", spec_text)
        business_type = m.group(1) if m else None
    content_spec = content_check.load_spec()
    if content_spec is not None:
        deck_type = content_check.resolve(content_spec, deck_type, None)[0]
    exempt = fam["exempt_layout_keywords"]
    content = [p for p in pages if not p.is_exempt(exempt)]

    lock = project / "spec_lock.md"
    palette = set()
    if lock.exists():
        palette = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}", lock.read_text(encoding="utf-8"))}
    palette |= {"#FFFFFF", "NONE", ""}

    # ---- C: chrome / geometry
    gv = fam["governing"]
    for p in content:
        for atom in fam.get("atoms", []):
            if not p.has_atom(atom):
                rep.add("ERROR", "C01", p.index, f"고정 요소 '{atom['id']}'({atom['type']})가 기준 위치에 없습니다")
        if p.title is None:
            rep.add("ERROR", "C02", p.index, f"제목(x{fam['title']['x']}, 기준선 {fam['title']['baseline']}, {fam['title']['size']}px)을 찾지 못했습니다")
        else:
            t = p.title
            if abs(t["x"] - fam["title"]["x"]) > fam["title"].get("tolerance", 3) or t["fill"] != fam["title"]["fill"].upper() or t["weight"] not in ("700", "bold"):
                rep.add("WARN", "C02", p.index, f"제목 위치·색·굵기가 기준과 다릅니다 (x={t['x']:g}, fill={t['fill']}, weight={t['weight']})")
        if gv.get("box"):
            gb = gv["box"]
            if not any(abs(r["x"] - gb[0]) <= 1 and abs(r["y"] - gb[1]) <= 1 and abs(r["w"] - gb[2]) <= 1 and abs(r["h"] - gb[3]) <= 1 for r in p.rects):
                rep.add("ERROR", "C03", p.index, f"거버닝 박스({','.join(str(v) for v in gb)})가 없습니다")
        if p.governing is not None:
            g = p.governing
            if g["fill"] != gv["fill"].upper():
                rep.add("WARN", "C03", p.index, f"거버닝 색이 기준({gv['fill']})과 다릅니다: {g['fill']}")
            if gv.get("weight_bold") and g["weight"] not in ("700", "bold"):
                rep.add("WARN", "C03", p.index, "거버닝은 볼드여야 합니다")
        if p.source is None:
            key = p.layout.lower()
            if any(k in key for k in rules["source_line"]["required_on_layouts_with"]):
                rep.add("WARN", "C04", p.index, f"근거·표·차트 장표인데 출처 줄(y{fam['source']['baseline']})이 없습니다")
        else:
            if not re.match(rules["source_line"]["format_regex"], p.source["text"]):
                rep.add("WARN", "C04", p.index, f"출처 줄은 '출처:'로 시작해야 합니다: {p.source['text'][:40]}")
            if abs(p.source["size"] - fam["source"]["size"]) > 1.5:
                rep.add("WARN", "C04", p.index, f"출처 줄 크기 {p.source['size']:g}px (기준 {fam['source']['size']}px)")
        if p.page_number is None:
            rep.add("ERROR", "C05", p.index, "페이지 번호가 기준 위치에 없습니다")
        elif p.page_number["text"].strip() != str(p.index):
            rep.add("ERROR", "C05", p.index, f"페이지 번호 '{p.page_number['text']}' ≠ 실제 순번 {p.index}")
    labels = Counter(p.footer_label["text"] for p in content if p.footer_label)
    if len(labels) > 1:
        rep.add("WARN", "C05", 0, f"푸터·섹션 라벨이 여러 종류입니다: {dict(labels)}")

    # ---- fonts & colors
    fams_ok = rules["font"]["required_families"]
    for p in pages:
        for t in p.texts:
            if t["family"] and not any(f in t["family"] for f in fams_ok):
                rep.add("ERROR", "C08", p.index, f"글꼴 '{t['family'][:30]}' — 허용 가족({', '.join(fams_ok)}) 아님")
                break
        ft = fam["footer"]

        def _limit(t):
            in_footer = _near(t["y"], ft["label"]["baseline"], 4) or _near(t["y"], ft["page_number"]["baseline"], 4)
            return fam["min_px"]["footer"] if in_footer else fam["min_px"]["content"]
        small = [t for t in p.texts if t["text"] and 0 < t["size"] < _limit(t) - 0.05]
        for t in small[:3]:
            rep.add("WARN", "C06", p.index, f"글자 {t['size']:g}px < {_limit(t)}px: '{t['text'][:24]}'")
        if palette:
            off = sorted({t["fill"] for t in p.texts if t["fill"] and t["fill"] not in palette} | {r["fill"] for r in p.rects if r["fill"] and r["fill"] not in palette})
            if off:
                rep.add("WARN", "C07", p.index, f"spec_lock 밖의 색: {', '.join(off[:5])}")

    # ---- G: governing
    gr = rules["governing"]
    regs = Counter()
    seen: list[tuple[int, str]] = []
    max_lines = int(gv.get("max_lines", 1))
    one_line_chars = int(gv["inner_width"] / gv["size"] * gr.get("line_fill_ratio", 0.97))
    for p in content:
        g = p.governing
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
        if n > max_lines:
            rep.add("ERROR", "G04", p.index, f"거버닝이 {n}줄입니다(최대 {max_lines}줄)")
        cnt = len(text.replace(" ", ""))
        for ln in g["lines"]:
            if _glyph_width(ln, g["size"]) > gv["inner_width"]:
                rep.add("WARN", "G04", p.index, f"거버닝이 영역 폭({gv['inner_width']}px)을 넘습니다: '{ln[:30]}…'")
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
        return any(layout.startswith(x) for x in rules["toc"]["layouts"]) or layout in ("toc", "toc-pages")

    def _toc_page(p):
        """Layout key, page role or file name (flat hand-drawn pages carry no layout)."""
        name = p.path.stem.lower().split("__")[0]  # `NN_<layout>__<label>`: the label may say 목차도식
        parts = re.split(r"[_\-\s]+", name)
        return (_is_toc(p.layout) or "toc" in p.role.lower()
                or any(k in parts for k in rules["toc"].get("file_keywords", ["toc", "목차"])))

    def _slot(t, rx):
        return any(re.match(rx, s or "") for s in (t["group"], t["id"]))

    toc_pages = [p for p in pages if _toc_page(p)]
    nt = rules["toc"].get("native_table", {"required": True, "level": "ERROR"})
    if nt.get("required", True):
        for p in toc_pages:
            if not any((el.get("data-pptx-native") or "").strip() == "table" for el in p.root.iter()):
                rep.add(nt.get("level", "ERROR"), "O03", p.index,
                        "목차가 표가 아닙니다 — 행 간격으로 놓은 글상자는 아래가 비고 세로 가운데 정렬이 안 됩니다. "
                        "목차 템플릿(표) 또는 data-pptx-native=\"table\"(셀 valign ctr, 행이 바닥선까지)로 바꾸세요")
    if toc_pages:
        toc = toc_pages[0]
        items = [t["text"] for t in toc.texts if _slot(t, r"toc-(item-)?\d+-title")]
        chapter_titles = [t for _, t in titles]
        for item in items:
            core = re.sub(tr["numbering_regex"], "", item).strip(" ./-–")
            if len(core) < rules["toc"]["match_min_chars"]:
                continue
            cands = chapter_titles + [t["text"] for p in pages for t in p.texts
                                      if (p.layout in rules["toc"]["divider_layouts"] and t["size"] >= 24)
                                      or (p.is_exempt(exempt) and not _is_toc(p.layout) and t["size"] >= 14)]
            if not any(core[:6] in ct or _similar(core, ct.split("/")[0]) > 0.5 for ct in cands):
                rep.add("WARN", "O01", toc.index, f"목차 항목 '{item}'에 대응하는 장 제목·장 구분을 찾지 못했습니다")
        ranges = [t["text"] for t in toc.texts if _slot(t, r"toc-\d+-pages")]
        last = 0
        for r in ranges:
            m = re.findall(r"\d+", r)
            if not m:
                continue
            a, b = int(m[0]), int(m[-1])
            if a < last or b > len(pages) or a > b:
                rep.add("WARN", "O02", toc.index, f"목차 쪽 범위 '{r}'가 순서·총 장수({len(pages)})와 맞지 않습니다")
            last = b
    elif deck_type in ("lecture", "handout", "kickoff", "final", "seminar", "insight") and not (
            content_spec is not None and deck_type in content_spec["report_types"]):  # R01 reports it
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
    # R01 (content-requirements) supersedes S03 for the report types it covers.
    covered = content_spec is not None and deck_type in content_spec["report_types"]
    if deck_type:
        all_layouts = set(p.layout for p in pages)
        for group in ([] if covered else st["required_layouts"].get(deck_type, [])):
            if not any(_layout_in(l, group) for l in all_layouts):
                rep.add("WARN", "S03", 0, f"{deck_type} 덱 필수 레이아웃 없음: {group.replace('|', ' 또는 ')}")
        closing = st["closing_layouts"].get(deck_type, [])
        tail = [p.layout for p in content[-3:]]
        if closing and not any(c in l for l in tail for c in closing):
            rep.add("WARN", "S02", content[-1].index if content else 0, f"{deck_type} 마무리 세트({', '.join(closing)}) 중 하나가 마지막 3장에 없습니다")
    for p in content:
        fm = p.slot_text("final-message") or p.slot_text("synthesis") or p.slot_text("conclusion") or p.slot_text("next-action")
        if fm and p.governing and _similar(fm["text"], p.governing["text"]) >= 0.6:
            rep.add("WARN", "S04", p.index, "결론 박스가 거버닝과 거의 같습니다 — '그래서 무엇을 할지'만")

    # ---- M: editable equations (v30). Formulas must be data-pptx-equation
    # carriers so they export as native OMML; reduction decks are strict.
    strict_math = (business_type or "").startswith("reduction")
    for p in pages:
        carriers = 0
        for t in p.texts:
            latex = t["el"].get("data-pptx-equation")
            if latex is not None:
                carriers += 1
                try:
                    parse_latex(latex)
                except EquationError as exc:
                    rep.add("ERROR", "M01", p.index, f"수식 LaTeX를 OMML로 바꿀 수 없습니다({t['id'] or '-'}): {exc}")
                continue
            for line in t["lines"]:
                if FORMULA_LIKE.search(line):
                    rep.add("ERROR" if strict_math else "WARN", "M02", p.index,
                            f"수식이 일반 텍스트입니다 — data-pptx-equation으로 바꾸세요: '{line[:40]}'")
                elif strict_math and len(line) <= 120 and WORD_FORMULA.search(line):
                    rep.add("WARN", "M02", p.index,
                            f"말로 쓴 산정식으로 보입니다 — 편집 가능한 수식(data-pptx-equation)으로 바꾸세요: '{line[:40]}'")
        page_text = " ".join(t["text"] for t in p.texts)
        if strict_math and carriers == 0 and re.search(r"모니터링\s?(인자|변수|항목)|Monitoring\s+Parameter", page_text):
            rep.add("WARN", "M03", p.index, "모니터링 인자 장표에 수식 기호가 없습니다 — 인자 열은 data-pptx-equation 기호로")

    # ---- R/B/Q: TOC and must-have content per report type × business type (v25)
    content_res = {}
    if content_spec is not None:
        content_res = content_check.check(content_check.pages_from_svg(pages), deck_type, business_type,
                                          content_spec, rep.add)
        business_type = content_res.get("business_type") or business_type

    summary = {
        "project": str(project), "family": family, "deck_type": deck_type, "business_type": business_type,
        "register": main_reg, "sections_missing": content_res.get("sections_missing", []),
        "pages": len(pages), "content_pages": len(content),
        "errors": rep.count("ERROR"), "warnings": rep.count("WARN"), "infos": rep.count("INFO"),
        "layouts": dict(Counter(p.layout for p in pages)),
    }
    return rep, summary


def write_report(project: Path, rep: Report, summary: dict, json_out: Path | None):
    out_dir = project / "analysis"
    out_dir.mkdir(exist_ok=True)
    md = [f"# INNerGEN QA/QC 보고 — {project.name}", "",
          f"- 계열: {summary.get('family')} · 덱 유형: {summary.get('deck_type') or '미지정'} · 사업 성격: {summary.get('business_type') or '미지정'} · 거버닝 문체 기준: {summary.get('register')}",
          f"- 장수 {summary.get('pages')} (본문 {summary.get('content_pages')}) · ERROR {summary.get('errors')} · WARN {summary.get('warnings')} · INFO {summary.get('infos')}", "",
          "| 수준 | 코드 | 장 | 내용 |", "|---|---|---|---|"]
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for it in sorted(rep.items, key=lambda i: (order[i["level"]], i["page"], i["code"])):
        md.append(f"| {it['level']} | {it['code']} | {('P%02d' % it['page']) if it['page'] else '덱'} | {it['message']} |")
    md += ["", "코드: C 화면 고정 요소 · G 거버닝 · T 제목 · O 목차 · S 구조 · R 보고 유형 목차·필수 내용 · B 사업 성격 필수 내용 · Q 잔재·금지 표현 · M 편집 가능 수식. "
           "규칙표: qaqc-v21.json(C·G·T·O·S), content-requirements-v25.json(R·B·Q), 설명: qaqc-v21.md, content-requirements-v25.md"]
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
    ap.add_argument("--business-type", default=None, help="cdp_disclosure|regulatory|reduction|inventory|lca_product|climate_risk|esg_rating|climate_education|climate_tech (default: design_spec.md innergen_business_type)")
    ap.add_argument("--register", default="auto", choices=["auto", "external", "internal"])
    ap.add_argument("--family", default=None, help="innergen_lecture|innergen_lecture_v20|innergen_business|innercarry (default: design_profile_v17.json + chrome detection)")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args(argv)
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    rep, summary = run(args.project, args.deck_type, args.register, args.family, rules, args.business_type)
    write_report(args.project, rep, summary, args.json)
    for it in rep.items:
        if it["level"] == "INFO":
            continue
        print(f"[{it['level']}] {it['code']} P{it['page']:02d} {it['message']}")
    print(f"[innergen_qaqc] family {summary.get('family')} · {summary.get('deck_type') or '-'} × {summary.get('business_type') or '-'} · {summary.get('pages')} pages · ERROR {summary.get('errors')} · WARN {summary.get('warnings')} · INFO {summary.get('infos')} · report: {args.project / 'analysis/innergen_qaqc_report.md'}")
    if summary.get("errors") or (args.strict and summary.get("warnings")):
        print("[innergen_qaqc] FAIL")
        return 1
    print("[innergen_qaqc] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
