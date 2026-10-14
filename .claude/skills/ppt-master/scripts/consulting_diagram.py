#!/usr/bin/env python3
"""
PPT Master - Consulting Diagram Geometry

Recomputes the data-driven slide-local shapes of the INNerGEN v24 consulting
layouts (s47 waterfall, s48 MACC, s49 pathway wedge, s50 materiality,
s51 risk heatmap, s53 Harvey balls, s55 stakeholder map, s57 nine-box) from
source numbers, so bar heights, widths, wedges and dot positions are
proportional instead of hand-drawn. The plot frame is read from the slide's
own fixed layout shapes (axes, plot background, grid cells); only the
family palette and text size come from the INNerGEN family table.

The tool rewrites only the slide-local elements named in the layout contract
(bars, links, badges, dots, wedges, Harvey fills) and moves value/price label
carriers. Placeholder bounds, layout shapes and filled text stay untouched.
It also checks the numbers behind the picture: a bridge must reconcile to its
end value, MACC levers must be sorted by cost, wedge shares must sum to 100%.

Usage:
    python3 scripts/consulting_diagram.py kinds
    python3 scripts/consulting_diagram.py example <kind>
    python3 scripts/consulting_diagram.py apply <slide.svg> <data.json> [-o out.svg]
    python3 scripts/consulting_diagram.py check <slide.svg> <data.json>

Examples:
    python3 scripts/consulting_diagram.py example waterfall_bridge > bridge.json
    python3 scripts/consulting_diagram.py apply projects/demo/svg_output/07_bridge.svg bridge.json

Dependencies:
    None (only uses standard library)
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402


# Family table mirrors the v24 template generator (body box, cell text size, palette).
FAMILIES = {
    'innergen-biz-': dict(
        body=(24, 94, 912, 392), s_cell=10.67,
        font='"IBM Plex Sans KR", "Malgun Gothic", sans-serif',
        NAVY='#2B4C7E', BLUE='#518FFF', LIGHT='#8FB3FF', NEUTRAL='#A6A6A6',
        MID='#B9CFFF', GOVS='#D9E7FD', WHITE='#FFFFFF'),
    'innercarry-': dict(
        body=(56, 156, 912, 460), s_cell=10.67,
        font='"IBM Plex Sans KR", "Malgun Gothic", sans-serif',
        NAVY='#0B1739', BLUE='#2F62F0', LIGHT='#7B9BF7', NEUTRAL='#94A3B8',
        MID='#B8CBF9', GOVS='#DFE7FF', WHITE='#FFFFFF'),
    'innergen-intro-': dict(
        body=(48, 120, 944, 484), s_cell=12,
        font='Pretendard, "Malgun Gothic", sans-serif',
        NAVY='#0B1739', BLUE='#2F62F0', LIGHT='#7B9BF7', NEUTRAL='#94A3B8',
        MID='#B8CBF9', GOVS='#DFE7FF', WHITE='#FFFFFF'),
}

EXAMPLES = {
    'waterfall_bridge': {
        'kind': 'waterfall_bridge', 'unit': 'tCO2e',
        'start': 100, 'deltas': [-18, -12, -9, 6, -15], 'end': 52},
    'macc_curve': {
        'kind': 'macc_curve', 'price': 30,
        'levers': [{'abatement': 16, 'cost': -42}, {'abatement': 12, 'cost': -25},
                   {'abatement': 10, 'cost': -10}, {'abatement': 18, 'cost': 12},
                   {'abatement': 14, 'cost': 25}, {'abatement': 17, 'cost': 42},
                   {'abatement': 13, 'cost': 70}]},
    'pathway_wedge': {
        'kind': 'pathway_wedge',
        'bau': [100, 108, 118], 'target': [100, 55, 10], 'shares': [0.35, 0.28, 0.22, 0.15]},
    'materiality_matrix': {
        'kind': 'materiality_matrix', 'max': 5, 'threshold': 3,
        'topics': [{'impact': 4.6, 'financial': 4.4}, {'impact': 3.9, 'financial': 4.1},
                   {'impact': 3.4, 'financial': 4.7}, {'impact': 4.2, 'financial': 3.5},
                   {'impact': 3.6, 'financial': 2.1}, {'impact': 1.8, 'financial': 4.0},
                   {'impact': 2.0, 'financial': 2.4}, {'impact': 1.0, 'financial': 1.2}]},
    'risk_heatmap': {
        'kind': 'risk_heatmap',
        'risks': [{'likelihood': 4, 'impact': 5}, {'likelihood': 4, 'impact': 4},
                  {'likelihood': 3, 'impact': 4}, {'likelihood': 5, 'impact': 2},
                  {'likelihood': 2, 'impact': 3}, {'likelihood': 3, 'impact': 1}]},
    'harvey_compare': {
        'kind': 'harvey_compare',
        'scores': [[4, 3, 2, 1], [3, 4, 1, 2], [2, 2, 4, 3], [4, 1, 3, 2], [1, 3, 2, 4]]},
    'stakeholder_map': {
        'kind': 'stakeholder_map', 'max': 5,
        'stakeholders': [{'influence': 4.5, 'interest': 4.2}, {'influence': 3.5, 'interest': 3.3},
                         {'influence': 4.0, 'interest': 1.5}, {'influence': 1.9, 'interest': 4.4},
                         {'influence': 1.1, 'interest': 2.9}, {'influence': 1.5, 'interest': 1.0}]},
    'nine_box': {
        'kind': 'nine_box',
        'units': [{'competitiveness': 2.9, 'attractiveness': 3.0, 'size': 120},
                  {'competitiveness': 2.2, 'attractiveness': 2.6, 'size': 60},
                  {'competitiveness': 3.1, 'attractiveness': 1.9, 'size': 75},
                  {'competitiveness': 1.4, 'attractiveness': 2.2, 'size': 30},
                  {'competitiveness': 1.9, 'attractiveness': 1.3, 'size': 90},
                  {'competitiveness': 1.0, 'attractiveness': 1.0, 'size': 20}]},
}

COUNTS = {'waterfall_bridge': 5, 'macc_curve': 7, 'pathway_wedge': 4, 'materiality_matrix': 8,
          'risk_heatmap': 6, 'harvey_compare': (5, 4), 'stakeholder_map': 6, 'nine_box': 6}


class DiagramError(ValueError):
    """Source numbers that cannot be drawn honestly on this layout."""


def fmt(v: float) -> str:
    v = round(v, 1)
    return str(int(v)) if v == int(v) else str(v)


class Slide:
    """Id-addressed edits on one SVG document, preserving all other markup."""

    def __init__(self, text: str):
        self.text = text
        self.nl = '\r\n' if '\r\n' in text else '\n'
        self.log: list[str] = []
        root = re.search(r'<svg\b[^>]*>', text)
        if not root:
            raise DiagramError('No <svg> root element.')
        master = re.search(r'data-pptx-master="([^"]+)"', root.group(0))
        layout = re.search(r'data-pptx-layout="([^"]+)"', root.group(0))
        self.layout = layout.group(1) if layout else ''
        prefix = next((p for p in FAMILIES if master and master.group(1).startswith(p)), None)
        if prefix is None:
            raise DiagramError('Not an INNerGEN v24 layout slide (unknown data-pptx-master).')
        self.f = FAMILIES[prefix]

    def _pattern(self, tag: str, id_: str) -> re.Pattern:
        if tag == 'text':
            return re.compile(rf'<text\b[^>]*\bid="{re.escape(id_)}"[^>]*>.*?</text>', re.DOTALL)
        return re.compile(rf'<{tag}\b[^>]*\bid="{re.escape(id_)}"[^>]*?/>', re.DOTALL)

    def attrs(self, tag: str, id_: str) -> dict:
        m = self._pattern(tag, id_).search(self.text)
        if not m:
            raise DiagramError(f'Frame shape <{tag} id="{id_}"> not found; is this the right layout?')
        head = m.group(0).split('>', 1)[0]
        return {k: v for k, v in re.findall(r'([\w:-]+)="([^"]*)"', head)}

    def put(self, tag: str, id_: str, markup: str, after: str | None = None) -> None:
        pat = self._pattern(tag, id_)
        if pat.search(self.text):
            self.text = pat.sub(lambda _m: markup, self.text, count=1)
            return
        anchor = after and re.search(rf'<\w+\b[^>]*\bid="{re.escape(after)}"[^>]*?(/>|>.*?</\w+>)',
                                     self.text, re.DOTALL)
        if not anchor:
            raise DiagramError(f'Slide-local element id="{id_}" is missing and has no anchor.')
        self.text = self.text[:anchor.end()] + self.nl + markup + self.text[anchor.end():]

    def drop(self, tag: str, id_: str) -> None:
        self.text = re.sub(rf'(\r?\n)?{self._pattern(tag, id_).pattern}', '', self.text, count=1, flags=re.DOTALL)

    def move_carrier(self, id_: str, y: float) -> None:
        pat = re.compile(rf'(<text\b[^>]*\bid="{re.escape(id_)}-carrier"[^>]*?\by=")[^"]*(")')
        if pat.search(self.text):
            self.text = pat.sub(lambda m: m.group(1) + fmt(y) + m.group(2), self.text, count=1)
        else:
            self.log.append(f'note: label carrier {id_}-carrier not found; label left in place')

    # Shape markup, matching the generator's attribute order.
    def rect(self, id_, x, y, w, h, fill):
        return (f'<rect id="{id_}" x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" '
                f'height="{fmt(h)}" fill="{fill}"/>')

    def line(self, id_, x1, y1, x2, y2, stroke, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        return (f'<line id="{id_}" x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" '
                f'stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def circle(self, id_, cx, cy, r, fill, stroke=None, sw=1):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        return f'<circle id="{id_}" cx="{fmt(cx)}" cy="{fmt(cy)}" r="{fmt(r)}" fill="{fill}"{s}/>'

    def path(self, id_, d, fill='none', stroke=None, sw=1, dash=None):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
        s += f' stroke-dasharray="{dash}"' if dash else ''
        return f'<path id="{id_}" d="{d}" fill="{fill}"{s}/>'

    def label(self, id_, cx, cy, s, fill, anchor='middle', baseline=False):
        f = self.f
        y = cy if baseline else cy + 0.36 * f['s_cell']
        return (f'<text id="{id_}" x="{fmt(cx)}" y="{fmt(y)}" text-anchor="{anchor}" '
                f"font-family='{f['font']}' font-size=\"{f['s_cell']}\" font-weight=\"700\" "
                f'fill="{fill}">{s}</text>')

    def badge(self, id_, cx, cy, r, s, fill, text_fill=None, stroke=None):
        self.put('circle', id_, self.circle(id_, cx, cy, r, fill, stroke, 1.5 if stroke else 1))
        self.put('text', id_ + '-no', self.label(id_ + '-no', cx, cy, s, text_fill or self.f['WHITE']))


def poly(points) -> str:
    return 'M ' + ' L '.join(f'{fmt(x)} {fmt(y)}' for x, y in points) + 'Z'


def need(data: dict, key: str, count, kind: str) -> list:
    rows = data.get(key)
    if not isinstance(rows, list) or len(rows) != count:
        raise DiagramError(f'{kind}: "{key}" needs exactly {count} entries (layout slot count).')
    return rows


def numbers(rows: list, keys: tuple, kind: str) -> list[tuple]:
    out = []
    for i, row in enumerate(rows, 1):
        try:
            out.append(tuple(float(row[k]) for k in keys))
        except (KeyError, TypeError, ValueError):
            raise DiagramError(f'{kind}: entry {i} needs numeric {", ".join(keys)}.') from None
    return out


def spread(cx: float, cy: float, n: int, gap: float) -> list[tuple]:
    """Offsets for n markers sharing one cell: rows of up to three."""
    cols = min(n, 3)
    rows = math.ceil(n / 3)
    pts = []
    for j in range(n):
        r_, c_ = divmod(j, 3)
        in_row = min(cols, n - r_ * 3)
        pts.append((cx + (c_ - (in_row - 1) / 2) * gap, cy + (r_ - (rows - 1) / 2) * gap))
    return pts


# --------------------------------------------------------------------------- kinds

def waterfall_bridge(s: Slide, d: dict) -> None:
    f = s.f
    bx, by, bw_, bh = f['body']
    deltas = [float(v) for v in need(d, 'deltas', COUNTS['waterfall_bridge'], 'waterfall_bridge')]
    start = float(d['start'])
    end = start + sum(deltas)
    if 'end' in d and abs(float(d['end']) - end) > max(1e-6, abs(end) * 0.005):
        raise DiagramError(f'waterfall_bridge: start {fmt(start)} + Σdeltas {fmt(sum(deltas))} = '
                           f'{fmt(end)}, not the stated end {fmt(float(d["end"]))}. Reconcile the source.')
    run, peak = start, start
    for v in deltas:
        run += v
        if run < 0:
            raise DiagramError('waterfall_bridge: running total below zero is not supported on this layout.')
        peak = max(peak, run)
    if peak <= 0:
        raise DiagramError('waterfall_bridge: start and running totals must be positive.')
    ax = s.attrs('line', 'axis-x')
    base, left, right = float(ax['y1']), float(ax['x1']), float(ax['x2'])
    top = by + 0.1 * bh
    scale = (base - top) / (peak * 1.1)
    vals = [start] + deltas + [end]
    slot = (right - left) / len(vals)
    bw = slot * 0.6
    run = 0.0
    for i, v in enumerate(vals):
        k = i + 1
        x = left + i * slot + (slot - bw) / 2
        if i == 0 or i == len(vals) - 1:
            total = v if i == 0 else run
            y, h, fill = base - total * scale, total * scale, f['NAVY']
            run = total
        elif v < 0:
            y, h, fill = base - run * scale, -v * scale, f['BLUE']
            run += v
        else:
            y, h, fill = base - (run + v) * scale, v * scale, f['NEUTRAL']
            run += v
        s.put('rect', f'bar-{k}', s.rect(f'bar-{k}', x, y, bw, max(h, 1), fill))
        if i < len(vals) - 1:
            lvl = base - run * scale
            s.put('line', f'link-{k}', s.line(f'link-{k}', x + bw, lvl, x + slot, lvl, f['NEUTRAL'], dash='3 2'))
        s.move_carrier(f'val-{k}', y - 0.035 * bh + 0.36 * f['s_cell'])
    s.log.append(f'bridge: {fmt(start)} {" ".join(f"{v:+g}" for v in deltas)} = {fmt(end)} (peak {fmt(peak)})')


def macc_curve(s: Slide, d: dict) -> None:
    f = s.f
    bx, by, bw_, bh = f['body']
    levers = numbers(need(d, 'levers', COUNTS['macc_curve'], 'macc_curve'), ('abatement', 'cost'), 'macc_curve')
    costs = [c for _, c in levers]
    if costs != sorted(costs):
        raise DiagramError('macc_curve: levers must be ordered by ascending cost (MACC rule); '
                           'reorder LEVER_1..7 and their rows to match.')
    if any(a <= 0 for a, _ in levers):
        raise DiagramError('macc_curve: every abatement must be positive.')
    price = d.get('price')
    zero_ax = s.attrs('line', 'axis-zero')
    zero, left, right = float(zero_ax['y1']), float(zero_ax['x1']), float(zero_ax['x2'])
    pos_room = zero - (by + 0.06 * bh) - 22
    neg_room = (by + 0.91 * bh) - zero - 22
    max_pos = max([c for c in costs if c > 0] + ([float(price)] if price is not None else []) + [0])
    max_neg = max([-c for c in costs if c < 0] + [0])
    k = min(pos_room / max_pos if max_pos else math.inf, neg_room / max_neg if max_neg else math.inf)
    span = right - left - 4
    total = sum(a for a, _ in levers)
    x = left + 2
    for i, (a, c) in enumerate(levers):
        n = i + 1
        w = a / total * span
        h = max(abs(c) * k, 1.5)
        y = zero if c < 0 else zero - h
        fill = f['LIGHT'] if c < 0 else (f['NAVY'] if price is not None and c > float(price) else f['BLUE'])
        s.put('rect', f'bar-{n}', s.rect(f'bar-{n}', x, y, w - 1.5, h, fill))
        badge_y = (y + h + 12) if c < 0 else (y - 12)
        s.badge(f'bar-{n}-badge', x + (w - 1.5) / 2, badge_y, 8.5, str(n), f['NAVY'])
        x += w
    if price is not None:
        py = zero - float(price) * k
        s.put('line', 'price-line', s.line('price-line', left, py, right, py, f['BLUE'], 1.5, '5 3'))
        s.move_carrier('price-label', py - 0.035 * bh + 0.36 * f['s_cell'])
    s.log.append(f'macc: total abatement {fmt(total)}, cost range {fmt(costs[0])}..{fmt(costs[-1])}'
                 + (f', price {fmt(float(price))}' if price is not None else ', no price line moved'))


def pathway_wedge(s: Slide, d: dict) -> None:
    f = s.f
    bau = [float(v) for v in need(d, 'bau', 3, 'pathway_wedge')]
    tgt = [float(v) for v in need(d, 'target', 3, 'pathway_wedge')]
    shares = [float(v) for v in need(d, 'shares', COUNTS['pathway_wedge'], 'pathway_wedge')]
    if any(t > b + 1e-9 for t, b in zip(tgt, bau)) or min(tgt) < 0:
        raise DiagramError('pathway_wedge: target must stay between 0 and BAU at every year.')
    if any(v < 0 for v in shares) or abs(sum(shares) - 1) > 0.005:
        raise DiagramError(f'pathway_wedge: lever shares sum to {sum(shares):.3f}; they must total 1.0 '
                           '(the gap between BAU and target).')
    ax, ay = s.attrs('line', 'axis-x'), s.attrs('line', 'axis-y')
    base, left, right, top = float(ax['y1']), float(ax['x1']), float(ax['x2']), float(ay['y1'])
    xs = [left, left + (right - left) * 0.42, right]
    vmax = max(bau + tgt) * 1.06
    V = lambda v: base - v * (base - top) / vmax  # noqa: E731
    fills = [f['NAVY'], f['BLUE'], f['LIGHT'], f['MID']]
    lower = tgt[:]
    for i, (sh, c) in enumerate(zip(shares, fills)):
        upper = [lo + sh * (b - t) for lo, b, t in zip(lower, bau, tgt)]
        pts = [(xs[j], V(upper[j])) for j in range(3)] + [(xs[j], V(lower[j])) for j in (2, 1, 0)]
        s.put('path', f'wedge-{i + 1}', s.path(f'wedge-{i + 1}', poly(pts), c))
        lower = upper
    s.put('path', 'residual', s.path('residual', poly(
        [(xs[j], V(tgt[j])) for j in range(3)] + [(xs[2], base), (xs[0], base)]), f['GOVS']))
    line_d = lambda vals: 'M ' + ' L '.join(f'{fmt(xs[j])} {fmt(V(vals[j]))}' for j in range(3))  # noqa: E731
    s.put('path', 'bau-line', s.path('bau-line', line_d(bau), 'none', f['NEUTRAL'], 2, '5 3'))
    s.put('path', 'target-line', s.path('target-line', line_d(tgt), 'none', f['NAVY'], 2.5))
    s.put('text', 'bau-tag', s.label('bau-tag', right - 4, V(bau[2]) - 6, 'BAU', f['NEUTRAL'], 'end', True))
    gap = bau[2] - tgt[2]
    s.log.append(f'pathway: final-year gap {fmt(gap)} split '
                 + ' / '.join(f'{v:.0%}' for v in shares) + f', residual {fmt(tgt[2])}')


def _scatter_frame(s: Slide, plot_id: str) -> tuple[float, float, float]:
    if plot_id == 'plot-bg':
        a = s.attrs('rect', 'plot-bg')
        return float(a['x']), float(a['y']), float(a['width'])
    ax, ay = s.attrs('line', 'axis-x'), s.attrs('line', 'axis-y')
    return float(ay['x1']), float(ay['y1']), float(ax['x2']) - float(ax['x1'])


def _avoid(points: list[list[float]], r: float) -> int:
    """Nudge later dots right/left until no two badges overlap; returns nudges."""
    moved = 0
    for i in range(1, len(points)):
        for _ in range(6):
            hit = any(math.dist(points[i], points[j]) < 2 * r + 1 for j in range(i))
            if not hit:
                break
            points[i][0] += (2 * r + 2) * (1 if moved % 2 == 0 else -1)
            moved += 1
    return moved


def materiality_matrix(s: Slide, d: dict) -> None:
    f = s.f
    rows = numbers(need(d, 'topics', COUNTS['materiality_matrix'], 'materiality_matrix'),
                   ('impact', 'financial'), 'materiality_matrix')
    top = float(d.get('max', 5))
    thr = float(d.get('threshold', top / 2))
    if not 0 < thr < top or any(not 0 <= v <= top for row in rows for v in row):
        raise DiagramError('materiality_matrix: scores must sit in 0..max and 0 < threshold < max.')
    x0, y0, side = _scatter_frame(s, 'plot-bg')
    m = lambda v: v / thr * 0.5 if v <= thr else 0.5 + (v - thr) / (top - thr) * 0.5  # noqa: E731
    # Keep badges inside the plot and off the quadrant captions (top band 30px, bottom 22px).
    r, pad = 10, 12 / side
    lo, hi = 22 / side, 1 - 30 / side
    pts = [[x0 + min(max(m(fi), pad), 1 - pad) * side, y0 + (1 - min(max(m(im), lo), hi)) * side]
           for im, fi in rows]
    moved = _avoid(pts, r)
    hot = 0
    for i, ((im, fi), (cx, cy)) in enumerate(zip(rows, pts)):
        dual = im >= thr and fi >= thr
        hot += dual
        s.badge(f'dot-{i + 1}', cx, cy, r, str(i + 1), f['BLUE'] if dual else f['NEUTRAL'])
    s.log.append(f'materiality: threshold {fmt(thr)}/{fmt(top)} on the dashed midlines, '
                 f'{hot} double-material topics' + (f', {moved} overlap nudges' if moved else ''))


def risk_heatmap(s: Slide, d: dict) -> None:
    f = s.f
    rows = numbers(need(d, 'risks', COUNTS['risk_heatmap'], 'risk_heatmap'),
                   ('likelihood', 'impact'), 'risk_heatmap')
    if any(v != int(v) or not 1 <= v <= 5 for row in rows for v in row):
        raise DiagramError('risk_heatmap: likelihood and impact are integer grades 1..5.')
    cell = s.attrs('rect', 'cell-5-1')
    gx, gy, c = float(cell['x']), float(cell['y']), float(cell['width']) + 2
    groups: dict[tuple, list[int]] = {}
    for i, (lk, im) in enumerate(rows):
        groups.setdefault((int(lk), int(im)), []).append(i)
    for (lk, im), idx in groups.items():
        cx, cy = gx + (lk - 1) * c + c / 2 - 1, gy + (5 - im) * c + c / 2 - 1
        for i, (px, py) in zip(idx, spread(cx, cy, len(idx), min(22, (c - 4) / min(len(idx), 3)))):
            dark = lk * im >= 11
            s.put('circle', f'mark-{i + 1}', s.circle(
                f'mark-{i + 1}', px, py, 10, f['WHITE'] if dark else f['NAVY'], f['NAVY'] if dark else None, 1.5))
            s.put('text', f'mark-{i + 1}-no', s.label(f'mark-{i + 1}-no', px, py, str(i + 1),
                                                      f['NAVY'] if dark else f['WHITE']))
    shared = sum(len(v) for v in groups.values() if len(v) > 1)
    s.log.append(f'risk: {len(rows)} marks on the 5×5 grid' + (f', {shared} sharing cells' if shared else ''))


def harvey_compare(s: Slide, d: dict) -> None:
    f = s.f
    nrow, ncol = COUNTS['harvey_compare']
    scores = need(d, 'scores', nrow, 'harvey_compare')
    for k, row in enumerate(scores, 1):
        if not isinstance(row, list) or len(row) != ncol or any(q not in (0, 1, 2, 3, 4) for q in row):
            raise DiagramError(f'harvey_compare: row {k} needs {ncol} integer quarters 0..4.')
        for j, q in enumerate(row, 1):
            id_ = f'ball-{k}-{j}'
            ring = s.attrs('circle', id_ + '-ring')
            cx, cy, r = float(ring['cx']), float(ring['cy']), float(ring['r'])
            s.drop('circle', id_ + '-fill')
            s.drop('path', id_ + '-fill')
            if q == 4:
                s.put('circle', id_ + '-fill', s.circle(id_ + '-fill', cx, cy, r, f['NAVY']), after=id_ + '-ring')
            elif q > 0:
                a = math.radians(q * 90 - 90)
                ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
                arc = (f'M {fmt(cx)} {fmt(cy)} L {fmt(cx)} {fmt(cy - r)} A {fmt(r)} {fmt(r)} 0 '
                       f'{1 if q > 2 else 0} 1 {fmt(ex)} {fmt(ey)} Z')
                s.put('path', id_ + '-fill', s.path(id_ + '-fill', arc, f['NAVY']), after=id_ + '-ring')
    s.log.append(f'harvey: {nrow}×{ncol} balls redrawn; option sums '
                 + ' / '.join(str(sum(row[j] for row in scores)) for j in range(ncol)))


def stakeholder_map(s: Slide, d: dict) -> None:
    f = s.f
    rows = numbers(need(d, 'stakeholders', COUNTS['stakeholder_map'], 'stakeholder_map'),
                   ('influence', 'interest'), 'stakeholder_map')
    top = float(d.get('max', 5))
    if any(not 0 <= v <= top for row in rows for v in row):
        raise DiagramError('stakeholder_map: influence and interest must sit in 0..max.')
    x0, y0, side = _scatter_frame(s, 'axes')
    r, pad = 10, 12 / side
    clamp = lambda v: min(max(v / top, pad), 1 - pad)  # noqa: E731
    pts = [[x0 + clamp(it) * side, y0 + (1 - clamp(inf)) * side] for inf, it in rows]
    moved = _avoid(pts, r)
    for i, ((inf, it), (cx, cy)) in enumerate(zip(rows, pts)):
        key = inf > top / 2 and it > top / 2
        s.badge(f'dot-{i + 1}', cx, cy, r, str(i + 1), f['BLUE'] if key else f['NAVY'])
    s.log.append(f'stakeholders: midpoint {fmt(top / 2)} splits the quadrants'
                 + (f', {moved} overlap nudges' if moved else ''))


def nine_box(s: Slide, d: dict) -> None:
    f = s.f
    rows = numbers(need(d, 'units', COUNTS['nine_box'], 'nine_box'),
                   ('competitiveness', 'attractiveness', 'size'), 'nine_box')
    if any(not 0.5 <= v <= 3.5 for row in rows for v in row[:2]) or any(row[2] <= 0 for row in rows):
        raise DiagramError('nine_box: grades are 1..3 (0.5..3.5 continuous) and size must be positive.')
    cell = s.attrs('rect', 'cell-1-1')
    gx, gy, side = float(cell['x']), float(cell['y']), 3 * (float(cell['width']) + 2)
    biggest = max(row[2] for row in rows)
    for i, (cp, at, size) in enumerate(rows):
        r = 9 + 7 * math.sqrt(size / biggest)
        cx = min(max(gx + (cp - 0.5) / 3 * side, gx + r), gx + side - 2 - r)
        cy = min(max(gy + (1 - (at - 0.5) / 3) * side, gy + r), gy + side - 2 - r)
        s.put('circle', f'bubble-{i + 1}', s.circle(f'bubble-{i + 1}', cx, cy, r, f['NAVY'], f['WHITE'], 1.5))
        s.put('text', f'bubble-{i + 1}-no', s.label(f'bubble-{i + 1}-no', cx, cy, str(i + 1), f['WHITE']))
    s.log.append('nine-box: bubble radius grows with √size (9–16), grade 1 = column/row centre')


KINDS = {fn.__name__: fn for fn in (waterfall_bridge, macc_curve, pathway_wedge, materiality_matrix,
                                    risk_heatmap, harvey_compare, stakeholder_map, nine_box)}


def detect(slide: Slide, data: dict) -> str:
    kind = data.get('kind')
    if kind:
        if kind not in KINDS:
            raise DiagramError(f'Unknown kind "{kind}". Run: consulting_diagram.py kinds')
        return kind
    for name in KINDS:
        if slide.layout.endswith(name.replace('_', '-')):
            return name
    raise DiagramError(f'Cannot infer kind from layout "{slide.layout}"; add "kind" to the data.')


def run(svg_path: Path, data_path: Path, out: Path | None, write: bool) -> int:
    slide = Slide(svg_path.read_bytes().decode('utf-8'))  # keep the file's own line endings
    data = json.loads(data_path.read_text(encoding='utf-8'))
    kind = detect(slide, data)
    try:
        KINDS[kind](slide, data)
    except (KeyError, TypeError) as exc:
        raise DiagramError(f'{kind}: malformed data ({exc}). See: consulting_diagram.py example {kind}') from None
    for line in slide.log:
        print(line)
    if write:
        target = out or svg_path
        target.write_text(slide.text, encoding='utf-8', newline='')
        print(f'{kind}: wrote {target}')
    else:
        print(f'{kind}: PASS (no file written)')
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description='Recompute INNerGEN v24 consulting diagram shapes from data.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('kinds', help='List supported layouts.')
    ex = sub.add_parser('example', help='Print a sample data file.')
    ex.add_argument('kind', choices=sorted(KINDS))
    for name in ('apply', 'check'):
        p = sub.add_parser(name, help='Rewrite the slide shapes.' if name == 'apply' else 'Validate only.')
        p.add_argument('svg', type=Path)
        p.add_argument('data', type=Path)
        if name == 'apply':
            p.add_argument('-o', '--output', type=Path, help='Write here instead of in place.')
    args = parser.parse_args(argv)
    if args.command == 'kinds':
        for name in KINDS:
            print(f'{name:20} {json.dumps(COUNTS[name])} entries')
        return 0
    if args.command == 'example':
        print(json.dumps(EXAMPLES[args.kind], ensure_ascii=False, indent=2))
        return 0
    try:
        return run(args.svg, args.data, getattr(args, 'output', None), args.command == 'apply')
    except DiagramError as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
