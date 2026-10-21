#!/usr/bin/env python3
"""
PPT Master - Content Group Centering Skill ZIP

Packs the ppt-content-group-centering skill into a standalone ZIP for
claude.ai chat / Claude Cowork upload and for Codex installs outside this
repository. The SVG checker from ppt-master/scripts is copied in so the ZIP
works without the repository.

Usage:
    python3 .claude/skills/ppt-content-group-centering/scripts/build_skill_zip.py [-o OUT.zip]

Examples:
    python3 .claude/skills/ppt-content-group-centering/scripts/build_skill_zip.py

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO = SKILL_DIR.parents[2]
CHECKER = REPO / ".claude/skills/ppt-master/scripts/content_balance_check.py"


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the standalone skill ZIP.")
    ap.add_argument("-o", "--output", type=Path, default=REPO / "OUTPUTS" / f"{SKILL_DIR.name}.zip")
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(SKILL_DIR.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                zf.write(p, f"{SKILL_DIR.name}/{p.relative_to(SKILL_DIR).as_posix()}")
        zf.write(CHECKER, f"{SKILL_DIR.name}/scripts/{CHECKER.name}")
    print(f"[build_skill_zip] {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
