#!/usr/bin/env python3
"""
PPT Master - claude.ai Chat Skill Builder

Packages the INNerGEN deck pipeline as a standalone `innergen-deck` skill that
claude.ai chat / Cowork can run inside its sandbox (Settings → Capabilities →
Skills → Upload skill). The bundle carries the chat procedure
(chat_skill/SKILL.chat.md), the export engine's import closure
(svg_to_pptx, svg_quality_checker, innergen_qaqc), the three INNerGEN family
templates, per-family base spec locks, and the INNerGEN rule documents. The
repository pipeline itself is unchanged; this only copies from it.

Usage:
    python3 scripts/build_chat_skill.py [options]

Examples:
    python3 .claude/skills/ppt-master/scripts/build_chat_skill.py
    python3 .claude/skills/ppt-master/scripts/build_chat_skill.py -o OUTPUTS/claude-chat-skill

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import modulefinder
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

# scripts/build_chat_skill.py: [0]=scripts [1]=ppt-master [2]=skills [3]=.claude [4]=repo
SKILL_ROOT = _SCRIPTS_DIR.parent
REPO_ROOT = _SCRIPTS_DIR.parents[3]
CHAT_SRC = _SCRIPTS_DIR / "chat_skill"
SKILL_NAME = "innergen-deck"
DEFAULT_OUT = REPO_ROOT / "OUTPUTS" / "claude-chat-skill"

ENTRY_SCRIPTS = ("svg_to_pptx.py", "svg_quality_checker.py", "innergen_qaqc.py")
FAMILIES = ("innergen_lecture", "innergen_business", "innercarry")
STYLE_DOCS = (
    "design-standard-v17.md", "design-standard-v17.json",
    "content-architecture-v20.md", "content-architecture-v20.json",
    "structured-slides-v18.md", "structured-slides-v18.json",
    "consulting-structures-v19.md",
    "design-governing-v11.md", "design-wrapping-v15.md",
    "innergen-profile-matrix-v16.md", "report-profiles.json",
    "qaqc-v21.md", "qaqc-v21.json",
)
ENGINE_DOCS = ("shared-standards.md", "executor-cheatcard.md", "semantic-svg.md")
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def _local_modules() -> tuple[set[str], set[str]]:
    """Top-level script modules and package directories the entry scripts import."""
    finder = modulefinder.ModuleFinder(path=[str(_SCRIPTS_DIR)] + sys.path)
    for entry in ENTRY_SCRIPTS:
        finder.run_script(str(_SCRIPTS_DIR / entry))
    modules: set[str] = set(ENTRY_SCRIPTS)
    packages: set[str] = set()
    for mod in finder.modules.values():
        file = getattr(mod, "__file__", None)
        if not file:
            continue
        path = Path(file).resolve()
        try:
            rel = path.relative_to(_SCRIPTS_DIR)
        except ValueError:
            continue
        if len(rel.parts) == 1:
            modules.add(rel.name)
        else:
            packages.add(rel.parts[0])
    return modules, packages


def build(out_dir: Path) -> Path:
    bundle = out_dir / SKILL_NAME
    if bundle.exists():
        shutil.rmtree(bundle)
    scripts = bundle / "scripts"
    scripts.mkdir(parents=True)

    shutil.copy2(CHAT_SRC / "SKILL.chat.md", bundle / "SKILL.md")
    shutil.copytree(CHAT_SRC / "locks", bundle / "locks")
    shutil.copy2(CHAT_SRC / "start_deck.py", scripts / "start_deck.py")

    modules, packages = _local_modules()
    for name in sorted(modules):
        shutil.copy2(_SCRIPTS_DIR / name, scripts / name)
    for pkg in sorted(packages):
        shutil.copytree(_SCRIPTS_DIR / pkg, scripts / pkg, ignore=_IGNORE)

    for family in FAMILIES:
        shutil.copytree(SKILL_ROOT / "templates" / "decks" / family,
                        bundle / "templates" / "decks" / family, ignore=_IGNORE)

    refs = bundle / "references"
    refs.mkdir()
    for name in STYLE_DOCS:
        shutil.copy2(REPO_ROOT / "docs" / "styles" / "innergen" / name, refs / name)
    for name in ENGINE_DOCS:
        shutil.copy2(SKILL_ROOT / "references" / name, refs / name)

    # claude.ai expects the ZIP to contain the skill folder, not loose files.
    archive = out_dir / f"{SKILL_NAME}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(out_dir).as_posix())
    print(f"[build_chat_skill] {len(modules)} module(s), {len(packages)} package(s), "
          f"{len(FAMILIES)} famil(ies), {len(STYLE_DOCS) + len(ENGINE_DOCS)} reference(s)")
    return archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the innergen-deck skill ZIP for claude.ai chat upload.",
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
    archive = build(out_dir)
    size_mb = archive.stat().st_size / 1_000_000
    print(f"[build_chat_skill] wrote {archive} ({size_mb:.1f} MB)")
    print("[build_chat_skill] upload: claude.ai → Settings → Capabilities → Skills → Upload skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
