#!/usr/bin/env python3
"""
PPT Master - INNerGEN content diagrams with alternatives (v33)

One body content can be drawn several ways: a five-step method is a chevron,
a numbered vertical list or a timeline; six parallel issues are cards, a table
or a hub. This tool takes the content of one page as JSON (items with labels,
descriptions and optional order, period, group, value, scores or two-sided
comparison), infers the relation, ranks the diagram forms that fit it and
draws two or three of them as editable family slides, so the author or the
reviewer can pick. `plan` picks which pages of a deck deserve alternatives.

Every shape is a <rect>/<polygon>/<line>, every label a <text>, inside the
family's 03a_content chrome (title, governing, source, footer filled from the
data), so the exported PPTX stays editable. Rules: docs/styles/innergen/
content-principles-v32.md §6 (relation → diagram) and content-diagrams-v33.md.

Usage:
    python3 scripts/content_diagrams.py forms
    python3 scripts/content_diagrams.py example <relation>
    python3 scripts/content_diagrams.py recommend <content.json>
    python3 scripts/content_diagrams.py build <content.json> --family <family> -o <dir> [--count 3] [--forms a,b,c]
    python3 scripts/content_diagrams.py pick <dir> <n|form> -o <project>/svg_output/NN_name.svg
    python3 scripts/content_diagrams.py plan <project> [--outline plan.md] [--max 6]
    python3 scripts/content_diagrams.py extract <slide.svg>        # draft content JSON from a drawn page

Dependencies:
    None (standard library only)
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable, Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
from report_diagrams import (FAMILIES, area_bounds, find_template, SVG_NS, Canvas, DiagramError, _copy_chrome_images,  # noqa: E402
                             _fill_placeholder, _flatten_structure, detect_mode, text_width, wrap)

RELATIONS = ("sequence", "parallel", "hierarchy", "comparison", "matrix", "quantity", "cause")
RELATION_KO = {"sequence": "순서·절차", "parallel": "병렬·구성", "hierarchy": "위계·분해", "comparison": "비교·대비",
               "matrix": "2축 분류", "quantity": "규모·수치", "cause": "원인·영향"}
ORDINAL = re.compile(r"^\s*(?:\d{1,2}[.)]|[①-⑩]|STEP\s*\d|Step\s*\d|Phase\s*\d|\d단계)")
CAUSE_WORDS = re.compile(r"원인|요인|영향|때문|으로 인해|이어져|이어지|초래|야기|→|동인|driver", re.I)


# ---------------------------------------------------------------------------
# Fitting helpers
# ---------------------------------------------------------------------------

class Fit:
    """Collects truncation so a variant that clips text ranks below one that fits."""

    def __init__(self) -> None:
        self.clipped: list[str] = []

    def lines(self, text: str, size: float, width: float, max_lines: int, bold: bool = False) -> list[str]:
        out = wrap(str(text or ""), size, width, bold=bold, max_lines=max_lines)
        if out and out[-1].endswith("…") and not str(text).endswith("…"):
            self.clipped.append(str(text)[:24])
        return out


def _fs(cv: Canvas) -> tuple[float, float, float]:
    small, body, head = cv.fam["ladder"]
    return small, body, head


def _conclusion(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float], fit: Fit
                ) -> tuple[float, float, float, float]:
    """Reserve the bottom band for the one-sentence conclusion strip (v32 §6.2)."""
    X, Y, W, H = box
    msg = data.get("conclusion")
    if not msg:
        return box
    small, body, head = _fs(cv)
    h = body * 2.7
    y = Y + H - h
    cv.rect("conclusion-box", X, y, W, h, fill=cv.fam["pale"])
    cv.rect("conclusion-bar", X, y, 4, h, fill=cv.fam["accent"])
    lines = fit.lines(msg, body, W - body * 2.4, 1, bold=True)
    cv.text_block("conclusion-text", X + body * 1.2, y, lines, body, h, fill=cv.fam["navy"], bold=True)
    return X, Y, W, H - h - body * 0.8


def _stack(cv: Canvas, x: float, y_top: float, h: float, blocks: list[tuple], anchor: str = "start") -> None:
    """Centre a content group (badge, label, description) vertically in its box (group centering)."""
    def height(size: float, n: int, leading: float) -> float:
        return size * (1 + leading * (n - 1)) if n else 0
    blocks = [b for b in blocks if b[1]]
    total = sum(height(b[2], len(b[1]), b[3].get("leading", 1.32)) for b in blocks)
    total += sum(b[4] for b in blocks[:-1])
    y = y_top + max(0.0, (h - total) / 2)
    for name, lines, size, kw, gap in blocks:
        leading = kw.get("leading", 1.32)
        cv.items(name, x, y + size * 0.86, lines, size, anchor=anchor, **kw) if kw.pop("split", False) else             cv.text(name, x, y + size * 0.86, lines, size, anchor=anchor, **kw)
        y += height(size, len(lines), leading) + gap


def _is_dark(hex_color: str) -> bool:
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b < 150


def _desc_lines(it: dict[str, Any]) -> str:
    d = it.get("desc", "")
    d = " ".join(d) if isinstance(d, list) else str(d)
    if not d and (it.get("out") or it.get("done")):
        d = " · ".join(f"{tag}: {it[key]}" for key, tag in (("out", "산출물"), ("done", "완료 기준")) if it.get(key))
    if not d and it.get("a") and it.get("b"):
        d = f"{it['a']} → {it['b']}"
    return d


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

ROW_TAGS = (("out", "산출물"), ("done", "완료 기준"))


def _cell_rows(it: dict[str, Any]) -> list[tuple[str, str]]:
    """Labelled rows (산출물 / 완료 기준) when the item carries them, else the plain description."""
    rows = [(tag, str(it[key])) for key, tag in ROW_TAGS if it.get(key)]
    return rows or [("", _desc_lines(it))]


def _draw_cell(cv: Canvas, fit: Fit, x: float, top: float, w: float, h: float, rows: list[tuple[str, str]],
               name: str) -> None:
    """Split a panel into equal labelled rows; each row's tag and text are centred as one group."""
    small, body, _ = _fs(cv)
    rh = h / len(rows)
    for j, (tag, text) in enumerate(rows):
        y = top + j * rh
        if j:
            cv.line(f"{name}-rule", x + body * 0.5, y, x + w - body * 0.5, y, cv.fam["rule"], 0.75)
        room = rh - body * 0.6 - (small * 1.5 if tag else 0)
        lines = fit.lines(text, body, w - body * 1.5, max(1, int(room / (body * 1.32))))
        _stack(cv, x + body * 0.5, y, rh, [(f"{name}-tag", [tag] if tag else [], small,
                                            dict(fill=cv.fam["muted"], bold=True), small * 0.45),
                                           (f"{name}-desc", lines, body, dict(split=True), 0)])


def _diamond(cv: Canvas, name: str, cx: float, cy: float, r: float, fill: str) -> None:
    cv.poly(name, [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill)


def draw_chevron(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    """Ordered chevrons. Optional per item: out/done (two labelled rows), gate (decision point after
    this step, the only accent on the page) and client (separate 고객 결정 row with approval markers)."""
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    gates = [i for i, it in enumerate(items[:-1]) if it.get("gate")]
    client = any(it.get("client") for it in items)
    if gates:
        Y, H = Y + small * 2.4, H - small * 2.4
    gap = body * (1.6 if gates else 0.35)
    cw = (W - gap * (n - 1)) / n
    ch = head * 3.2
    ramp = cv.fam["ramp"]
    client_h = 0.0
    if client:
        pw0 = cw - min(ch * 0.35, cw * 0.18) * 0.5 - body
        need = max(len(wrap(str(it.get("client", "")), body, pw0, max_lines=4)) for it in items)
        client_h = small * 1.95 + body * (1 + 1.32 * (need - 1)) + body * 1.2
        client_h = max(client_h, (H - ch - body * 0.9 - small * 1.8) * 0.42)
    for i, it in enumerate(items):
        x = X + i * (cw + gap)
        tip = min(ch * 0.35, cw * 0.18)
        pts = [(x, Y), (x + cw - tip, Y), (x + cw, Y + ch / 2), (x + cw - tip, Y + ch), (x, Y + ch)]
        if i:
            pts.append((x + tip, Y + ch / 2))
        # With a gate the steps share one tone so the gate is the single emphasis.
        fill = cv.fam["navy"] if gates else ramp[min(len(ramp) - 1, 1 + round(i * (len(ramp) - 2) / max(1, n - 1)))]
        dark = _is_dark(fill)
        cv.poly("step-chevron", pts, fill)
        lines = fit.lines(f"{i + 1}. {it['label']}", body, cw - tip * 2 - body * 0.6, 2, bold=True)
        cv.text_block("step-label", x + (cw - tip * (0 if i else 1)) / 2 + (tip / 2 if i else 0), Y, lines, body, ch,
                      fill=cv.fam["white"] if dark else cv.fam["navy"], bold=True, anchor="middle", leading=1.15)
        top = Y + ch + body * 0.9
        if it.get("period"):
            cv.text("step-period", x + cw / 2, top + small * 0.9, it["period"], small, fill=cv.fam["muted"], anchor="middle")
            top += small * 1.8
        pw = cw - tip * 0.5
        bottom = Y + H - (client_h + body * 0.5 if client else 0)
        cv.rect("step-panel", x, top, pw, bottom - top, fill=cv.fam["zebra"])
        _draw_cell(cv, fit, x, top, pw, bottom - top, _cell_rows(it), "step")
        if client:
            cy = Y + H - client_h
            cv.rect("client-cell", x, cy, pw, client_h, fill=cv.fam["white"], stroke=cv.fam["mid"])
            _draw_cell(cv, fit, x, cy, pw, client_h, [("고객 결정", str(it.get("client", "")))], "client")
            # Approval marker sits on the cell's top-right corner: the stage ends with the client's decision.
            _diamond(cv, "client-approval", x + pw - body * 0.6, cy, body * 0.42, cv.fam["navy"])
        if i in gates:
            gx = x + cw + gap / 2
            r = min(gap * 0.42, body * 0.7)
            cv.line("gate-rule", gx, Y - small * 0.9, gx, Y + H, cv.fam["accent"], 1.5, dash=True)
            _diamond(cv, "gate-marker", gx, Y + ch / 2, r, cv.fam["accent"])
            tag = fit.lines(str(it["gate"]), small, cw, 1, bold=True)
            cv.text("gate-label", gx, Y - small * 1.2, tag, small, fill=cv.fam["accent"], bold=True, anchor="middle")


def draw_steps(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    row = H / n
    r = min(row * 0.32, head * 1.1)
    label_w = W * 0.27
    for i, it in enumerate(items):
        y = Y + i * row
        cy = y + row / 2
        if i < n - 1:
            cv.line("steps-spine", X + r, cy + r, X + r, cy + row - r, cv.fam["mid"], 2)
        cv.rect("steps-dot", X, cy - r, 2 * r, 2 * r, fill=cv.fam["accent"] if i == 0 else cv.fam["navy"], rx=r)
        cv.text("steps-no", X + r, cy + head * 0.35, str(i + 1), head, fill=cv.fam["white"], bold=True, anchor="middle")
        lx = X + 2 * r + body
        lab = fit.lines(it["label"], head, label_w - body, 2, bold=True)
        cv.text_block("steps-label", lx, y, lab, head, row, fill=cv.fam["navy"], bold=True, leading=1.15)
        dx = lx + label_w
        max_l = max(1, int((row - body * 0.6 - (small * 1.6 if it.get("period") else 0)) / (body * 1.32)))
        desc = fit.lines(_desc_lines(it), body, X + W - dx, max_l)
        _stack(cv, dx, y, row, [("steps-period", [it["period"]] if it.get("period") else [], small,
                                 dict(fill=cv.fam["accent"], bold=True), small * 0.4),
                                ("steps-desc", desc, body, dict(split=True), 0)])
        if i:
            cv.line("steps-rule", lx, y, X + W, y, cv.fam["rule"], 0.75)


def draw_timeline(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    col = W / n
    size = small if n > 4 else body
    labels = [fit.lines(it["label"], head, col - body, 2, bold=True) for it in items]
    descs = [fit.lines(_desc_lines(it), size, col - body * 0.8, 6) for it in items]
    lab_h = head * 1.15 * max(len(l) for l in labels)
    desc_h = size * 1.32 * max(len(d) for d in descs)
    total = lab_h + body * 1.2 + head * 1.6 + body * 1.4 + body * 1.6 + desc_h
    top = Y + max(0.0, (H - total) / 2)
    axis_y = top + lab_h + body * 1.2 + head * 1.6 + body * 0.7
    cv.rect("tl-axis", X, axis_y - 2, W, 4, fill=cv.fam["mid"])
    for i, it in enumerate(items):
        cx = X + col * (i + 0.5)
        r = body * 0.7
        cv.text_block("tl-label", cx, top, labels[i], head, lab_h, fill=cv.fam["navy"], bold=True, anchor="middle",
                      leading=1.15)
        cv.text("tl-period", cx, axis_y - body * 1.3, it.get("period") or f"{i + 1}", head, fill=cv.fam["accent"],
                bold=True, anchor="middle")
        cv.rect("tl-dot", cx - r, axis_y - r, 2 * r, 2 * r, fill=cv.fam["accent"] if i == n - 1 else cv.fam["navy"], rx=r)
        dy = axis_y + body * 1.4
        cv.line("tl-tick", cx, axis_y + r, cx, dy, cv.fam["rule"], 1)
        cv.items("tl-desc", cx, dy + body * 1.4, descs[i], size, anchor="middle")
        if i:
            cv.line("tl-divider", X + col * i, dy, X + col * i, dy + body * 1.6 + desc_h, cv.fam["rule"], 0.75)


def draw_cards(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    cols = n if n <= 3 else (2 if n == 4 else 3)
    rows = math.ceil(n / cols)
    gap = body * 0.8
    cw = (W - gap * (cols - 1)) / cols
    chh = (H - gap * (rows - 1)) / rows
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x, y = X + c * (cw + gap), Y + r * (chh + gap)
        cv.rect("card-box", x, y, cw, chh, fill=cv.fam["zebra"], stroke=cv.fam["panel"])
        cv.rect("card-bar", x, y, cw, 3, fill=cv.fam["accent"])
        badge = it.get("value_label") or f"{i + 1:02d}"
        lab = fit.lines(it["label"], head, cw - body * 2, 2, bold=True)
        max_l = max(1, int((chh - head * 4.5) / (body * 1.32)))
        desc = fit.lines(_desc_lines(it), body, cw - body * 2, max_l)
        _stack(cv, x + body, y + 3, chh - 3, [
            ("card-no", [badge], head, dict(fill=cv.fam["accent"], bold=True), head * 0.35),
            ("card-label", lab, head, dict(fill=cv.fam["navy"], bold=True, leading=1.15), body * 0.6),
            ("card-desc", desc, body, dict(split=True), 0)])


def draw_table(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    if all(it.get("group") for it in items) and not data.get("columns"):
        _draw_group_table(cv, data, box, fit)
        return
    unit = data.get("unit", "")
    # (header, cell getter, relative width, emphasis); only columns that carry content
    cols: list[tuple[str, Callable[[dict], str], float, bool]] = [(data.get("label_header", "구분"), lambda it: it["label"], 1.0, True)]
    if data.get("columns") and all("a" in it for it in items):
        cols += [(data["columns"][0], lambda it: str(it.get("a", "")), 1.8, False),
                 (data["columns"][1], lambda it: str(it.get("b", "")), 1.8, False)]
    elif any(it.get("desc") for it in items):
        cols.append((data.get("desc_header", "내용"), _desc_lines, 2.8, False))
    if all("x" in it and "y" in it for it in items):
        axes = data.get("axes", {"x": "x", "y": "y"})
        cols += [(axes["y"], lambda it: f"{float(it['y']):g}", 0.6, False), (axes["x"], lambda it: f"{float(it['x']):g}", 0.6, False)]
    if all(it.get("value") is not None for it in items):
        cols.append((data.get("value_header", f"값({unit})" if unit else "값"),
                     lambda it: f"{float(it['value']):,g}{it.get('unit', '') if not unit else ''}", 0.7, True))
    total = sum(c[2] for c in cols)
    widths = [c[2] / total for c in cols]
    hh = body * 2.4
    cv.rect("tbl-head", X, Y, W, hh, fill=cv.fam["navy"])
    x = X
    for (h, *_), w in zip(cols, widths):
        cv.text("tbl-head-text", x + body * 0.7, Y + hh / 2 + body * 0.35, h, body, fill=cv.fam["white"], bold=True)
        x += W * w
    row = (H - hh) / len(items)
    for i, it in enumerate(items):
        y = Y + hh + i * row
        if i % 2:
            cv.rect("tbl-zebra", X, y, W, row, fill=cv.fam["zebra"])
        cv.line("tbl-rule", X, y + row, X + W, y + row, cv.fam["rule"], 0.75)
        x = X
        max_l = max(1, int((row - body * 0.5) / (body * 1.3)))
        for (h, get, _, bold), w in zip(cols, widths):
            lines = fit.lines(get(it), body, W * w - body * 1.4, max_l, bold=bold)
            cv.text_block("tbl-cell", x + body * 0.7, y, lines, body, row,
                          fill=cv.fam["navy"] if bold else cv.fam["text"], bold=bold, leading=1.3)
            x += W * w


def _draw_group_table(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    groups = _groups(data["items"])
    has_desc = any(_desc_lines(it) for it in data["items"])
    widths = [0.2, 0.3, 0.5] if has_desc else [0.24, 0.76]
    heads = [data.get("group_header", "구분"), data.get("label_header", "항목")] + (["내용"] if has_desc else [])
    hh = body * 2.4
    cv.rect("tbl-head", X, Y, W, hh, fill=cv.fam["navy"])
    x = X
    for h, w in zip(heads, widths):
        cv.text("tbl-head-text", x + body * 0.7, Y + hh / 2 + body * 0.35, h, body, fill=cv.fam["white"], bold=True)
        x += W * w
    row = (H - hh) / len(data["items"])
    y = Y + hh
    for gi, (g, members) in enumerate(groups):
        gh = row * len(members)
        cv.rect("tbl-group", X, y, W * widths[0], gh, fill=cv.fam["pale"])
        cv.text_block("tbl-group-text", X + body * 0.7, y, fit.lines(g, body, W * widths[0] - body * 1.4, 3, bold=True),
                      body, gh, fill=cv.fam["navy"], bold=True)
        for k, it in enumerate(members):
            ry = y + k * row
            cv.line("tbl-rule", X + W * widths[0], ry + row, X + W, ry + row, cv.fam["rule"], 0.75)
            x = X + W * widths[0]
            cells = [it["label"]] + ([_desc_lines(it)] if has_desc else [])
            for j, (cell, w) in enumerate(zip(cells, widths[1:])):
                lines = fit.lines(cell, body, W * w - body * 1.4, max(1, int((row - body * 0.5) / (body * 1.3))), bold=j == 0)
                cv.text_block("tbl-cell", x + body * 0.7, ry, lines, body, row, bold=j == 0,
                              fill=cv.fam["navy"] if j == 0 else cv.fam["text"])
                x += W * w
        y += gh
        cv.line("tbl-group-rule", X, y, X + W, y, cv.fam["navy"] if gi < len(groups) - 1 else cv.fam["rule"], 1)


def draw_hub(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    cx, cy = X + W / 2, Y + H / 2
    hub_w, hub_h = W * 0.2, min(H * 0.3, head * 5)
    cv.rect("hub-core", cx - hub_w / 2, cy - hub_h / 2, hub_w, hub_h, fill=cv.fam["navy"], rx=hub_h / 2)
    core_txt = data.get("hub") or re.split(r"\s[–-]\s", re.sub(r"^\s*[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩIVX\d]+\.\s*", "", data.get("title", "")))[-1]
    core = fit.lines(core_txt, head, hub_w - body * 2, 2, bold=True)
    cv.text_block("hub-core-text", cx, cy - hub_h / 2, core, head, hub_h, fill=cv.fam["white"], bold=True,
                  anchor="middle", leading=1.15)
    left = [it for i, it in enumerate(items) if i % 2 == 0]
    right = [it for i, it in enumerate(items) if i % 2 == 1]
    side_w = (W - hub_w) / 2 - body * 2.2
    for side, group in ((-1, left), (1, right)):
        k = len(group)
        if not k:
            continue
        bh = (H - body * (k - 1)) / k
        for j, it in enumerate(group):
            y = Y + j * (bh + body)
            x = X if side < 0 else X + W - side_w
            cv.rect("hub-node", x, y, side_w, bh, fill=cv.fam["zebra"], stroke=cv.fam["panel"])
            cv.rect("hub-node-bar", x if side > 0 else x + side_w - 4, y, 4, bh, fill=cv.fam["accent"])
            ax = x + side_w if side < 0 else x
            cv.line("hub-link", ax, y + bh / 2, cx + side * hub_w * 0.42, cy, cv.fam["light"], 1.5)
            lab = fit.lines(it["label"], head, side_w - body * 1.6, 1, bold=True)
            max_l = max(1, int((bh - head * 2.4) / (body * 1.32)))
            desc = fit.lines(_desc_lines(it), body, side_w - body * 1.6, max_l)
            _stack(cv, x + body * 0.8 + (4 if side > 0 else 0), y, bh, [
                ("hub-label", lab, head, dict(fill=cv.fam["navy"], bold=True), body * 0.5),
                ("hub-desc", desc, body, dict(split=True), 0)])


def _groups(items: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
    order: list[str] = []
    for it in items:
        g = it.get("group", "")
        if g not in order:
            order.append(g)
    return [(g, [it for it in items if it.get("group", "") == g]) for g in order]


def draw_tree(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    groups = _groups(data["items"])
    root_w = W * 0.2
    grp_w = W * 0.22
    leaf_x = X + root_w + grp_w + body * 4
    leaf_w = X + W - leaf_x
    total = sum(len(g[1]) for g in groups)
    unit = H / total
    root = fit.lines(data.get("root") or data.get("title", ""), head, root_w - body * 1.6, 3, bold=True)
    cv.rect("tree-root", X, Y + H / 2 - head * 2.4, root_w, head * 4.8, fill=cv.fam["navy"])
    cv.text_block("tree-root-text", X + root_w / 2, Y + H / 2 - head * 2.4, root, head, head * 4.8,
                  fill=cv.fam["white"], bold=True, anchor="middle", leading=1.15)
    gx = X + root_w + body * 2
    y = Y
    for g, members in groups:
        gh = unit * len(members)
        gy = y + gh / 2
        cv.path("tree-link", f"M{X + root_w:.1f},{Y + H / 2:.1f} H{gx - body:.1f} V{gy:.1f} H{gx:.1f}", cv.fam["mid"])
        bh = min(gh - body * 0.6, head * 3.4)
        cv.rect("tree-group", gx, gy - bh / 2, grp_w, bh, fill=cv.fam["accent"])
        gl = fit.lines(g or "—", body, grp_w - body * 1.2, 2, bold=True)
        cv.text_block("tree-group-text", gx + grp_w / 2, gy - bh / 2, gl, body, bh, fill=cv.fam["white"], bold=True,
                      anchor="middle", leading=1.15)
        for k, it in enumerate(members):
            ly = y + unit * k
            lc = ly + unit / 2
            cv.path("tree-leaf-link", f"M{gx + grp_w:.1f},{gy:.1f} H{leaf_x - body * 2:.1f} V{lc:.1f} H{leaf_x:.1f}",
                    cv.fam["rule"], 1)
            cv.rect("tree-leaf", leaf_x, ly + body * 0.2, leaf_w, unit - body * 0.4, fill=cv.fam["zebra"])
            max_l = max(1, int((unit - body * 0.6) / (body * 1.3)))
            txt = it["label"] + (f" — {_desc_lines(it)}" if _desc_lines(it) else "")
            lines = fit.lines(txt, body, leaf_w - body * 1.4, max_l)
            cv.text_block("tree-leaf-text", leaf_x + body * 0.7, ly + body * 0.2, lines, body, unit - body * 0.4)
        y += gh


def draw_layers(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    groups = _groups(data["items"])
    k = len(groups)
    gap = body * 0.5
    bh = (H - gap * (k - 1)) / k
    lab_w = W * 0.2
    for i, (g, members) in enumerate(groups):
        y = Y + i * (bh + gap)
        fill = [cv.fam["navy"], cv.fam["accent"], cv.fam["light"], cv.fam["mid"]][min(i, 3)]
        dark = fill in (cv.fam["navy"], cv.fam["accent"])
        cv.rect("layer-label", X, y, lab_w, bh, fill=fill)
        gl = fit.lines(g or "—", head, lab_w - body * 1.2, 2, bold=True)
        cv.text_block("layer-label-text", X + lab_w / 2, y, gl, head, bh,
                      fill=cv.fam["white"] if dark else cv.fam["navy"], bold=True, anchor="middle", leading=1.15)
        cv.rect("layer-band", X + lab_w, y, W - lab_w, bh, fill=cv.fam["zebra"])
        m = len(members)
        cw = (W - lab_w - body * (m + 1)) / m
        for j, it in enumerate(members):
            x = X + lab_w + body + j * (cw + body)
            cv.rect("layer-cell", x, y + body * 0.5, cw, bh - body, fill=cv.fam["white"], stroke=cv.fam["panel"])
            max_l = max(1, int((bh - body * 1.6) / (body * 1.3)))
            txt = it["label"] if not _desc_lines(it) else f"{it['label']}: {_desc_lines(it)}"
            lines = fit.lines(txt, body, cw - body * 1.2, max_l)
            cv.text_block("layer-cell-text", x + cw / 2, y + body * 0.5, lines, body, bh - body, anchor="middle")


def draw_two_column(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    cols = data.get("columns", ["현행", "목표"])
    lab_w = W * 0.18
    arrow = body * 2.4
    cw = (W - lab_w - arrow - body) / 2
    xa = X + lab_w + body * 0.5
    xb = xa + cw + arrow
    hh = head * 2.4
    cv.rect("cmp-head-a", xa, Y, cw, hh, fill=cv.fam["neutral"])
    cv.rect("cmp-head-b", xb, Y, cw, hh, fill=cv.fam["navy"])
    cv.text("cmp-head-a-text", xa + cw / 2, Y + hh / 2 + head * 0.35, cols[0], head, fill=cv.fam["white"], bold=True, anchor="middle")
    cv.text("cmp-head-b-text", xb + cw / 2, Y + hh / 2 + head * 0.35, cols[1], head, fill=cv.fam["white"], bold=True, anchor="middle")
    row = (H - hh - body * 0.5) / len(items)
    for i, it in enumerate(items):
        y = Y + hh + body * 0.5 + i * row
        lab = fit.lines(it["label"], body, lab_w - body * 0.4, 3, bold=True)
        cv.text_block("cmp-label", X, y, lab, body, row, fill=cv.fam["navy"], bold=True, leading=1.2)
        max_l = max(1, int((row - body * 0.8) / (body * 1.3)))
        cv.rect("cmp-a", xa, y + body * 0.2, cw, row - body * 0.4, fill=cv.fam["zebra"])
        cv.rect("cmp-b", xb, y + body * 0.2, cw, row - body * 0.4, fill=cv.fam["pale"])
        cv.text_block("cmp-a-text", xa + body * 0.7, y, fit.lines(it.get("a", ""), body, cw - body * 1.4, max_l), body, row)
        cv.text_block("cmp-b-text", xb + body * 0.7, y, fit.lines(it.get("b", ""), body, cw - body * 1.4, max_l), body, row,
                      fill=cv.fam["navy"])
        ax = xa + cw + body * 0.5
        cy = y + row / 2
        cv.poly("cmp-arrow", [(ax, cy - body * 0.6), (ax + arrow - body, cy), (ax, cy + body * 0.6)], cv.fam["accent"])


def draw_matrix(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    axes = data.get("axes", {"x": "x", "y": "y"})
    items = data["items"]
    gx, gy, gw, gh = X + body * 3, Y, min(W * 0.58, H * 1.4), H - body * 2.6
    hi = data.get("scale", 5)
    for r in range(2):
        for c in range(2):
            fill = cv.fam["panel"] if (r, c) == (0, 1) else cv.fam["zebra"]
            cv.rect("mx-cell", gx + c * gw / 2, gy + r * gh / 2, gw / 2, gh / 2, fill=fill, stroke=cv.fam["white"], sw=2)
    for q, (qx, qy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        label = (data.get("quadrants") or [None] * 4)[q]
        if label:
            cv.text("mx-quadrant", gx + qx * gw / 2 + body * 0.5, gy + qy * gh / 2 + small * 1.5, label, small,
                    fill=cv.fam["muted"], bold=True)
    cv.text("mx-x-axis", gx + gw / 2, gy + gh + body * 1.9, f"{axes['x']} →", body, fill=cv.fam["navy"], bold=True, anchor="middle")
    cv.text("mx-y-axis", X, gy + gh / 2, axes["y"], body, fill=cv.fam["navy"], bold=True)
    cv.text("mx-y-high", X, gy + small, "높음", small, fill=cv.fam["muted"])
    cv.text("mx-y-low", X, gy + gh - small * 0.3, "낮음", small, fill=cv.fam["muted"])
    lx = gx + gw + body * 2
    lw = X + W - lx
    row = min(body * 3.2, gh / max(1, len(items)))
    for i, it in enumerate(items):
        px = gx + (float(it["x"]) - 0.5) / hi * gw
        py = gy + gh - (float(it["y"]) - 0.5) / hi * gh
        r = body * 0.95
        cv.rect("mx-dot", px - r, py - r, 2 * r, 2 * r, fill=cv.fam["accent"], rx=r)
        cv.text("mx-dot-no", px, py + small * 0.35, str(i + 1), small, fill=cv.fam["white"], bold=True, anchor="middle")
        y = gy + i * row
        cv.text("mx-legend-no", lx, y + body, f"{i + 1}", body, fill=cv.fam["accent"], bold=True)
        lines = fit.lines(it["label"] + (f" — {_desc_lines(it)}" if _desc_lines(it) else ""), small, lw - body * 1.6,
                          max(1, int(row / (small * 1.3))))
        cv.items("mx-legend", lx + body * 1.4, y + body, lines, small, leading=1.25)


def _bar_value(it: dict[str, Any]) -> float:
    if it.get("value") is not None:
        return float(it["value"])
    return float(it["x"]) * float(it["y"])


def draw_bars(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    scored = any(it.get("value") is None for it in items)
    if scored:  # matrix content: rank by effect × ease
        items = sorted(items, key=_bar_value, reverse=True)
        axes = data.get("axes", {"x": "x", "y": "y"})
        cv.text("bar-note", X + W, Y + small, f"점수 = {axes['y']} × {axes['x']}", small, fill=cv.fam["muted"], anchor="end")
    vmax = max(_bar_value(it) for it in items) or 1
    lab_w = W * 0.24
    val_w = body * 7
    bar_x = X + lab_w
    bar_w = W - lab_w - val_w
    top = Y + (small * 2 if scored else 0)
    row = min((Y + H - top) / len(items), head * 4.2)
    top += (Y + H - top - row * len(items)) / 2
    unit = data.get("unit") or items[0].get("unit", "")
    for i, it in enumerate(items):
        y = top + i * row
        desc = fit.lines(_desc_lines(it), small, bar_w + val_w - body, 1) if _desc_lines(it) else []
        bh = min(row * 0.42, body * 2)
        group = bh + (small * 1.7 if desc else 0)
        by = y + (row - group) / 2
        lab = fit.lines(it["label"], body, lab_w - body, 2, bold=True)
        cv.text_block("bar-label", X, by, lab, body, bh, fill=cv.fam["navy"], bold=True, leading=1.15)
        w = max(2.0, bar_w * _bar_value(it) / vmax)
        cv.rect("bar", bar_x, by, w, bh, fill=cv.fam["accent"] if i == 0 else cv.fam["light"])
        val = (f"{_bar_value(it):.1f}" if scored else f"{_bar_value(it):,g}{it.get('unit', unit)}")
        cv.text("bar-value", bar_x + w + body * 0.5, by + bh / 2 + body * 0.35, val, body, fill=cv.fam["navy"], bold=True)
        if desc:
            cv.text("bar-desc", bar_x, by + bh + small * 1.4, desc, small, fill=cv.fam["muted"])
        if i:
            cv.line("bar-rule", X, y, X + W, y, cv.fam["rule"], 0.5)


def draw_kpi(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    gap = body
    cw = (W - gap * (n - 1)) / n
    big = min(head * 3.2, cw / 4.2)
    for i, it in enumerate(items):
        x = X + i * (cw + gap)
        cv.rect("kpi-box", x, Y, cw, H, fill=cv.fam["zebra"])
        cv.rect("kpi-bar", x, Y, cw, 4, fill=cv.fam["accent"])
        cv.text("kpi-label", x + cw / 2, Y + head * 2.4, fit.lines(it["label"], head, cw - body * 2, 2, bold=True), head,
                fill=cv.fam["navy"], bold=True, anchor="middle", leading=1.15)
        val = f"{float(it['value']):,g}"
        cv.text("kpi-value", x + cw / 2, Y + H * 0.48, val, big, fill=cv.fam["accent"], bold=True, anchor="middle")
        if it.get("unit") or data.get("unit"):
            cv.text("kpi-unit", x + cw / 2, Y + H * 0.48 + head * 1.5, it.get("unit") or data["unit"], head, fill=cv.fam["muted"], anchor="middle")
        max_l = max(1, int((H * 0.36 - body) / (body * 1.3)))
        desc = fit.lines(_desc_lines(it), body, cw - body * 2, max_l)
        cv.items("kpi-desc", x + cw / 2, Y + H * 0.66, desc, body, anchor="middle")


def draw_chain(cv: Canvas, data: dict[str, Any], box, fit: Fit) -> None:
    X, Y, W, H = box
    small, body, head = _fs(cv)
    items = data["items"]
    n = len(items)
    arrow = body * 2.6
    cw = (W - arrow * (n - 1)) / n
    bh = min(H * 0.36, head * 6)
    descs = [fit.lines(_desc_lines(it), body, cw - body * 0.6, 5) for it in items]
    desc_h = body * 1.32 * max(len(d) for d in descs) if any(descs) else 0
    by = Y + max(small * 2, (H - (bh + body * 1.8 + desc_h)) / 2)
    for i, it in enumerate(items):
        x = X + i * (cw + arrow)
        last = i == n - 1
        cv.rect("chain-box", x, by, cw, bh, fill=cv.fam["navy"] if last else cv.fam["panel"], rx=4)
        lab = fit.lines(it["label"], head, cw - body * 1.6, 3, bold=True)
        cv.text_block("chain-label", x + cw / 2, by, lab, head, bh, fill=cv.fam["white"] if last else cv.fam["navy"],
                      bold=True, anchor="middle", leading=1.15)
        tag = it.get("tag") or ("결과" if last else ("원인" if i == 0 else "영향"))
        cv.text("chain-tag", x + cw / 2, by - small * 0.8, tag, small, fill=cv.fam["muted"], bold=True, anchor="middle")
        if not last:
            ax = x + cw + body * 0.3
            cy = by + bh / 2
            cv.poly("chain-arrow", [(ax, cy - body * 0.7), (ax + arrow - body * 0.6, cy), (ax, cy + body * 0.7)],
                    cv.fam["accent"])
        cv.items("chain-desc", x + cw / 2, by + bh + body * 1.8, descs[i], body, anchor="middle")


# name: (relations served, feasible(data) -> bool, draw, Korean description)
FORMS: dict[str, tuple[tuple[str, ...], Callable[[dict], bool], Callable, str]] = {
    "chevron": (("sequence",), lambda d: 3 <= len(d["items"]) <= 6, draw_chevron, "가로 셰브런 단계 + 단계별 설명"),
    "steps": (("sequence", "cause"), lambda d: 2 <= len(d["items"]) <= 7, draw_steps, "세로 번호 단계(스파인) + 설명"),
    "timeline": (("sequence",), lambda d: 3 <= len(d["items"]) <= 7 and sum(bool(i.get("period")) for i in d["items"]) * 2 >= len(d["items"]),
                 draw_timeline, "시간축 + 시점 마일스톤"),
    "cards": (("parallel", "comparison", "cause", "quantity"), lambda d: 2 <= len(d["items"]) <= 6 and all(_desc_lines(i) for i in d["items"]), draw_cards, "번호 카드 그리드"),
    "table": (RELATIONS, lambda d: 2 <= len(d["items"]) <= 9, draw_table, "표(구분 × 내용, 비교 2열)"),
    "hub": (("parallel",), lambda d: 3 <= len(d["items"]) <= 6, draw_hub, "중심 개념 + 구성 요소(프레임워크)"),
    "tree": (("hierarchy", "cause"), lambda d: len(_groups(d["items"])) >= 2 and len(d["items"]) <= 10, draw_tree, "트리(상위 → 그룹 → 항목)"),
    "layers": (("hierarchy",), lambda d: 2 <= len(_groups(d["items"])) <= 4 and max(len(m) for _, m in _groups(d["items"])) <= 4,
               draw_layers, "층 구조(그룹별 띠)"),
    "two_column": (("comparison",), lambda d: bool(d.get("columns")) and all("a" in i and "b" in i for i in d["items"]) and len(d["items"]) <= 6,
                   draw_two_column, "현행 → 목표 2열 대비"),
    "matrix": (("matrix",), lambda d: all("x" in i and "y" in i for i in d["items"]) and len(d["items"]) <= 10, draw_matrix,
               "2×2 매트릭스 + 범례"),
    "bars": (("quantity", "matrix"), lambda d: all(i.get("value") is not None or ("x" in i and "y" in i) for i in d["items"]) and len(d["items"]) <= 8,
             draw_bars, "가로 막대(크기 비교)"),
    "kpi": (("quantity",), lambda d: all(i.get("value") is not None for i in d["items"]) and len(d["items"]) <= 4, draw_kpi,
            "큰 숫자 카드"),
    "chain": (("cause",), lambda d: 2 <= len(d["items"]) <= 5, draw_chain, "원인 → 영향 → 결과 체인"),
}

PREFERENCE = {
    "sequence": ["chevron", "steps", "timeline", "table"],
    "parallel": ["cards", "hub", "table"],
    "hierarchy": ["tree", "layers", "table"],
    "comparison": ["two_column", "table", "cards"],
    "matrix": ["matrix", "bars", "table"],
    "quantity": ["bars", "kpi", "table", "cards"],
    "cause": ["chain", "tree", "steps", "table"],
}
# When the text is long, prefer forms with wide text cells.
LONG_TEXT_FIRST = {"sequence": ["steps", "chevron", "table"], "parallel": ["table", "cards", "hub"]}


# ---------------------------------------------------------------------------
# Inference and ranking
# ---------------------------------------------------------------------------

def infer_relation(data: dict[str, Any]) -> tuple[str, str]:
    items = data.get("items", [])
    rel = data.get("relation", "auto")
    if rel in RELATIONS:
        return rel, "지정"
    if items and all("x" in i and "y" in i for i in items):
        return "matrix", "모든 항목에 x·y 점수"
    if items and data.get("columns") and all("a" in i and "b" in i for i in items):
        return "comparison", "항목마다 두 열 값(a·b)"
    if items and all(i.get("value") is not None for i in items):
        return "quantity", "모든 항목에 수치"
    if items and len({i.get("group", "") for i in items}) >= 2 and all(i.get("group") for i in items):
        return "hierarchy", "항목에 상위 그룹"
    text = " ".join(f"{i.get('label', '')} {_desc_lines(i)}" for i in items) + " " + data.get("governing", "")
    if sum(bool(i.get("period")) for i in items) * 2 >= max(1, len(items)) or sum(bool(ORDINAL.match(i.get("label", ""))) for i in items) >= 2 \
            or re.search(r"단계|절차|순서|프로세스|로드맵|추진\s?일정", data.get("title", "") + data.get("governing", "")):
        return "sequence", "시점·단계 번호·절차어"
    if CAUSE_WORDS.search(data.get("title", "") + data.get("governing", "")) and len(items) <= 5:
        return "cause", "원인·영향어"
    return "parallel", "순서·수치·위계 표지 없음"


def _text_load(data: dict[str, Any]) -> float:
    items = data.get("items", [])
    return sum(len(_desc_lines(i)) for i in items) / max(1, len(items))


def recommend(data: dict[str, Any], count: int = 3) -> dict[str, Any]:
    rel, why = infer_relation(data)
    order = list(PREFERENCE[rel])
    if _text_load(data) > 45 and rel in LONG_TEXT_FIRST:
        order = LONG_TEXT_FIRST[rel] + [f for f in order if f not in LONG_TEXT_FIRST[rel]]
    order += [f for f in ("table", "cards", "steps") if f not in order]
    ranked, skipped = [], []
    for f in order:
        rels, ok, _, desc = FORMS[f]
        try:
            feasible = ok(data)
        except (KeyError, ValueError, TypeError):
            feasible = False
        (ranked if feasible else skipped).append({"form": f, "desc": desc, "fits_relation": rel in rels})
    return {"relation": rel, "relation_ko": RELATION_KO[rel], "reason": why, "candidates": ranked[:count],
            "skipped": [s["form"] for s in skipped]}


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def check(data: dict[str, Any]) -> list[str]:
    errors = []
    items = data.get("items")
    if not isinstance(items, list) or len(items) < 2:
        errors.append("items는 2개 이상의 목록이어야 합니다")
        return errors
    for k, it in enumerate(items, 1):
        if not str(it.get("label", "")).strip():
            errors.append(f"items[{k}]에 label이 없습니다")
        if it.get("value") is not None and not isinstance(it["value"], (int, float)):
            errors.append(f"items[{k}].value는 숫자여야 합니다")
    if data.get("relation", "auto") not in RELATIONS + ("auto",):
        errors.append(f"relation은 auto 또는 {', '.join(RELATIONS)}")
    return errors


def build_one(data: dict[str, Any], form: str, family: str, base: Optional[Path], mode: str,
              near: Optional[Path] = None) -> tuple[str, list[str]]:
    if family not in FAMILIES:
        raise DiagramError(f"unknown family {family!r}; use one of {sorted(FAMILIES)}")
    base = base or find_template(family, "03a_content.svg", near)
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.parse(str(base)).getroot()
    area = parent = None
    for p in root.iter():
        for ch in list(p):
            if ch.get("id") in ("content-area", "report-diagram"):
                area, parent = ch, p
                break
        if area is not None:
            break
    fam = FAMILIES[family]
    if area is None or parent is None:
        # A drawn deck page as base: keep its chrome, redraw only the body between governing and source.
        area, parent, (X, Y, W, H), fam = _page_zone(root, fam, base)
    else:
        X, Y, W, H = area_bounds(area, family)
    cv = Canvas(fam, "content-diagram")
    fit = Fit()
    box = _conclusion(cv, data, (X, Y, W, H), fit)
    FORMS[form][2](cv, data, box, fit)
    fragment = ET.fromstring(f'<svg xmlns="{SVG_NS}">{cv.svg(form)}</svg>')[0]
    idx = list(parent).index(area)
    parent.remove(area)
    parent.insert(idx, fragment)
    root.set("data-content-diagram", form)
    _fill_placeholder(root, "content-title", data.get("title"))
    _fill_placeholder(root, "key-message", data.get("governing"))
    _fill_placeholder(root, "source-note", data.get("source", ""))
    _fill_placeholder(root, "footer-section", data.get("section", ""))
    _fill_placeholder(root, "page-number", str(data.get("page", "")))
    if mode == "flat":
        _flatten_structure(root)
    warnings = [f"글자가 잘림: '{c}…'" for c in fit.clipped]
    small = FAMILIES[family]["min_px"]
    for el in root.iter(f"{{{SVG_NS}}}text"):
        try:
            if 0 < float(el.get("font-size", "99")) < small - 0.01:
                warnings.append(f"글자 {el.get('font-size')}px < {small}px")
                break
        except ValueError:
            pass
    return ET.tostring(root, encoding="unicode"), warnings


CHROME_IDS = re.compile(r"^(header|title|page-title|content-title|governing|key-message|source|source-note|footer|"
                        r"page-number|footer-section|logo|background|bg)", re.I)


def _bottom(el: ET.Element) -> float:
    ys = [0.0]
    for e in el.iter():
        try:
            if e.get("height") and e.get("y") is not None:
                ys.append(float(e.get("y") or 0) + float(e.get("height") or 0))
            elif e.tag.endswith("text") and e.get("y"):
                ys.append(float(e.get("y") or 0) + float(e.get("font-size") or 12) * 0.3)
        except ValueError:
            pass
    return max(ys)


def _top(el: ET.Element) -> float:
    ys = []
    for e in el.iter():
        try:
            if e.tag.endswith("text") and e.get("y"):
                ys.append(float(e.get("y") or 0) - float(e.get("font-size") or 12))
            elif e.get("y") is not None and e.get("height"):
                ys.append(float(e.get("y") or 0))
        except ValueError:
            pass
    return min(ys) if ys else 1e9


def _page_zone(root: ET.Element, fam: dict[str, Any], base: Path):
    """Body zone of a hand-drawn page: below header/governing, above source/footer."""
    vb = (root.get("viewBox") or "0 0 960 540").split()
    cw, ch = float(vb[2]), float(vb[3])
    kept = [c for c in list(root) if CHROME_IDS.match(c.get("id") or "") or
            (c.get("id") is None and c.tag.endswith("rect") and float(c.get("width") or 0) >= cw - 1)]
    if not any(re.match(r"governing|key-message", c.get("id") or "") for c in kept):
        raise DiagramError(f"{base.name}: no content-area placeholder and no governing group to anchor the body")
    heads = [c for c in kept if re.match(r"header|title|page-title|content-title|governing|key-message", c.get("id") or "")]
    tails = [c for c in kept if re.match(r"source|footer|page-number", c.get("id") or "")]
    gov = next(c for c in kept if re.match(r"governing|key-message", c.get("id") or ""))
    xs = [float(e.get("x") or 0) for e in gov.iter() if e.get("x") is not None]
    left = min(xs) if xs else 34.0
    top = max(_bottom(c) for c in heads) + 18
    bottom = min((_top(c) for c in tails), default=ch - 40) - 14
    for c in list(root):
        if c not in kept:
            root.remove(c)
    idx = min((list(root).index(c) for c in tails), default=len(root))
    holder = ET.Element(f"{{{SVG_NS}}}g", {"id": "content-area"})
    root.insert(idx, holder)
    fam = _lock_tokens(dict(fam), base)
    if root.get("font-family") and not fam.get("_locked_font"):
        fam["font"] = root.get("font-family")
    return holder, root, (left, top, cw - 2 * left, bottom - top), fam


def _lock_tokens(fam: dict[str, Any], base: Path) -> dict[str, Any]:
    """A drawn deck keeps its own palette and type sizes: read the project's spec_lock.md."""
    lock = next((d / "spec_lock.md" for d in list(base.resolve().parents)[:5] if (d / "spec_lock.md").is_file()), None)
    if lock is None:
        return fam
    vals = dict(re.findall(r"^-\s*([a-z_]+):\s*(.+?)\s*$", lock.read_text(encoding="utf-8"), re.M))
    hexes = {k: v for k, v in vals.items() if re.fullmatch(r"#[0-9A-Fa-f]{6}", v)}
    # Only locked colors (qaqc C07): greys and panel stand in for the tint ramp.
    navy = hexes.get("primary", fam["navy"])
    panel = hexes.get("panel", fam["panel"])
    border = hexes.get("border", fam["rule"])
    grey = hexes.get("text_secondary", fam["muted"])
    fam.update(navy=navy, accent=hexes.get("accent", navy), light=border, mid=border, panel=panel, zebra=panel,
               pale=panel, rule=border, neutral=grey, muted=grey, text=hexes.get("text", fam["text"]),
               ramp=[panel, border, grey, navy, navy])
    try:
        small = float(vals.get("note") or vals.get("annotation") or fam["ladder"][0])
        body = float(vals.get("body") or fam["ladder"][1])
        head = float(vals.get("subheading") or fam["ladder"][2])
        fam["ladder"] = (small, body, head)
        fam["min_px"] = float(vals.get("source") or fam["min_px"])
    except ValueError:
        pass
    if vals.get("font_family"):
        fam["font"], fam["_locked_font"] = vals["font_family"], True
    return fam


def build_variants(data: dict[str, Any], family: str, out: Path, count: int, forms: Optional[list[str]],
                   base: Optional[Path], mode: str) -> dict[str, Any]:
    rec = recommend(data, count=len(FORMS))
    chosen = forms or [c["form"] for c in rec["candidates"]]
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for form in chosen:
        if form not in FORMS:
            raise DiagramError(f"unknown form {form!r}; use one of {sorted(FORMS)}")
        svg, warnings = build_one(data, form, family, base, mode, near=out)
        results.append({"form": form, "svg": svg, "warnings": warnings,
                        "fits_relation": rec["relation"] in FORMS[form][0], "desc": FORMS[form][3]})
        if len([r for r in results if not r["warnings"]]) >= count and not forms:
            break
    # A variant that clips text drops behind those that fit; keep the relation order otherwise.
    results.sort(key=lambda r: (bool(r["warnings"]), not r["fits_relation"]))
    results = results[:count]
    for old in out.glob("v*_*.svg"):
        old.unlink()
    index = []
    for i, r in enumerate(results, 1):
        path = out / f"v{i}_{r['form']}.svg"
        path.write_text(r["svg"], encoding="utf-8")
        _copy_chrome_images(r["svg"], base or find_template(family, "03a_content.svg", out), path)
        index.append({"rank": i, "form": r["form"], "file": path.name, "desc": r["desc"],
                      "fits_relation": r["fits_relation"], "warnings": r["warnings"]})
    summary = {"title": data.get("title", ""), "page": data.get("page"), "family": family, "relation": rec["relation"],
               "relation_ko": rec["relation_ko"], "reason": rec["reason"], "recommended": index[0]["file"] if index else None,
               "variants": index}
    (out / "variants.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "variants.html").write_text(_compare_html(summary, out), encoding="utf-8")
    return summary


def _compare_html(summary: dict[str, Any], out: Path) -> str:
    cards = []
    for v in summary["variants"]:
        warn = "".join(f"<li>{html.escape(w)}</li>" for w in v["warnings"]) or "<li>잘림 없음</li>"
        tag = "추천" if v["rank"] == 1 else f"후보 {v['rank']}"
        cards.append(f'<figure><figcaption><b>{tag} · {html.escape(v["form"])}</b> — {html.escape(v["desc"])}'
                     f'<ul>{warn}</ul></figcaption><img src="{html.escape(v["file"])}" alt="{html.escape(v["form"])}"></figure>')
    return (f'<!doctype html><meta charset="utf-8"><title>{html.escape(summary["title"])} — 도식 후보</title>'
            '<style>body{font-family:"Malgun Gothic",sans-serif;margin:16px;background:#f5f6f8}'
            'figure{background:#fff;margin:0 0 16px;padding:12px;border:1px solid #ddd}img{width:100%;max-width:960px;display:block;border:1px solid #eee}'
            'figcaption{margin-bottom:8px}ul{margin:4px 0 0 18px;color:#666;font-size:13px}</style>'
            f'<h1 style="font-size:18px">{html.escape(summary["title"])}</h1>'
            f'<p>관계: {summary["relation_ko"]} ({html.escape(summary["reason"])}) · 고르기: '
            f'<code>content_diagrams.py pick {html.escape(str(out))} &lt;번호&gt; -o &lt;svg_output/NN_이름.svg&gt;</code></p>'
            + "".join(cards))


def pick(out: Path, which: str, target: Path) -> Path:
    summary = json.loads((out / "variants.json").read_text(encoding="utf-8"))
    match = next((v for v in summary["variants"] if str(v["rank"]) == which or v["form"] == which), None)
    if match is None:
        raise DiagramError(f"no variant {which!r} in {out}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out / match["file"], target)
    no = re.match(r"(\d{1,3})_", target.name)
    if no and not summary.get("page"):  # number the page from its deck position
        ET.register_namespace("", SVG_NS)
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        tree = ET.parse(str(target))
        _fill_placeholder(tree.getroot(), "page-number", str(int(no.group(1))))
        tree.write(str(target), encoding="unicode")
    summary["picked"] = {"rank": match["rank"], "form": match["form"], "target": str(target)}
    (out / "variants.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for href in re.findall(r'(?:xlink:)?href="(?!data:|https?:)([^"]+)"', (out / match["file"]).read_text(encoding="utf-8")):
        src, dst = (out / href).resolve(), (target.parent / href).resolve()
        if src.is_file() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return target


# ---------------------------------------------------------------------------
# Plan: which pages get alternatives
# ---------------------------------------------------------------------------

KEY_TITLE = re.compile(r"전략|방안|방향|결과|로드맵|프레임워크|체계|진단|과제|요약|절차|프로세스|구조|모델|추진|개선|시사점|대응|범위|방법")
FLOW_CUE = re.compile(r"\d+\s*[–~-]\s*\d+\s*주|\d+\s*주\s*차|\d단계|WP\s?\d|Phase\s?\d|STEP\s?\d", re.I)
DRAWN = re.compile(r"chevron|gantt|timeline|matrix|tree|waterfall|macc|wedge|heatmap|radar|raci|kpi|chart|nine-box|scqa")


def plan(pages: list[Any], max_pages: int) -> list[dict[str, Any]]:
    """Score body pages for diagram alternatives. `pages` are innergen_story_check.StoryPage."""
    content = [p for p in pages if p.role == "content"]
    if not content:
        return []
    closing = {p.index for p in content[-3:]}
    seen_chapter: set[str] = set()
    rows = []
    for p in content:
        score, why = 0, []
        chap = re.match(r"^\s*([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[IVX]{1,4}|\d{1,2})\.", p.title)
        if chap and chap.group(1) not in seen_chapter:
            seen_chapter.add(chap.group(1))
            score += 2
            why.append("장 첫 장표")
        if re.search(r"\d", p.governing):
            score += 2
            why.append("거버닝 수치")
        n_items = len([b for b in p.body if 4 <= len(b) <= 160])
        if n_items >= 6:
            score += 3
            why.append(f"본문 {n_items}줄(내용 많음)")
        elif n_items >= 4:
            score += 1
        if KEY_TITLE.search(p.title + " " + p.governing):
            score += 2
            why.append("핵심 주제어")
        if p.index in closing:
            score += 2
            why.append("마무리")
        flow = sum(bool(ORDINAL.match(b) or "→" in b or FLOW_CUE.search(b)) for b in p.body)
        if DRAWN.search(p.layout):
            score -= 2
            why.append("이미 전용 도식")
        elif flow >= 2:
            score += min(5, 1 + flow // 2)
            why.append(f"순서·흐름을 글로만 표현({flow}줄)")
        rows.append({"page": p.index, "title": p.title, "score": score, "why": why})
    limit = len(rows) if max_pages >= 999 else max(2, min(max_pages, math.ceil(len(content) * 0.25)))
    top = sorted(rows, key=lambda r: (-r["score"], r["page"]))[:limit]
    return sorted(top, key=lambda r: r["page"])


# ---------------------------------------------------------------------------
# Select: "여러 도식 후보 보기" checkboxes on the TOC
# ---------------------------------------------------------------------------

SELECT_FILE = "diagram_select.md"
CHECK = re.compile(r"^(\s*)-\s*\[([ xX✓])\]\s*(.+)$")


def read_select(path: Path) -> set[int]:
    """Pages checked in the TOC checklist; a checked chapter selects all of its pages."""
    pages: set[int] = set()
    chapter_on = False
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CHECK.match(line)
        if not m:
            continue
        on = m.group(2) != " "
        page = re.match(r"P(\d{1,3})\b", m.group(3))
        if not m.group(1) and not page:  # chapter line
            chapter_on = on
        elif page and (on or chapter_on):
            pages.add(int(page.group(1)))
    return pages


def write_select(project: Path, source: Path, recommended: dict[int, list[str]], checks: set[str]) -> Path:
    import toc_builder
    rows = toc_builder._page_rows(source)
    titles = {r["page"]: r["title"] for r in rows}
    chapters = toc_builder.chapters(rows)
    path = project / "analysis" / SELECT_FILE
    old = read_select(path) if path.exists() else set()
    lines = ["# 목차 — 여러 도식 후보 보기", "",
             "체크한 장·장표만 같은 내용을 도식 2–3개로 그려 비교합니다. 체크하지 않은 장표는 도식 1개(기본)로 둡니다.",
             "장을 체크하면 그 장의 본문 장표 전체가 대상입니다. ★는 중요도 추천(체크는 직접)입니다.",
             "체크 후: `content_diagrams.py plan <project>` → 대상 장표 목록(analysis/diagram_plan.md)", ""]
    for ch in chapters:
        key = {ch["no"], ch["name"], f"{ch['no']}.", f"{ch['no']}장"}
        ch_on = bool(key & checks)
        lines.append(f"- [{'x' if ch_on else ' '}] {ch['no']}. {ch['name']} ({ch['range']})")
        for pg in ch["pages"]:
            on = pg in old or f"P{pg:02d}" in checks or f"P{pg}" in checks
            star = f" ★ {', '.join(recommended[pg])}" if pg in recommended else ""
            lines.append(f"  - [{'x' if on else ' '}] P{pg:02d} {titles.get(pg, '')}{star}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Extract: draft content JSON from a drawn page
# ---------------------------------------------------------------------------

def extract(svg: Path) -> dict[str, Any]:
    import innergen_qaqc as qaqc
    page = qaqc.Page(svg, 0)
    texts = [t for t in page.texts if t["text"]]
    m = re.search(r'viewBox="[\d.\s-]*?([\d.]+)\s+([\d.]+)"', svg.read_text(encoding="utf-8")[:600])
    w, h = (float(m.group(1)), float(m.group(2))) if m else (960.0, 540.0)
    top = sorted((t for t in texts if t["y"] < h * 0.24), key=lambda t: (-t["size"], t["y"]))
    title = top[0]["text"] if top else ""
    governing = next((t["text"] for t in top[1:] if len(t["text"]) >= 12), "")
    source = next((t["text"] for t in texts if re.match(r"\s*(출처|Source)", t["text"])), "")
    body = [t for t in texts if t["text"] not in (title, governing, source) and h * 0.18 < t["y"] < h * 0.93
            and not re.search(r"page-number|footer|source", f"{t['id']} {t['group']}".lower())]
    body.sort(key=lambda t: (round(t["y"] / 4), t["x"]))
    items: list[dict[str, Any]] = []
    for t in body:
        txt = t["text"].strip()
        bold = str(t["weight"]) in ("700", "bold", "600")
        if (bold and len(txt) <= 40) or ORDINAL.match(txt) or not items:
            items.append({"label": ORDINAL.sub("", txt).strip() or txt, "desc": []})
        else:
            items[-1]["desc"].append(txt)
    items = [{"label": i["label"], "desc": " ".join(i["desc"])} for i in items if i["label"]]
    return {"title": title, "governing": governing, "source": source, "relation": "auto", "items": items,
            "_note": "초안: 굵은 짧은 줄·번호 줄을 label, 뒤따르는 줄을 desc로 묶었습니다. label은 명사구로 줄이고 desc는 한두 줄로 정리한 뒤 build 하세요."}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

EXAMPLES = {
    "sequence": {"title": "Ⅱ. 추진방안 – 단계별 수행", "governing": "진단부터 이관까지 5단계로 10주 안에 첫해 산정을 마감할 예정입니다",
                 "source": "출처: 이너젠 수행계획(예시)", "relation": "auto", "conclusion": "2단계 종료 시 범위·공수를 재승인한 뒤 전 대상으로 확산합니다",
                 "items": [{"label": "경계 진단", "period": "1–2주", "desc": "재무 연결 목록과 GHG 경계 대조, 차이 사유 기록"},
                           {"label": "데이터 사전", "period": "2–3주", "desc": "Scope·항목·단위·계수·방법 정의"},
                           {"label": "시범 산정", "period": "4–5주", "desc": "대표 법인 2곳 산정·검토"},
                           {"label": "전 대상 확산", "period": "6–8주", "desc": "전 법인 취합·대사·예외 승인"},
                           {"label": "마감·이관", "period": "9–10주", "desc": "승인 집계·방법 설명·재수행 교육"}]},
    "parallel": {"title": "Ⅰ. 현황 – 공시 대응 과제", "governing": "연결 공시 준비에는 4가지 과제가 동시에 필요합니다", "relation": "auto",
                 "items": [{"label": "경계 정합", "desc": "재무 연결 범위와 측정 경계 차이 해소"},
                           {"label": "데이터 체계", "desc": "항목·단위·계수 정의서와 취합 양식"},
                           {"label": "Scope 3", "desc": "전 카테고리 진단 후 중점 항목 산정"},
                           {"label": "내부 통제", "desc": "검토·승인 이력과 증빙 역추적"}]},
    "hierarchy": {"title": "Ⅲ. 과업 구조", "governing": "3대 과업 7개 세부과업으로 수행합니다", "root": "연결 기준 GHG 산정", "relation": "auto",
                  "items": [{"group": "범위", "label": "경계 대조"}, {"group": "범위", "label": "법인 목록 확정"},
                            {"group": "산정", "label": "데이터 사전"}, {"group": "산정", "label": "Scope 1·2"}, {"group": "산정", "label": "Scope 3"},
                            {"group": "운영", "label": "검토·승인"}, {"group": "운영", "label": "재수행 교육"}]},
    "comparison": {"title": "Ⅱ. 개선 방향 – 현행 대비 목표", "governing": "취합 방식을 법인별 파일에서 표준 양식으로 바꿔 검토 시간을 줄입니다",
                   "relation": "auto", "columns": ["현행", "목표"],
                   "items": [{"label": "취합", "a": "법인별 자체 양식 메일 회신", "b": "표준 양식 + 검증 규칙 자동 점검"},
                             {"label": "계수", "a": "담당자별 다른 출처", "b": "버전 관리된 계수표 한 곳"},
                             {"label": "승인", "a": "최종 합계만 승인", "b": "법인·항목 단위 승인 이력"}]},
    "matrix": {"title": "Ⅳ. 개선과제 우선순위", "governing": "효과가 크고 쉬운 3개 과제를 금년에 먼저 추진합니다", "relation": "auto",
               "axes": {"x": "실행 용이성", "y": "기대 효과"}, "quadrants": ["중기 과제", "우선 추진", "보류", "빠른 개선"],
               "items": [{"label": "경계 대사표", "x": 4.5, "y": 4.6}, {"label": "계수 관리", "x": 4, "y": 3.5},
                         {"label": "Scope 3 확대", "x": 2, "y": 4.2}, {"label": "시스템 연계", "x": 1.5, "y": 2.5},
                         {"label": "승인 이력", "x": 3.8, "y": 4.1}]},
    "quantity": {"title": "Ⅰ. 배출 현황 – Scope별 규모", "governing": "Scope 2가 전체의 78%로 전력 계약 관리가 감축의 핵심입니다(예시)",
                 "relation": "auto", "source": "출처: 예시 데이터", "unit": "천tCO2eq",
                 "items": [{"label": "Scope 2", "value": 78}, {"label": "Scope 3(산정분)", "value": 15}, {"label": "Scope 1", "value": 7}]},
    "cause": {"title": "Ⅰ. 배경 – 데이터 품질 문제", "governing": "취합 기준 부재가 수치 불일치로 이어져 공시 검증 리스크가 커집니다",
              "relation": "auto",
              "items": [{"label": "취합 기준 부재", "desc": "법인마다 다른 단위·기간"}, {"label": "수치 불일치", "desc": "합계와 법인 합이 다름"},
                        {"label": "검증 리스크", "desc": "보증 의견 한정 가능성"}]},
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="INNerGEN content diagrams with alternatives.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("forms", help="list diagram forms")
    ex = sub.add_parser("example", help="print example content JSON")
    ex.add_argument("relation", choices=sorted(EXAMPLES))
    rc = sub.add_parser("recommend", help="infer relation and rank forms")
    rc.add_argument("data", type=Path)
    bd = sub.add_parser("build", help="draw 2-3 alternative slides")
    bd.add_argument("data", type=Path)
    bd.add_argument("--family", required=True, choices=sorted(FAMILIES))
    bd.add_argument("-o", "--out", type=Path, required=True, help="output folder for v1_*.svg … and variants.html")
    bd.add_argument("--count", type=int, default=3)
    bd.add_argument("--forms", default=None, help="comma list to force forms")
    bd.add_argument("--base", type=Path, default=None)
    bd.add_argument("--mode", choices=("auto", "structured", "flat"), default="auto")
    pk = sub.add_parser("pick", help="copy one variant into the deck")
    pk.add_argument("dir", type=Path)
    pk.add_argument("which", help="rank number or form name")
    pk.add_argument("-o", "--output", type=Path, required=True)
    sl = sub.add_parser("select", help="write the TOC checklist for 여러 도식 후보 보기")
    sl.add_argument("project", type=Path)
    sl.add_argument("--outline", type=Path, default=None)
    sl.add_argument("--check", default="", help="comma list to tick: chapter numbers (Ⅲ) or pages (P05)")
    pl = sub.add_parser("plan", help="list the checked pages that get alternatives")
    pl.add_argument("project", type=Path)
    pl.add_argument("--outline", type=Path, default=None)
    pl.add_argument("--max", type=int, default=6)
    pl.add_argument("--auto", action="store_true", help="ignore the checklist and use the importance ranking")
    xt = sub.add_parser("extract", help="draft content JSON from a drawn page")
    xt.add_argument("svg", type=Path)
    return ap


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    if args.command == "forms":
        for name, (rels, _, _, desc) in FORMS.items():
            print(f"{name:11s} {', '.join(RELATION_KO[r] for r in rels):40s} {desc}")
        return 0
    if args.command == "example":
        print(json.dumps(EXAMPLES[args.relation], ensure_ascii=False, indent=2))
        return 0
    if args.command == "extract":
        print(json.dumps(extract(args.svg), ensure_ascii=False, indent=2))
        return 0
    if args.command == "pick":
        try:
            t = pick(args.dir, args.which, args.output)
        except DiagramError as exc:
            print(f"ERROR  {exc}")
            return 1
        print(f"OK  {t}")
        return 0
    if args.command in ("plan", "select"):
        import innergen_story_check as story
        rules = json.loads(story.RULES_PATH.read_text(encoding="utf-8"))
        pages = story.pages_from_outline(args.outline) if args.outline else story.pages_from_project(args.project, rules)
        ranked = plan(pages, args.max if args.command == "plan" else 6)
        out = args.project / "analysis"
        sel_path = out / SELECT_FILE
        if args.command == "select":
            checks = {c.strip() for c in args.check.split(",") if c.strip()}
            path = write_select(args.project, args.outline or args.project, {r["page"]: r["why"] for r in ranked}, checks)
            print(path.read_text(encoding="utf-8"))
            print(f"[content_diagrams] 체크 {len(read_select(path))}장 → {path}")
            return 0
        if args.auto:
            rows, how = ranked, "중요도 순위(--auto)"
        elif sel_path.exists():
            chosen = read_select(sel_path)
            scored = {r["page"]: r for r in plan(pages, 999)} if chosen else {}
            by_index = {p.index: p for p in pages}
            rows = [scored.get(n) or {"page": n, "title": by_index[n].title if n in by_index else "", "score": 0, "why": []}
                    for n in sorted(chosen)]
            for r in rows:
                r["why"] = ["목차에서 체크"] + r["why"]
            how = f"목차 체크({sel_path.name})"
        else:
            rows, how = [], "체크리스트 없음"
            print(f"[content_diagrams] {SELECT_FILE}가 없습니다 — `content_diagrams.py select {args.project}`로 목차 체크리스트를 만드세요"
                  " (추천: " + ", ".join(f"P{r['page']:02d}" for r in ranked) + ")")
        out.mkdir(parents=True, exist_ok=True)
        md = ["# 도식 후보 대상 장표", "", f"선정: {how}. 여기 있는 장표만 도식 후보 3개를 만든다(content-diagrams-v33.md §3).", "",
              "| 장 | 제목 | 점수 | 이유 |", "|---|---|---|---|"]
        md += [f"| P{r['page']:02d} | {r['title']} | {r['score']} | {', '.join(r['why'])} |" for r in rows]
        (out / "diagram_plan.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        (out / "diagram_plan.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for r in rows:
            print(f"P{r['page']:02d}  {r['score']:>2}  {r['title'][:40]}  ({', '.join(r['why'])})")
        print(f"[content_diagrams] {len(rows)} page(s) → {out / 'diagram_plan.md'}")
        return 0
    data = json.loads(args.data.read_text(encoding="utf-8"))
    errors = check(data)
    for e in errors:
        print(f"ERROR  {e}")
    if errors:
        return 1
    if args.command == "recommend":
        print(json.dumps(recommend(data), ensure_ascii=False, indent=2))
        return 0
    forms = [f.strip() for f in args.forms.split(",")] if args.forms else None
    out = args.out
    mode = detect_mode(out / "x.svg") if args.mode == "auto" else args.mode
    if args.mode == "auto" and mode == "structured":
        mode = detect_mode(out.parent / "svg_output" / "x.svg")
    try:
        summary = build_variants(data, args.family, out, args.count, forms, args.base, mode)
    except DiagramError as exc:
        print(f"ERROR  {exc}")
        return 1
    print(f"관계: {summary['relation_ko']} ({summary['reason']})")
    for v in summary["variants"]:
        flag = "추천" if v["rank"] == 1 else f"후보{v['rank']}"
        warn = f"  ⚠ {'; '.join(v['warnings'])}" if v["warnings"] else ""
        print(f"  {flag}  {v['file']:22s} {v['desc']}{warn}")
    print(f"[content_diagrams] {len(summary['variants'])} variant(s) → {out / 'variants.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
