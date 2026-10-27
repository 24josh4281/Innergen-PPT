#!/usr/bin/env python3
"""
PPT Master - Portable Skill Environment Check

Report runtime dependencies and renderer/font availability without changing
the environment. See ENVIRONMENT.md in the generated skill.

Usage:
    python3 scripts/environment_check.py

Examples:
    python3 scripts/environment_check.py --mode equations

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Check portable skill prerequisites without installing.")
    parser.add_argument("--mode", choices=("deck", "equations"), default="deck")
    args = parser.parse_args(argv)
    modules = {"pptx": "python-pptx"}
    if args.mode == "deck":
        modules.update({"lxml": "lxml", "PIL": "Pillow", "openpyxl": "openpyxl",
                        "xlsxwriter": "XlsxWriter", "yaml": "PyYAML"})
    missing = [package for module, package in modules.items() if importlib.util.find_spec(module) is None]
    roots = [Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), Path.home() / ".fonts"]
    if os.name == "nt":
        roots.extend([Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
                      Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Microsoft/Windows/Fonts"])
    names = [p.stem.lower() for root in roots if root.is_dir()
             for p in root.rglob("*") if p.suffix.lower() in (".ttf", ".otf", ".ttc")]
    print(json.dumps({"mode": args.mode, "missing_packages": missing,
                      "libreoffice": shutil.which("soffice") or shutil.which("libreoffice"),
                      "pretendard_found": any("pretendard" in n for n in names),
                      "ibm_plex_sans_kr_found": any("ibmplexsanskr" in n.replace("-", "") for n in names)},
                     ensure_ascii=False, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
