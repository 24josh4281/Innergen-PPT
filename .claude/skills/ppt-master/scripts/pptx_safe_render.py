#!/usr/bin/env python3
"""
PowerPoint-exact slide render that never closes the user's PowerPoint.

OfficeCLI's native render quits the PowerPoint it drives, and its HTML engine
can move line wraps by about one character. This renders through PowerPoint
itself (exact wraps) via pptx_safe_render.ps1: a temp copy opens read-only and
windowless, only that copy is closed, and PowerPoint is quit only when this
call started it and nothing else is open.

Usage:
    python3 pptx_safe_render.py <deck.pptx> -o <out_dir> [--pages 1,3] [--grid out.png]
                                [--lines lines.json]

Exit codes: 0 ok, 3 PowerPoint unavailable (use `officecli ... --render html`),
4 render failed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Optional

PS_SCRIPT = Path(__file__).with_name("pptx_safe_render.ps1")
UNAVAILABLE = 3
FAILED = 4


def render(pptx: Path, out_dir: Path, pages: Optional[list[int]] = None,
           width: int = 1600, timeout: int = 300,
           lines_out: Optional[Path] = None) -> tuple[int, list[Path], str]:
    """Render slides to out_dir/p<k>.png. Returns (code, pngs, detail).

    ``lines_out`` also writes, per text frame, the authored line count and the
    line count PowerPoint lays out (see ``line_mismatches``).
    """
    if os.name != "nt" or not PS_SCRIPT.exists():
        return UNAVAILABLE, [], "PowerPoint render needs Windows"
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("p*.png"):
        old.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        # A unique name never collides with a deck already open in PowerPoint.
        copy = Path(tmp) / f"render_{uuid.uuid4().hex[:8]}.pptx"
        shutil.copyfile(pptx, copy)
        args = ["powershell", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-File", str(PS_SCRIPT),
                "-Pptx", str(copy), "-OutDir", str(out_dir.resolve()),
                "-Width", str(width)]
        if pages:
            args += ["-Pages", ",".join(str(p) for p in pages)]
        if lines_out is not None:
            lines_out.parent.mkdir(parents=True, exist_ok=True)
            args += ["-LinesOut", str(lines_out.resolve())]
        try:
            proc = subprocess.run(args, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as exc:
            return FAILED, [], str(exc)
    pngs = sorted(out_dir.glob("p*.png"), key=lambda p: int(p.stem[1:]))
    code = proc.returncode
    if code == 0 and not pngs:
        code = FAILED
    return code, pngs, (proc.stderr or proc.stdout).strip()[-300:]


def line_mismatches(lines_json: Path) -> list[dict]:
    """Text frames whose PowerPoint line count differs from the authored one.

    Authored lines are paragraphs plus explicit a:br breaks, so a frame that
    PowerPoint re-wraps (Korean font metrics wider than the SVG estimate)
    shows more rendered lines than authored ones. Native table cells are
    left out: their text is meant to wrap inside the column.
    """
    try:
        rows = json.loads(lines_json.read_text(encoding="utf-8-sig") or "[]")
    except (OSError, ValueError):
        return []
    if isinstance(rows, dict):
        rows = [rows]
    return [row for row in rows
            if not row.get("cell")
            and int(row.get("rendered", 0)) != int(row.get("authored", 0))]


def contact_sheet(pngs: list[Path], out: Path, columns: Optional[int] = None,
                  tile_width: int = 480, gap: int = 12) -> Path:
    """Tile slide PNGs into one roughly square sheet."""
    from PIL import Image

    tiles = []
    for png in pngs:
        with Image.open(png) as img:
            scale = tile_width / img.width
            tiles.append(img.convert("RGB").resize(
                (tile_width, round(img.height * scale))))
    cols = columns or max(1, math.ceil(math.sqrt(len(tiles))))
    rows = math.ceil(len(tiles) / cols)
    tile_h = max(t.height for t in tiles)
    sheet = Image.new("RGB", (cols * tile_width + (cols + 1) * gap,
                              rows * tile_h + (rows + 1) * gap), "#d9d9d9")
    for i, tile in enumerate(tiles):
        r, c = divmod(i, cols)
        sheet.paste(tile, (gap + c * (tile_width + gap), gap + r * (tile_h + gap)))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def _pages(spec: str) -> list[int]:
    pages: list[int] = []
    for part in spec.split(","):
        lo, _, hi = part.partition("-")
        pages += range(int(lo), int(hi or lo) + 1)
    return pages


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="PowerPoint-exact slide render that never closes the user's PowerPoint.")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("-o", "--out-dir", type=Path, required=True)
    parser.add_argument("--pages", help="e.g. 1-3,5 (default: all)")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--grid", type=Path, help="also write a contact sheet")
    parser.add_argument("--lines", type=Path,
                        help="also write per-frame authored/rendered line counts (JSON)")
    args = parser.parse_args(argv)

    code, pngs, detail = render(args.pptx, args.out_dir,
                                _pages(args.pages) if args.pages else None,
                                args.width, lines_out=args.lines)
    if code != 0:
        print(f"[pptx_safe_render] failed (exit {code}): {detail}", file=sys.stderr)
        return code
    print(f"[pptx_safe_render] {len(pngs)} slide(s) -> {args.out_dir}")
    if args.grid:
        print(f"[pptx_safe_render] grid -> {contact_sheet(pngs, args.grid)}")
    if args.lines:
        bad = line_mismatches(args.lines)
        print(f"[pptx_safe_render] lines -> {args.lines} "
              f"({len(bad)} frame(s) re-wrapped by PowerPoint)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
