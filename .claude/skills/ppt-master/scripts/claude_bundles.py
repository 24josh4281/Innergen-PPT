#!/usr/bin/env python3
"""
PPT Master - claude.ai Bundle Sync

Builds both claude.ai deliverables from the repository in one step — the
`innergen-deck` chat/Cowork skill ZIP (build_chat_skill.py) and the INNerGEN
design system for Claude Design (build_design_system.py) — and tracks, per
machine, which content hash was last uploaded. claude.ai stores skills and
design systems inside each account, so a clone cannot push them by itself;
this tool makes the upload a one-file step and says exactly when a re-upload
is due. setup_env.py runs `build`, and the repository git hooks
(.githooks/post-merge, post-rewrite) run `build --quiet --if-changed` after
every pull, so an unchanged pull costs one file walk and prints nothing.

Usage:
    python3 scripts/claude_bundles.py build [--quiet] [--if-changed] [--no-fonts]
    python3 scripts/claude_bundles.py status
    python3 scripts/claude_bundles.py mark-uploaded {chat,design,all}

Examples:
    python3 .claude/skills/ppt-master/scripts/claude_bundles.py build
    python3 .claude/skills/ppt-master/scripts/claude_bundles.py mark-uploaded all

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402
import build_chat_skill  # noqa: E402
import build_design_system  # noqa: E402

REPO_ROOT = _SCRIPTS_DIR.parents[3]
STATE = REPO_ROOT / "OUTPUTS" / "claude-bundles-state.json"
RELEASE_TAG = "claude-bundles"

BUNDLES = {
    "chat": dict(
        label="claude.ai 채팅·Cowork 스킬 innergen-deck",
        out=build_chat_skill.DEFAULT_OUT, folder=build_chat_skill.SKILL_NAME,
        where="claude.ai → 설정 → Capabilities(기능) → Skills → 기존 innergen-deck 삭제 후 Upload skill"),
    "design": dict(
        label="Claude Design 디자인 시스템 INNerGEN",
        out=build_design_system.DEFAULT_OUT, folder=build_design_system.BUNDLE_NAME,
        where="claude.ai/design → 디자인 시스템 → INNerGEN 업데이트(처음이면 새로 만들기)에 ZIP 또는 폴더 첨부"),
}


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_fingerprint() -> str:
    """Cheap stat-based fingerprint of every input the two builders read."""
    skill = build_chat_skill.SKILL_ROOT
    roots = [skill / "scripts", skill / "references", build_design_system.STYLE_DIR,
             build_design_system.FONT_DIR] + [build_design_system.DECKS / f for f in build_design_system.FAMILIES]
    h = hashlib.sha256()
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                st = path.stat()
                h.update(f"{path.relative_to(REPO_ROOT).as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    return h.hexdigest()[:16]


def build_all(fonts: bool = True, quiet: bool = False, if_changed: bool = False) -> dict:
    """Rebuild both bundles (or skip when no input changed); returns the updated state."""
    state = load_state()
    fingerprint = source_fingerprint()
    archives = [b["out"] / f"{b['folder']}.zip" for b in BUNDLES.values()]
    if if_changed and state.get("sources") == fingerprint and all(a.is_file() for a in archives):
        return state
    sink = io.StringIO() if quiet else sys.stdout
    with contextlib.redirect_stdout(sink):
        build_chat_skill.build(BUNDLES["chat"]["out"].resolve())
        build_design_system.build(BUNDLES["design"]["out"].resolve(), fonts=fonts)
    now = datetime.now().isoformat(timespec="seconds")
    for key, b in BUNDLES.items():
        digest = build_design_system.content_hash(b["out"] / b["folder"])
        entry = state.setdefault(key, {})
        if entry.get("built") != digest:
            entry.update(built=digest, built_at=now)
    state["sources"] = fingerprint
    save_state(state)
    return state


def pending(state: dict) -> list[str]:
    return [k for k in BUNDLES if state.get(k, {}).get("built") and
            state[k].get("built") != state[k].get("uploaded")]


def report(state: dict, quiet: bool = False) -> None:
    due = pending(state)
    if quiet and not due:
        return
    print("[claude-bundles] claude.ai 반영 상태")
    for key, b in BUNDLES.items():
        entry = state.get(key, {})
        archive = b["out"] / f"{b['folder']}.zip"
        mark = "업로드 필요" if key in due else "최신(업로드됨)"
        print(f"  - {b['label']}: {mark} · 빌드 {entry.get('built', '없음')} · 업로드 {entry.get('uploaded') or '기록 없음'}")
        if key in due:
            print(f"      파일: {archive}")
            print(f"      위치: {b['where']}")
    if due:
        print("  올린 뒤 기록: python .claude/skills/ppt-master/scripts/claude_bundles.py mark-uploaded "
              + ("all" if len(due) > 1 else due[0]))
        print("  조직(Team/Enterprise) 배포는 관리자가 한 번 올리면 구성원 전원에게 적용됩니다. "
              f"최신 파일은 GitHub Release `{RELEASE_TAG}`에도 있습니다.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and track the claude.ai chat skill and Claude Design bundles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="rebuild both bundles and report what needs uploading")
    b.add_argument("--quiet", action="store_true", help="print only when an upload is due (git hooks)")
    b.add_argument("--if-changed", action="store_true", help="skip the rebuild when no input file changed")
    b.add_argument("--no-fonts", action="store_true", help="omit fonts from the design system")
    sub.add_parser("status", help="show built vs uploaded versions")
    m = sub.add_parser("mark-uploaded", help="record that the current build was uploaded")
    m.add_argument("which", choices=("chat", "design", "all"))
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    if args.command == "build":
        state = build_all(fonts=not args.no_fonts, quiet=args.quiet, if_changed=args.if_changed)
        report(state, quiet=args.quiet)
        return 0
    state = load_state()
    if args.command == "mark-uploaded":
        keys = list(BUNDLES) if args.which == "all" else [args.which]
        for key in keys:
            entry = state.get(key, {})
            if not entry.get("built"):
                print(f"[claude-bundles] {key}: 빌드 기록 없음 — 먼저 build를 실행하세요", file=sys.stderr)
                return 1
            entry["uploaded"] = entry["built"]
            entry["uploaded_at"] = datetime.now().isoformat(timespec="seconds")
        save_state(state)
    report(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
