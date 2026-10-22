"""Explicit SVG card stacks, shared by preview and native PPTX conversion.

A rect declares data-card-members="title number body" in vertical order.
Members are plain <text> or a single uniform-text placeholder <g>. Slot bounds
are retained as data-card-slot-bounds when start_deck strips PPTX metadata.
No inference from overlapping shapes, no font shrinking, no source overwrites.
"""
from __future__ import annotations
import argparse
import math
import re
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET

SVG = "http://www.w3.org/2000/svg"


class CardLayoutError(ValueError):
    pass


def _number(value):
    value = float(value)
    if not math.isfinite(value):
        raise CardLayoutError("card geometry must be finite")
    return value


def _advance(char):
    if unicodedata.combining(char):
        return 0
    if char.isspace():
        return .35
    if unicodedata.east_asian_width(char) in ("W", "F"):
        return 1
    return .95 if char in "MWmw@#%" else .65


def wrap_text(text, width, size):
    capacity = width / (size * 1.08)
    lines = []
    for paragraph in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = ""
        for word in paragraph.split():
            if sum(map(_advance, word)) > capacity:
                raise CardLayoutError(f"word exceeds card width: {word!r}; widen card or insert a line break")
            candidate = f"{line} {word}" if line else word
            if line and sum(map(_advance, candidate)) > capacity:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    return lines


def _text_content(text):
    if not len(text):
        return text.text or ""
    # Only uniform line tspans: rich inline styles require their own measurement.
    if (text.text or "").strip() or any(c.tag != f"{{{SVG}}}tspan" or len(c) or
            set(c.attrib) - {"x", "y", "dy"} or (c.tail or "").strip() for c in text):
        raise CardLayoutError("card members support uniform line tspans only")
    return "\n".join(c.text or "" for c in text)


def apply_card_layout(root):
    """Plan all cards atomically; return geometry reports. Unmarked SVGs unchanged."""
    cards = [e for e in root.iter() if e.get("data-card-members") is not None]
    if not cards:
        return []
    ids = {}
    parents = {child: parent for parent in root.iter() for child in parent}
    for elem in root.iter():
        if elem.get("id"):
            if elem.get("id") in ids:
                raise CardLayoutError(f"duplicate id: {elem.get('id')}")
            ids[elem.get("id")] = elem
    used, plans, reports = set(), [], []
    for card in cards:
        name = card.get("id", "card")
        try:
            if card.tag != f"{{{SVG}}}rect":
                raise CardLayoutError("container must be a rect")
            cx, cy, cw, ch = [_number(card.get(a, 0)) for a in ("x", "y", "width", "height")]
            pad = _number(card.get("data-card-padding", 8))
            gap = _number(card.get("data-card-gap", 6))
            if pad < 0 or gap < 0 or cw <= 2 * pad or ch <= 2 * pad:
                raise CardLayoutError("invalid card dimensions, gap or padding")
            members = card.get("data-card-members").split()
            if not members or len(set(members)) != len(members) or used.intersection(members):
                raise CardLayoutError("empty or repeated card membership")
            used.update(members)
            pending, unresolved = [], False
            for member_id in members:
                member = ids.get(member_id)
                if member is None:
                    raise CardLayoutError(f"missing member {member_id}")
                # Reject transforms rather than mixing SVG coordinate systems.
                for node in (card, member):
                    while node is not None:
                        if node.get("transform"):
                            raise CardLayoutError("transformed cards require coordinates to be materialized first")
                        node = parents.get(node)
                texts = [e for e in member.iter() if e.tag == f"{{{SVG}}}text"]
                if len(texts) != 1:
                    raise CardLayoutError(f"{member_id} must contain one editable text object")
                text = texts[0]
                content = _text_content(text)
                unresolved |= bool(re.search(r"\{\{[^}]+\}\}", content))
                if not content.strip():
                    continue
                size = _number(text.get("font-size", 12))
                if size <= 0:
                    raise CardLayoutError("font size must be positive")
                raw = text.get("data-card-slot-bounds") or member.get("data-card-slot-bounds") or member.get("data-pptx-placeholder-bounds")
                if raw:
                    x, _, w, _ = map(_number, raw.split())
                    # Respect the template's horizontal column; clamp to padding.
                    left, right = max(x, cx + pad), min(x + w, cx + cw - pad)
                else:
                    left, right = cx + pad, cx + cw - pad
                if right <= left:
                    raise CardLayoutError(f"{member_id} has no width inside container")
                lines = wrap_text(content, right - left, size) if not unresolved else [content]
                # Native converter normally reserves 1.5em + padding. Explicit card
                # frames below reserve 1.5em per line with no extra hidden slack.
                height = len(lines) * size * 1.5
                pending.append((member, text, left, right - left, size, lines, height))
            if unresolved:
                continue  # token templates stay byte-for-byte unchanged until filled
            gaps = [_number(p[1].get("data-card-gap-after", gap)) for p in pending]
            if any(value < 0 for value in gaps):
                raise CardLayoutError("member gaps must be nonnegative")
            total = sum(p[-1] for p in pending) + sum(gaps[:-1])
            if total > ch - 2 * pad + .001:
                raise CardLayoutError(f"content height {total:.2f} > available {ch - 2 * pad:.2f}; enlarge card or split content")
            top = cy + (ch - total) / 2
            placed = []
            for member, text, x, width, size, lines, height in pending:
                plans.append((member, text, x, top, width, height, size, lines))
                placed.append(dict(id=member.get("id"), x=x, y=top, w=width, h=height))
                top += height + _number(text.get("data-card-gap-after", gap))
            reports.append(dict(card=name, top=(ch-total)/2, bottom=(ch-total)/2, gap=gap, members=placed))
        except (ValueError, TypeError) as exc:
            raise CardLayoutError(f"{name}: {exc}") from exc
    for member, text, x, y, w, h, size, lines in plans:
        bounds = f"{x:.4f} {y:.4f} {w:.4f} {h:.4f}"
        # Keep reusable placeholder bounds unchanged; only the slide text frame moves.
        text.set("data-card-frame", bounds)
        text.set("data-paragraph-line-height", str(size * 1.5))
        text.set("data-pptx-preserve-line-breaks", "true")
        text.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        anchor = text.get("text-anchor", "start")
        tx = x + (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
        text.set("x", f"{tx:.4f}")
        text.set("y", f"{y + size * .85:.4f}")
        for child in list(text):
            text.remove(child)
        text.text = lines[0] if len(lines) == 1 else None
        if len(lines) > 1:
            for i, line in enumerate(lines):
                span = ET.SubElement(text, f"{{{SVG}}}tspan", {"x": f"{tx:.4f}", "dy": str(size * 1.5 if i else 0)})
                span.text = line or "\u00a0"
    return reports


def layout_svg(svg):
    root = ET.fromstring(svg)
    if not any(e.get("data-card-members") for e in root.iter()):
        return svg
    if not apply_card_layout(root):
        return svg
    ET.register_namespace("", SVG)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    return ET.tostring(root, encoding="unicode")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("choose a separate output to preserve the source")
    args.output.write_text(layout_svg(args.source.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
