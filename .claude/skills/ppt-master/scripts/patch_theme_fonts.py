#!/usr/bin/env python3
"""
PPT Master - PPTX Theme Font Patcher

Sets the major and minor theme fonts (latin, ea, cs and the CJK script entries)
of a finished PPTX. Flat exports keep the baseline theme (Calibri / Malgun Gothic),
so text newly typed in PowerPoint would otherwise fall back to Malgun Gothic.

Usage:
    python3 scripts/patch_theme_fonts.py <deck.pptx> [--font "IBM Plex Sans KR"]

Examples:
    python3 .claude/skills/ppt-master/scripts/patch_theme_fonts.py exports/deck.pptx

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Optional

DEFAULT_FONT = "IBM Plex Sans KR"
_THEME_PART = re.compile(r"ppt/theme/theme\d+\.xml$")
_FONT_BLOCK = re.compile(r"<a:(majorFont|minorFont)>.*?</a:\1>", re.S)
_FACE = re.compile(r'<a:(latin|ea|cs) typeface="[^"]*"')
_CJK_SCRIPT = re.compile(r'<a:font script="(Hang|Jpan|Hans|Hant)" typeface="[^"]*"')


def patch_theme_xml(xml: str, font: str) -> str:
    """Return theme XML with every major/minor face set to font."""

    def fix(block: re.Match[str]) -> str:
        text = _FACE.sub(lambda m: f'<a:{m.group(1)} typeface="{font}"', block.group(0))
        return _CJK_SCRIPT.sub(lambda m: f'<a:font script="{m.group(1)}" typeface="{font}"', text)

    return _FONT_BLOCK.sub(fix, xml)


def patch_pptx(pptx: Path, font: str) -> int:
    """Rewrite pptx in place and return the number of theme parts changed."""
    tmp = pptx.with_suffix(".tmp.pptx")
    changed = 0
    with zipfile.ZipFile(pptx) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if _THEME_PART.match(item.filename):
                data = patch_theme_xml(data.decode("utf-8"), font).encode("utf-8")
                changed += 1
            zout.writestr(item, data)
    shutil.move(str(tmp), str(pptx))
    return changed


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Set the theme fonts of a finished PPTX.")
    parser.add_argument("pptx", type=Path, help="PPTX file to rewrite in place")
    parser.add_argument("--font", default=DEFAULT_FONT, help=f"theme font family (default: {DEFAULT_FONT})")
    args = parser.parse_args(argv)
    if not args.pptx.is_file():
        print(f"Error: file not found: {args.pptx}", file=sys.stderr)
        return 1
    print(f"{args.pptx.name}: {patch_pptx(args.pptx, args.font)} theme part(s) -> {args.font}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
