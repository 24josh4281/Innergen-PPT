#!/usr/bin/env python3
"""
INNerGEN Deck (chat skill) - Project Scaffold

Creates a deck project for the standalone innergen-deck skill: copies the
family's base spec_lock.md, brand images and SVG layout templates, and makes the
svg_output/ folder the page SVGs are written into. claude.ai caps a skill at 200
files and rejects nested ZIPs, so each family ships as templates/decks/<family>.json
(layout SVG text) plus <family>_images/; both are read in place, so the skill
folder may be read-only. Bundled into the claude.ai
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
import json
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
    "innergen_lecture": "이너젠 뉴 · 교육/강의 (13:9) · Pretendard",
    "innergen_business": "이너젠 뉴 · 사업/회사 소개 (16:9) · IBM Plex Sans KR",
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


def deck_files(family: str):
    """Yield (relative path, bytes) for the family's images/ and templates/ files."""
    folder = DECKS_DIR / family
    if folder.is_dir():
        for path in sorted(folder.rglob("*")):
            rel = path.relative_to(folder)
            if path.is_file() and rel.parts[0] in ("images", "templates"):
                yield rel.as_posix(), path.read_bytes()
        return
    texts = json.loads((DECKS_DIR / f"{family}.json").read_text(encoding="utf-8"))
    for rel, text in texts.items():
        yield rel, text.encode("utf-8")
    for path in sorted((DECKS_DIR / f"{family}_images").iterdir()):
        yield f"images/{path.name}", path.read_bytes()


def scaffold(family: str, out: Path, force: bool) -> None:
    if out.exists() and any(out.iterdir()):
        if not force:
            raise SystemExit(f"{out} is not empty — pass --force to rebuild it")
        shutil.rmtree(out)
    for sub in ("svg_output", "analysis", "exports", "images", "templates"):
        (out / sub).mkdir(parents=True)
    for rel, data in deck_files(family):
        dst = out / rel
        if dst.suffix == ".svg":
            dst.write_text(flatten_template(data.decode("utf-8"), dst.stem),
                           encoding="utf-8", newline="\n")
        else:
            dst.write_bytes(data)
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
