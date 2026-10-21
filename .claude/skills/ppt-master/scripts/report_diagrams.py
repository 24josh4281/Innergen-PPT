#!/usr/bin/env python3
"""
PPT Master - INNerGEN Report-Stage Diagrams (v26)

Generates the structured body of kickoff / interim / final report slides from
JSON data instead of hand-placed shapes: 수행일정 (schedule Gantt), 추진절차
(procedure grid), 세부현황 (interim status board), 이슈·조치 (issue/action),
and 수행범위 (scope modules, include/exclude matrix, deliverables gallery).
Geometry follows the reference study in docs/styles/innergen/report-diagrams-v26.md:
wide hierarchical text columns, bars at ~50% row height, a bottom report row,
light→dark phase ramps, state words + dates instead of percentages.

The tool takes a family chrome slide (default: the family's 03a_content.svg),
fills title / governing / source / footer placeholders from the data, and
replaces the `content-area` placeholder with an editable SVG group. Every
label stays a <text>, every bar a <rect>, so the exported PPTX is editable.
Data checks stop the run on impossible input (end before start, bar outside
the period, unknown state words, too many rows for the body box).

Usage:
    python3 scripts/report_diagrams.py kinds
    python3 scripts/report_diagrams.py example <kind>
    python3 scripts/report_diagrams.py check <data.json>
    python3 scripts/report_diagrams.py build <data.json> --family <family> -o <slide.svg> [--base <chrome.svg>]

Examples:
    python3 scripts/report_diagrams.py example schedule > schedule.json
    python3 scripts/report_diagrams.py build schedule.json --family innergen_business -o projects/demo/svg_output/05_schedule.svg

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any, Optional
from xml.sax.saxutils import escape

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

SVG_NS = "http://www.w3.org/2000/svg"
DECKS_DIR = _SCRIPTS_DIR.parent / "templates" / "decks"

# Family tokens: colors from design-standard-v17 profiles / family templates,
# min_px from qaqc-v21 (C06); ladder = the (small, body, emphasis) cell sizes the
# family templates already use. ramp = phase progression light -> dark.
FAMILIES: dict[str, dict[str, Any]] = {
    "innergen_business": dict(
        font='"IBM Plex Sans KR", "Malgun Gothic", sans-serif', min_px=10.67, ladder=(10.67, 12, 13.33),
        navy="#2B4C7E", accent="#518FFF", light="#8FB3FF", mid="#B9CFFF", panel="#D9E7FD",
        pale="#EEF3FF", zebra="#F3F7FF", rule="#D9D9D9", text="#000000", muted="#595959",
        neutral="#A6A6A6", alert="#FF0000", white="#FFFFFF",
        ramp=["#EEF3FF", "#B9CFFF", "#8FB3FF", "#518FFF", "#2B4C7E"]),
    "innergen_lecture": dict(
        font='Pretendard, "Malgun Gothic", sans-serif', min_px=12, ladder=(12, 13.33, 14.67),
        navy="#0B1739", accent="#2F62F0", light="#7B9BF7", mid="#B8CBF9", panel="#DFE7FF",
        pale="#EEF2FF", zebra="#F3F6FF", rule="#E2E8F0", text="#475569", muted="#64748B",
        neutral="#94A3B8", alert="#FF0000", white="#FFFFFF",
        ramp=["#DFE7FF", "#B8CBF9", "#7B9BF7", "#2F62F0", "#0B1739"]),
    "innercarry": dict(
        font='"IBM Plex Sans KR", "Malgun Gothic", sans-serif', min_px=10.67, ladder=(10.67, 12, 13.33),
        navy="#0B1739", accent="#2F62F0", light="#7B9BF7", mid="#B8CBF9", panel="#DFE7FF",
        pale="#EEF2FF", zebra="#F3F6FF", rule="#E2E8F0", text="#475569", muted="#64748B",
        neutral="#94A3B8", alert="#991B1B", white="#FFFFFF",
        ramp=["#DFE7FF", "#B8CBF9", "#7B9BF7", "#2F62F0", "#0B1739"]),
}

STATES = ["완료", "진행 중", "예정", "보완", "지연", "n/a"]
SCOPE_MARKS = {"포함": "●", "선택": "◐", "제외": "–"}
REPORT_TYPES = ["착수", "중간", "최종"]
STAGES = ["proposal", "kickoff", "interim", "final"]

# Governing tense by stage (G19): kickoff promises, interim mixes, final reports.
STAGE_TENSE = {
    "kickoff": (r"예정|계획|추진할|수행할|진행할", "착수 보고 거버닝은 계획형(~할 예정입니다)으로"),
    "interim": (r"진행|완료|예정", "중간 보고 거버닝은 '…는 완료, …는 진행 중이며 … 예정' 형태로"),
    "final": (r"하였|했습|완료하|도출하|마련하|수립하였", "최종 보고 거버닝은 결과형(~하였습니다)으로"),
}


class DiagramError(ValueError):
    """Raised for data that cannot be drawn faithfully."""


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _char_em(ch: str) -> float:
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3 or 0x3130 <= code <= 0x318F or 0x4E00 <= code <= 0x9FFF:
        return 1.0
    if ch == " ":
        return 0.3
    if ch in "●◐★▲▪◎·–":
        return 0.9
    if ch.isupper() or ch.isdigit():
        return 0.62
    return 0.52


def text_width(text: str, size: float, bold: bool = False) -> float:
    return sum(_char_em(c) for c in text) * size * (1.04 if bold else 1.0)


def wrap(text: str, size: float, width: float, bold: bool = False, max_lines: int = 4) -> list[str]:
    """Greedy wrap on spaces; Hangul words never split mid-word unless alone."""
    words = str(text).split()
    lines: list[str] = []
    cur = ""
    for word in words:
        cand = f"{cur} {word}".strip()
        if text_width(cand, size, bold) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" ,") + "…"
    return lines or [""]


class Canvas:
    """Accumulates SVG fragments with unique ids."""

    def __init__(self, fam: dict[str, Any], prefix: str):
        self.fam = fam
        self.prefix = prefix
        self.parts: list[str] = []
        self.counter = 0

    def _id(self, name: str) -> str:
        self.counter += 1
        return f"{self.prefix}-{name}-{self.counter}"

    def rect(self, name: str, x: float, y: float, w: float, h: float, fill: str = "none",
             stroke: Optional[str] = None, sw: float = 1.0, rx: float = 0, dash: bool = False) -> None:
        st = f' stroke="{stroke}" stroke-width="{sw:g}"' if stroke else ""
        da = ' stroke-dasharray="4 3"' if dash and stroke else ""
        r = f' rx="{rx:g}" ry="{rx:g}"' if rx else ""
        self.parts.append(f'<rect id="{self._id(name)}" x="{x:.1f}" y="{y:.1f}" width="{max(w, 0.5):.1f}" '
                          f'height="{max(h, 0.5):.1f}" fill="{fill}"{st}{da}{r}/>')

    def line(self, name: str, x1: float, y1: float, x2: float, y2: float, stroke: str,
             sw: float = 1.0, dash: bool = False) -> None:
        da = ' stroke-dasharray="4 3"' if dash else ""
        self.parts.append(f'<line id="{self._id(name)}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                          f'y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw:g}"{da}/>')

    def poly(self, name: str, points: list[tuple[float, float]], fill: str,
             stroke: Optional[str] = None) -> None:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        st = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
        self.parts.append(f'<polygon id="{self._id(name)}" points="{pts}" fill="{fill}"{st}/>')

    def path(self, name: str, d: str, stroke: str, sw: float = 1.2) -> None:
        self.parts.append(f'<path id="{self._id(name)}" d="{d}" fill="none" stroke="{stroke}" '
                          f'stroke-width="{sw:g}"/>')

    def text(self, name: str, x: float, y: float, lines: list[str] | str, size: float,
             fill: Optional[str] = None, bold: bool = False, anchor: str = "start",
             leading: float = 1.32) -> None:
        if isinstance(lines, str):
            lines = [lines]
        fill = fill or self.fam["text"]
        weight = "700" if bold else "400"
        head = (f'<text id="{self._id(name)}" x="{x:.1f}" y="{y:.1f}" font-family=\'{self.fam["font"]}\' '
                f'font-size="{size:g}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">')
        if len(lines) == 1:
            self.parts.append(f"{head}{escape(lines[0])}</text>")
            return
        spans = [f'<tspan x="{x:.1f}" dy="{0 if i == 0 else size * leading:.2f}">{escape(t)}</tspan>'
                 for i, t in enumerate(lines)]
        self.parts.append(head + "".join(spans) + "</text>")

    def items(self, name: str, x: float, y: float, lines: list[str], size: float, leading: float = 1.32,
              **kw: Any) -> None:
        """One <text> per list line: independent bullets must not merge into a paragraph."""
        for i, line in enumerate(lines):
            self.text(name, x, y + i * size * leading, line, size, **kw)

    def text_block(self, name: str, x: float, y_top: float, lines: list[str], size: float,
                   h: float, **kw: Any) -> None:
        """Vertically centre lines inside [y_top, y_top + h]."""
        leading = kw.pop("leading", 1.32)
        block = size * (1 + leading * (len(lines) - 1))
        baseline = y_top + (h - block) / 2 + size * 0.86
        self.text(name, x, baseline, lines, size, leading=leading, **kw)

    def svg(self, kind: str) -> str:
        return (f'<g id="{self.prefix}" data-report-diagram="{kind}">' + "".join(self.parts) + "</g>")


# ---------------------------------------------------------------------------
# Schedule (수행일정 Gantt)
# ---------------------------------------------------------------------------

def _parse_when(value: str, end: bool = False) -> date:
    m = re.fullmatch(r"(\d{4})-(\d{1,2})(?:-(\d{1,2}))?", str(value).strip())
    if not m:
        raise DiagramError(f"date must be YYYY-MM or YYYY-MM-DD: {value!r}")
    y, mo = int(m.group(1)), int(m.group(2))
    if m.group(3):
        return date(y, mo, int(m.group(3)))
    return date(y, mo, calendar.monthrange(y, mo)[1] if end else 1)


def _month_pos(d: date, origin: date, end: bool = False) -> float:
    """Fractional month offset of a date from the first day of origin's month."""
    months = (d.year - origin.year) * 12 + d.month - origin.month
    days = calendar.monthrange(d.year, d.month)[1]
    frac = (d.day if end else d.day - 1) / days
    return months + frac


def check_schedule(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        p0 = _parse_when(data["period"]["start"])
        p1 = _parse_when(data["period"]["end"], end=True)
    except (KeyError, DiagramError) as exc:
        return [f"period: {exc}"]
    if p1 <= p0:
        errors.append("period end is not after start")
    months = _month_pos(p1, p0, end=True)
    if not 2 <= months <= 24:
        errors.append(f"period spans {months:.1f} months; use 2–24 (split longer programmes)")
    rows = 0
    for g in data.get("groups", []):
        tasks = g.get("tasks", [])
        if not 1 <= len(tasks) <= 8:
            errors.append(f"group {g.get('label')!r}: {len(tasks)} tasks (1–8 per group)")
        for t in tasks:
            rows += 1
            for key in ("start", "end"):
                if key not in t:
                    errors.append(f"task {t.get('label')!r}: missing {key}")
            try:
                s, e = _parse_when(t["start"]), _parse_when(t["end"], end=True)
                if e < s:
                    errors.append(f"task {t.get('label')!r}: end before start")
                if s < p0 or e > p1:
                    errors.append(f"task {t.get('label')!r}: bar outside the period")
                actual = t.get("actual")
                if actual:
                    if actual.get("status") and actual["status"] not in STATES:
                        errors.append(f"task {t.get('label')!r}: status must be one of {STATES}")
            except (KeyError, DiagramError) as exc:
                errors.append(f"task {t.get('label')!r}: {exc}")
    if rows == 0:
        errors.append("schedule has no tasks")
    if rows > 23:
        errors.append(f"{rows} task rows; split the schedule (max 23)")
    for r in data.get("reports", []):
        if r.get("type") not in REPORT_TYPES:
            errors.append(f"report type must be one of {REPORT_TYPES}: {r.get('type')!r}")
        else:
            try:
                d = _parse_when(r["at"])
                if not p0 <= d <= p1:
                    errors.append(f"report {r['type']} outside the period")
            except (KeyError, DiagramError) as exc:
                errors.append(f"report {r.get('type')}: {exc}")
    types = {r.get("type") for r in data.get("reports", [])}
    if data.get("stage") in ("kickoff", "final") and not {"착수", "최종"} <= types:
        errors.append("kickoff/final schedules need 착수 and 최종 in the report row")
    if data.get("stage") == "interim" and not data.get("as_of"):
        errors.append("interim schedule needs as_of (기준일)")
    return errors


def draw_schedule(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    p0 = _parse_when(data["period"]["start"])
    p1 = _parse_when(data["period"]["end"], end=True)
    n_months = round(_month_pos(p1, p0, end=True))
    unit = data["period"].get("unit", "month")
    sub = {"month": 1, "half_month": 2, "week": 4}[unit]
    groups = data.get("groups", [])
    n_rows = sum(len(g["tasks"]) for g in groups)
    has_groups = any(g.get("label") for g in groups)
    note_key = next((k for k in ("note", "deliverable") if any(t.get(k) for g in groups for t in g["tasks"])), None)
    reports = data.get("reports", [])
    events = data.get("events", [])

    base = fam["min_px"]
    fs = fam["ladder"][2 if n_rows <= 10 else 1 if n_rows <= 16 else 0]
    head_fs = fs
    year_header = data["period"].get("year_header", p0.year != p1.year)
    head_rows = 1 + (1 if year_header else 0) + (1 if sub == 4 else 0)
    head_h = fs * 1.9
    report_rows = 1 if reports else 0
    row_h = (H - head_h * head_rows - (fs * 2.0 if report_rows else 0)) / n_rows
    row_h = min(row_h, fs * 3.4)
    if row_h < fs * 1.55:
        raise DiagramError(f"{n_rows} rows do not fit {H:.0f}px at {fs:g}px; split the schedule")

    # Columns: group | task | grid | note  (text share 43–60% per reference S-A/S-B)
    group_w = W * 0.13 if has_groups else 0
    note_w = W * 0.13 if note_key else 0
    longest = max((text_width(t["label"], fs) for g in groups for t in g["tasks"]), default=0)
    task_w = min(max(W * 0.24, longest + fs * 1.6), W * 0.36)
    grid_x = X + group_w + task_w
    grid_w = W - group_w - task_w - note_w
    cell_w = grid_w / (n_months * sub)

    def gx(d: date, end: bool = False) -> float:
        return grid_x + _month_pos(d, p0, end=end) / n_months * grid_w

    # Header
    y = Y
    hh = head_h * head_rows
    cv.rect("head-bg", X, y, W, hh, fill=fam["navy"])
    if has_groups:
        cv.text_block("head-group", X + group_w / 2, y, ["구분"], head_fs, hh, fill=fam["white"], bold=True, anchor="middle")
    cv.text_block("head-task", X + group_w + task_w / 2, y, ["세부 과업"], head_fs, hh, fill=fam["white"], bold=True, anchor="middle")
    if note_key:
        cv.text_block("head-note", grid_x + grid_w + note_w / 2, y, ["비고" if note_key == "note" else "산출물"],
                      head_fs, hh, fill=fam["white"], bold=True, anchor="middle")
    row_y = y
    if year_header:
        yr_start = 0
        for yr in range(p0.year, p1.year + 1):
            m_count = sum(1 for k in range(n_months) if (p0.month - 1 + k) // 12 + p0.year == yr)
            x0 = grid_x + yr_start / n_months * grid_w
            w0 = m_count / n_months * grid_w
            cv.text_block("head-year", x0 + w0 / 2, row_y, [f"{yr}년"], head_fs, head_h, fill=fam["white"], bold=True, anchor="middle")
            if yr_start:
                cv.line("head-year-sep", x0, row_y, x0, row_y + head_h, fam["white"])
            yr_start += m_count
        cv.line("head-year-rule", grid_x, row_y + head_h, grid_x + grid_w, row_y + head_h, fam["white"], 0.75)
        row_y += head_h
    for k in range(n_months):
        mo = (p0.month - 1 + k) % 12 + 1
        x0 = grid_x + k / n_months * grid_w
        cv.text_block("head-month", x0 + grid_w / n_months / 2, row_y, [f"{mo}월"], head_fs, head_h,
                      fill=fam["white"], bold=True, anchor="middle")
        if k:
            cv.line("head-month-sep", x0, row_y, x0, Y + hh, fam["white"], 0.75)
    if sub == 4:
        row_y += head_h
        cv.line("head-week-rule", grid_x, row_y, grid_x + grid_w, row_y, fam["white"], 0.75)
        for k in range(n_months * 4):
            cv.text_block("head-week", grid_x + (k + 0.5) * cell_w, row_y, [f"{k % 4 + 1}W" if text_width("4W", base) + 4 <= cell_w else f"{k % 4 + 1}"], base,
                          head_h, fill=fam["white"], anchor="middle")
    body_top = Y + hh
    body_h = row_h * n_rows

    # Zebra by group, vertical grid
    for k in range(n_months * sub + 1):
        x0 = grid_x + k * cell_w
        major = k % sub == 0
        cv.line("grid-v", x0, body_top, x0, body_top + body_h, fam["rule"] if major else fam["panel"], 0.75)

    as_of = _parse_when(data["as_of"]) if data.get("as_of") else None
    r = 0
    for g_idx, g in enumerate(groups):
        g_top = body_top + r * row_h
        g_h = len(g["tasks"]) * row_h
        if g_idx % 2 == 1:
            cv.rect("group-band", X, g_top, W, g_h, fill=fam["zebra"])
        if has_groups:
            cv.rect("group-cell", X, g_top, group_w, g_h, fill=fam["pale"])
            lines = wrap(g.get("label", ""), fs, group_w - fs, bold=True, max_lines=max(1, int(g_h / (fs * 1.3))))
            cv.text_block("group-label", X + group_w / 2, g_top, lines, fs, g_h, fill=fam["navy"], bold=True, anchor="middle")
        for t in g["tasks"]:
            ty = body_top + r * row_h
            kind = t.get("kind", "task")
            label_lines = wrap(t["label"], fs, task_w - fs * 1.2, bold=kind == "summary",
                               max_lines=max(1, int(row_h / (fs * 1.25))))
            cv.text_block("task-label", X + group_w + fs * 0.6, ty, label_lines, fs, row_h,
                          fill=fam["navy"] if kind == "summary" else fam["text"], bold=kind == "summary")
            s, e = _parse_when(t["start"]), _parse_when(t["end"], end=True)
            bx0, bx1 = gx(s), gx(e, end=True)
            bh = row_h * (0.56 if kind == "summary" else 0.46)
            by = ty + (row_h - bh) / 2
            if kind == "continuous":
                cv.rect("bar-continuous", bx0, by, bx1 - bx0, bh, fill=fam["neutral"])
            elif data.get("stage") == "interim" and as_of is not None:
                # Plan as outline, actual as fill up to the reference date.
                cv.rect("bar-plan", bx0, by, bx1 - bx0, bh, fill=fam["white"], stroke=fam["accent"])
                actual = t.get("actual") or {}
                status = actual.get("status")
                a_end = min(as_of, e) if status != "완료" else _parse_when(actual.get("end", t["end"]), end=True)
                if s <= as_of or status == "완료":
                    a_start = _parse_when(actual.get("start", t["start"]))
                    ax1 = gx(a_end, end=True)
                    fill = fam["alert"] if status in ("지연", "보완") else (fam["navy"] if kind == "summary" else fam["accent"])
                    if ax1 > gx(a_start):
                        cv.rect("bar-actual", gx(a_start), by, ax1 - gx(a_start), bh, fill=fill)
            else:
                fill = fam["navy"] if kind == "summary" else fam["accent"]
                cv.rect("bar", bx0, by, bx1 - bx0, bh, fill=fill)
            if note_key and t.get(note_key):
                nl = wrap(t[note_key], base, note_w - fs, max_lines=2)
                cv.text_block("note", grid_x + grid_w + fs * 0.5, ty, nl, base, row_h, fill=fam["muted"])
            cv.line("row-rule", X + group_w, ty + row_h, X + W, ty + row_h, fam["rule"], 0.75)
            r += 1
        cv.line("group-rule", X, g_top + g_h, X + W, g_top + g_h, fam["rule"], 1)

    for ev in events:
        d = _parse_when(ev["at"])
        row_index = 0
        if ev.get("task"):
            flat = [t["label"] for g in groups for t in g["tasks"]]
            if ev["task"] in flat:
                row_index = flat.index(ev["task"])
        ey = body_top + row_index * row_h + row_h / 2 + fs * 0.35
        cv.text("event-star", gx(d), ey, "★", fam["ladder"][2], fill=fam["alert"], anchor="middle")
        if ev.get("label"):
            cv.text("event-label", gx(d) + fs * 0.9, ey, ev["label"], base, fill=fam["alert"], bold=True)

    # Report row (보고): navy cells at the report's unit cell
    bottom = body_top + body_h
    if reports:
        rh = fs * 2.0
        cv.rect("report-row", X, bottom, W, rh, fill=fam["pale"])
        cv.text_block("report-label", X + (group_w + task_w) / 2, bottom, ["보고"], fs, rh, fill=fam["navy"],
                      bold=True, anchor="middle")
        for rep in reports:
            d = _parse_when(rep["at"])
            k = int(_month_pos(d, p0) * sub)
            k = min(k, n_months * sub - 1)
            label = f"{rep['type']} 보고"
            span = 1
            while text_width(label, base, True) + 6 > cell_w * span and span < sub * 2:
                span += 1
            x0 = grid_x + k * cell_w
            x0 = min(x0, grid_x + grid_w - cell_w * span)
            cv.rect("report-cell", x0 + 1, bottom + 3, cell_w * span - 2, rh - 6, fill=fam["navy"], rx=2)
            text = label if text_width(label, base, True) + 4 <= cell_w * span else rep["type"]
            cv.text_block("report-text", x0 + cell_w * span / 2, bottom + 3, [text], base, rh - 6,
                          fill=fam["white"], bold=True, anchor="middle")
        bottom += rh
    if as_of is not None and p0 <= as_of <= p1:
        ax = gx(as_of, end=True)
        cv.line("as-of", ax, body_top, ax, bottom, fam["alert"], 1.2, dash=True)
        cv.text("as-of-label", ax, bottom + base * 1.35, f"▲ 기준일 {as_of.month}/{as_of.day}", base,
                fill=fam["alert"], bold=True, anchor="middle")
    cv.line("frame-bottom", X, bottom, X + W, bottom, fam["navy"], 1)
    cv.line("grid-left", grid_x, Y, grid_x, bottom, fam["navy"], 1)
    if has_groups:
        cv.line("group-sep", X + group_w, body_top, X + group_w, body_top + body_h, fam["rule"], 0.75)


# ---------------------------------------------------------------------------
# Procedure (추진절차)
# ---------------------------------------------------------------------------

def check_procedure(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    phases = data.get("phases", [])
    if not 3 <= len(phases) <= 6:
        errors.append(f"{len(phases)} phases; use 3–6")
    lanes = data.get("lanes", [])
    ids = set()
    per_phase: dict[int, int] = {}
    for n in data.get("nodes", []):
        if not 0 <= n.get("phase", -1) < len(phases):
            errors.append(f"node {n.get('label')!r}: phase index out of range")
        if lanes and n.get("lane") not in lanes:
            errors.append(f"node {n.get('label')!r}: lane must be one of {lanes}")
        if n.get("id"):
            ids.add(n["id"])
        per_phase[n.get("phase", -1)] = per_phase.get(n.get("phase", -1), 0) + 1
    for p, c in per_phase.items():
        limit = 5 * max(1, len(lanes)) if lanes else 5
        if c > limit:
            errors.append(f"phase {p}: {c} nodes (max {limit})")
    for e in data.get("edges", []):
        if len(e) != 2 or e[0] not in ids or e[1] not in ids:
            errors.append(f"edge {e} must join two node ids")
    for key in ("current_phase", "this_report_phase"):
        if data.get(key) is not None and not 0 <= data[key] < len(phases):
            errors.append(f"{key} out of range")
    return errors


def _chevron(x: float, y: float, w: float, h: float, first: bool) -> list[tuple[float, float]]:
    tip = min(h * 0.38, w * 0.18)
    if first:
        return [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h)]
    return [(x, y), (x + w - tip, y), (x + w, y + h / 2), (x + w - tip, y + h), (x, y + h), (x + tip, y + h / 2)]


def draw_procedure(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    phases = data["phases"]
    n = len(phases)
    lanes = data.get("lanes", [])
    nodes = data.get("nodes", [])
    base = fam["min_px"]
    fs = fam["ladder"][1]
    lane_w = W * 0.085 if lanes else 0
    terminal = data.get("terminal")
    term_w = W * 0.1 if terminal else 0
    gap = fs * 0.5
    col_x0 = X + lane_w + (gap if lanes else 0)
    col_w = (W - lane_w - (gap if lanes else 0) - term_w - (gap if terminal else 0)) / n
    chev_h = fs * 3.1
    current = data.get("current_phase")
    this_report = data.get("this_report_phase")
    ramp = fam["ramp"]

    # Chevron band with period labels
    for i, ph in enumerate(phases):
        cx = col_x0 + i * col_w
        if current is not None:
            fill = fam["navy"] if i == current else (fam["mid"] if i < current else fam["pale"])
        else:
            fill = ramp[round(i * (len(ramp) - 1) / max(1, n - 1))]
        dark = fill in (fam["navy"], fam["accent"], ramp[-1], ramp[-2])
        cv.poly("phase-chevron", _chevron(cx, Y, col_w + (col_w * 0.06 if i < n - 1 else 0), chev_h, i == 0), fill)
        label = f"{i + 1}. {ph['label']}"
        lines = wrap(label, fs, col_w * 0.78, bold=True, max_lines=2)
        cv.text_block("phase-label", cx + col_w * 0.5, Y, lines, fs, chev_h, fill=fam["white"] if dark else fam["navy"],
                      bold=True, anchor="middle", leading=1.15)
        if ph.get("period"):
            cv.text("phase-period", cx + col_w / 2, Y + chev_h + base * 1.35, ph["period"], base,
                    fill=fam["muted"], anchor="middle")
    top = Y + chev_h + (base * 2.0 if any(p.get("period") for p in phases) else gap)
    outputs = any(p.get("outputs") for p in phases)
    out_lines = max((len(p.get("outputs", [])) for p in phases), default=0)
    out_h = (base * 1.35 * out_lines + base * 2.6) if outputs else 0
    grid_h = Y + H - top - out_h - (gap if outputs else 0)

    # Lanes (vertical labels) and node grid
    lane_list = lanes or [None]
    lane_h = grid_h / len(lane_list)
    positions: dict[str, tuple[float, float, float, float]] = {}
    for li, lane in enumerate(lane_list):
        ly = top + li * lane_h
        if lane is not None:
            cv.rect("lane-label", X, ly + 2, lane_w, lane_h - 4, fill=fam["navy"])
            lines = wrap(lane, fs, lane_w - fs * 0.8, bold=True, max_lines=4)
            cv.text_block("lane-text", X + lane_w / 2, ly + 2, lines, fs, lane_h - 4, fill=fam["white"], bold=True,
                          anchor="middle", leading=1.2)
            if li:
                cv.line("lane-sep", col_x0, ly, col_x0 + col_w * n, ly, fam["rule"], 0.75, dash=True)
        for pi in range(n):
            cell_nodes = [nd for nd in nodes if nd.get("phase") == pi and (lane is None or nd.get("lane") == lane)]
            if not cell_nodes:
                continue
            k = len(cell_nodes)
            pad = fs * 0.5
            nh = min(fs * 3.4, (lane_h - pad * (k + 1)) / k)
            if nh < fs * 1.6:
                raise DiagramError(f"phase {pi} lane {lane!r}: {k} nodes do not fit; move some to another lane")
            stack_h = k * nh + (k - 1) * pad
            ny = ly + (lane_h - stack_h) / 2
            nw = col_w * 0.8
            nx = col_x0 + pi * col_w + (col_w - nw) / 2
            for nd in cell_nodes:
                optional = nd.get("optional", False)
                cv.rect("node", nx, ny, nw, nh, fill=fam["white"], stroke=fam["accent"] if not optional else fam["neutral"],
                        dash=optional, rx=3)
                label = nd["label"] + (" (필요 시)" if optional else "")
                lines = wrap(label, fs, nw - fs * 0.8, max_lines=max(1, int(nh / (fs * 1.25))))
                cv.text_block("node-text", nx + nw / 2, ny, lines, fs, nh, anchor="middle", leading=1.2)
                if nd.get("id"):
                    positions[nd["id"]] = (nx, ny, nw, nh)
                ny += nh + pad
    for a, b in data.get("edges", []):
        ax, ay, aw, ah = positions[a]
        bx, by, bw, bh = positions[b]
        if bx > ax + aw:
            x1, y1, x2, y2 = ax + aw, ay + ah / 2, bx, by + bh / 2
            mx = (x1 + x2) / 2
            cv.path("edge", f"M {x1:.1f} {y1:.1f} H {mx:.1f} V {y2:.1f} H {x2 - 5:.1f}", fam["neutral"])
            cv.poly("edge-head", [(x2 - 6, y2 - 3.5), (x2, y2), (x2 - 6, y2 + 3.5)], fam["neutral"])
        else:
            x1, y1 = ax + aw / 2, ay + ah
            x2, y2 = bx + bw / 2, by
            cv.path("edge", f"M {x1:.1f} {y1:.1f} V {(y1 + y2) / 2:.1f} H {x2:.1f} V {y2 - 5:.1f}", fam["neutral"])
            cv.poly("edge-head", [(x2 - 3.5, y2 - 6), (x2, y2), (x2 + 3.5, y2 - 6)], fam["neutral"])
    if terminal:
        tx = col_x0 + n * col_w + gap
        th = min(grid_h, fs * 4.2)
        ty = top + (grid_h - th) / 2
        cv.rect("terminal", tx, ty, term_w, th, fill=fam["navy"], rx=4)
        cv.text_block("terminal-text", tx + term_w / 2, ty, wrap(terminal, fs, term_w - fs, bold=True, max_lines=3),
                      fs, th, fill=fam["white"], bold=True, anchor="middle")
        cv.poly("terminal-head", [(tx - gap * 0.9, ty + th / 2 - 5), (tx - 2, ty + th / 2), (tx - gap * 0.9, ty + th / 2 + 5)],
                fam["navy"])
    if this_report is not None:
        fx = col_x0 + this_report * col_w + 2
        cv.rect("this-report", fx, Y - 4, col_w - 4, H + 4 - (0 if outputs else 0), stroke=fam["alert"], sw=1.5, dash=True)
        tag_w = text_width("이번 보고", base, True) + base
        cv.rect("this-report-tag", fx + col_w - 4 - tag_w, Y - 4 - base * 1.6, tag_w, base * 1.6, fill=fam["alert"])
        cv.text_block("this-report-text", fx + col_w - 4 - tag_w / 2, Y - 4 - base * 1.6, ["이번 보고"], base,
                      base * 1.6, fill=fam["white"], bold=True, anchor="middle")
    if outputs:
        oy = Y + H - out_h
        if lanes:
            cv.rect("output-label", X, oy, lane_w, out_h, fill=fam["pale"])
            cv.text_block("output-label-text", X + lane_w / 2, oy, ["산출물"], fs, out_h, fill=fam["navy"], bold=True,
                          anchor="middle")
        for i, ph in enumerate(phases):
            cx = col_x0 + i * col_w + 3
            cv.rect("output-box", cx, oy, col_w - 6, out_h, fill=fam["zebra"], stroke=fam["rule"])
            lines = [f"· {o}" for o in ph.get("outputs", [])]
            if lines:
                wrapped: list[str] = []
                for ln in lines:
                    wrapped += wrap(ln, base, col_w - 6 - base * 1.4, max_lines=2)
                cv.items("output-text", cx + base * 0.7, oy + base * 1.5, wrapped[: out_lines + 1], base, fill=fam["text"],
                         leading=1.3)


# ---------------------------------------------------------------------------
# Status (세부현황, interim)
# ---------------------------------------------------------------------------

def check_status(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    items = data.get("items", [])
    if not 1 <= len(items) <= 5:
        errors.append(f"{len(items)} items; use 1–5 per slide")
    alerts = 0
    for it in items:
        if it.get("status") not in STATES:
            errors.append(f"item {it.get('task')!r}: status must be one of {STATES}")
        if it.get("status") in ("지연", "보완"):
            alerts += 1
        if it.get("progress_pct") is not None:
            errors.append(f"item {it.get('task')!r}: references use state words + dates, not progress %")
        for col in ("done", "next"):
            for entry in it.get(col, []):
                if not entry.get("headline"):
                    errors.append(f"item {it.get('task')!r} {col}: headline required")
    if alerts > 2:
        errors.append(f"{alerts} 지연/보완 highlights; keep red emphasis to 2 or fewer")
    return errors


def _pill(cv: Canvas, x: float, y: float, status: str, size: float) -> float:
    fam = cv.fam
    style = {
        "완료": (fam["navy"], None, fam["white"]),
        "진행 중": (fam["accent"], None, fam["white"]),
        "예정": (fam["white"], fam["accent"], fam["accent"]),
        "보완": (fam["alert"], None, fam["white"]),
        "지연": (fam["alert"], None, fam["white"]),
        "n/a": (fam["white"], fam["neutral"], fam["muted"]),
    }[status]
    w = text_width(status, size, True) + size * 1.4
    h = size * 1.65
    cv.rect("status-pill", x, y, w, h, fill=style[0], stroke=style[1], rx=h / 2)
    cv.text_block("status-text", x + w / 2, y, [status], size, h, fill=style[2], bold=True, anchor="middle")
    return w


def draw_status(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    base = fam["min_px"]
    fs = fam["ladder"][1]
    periods = data.get("periods", {})
    items = data["items"]
    requests = data.get("requests", [])
    task_w = W * 0.19
    col_w = (W - task_w) / 2
    head_h = fs * 2.0
    cv.rect("head", X, Y, W, head_h, fill=fam["navy"])
    heads = [("과업", X + task_w / 2),
             (f"진행 현황 ({periods['done']})" if periods.get("done") else "진행 현황", X + task_w + col_w / 2),
             (f"향후 계획 ({periods['next']})" if periods.get("next") else "향후 계획", X + task_w + col_w * 1.5)]
    for label, cx in heads:
        cv.text_block("head-text", cx, Y, [label], fs, head_h, fill=fam["white"], bold=True, anchor="middle")
    req_h = (fs * 2.4 + base * 1.35 * max(0, len(requests) - 1)) if requests else 0
    avail = H - head_h - (req_h + fs * 0.6 if requests else 0)

    def entry_lines(entries: list[dict[str, Any]], expected: bool) -> list[tuple[str, bool]]:
        out: list[tuple[str, bool]] = []
        for e in entries:
            date_s = f" ({e['date']}{' 예상' if expected and e.get('expected') else ''})" if e.get("date") else ""
            for i, ln in enumerate(wrap(f"▪ {e['headline']}{date_s}", fs, col_w - fs * 1.6, bold=True, max_lines=2)):
                out.append((ln if i == 0 else "  " + ln, True))
            for d in e.get("details", [])[:3]:
                for i, ln in enumerate(wrap(f"- {d}", base, col_w - fs * 2.4, max_lines=2)):
                    out.append(("   " + ln if i == 0 else "     " + ln, False))
        return out

    blocks = [(entry_lines(it.get("done", []), False), entry_lines(it.get("next", []), True)) for it in items]
    weights = [max(len(a), len(b), 3) for a, b in blocks]
    unit = avail / sum(weights)
    if unit < fs * 1.3:
        raise DiagramError("status text does not fit; cut details to ≤3 per entry or split items across slides")
    y = Y + head_h
    for idx, (it, (done, nxt)) in enumerate(zip(items, blocks)):
        rh = weights[idx] * unit
        if idx % 2:
            cv.rect("row-band", X, y, W, rh, fill=fam["zebra"])
        cv.rect("task-cell", X, y, task_w, rh, fill=fam["pale"])
        t_lines = wrap(it["task"], fs, task_w - fs * 1.2, bold=True, max_lines=3)
        block_h = fs * 1.3 * len(t_lines) + fs * 2.1
        ty = y + (rh - block_h) / 2
        cv.text("task-text", X + task_w / 2, ty + fs, t_lines, fs, fill=fam["navy"], bold=True, anchor="middle", leading=1.3)
        pill_size = base
        pw = text_width(it["status"], pill_size, True) + pill_size * 1.4
        _pill(cv, X + task_w / 2 - pw / 2, ty + fs * 1.3 * len(t_lines) + fs * 0.25, it["status"], pill_size)
        for ci, col in enumerate((done, nxt)):
            cx = X + task_w + ci * col_w + fs * 0.7
            line_h = min(unit, fs * 1.5)
            cy = y + (rh - line_h * len(col)) / 2 + fs * 0.95
            for text_s, bold in col:
                cv.text("cell-text", cx, cy, text_s, fs if bold else base,
                        fill=fam["text"] if bold else fam["muted"], bold=bold)
                cy += line_h
        cv.line("row-rule", X, y + rh, X + W, y + rh, fam["rule"], 0.75, dash=True)
        y += rh
    cv.line("col-sep", X + task_w + col_w, Y + head_h, X + task_w + col_w, y, fam["rule"], 0.75)
    if requests:
        ry = Y + H - req_h
        cv.rect("request-band", X, ry, W, req_h, fill=fam["pale"], stroke=fam["panel"])
        cv.rect("request-tag", X, ry, task_w, req_h, fill=fam["navy"])
        cv.text_block("request-label", X + task_w / 2, ry, ["요청 사항"], fs, req_h, fill=fam["white"], bold=True, anchor="middle")
        lines = []
        for rq in requests:
            lines += wrap(f"✓ {rq}", fs, W - task_w - fs * 1.4, max_lines=2)
        cv.items("request-text", X + task_w + fs * 0.7, ry + (req_h - fs * 1.3 * len(lines)) / 2 + fs * 0.95, lines, fs,
                 leading=1.3, fill=fam["text"])


# ---------------------------------------------------------------------------
# Issue / action table
# ---------------------------------------------------------------------------

ISSUE_COLS = [("issue", "이슈", 0.24), ("impact", "영향", 0.18), ("action", "조치", 0.26),
              ("request", "요청·기한", 0.18), ("status", "상태", 0.14)]


def check_issues(data: dict[str, Any]) -> list[str]:
    errors = []
    rows = data.get("issues", [])
    if not 1 <= len(rows) <= 6:
        errors.append(f"{len(rows)} issues; use 1–6")
    for r in rows:
        if r.get("status") not in STATES:
            errors.append(f"issue {r.get('issue')!r}: status must be one of {STATES}")
    return errors


def draw_issues(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    base = fam["min_px"]
    fs = fam["ladder"][1]
    head_h = fs * 2.0
    rows = data["issues"]
    cv.rect("head", X, Y, W, head_h, fill=fam["navy"])
    xs = [X]
    for _, _, share in ISSUE_COLS:
        xs.append(xs[-1] + W * share)
    for i, (_, label, _) in enumerate(ISSUE_COLS):
        cv.text_block("head-text", (xs[i] + xs[i + 1]) / 2, Y, [label], fs, head_h, fill=fam["white"], bold=True, anchor="middle")
    wrapped = []
    for r in rows:
        cells = []
        for i, (key, _, _) in enumerate(ISSUE_COLS[:-1]):
            cells.append(wrap(str(r.get(key, "")), fs if key == "issue" else base, xs[i + 1] - xs[i] - fs, bold=key == "issue",
                              max_lines=4))
        wrapped.append(cells)
    weights = [max(max(len(c) for c in cells), 2) for cells in wrapped]
    unit = min((H - head_h) / sum(weights), fs * 2.6)
    y = Y + head_h
    for r, cells, wgt in zip(rows, wrapped, weights):
        rh = wgt * unit
        for i, lines in enumerate(cells):
            key = ISSUE_COLS[i][0]
            cv.text_block("cell", xs[i] + fs * 0.5, y, lines, fs if key == "issue" else base, rh,
                          fill=fam["navy"] if key == "issue" else fam["text"], bold=key == "issue")
        pw = text_width(r["status"], base, True) + base * 1.4
        _pill(cv, (xs[-2] + xs[-1]) / 2 - pw / 2, y + (rh - base * 1.65) / 2, r["status"], base)
        cv.line("row-rule", X, y + rh, X + W, y + rh, fam["rule"], 0.75)
        y += rh
    for x in xs[1:-1]:
        cv.line("col-rule", x, Y + head_h, x, y, fam["rule"], 0.75)


# ---------------------------------------------------------------------------
# Scope (수행범위)
# ---------------------------------------------------------------------------

def check_scope(data: dict[str, Any]) -> list[str]:
    errors = []
    variant = data.get("variant", "modules")
    if variant == "modules":
        mods = data.get("modules", [])
        if not 2 <= len(mods) <= 6:
            errors.append(f"{len(mods)} modules; use 2–6")
        for m in mods:
            if not 1 <= len(m.get("activities", [])) <= 5:
                errors.append(f"module {m.get('title')!r}: 1–5 activities")
    elif variant == "matrix":
        cols = data.get("columns", [])
        if not 1 <= len(cols) <= 7:
            errors.append(f"{len(cols)} scope columns; use 1–7")
        targets = data.get("targets", [])
        if not 1 <= len(targets) <= 12:
            errors.append(f"{len(targets)} targets; use 1–12")
        for t in targets:
            for c in cols:
                v = t.get("scope", {}).get(c)
                if v not in SCOPE_MARKS:
                    errors.append(f"target {t.get('name')!r} / {c}: use 포함·선택·제외 (got {v!r})")
    elif variant == "deliverables":
        d = data.get("deliverables", [])
        if not 2 <= len(d) <= 6:
            errors.append(f"{len(d)} deliverables; use 2–6")
    else:
        errors.append(f"unknown scope variant {variant!r}")
    return errors


def draw_scope(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    variant = data.get("variant", "modules")
    {"modules": _scope_modules, "matrix": _scope_matrix, "deliverables": _scope_deliverables}[variant](cv, data, box)


def _scope_modules(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    base = fam["min_px"]
    fs = fam["ladder"][1]
    mods = data["modules"]
    banner = data.get("banner")
    if banner:
        bh = fs * 2.2
        cv.rect("banner", X, Y, W, bh, fill=fam["pale"], stroke=fam["panel"])
        tag = data.get("tag", "수행 범위")
        tw = text_width(tag, fs, True) + fs * 2
        cv.poly("banner-tag", [(X, Y), (X + tw, Y), (X + tw + bh * 0.35, Y + bh / 2), (X + tw, Y + bh), (X, Y + bh)], fam["navy"])
        cv.text_block("banner-tag-text", X + tw / 2, Y, [tag], fs, bh, fill=fam["white"], bold=True, anchor="middle")
        cv.text_block("banner-text", X + tw + bh * 0.35 + fs, Y, [banner], fs, bh, fill=fam["navy"], bold=True)
        Y += bh + fs * 0.7
        H -= bh + fs * 0.7
    cols = 3 if len(mods) in (3, 5, 6) else 2
    rows = (len(mods) + cols - 1) // cols
    gap = fs * 0.8
    mw = (W - gap * (cols - 1)) / cols
    mh = (H - gap * (rows - 1)) / rows
    for i, m in enumerate(mods):
        mx = X + (i % cols) * (mw + gap)
        my = Y + (i // cols) * (mh + gap)
        optional = m.get("optional", False)
        hh = fs * 2.2
        cv.rect("module-box", mx, my, mw, mh, fill=fam["white"], stroke=fam["neutral"] if optional else fam["rule"],
                dash=optional)
        cv.rect("module-head", mx, my, mw, hh, fill=fam["navy"] if not optional else fam["muted"])
        title = f"{i + 1:02d}  {m['title']}" + (" (필요 시)" if optional else "")
        cv.text_block("module-title", mx + fs * 0.7, my, wrap(title, fs, mw - fs * 1.4, True, 1), fs, hh,
                      fill=fam["white"], bold=True)
        lines: list[str] = []
        for a in m.get("activities", []):
            lines += wrap(f"· {a}", fs, mw - fs * 1.6, max_lines=2)
        cv.items("module-body", mx + fs * 0.7, my + hh + fs * 1.5, lines, fs, leading=1.4)
        if m.get("output"):
            oh = fs * 2.2
            cv.rect("module-output", mx + 1, my + mh - oh - 1, mw - 2, oh, fill=fam["pale"])
            cv.text_block("module-output-text", mx + fs * 0.7, my + mh - oh - 1,
                          wrap(f"→ {m['output']}", fs, mw - fs * 1.4 - (text_width(m.get('due', ''), base) + fs if m.get('due') else 0), True, 1),
                          fs, oh, fill=fam["navy"], bold=True)
        if m.get("due"):
            due_y = my + mh - fs * 2.2 - 1 if m.get("output") else my + mh - fs * 2.2
            cv.text_block("module-due", mx + mw - fs * 0.6, due_y, [m["due"]], base, fs * 2.2, fill=fam["accent"],
                          bold=True, anchor="end")


def _scope_matrix(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    base = fam["min_px"]
    fs = fam["ladder"][1]
    cols = data["columns"]
    targets = data["targets"]
    attrs = data.get("attributes", [])  # e.g. ["형태", "위치"]
    out = data.get("out_of_scope") or []
    note_h = fs * 2.0 + (fs * 3.0 if out else 0)
    head_h = fs * 2.2
    name_w = W * 0.24
    attr_w = W * 0.13
    mark_w = (W - name_w - attr_w * len(attrs)) / len(cols)
    row_h = min((H - head_h - note_h) / len(targets), fs * 3.6)
    cv.rect("head", X, Y, W, head_h, fill=fam["navy"])
    cv.text_block("head-name", X + name_w / 2, Y, [data.get("target_label", "대상")], fs, head_h, fill=fam["white"],
                  bold=True, anchor="middle")
    x = X + name_w
    for a in attrs:
        cv.text_block("head-attr", x + attr_w / 2, Y, [a], fs, head_h, fill=fam["white"], bold=True, anchor="middle")
        x += attr_w
    for c in cols:
        cv.text_block("head-col", x + mark_w / 2, Y, wrap(c, fs, mark_w - 6, True, 2), fs, head_h, fill=fam["white"],
                      bold=True, anchor="middle", leading=1.1)
        x += mark_w
    y = Y + head_h
    for i, t in enumerate(targets):
        if i % 2:
            cv.rect("row-band", X, y, W, row_h, fill=fam["zebra"])
        cv.text_block("target-name", X + fs * 0.6, y, wrap(t["name"], fs, name_w - fs, True, 2), fs, row_h,
                      fill=fam["navy"], bold=True)
        x = X + name_w
        for a in attrs:
            cv.text_block("target-attr", x + attr_w / 2, y, [str(t.get("attributes", {}).get(a, ""))], base, row_h,
                          anchor="middle")
            x += attr_w
        for c in cols:
            v = t["scope"][c]
            color = {"포함": fam["accent"], "선택": fam["light"], "제외": fam["neutral"]}[v]
            cv.text_block("mark", x + mark_w / 2, y, [f"{SCOPE_MARKS[v]} {v}"], base, row_h, fill=color,
                          bold=v != "제외", anchor="middle")
            x += mark_w
        cv.line("row-rule", X, y + row_h, X + W, y + row_h, fam["rule"], 0.75)
        y += row_h
    cv.text("legend", X + W, y + fs * 1.4, "● 포함   ◐ 선택(필요 시)   – 제외", base, fill=fam["muted"], anchor="end")
    if out:
        oy = y + fs * 2.4
        oh = fs * 2.4
        cv.rect("out-scope", X, oy, W, oh, fill=fam["zebra"], stroke=fam["rule"])
        cv.rect("out-scope-tag", X, oy, name_w, oh, fill=fam["muted"])
        cv.text_block("out-scope-label", X + name_w / 2, oy, ["범위 밖(제외)"], fs, oh, fill=fam["white"], bold=True,
                      anchor="middle")
        cv.text_block("out-scope-text", X + name_w + fs * 0.7, oy, [" · ".join(out)], fs, oh, fill=fam["text"])


def _scope_deliverables(cv: Canvas, data: dict[str, Any], box: tuple[float, float, float, float]) -> None:
    fam = cv.fam
    X, Y, W, H = box
    base = fam["min_px"]
    fs = fam["ladder"][1]
    items = data["deliverables"]
    cols = 3 if len(items) > 4 or len(items) == 3 else 2
    rows = (len(items) + cols - 1) // cols
    gap = fs * 0.8
    cw = (W - gap * (cols - 1)) / cols
    ch = (H - gap * (rows - 1)) / rows
    for i, d in enumerate(items):
        cx = X + (i % cols) * (cw + gap)
        cy = Y + (i // cols) * (ch + gap)
        hh = fs * 2.1
        cv.rect("deliv-box", cx, cy, cw, ch, fill=fam["zebra"], stroke=fam["rule"])
        cv.rect("deliv-head", cx, cy, cw, hh, fill=fam["navy"])
        cv.text_block("deliv-title", cx + fs * 0.6, cy, wrap(d["name"], fs, cw - fs * 4.5, True, 1), fs, hh,
                      fill=fam["white"], bold=True)
        if d.get("phase"):
            cv.text_block("deliv-phase", cx + cw - fs * 0.6, cy, [d["phase"]], base, hh, fill=fam["mid"], bold=True,
                          anchor="end")
        body_y = cy + hh
        body_h = ch - hh
        if d.get("image"):
            iw, ih = cw - fs * 1.2, body_h - fs * 3.2
            cv.parts.append(f'<image id="{cv._id("deliv-image")}" x="{cx + fs * 0.6:.1f}" y="{body_y + fs * 0.6:.1f}" '
                            f'width="{iw:.1f}" height="{ih:.1f}" href="{escape(d["image"])}" '
                            f'preserveAspectRatio="xMidYMid meet"/>')
        else:
            cv.rect("deliv-placeholder", cx + fs * 0.6, body_y + fs * 0.6, cw - fs * 1.2, body_h - fs * 3.2,
                    fill=fam["white"], stroke=fam["panel"], dash=True)
            if d.get("desc"):
                cv.text_block("deliv-desc", cx + cw / 2, body_y + fs * 0.6,
                              wrap(d["desc"], base, cw - fs * 2.4, max_lines=3), base, body_h - fs * 3.2,
                              fill=fam["muted"], anchor="middle")
        if d.get("illustrative", True):
            cv.text("deliv-illustrative", cx + cw - fs * 0.6, cy + ch - fs * 0.7, "Illustrative", base,
                    fill=fam["muted"], anchor="end")


# ---------------------------------------------------------------------------
# Registry, examples, slide assembly
# ---------------------------------------------------------------------------

KINDS = {
    "schedule": (check_schedule, draw_schedule, "수행일정 간트(계층 과업·월/반월/주·보고 행·기준일)"),
    "procedure": (check_procedure, draw_procedure, "추진절차(단계 셰브론·병행 흐름·노드 격자·산출물·현재 단계)"),
    "status": (check_status, draw_status, "세부현황(과업 | 진행 현황 | 향후 계획 + 상태어·요청 사항)"),
    "issues": (check_issues, draw_issues, "이슈·조치 표(이슈 | 영향 | 조치 | 요청·기한 | 상태)"),
    "scope": (check_scope, draw_scope, "수행범위(modules 모듈 격자 / matrix 포함·제외 / deliverables 산출물)"),
}

EXAMPLES: dict[str, dict[str, Any]] = {
    "schedule": {
        "kind": "schedule", "stage": "kickoff",
        "title": "1. 수행 일정", "governing": "11월 착수 후 6개월간 3단계로 과업을 수행할 예정입니다",
        "source": "", "section": "사업 수행 계획",
        "period": {"start": "2026-11", "end": "2027-04", "unit": "month"},
        "groups": [
            {"label": "현황 진단", "tasks": [
                {"label": "자료 요청·수집", "start": "2026-11", "end": "2026-11", "note": "자료요청서"},
                {"label": "배출원·감축 잠재량 진단", "start": "2026-11-15", "end": "2026-12"}]},
            {"label": "방법론·산정", "tasks": [
                {"label": "베이스라인 시나리오 설정", "start": "2026-12", "end": "2027-01"},
                {"label": "모니터링 인자·산정식 확정", "start": "2027-01", "end": "2027-02", "note": "산정식 Word"},
                {"label": "감축량 산정", "start": "2027-02", "end": "2027-03"}]},
            {"label": "보고·확정", "tasks": [
                {"label": "모니터링 계획서 작성", "start": "2027-03", "end": "2027-04", "note": "계획서"},
                {"label": "주간 진행 보고", "start": "2026-11", "end": "2027-04", "kind": "continuous"}]},
        ],
        "reports": [{"type": "착수", "at": "2026-11"}, {"type": "중간", "at": "2027-02"},
                    {"type": "최종", "at": "2027-04"}],
    },
    "procedure": {
        "kind": "procedure", "stage": "kickoff",
        "title": "2. 추진 절차", "governing": "현황 진단부터 계획서 확정까지 4단계로 진행할 예정입니다",
        "phases": [
            {"label": "현황 진단", "period": "1개월", "outputs": ["자료요청서", "진단 결과"]},
            {"label": "방법론 검토", "period": "1.5개월", "outputs": ["적용 방법론 검토서"]},
            {"label": "산정·모니터링 설계", "period": "2개월", "outputs": ["산정식(Word·PPT 수식)", "모니터링 인자표"]},
            {"label": "계획서 확정", "period": "1.5개월", "outputs": ["모니터링 계획서"]}],
        "lanes": ["컨설팅", "고객사"],
        "nodes": [
            {"id": "a1", "phase": 0, "lane": "컨설팅", "label": "자료 요청"},
            {"id": "b1", "phase": 0, "lane": "고객사", "label": "운영 자료 제공"},
            {"id": "a2", "phase": 1, "lane": "컨설팅", "label": "적용 방법론 비교"},
            {"id": "a3", "phase": 2, "lane": "컨설팅", "label": "베이스라인 설정"},
            {"id": "a4", "phase": 2, "lane": "컨설팅", "label": "모니터링 인자 정의"},
            {"id": "b3", "phase": 2, "lane": "고객사", "label": "계측 체계 확인"},
            {"id": "a5", "phase": 3, "lane": "컨설팅", "label": "계획서 작성"},
            {"id": "b4", "phase": 3, "lane": "고객사", "label": "검토·확정"}],
        "edges": [["a1", "a2"], ["b1", "a2"], ["a2", "a3"], ["a4", "a5"], ["b3", "b4"]],
        "terminal": "최종 보고",
    },
    "status": {
        "kind": "status", "stage": "interim",
        "title": "3. 세부 진행 현황", "governing": "진단·방법론 검토는 완료했고 산정은 진행 중이며 3월 확정 예정입니다",
        "periods": {"done": "~2/14", "next": "2/15~3/31"},
        "items": [
            {"task": "현황 진단", "status": "완료",
             "done": [{"headline": "배출원 목록·감축 잠재량 확정", "date": "12.20", "details": ["사업장 3곳 현장 확인"]}],
             "next": [{"headline": "n/a"}]},
            {"task": "방법론·산정", "status": "진행 중",
             "done": [{"headline": "베이스라인 시나리오 합의", "date": "1.30"}],
             "next": [{"headline": "감축량 산정", "date": "3.15", "expected": True,
                       "details": ["계측 자료 12개월분 반영"]}]},
            {"task": "모니터링 설계", "status": "보완",
             "done": [{"headline": "모니터링 인자 초안", "date": "2.10", "details": ["유량계 검교정 주기 확인 필요"]}],
             "next": [{"headline": "인자표·QA/QC 확정", "date": "2.28", "expected": True}]}],
        "requests": ["유량계 검교정 성적서(최근 2년) 2/20까지 송부 요청"],
    },
    "issues": {
        "kind": "issues", "stage": "interim", "title": "4. 이슈 및 조치",
        "governing": "계측 자료 공백 1건은 대체 산정으로 조치하고 2월 중 확정할 예정입니다",
        "issues": [
            {"issue": "계측 자료 2개월 누락", "impact": "감축량 과소 산정", "action": "구매 기록으로 대체 산정",
             "request": "구매 영수증 2/20", "status": "진행 중"},
            {"issue": "배출계수 공표 지연", "impact": "최종값 확정 지연", "action": "직전 연도 값 잠정 적용",
             "request": "-", "status": "예정"}],
    },
    "scope": {
        "kind": "scope", "variant": "modules", "stage": "kickoff",
        "title": "1. 수행 범위", "governing": "감축사업 등록에 필요한 진단·산정·모니터링 설계를 수행할 예정입니다",
        "banner": "감축사업 방법론 적용 및 모니터링 계획 수립", "tag": "수행 범위",
        "modules": [
            {"title": "현황 진단", "activities": ["배출원·에너지 사용 현황", "감축 잠재량 진단"], "output": "진단 결과서", "due": "~12월"},
            {"title": "방법론 검토", "activities": ["적용 가능 방법론 비교", "적용 조건 확인"], "output": "방법론 검토서", "due": "~1월"},
            {"title": "베이스라인 설정", "activities": ["시나리오 대안 분석", "추가성 검토"], "output": "베이스라인 시나리오", "due": "~1월"},
            {"title": "산정식 수립", "activities": ["베이스라인·사업·누출 배출량", "Word·PPT 편집 가능 수식"], "output": "산정식(Word·PPT)", "due": "~2월"},
            {"title": "모니터링 설계", "activities": ["모니터링 인자·주기", "QA/QC 절차"], "output": "모니터링 인자표", "due": "~3월"},
            {"title": "등록 지원", "activities": ["계획서 작성", "검증 대응"], "optional": True,
             "output": "모니터링 계획서", "due": "~4월"}],
    },
}


def _fill_placeholder(root: ET.Element, gid: str, value: Optional[str]) -> None:
    if value is None:
        return
    for g in root.iter(f"{{{SVG_NS}}}g"):
        if g.get("id") == gid:
            for t in g.iter(f"{{{SVG_NS}}}text"):
                for ch in list(t):
                    t.remove(ch)
                t.text = value
                return


def check(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one diagram data file."""
    kind = data.get("kind")
    if kind not in KINDS:
        return [f"unknown kind {kind!r}; use one of {sorted(KINDS)}"], []
    errors = KINDS[kind][0](data)
    warnings: list[str] = []
    stage = data.get("stage")
    if stage and stage not in STAGES:
        errors.append(f"stage must be one of {STAGES}")
    gov = data.get("governing", "")
    if stage in STAGE_TENSE and gov:
        pattern, msg = STAGE_TENSE[stage]
        if not re.search(pattern, gov):
            warnings.append(msg)
    if stage in ("kickoff", "final") and re.search(r"진행률|\d+\s?%", json.dumps(data, ensure_ascii=False)):
        warnings.append("보고 레퍼런스는 진행률(%) 대신 상태어·날짜를 씁니다")
    return errors, warnings


def build(data: dict[str, Any], family: str, base: Optional[Path], mode: str = "structured") -> str:
    if family not in FAMILIES:
        raise DiagramError(f"unknown family {family!r}; use one of {sorted(FAMILIES)}")
    base = base or DECKS_DIR / family / "templates" / "03a_content.svg"
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(str(base))
    root = tree.getroot()
    area = None
    parent = None
    for p in root.iter():
        for ch in list(p):
            if ch.get("id") in ("content-area", "report-diagram"):
                area, parent = ch, p
                break
        if area is not None:
            break
    if area is None:
        raise DiagramError(f"{base.name}: no content-area placeholder to replace")
    if area.get("data-pptx-placeholder-bounds"):
        X, Y, W, H = (float(v) for v in area.get("data-pptx-placeholder-bounds").split())
    else:
        X, Y, W, H = (float(area.get(k)) for k in ("x", "y", "width", "height"))
    kind = data["kind"]
    cv = Canvas(FAMILIES[family], "report-diagram")
    KINDS[kind][1](cv, data, (X, Y, W, H))
    fragment = ET.fromstring(f'<svg xmlns="{SVG_NS}">{cv.svg(kind)}</svg>')[0]
    idx = list(parent).index(area)
    parent.remove(area)
    parent.insert(idx, fragment)
    root.set("data-report-diagram", kind)
    _fill_placeholder(root, "content-title", data.get("title"))
    _fill_placeholder(root, "key-message", data.get("governing"))
    _fill_placeholder(root, "source-note", data.get("source", ""))
    _fill_placeholder(root, "footer-section", data.get("section", ""))
    _fill_placeholder(root, "page-number", str(data.get("page", "")))
    if mode == "flat":
        _flatten_structure(root)
    return ET.tostring(root, encoding="unicode")


STRUCTURE_ATTRS = ("data-pptx-layer", "data-pptx-layout", "data-pptx-layout-name", "data-pptx-master",
                   "data-pptx-master-name", "data-pptx-placeholder", "data-pptx-placeholder-bounds",
                   "data-pptx-placeholder-carrier", "data-pptx-placeholder-idx", "data-pptx-editable")


def _flatten_structure(root: ET.Element) -> None:
    """Drop Master/Layout/placeholder metadata for pptx_structure.mode: flat projects."""
    for el in root.iter():
        for attr in STRUCTURE_ATTRS:
            el.attrib.pop(attr, None)
    root.set("data-pptx-page-role", root.get("data-pptx-page-role") or "content")


def detect_mode(output: Path) -> str:
    """Read pptx_structure.mode from the project that owns svg_output/<slide>."""
    lock = output.resolve().parent.parent / "spec_lock.md"
    if lock.is_file():
        m = re.search(r"##\s*pptx_structure\s*\n-\s*mode:\s*(\w+)", lock.read_text(encoding="utf-8"))
        if m:
            return "flat" if m.group(1) == "flat" else "structured"
    return "structured"


def _copy_chrome_images(svg: str, base: Path, output: Path) -> None:
    """Copy relative chrome images (logos) next to the output, as deck templates expect."""
    import shutil
    for href in re.findall(r'(?:xlink:)?href="(?!data:|https?:)([^"]+)"', svg):
        src = (base.parent / href).resolve()
        dst = (output.parent / href).resolve()
        if src.is_file() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="INNerGEN report-stage diagrams from JSON.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("kinds", help="list diagram kinds")
    ex = sub.add_parser("example", help="print example data")
    ex.add_argument("kind", choices=sorted(KINDS))
    ck = sub.add_parser("check", help="validate data")
    ck.add_argument("data", type=Path)
    bd = sub.add_parser("build", help="write a slide SVG")
    bd.add_argument("data", type=Path)
    bd.add_argument("--family", required=True, choices=sorted(FAMILIES))
    bd.add_argument("--base", type=Path, default=None, help="chrome slide with a content-area placeholder")
    bd.add_argument("-o", "--output", type=Path, required=True)
    bd.add_argument("--mode", choices=("auto", "structured", "flat"), default="auto",
                    help="pptx_structure mode; auto reads <project>/spec_lock.md")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    if args.command == "kinds":
        for k, (_, _, desc) in KINDS.items():
            print(f"{k:10s} {desc}")
        return 0
    if args.command == "example":
        print(json.dumps(EXAMPLES[args.kind], ensure_ascii=False, indent=2))
        return 0
    data = json.loads(args.data.read_text(encoding="utf-8"))
    errors, warnings = check(data)
    for w in warnings:
        print(f"WARN   {w}")
    for e in errors:
        print(f"ERROR  {e}")
    if errors:
        return 1
    if args.command == "check":
        print(f"OK  {args.data}  kind={data['kind']}")
        return 0
    try:
        mode = detect_mode(args.output) if args.mode == "auto" else args.mode
        svg = build(data, args.family, args.base, mode)
    except DiagramError as exc:
        print(f"ERROR  {exc}")
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    _copy_chrome_images(svg, args.base or DECKS_DIR / args.family / "templates" / "03a_content.svg", args.output)
    print(f"OK  {args.output}  kind={data['kind']}  family={args.family}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
