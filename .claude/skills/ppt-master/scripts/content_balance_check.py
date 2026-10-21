#!/usr/bin/env python3
"""
PPT Master - Content Balance Check

Finds two recurring spacing defects in authored SVG pages, before PPTX export:

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

Gaps are measured on visible glyph bounds, not on text-box bounds: a line's
ink spans baseline - 0.78em to baseline + 0.12em for Hangul (0.72em / 0.02em
for digits), measured on IBM Plex Sans KR, Pretendard and Malgun Gothic.
`--fix` moves every flagged CB01 content group by one shared delta; x
positions, spacing inside the group and text alignment stay unchanged. CB02
and CB03 are report-only: redistribute the rows or re-plan the page (see the
skill ppt-content-group-centering).

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
SHIFTABLE = {"text", "rect", "circle", "ellipse", "image", "line", "polygon", "polyline"}


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

    def walk(el, style, under_transform, in_ph=False):
        nonlocal transformed
        tag = _tag(el)
        in_ph = in_ph or el.get("data-pptx-placeholder") is not None
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
                it.placeholder = in_ph
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
            items[-1].placeholder = in_ph
        for ch in el:
            walk(ch, st, tr, in_ph)

    walk(root, {}, False)
    return items, transformed


def _containers(items: list[Item], cw: float, ch: float) -> list[Item]:
    out = []
    for it in items:
        if it.kind != "rect" or it.fill in ("NONE", "TRANSPARENT"):
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


def _balance(c: Item, zone: tuple[float, float], content: list[Item], page: str) -> Optional[Finding]:
    top, bottom = zone
    if not any(it.is_text for it in content):
        return None
    if any(not it.is_text and it.h >= (bottom - top) * 0.85 for it in content):
        return None                          # inner frame / image fills the zone
    g0 = min(it.y0 for it in content)
    g1 = max(it.y1 for it in content)
    gap_top, gap_bottom = g0 - top, bottom - g1
    if gap_top < 0 or gap_bottom < 0:
        return None
    imbalance = gap_bottom - gap_top
    if imbalance <= max(MIN_IMBALANCE_PX, IMBALANCE_RATIO * (bottom - top)):
        return None
    return Finding("CB01", page, (round(c.x0, 1), round(top, 1), round(c.w, 1), round(bottom - top, 1)),
                   round(gap_top, 1), round(gap_bottom, 1), round(imbalance / 2, 2), items=content)


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


def analyse_toc(items: list[Item], cw: float, ch: float, page: str) -> Optional[Finding]:
    footer = [it for it in items if it.kind == "line" and it.h < 1 and it.w >= cw * 0.5 and it.y0 > ch * 0.8]
    floor = min((it.y0 for it in footer), default=ch * 0.92)
    body = [it for it in items if it.y1 < floor - 0.5 and it.y0 > ch * 0.15
            and not (it.kind == "rect" and it.w >= cw * 0.95)]
    if not body:
        return None
    last = max(it.y1 for it in body)
    void = floor - last
    if void <= TOC_VOID_RATIO * ch:
        return None
    return Finding("CB02", page, (0, round(last, 1), round(cw, 1), round(void, 1)), 0.0, round(void, 1),
                   note=f"목차 영역이 y{last:.0f}에서 끝나 바닥선(y{floor:.0f})까지 {void:.0f}px가 비어 있음 — 행 간격을 늘려 영역을 채우세요")


def _footer_floor(items: list[Item], cw: float, ch: float) -> float:
    rules = [it for it in items if it.kind in ("line", "rect") and it.h < 2.5 and it.w >= cw * 0.5]
    footer = [it for it in rules if "footer" in (it.el.get("id") or "").lower()]
    footer = footer or [it for it in rules if it.y0 > ch * 0.85]
    return min((it.y0 for it in footer), default=ch * 0.95)


def analyse_page_bottom(items: list[Item], cw: float, ch: float, page: str) -> Optional[Finding]:
    """CB03: gap between the lowest body element and the source line (or the footer line)."""
    floor = _footer_floor(items, cw, ch)
    sources = [it for it in items if it.is_text and ch * 0.6 < it.y0 < floor
               and ("".join(it.el.itertext()).strip().startswith(SOURCE_PREFIXES)
                    or "source" in (it.el.get("id") or "").lower())]
    if sources:
        floor = min(it.y0 for it in sources)
    body = [it for it in items if it not in sources and it.y0 > ch * 0.18 and it.y1 < floor - 0.5
            and not (it.kind == "rect" and it.w >= cw * 0.95 and it.h >= ch * 0.5)]
    if not body:
        return None
    last = max(it.y1 for it in body)
    void = floor - last
    if void <= PAGE_VOID_RATIO * ch:
        return None
    target = "출처 줄" if sources else "바닥선"
    return Finding("CB03", page, (0, round(last, 1), round(cw, 1), round(void, 1)), 0.0, round(void, 1),
                   note=f"본문이 y{last:.0f}에서 끝나 {target}(y{floor:.0f})까지 {void:.0f}px가 비어 있음 "
                        f"(허용 {PAGE_VOID_RATIO * ch:.0f}px) — 본문 글자·행 높이를 키우거나 맺음 메시지 띠를 넣으세요")


def shift(content: list[Item], delta: float) -> bool:
    if any(_tag(it.el) not in SHIFTABLE or it.placeholder for it in content):
        return False
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


def check_file(path: Path, fix: bool) -> list[Finding]:
    tree = ET.parse(str(path))
    root = tree.getroot()
    vb = [float(v) for v in (root.get("viewBox") or "0 0 1280 720").split()]
    cw, ch = vb[2], vb[3]
    items, _ = collect(root)
    findings: list[Finding] = []
    role = (root.get("data-pptx-page-role") or "") + " " + (root.get("data-pptx-layout") or "") + " " + path.stem
    if "toc" in role.lower() or "목차" in path.stem:
        f = analyse_toc(items, cw, ch, path.name)
        if f:
            findings.append(f)
    elif not any(r in role.lower() for r in NO_BODY_ROLES):
        f = analyse_page_bottom(items, cw, ch, path.name)
        if f:
            findings.append(f)
    changed = False
    for c in _containers(items, cw, ch):
        for f in analyse_card(c, items, path.name):
            if fix and shift(f.items, f.delta):
                f.fixed, changed = True, True
            elif fix:
                f.note = ("구조화 자리(placeholder) — 템플릿·자리 경계에서 수정"
                          if any(it.placeholder for it in f.items) else "자동 보정 불가(경로·변형 요소 포함) — 직접 이동")
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
    ap = argparse.ArgumentParser(description="Detect top-heavy content blocks (CB01), TOC bottom voids (CB02) and page bottom voids (CB03).")
    ap.add_argument("target", type=Path, help="project path, svg directory or a single SVG")
    ap.add_argument("--fix", action="store_true", help="center flagged CB01 content groups in place")
    ap.add_argument("--json", type=Path, help="write the findings as JSON")
    args = ap.parse_args(argv)
    files = resolve(args.target)
    if not files:
        print(f"[content_balance] no SVG found under {args.target}")
        return 1
    all_f: list[Finding] = []
    for p in files:
        all_f.extend(check_file(p, args.fix))
    for f in all_f:
        if f.code == "CB01":
            state = "보정함" if f.fixed else (f.note or f"아래로 {f.delta:g}px 이동 권장")
            print(f"[WARN] CB01 {f.page} 상자 {f.box}: 위 여백 {f.gap_top:g}px · 아래 여백 {f.gap_bottom:g}px — {state}")
        else:
            print(f"[WARN] {f.code} {f.page}: {f.note}")
    open_n = sum(1 for f in all_f if not f.fixed)
    print(f"[content_balance] {len(files)} pages · CB01 {sum(f.code == 'CB01' for f in all_f)} · "
          f"CB02 {sum(f.code == 'CB02' for f in all_f)} · CB03 {sum(f.code == 'CB03' for f in all_f)} · fixed {len(all_f) - open_n} · open {open_n}")
    if args.json:
        args.json.write_text(json.dumps([{k: v for k, v in f.__dict__.items() if k != "items"} for f in all_f],
                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
