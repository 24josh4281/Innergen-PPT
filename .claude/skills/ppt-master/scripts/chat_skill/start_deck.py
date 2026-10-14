#!/usr/bin/env python3
"""
INNerGEN Deck (chat skill) - Project Scaffold

Creates a deck project for the standalone innergen-deck skill: copies the
family's base spec_lock.md, brand images and SVG layout templates, and makes the
svg_output/ folder the page SVGs are written into. Bundled into the claude.ai
chat skill by build_chat_skill.py; it is not used by the repository pipeline.

Usage:
    python3 scripts/start_deck.py --family <family> --out <project_dir>

Examples:
    python3 scripts/start_deck.py --family innergen_lecture --out /tmp/deck
    python3 scripts/start_deck.py --family innergen_business --out /tmp/kickoff --force

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parent.parent
LOCKS_DIR = SKILL_DIR / "locks"
DECKS_DIR = SKILL_DIR / "templates" / "decks"

# Flat export (pptx_structure: flat) rejects the templates' Master/Layout metadata
# and instead expects one root data-pptx-page-role per page.
_STRUCTURE_ATTR_RE = re.compile(r"""\s+data-pptx-[\w-]+=(?:"[^"]*"|'[^']*')""")
_SVG_ROOT_RE = re.compile(r"<svg\b")
PAGE_ROLES = (("01_cover", "cover"), ("02c_", "section"), ("02", "toc"), ("04_ending", "ending"))

FAMILIES = {
    "innergen_lecture": "이너젠 교육·강의(블루) 13:9 · Pretendard",
    "innergen_business": "이너젠 회사소개·컨설팅 보고 16:9 · IBM Plex Sans KR",
    "innercarry": "이너캐리 제품 소개 4:3 · IBM Plex Sans KR",
}


def page_role(layout_name: str) -> str:
    for prefix, role in PAGE_ROLES:
        if layout_name.startswith(prefix):
            return role
    return "content"


def flatten_template(svg: str, layout_name: str) -> str:
    """Drop data-pptx-* Master/Layout/placeholder attributes and declare the
    flat route's root page role (cover/toc/section/content/ending)."""
    svg = _STRUCTURE_ATTR_RE.sub("", svg)
    role = f'<svg data-pptx-page-role="{page_role(layout_name)}"'
    return _SVG_ROOT_RE.sub(role, svg, count=1)


def scaffold(family: str, out: Path, force: bool) -> None:
    if out.exists() and any(out.iterdir()):
        if not force:
            raise SystemExit(f"{out} is not empty — pass --force to rebuild it")
        shutil.rmtree(out)
    deck = DECKS_DIR / family
    (out / "svg_output").mkdir(parents=True)
    (out / "analysis").mkdir()
    (out / "exports").mkdir()
    shutil.copytree(deck / "images", out / "images")
    (out / "templates").mkdir()
    for src in (deck / "templates").iterdir():
        dst = out / "templates" / src.name
        if src.suffix == ".svg":
            dst.write_text(flatten_template(src.read_text(encoding="utf-8"), src.stem),
                           encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dst)
    shutil.copy2(LOCKS_DIR / f"{family}.md", out / "spec_lock.md")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scaffold an INNerGEN deck project.")
    parser.add_argument("--family", required=True, choices=sorted(FAMILIES))
    parser.add_argument("--out", required=True, type=Path, help="project directory to create")
    parser.add_argument("--force", action="store_true", help="replace a non-empty project directory")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    out = args.out.resolve()
    scaffold(args.family, out, args.force)
    layouts = sorted(p.stem for p in (out / "templates").glob("*.svg"))
    print(f"[start_deck] {args.family} — {FAMILIES[args.family]}")
    print(f"[start_deck] project: {out}")
    print(f"[start_deck] write pages to {out / 'svg_output'} as NN_<name>.svg")
    print(f"[start_deck] layouts ({len(layouts)}): {', '.join(layouts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
