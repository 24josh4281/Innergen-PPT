#!/usr/bin/env python3
"""
INNerGEN standard pages - writes the fixed pages every company deck repeats
(cover, company overview table, business-area grid, key numbers, closing)
straight from the company-facts ledger into a scaffolded project's svg_output/.

Run start_deck.py first; this script fills the project's own templates/, so the
geometry and colors always follow the family (innergen_business 16:9,
innercarry 4:3, innergen_lecture 13:9). Page numbers follow the standard tables
in references/standard-decks-v28.md (§A company_intro, §B innercarry_intro);
the other pages are still written by hand.

Ledger values marked `needs_confirm` (for example 감축실적 250만 vs 300만 톤) are
left out unless --include-unconfirmed is given, and every omission or image the
page still needs is listed at the end. Client logos are never invented: pass
--client-logo to add the 주요 고객 row.

Usage:
    python3 scripts/innergen_standard_pages.py /tmp/deck --deck company_intro
    python3 scripts/innergen_standard_pages.py /tmp/deck --deck innercarry_intro --date "2026. 10."
    python3 scripts/innergen_standard_pages.py /tmp/deck --deck company_intro --pages cover,ending --force
    python3 scripts/innergen_standard_pages.py /tmp/deck --deck company_intro --client-logo clients.png

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import innergen_facts_check as facts_check  # noqa: E402

LINE_HEIGHT = 1.4
SOURCE_LINE = "출처: 이너젠 내부 자료(’26.9월 기준)"

# Standard page numbers and copy (standard-decks-v28.md §A, §B). Governing lines
# are the reviewed drafts there (one line, ≤38 characters without spaces).
DECKS = {
    "company_intro": {
        "section": "회사 소개",
        "pages": {
            "cover": (1, "01_cover", {"title": "㈜ 이너젠 소개자료"}),
            "overview": (2, "03e_content_table", {
                "title": "1. 회사 개요",
                "governing": "이너젠은 5개 분야에 전문성을 갖춘 기후변화 컨설팅사입니다."}),
            "areas": (4, "s18_keyword_grid", {
                "title": "3. 사업 분야",
                "governing": "이너젠은 규제 대응부터 RE100 조달까지 탄소 업무 전 영역을 한 팀이 지원합니다."}),
            "kpi": (5, "03f_content_kpi", {
                "title": "3-1. 규제 대응 / 탄소중립 전략",
                "governing": "이너젠은 18개+ 업종 산정 실적으로 국가별 GHG 규제에 대응합니다."}),
            "ending": (13, "04_ending", {"title": "Thank you."}),
        },
    },
    "innercarry_intro": {
        "section": "PART 00 회사소개",
        "pages": {
            "cover": (1, "01_cover", {"title": "이너젠 및 이너캐리 소개자료"}),
            "overview": (3, "03e_content_table", {
                "title": "이너젠 회사 개요",
                "governing": "이너젠은 온실가스 규제·공시 대응을 돕는 기후변화 컨설팅사입니다."}),
            "areas": (4, "s18_keyword_grid", {
                "title": "이너젠 사업 분야",
                "governing": "이너젠은 컨설팅 부문 5개 분야와 IT 부문 솔루션을 함께 제공합니다."}),
            "ending": (23, "04_ending", {"title": "Thank you."}),
        },
    },
}

# Short area labels, in the order and wording of messages.company_overview
# ('규제대응 / 감축사업 / 제품 LCA / 기후공시 / RE100').
AREA_SHORT = {"regulatory": "규제대응", "credit": "감축사업", "lca": "제품 LCA",
              "disclosure": "기후공시", "re100": "RE100"}


# ---------------------------------------------------------------- SVG helpers

_ATTR_RE = re.compile(r'([\w:-]+)=(?:"([^"]*)"|\'([^\']*)\')')


def _attrs(tag: str) -> dict:
    return {m.group(1): m.group(2) if m.group(2) is not None else m.group(3) for m in _ATTR_RE.finditer(tag)}


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _num(v, default=0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _canvas(svg: str) -> tuple[float, float]:
    m = re.search(r'viewBox="[\d.\s]*?\s([\d.]+)\s+([\d.]+)"', svg)
    return (float(m.group(1)), float(m.group(2))) if m else (960.0, 540.0)


def _boxes(svg: str) -> dict:
    """id -> {x, y, w, h, fill, stroke, kind} for rects and images."""
    out = {}
    for m in re.finditer(r"<(rect|image)\b[^>]*>", svg):
        a = _attrs(m.group(0))
        if "id" not in a:
            continue
        out[a["id"]] = {"x": _num(a.get("x")), "y": _num(a.get("y")), "w": _num(a.get("width")),
                        "h": _num(a.get("height")), "fill": a.get("fill"), "stroke": a.get("stroke"),
                        "kind": m.group(1)}
    return out


def text_width(s: str, size: float, bold: bool = False) -> float:
    """Rough advance width for IBM Plex Sans KR / Pretendard."""
    w = 0.0
    for ch in s:
        o = ord(ch)
        if 0x1100 <= o <= 0x11FF or 0x3000 <= o <= 0x9FFF or 0xAC00 <= o <= 0xD7AF or 0xFF00 <= o <= 0xFFEF:
            w += 1.0
        elif ch == " ":
            w += 0.28
        elif ch.isupper() or ch.isdigit():
            w += 0.62
        elif ch.isalpha():
            w += 0.52
        else:
            w += 0.38
    return w * size * (1.04 if bold else 1.0)


def wrap(s: str, width: float, size: float, bold: bool = False) -> list[str]:
    """Greedy word wrap on spaces (Korean words stay whole); keeps a 6% margin
    because PowerPoint fonts run wider than the estimate."""
    width *= 0.94
    lines, cur = [], ""
    for word in s.split(" "):
        trial = f"{cur} {word}" if cur else word
        if cur and text_width(trial, size, bold) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


class Page:
    def __init__(self, svg: str):
        self.svg = svg
        self.W, self.H = _canvas(svg)
        self.boxes = _boxes(svg)
        self.notes: list[str] = []

    # -- geometry
    def _container(self, x: float, y: float, skip=("master-bg",)):
        best = None
        for bid, b in self.boxes.items():
            if bid in skip or b["kind"] != "rect":
                continue
            if b["x"] <= x <= b["x"] + b["w"] and b["y"] <= y <= b["y"] + b["h"]:
                if best is None or b["w"] * b["h"] < best[1]["w"] * best[1]["h"]:
                    best = (bid, b)
        return best

    def _carrier(self, slot: str):
        m = re.search(r'<g id="([\w-]+)">\s*<text\b([^>]*)>\{\{' + slot + r'\}\}</text>\s*</g>', self.svg)
        return m

    def _box_for(self, a: dict) -> tuple[float, float, float, float, bool]:
        """(left, right, top, bottom, contained) usable area around a carrier."""
        x, y, fs = _num(a.get("x")), _num(a.get("y")), _num(a.get("font-size"), 14)
        anchor = a.get("text-anchor", "start")
        cont = self._container(x, y - fs * 0.4)
        if cont and not (cont[1]["w"] >= self.W * 0.95 and cont[1]["h"] >= self.H * 0.95):
            b = cont[1]
            pad = max(8.0, x - b["x"]) if anchor == "start" else 8.0
            left, right = b["x"] + (pad if anchor != "start" else x - b["x"]), b["x"] + b["w"] - pad
            if anchor == "start":
                left = x
            return left, right, b["y"], b["y"] + b["h"], True
        margin = max(24.0, min(x, self.W - x)) if anchor != "middle" else 36.0
        left, right = (x, self.W - margin) if anchor == "start" else (margin, self.W - margin)
        for b in self.boxes.values():  # an illustration to the right limits the line
            if b["kind"] == "image" and b["x"] > x and b["y"] <= y <= b["y"] + b["h"]:
                right = min(right, b["x"] - 16)
        return left, right, 0.0, self.H, False

    # -- slots
    def fill(self, slot: str, value, *, center: bool | None = None) -> None:
        """Replace {{slot}} with one or more lines (wrapped to the available width)."""
        m = self._carrier(slot)
        if not m:
            return
        a = _attrs(m.group(2))
        fs = _num(a.get("font-size"), 14)
        bold = a.get("font-weight") in ("700", "bold")
        left, right, top, bottom, contained = self._box_for(a)
        anchor = a.get("text-anchor", "start")
        width = right - left if anchor != "middle" else min(right - _num(a.get("x")), _num(a.get("x")) - left) * 2
        lines: list[str] = []
        for part in ([value] if isinstance(value, str) else value):
            lines.extend(wrap(part, width, fs, bold))
        lh = fs * LINE_HEIGHT
        y0 = _num(a.get("y"))
        if center is None:
            center = contained and anchor == "middle"
        if center and len(lines) > 1:
            y0 -= (len(lines) - 1) * lh / 2
        if y0 + (len(lines) - 1) * lh > bottom - fs * 0.2:
            self.notes.append(f"{slot}: {len(lines)}줄이 영역을 넘을 수 있음 — 문구를 줄이거나 장을 나눔")
        x = a.get("x")
        if len(lines) == 1:  # a single tspan shifts the PPTX text box; keep plain text
            tspans = _esc(lines[0])
        else:
            tspans = "".join(f'<tspan x="{x}" y="{y0 + i * lh:.1f}">{_esc(t)}</tspan>' for i, t in enumerate(lines))
        new_text = re.sub(r'\s(x|y)="[^"]*"', "", m.group(2))
        self.svg = self.svg.replace(m.group(0), f'<g id="{m.group(1)}"><text x="{x}" y="{y0:.1f}"{new_text}>{tspans}</text></g>')

    def drop(self, slot: str, *shape_ids: str) -> None:
        m = self._carrier(slot)
        if m:
            self.svg = self.svg.replace(m.group(0), "")
        for sid in shape_ids:
            self.svg = re.sub(r'<(rect|image|line|text)\b[^>]*\bid="' + re.escape(sid) + r'"[^>]*/>\n?', "", self.svg)
            self.svg = re.sub(r'<text\b[^>]*\bid="' + re.escape(sid) + r'"[^>]*>.*?</text>\n?', "", self.svg)

    def replace_group(self, slot: str, body: str) -> None:
        m = self._carrier(slot)
        if m:
            self.svg = self.svg.replace(m.group(0), f'<g id="{m.group(1)}">{body}</g>')

    def carrier_attrs(self, slot: str) -> dict:
        m = self._carrier(slot)
        return _attrs(m.group(2)) if m else {}

    def leftover(self) -> list[str]:
        return re.findall(r"\{\{([A-Z0-9_]+)\}\}", self.svg)


def _text_el(x, y, s, a: dict, *, size=None, weight=None, fill=None, anchor=None) -> str:
    fam = a.get("font-family", '"Malgun Gothic", sans-serif')
    parts = [f'x="{x:.1f}"', f'y="{y:.1f}"']
    if anchor:
        parts.append(f'text-anchor="{anchor}"')
    parts.append(f"font-family='{fam}'")
    parts.append(f'font-size="{size or a.get("font-size", "13.33")}"')
    parts.append(f'font-weight="{weight or a.get("font-weight", "400")}"')
    parts.append(f'fill="{fill or a.get("fill", "#000000")}"')
    return f"<text {' '.join(parts)}>{_esc(s)}</text>"


# ---------------------------------------------------------------- ledger

class Ledger:
    def __init__(self, facts: dict, include_unconfirmed: bool):
        self.f = facts
        self.include = include_unconfirmed
        self.flags: list[str] = []

    def v(self, *path, default=""):
        node = self.f
        for p in path:
            if isinstance(node, list):
                node = next((x for x in node if isinstance(x, dict) and x.get("id") == p), {})
            else:
                node = node.get(p, {}) if isinstance(node, dict) else {}
        if isinstance(node, dict):
            return node.get("value", default)
        return node

    def status(self, *path) -> str:
        node = self.f
        for p in path:
            if isinstance(node, list):
                node = next((x for x in node if isinstance(x, dict) and x.get("id") == p), {})
            else:
                node = node.get(p, {}) if isinstance(node, dict) else {}
        return node.get("status", "confirmed") if isinstance(node, dict) else "confirmed"

    def ok(self, label: str, *path) -> bool:
        """True when the value may go on a page; records the decision."""
        st = self.status(*path)
        if st == "confirmed":
            return True
        if self.include:
            self.flags.append(f"확인 필요 값 사용: {label}")
            return True
        self.flags.append(f"확인 필요라서 뺌: {label} (--include-unconfirmed로 넣음)")
        return False

    def metric(self, mid: str) -> dict:
        return next((m for m in self.f.get("metrics", []) if m.get("id") == mid), {})


# ---------------------------------------------------------------- page builders

def build_cover(p: Page, L: Ledger, deck: str, spec: dict, opts) -> None:
    label_attrs = p.carrier_attrs("COVER_MESSAGE")  # read before the slot is filled
    p.fill("TITLE", spec["title"])
    if deck == "innercarry_intro":
        p.fill("SUBTITLE", L.v("messages", "innercarry_subtitle"))
        p.fill("COVER_MESSAGE", L.v("messages", "innercarry_tagline"))
        p.fill("AUTHOR", f"{L.v('company', 'legal_name')} · {L.v('company', 'website')}")
    else:
        p.fill("SUBTITLE", L.v("messages", "company_hashtags"))
        p.fill("COVER_MESSAGE", L.v("messages", "company_tagline"))
        p.fill("AUTHOR", L.v("company", "name_ko"))
    order = ("inventory_projects", "industries", "methodologies")
    mets = [L.metric(m) for m in order if L.metric(m)]
    dividers = sorted(_num(_attrs(t).get("x1")) for t in re.findall(r'<line\b[^>]*id="cover-hero-divider-\d"[^>]*/>', p.svg))
    a = p.carrier_attrs("KEY_FIGURES")
    if dividers:  # the 4:3 cover has a three-column figure band: figure + label per column
        x0, y0 = _num(a.get("x")), _num(a.get("y"))
        panel = p.boxes.get("cover-hero-panel", {"x": x0 - 24})
        xs = [x0] + [d + (x0 - panel["x"]) for d in dividers]
        la = label_attrs or a
        body = "".join(_text_el(x, y0 - 8, m["value"], a) + _text_el(x, y0 + 30, m["label"], la, weight="400")
                       for x, m in zip(xs, mets))
        p.replace_group("KEY_FIGURES", body)
    else:  # one line: as many figures as fit the panel, the headline number first
        left, right, *_ = p._box_for(a)
        fs, bold = _num(a.get("font-size"), 29.33), a.get("font-weight") == "700"
        figs = [f"{m['value']} {m['label'].replace(' 및 규제 대응', '')}" for m in mets]
        for n in range(len(figs), 0, -1):
            line = " · ".join(figs[:n])
            if text_width(line, fs, bold) <= (right - left) * 0.94 or n == 1:
                break
        p.fill("KEY_FIGURES", line)
    p.fill("DATE", opts.date)
    if opts.event:
        p.fill("EVENT_NAME", opts.event)
    else:
        p.drop("EVENT_NAME")


def build_overview(p: Page, L: Ledger, deck: str, spec: dict, opts, project: Path) -> None:
    c = lambda k: L.v("company", k)  # noqa: E731
    head = L.f.get("company", {}).get("headcount", {})
    as_of = head.get("as_of", "")
    as_of_txt = f" (’{as_of[2:4]}.{int(as_of[5:7])}월 기준)" if re.match(r"\d{4}-\d{2}", as_of) else ""
    addr = L.f.get("company", {}).get("address", {})
    areas = L.v("business_areas") or []
    rows = [
        ("회사명", f"{c('name_ko')} ({c('name_en')})"),
        ("대표자", c("ceo")),
        ("구성 인원", f"{c('headcount')}{as_of_txt}"),
        ("설립일", c("founded")),
        ("위치", f"({addr.get('postcode')}) {addr.get('value')}" if addr.get("postcode") else addr.get("value", "")),
        ("연락처", f"{c('phone')} · {c('email')} · {c('website')}"),
        ("사업 분야", " · ".join(AREA_SHORT.get(a["id"], a["name"]) for a in areas)),
    ]
    logo = None
    if opts.client_logo:
        src = Path(opts.client_logo)
        (project / "images").mkdir(exist_ok=True)
        dst = project / "images" / src.name
        if src.resolve() != dst.resolve():
            shutil.copyfile(src, dst)
        logo = dst.name
        rows.append(("주요 고객", None))
    else:
        L.flags.append("주요 고객 로고 이미지가 없어 행을 뺌 (--client-logo <파일>로 넣음)")

    a = p.carrier_attrs("EVIDENCE_AREA")
    frame = p.boxes.get("evidence-frame")
    dark = (p.boxes.get("evidence-header") or {}).get("fill") or "#2B4C7E"
    light = (p.boxes.get("final-box") or {}).get("fill") or "#EEF3FF"
    line = (frame or {}).get("stroke") or "#D9D9D9"
    fs = _num(a.get("font-size"), 13.33)
    units = [2 if v is None else 1 for _, v in rows]
    unit_h = frame["h"] / sum(units)
    label_w = round(frame["w"] * 0.18, 1)
    parts, y = [], frame["y"]
    for (label, value), u in zip(rows, units):
        h = unit_h * u
        parts.append(f'<rect x="{frame["x"]:.1f}" y="{y:.1f}" width="{label_w}" height="{h:.1f}" fill="{light}"/>')
        parts.append(_text_el(frame["x"] + 16, y + h / 2 + fs * 0.35, label, a, weight="700", fill=dark))
        vx = frame["x"] + label_w + 16
        if value is None:
            parts.append(f'<image x="{vx:.1f}" y="{y + 6:.1f}" width="{frame["w"] - label_w - 32:.1f}" '
                         f'height="{h - 12:.1f}" xlink:href="../images/{_esc(logo)}" preserveAspectRatio="xMidYMid meet"/>')
        else:
            lines = wrap(value, frame["w"] - label_w - 32, fs)
            lh = fs * LINE_HEIGHT
            y0 = y + h / 2 + fs * 0.35 - (len(lines) - 1) * lh / 2
            inner = (_esc(lines[0]) if len(lines) == 1 else
                     "".join(f'<tspan x="{vx:.1f}" y="{y0 + i * lh:.1f}">{_esc(t)}</tspan>' for i, t in enumerate(lines)))
            parts.append(f'<text x="{vx:.1f}" y="{y0:.1f}" font-family=\'{a.get("font-family")}\' font-size="{fs}" '
                         f'font-weight="400" fill="{a.get("fill", "#000000")}">{inner}</text>')
        y += h
        if y < frame["y"] + frame["h"] - 1:
            parts.append(f'<line x1="{frame["x"]:.1f}" y1="{y:.1f}" x2="{frame["x"] + frame["w"]:.1f}" y2="{y:.1f}" '
                         f'stroke="{line}" stroke-width="1"/>')
    p.replace_group("EVIDENCE_AREA", "".join(parts))
    p.fill("PAGE_TITLE", spec["title"])
    p.fill("KEY_MESSAGE", spec["governing"])
    p.fill("EVIDENCE_CAPTION", "회사 개요")
    p.fill("FINAL_MESSAGE", L.v("messages", "slogan"))
    p.fill("SOURCE", SOURCE_LINE)


def build_areas(p: Page, L: Ledger, deck: str, spec: dict, opts) -> None:
    areas = (L.v("business_areas") or [])[:5]
    p.fill("PAGE_TITLE", spec["title"])
    p.fill("KEY_MESSAGE", spec["governing"])
    for i, a in enumerate(areas, 1):
        p.fill(f"QUESTION_{i}", AREA_SHORT.get(a["id"], a["name"]))
        p.fill(f"CELL_{i}_1", a["name"])
        p.fill(f"CELL_{i}_2", a["tags"].replace(" / ", " · ").replace(", ", " · "))
    if deck == "company_intro":
        # The third row points at each area's detail section (3-1 … 3-5 in §A).
        for i in range(1, len(areas) + 1):
            p.fill(f"CELL_{i}_3", f"3-{i} 상세")
    else:
        # INNerCarry deck: one strip across row 3 carries the IT division (§B p4).
        first, last = p.boxes.get("cell-1-3-bg"), p.boxes.get("cell-5-3-bg")
        a = p.carrier_attrs("CELL_1_3")
        for i in range(1, 6):
            p.drop(f"CELL_{i}_3", f"cell-{i}-3-bg")
        it = next((d for d in L.v("company", "divisions") or [] if d.get("name", "").startswith("IT")), None)
        p1, p5, c2 = p.boxes.get("col-1-panel"), p.boxes.get("col-5-panel"), p.boxes.get("cell-1-2-bg")
        if first and last and it and p1 and p5 and c2:
            # Shorten the five column panels to rows 1-2 so the strip sits below them.
            inset = first["x"] - p1["x"]
            new_h = c2["y"] + c2["h"] + inset - p1["y"]
            for i in range(1, 6):
                p.svg = re.sub(r'(<rect id="col-' + str(i) + r'-panel"[^>]*?height=")[^"]*"', rf'\g<1>{new_h:.1f}"', p.svg)
            strip_y = p1["y"] + new_h + inset
            strip = {"x": p1["x"], "y": strip_y, "w": p5["x"] + p5["w"] - p1["x"], "h": p1["y"] + p1["h"] - strip_y}
            p.svg = p.svg.replace("</svg>", f'<rect id="it-division-panel" x="{strip["x"]:.1f}" y="{strip["y"]:.1f}" '
                                  f'width="{strip["w"]:.1f}" height="{strip["h"]:.1f}" fill="{p1["fill"]}"/>\n</svg>')
            first = {"x": strip["x"] + inset, "y": strip["y"] + inset, "w": 0, "h": strip["h"] - 2 * inset,
                     "fill": first["fill"]}
            last = {"x": strip["x"] + strip["w"] - inset, "w": 0}
            x, w = first["x"], last["x"] - first["x"]
            fs = _num(a.get("font-size"), 12)
            lines = [f"{it['name']} ({it['since']}~)"] + wrap(it["desc"], w - 32, fs)
            lh = fs * LINE_HEIGHT
            y0 = first["y"] + first["h"] / 2 + fs * 0.35 - (len(lines) - 1) * lh / 2
            body = (f'<rect id="it-division-bg" x="{x:.1f}" y="{first["y"]:.1f}" width="{w:.1f}" height="{first["h"]:.1f}" '
                    f'fill="{first["fill"] or "#FFFFFF"}"/>'
                    + f'<text x="{x + w / 2:.1f}" y="{y0:.1f}" text-anchor="middle" font-family=\'{a.get("font-family")}\' '
                    f'font-size="{fs}" font-weight="700" fill="{a.get("fill", "#000000")}">'
                    + "".join(f'<tspan x="{x + w / 2:.1f}" y="{y0 + i * lh:.1f}"'
                              + ('' if i == 0 else ' font-weight="400"') + f">{_esc(t)}</tspan>"
                              for i, t in enumerate(lines)) + "</text>")
            p.svg = p.svg.replace("</svg>", f'<g id="it-division">{body}</g>\n</svg>')
            launch = L.f.get("innercarry", {}).get("launch", {})
            if launch.get("status") not in (None, "confirmed"):
                L.flags.append("이너캐리 출시 시점은 원장에 확인 필요로 표시됨 — 사업 분야 IT 부문 문구 확인")
    p.fill("SOURCE", SOURCE_LINE)


def build_kpi(p: Page, L: Ledger, deck: str, spec: dict, opts) -> None:
    p.fill("PAGE_TITLE", spec["title"])
    p.fill("KEY_MESSAGE", spec["governing"])
    for i, mid in enumerate(("industries", "inventory_projects", "methodologies"), 1):
        m = L.metric(mid)
        p.fill(f"KPI_{i}_FIGURE", m.get("value", ""))
        p.fill(f"KPI_{i}_LABEL", m.get("label", ""))
    detail = []
    meth = L.metric("methodologies")
    if meth.get("detail"):
        detail.append(f"· {meth['label']}: {meth['detail']}")
    cred = L.metric("credits_recognized")
    if cred and L.ok(f"감축실적 인정 {cred.get('value')}", "metrics", "credits_recognized"):
        detail.append(f"· {cred['label']} {cred['value']} ({cred.get('detail', '')})")
    for mid in ("verifiers", "kea_experts"):
        m = L.metric(mid)
        if m:
            detail.append(f"· {m['label']} {m['value']}" + (f" ({m['detail']})" if mid == "verifiers" and m.get("detail") else ""))
    p.fill("CONTENT_AREA", detail, center=False)
    p.fill("SOURCE", "출처: 이너젠 내부 실적(’26.9월 기준)")


def build_ending(p: Page, L: Ledger, deck: str, spec: dict, opts) -> None:
    c = lambda k: L.v("company", k)  # noqa: E731
    addr = L.f.get("company", {}).get("address", {})
    address = f"({addr.get('postcode')}) {addr.get('value')}"
    p.fill("THANK_YOU", spec["title"])
    if deck == "innercarry_intro":
        p.fill("CLOSING_MESSAGE", L.v("messages", "innercarry_tagline"))
        p.fill("CONTACT_INFO", [L.v("messages", "slogan").split(" · ")[0],
                                f"CONTACT {c('phone')} · {c('email')}", address], center=None)
    else:
        p.fill("CLOSING_MESSAGE", L.v("messages", "closing_philosophy"))
        p.fill("CONTACT_INFO", [L.v("messages", "closing_we_do"),
                                f"{c('phone')} · {c('email')} · {address}"])


BUILDERS = {"cover": build_cover, "overview": build_overview, "areas": build_areas,
            "kpi": build_kpi, "ending": build_ending}


# ---------------------------------------------------------------- main

def write_pages(project: Path, deck: str, which: list[str], L: Ledger, opts) -> list[tuple]:
    cfg = DECKS[deck]
    tpl_dir, out_dir = project / "templates", project / "svg_output"
    out_dir.mkdir(exist_ok=True)
    results = []
    for key in which:
        if key not in cfg["pages"]:
            results.append((key, None, "이 덱 유형에는 없는 표준 장"))
            continue
        no, layout, spec = cfg["pages"][key]
        tpl = tpl_dir / f"{layout}.svg"
        if not tpl.exists():
            results.append((key, None, f"템플릿 없음: {tpl}"))
            continue
        target = out_dir / f"{no:02d}_{layout}.svg"
        if target.exists() and not opts.force:
            results.append((key, target, "이미 있어 건너뜀 (--force로 덮어씀)"))
            continue
        p = Page(tpl.read_text(encoding="utf-8"))
        if key == "overview":
            build_overview(p, L, deck, spec, opts, project)
        else:
            BUILDERS[key](p, L, deck, spec, opts)
        p.fill("SECTION_NAME", cfg["section"])
        p.fill("PAGE_NUM", str(no))
        left = p.leftover()
        if left:
            p.notes.append(f"남은 자리표시자: {', '.join(left)}")
        target.write_text(p.svg, encoding="utf-8")
        results.append((key, target, "; ".join(p.notes) or "OK"))
    return results


def main(argv=None) -> int:
    try:
        from console_encoding import configure_utf8_stdio
        configure_utf8_stdio()
    except ImportError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path, help="project folder made by start_deck.py")
    ap.add_argument("--deck", required=True, choices=sorted(DECKS))
    ap.add_argument("--pages", default="all", help="comma list: cover,overview,areas,kpi,ending (default: all for the deck)")
    ap.add_argument("--date", default=None, help='cover date (default: this month, e.g. "2026. 10.")')
    ap.add_argument("--event", default=None, help="cover event line (omitted when not given)")
    ap.add_argument("--client-logo", default=None, help="client logo image for the 주요 고객 row")
    ap.add_argument("--include-unconfirmed", action="store_true", help="also use ledger values marked needs_confirm")
    ap.add_argument("--force", action="store_true", help="overwrite pages already in svg_output/")
    ap.add_argument("--facts", type=Path, default=None)
    opts = ap.parse_args(argv)
    if not (opts.project / "templates").is_dir():
        ap.error(f"{opts.project}/templates not found — run start_deck.py --family <family> --out {opts.project} first")
    if opts.date is None:
        today = _dt.date.today()
        opts.date = f"{today.year}. {today.month}."
    facts = facts_check.load_facts(opts.facts)
    if facts is None:
        print(f"[standard_pages] ledger not found: {opts.facts or facts_check.FACTS_PATH}")
        return 2
    L = Ledger(facts, opts.include_unconfirmed)
    which = list(DECKS[opts.deck]["pages"]) if opts.pages == "all" else [s.strip() for s in opts.pages.split(",") if s.strip()]
    for key, path, note in write_pages(opts.project, opts.deck, which, L, opts):
        print(f"[{'PAGE' if path else 'SKIP'}] {key}: {path.name if path else '-'} · {note}")
    for flag in dict.fromkeys(L.flags):
        print(f"[CHECK] {flag}")
    print("[standard_pages] 나머지 장은 standard-decks-v28.md 표대로 직접 작성한 뒤 svg_quality_checker·innergen_qaqc를 돌린다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
