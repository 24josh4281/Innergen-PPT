#!/usr/bin/env python3
"""
INNerGEN v30 report diagrams (s65–s74) for the three deck families.

Builds the proposal / interim / final-report structures borrowed (structure
only) from public Big4 and MBB method pages - see consulting-references-v30.md -
in the INNerGEN families' own chrome, palette and type sizes. Chrome (title,
governing line, source, footer, page number) is copied verbatim from each
family's s44 template so QA geometry stays identical.

Usage:
    python3 docs/innergen-v30/build_templates_v30.py --skill claude-skills/innergen-deck --out OUT
      writes OUT/<family>/s65_*.svg … and, with --update-json, adds them to
      templates/decks/<family>.json (layout SVGs + design_spec.md rows).

Dependencies: standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CHROME_IDS = ("master-bg", "title-bar", "top-rule", "governing-rule", "governing-box", "footer-line",
              "footer-logo", "content-title", "key-message", "source-note", "footer-section", "page-number")

FAMILIES = {
    "innergen_business": dict(
        prefix="innergen-biz", master="innergen-biz-master-16x9", master_name="이너젠 회사소개 16:9",
        name="이너젠 회사소개", box=(24, 94, 936, 486), font='"IBM Plex Sans KR", "Malgun Gothic", sans-serif',
        dark="#2B4C7E", accent="#518FFF", accent2="#8FB3FF", tint="#B9CFFF", zebra="#F3F7FF", strip="#EEF3FF",
        text="#000000", muted="#595959", line="#D9D9D9", conn="#A6A6A6", cell=12, label=12, small=10.67, big=21.33),
    "innergen_lecture": dict(
        prefix="innergen-intro", master="innergen-intro-master-13x9", master_name="이너젠 소개자료 13:9",
        name="이너젠 소개자료", box=(48, 120, 992, 604), font='Pretendard, "Malgun Gothic", sans-serif',
        dark="#0B1739", accent="#2F62F0", accent2="#7B9BF7", tint="#B8CBF9", zebra="#F3F6FF", strip="#EEF2FF",
        text="#475569", muted="#64748B", line="#E2E8F0", conn="#94A3B8", cell=12, label=13.33, small=12, big=24),
    "innercarry": dict(
        prefix="innercarry", master="innercarry-master-4x3", master_name="이너캐리 4:3",
        name="이너캐리", box=(56, 156, 968, 616), font='"IBM Plex Sans KR", "Malgun Gothic", sans-serif',
        dark="#0B1739", accent="#2F62F0", accent2="#7B9BF7", tint="#B8CBF9", zebra="#F3F6FF", strip="#EEF2FF",
        text="#475569", muted="#64748B", line="#E2E8F0", conn="#94A3B8", cell=12, label=12, small=10.67, big=21.33),
}


def r1(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Svg:
    def __init__(self, fam: dict, chrome: list[str]):
        self.f = fam
        self.layout: list[str] = []
        self.slots: list[str] = []
        self.tokens: list[str] = []
        self.chrome = chrome
        self.idx = 0
        x0, y0, x1, y1 = fam["box"]
        self.x0, self.y0, self.w, self.h = x0, y0, x1 - x0, y1 - y0

    # coordinates: u/v are fractions of the content box
    def X(self, u):
        return self.x0 + u * self.w

    def Y(self, v):
        return self.y0 + v * self.h

    def _attrs(self):
        return 'data-pptx-layer="layout" data-pptx-editable="false"'

    def rect(self, id_, x, y, w, h, fill, stroke=None, rx=0, dash=None):
        s = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
        s += f' stroke-dasharray="{dash}"' if dash else ""
        r = f' rx="{rx}" ry="{rx}"' if rx else ""
        self.layout.append(f'<rect id="{id_}" x="{r1(x)}" y="{r1(y)}" width="{r1(w)}" height="{r1(h)}"{r} fill="{fill}"{s} {self._attrs()}/>')

    def line(self, id_, x1, y1, x2, y2, color=None, width=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.layout.append(f'<line id="{id_}" x1="{r1(x1)}" y1="{r1(y1)}" x2="{r1(x2)}" y2="{r1(y2)}" stroke="{color or self.f["line"]}" stroke-width="{width}"{d} {self._attrs()}/>')

    def path(self, id_, d, fill, stroke=None, width=1, dash=None):
        s = f' stroke="{stroke}" stroke-width="{width}"' if stroke else ""
        s += f' stroke-dasharray="{dash}"' if dash else ""
        self.layout.append(f'<path id="{id_}" d="{d}" fill="{fill}"{s} {self._attrs()}/>')

    def circle(self, id_, cx, cy, r, fill, stroke=None):
        s = f' stroke="{stroke}" stroke-width="1.5"' if stroke else ""
        self.layout.append(f'<circle id="{id_}" cx="{r1(cx)}" cy="{r1(cy)}" r="{r1(r)}" fill="{fill}"{s} {self._attrs()}/>')

    def label(self, id_, x, y, text, size=None, fill=None, weight=700, anchor="start"):
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.layout.append(f'<text id="{id_}" x="{r1(x)}" y="{r1(y)}"{a} font-family=\'{self.f["font"]}\' font-size="{size or self.f["label"]}" font-weight="{weight}" fill="{fill or self.f["dark"]}" {self._attrs()}>{text}</text>')

    def slot(self, id_, token, x, y, w, h, size=None, fill=None, weight=400, anchor="start", valign="top", pad=6):
        """Placeholder text box. valign top: baseline at top+pad+size; middle: centred."""
        self.idx += 1
        size = size or self.f["cell"]
        if valign == "top":
            by = y + pad + size * 0.9
        else:
            by = y + h / 2 + size * 0.35
        if anchor == "middle":
            tx = x + w / 2
        elif anchor == "end":
            tx = x + w - pad
        else:
            tx = x + pad
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        self.tokens.append(token)
        self.slots.append(
            f'<g id="{id_}" data-pptx-placeholder="body" data-pptx-placeholder-idx="{self.idx}" data-pptx-placeholder-bounds="{r1(x)} {r1(y)} {r1(w)} {r1(h)}">'
            f'<text id="{id_}-carrier" data-pptx-placeholder-carrier="true" data-card-slot-bounds="{r1(x)} {r1(y)} {r1(w)} {r1(h)}" x="{r1(tx)}" y="{r1(by)}"{a} font-family=\'{self.f["font"]}\' font-size="{size}" font-weight="{weight}" fill="{fill or self.f["text"]}">{{{{{token}}}}}</text></g>')

    def card(self, background, members, gap=6, padding=8):
        """Declare an ordered stack without changing native object identities."""
        # A static label that travels with the stack belongs to the slide, not
        # the shared Layout. Keep Layout geometry stable across content lengths.
        for member in members:
            for atom in list(self.layout):
                if f'id="{member}"' in atom:
                    self.layout.remove(atom)
                    self.slots.append(atom.replace(self._attrs(), ""))
        for i, rect in enumerate(self.layout):
            if f'id="{background}"' in rect:
                attrs = (f' data-card-members="{" ".join(members)}"'
                         f' data-card-gap="{gap}" data-card-padding="{padding}"')
                self.layout[i] = rect.replace('/>', attrs + '/>')
                return
        raise ValueError(f"Missing card background: {background}")

    def render(self, layout_id: str, layout_name: str, canvas: tuple[int, int]) -> str:
        f = self.f
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {canvas[0]} {canvas[1]}" '
                f'data-pptx-master="{f["master"]}" data-pptx-master-name="{f["master_name"]}" '
                f'data-pptx-layout="{f["prefix"]}-{layout_id}" data-pptx-layout-name="{f["name"]} {layout_name}">')
        chrome_layout = [c for c in self.chrome if 'data-pptx-placeholder=' not in c]
        chrome_slots = [c for c in self.chrome if 'data-pptx-placeholder=' in c]
        # keep chrome placeholders first among slots (title, key message) and source/footer/page after
        first = [c for c in chrome_slots if 'id="content-title"' in c or 'id="key-message"' in c]
        last = [c for c in chrome_slots if c not in first]
        return "\n".join([head] + chrome_layout + self.layout + first + self.slots + last + ["</svg>"]) + "\n"


# ---------------------------------------------------------------- layouts
def s65(s: Svg):
    """과업 이해: 고객 상황 → 핵심 쟁점 → 이너젠 대응 방향 (proposal 'our understanding')."""
    f = s.f
    hh = 0.085
    cols = [(0.0, 0.27, "고객 상황", f["zebra"], f["dark"]), (0.29, 0.31, "핵심 쟁점", f["dark"], "#FFFFFF"),
            (0.65, 0.35, "이너젠 대응 방향", f["accent"], "#FFFFFF")]
    for i, (u, w, name, bg, fg) in enumerate(cols, 1):
        s.rect(f"head-{i}-bg", s.X(u), s.Y(0), w * s.w, hh * s.h, bg)
        s.label(f"head-{i}-label", s.X(u) + w * s.w / 2, s.Y(hh / 2) + f["label"] * 0.35, name, fill=fg, anchor="middle")
    top, bot = 0.115, 0.86
    s.rect("situation-bg", s.X(0), s.Y(top), 0.27 * s.w, (bot - top) * s.h, f["zebra"])
    s.slot("situation-title", "SITUATION_TITLE", s.X(0), s.Y(top), 0.27 * s.w, 0.1 * s.h, weight=700, fill=f["dark"])
    s.slot("situation-body", "SITUATION_BODY", s.X(0), s.Y(top + 0.1), 0.27 * s.w, (bot - top - 0.1) * s.h)
    gap = 0.025
    rh = (bot - top - 2 * gap) / 3
    for i in range(3):
        v = top + i * (rh + gap)
        s.rect(f"issue-{i+1}-box", s.X(0.29), s.Y(v), 0.31 * s.w, rh * s.h, "#FFFFFF", stroke=f["line"])
        s.circle(f"issue-{i+1}-badge", s.X(0.29) + 16, s.Y(v) + 18, 9, f["dark"])
        s.label(f"issue-{i+1}-no", s.X(0.29) + 16, s.Y(v) + 18 + f["small"] * 0.35, str(i + 1), size=f["small"], fill="#FFFFFF", anchor="middle")
        s.slot(f"issue-{i+1}-title", f"ISSUE_{i+1}_TITLE", s.X(0.29) + 28, s.Y(v), 0.31 * s.w - 28, 0.08 * s.h, weight=700, fill=f["dark"])
        s.slot(f"issue-{i+1}-body", f"ISSUE_{i+1}_BODY", s.X(0.29) + 28, s.Y(v + 0.07), 0.31 * s.w - 28, (rh - 0.07) * s.h)
        ay = s.Y(v + rh / 2)
        ax0, ax1 = s.X(0.605), s.X(0.645)
        s.path(f"arrow-{i+1}", f"M {r1(ax0)} {r1(ay-7)} L {r1(ax1-8)} {r1(ay-7)} L {r1(ax1-8)} {r1(ay-12)} L {r1(ax1)} {r1(ay)} L {r1(ax1-8)} {r1(ay+12)} L {r1(ax1-8)} {r1(ay+7)} L {r1(ax0)} {r1(ay+7)} Z", f["tint"])
        s.rect(f"resp-{i+1}-box", s.X(0.65), s.Y(v), 0.35 * s.w, rh * s.h, f["strip"])
        s.rect(f"resp-{i+1}-bar", s.X(0.65), s.Y(v), 3, rh * s.h, f["accent"])
        s.slot(f"resp-{i+1}-title", f"RESP_{i+1}_TITLE", s.X(0.65) + 6, s.Y(v), 0.25 * s.w, 0.08 * s.h, weight=700, fill=f["accent"])
        s.slot(f"resp-{i+1}-module", f"RESP_{i+1}_MODULE", s.X(0.9), s.Y(v), 0.1 * s.w, 0.08 * s.h, size=f["small"], fill=f["muted"], anchor="end")
        s.slot(f"resp-{i+1}-body", f"RESP_{i+1}_BODY", s.X(0.65) + 6, s.Y(v + 0.07), 0.35 * s.w - 6, (rh - 0.07) * s.h)
    s.card("situation-bg", ["situation-title", "situation-body"])
    for i in range(1, 4):
        s.card(f"issue-{i}-box", [f"issue-{i}-title", f"issue-{i}-body"])
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f["label"] * 0.35, "제안 범위", fill=f["accent"])
    s.slot("scope", "SCOPE", s.X(0.12), s.Y(0.89), 0.87 * s.w, 0.11 * s.h, valign="middle")


def s66(s: Svg):
    """차별화 기둥: 고객 가치 지붕 + 기둥 3개(근거 수치) + 기반."""
    f = s.f
    s.path("roof", f"M {r1(s.X(0))} {r1(s.Y(0.16))} L {r1(s.X(0.5))} {r1(s.Y(0))} L {r1(s.X(1))} {r1(s.Y(0.16))} Z", f["dark"])
    s.slot("value-prop", "VALUE_PROP", s.X(0.2), s.Y(0.065), 0.6 * s.w, 0.09 * s.h, size=f["label"], weight=700, fill="#FFFFFF", anchor="middle", valign="middle")
    gap = 0.03
    pw = (1 - 2 * gap) / 3
    for i in range(3):
        u = i * (pw + gap)
        s.rect(f"pillar-{i+1}-head", s.X(u), s.Y(0.19), pw * s.w, 0.09 * s.h, f["accent"])
        s.slot(f"pillar-{i+1}-title", f"PILLAR_{i+1}_TITLE", s.X(u), s.Y(0.19), pw * s.w, 0.09 * s.h, size=f["label"], weight=700, fill="#FFFFFF", anchor="middle", valign="middle")
        s.rect(f"pillar-{i+1}-body-bg", s.X(u), s.Y(0.28), pw * s.w, 0.36 * s.h, "#FFFFFF", stroke=f["line"])
        s.slot(f"pillar-{i+1}-body", f"PILLAR_{i+1}_BODY", s.X(u), s.Y(0.28), pw * s.w, 0.36 * s.h)
        s.rect(f"proof-{i+1}-bg", s.X(u), s.Y(0.64), pw * s.w, 0.2 * s.h, f["zebra"])
        s.label(f"proof-{i+1}-tag", s.X(u) + 8, s.Y(0.64) + f["small"] + 6, "근거", size=f["small"], fill=f["muted"])
        s.slot(f"proof-{i+1}-num", f"PROOF_{i+1}_NUM", s.X(u), s.Y(0.665), pw * s.w, 0.09 * s.h, size=f["big"], weight=700, fill=f["accent"], anchor="middle", valign="middle")
        s.slot(f"proof-{i+1}-label", f"PROOF_{i+1}_LABEL", s.X(u), s.Y(0.755), pw * s.w, 0.08 * s.h, anchor="middle", valign="middle")
        s.card(f"proof-{i+1}-bg", [f"proof-{i+1}-tag", f"proof-{i+1}-num", f"proof-{i+1}-label"], gap=3, padding=3)
        s.card(f"pillar-{i+1}-body-bg", [f"pillar-{i+1}-body"])
    s.rect("foundation", s.X(0), s.Y(0.87), s.w, 0.13 * s.h, f["strip"])
    s.label("foundation-label", s.X(0) + 10, s.Y(0.935) + f["label"] * 0.35, "공통 기반", fill=f["accent"])
    s.slot("foundation-body", "FOUNDATION", s.X(0.12), s.Y(0.87), 0.87 * s.w, 0.13 * s.h, valign="middle")


def _table(s: Svg, cols, heads, rows, top=0.0, bottom=0.86, head_h=0.085, badge=True, prefix=("ROW",), zebra=True):
    """Generic header + rows table. cols: list of (u, w); returns row geometry list."""
    f = s.f
    s.rect("head-bg", s.X(0), s.Y(top), s.w, head_h * s.h, f["dark"])
    for i, ((u, w), name) in enumerate(zip(cols, heads), 1):
        if name:
            s.label(f"head-{i}", s.X(u + w / 2), s.Y(top + head_h / 2) + f["label"] * 0.35, name, fill="#FFFFFF", anchor="middle")
    rh = (bottom - top - head_h) / rows
    geo = []
    for r in range(rows):
        v = top + head_h + r * rh
        if zebra and r % 2 == 1:
            s.rect(f"row-{r+1}-zebra", s.X(0), s.Y(v), s.w, rh * s.h, f["zebra"])
        s.line(f"row-{r+1}-rule", s.X(0), s.Y(v + rh), s.X(1), s.Y(v + rh))
        if badge:
            s.circle(f"row-{r+1}-badge", s.X(cols[0][0] + cols[0][1] / 2), s.Y(v + rh / 2), 9, f["dark"])
            s.label(f"row-{r+1}-no", s.X(cols[0][0] + cols[0][1] / 2), s.Y(v + rh / 2) + f["small"] * 0.35, str(r + 1), size=f["small"], fill="#FFFFFF", anchor="middle")
        geo.append((v, rh))
    for i, (u, w) in enumerate(cols[1:], 1):
        s.line(f"col-{i}-rule", s.X(u), s.Y(top + head_h), s.X(u), s.Y(bottom))
    return geo


def s67(s: Svg):
    """제안요청서 요구사항 대응표 (compliance matrix)."""
    f = s.f
    cols = [(0, 0.05), (0.05, 0.31), (0.36, 0.40), (0.76, 0.13), (0.89, 0.11)]
    geo = _table(s, cols, ["No", "요구사항(제안요청서)", "이너젠 대응 방안", "반영 위치", "충족"], 6)
    for r, (v, rh) in enumerate(geo, 1):
        s.slot(f"req-{r}", f"REQ_{r}", s.X(0.05), s.Y(v), 0.31 * s.w, rh * s.h, weight=700, fill=f["dark"], valign="middle")
        s.slot(f"resp-{r}", f"RESP_{r}", s.X(0.36), s.Y(v), 0.40 * s.w, rh * s.h, valign="middle")
        s.slot(f"loc-{r}", f"LOC_{r}", s.X(0.76), s.Y(v), 0.13 * s.w, rh * s.h, fill=f["muted"], anchor="middle", valign="middle")
        s.slot(f"fit-{r}", f"FIT_{r}", s.X(0.89), s.Y(v), 0.11 * s.w, rh * s.h, weight=700, fill=f["accent"], anchor="middle", valign="middle")
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f["strip"])
    s.label("legend", s.X(1) - 8, s.Y(0.945) + f["small"] * 0.35, "충족 ● · 부분 충족 ◐ · 대안 제시 ○", size=f["small"], fill=f["muted"], weight=400, anchor="end")
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f["label"] * 0.35, "요약", fill=f["accent"])
    s.slot("summary", "SUMMARY", s.X(0.07), s.Y(0.89), 0.62 * s.w, 0.11 * s.h, valign="middle")


def s68(s: Svg):
    """가설 검증 현황 (interim hypothesis tracker)."""
    f = s.f
    cols = [(0, 0.05), (0.05, 0.25), (0.30, 0.20), (0.50, 0.25), (0.75, 0.10), (0.85, 0.15)]
    geo = _table(s, cols, ["No", "가설", "검증 분석", "결과·근거", "판정", "다음 단계"], 5)
    for r, (v, rh) in enumerate(geo, 1):
        s.slot(f"hypo-{r}", f"HYPO_{r}", s.X(0.05), s.Y(v), 0.25 * s.w, rh * s.h, weight=700, fill=f["dark"], valign="middle")
        s.slot(f"analysis-{r}", f"ANALYSIS_{r}", s.X(0.30), s.Y(v), 0.20 * s.w, rh * s.h, valign="middle")
        s.slot(f"evidence-{r}", f"EVIDENCE_{r}", s.X(0.50), s.Y(v), 0.25 * s.w, rh * s.h, valign="middle")
        pw, ph = 0.08 * s.w, min(26, rh * s.h * 0.6)
        px, py = s.X(0.80) - pw / 2, s.Y(v + rh / 2) - ph / 2
        s.rect(f"verdict-{r}-pill", px, py, pw, ph, f["strip"], stroke=f["tint"], rx=ph / 2)
        s.slot(f"verdict-{r}", f"VERDICT_{r}", px, py, pw, ph, weight=700, fill=f["accent"], anchor="middle", valign="middle", pad=0)
        s.slot(f"next-{r}", f"NEXT_{r}", s.X(0.85), s.Y(v), 0.15 * s.w, rh * s.h, fill=f["muted"], valign="middle")
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f["label"] * 0.35, "중간 결론", fill=f["accent"])
    s.label("legend", s.X(1) - 8, s.Y(0.945) + f["small"] * 0.35, "판정: 확인 · 수정 · 기각 · 검증 중", size=f["small"], fill=f["muted"], weight=400, anchor="end")
    s.slot("interim-conclusion", "INTERIM_CONCLUSION", s.X(0.1), s.Y(0.89), 0.62 * s.w, 0.11 * s.h, valign="middle")


def s69(s: Svg):
    """이슈·리스크 로그: 영향×가능성 3×3 + 로그 표 (PMO, interim)."""
    f = s.f
    mx, mw = 0.0, 0.27
    s.label("matrix-title", s.X(0), s.Y(0) + f["label"], "영향 × 가능성", fill=f["dark"])
    gx0, gy0 = s.X(0.05), s.Y(0.08)
    gw, gh = (mw - 0.05) * s.w, 0.66 * s.h
    shades = [[f["strip"], f["tint"], f["accent2"]], [f["zebra"], f["strip"], f["tint"]], ["#FFFFFF", f["zebra"], f["strip"]]]
    for r in range(3):
        for c in range(3):
            s.rect(f"cell-{r+1}-{c+1}", gx0 + c * gw / 3, gy0 + r * gh / 3, gw / 3, gh / 3, shades[r][c], stroke="#FFFFFF")
    s.label("axis-y", s.X(0.02), gy0 + gh / 2, "영향", size=f["small"], fill=f["muted"], weight=400, anchor="middle")
    s.label("axis-y-hi", gx0 - 4, gy0 + f["small"], "높음", size=f["small"], fill=f["muted"], weight=400, anchor="end")
    s.label("axis-x", gx0 + gw / 2, gy0 + gh + f["small"] * 2.4, "발생 가능성 →", size=f["small"], fill=f["muted"], weight=400, anchor="middle")
    pos = [(2, 0), (1, 1), (2, 1), (0, 2), (1, 2)]
    for i, (c, r) in enumerate(pos, 1):
        cx, cy = gx0 + (c + 0.5) * gw / 3, gy0 + (r + 0.5) * gh / 3
        s.circle(f"marker-{i}", cx, cy, 11, f["dark"])
        s.label(f"marker-{i}-id", cx, cy + f["small"] * 0.35, f"R{i}", size=f["small"], fill="#FFFFFF", anchor="middle")
    s.slot("matrix-note", "MATRIX_NOTE", s.X(0), s.Y(0.8), mw * s.w, 0.09 * s.h, size=f["small"], fill=f["muted"])
    # log table on the right
    t0 = 0.30
    cols = [(t0, 0.05), (t0 + 0.05, 0.20), (t0 + 0.25, 0.07), (t0 + 0.32, 0.18), (t0 + 0.50, 0.08), (t0 + 0.58, 0.06), (t0 + 0.64, 0.06)]
    f2 = s.f
    s.rect("head-bg", s.X(t0), s.Y(0), (1 - t0) * s.w, 0.085 * s.h, f2["dark"])
    for i, ((u, w), name) in enumerate(zip(cols, ["ID", "이슈·리스크", "영향", "대응", "담당", "기한", "상태"]), 1):
        s.label(f"head-{i}", s.X(u + w / 2), s.Y(0.0425) + f2["label"] * 0.35, name, fill="#FFFFFF", anchor="middle")
    rows, top, bottom = 5, 0.085, 0.86
    rh = (bottom - top) / rows
    for r in range(rows):
        v = top + r * rh
        if r % 2:
            s.rect(f"row-{r+1}-zebra", s.X(t0), s.Y(v), (1 - t0) * s.w, rh * s.h, f2["zebra"])
        s.line(f"row-{r+1}-rule", s.X(t0), s.Y(v + rh), s.X(1), s.Y(v + rh))
        s.label(f"row-{r+1}-id", s.X(t0 + 0.025), s.Y(v + rh / 2) + f2["cell"] * 0.35, f"R{r+1}", size=f2["cell"], anchor="middle")
        s.slot(f"risk-{r+1}", f"RISK_{r+1}", s.X(t0 + 0.05), s.Y(v), 0.20 * s.w, rh * s.h, weight=700, fill=f2["dark"], valign="middle")
        s.slot(f"impact-{r+1}", f"IMPACT_{r+1}", s.X(t0 + 0.25), s.Y(v), 0.07 * s.w, rh * s.h, anchor="middle", valign="middle")
        s.slot(f"action-{r+1}", f"ACTION_{r+1}", s.X(t0 + 0.32), s.Y(v), 0.18 * s.w, rh * s.h, valign="middle")
        s.slot(f"owner-{r+1}", f"OWNER_{r+1}", s.X(t0 + 0.50), s.Y(v), 0.08 * s.w, rh * s.h, anchor="middle", valign="middle")
        s.slot(f"due-{r+1}", f"DUE_{r+1}", s.X(t0 + 0.58), s.Y(v), 0.06 * s.w, rh * s.h, weight=700, fill=f2["accent"], anchor="middle", valign="middle")
        s.slot(f"state-{r+1}", f"STATE_{r+1}", s.X(t0 + 0.64), s.Y(v), 0.06 * s.w, rh * s.h, fill=f2["muted"], anchor="middle", valign="middle")
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f2["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f2["label"] * 0.35, "결정·지원 필요", fill=f2["accent"])
    s.slot("escalation", "ESCALATION", s.X(0.16), s.Y(0.89), 0.83 * s.w, 0.11 * s.h, valign="middle")


def s70(s: Svg):
    """피라미드 요약: 핵심 메시지 → 핵심 근거 3 → 뒷받침 3×3 (Minto)."""
    f = s.f
    s.rect("main-bg", s.X(0.12), s.Y(0), 0.76 * s.w, 0.13 * s.h, f["dark"])
    s.slot("main-point", "MAIN_POINT", s.X(0.12), s.Y(0), 0.76 * s.w, 0.13 * s.h, size=f["label"], weight=700, fill="#FFFFFF", anchor="middle", valign="middle")
    gap = 0.03
    kw = (1 - 2 * gap) / 3
    bus = 0.19
    s.line("stem", s.X(0.5), s.Y(0.13), s.X(0.5), s.Y(bus), color=f["conn"], width=1.5)
    s.line("bus", s.X(kw / 2), s.Y(bus), s.X(1 - kw / 2), s.Y(bus), color=f["conn"], width=1.5)
    for i in range(3):
        u = i * (kw + gap)
        s.line(f"drop-{i+1}", s.X(u + kw / 2), s.Y(bus), s.X(u + kw / 2), s.Y(0.23), color=f["conn"], width=1.5)
        s.rect(f"key-{i+1}-bg", s.X(u), s.Y(0.23), kw * s.w, 0.17 * s.h, f["strip"])
        s.rect(f"key-{i+1}-bar", s.X(u), s.Y(0.23), kw * s.w, 3, f["accent"])
        s.slot(f"key-{i+1}-title", f"KEY_{i+1}_TITLE", s.X(u), s.Y(0.235), kw * s.w, 0.07 * s.h, size=f["label"], weight=700, fill=f["accent"])
        s.slot(f"key-{i+1}-body", f"KEY_{i+1}_BODY", s.X(u), s.Y(0.30), kw * s.w, 0.10 * s.h)
        s.card(f"key-{i+1}-bg", [f"key-{i+1}-title", f"key-{i+1}-body"], gap=4, padding=5)
        for j in range(3):
            v = 0.43 + j * 0.15
            s.rect(f"support-{i+1}-{j+1}-bar", s.X(u), s.Y(v), 3, 0.12 * s.h, f["tint"])
            s.rect(f"support-{i+1}-{j+1}-bg", s.X(u) + 3, s.Y(v), kw * s.w - 3, 0.12 * s.h, f["zebra"])
            s.slot(f"support-{i+1}-{j+1}", f"SUPPORT_{i+1}_{j+1}", s.X(u) + 3, s.Y(v), kw * s.w - 3, 0.12 * s.h, valign="middle")
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f["label"] * 0.35, "다음 행동", fill=f["accent"])
    s.slot("next-action", "NEXT_ACTION", s.X(0.12), s.Y(0.89), 0.87 * s.w, 0.11 * s.h, valign="middle")


def s71(s: Svg):
    """진단 결과 × 개선 과제 연계 매트릭스."""
    f = s.f
    lw = 0.30
    n, m = 5, 5
    cw = (1 - lw) / m
    head_h, top, bottom = 0.14, 0.0, 0.78
    s.rect("corner", s.X(0), s.Y(top), lw * s.w, head_h * s.h, f["strip"])
    s.label("corner-label", s.X(0) + 8, s.Y(top + head_h / 2) + f["label"] * 0.35, "진단 결과 \\ 개선 과제", fill=f["dark"])
    for c in range(m):
        u = lw + c * cw
        s.rect(f"init-{c+1}-bg", s.X(u) + 1, s.Y(top), cw * s.w - 2, head_h * s.h, f["dark"])
        s.slot(f"init-{c+1}", f"INIT_{c+1}", s.X(u) + 1, s.Y(top), cw * s.w - 2, head_h * s.h, weight=700, fill="#FFFFFF", anchor="middle", pad=6)
    rh = (bottom - head_h) / n
    for r in range(n):
        v = head_h + r * rh
        s.rect(f"finding-{r+1}-bg", s.X(0), s.Y(v) + 1, lw * s.w, rh * s.h - 2, f["zebra"])
        s.slot(f"finding-{r+1}", f"FINDING_{r+1}", s.X(0), s.Y(v), lw * s.w, rh * s.h, weight=700, fill=f["dark"], valign="middle")
        s.line(f"row-{r+1}-rule", s.X(lw), s.Y(v + rh), s.X(1), s.Y(v + rh))
        for c in range(m):
            u = lw + c * cw
            s.slot(f"mark-{r+1}-{c+1}", f"MARK_{r+1}_{c+1}", s.X(u), s.Y(v), cw * s.w, rh * s.h, size=f["big"], fill=f["accent"], anchor="middle", valign="middle", pad=0)
    for c in range(1, m):
        s.line(f"col-{c}-rule", s.X(lw + c * cw), s.Y(head_h), s.X(lw + c * cw), s.Y(bottom))
    s.rect("priority-bg", s.X(0), s.Y(0.79), s.w, 0.08 * s.h, f["strip"])
    s.label("priority-label", s.X(0) + 8, s.Y(0.83) + f["label"] * 0.35, "우선순위·시기", fill=f["accent"])
    for c in range(m):
        u = lw + c * cw
        s.slot(f"priority-{c+1}", f"PRIORITY_{c+1}", s.X(u), s.Y(0.79), cw * s.w, 0.08 * s.h, weight=700, fill=f["accent"], anchor="middle", valign="middle", pad=0)
    s.label("legend", s.X(1), s.Y(0.92) + f["small"] * 0.35, "● 직접 해결 · ◐ 일부 기여 · 빈칸 무관", size=f["small"], fill=f["muted"], weight=400, anchor="end")
    s.slot("map-note", "MAP_NOTE", s.X(0), s.Y(0.89), 0.6 * s.w, 0.11 * s.h, valign="middle", pad=0)


def s72(s: Svg):
    """과제 정의서 (initiative charter one-pager)."""
    f = s.f
    s.rect("charter-head", s.X(0), s.Y(0), s.w, 0.1 * s.h, f["dark"])
    s.slot("charter-id", "CHARTER_ID", s.X(0), s.Y(0), 0.08 * s.w, 0.1 * s.h, weight=700, fill=f["tint"], anchor="middle", valign="middle")
    s.slot("charter-name", "CHARTER_NAME", s.X(0.08), s.Y(0), 0.62 * s.w, 0.1 * s.h, size=f["label"], weight=700, fill="#FFFFFF", valign="middle")
    s.slot("charter-owner", "OWNER", s.X(0.70), s.Y(0), 0.30 * s.w, 0.1 * s.h, fill="#FFFFFF", anchor="end", valign="middle")
    boxes_l = [("objective", "목표", "OBJECTIVE", 0.12, 0.22), ("scope", "범위(포함·제외)", "SCOPE", 0.36, 0.22), ("risk", "리스크·의존성", "RISK", 0.60, 0.25)]
    for id_, name, tok, v, h in boxes_l:
        s.rect(f"{id_}-bg", s.X(0), s.Y(v), 0.48 * s.w, h * s.h, "#FFFFFF", stroke=f["line"])
        s.rect(f"{id_}-bar", s.X(0), s.Y(v), 3, h * s.h, f["accent"])
        s.label(f"{id_}-label", s.X(0) + 10, s.Y(v) + f["label"] + 6, name, fill=f["accent"])
        s.slot(id_, tok, s.X(0) + 4, s.Y(v + 0.055), 0.48 * s.w - 4, (h - 0.055) * s.h)
        s.card(f"{id_}-bg", [f"{id_}-label", id_], gap=6, padding=8)
    # KPI mini table
    u0 = 0.50
    s.label("kpi-label", s.X(u0) + 2, s.Y(0.12) + f["label"] + 6, "KPI", fill=f["accent"])
    s.rect("kpi-head", s.X(u0), s.Y(0.18), 0.5 * s.w, 0.06 * s.h, f["strip"])
    for i, (u, w, name) in enumerate([(0, 0.24, "지표"), (0.24, 0.13, "기준값"), (0.37, 0.13, "목표값")], 1):
        s.label(f"kpi-head-{i}", s.X(u0 + u + w / 2), s.Y(0.21) + f["small"] * 0.35, name, size=f["small"], fill=f["dark"], anchor="middle")
    for r in range(3):
        v = 0.24 + r * 0.065
        s.line(f"kpi-{r+1}-rule", s.X(u0), s.Y(v + 0.065), s.X(1), s.Y(v + 0.065))
        s.slot(f"kpi-{r+1}-name", f"KPI_{r+1}_NAME", s.X(u0), s.Y(v), 0.24 * s.w, 0.065 * s.h, valign="middle")
        s.slot(f"kpi-{r+1}-base", f"KPI_{r+1}_BASE", s.X(u0 + 0.24), s.Y(v), 0.13 * s.w, 0.065 * s.h, anchor="middle", valign="middle")
        s.slot(f"kpi-{r+1}-target", f"KPI_{r+1}_TARGET", s.X(u0 + 0.37), s.Y(v), 0.13 * s.w, 0.065 * s.h, weight=700, fill=f["accent"], anchor="middle", valign="middle")
    # milestones
    s.label("ms-label", s.X(u0) + 2, s.Y(0.47) + f["label"] + 6, "마일스톤", fill=f["accent"])
    ly = s.Y(0.62)
    s.line("ms-line", s.X(u0 + 0.02), ly, s.X(0.98), ly, color=f["conn"], width=2)
    for i in range(4):
        cx = s.X(u0 + 0.06 + i * 0.12)
        s.path(f"ms-{i+1}-diamond", f"M {r1(cx)} {r1(ly-8)} L {r1(cx+8)} {r1(ly)} L {r1(cx)} {r1(ly+8)} L {r1(cx-8)} {r1(ly)} Z", f["accent"] if i == 0 else f["dark"])
        s.slot(f"ms-{i+1}-date", f"MS_{i+1}_DATE", cx - 0.06 * s.w, s.Y(0.53), 0.12 * s.w, 0.05 * s.h, weight=700, fill=f["dark"], anchor="middle", valign="middle", pad=0)
        s.slot(f"ms-{i+1}-name", f"MS_{i+1}_NAME", cx - 0.06 * s.w, s.Y(0.645), 0.12 * s.w, 0.1 * s.h, anchor="middle", pad=2)
    s.rect("resource-bg", s.X(u0), s.Y(0.76), 0.5 * s.w, 0.09 * s.h, f["zebra"])
    s.label("resource-label", s.X(u0) + 8, s.Y(0.805) + f["label"] * 0.35, "필요 자원", fill=f["dark"])
    s.slot("resource", "RESOURCE", s.X(u0 + 0.11), s.Y(0.76), 0.39 * s.w, 0.09 * s.h, valign="middle")
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f["label"] * 0.35, "기대 효과", fill=f["accent"])
    s.slot("benefit", "BENEFIT", s.X(0.12), s.Y(0.89), 0.87 * s.w, 0.11 * s.h, valign="middle")


def s73(s: Svg):
    """웨이브 실행 로드맵: 워크스트림 4 × 웨이브 3 + 마일스톤."""
    f = s.f
    lw = 0.16
    ww = (1 - lw) / 3
    hh = 0.12
    fills = [f["accent"], f["dark"], f["dark"]]
    for c in range(3):
        u = lw + c * ww
        x0, x1 = s.X(u), s.X(u + ww) - 4
        y0, y1 = s.Y(0), s.Y(hh)
        tip = 12
        notch = tip if c else 0
        s.path(f"wave-{c+1}-chevron", f"M {r1(x0)} {r1(y0)} L {r1(x1-tip)} {r1(y0)} L {r1(x1)} {r1((y0+y1)/2)} L {r1(x1-tip)} {r1(y1)} L {r1(x0)} {r1(y1)} L {r1(x0+notch)} {r1((y0+y1)/2)} Z", fills[c])
        s.slot(f"wave-{c+1}-name", f"WAVE_{c+1}_NAME", x0 + notch, y0, (x1 - x0) - notch - tip, (y1 - y0) * 0.55, weight=700, fill="#FFFFFF", anchor="middle", valign="middle", pad=0)
        s.slot(f"wave-{c+1}-period", f"WAVE_{c+1}_PERIOD", x0 + notch, y0 + (y1 - y0) * 0.5, (x1 - x0) - notch - tip, (y1 - y0) * 0.45, size=f["small"], fill=f["tint"] if c else "#FFFFFF", anchor="middle", valign="middle", pad=0)
    s.label("quick-win-tag", s.X(lw) + 4, s.Y(hh) + f["small"] + 4, "Quick win", size=f["small"], fill=f["accent"])
    rows, top, bottom = 4, hh + 0.05, 0.76
    rh = (bottom - top) / rows
    for r in range(rows):
        v = top + r * rh
        s.rect(f"ws-{r+1}-bg", s.X(0), s.Y(v) + 2, lw * s.w - 6, rh * s.h - 4, f["zebra"])
        s.slot(f"ws-{r+1}", f"WS_{r+1}", s.X(0), s.Y(v), lw * s.w - 6, rh * s.h, weight=700, fill=f["dark"], valign="middle")
        s.line(f"row-{r+1}-rule", s.X(lw), s.Y(v + rh), s.X(1), s.Y(v + rh))
        for c in range(3):
            u = lw + c * ww
            bx, by, bw, bh = s.X(u) + 4, s.Y(v) + 6, ww * s.w - 12, rh * s.h - 12
            s.rect(f"act-{r+1}-{c+1}-bar", bx, by, bw, bh, f["strip"] if c else f["zebra"], stroke=f["tint"], rx=3)
            s.slot(f"act-{r+1}-{c+1}", f"ACT_{r+1}_{c+1}", bx, by, bw, bh, valign="middle")
    ly = s.Y(0.82)
    s.label("ms-label", s.X(0) + 4, ly + f["label"] * 0.35, "마일스톤", fill=f["accent"])
    s.line("ms-line", s.X(lw), ly, s.X(1), ly, color=f["conn"], width=2)
    for c in range(3):
        cx = s.X(lw + (c + 1) * ww) - 14
        s.path(f"ms-{c+1}-diamond", f"M {r1(cx)} {r1(ly-8)} L {r1(cx+8)} {r1(ly)} L {r1(cx)} {r1(ly+8)} L {r1(cx-8)} {r1(ly)} Z", f["accent"])
        s.slot(f"mile-{c+1}", f"MILE_{c+1}", s.X(lw + c * ww), ly + 10, ww * s.w - 20, 0.08 * s.h, anchor="end", pad=2)
    s.rect("end-strip", s.X(0), s.Y(0.92), s.w, 0.08 * s.h, f["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.96) + f["label"] * 0.35, "선행 조건", fill=f["accent"])
    s.slot("prerequisite", "PREREQUISITE", s.X(0.12), s.Y(0.92), 0.87 * s.w, 0.08 * s.h, valign="middle")


def s74(s: Svg):
    """투자·효과 비즈니스 케이스: 연도별 투자(−)·효과(+) 막대 + 누적선 + 회수 시점 + 핵심 지표."""
    f = s.f
    cw = 0.64
    s.slot("axis-y", "AXIS_Y", s.X(0), s.Y(0), 0.3 * s.w, 0.06 * s.h, size=f["small"], fill=f["muted"], pad=0)
    lx = s.X(cw) - 4
    s.rect("legend-ben", lx - 210, s.Y(0.02), 10, 10, f["accent"])
    s.label("legend-ben-t", lx - 196, s.Y(0.02) + 10, "효과", size=f["small"], fill=f["muted"], weight=400)
    s.rect("legend-inv", lx - 150, s.Y(0.02), 10, 10, f["dark"])
    s.label("legend-inv-t", lx - 136, s.Y(0.02) + 10, "투자", size=f["small"], fill=f["muted"], weight=400)
    s.line("legend-cum", lx - 90, s.Y(0.02) + 5, lx - 70, s.Y(0.02) + 5, color=f["accent2"], width=2)
    s.label("legend-cum-t", lx - 66, s.Y(0.02) + 10, "누적 순효과", size=f["small"], fill=f["muted"], weight=400)
    ch0, ch1 = 0.08, 0.83
    zero = 0.50
    s.line("zero-axis", s.X(0.03), s.Y(zero), s.X(cw), s.Y(zero), color=f["conn"], width=1)
    n = 6
    step = (cw - 0.05) / n
    # example proportions (예시): investment and benefit per year, same unit; bars are slide-local shapes
    inv = [250, 140, 30, 0, 0, 0]
    ben = [0, 60, 140, 210, 250, 270]
    k = 0.38 / 750  # value -> fraction of content height (one scale for bars and the cumulative line)
    cum, acc = [], 0.0
    for i in range(n):
        acc += ben[i] - inv[i]
        cum.append(acc)
    pts = []
    for i in range(n):
        cx = s.X(0.05 + (i + 0.5) * step)
        bw = step * s.w * 0.32
        hb, hi = ben[i] * k * s.h, inv[i] * k * s.h
        if hb:
            s.rect(f"ben-{i+1}-bar", cx - bw - 1, s.Y(zero) - hb, bw, hb, f["accent"])
        if hi:
            s.rect(f"inv-{i+1}-bar", cx + 1, s.Y(zero), bw, hi, f["dark"])
        s.slot(f"ben-{i+1}", f"BEN_{i+1}", cx - bw * 1.6, s.Y(zero) - hb - 18, bw * 1.6, 16, size=f["small"], fill=f["accent"], anchor="middle", valign="middle", pad=0)
        s.slot(f"inv-{i+1}", f"INV_{i+1}", cx, s.Y(zero) + hi + 2, bw * 1.6, 16, size=f["small"], fill=f["dark"], anchor="middle", valign="middle", pad=0)
        s.slot(f"year-{i+1}", f"YEAR_{i+1}", cx - step * s.w / 2, s.Y(ch1), step * s.w, 0.05 * s.h, anchor="middle", valign="middle", pad=0)
        pts.append((cx, s.Y(zero) - cum[i] * k * s.h))
    d = "M " + " L ".join(f"{r1(x)} {r1(y)}" for x, y in pts)
    s.path("cum-line", d, "none", stroke=f["accent2"], width=2)
    for i, (x, y) in enumerate(pts, 1):
        s.circle(f"cum-{i}-dot", x, y, 3.5, "#FFFFFF", stroke=f["accent2"])
    px = s.X(0.05 + 3.54 * step)
    s.line("payback-line", px, s.Y(ch0), px, s.Y(ch1) - 4, color=f["accent"], width=1.5, dash="4 3")
    s.slot("payback", "PAYBACK", px + 4, s.Y(ch0), 0.16 * s.w, 0.06 * s.h, size=f["small"], weight=700, fill=f["accent"], pad=0)
    # KPI panel
    u0 = cw + 0.03
    pw = 1 - u0
    for i in range(3):
        v = i * 0.2
        s.rect(f"kpi-{i+1}-bg", s.X(u0), s.Y(v), pw * s.w, 0.18 * s.h, f["zebra"])
        s.rect(f"kpi-{i+1}-bar", s.X(u0), s.Y(v), 3, 0.18 * s.h, f["accent"])
        s.slot(f"kpi-{i+1}-value", f"KPI_{i+1}_VALUE", s.X(u0) + 4, s.Y(v), pw * s.w - 4, 0.11 * s.h, size=f["big"], weight=700, fill=f["accent"], valign="middle")
        s.slot(f"kpi-{i+1}-label", f"KPI_{i+1}_LABEL", s.X(u0) + 4, s.Y(v + 0.1), pw * s.w - 4, 0.08 * s.h, fill=f["dark"], valign="middle")
        s.card(f"kpi-{i+1}-bg", [f"kpi-{i+1}-value", f"kpi-{i+1}-label"], gap=4, padding=5)
    s.rect("assume-bg", s.X(u0), s.Y(0.61), pw * s.w, 0.25 * s.h, "#FFFFFF", stroke=f["line"])
    s.label("assume-label", s.X(u0) + 8, s.Y(0.61) + f["label"] + 6, "주요 가정", fill=f["dark"])
    s.slot("assumptions", "ASSUMPTIONS", s.X(u0), s.Y(0.66), pw * s.w, 0.2 * s.h)
    s.card("assume-bg", ["assume-label", "assumptions"], gap=6, padding=8)
    s.rect("end-strip", s.X(0), s.Y(0.89), s.w, 0.11 * s.h, f["strip"])
    s.label("end-label", s.X(0) + 10, s.Y(0.945) + f["label"] * 0.35, "판단", fill=f["accent"])
    s.slot("verdict", "VERDICT", s.X(0.08), s.Y(0.89), 0.91 * s.w, 0.11 * s.h, valign="middle")


LAYOUTS = [
    ("s65_proposal_understanding", "proposal-understanding", "과업 이해(고객 상황·핵심 쟁점·대응 방향)", s65),
    ("s66_why_us_pillars", "why-us-pillars", "차별화 기둥(고객 가치·기둥 3·근거 수치)", s66),
    ("s67_rfp_compliance", "rfp-compliance", "제안요청서 요구사항 대응표", s67),
    ("s68_hypothesis_tracker", "hypothesis-tracker", "가설 검증 현황(판정·다음 단계)", s68),
    ("s69_issue_risk_log", "issue-risk-log", "이슈·리스크 로그(영향×가능성+대응표)", s69),
    ("s70_pyramid_summary", "pyramid-summary", "피라미드 요약(핵심 메시지·근거 3·뒷받침)", s70),
    ("s71_findings_initiatives", "findings-initiatives", "진단 결과×개선 과제 연계 매트릭스", s71),
    ("s72_initiative_charter", "initiative-charter", "과제 정의서(목표·KPI·마일스톤·리스크)", s72),
    ("s73_wave_roadmap", "wave-roadmap", "웨이브 실행 로드맵(워크스트림×웨이브)", s73),
    ("s74_business_case", "business-case", "투자·효과 비즈니스 케이스(누적·회수 시점)", s74),
]


def chrome_of(svg: str) -> tuple[list[str], tuple[int, int]]:
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    keep = [ln for ln in svg.splitlines() if re.match(r'<(?:rect|line|image|g|text) id="(%s)"' % "|".join(map(re.escape, CHROME_IDS)), ln)]
    return keep, (int(vb.group(1)), int(vb.group(2)))


def build(skill: Path, out: Path | None, update_json: bool) -> dict:
    result = {}
    for fam_id, fam in FAMILIES.items():
        jpath = skill / "templates" / "decks" / f"{fam_id}.json"
        texts = json.loads(jpath.read_text(encoding="utf-8"))
        chrome, canvas = chrome_of(texts["templates/s44_hypothesis_workplan.svg"])
        made = []
        for fname, lid, lname, fn in LAYOUTS:
            s = Svg(fam, chrome)
            fn(s)
            svg = s.render(lid, lname, canvas)
            texts[f"templates/{fname}.svg"] = svg
            made.append((fname, lid, lname, s.tokens))
            if out:
                (out / fam_id).mkdir(parents=True, exist_ok=True)
                (out / fam_id / f"{fname}.svg").write_text(svg, encoding="utf-8")
        spec = texts["templates/design_spec.md"]
        spec = update_design_spec(spec, fam, made)
        texts["templates/design_spec.md"] = spec
        if out:
            (out / fam_id / "design_spec.v30-rows.md").write_text(design_spec_rows(fam, made), encoding="utf-8")
        if update_json:
            # keep the file's own line endings (the PC build writes CRLF on Windows)
            nl = "\r\n" if b"\r\n" in jpath.read_bytes()[:200] else "\n"
            jpath.write_text(json.dumps(texts, ensure_ascii=False, indent=0) + "\n", encoding="utf-8", newline=nl)
        result[fam_id] = made
    return result


def design_spec_rows(fam, made) -> str:
    ph = "\n".join(f'  {fname}: [{", ".join(json.dumps("{{" + t + "}}", ensure_ascii=False) for t in (["PAGE_TITLE", "KEY_MESSAGE"] + toks)[:7])}]' for fname, _, _, toks in made)
    roster = "\n".join(f'| `{fname}.svg` | `{fam["prefix"]}-{lid}` / {fam["name"]} {lname} | 슬롯 {len(toks) + 4}개 |' for fname, lid, lname, toks in made)
    return f"<!-- placeholders: 프런트매터 placeholders 끝에 추가 -->\n{ph}\n\n<!-- V. Page Roster 표 끝에 추가 -->\n{roster}\n\n<!-- I. Template Overview 목록에 추가 -->\n{V30_BULLET}\n"


V30_BULLET = ("- v30 보고서 도식 s65–s74(과업 이해·차별화 기둥·요구사항 대응표·가설 검증 현황·이슈·리스크 로그·피라미드 요약·"
              "진단-과제 연계·과제 정의서·웨이브 로드맵·비즈니스 케이스)은 제안서·중간보고·최종보고용이다. 리스크 표식·막대·누적선·마일스톤은 "
              "슬라이드 로컬 도형이라 값에 맞춰 고쳐 쓴다(`governing-body-v30.md` §4, `consulting-references-v30.md`).")


def update_design_spec(spec: str, fam, made) -> str:
    if "s65_proposal_understanding" in spec:
        return spec
    ph = "\n".join(f'  {fname}: [{", ".join(json.dumps("{{" + t + "}}", ensure_ascii=False) for t in (["PAGE_TITLE", "KEY_MESSAGE"] + toks)[:7])}]' for fname, _, _, toks in made)
    spec = re.sub(r"(\n  s\d{2}_[a-z_]+: \[[^\n]*\])(\n---)", lambda m: m.group(1) + "\n" + ph + m.group(2), spec, count=1)
    spec = re.sub(r"^page_count: (\d+)$", lambda m: f"page_count: {int(m.group(1)) + len(made)}", spec, count=1, flags=re.M)
    roster = "\n".join(f'| `{fname}.svg` | `{fam["prefix"]}-{lid}` / {fam["name"]} {lname} | 슬롯 {len(toks) + 4}개 |' for fname, lid, lname, toks in made)
    spec = re.sub(r"(\n\| `s\d{2}_[a-z_]+\.svg` \|[^\n]*)(\n\n## VI\.)", lambda m: m.group(1) + "\n" + roster + m.group(2), spec, count=1)
    spec = re.sub(r"(\n- 세부 규칙: )", "\n" + V30_BULLET + r"\1", spec, count=1)
    return spec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--update-json", action="store_true")
    args = ap.parse_args(argv)
    res = build(args.skill, args.out, args.update_json)
    for fam, made in res.items():
        print(f"[v30] {fam}: {len(made)} layouts, slots {sum(len(t) for *_, t in made)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
