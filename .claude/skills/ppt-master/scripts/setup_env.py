#!/usr/bin/env python3
"""
PPT Master - Environment Setup

One-shot bootstrap for a fresh clone: creates the repository virtual
environment (.venv), installs requirements.txt into it, installs the bundled
fonts for the current user, regenerates the per-host skill stubs
(.codex/skills for GPT/Codex, .gemini/skills for Gemini CLI; Claude Code reads
.claude/skills directly) and verifies the result. Afterwards opening Claude
Code, Codex or Gemini CLI at the repository root picks up the same skill set.

Run it with any system Python 3.10+; the root wrappers setup.ps1 / setup.sh
find one for you. Safe to re-run: every step is idempotent.

Usage:
    python3 scripts/setup_env.py [options]

Examples:
    python3 .claude/skills/ppt-master/scripts/setup_env.py
    python3 .claude/skills/ppt-master/scripts/setup_env.py --skip-fonts
    python3 .claude/skills/ppt-master/scripts/setup_env.py --recreate
    python3 .claude/skills/ppt-master/scripts/setup_env.py --check

Dependencies:
    None (only uses standard library; installs requirements.txt into .venv)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
import sync_codex_stubs  # noqa: E402

# scripts/setup_env.py: [0]=scripts [1]=ppt-master [2]=skills [3]=.claude [4]=repo
REPO_ROOT = Path(__file__).resolve().parents[4]
VENV_DIR = REPO_ROOT / ".venv"
REQUIREMENTS = REPO_ROOT / "requirements.txt"
MIN_PYTHON = (3, 10)

# Imports that prove the core pipeline (SVG → PPTX, PDF/DOCX intake) works.
SMOKE_IMPORTS = ("pptx", "pymupdf", "mammoth", "PIL", "openpyxl")

# Host → (CLI binary, project-level skill directory, context file).
HOSTS = (
    ("Claude Code", "claude", ".claude/skills", "CLAUDE.md"),
    ("GPT (Codex CLI / ChatGPT Codex)", "codex", ".codex/skills", "AGENTS.md"),
    ("Gemini CLI", "gemini", ".gemini/skills", "GEMINI.md"),
)


def _step(msg: str) -> None:
    print(f"\n[setup] {msg}", flush=True)


def venv_python(venv_dir: Path = VENV_DIR) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list[str]) -> int:
    print("  $ " + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.call([str(c) for c in cmd], cwd=REPO_ROOT)


def ensure_venv(recreate: bool) -> Path:
    py = venv_python()
    if recreate and VENV_DIR.exists():
        _step(f"removing {VENV_DIR.name}/ (--recreate)")
        shutil.rmtree(VENV_DIR)
    if py.is_file():
        _step(f"reusing {VENV_DIR.name}/ ({py.relative_to(REPO_ROOT)})")
        return py
    _step(f"creating {VENV_DIR.name}/ with Python {sys.version.split()[0]}")
    venv.EnvBuilder(with_pip=True, upgrade_deps=False).create(VENV_DIR)
    if not py.is_file():
        raise RuntimeError(f"virtual environment created but {py} is missing")
    return py


def install_requirements(py: Path) -> int:
    _step("installing requirements.txt into .venv")
    rc = _run([py, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
    if rc:
        return rc
    return _run([py, "-m", "pip", "install", "-r", REQUIREMENTS, "--quiet"])


def install_fonts(py: Path) -> int:
    _step("installing bundled fonts for the current user")
    return _run([py, _SCRIPTS_DIR / "install_fonts.py"])


def sync_stubs() -> int:
    _step("regenerating host skill stubs (.codex/skills, .gemini/skills)")
    return sync_codex_stubs.main([])


def smoke_test(py: Path) -> int:
    _step("verifying core imports inside .venv")
    code = "import " + ", ".join(SMOKE_IMPORTS) + "; print('  imports ok')"
    return _run([py, "-c", code])


def report_hosts() -> None:
    _step("host readiness")
    for label, binary, skill_dir, context in HOSTS:
        found = "found" if shutil.which(binary) else "not on PATH"
        print(f"  - {label}: `{binary}` {found}; skills {skill_dir}/, rules {context}")
    print("\n  Open any of them at the repository root, e.g.:")
    print("    claude    |    codex    |    gemini")
    print('  then ask: "이너젠 스타일로 <자료> 컨설팅 장표 만들어줘"')
    if not shutil.which("codex"):
        print("\n  Note: AI images default to the Codex CLI backend "
              "(npm install -g @openai/codex && codex login), or set "
              "IMAGE_BACKEND + an API key in .env.")


def check_only() -> int:
    py = venv_python()
    problems = 0
    if not py.is_file():
        print(f"[setup] missing {py.relative_to(REPO_ROOT)} — run setup without --check")
        problems += 1
    elif smoke_test(py):
        problems += 1
    if sync_codex_stubs.check():
        problems += 1
    report_hosts()
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create .venv, install dependencies and fonts, and sync the "
                    "Claude/Codex/Gemini skill sets.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--recreate", action="store_true",
                        help="delete and rebuild .venv from scratch")
    parser.add_argument("--skip-fonts", action="store_true",
                        help="do not install the bundled fonts")
    parser.add_argument("--check", action="store_true",
                        help="verify an existing setup without changing anything")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    if sys.version_info < MIN_PYTHON:
        print(f"[setup] Python {'.'.join(map(str, MIN_PYTHON))}+ required, "
              f"found {sys.version.split()[0]}", file=sys.stderr)
        return 1
    if args.check:
        return check_only()

    py = ensure_venv(args.recreate)
    if install_requirements(py):
        print("[setup] pip install failed — see the output above", file=sys.stderr)
        return 1
    if not args.skip_fonts and install_fonts(py):
        print("[setup] font install reported a problem — decks still build, "
              "but text metrics may differ; re-run install_fonts.py later",
              file=sys.stderr)
    if sync_stubs() or sync_codex_stubs.check():
        return 1
    if smoke_test(py):
        return 1
    report_hosts()
    print("\n[setup] done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
