#!/usr/bin/env python3
"""
PPT Master - Codex Workspace Package

Build a source-only ZIP for another PC. Include allowlisted Git-tracked files
and, only when requested, untracked source files. Exclude local data, virtual
environments, credentials and Git history. Each PC runs the existing setup.
See the repository's Korean usage guide for installation and update limits.

Usage:
    python3 scripts/build_codex_package.py --output <new-file.zip> [options]

Examples:
    python3 .claude/skills/ppt-master/scripts/build_codex_package.py --output OUTPUTS/codex/slide-master.zip
    python3 .claude/skills/ppt-master/scripts/build_codex_package.py --output draft.zip --include-untracked

Dependencies:
    None (standard library only; Git executable required)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from console_encoding import configure_utf8_stdio

REPO_ROOT = Path(__file__).resolve().parents[4]
PACKAGE_ROOT = "slide-master-codex"
ROOT_FILES = {
    ".gitattributes", ".gitignore", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    "LICENSE", "README.md", "requirements.txt", "setup.ps1", "setup.sh",
    "setup-codex.cmd", "설치안내.md", "사용방법.md",
}
SOURCE_DIRS = (
    ".claude/skills/", ".codex/skills/", ".gemini/skills/",
    ".githooks/", ".github/workflows/", "docs/",
)
BLOCKED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "inputs", "outputs",
    "output", "tmp", "projects", ".preview", ".bkit", ".superpowers",
}
BLOCKED_SUFFIXES = {".pyc", ".pyo", ".pem", ".key", ".pfx", ".p12", ".log"}
BLOCKED_NAMES = {"auth.json", "credentials.json", "config.toml", "settings.local.json"}
REQUIRED_FILES = {
    "setup.ps1", "setup.sh", "setup-codex.cmd", "requirements.txt", "AGENTS.md",
    "CLAUDE.md", "사용방법.md",
    ".claude/skills/ppt-master/scripts/setup_env.py",
    ".claude/skills/ppt-master/scripts/sync_codex_stubs.py",
    ".claude/skills/ppt-master/workflows/routing.md",
}


def git_output(*args: str) -> str:
    """Read Git metadata without changing the index or working tree."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], check=True,
        capture_output=True, encoding="utf-8", errors="strict",
    )
    return result.stdout


def allowed(path: str) -> bool:
    """Limit the package to portable workflow source and bundled assets."""
    rel = PurePosixPath(path)
    parts = [part.lower() for part in rel.parts]
    if rel.is_absolute() or ".." in parts or any(part in BLOCKED_DIRS for part in parts):
        return False
    if any(part.startswith(".env") for part in parts):
        return False
    if rel.name.lower() in BLOCKED_NAMES or rel.suffix.lower() in BLOCKED_SUFFIXES:
        return False
    if path.startswith(("docs/handoff/", "docs/superpowers/")):
        return False
    return path in ROOT_FILES or path.startswith(SOURCE_DIRS)


def collect_files(include_untracked: bool) -> tuple[list[str], list[str]]:
    """Collect explicit source paths; reject links that could escape the repository."""
    tracked = set(filter(None, git_output("ls-files", "-z").split("\0")))
    untracked = set(filter(None, git_output("ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    candidates = tracked | untracked if include_untracked else tracked
    selected = []
    for rel in sorted(candidates):
        if not allowed(rel):
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            if rel in tracked:
                raise ValueError(f"Tracked file is missing: {rel}; resolve before packaging.")
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(REPO_ROOT):
            raise ValueError(f"Refusing linked source: {rel}")
        selected.append(rel)
    missing = REQUIRED_FILES - set(selected)
    if missing:
        raise ValueError("Missing package files: " + ", ".join(sorted(missing))
                         + "; commit them or use --include-untracked for a draft.")
    return selected, sorted(set(selected) & untracked)


def build_package(output: Path, include_untracked: bool) -> dict:
    """Write a new ZIP and a SHA-256 sidecar, preserving existing outputs."""
    output = output.resolve()
    checksum = output.with_suffix(output.suffix + ".sha256")
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must end in .zip.")
    if output.exists() or checksum.exists():
        raise ValueError("Output already exists; choose a new versioned filename.")
    paths, untracked = collect_files(include_untracked)
    status = git_output("status", "--porcelain", "--untracked-files=all")
    manifest = {
        "schema": "codex_workspace_package.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "repository": "https://github.com/24josh4281/Innergen-PPT.git",
        "deployment_branch": "slide-master",
        "source_commit": git_output("rev-parse", "HEAD").strip(),
        "source_branch": git_output("branch", "--show-current").strip(),
        "working_tree_has_changes": bool(status.strip()),
        "included_tracked_changes": sorted(set(paths) & set(filter(None,
            git_output("diff", "HEAD", "--name-only", "-z").split("\0")))),
        "included_untracked_source": untracked,
        "install": "setup-codex.cmd (Windows); sh setup.sh (macOS/Linux)",
        "update": "ZIP snapshot has no Git history; use a new package or a separate Git clone.",
        "excluded": "Client data, projects, outputs, .venv, .git, credentials and user settings.",
        "files": [],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for rel in paths:
            data = (REPO_ROOT / rel).read_bytes()
            archive.writestr(f"{PACKAGE_ROOT}/{rel}", data)
            manifest["files"].append({
                "path": rel, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            })
        archive.writestr(f"{PACKAGE_ROOT}/package-manifest.json",
                         json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        archive.writestr(f"{PACKAGE_ROOT}/projects/README.md",
                         "# Local projects\n\nKeep source documents and new decks here. This folder is not distributed.\n")
    with zipfile.ZipFile(output) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"ZIP integrity check failed: {bad}; keep this file for diagnosis.")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with checksum.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{digest}  {output.name}\n")
    return {"output": str(output), "files": len(paths), "size_bytes": output.stat().st_size,
            "sha256": digest, "included_untracked": len(untracked),
            "source_commit": manifest["source_commit"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="new versioned ZIP filename")
    parser.add_argument("--include-untracked", action="store_true", help="include allowlisted untracked source in a draft")
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        result = build_package(args.output, args.include_untracked)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Package failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
