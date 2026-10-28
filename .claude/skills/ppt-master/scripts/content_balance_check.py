#!/usr/bin/env python3
"""
PPT Master - Content Balance Check

Finds recurring spacing defects in authored SVG pages, before PPTX export:

  CB01 상단 쏠림 (top-heavy content block) — the content inside a background
       box (card, KPI tile, callout, row) is anchored to the top, so the gap
       under the last line is much larger than the gap above the first line.
       The fix is to move the whole content group, never each text alone, so
       that the visible block sits in the vertical middle of the box.
  CB02 목차 하단 공백 (TOC bottom void) — the TOC rows end high on the page and
       leave an empty band above the footer line.
  CB03 본문 하단 공백 (page bottom void) — on a content page the lowest body
       element ends far above the source line (or the footer line when there is
       none). Enlarge body text, give rows and cards more height, or add a
       closing message strip so the content zone is used to its floor.
  CB04 목차가 표가 아님 (TOC not a table) — the TOC page has no
       data-pptx-native="table"; rows drawn as spaced text boxes leave a band
       under the last row and cannot center vertically. Use the TOC template
       table (cells valign ctr, rows sharing the zone down to the footer line).
  CB05 카드 안 내용 부족 (sparse card) — a centered text list fills less than
       60% of its card body. `--fix` widens line pitch (≤ 1.9em) and one shared
       paragraph gap until it fills about 75%, then re-centers it.
  CB06 줄마다 개별 개체 (split text lines) — lines or bullets of one card are
       separate <text> objects next to drawn bullet squares, so PowerPoint
       cannot change their line spacing. `--fix` merges them into one <text>
       (bullet → `▪ `/`• ` character, wrapped lines keep the text indent), which
       exports as one text box with native bullets.
  CB07 불필요한 줄바꿈 (premature wrap) — a wrapped line would fit on the line
       above within 95% of the box's free width. `--fix` joins it and keeps the
       block's vertical center. Wide one-line rows (Q1–Q8) are checked too.

Gaps are measured on visible glyph bounds, not on text-box bounds: a line's
ink spans baseline - 0.78em to baseline + 0.12em for Hangul (0.72em / 0.02em
for digits), measured on IBM Plex Sans KR, Pretendard and Malgun Gothic.
`--fix` moves every flagged CB01 content group by one shared delta; x
positions, spacing inside the group and text alignment stay unchanged. CB02
and CB03 are report-only: redistribute the rows or re-plan the page (see the
skill ppt-content-group-centering).

Structured templates: a placeholder slot with
`data-pptx-placeholder-anchor="middle"` may have its carrier moved inside its
unchanged bounds, so `--fix` centers such slots and also flags groups that sit
too low. Fixed `data-pptx-layer="layout"` elements never move in a deck; when a
group mixes them with centered slots, each slot is centered in its own bounds
instead. `--template` is for template authors: it also moves layout-layer
content and keeps each moved carrier inside its bounds. A container rect with
`data-balance-exempt="<reason>"` is skipped and reported as exempt; the same
attribute on the root `<svg>` skips CB03 for a free-layout template page.

Usage:
    python3 scripts/content_balance_check.py <project_path|svg_dir|file.svg> [options]

Examples:
    python3 scripts/content_balance_check.py projects/demo
    python3 scripts/content_balance_check.py projects/demo --fix
    python3 scripts/content_balance_check.py projects/demo/svg_output/03_kpi.svg --json report.json

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

HANGUL_ASCENT, HANGUL_DESCENT = 0.78, 0.12
LATIN_ASCENT, DIGIT_DESCENT, LATIN_DESCENT = 0.72, 0.02, 0.21
EDGE_TOL = 1.5
MIN_IMBALANCE_PX = 6.0
IMBALANCE_RATIO = 0.12
TOC_VOID_RATIO = 0.10
PAGE_VOID_RATIO = 0.06
SOURCE_PREFIXES = ("출처", "자료:", "Source", "source")
NO_BODY_ROLES = ("cover", "ending", "closing", "section", "chapter", "divider", "toc", "표지", "맺음", "간지", "목차")
FULL_SLOT_RATIO = 0.75                  # a slot this tall (vs. its zone) centers on its own
SHIFTABLE = {"text", "rect", "circle", "ellipse", "image", "line", "polygon", "polyline"}
# Card text tidy (CB05–CB07)
SPARSE_FILL = 0.60                      # CB05: a text list filling less than this of its zone
FILL_TARGET = 0.75                      # spread until the list fills this much
MAX_LINE_PITCH = 1.9                    # line pitch cap while spreading (× font size)
MAX_PARA_GAP = 1.8                      # extra paragraph gap cap (× font size)
WRAP_PITCH = 1.75                       # CB07: only lines this close (× size) are a wrapped sentence
LINE_PITCH_MAX = 3.2                    # CB06: same-x texts this close (× size) are one block
MARKER_MAX = 12.0                       # a drawn bullet square/dot is at most this big
WRAP_MARGIN = 0.95                      # CB07: joined line must fit 95% of the free width
BULLET_CHARS = "▪■•●◆·"


def _tag(el) -> str:
    return el.tag.rsplit("}", 1)[-1]


def _f(v, default: float = 0.0) -> float:
    try:
        return float(str(v).replace("px", ""))
    except (TypeError, ValueError):
        return default


@dataclass
class Item:
    el: ET.Element
    kind: str
    x0: float
    y0: float
    x1: float
    y1: float
    fill: str = ""
    is_text: bool = False
    ax: float = 0.0
    placeholder: bool = False
    layer: str = ""                          # data-pptx-layer of the element (master/layout = fixed)
    slot: Optional[ET.Element] = None        # placeholder <g> that carries this element
    anchor: str = ""                         # data-pptx-placeholder-anchor of that slot

    @property
    def movable(self) -> bool:
        """A deck may move it: slide-local, and a placeholder only when its slot opts in."""
        return self.layer not in ("master", "layout") and (not self.placeholder or self.anchor == "middle")

    @property
    def w(self) -> float:
        return self.x1 - self.x0

    @property
    def h(self) -> float:
        return self.y1 - self.y0

    def inside(self, c: "Item", tol: float = 0.6) -> bool:
        if self.is_text:  # width is estimated: test the anchor point, not the right edge
            return (c.x0 - tol <= self.ax <= c.x1 + tol
                    and self.y0 >= c.y0 - tol and self.y1 <= c.y1 + tol)
        return (self.x0 >= c.x0 - tol and self.x1 <= c.x1 + tol
                and self.y0 >= c.y0 - tol and self.y1 <= c.y1 + tol)


@dataclass
class Finding:
    code: str
    page: str
    box: tuple
    gap_top: float
    gap_bottom: float
    delta: float = 0.0
    fixed: bool = False
    note: str = ""
    items: list = field(default_factory=list, repr=False)


def _text_width(s: str, size: float) -> float:
    w = 0.0
    for ch in s:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F or 0x4E00 <= o <= 0x9FFF:
            w += 1.0
        elif ch == " ":
            w += 0.28
        else:
            w += 0.58
    return w * size


def _metrics(s: str) -> tuple[float, float]:
    if any(0xAC00 <= ord(c) <= 0xD7A3 or 0x4E00 <= ord(c) <= 0x9FFF for c in s):
        return HANGUL_ASCENT, HANGUL_DESCENT
    if any(c in "gjpqy" for c in s):
        return LATIN_ASCENT, LATIN_DESCENT
    return LATIN_ASCENT, DIGIT_DESCENT


def _text_item(el, style: dict) -> Optional[Item]:
    size = _f(el.get("font-size") or style.get("font-size"), 16.0)
    anchor = el.get("text-anchor") or style.get("text-anchor") or "start"
    x, y = _f(el.get("x")), _f(el.get("y"))
    lines: list[tuple[float, float, str]] = []
    head = (el.text or "").strip()
    if head:
        lines.append((x, y, head))
    cy = y
    for ts in el:
        if _tag(ts) != "tspan":
            continue
        tx = _f(ts.get("x"), x) if ts.get("x") is not None else x
        if ts.get("y") is not None:
            cy = _f(ts.get("y"))
        elif ts.get("dy") is not None:
            cy += _f(ts.get("dy"))
        t = "".join(ts.itertext()).strip()
        if t:
            lines.append((tx, cy, t))
    if not lines:
        return None
    x0 = y0 = float("inf")
    x1 = y1 = float("-inf")
    for lx, ly, t in lines:
        asc, desc = _metrics(t)
        wdt = _text_width(t, size)
        left = lx - wdt if anchor == "end" else lx - wdt / 2 if anchor == "middle" else lx
        x0, x1 = min(x0, left), max(x1, left + wdt)
        y0, y1 = min(y0, ly - asc * size), max(y1, ly + desc * size)
    return Item(el, "text", x0, y0, x1, y1, is_text=True, ax=x)


def collect(root) -> tuple[list[Item], bool]:
    """Flatten drawable elements with absolute bounds. Returns (items, has_transform)."""
    items: list[Item] = []
    transformed = False

    def walk(el, style, under_transform, slot=None):
        nonlocal transformed
        tag = _tag(el)
        if slot is None and el.get("data-pptx-placeholder") is not None:
            slot = el
        if tag in ("defs", "metadata", "style", "clipPath", "mask", "symbol"):
            return
        st = dict(style)
        for k in ("font-size", "text-anchor"):
            if el.get(k) is not None:
                st[k] = el.get(k)
        tr = under_transform or bool(el.get("transform"))
        if tr and tag in SHIFTABLE | {"path"}:
            transformed = True
            return
        if tag == "text":
            it = _text_item(el, st)
            if it:
                _tag_item(it, el, slot)
                items.append(it)
            return
        if tag == "rect":
            x, y, w, h = (_f(el.get(k)) for k in ("x", "y", "width", "height"))
            items.append(Item(el, "rect", x, y, x + w, y + h, (el.get("fill") or "").upper()))
        elif tag in ("circle", "ellipse"):
            cx, cy = _f(el.get("cx")), _f(el.get("cy"))
            rx = _f(el.get("r")) or _f(el.get("rx"))
            ry = _f(el.get("r")) or _f(el.get("ry"))
            items.append(Item(el, tag, cx - rx, cy - ry, cx + rx, cy + ry))
        elif tag == "image":
            x, y, w, h = (_f(el.get(k)) for k in ("x", "y", "width", "height"))
            items.append(Item(el, "image", x, y, x + w, y + h))
        elif tag == "line":
            x1, y1, x2, y2 = (_f(el.get(k)) for k in ("x1", "y1", "x2", "y2"))
            items.append(Item(el, "line", min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
        elif tag in ("polygon", "polyline"):
            nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", el.get("points", ""))]
            if len(nums) >= 4:
                xs, ys = nums[0::2], nums[1::2]
                items.append(Item(el, tag, min(xs), min(ys), max(xs), max(ys)))
        elif tag == "path":
            transformed = True  # bounds unknown; containers holding paths are skipped
        if items and items[-1].el is el:
            _tag_item(items[-1], el, slot)
        for ch in el:
            walk(ch, st, tr, slot)

    walk(root, {}, False)
    return items, transformed


def _tag_item(it: Item, el, slot) -> None:
    it.layer = (el.get("data-pptx-layer") or "").strip().lower()
    if slot is not None:
        it.placeholder, it.slot = True, slot
        it.anchor = (slot.get("data-pptx-placeholder-anchor") or "").strip().lower()


def slot_bounds(slot) -> Optional[list[float]]:
    """`x y width height` of a placeholder slot, or None."""
    nums = re.findall(r"-?\d+(?:\.\d+)?", (slot.get("data-pptx-placeholder-bounds") or "") if slot is not None else "")
    return [float(n) for n in nums] if len(nums) == 4 else None


def _containers(items: list[Item], cw: float, ch: float) -> list[Item]:
    out = []
    for it in items:
        if it.kind != "rect" or it.fill in ("NONE", "TRANSPARENT") or it.el.get("data-balance-exempt"):
            continue
        if it.w < 40 or it.h < 24:
            continue
        if it.w >= cw * 0.95 and it.h >= ch * 0.95:
            continue
        if it.w >= cw * 0.4 and it.h <= it.w * 0.16:
            continue                         # table row band: cells follow the table rule
        out.append(it)
    out.sort(key=lambda c: c.w * c.h)
    return out


def _touches_edge(it: Item, c: Item) -> bool:
    return (abs(it.y0 - c.y0) <= EDGE_TOL or abs(it.y1 - c.y1) <= EDGE_TOL
            or abs(it.x0 - c.x0) <= EDGE_TOL or abs(it.x1 - c.x1) <= EDGE_TOL)


def _is_divider(it: Item, c: Item) -> bool:
    thin = (it.kind == "line" and it.h < 1) or (it.kind == "rect" and it.h <= 2.5)
    return thin and it.w >= c.w * 0.6


def _split_header(top: float, content: list[Item]) -> tuple[float, list[Item]]:
    """A top row made only of fixed layout elements (section label, step badge + letter)
    or of slots declared `anchor="top"` (panel heading) is the card's heading: it
    stays put and the rest is centered below it."""
    rows = sorted(content, key=lambda it: it.y0)
    if len(rows) < 2:
        return top, content
    band = [rows[0]]
    y1 = rows[0].y1
    for it in rows[1:]:
        if it.y0 < y1 - 0.5:
            band.append(it)
            y1 = max(y1, it.y1)
    rest = [it for it in content if it not in band]
    if (rest and any(it.is_text for it in band) and all(it.layer == "layout" or it.anchor == "top" for it in band)
            and min(it.y0 for it in rest) >= y1):
        return y1, rest
    return top, content


def _balance(c: Item, zone: tuple[float, float], content: list[Item], page: str) -> Optional[Finding]:
    top, bottom = zone
    if not any(it.is_text for it in content):
        return None
    top, content = _split_header(top, content)
    if not content or any(it.anchor == "top" for it in content):
        return None                          # slot declared top-anchored (chart, table, free drawing)
    if any(not it.is_text and it.h >= (bottom - top) * 0.85 for it in content):
        return None                          # inner frame / image fills the zone
    g0 = min(it.y0 for it in content)
    g1 = max(it.y1 for it in content)
    gap_top, gap_bottom = g0 - top, bottom - g1
    if gap_top < 0 or gap_bottom < 0:
        return None
    imbalance = gap_bottom - gap_top
    if any(it.anchor == "middle" for it in content):
        imbalance_seen = abs(imbalance)          # a centered slot may also have been written too low
    else:
        imbalance_seen = imbalance
    if imbalance_seen <= max(MIN_IMBALANCE_PX, IMBALANCE_RATIO * (bottom - top)):
        return None
    return Finding("CB01", page, (round(c.x0, 1), round(top, 1), round(c.w, 1), round(bottom - top, 1)),
                   round(gap_top, 1), round(gap_bottom, 1), round(imbalance / 2, 2), items=content)


def _card_zones(c: Item, items: list[Item]) -> list[tuple[tuple[float, float], list[Item]]]:
    """Text zones of a card for the tidy pass: the body under a header band, or the
    zone below a single heading rule. Cards with list separators keep one zone."""
    inside = [it for it in items if it is not c and it.inside(c)]
    top, bottom = c.y0, c.y1
    content, cuts = [], []
    for it in inside:
        if not it.is_text and _touches_edge(it, c):
            if it.w >= c.w * 0.9 and abs(it.y0 - c.y0) <= EDGE_TOL and it.h < c.h * 0.5:
                top = max(top, it.y1)
            elif it.w >= c.w * 0.9 and abs(it.y1 - c.y1) <= EDGE_TOL and it.h < c.h * 0.5:
                bottom = min(bottom, it.y0)
            continue
        if _is_divider(it, c):
            cuts.append(it.y0)
            continue
        content.append(it)
    content = [it for it in content if it.y0 >= top - 0.6 and it.y1 <= bottom + 0.6]
    cuts = sorted({round(y, 1) for y in cuts if top < y < bottom})
    if len(cuts) == 1:
        lower = [it for it in content if it.y0 >= cuts[0] - 0.6]
        return [((cuts[0], bottom), lower)] if lower else []
    if cuts:
        return []
    return [((top, bottom), content)] if content else []


def _is_line_tspan(ts) -> bool:
    return _tag(ts) == "tspan" and any(ts.get(k) is not None for k in ("x", "y", "dy"))


def _plain_text(el) -> bool:
    """Lines are direct tspans only: no transform, no positioned nested tspan."""
    if el.get("transform") or (el.get("text-anchor") or "start") != "start":
        return False
    for ts in el:
        if _tag(ts) != "tspan":
            return False
        for sub in ts.iter():
            if sub is not ts and _tag(sub) == "tspan" and any(sub.get(k) is not None for k in ("x", "y", "dy")):
                return False
    return True


def _canon(el) -> list[list]:
    """Rewrite a plain <text> so each visual line is a direct tspan with x and dy
    (the first line has no dy; its baseline is the text's y). Inline runs fold
    into their line. Returns [[tspan, baseline], ...]."""
    x, y = el.get("x") or "0", _f(el.get("y"))
    lines: list[list] = []
    head = (el.text or "").strip()
    el.text = None
    if head:
        ts = ET.Element(f"{{{SVG_NS}}}tspan", {"x": x})
        ts.text = head
        el.insert(0, ts)
        lines.append([ts, y])
    cy = y
    for ts in list(el):
        if lines and ts is lines[0][0]:
            continue
        if ts.get("y") is not None:
            cy = _f(ts.get("y"))
        elif ts.get("dy") is not None:
            cy += _f(ts.get("dy"))
        elif lines:
            el.remove(ts)
            lines[-1][0].append(ts)
            continue
        lines.append([ts, cy])
    for i, (ts, b) in enumerate(lines):
        ts.set("x", ts.get("x") or x)        # keeps a bullet's hanging indent
        ts.attrib.pop("y", None)
        if i == 0:
            ts.attrib.pop("dy", None)
        else:
            ts.set("dy", f"{b - lines[i - 1][1]:g}")
        if not (ts.tail or "").strip():
            ts.tail = None
    if lines:
        el.set("y", f"{lines[0][1]:g}")
    return lines


def _line_text(ts) -> str:
    return "".join(ts.itertext()).strip()


def _size(el) -> float:
    return _f(el.get("font-size"), 16.0)


def _marker_for(t: Item, items: list[Item]) -> Optional[Item]:
    """A small square/dot just left of the text's first line (a drawn bullet)."""
    size = _size(t.el)
    first = t.y0 + HANGUL_ASCENT * size
    for m in items:
        if m.is_text or m.kind not in ("rect", "circle", "ellipse") or m.w > MARKER_MAX or m.h > MARKER_MAX:
            continue
        cy = (m.y0 + m.y1) / 2
        if 0 <= t.ax - m.x1 <= 2.5 * size and first - HANGUL_ASCENT * size - 2 <= cy <= first + 2:
            return m
    return None


def _text_blocks(content: list[Item]) -> list[list[Item]]:
    """Runs of left-aligned texts at one x and one size, stacked at line/paragraph pitch."""
    texts = sorted((it for it in content if it.is_text and _plain_text(it.el)), key=lambda it: (round(it.ax), it.y0))
    blocks: list[list[Item]] = []
    for t in texts:
        prev = blocks[-1][-1] if blocks else None
        if (prev is not None and abs(prev.ax - t.ax) <= 1 and _size(prev.el) == _size(t.el)
                and 0 < t.y0 - prev.y1 <= (LINE_PITCH_MAX - 1) * _size(t.el)):
            blocks[-1].append(t)
        else:
            blocks.append([t])
    return [b for b in blocks if len(b) >= 2]


STYLE_DEFAULTS = {"fill": "#000000", "font-weight": "400", "font-style": "normal",
                  "fill-opacity": "1", "text-decoration": "none"}


def _style(ts) -> tuple:
    return tuple(ts.get(k) for k in STYLE_DEFAULTS)


def merge_block(block: list[Item], items: list[Item]) -> None:
    """CB06 fix: one <text> per block; drawn bullet squares become text bullets
    (▪/•) so PowerPoint gets one text box with native bullets and line spacing.
    Text-level styles that differ inside the block move onto each line."""
    base = block[0].el
    markers = [_marker_for(t, items) for t in block]
    x = min([m.x0 for m in markers if m] + [block[0].ax]) if any(markers) else block[0].ax
    mixed = [k for k in STYLE_DEFAULTS if len({t.el.get(k) or STYLE_DEFAULTS[k] for t in block}) > 1]
    all_lines: list[list] = []
    heads: set[int] = set()
    for t, m in zip(block, markers):
        lines = _canon(t.el)
        for ts, _b in lines:
            for k in mixed:
                if ts.get(k) is None:
                    ts.set(k, t.el.get(k) or STYLE_DEFAULTS[k])
        if m is not None and lines:
            ts = lines[0][0]
            heads.add(id(ts))
            dot = ET.Element(f"{{{SVG_NS}}}tspan", {"fill": m.el.get("fill") or "#000000"})
            dot.text = "▪ " if m.kind == "rect" else "• "
            dot.tail, ts.text = ts.text, None
            ts.insert(0, dot)
        all_lines += lines
    for t in block[1:]:
        for parent in _parents(t.el):
            parent.remove(t.el)
    for m in markers:
        if m is not None:
            for parent in _parents(m.el):
                parent.remove(m.el)
    for ts in list(base):
        base.remove(ts)
    base.set("x", f"{x:g}")
    base.set("y", f"{all_lines[0][1]:g}")
    for i, (ts, b) in enumerate(all_lines):
        if id(ts) in heads or not any(markers):
            ts.set("x", f"{x:g}")            # bullet line starts at the marker; wrapped lines keep the text indent
        ts.attrib.pop("dy", None)
        if i:
            ts.set("dy", f"{b - all_lines[i - 1][1]:g}")
        base.append(ts)


_PARENTS: dict = {}


def _parents(el) -> list:
    p = _PARENTS.get(id(el))
    return [p] if p is not None else []


def _starts_marker(ts) -> bool:
    return _line_text(ts)[:1] in BULLET_CHARS


def rejoin_lines(el, t: Item, c: Item, content: list[Item]) -> int:
    """CB07 fix: pull a wrapped line back up when the whole line fits the frame
    (`el` is the text itself, or a copy when only reporting)."""
    if _n_lines(el) < 2:
        return 0
    lines = _canon(el)
    size, x = _size(el), _f(el.get("x"))
    if any(o is not t and o.x0 > x + 4 for o in content):
        return 0                             # a table row / column layout: the cell edge is unknown
    pad = max(8.0, min(24.0, x - c.x0))
    right = c.x1 - pad
    dys = [_f(ts.get("dy")) for ts, _ in lines[1:]]
    pitch = min(dys)
    joined, i, removed = 0, 0, 0.0
    while i < len(lines) - 1:
        cur, nxt = lines[i][0], lines[i + 1][0]
        soft = (abs(_f(nxt.get("dy")) - pitch) <= 0.5 and pitch <= WRAP_PITCH * size and not _starts_marker(nxt)
                and _style(cur) == _style(nxt))  # a bold heading line never joins its body
        if soft and _text_width(_line_text(cur) + " " + _line_text(nxt), size) <= (right - x) * WRAP_MARGIN:
            if len(cur):
                cur[-1].tail = (cur[-1].tail or "") + " " + (nxt.text or "")
            else:
                cur.text = (cur.text or "") + " " + (nxt.text or "")
            for ch in list(nxt):
                nxt.remove(ch)
                cur.append(ch)
            removed += _f(nxt.get("dy"))
            el.remove(nxt)
            del lines[i + 1]
            joined += 1
            continue
        i += 1
    if removed:                              # keep the block's vertical center
        el.set("y", f"{_f(el.get('y')) + removed / 2:g}")
    return joined


def spread_zone(zone: tuple[float, float], content: list[Item]) -> Optional[float]:
    """CB05 fix: widen line and paragraph spacing of a text list until it fills
    FILL_TARGET of its zone (line pitch ≤ MAX_LINE_PITCH em, paragraph gap
    ≤ MAX_PARA_GAP em). Returns the new fill ratio, or None when not a text list."""
    z0, z1 = zone
    texts = [it for it in content if it.is_text]
    if any(not it.is_text and (it.w > MARKER_MAX or it.h > MARKER_MAX) for it in content):
        return None
    if not texts or any(not _plain_text(t.el) for t in texts):
        return None
    g0, g1 = min(it.y0 for it in content), max(it.y1 for it in content)
    if sum(_n_lines(t.el) for t in texts) < 3 or (g1 - g0) >= SPARSE_FILL * (z1 - z0):
        return None
    canon = {id(t): _canon(t.el) for t in texts}
    size = max(_size(t.el) for t in texts)
    clusters: list[list[Item]] = []
    for it in sorted(content, key=lambda it: it.y0):
        if clusters and it.y0 < max(o.y1 for o in clusters[-1]) - 0.5:
            clusters[-1].append(it)
        else:
            clusters.append([it])
    soft, para = [], []
    for t in texts:
        lines = canon[id(t)]
        if len(lines) < 2:
            continue
        pitch = min(_f(ts.get("dy")) for ts, _ in lines[1:])
        for ts, _ in lines[1:]:
            (soft if abs(_f(ts.get("dy")) - pitch) <= 0.5 and not _starts_marker(ts) else para).append((ts, pitch))
    n_between = len(clusters) - 1
    extra = FILL_TARGET * (z1 - z0) - (g1 - g0)
    base_pitch = min((p for _, p in soft + para), default=1.4 * size)
    s = min(max(0.0, MAX_LINE_PITCH * size - base_pitch), extra * 0.35 / len(soft)) if soft else 0.0
    n_para = len(para) + n_between
    p = min(MAX_PARA_GAP * size, (extra - s * len(soft)) / n_para) if n_para else 0.0
    p = max(p, s)
    total = s * len(soft) + p * n_para
    if total > extra > 0:
        s, p = s * extra / total, p * extra / total
    if s + p <= 0.5:
        return None
    gap = sum(_f(ts.get("dy")) - pitch for ts, pitch in para) / len(para) if para else 0.0
    new_dy = {id(ts): _f(ts.get("dy")) + s for ts, _ in soft}
    new_dy.update({id(ts): pitch + gap + s + p for ts, pitch in para})   # one shared paragraph gap
    grow = {id(t): sum(new_dy[id(ts)] - _f(ts.get("dy")) for ts, _ in canon[id(t)][1:]) for t in texts}
    cl_grow = [max((grow[id(it)] for it in cl if it.is_text), default=0.0) for cl in clusters]
    new_h = (g1 - g0) + sum(cl_grow) + p * n_between
    for ts, _ in soft + para:
        ts.set("dy", f"{new_dy[id(ts)]:.2f}".rstrip("0").rstrip("."))
    offset = z0 + (z1 - z0 - new_h) / 2 - g0     # spread and re-center in one move
    for cl, g in zip(clusters, cl_grow):
        shift(cl, offset)
        offset += g + p
    return new_h / (z1 - z0)


def tidy_card(c: Item, items: list[Item], page: str, fix: bool,
              spread: bool = True) -> tuple[list[Finding], bool]:
    """CB06 → CB07 → CB05 on one card; CB01 centering runs afterwards.
    `spread=False` once the card was spread, so the caps hold across passes."""
    out: list[Finding] = []
    changed = False
    box = (round(c.x0, 1), round(c.y0, 1), round(c.w, 1), round(c.h, 1))
    for (z0, z1), content in _card_zones(c, items):
        for block in _text_blocks(content):
            out.append(Finding("CB06", page, box, 0.0, 0.0, fixed=fix,
                               note=f"본문 {len(block)}줄/문단이 개별 텍스트 개체 — PPT에서 줄간격 조정 불가"
                                    + (", 한 텍스트(네이티브 불릿)로 합침" if fix else ", 한 <text>+tspan으로 합치세요")))
            if fix:
                merge_block(block, items)
                changed = True
        if changed:
            return out, True                  # re-measure before the next pass
        for t in content:
            if not t.is_text or not _plain_text(t.el):
                continue
            n = rejoin_lines(t.el if fix else copy.deepcopy(t.el), t, c, content)
            if n:
                out.append(Finding("CB07", page, box, 0.0, 0.0, fixed=fix,
                                   note=f"폭이 남는데 줄바꿈 {n}곳 — " + ("한 줄로 합침" if fix else "한 줄로 합치세요")))
                changed = changed or fix
        if changed:
            return out, True
        g0 = min((it.y0 for it in content), default=z0)
        g1 = max((it.y1 for it in content), default=z0)
        fill = (g1 - g0) / (z1 - z0) if z1 > z0 else 1.0
        n_lines = sum(_n_lines(it.el) for it in content if it.is_text)
        if spread and z1 - z0 >= 120 and fill < SPARSE_FILL and n_lines >= 3:
            new = spread_zone((z0, z1), content) if fix else None
            note = (f"내용이 영역의 {fill:.0%}만 채움 — 줄·문단 간격을 넓혀 {new:.0%}로 채움" if new
                    else f"내용이 영역의 {fill:.0%}만 채움 — 줄간격·문단 간격을 넓히거나 글자 크기를 키우세요")
            out.append(Finding("CB05", page, box, round(g0 - z0, 1), round(z1 - g1, 1), fixed=bool(new), note=note))
            changed = changed or bool(new)
    return out, changed


def _n_lines(el) -> int:
    return int(bool((el.text or "").strip())) + sum(1 for ts in el if _is_line_tspan(ts)) or 1


def analyse_card(c: Item, items: list[Item], page: str) -> list[Finding]:
    """Check one background box. A single internal full-width rule splits it into
    a heading zone (kept in place when it hugs the rule) and a body zone that is
    centred; two or more rules are list separators and move with the list."""
    inside = [it for it in items if it is not c and it.inside(c)]
    if not inside:
        return []
    top, bottom = c.y0, c.y1
    content, rules = [], []
    for it in inside:
        if not it.is_text and _touches_edge(it, c):
            if it.w >= c.w * 0.9 and abs(it.y0 - c.y0) <= EDGE_TOL and it.h < c.h * 0.5:
                top = max(top, it.y1)        # header band / accent bar on top
            elif it.w >= c.w * 0.9 and abs(it.y1 - c.y1) <= EDGE_TOL and it.h < c.h * 0.5:
                bottom = min(bottom, it.y0)  # footer band on bottom
            continue                         # side bars, corner tags, frames
        (rules if _is_divider(it, c) else content).append(it)
    content = [it for it in content if it.y0 >= top - 0.6 and it.y1 <= bottom + 0.6]
    cuts = sorted({round(r.y0, 1) for r in rules if top < r.y0 < bottom})
    if len(cuts) != 1:
        # no rule, or row separators of a list: the whole list moves as one group
        content += [r for r in rules if top <= r.y0 <= bottom]
        f = _balance(c, (top, bottom), content, page)
        return [f] if f else []
    edges = [top] + cuts + [bottom]
    zones = []
    for z0, z1 in zip(edges, edges[1:]):
        zc = [it for it in content if it.y0 >= z0 - 0.6 and it.y1 <= z1 + 0.6]
        if zc:
            zones.append(((z0, z1), zc))
    out = []
    for i, ((z0, z1), zc) in enumerate(zones):
        if i == 0 and len(zones) > 1:
            g0, g1 = min(it.y0 for it in zc), max(it.y1 for it in zc)
            if (z1 - g1) <= 1.5 * (g0 - z0) + 4:
                continue                     # heading zone hugging its rule
        f = _balance(c, (z0, z1), zc, page)
        if f:
            out.append(f)
    return out


def _native_table_bottom(root) -> Optional[float]:
    """Lowest edge of the native tables on a page (metadata y + height), or None."""
    bottoms = []
    for el in root.iter():
        if _tag(el) == "metadata" and (el.get("data-pptx-native") or "").strip() == "table":
            try:
                meta = json.loads(el.text or "{}")
                bottoms.append(float(meta["y"]) + float(meta["height"]))
            except (ValueError, KeyError, TypeError):
                continue
    return max(bottoms) if bottoms else None


def analyse_toc(items: list[Item], cw: float, ch: float, page: str,
                table_bottom: Optional[float] = None) -> Optional[Finding]:
    # A native table's own row rules are body, not the footer line.
    above = table_bottom + 0.5 if table_bottom is not None else 0.0
    footer = [it for it in items if it.kind == "line" and it.h < 1 and it.w >= cw * 0.5 and it.y0 > max(ch * 0.8, above)]
    floor = min((it.y0 for it in footer), default=ch * 0.92)
    body = [it for it in items if it.y1 < floor - 0.5 and it.y0 > ch * 0.15
            and not (it.kind == "rect" and it.w >= cw * 0.95)]
    if not body and table_bottom is None:
        return None
    last = max([it.y1 for it in body] + ([min(table_bottom, floor)] if table_bottom is not None else []))
    void = floor - last
    if void <= TOC_VOID_RATIO * ch:
        return None
    return Finding("CB02", page, (0, round(last, 1), round(cw, 1), round(void, 1)), 0.0, round(void, 1),
                   note=f"목차 영역이 y{last:.0f}에서 끝나 바닥선(y{floor:.0f})까지 {void:.0f}px가 비어 있음 — 행 간격을 늘려 영역을 채우세요")


def _footer_floor(items: list[Item], cw: float, ch: float, below: float = 0.0) -> float:
    """Footer line: a rule whose id names the footer, else a wide low rule under `below`."""
    rules = [it for it in items if it.kind in ("line", "rect") and it.h < 2.5 and it.w >= cw * 0.5]
    footer = [it for it in rules if "footer" in (it.el.get("id") or "").lower()]
    footer = footer or [it for it in rules if it.y0 > max(ch * 0.85, below)]
    return min((it.y0 for it in footer), default=ch * 0.95)


def _path_bottoms(root, ch: float) -> list[float]:
    """Lowest y of each untransformed absolute path (M/L/C/S/Q/T pairs and V values)."""
    out = []
    for el in root.iter():
        if _tag(el) != "path" or el.get("transform") or el.get("id", "").startswith(("footer", "source")):
            continue
        ys, cmd, idx = [], "", 0
        for tok in re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", el.get("d", "")):
            if tok.isalpha():
                cmd, idx = tok, 0
                continue
            if (cmd in "MLCSQT" and idx % 2 == 1) or cmd == "V":
                ys.append(float(tok))
            idx += 1
        if ys and not any(c.islower() for c in re.findall(r"[A-Za-z]", el.get("d", ""))):
            out.append(max(ys))
    return [y for y in out if ch * 0.18 < y < ch]


def analyse_page_bottom(items: list[Item], cw: float, ch: float, page: str,
                        path_bottoms: list[float] = ()) -> Optional[Finding]:
    """CB03: gap between the lowest body element and the source line (or the footer line)."""
    sources = [it for it in items if it.is_text and it.y0 > ch * 0.6
               and ("".join(it.el.itertext()).strip().startswith(SOURCE_PREFIXES)
                    or "source" in (it.el.get("id") or "").lower())]
    # A table or frame rule above the source line is body, not the footer.
    floor = _footer_floor(items, cw, ch, below=max((it.y0 for it in sources), default=0.0))
    sources = [it for it in sources if it.y0 < floor]
    if sources:
        floor = min(it.y0 for it in sources)
    body = [it for it in items if it not in sources and it.y0 > ch * 0.155 and it.y1 < floor - 0.5
            and not (it.kind == "rect" and it.w >= cw * 0.95 and it.h >= ch * 0.5)]
    if not body:
        return None
    last = max([it.y1 for it in body] + [y for y in path_bottoms if y < floor - 0.5])
    void = floor - last
    if void <= PAGE_VOID_RATIO * ch:
        return None
    target = "출처 줄" if sources else "바닥선"
    return Finding("CB03", page, (0, round(last, 1), round(cw, 1), round(void, 1)), 0.0, round(void, 1),
                   note=f"본문이 y{last:.0f}에서 끝나 {target}(y{floor:.0f})까지 {void:.0f}px가 비어 있음 "
                        f"(허용 {PAGE_VOID_RATIO * ch:.0f}px) — 본문 글자·행 높이를 키우거나 맺음 메시지 띠를 넣으세요")


def _can_shift(content: list[Item], template: bool) -> bool:
    for it in content:
        if _tag(it.el) not in SHIFTABLE:
            return False
        if template:
            if it.layer == "master" or (it.placeholder and it.anchor != "middle"):
                return False
        elif not it.movable:
            return False
    return True


def _move_slot_bounds(content: list[Item], delta: float, zone: tuple[float, float]) -> None:
    """Template mode: keep each moved carrier inside its slot bounds, and the bounds inside the zone."""
    for slot in {id(it.slot): it.slot for it in content if it.slot is not None}.values():
        b = slot_bounds(slot)
        if b is None:
            continue
        ink = [it for it in content if it.slot is slot]
        y0, y1 = min(it.y0 for it in ink) + delta, max(it.y1 for it in ink) + delta
        if b[1] - 0.5 <= y0 and y1 <= b[1] + b[3] + 0.5:
            continue
        top = min(max(b[1] + delta, zone[0]), zone[1] - b[3])
        slot.set("data-pptx-placeholder-bounds", " ".join(f"{v:g}" for v in (b[0], round(top, 1), b[2], b[3])))


def center_in_slots(content: list[Item], min_height: float = 0.0) -> bool:
    """Center opted-in carriers inside their own slot bounds: rows beside fixed badges,
    or side-by-side slots that each span the zone (`min_height` filters stacked slots)."""
    moved = False
    for it in content:
        b = slot_bounds(it.slot)
        if it.anchor != "middle" or b is None or not it.is_text or it.layer in ("master", "layout"):
            continue
        if b[3] < min_height or it.h > b[3]:
            continue
        delta = round(b[1] + (b[3] - it.h) / 2 - it.y0, 2)
        if abs(delta) > 0.5:
            shift([it], delta)
            moved = True
    return moved


def shift(content: list[Item], delta: float) -> bool:
    for it in content:
        el, tag = it.el, _tag(it.el)
        keys = {"rect": ("y",), "image": ("y",), "text": ("y",), "circle": ("cy",),
                "ellipse": ("cy",), "line": ("y1", "y2")}.get(tag, ())
        for k in keys:
            if el.get(k) is not None:
                el.set(k, f"{_f(el.get(k)) + delta:g}")
        if tag == "text":
            for ts in el:
                if _tag(ts) == "tspan" and ts.get("y") is not None:
                    ts.set("y", f"{_f(ts.get('y')) + delta:g}")
        if tag in ("polygon", "polyline"):
            nums = re.findall(r"(-?\d+(?:\.\d+)?)[ ,]+(-?\d+(?:\.\d+)?)", el.get("points", ""))
            el.set("points", " ".join(f"{x},{_f(y) + delta:g}" for x, y in nums))
    return True


def _refusal(content: list[Item]) -> str:
    if any(it.layer in ("master", "layout") for it in content):
        return "고정 레이아웃 요소(data-pptx-layer=layout) 포함 — 템플릿에서 수정"
    if any(it.placeholder and it.anchor != "middle" for it in content):
        return "구조화 자리(placeholder)가 위 고정 — 템플릿에 data-pptx-placeholder-anchor=\"middle\" 지정 필요"
    return "자동 보정 불가(경로·변형 요소 포함) — 직접 이동"


def exempt_notes(path: Path) -> list[str]:
    """Containers the template author exempted, with the stated reason."""
    root = ET.parse(str(path)).getroot()
    notes = [f"{path.name} #{el.get('id') or 'rect'}: {el.get('data-balance-exempt')}"
             for el in root.iter() if _tag(el) == "rect" and el.get("data-balance-exempt")]
    if root.get("data-balance-exempt"):
        notes.append(f"{path.name} (CB03 제외): {root.get('data-balance-exempt')}")
    notes += [f"{path.name} #{el.get('id')}: 위 고정 자리(차트·표·도식을 채우는 영역)"
              for el in root.iter() if (el.get("data-pptx-placeholder-anchor") or "").strip().lower() == "top"]
    return notes


def check_file(path: Path, fix: bool, template: bool = False) -> list[Finding]:
    tree = ET.parse(str(path))
    root = tree.getroot()
    vb = [float(v) for v in (root.get("viewBox") or "0 0 1280 720").split()]
    cw, ch = vb[2], vb[3]
    items, _ = collect(root)
    findings: list[Finding] = []
    role = (root.get("data-pptx-page-role") or "") + " " + (root.get("data-pptx-layout") or "") + " " + path.stem
    if "toc" in role.lower() or "목차" in path.stem:
        f = analyse_toc(items, cw, ch, path.name, _native_table_bottom(root))
        if f:
            findings.append(f)
        strict = (root.get("data-pptx-page-role") or "") + " " + (root.get("data-pptx-layout") or "") + " " + path.stem.split("__")[0]
        if (re.search(r"(^|[\s_\-])(toc|목차)([\s_\-]|$)", strict.lower())
                and not any((el.get("data-pptx-native") or "").strip() == "table" for el in root.iter())):
            findings.append(Finding("CB04", path.name, (0, 0, round(cw, 1), round(ch, 1)), 0.0, 0.0,
                                    note="목차가 표가 아님 — 목차 템플릿의 표(data-pptx-native=\"table\", "
                                         "셀 valign ctr, 행이 바닥선까지)로 바꾸고 --native-objects로 내보내세요"))
    elif not any(r in role.lower() for r in NO_BODY_ROLES) and not root.get("data-balance-exempt"):
        f = analyse_page_bottom(items, cw, ch, path.name, _path_bottoms(root, ch))
        if f:
            findings.append(f)
    changed = False
    if not template:
        # Row bands count here: a wide one-line box (Q1–Q8 rows) can still wrap too early.
        boxes = [it.el for it in items if it.kind == "rect" and it.fill not in ("NONE", "TRANSPARENT")
                 and it.w >= 40 and it.h >= 24 and not (it.w >= cw * 0.95 and it.h >= ch * 0.95)
                 and not it.el.get("data-balance-exempt")]
        for rect in boxes:
            spread = True
            for _ in range(4):                   # merge → rejoin → spread, re-measuring between
                _PARENTS.clear()
                _PARENTS.update({id(k): p for p in root.iter() for k in p})
                c = next((it for it in items if it.el is rect), None)
                if c is None:
                    break
                found, moved = tidy_card(c, items, path.name, fix, spread)
                findings.extend(found)
                spread = spread and not any(f.code == "CB05" and f.fixed for f in found)
                if not moved:
                    break
                changed = True
                items, _ = collect(root)
    for c in _containers(items, cw, ch):
        for f in analyse_card(c, items, path.name):
            if fix and _can_shift(f.items, template):
                if template:
                    _move_slot_bounds(f.items, f.delta, (f.box[1], f.box[1] + f.box[3]))
                shift(f.items, f.delta)
                if not template:
                    for it in f.items:           # the shift moved them; keep the measured box in step
                        it.y0, it.y1 = it.y0 + f.delta, it.y1 + f.delta
                    center_in_slots(f.items, FULL_SLOT_RATIO * f.box[3])
                f.fixed, changed = True, True
            elif fix and not template and center_in_slots(f.items):
                f.fixed, changed = True, True
                f.note = "고정 요소는 두고 자리별로 가운데 정렬함 — 렌더로 확인"
            elif fix:
                f.note = _refusal(f.items)
            findings.append(f)
        if changed:
            items, _ = collect(root)         # re-measure after a move
    if changed:
        tree.write(str(path), encoding="utf-8", xml_declaration=False)
    return findings


def resolve(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    svg_dir = target / "svg_output" if (target / "svg_output").is_dir() else target
    return sorted(svg_dir.glob("*.svg"))


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Detect top-heavy content blocks (CB01), TOC bottom voids (CB02), page bottom voids (CB03) and TOC pages that are not a table (CB04).")
    ap.add_argument("target", type=Path, help="project path, svg directory or a single SVG")
    ap.add_argument("--fix", action="store_true", help="center flagged CB01 content groups in place")
    ap.add_argument("--template", action="store_true",
                    help="template authoring: with --fix, also move layout-layer content and slot bounds")
    ap.add_argument("--json", type=Path, help="write the findings as JSON")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass
    files = resolve(args.target)
    if not files:
        print(f"[content_balance] no SVG found under {args.target}")
        return 1
    all_f: list[Finding] = []
    exempt: list[str] = []
    for p in files:
        all_f.extend(check_file(p, args.fix, args.template))
        exempt.extend(exempt_notes(p))
    for f in all_f:
        if f.code == "CB01":
            hint = f"{'아래' if f.delta > 0 else '위'}로 {abs(f.delta):g}px 이동 권장"
            state = (f.note or "보정함") if f.fixed else (f.note or hint)
            print(f"[WARN] CB01 {f.page} 상자 {f.box}: 위 여백 {f.gap_top:g}px · 아래 여백 {f.gap_bottom:g}px — {state}")
        else:
            print(f"[WARN] {f.code} {f.page}: {f.note}")
    for note in exempt:
        print(f"[INFO] 제외 {note}")
    open_n = sum(1 for f in all_f if not f.fixed)
    print(f"[content_balance] {len(files)} pages · CB01 {sum(f.code == 'CB01' for f in all_f)} · "
          f"CB02 {sum(f.code == 'CB02' for f in all_f)} · CB03 {sum(f.code == 'CB03' for f in all_f)} · "
          f"CB04 {sum(f.code == 'CB04' for f in all_f)} · "
          f"fixed {len(all_f) - open_n} · open {open_n} · exempt {len(exempt)}")
    if args.json:
        args.json.write_text(json.dumps([{k: v for k, v in f.__dict__.items() if k != "items"} for f in all_f],
                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
