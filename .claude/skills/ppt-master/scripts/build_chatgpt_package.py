#!/usr/bin/env python3
"""
PPT Master - ChatGPT Package Builder

Repackages the claude.ai `innergen-deck` chat skill for ChatGPT chat, Projects
and Work workspaces, where the deck pipeline runs inside the Python tool. The
package adds a ChatGPT adapter (CHATGPT.md: unpack step and path/command
substitutions) to the skill folder and writes the project instructions and a
Korean install guide beside the ZIP. The chat skill itself is unchanged.

Usage:
    python3 scripts/build_chatgpt_package.py [options]

Examples:
    python3 .claude/skills/ppt-master/scripts/build_chatgpt_package.py
    python3 .claude/skills/ppt-master/scripts/build_chatgpt_package.py -o OUTPUTS/chatgpt-package

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from build_chat_skill import REPO_ROOT, SKILL_NAME, build  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402

GPT_SRC = _SCRIPTS_DIR / "chat_skill" / "chatgpt"
DEFAULT_OUT = REPO_ROOT / "OUTPUTS" / "chatgpt-package"
ARCHIVE = "innergen-deck-chatgpt.zip"
INSTRUCTIONS = "chatgpt-project-instructions.txt"
GUIDE = "설치방법.md"
# ChatGPT project instructions accept about 8,000 characters.
MAX_INSTRUCTION_CHARS = 8000


def package(out_dir: Path) -> Path:
    text = (GPT_SRC / "instructions.txt").read_text(encoding="utf-8")
    if len(text) > MAX_INSTRUCTION_CHARS:
        raise SystemExit(f"[build_chatgpt_package] instructions are {len(text)} characters; "
                         f"ChatGPT accepts {MAX_INSTRUCTION_CHARS}")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        build(work)
        bundle = work / SKILL_NAME
        shutil.copy2(GPT_SRC / "CHATGPT.md", bundle / "CHATGPT.md")
        archive = out_dir / ARCHIVE
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(work).as_posix())
    (out_dir / INSTRUCTIONS).write_text(text, encoding="utf-8")
    shutil.copy2(GPT_SRC / GUIDE, out_dir / GUIDE)
    return archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the ChatGPT chat/Work package (skill ZIP + project instructions).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT,
                        help=f"output directory (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = package(out_dir)
    size_mb = archive.stat().st_size / 1_000_000
    print(f"[build_chatgpt_package] wrote {archive} ({size_mb:.1f} MB)")
    print(f"[build_chatgpt_package] paste {INSTRUCTIONS} into the project instructions; "
          f"see {GUIDE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
