#!/usr/bin/env python3
"""
PPT Master - Environment Setup

One-shot bootstrap for a fresh clone: creates the repository virtual
environment (.venv), installs requirements.txt into it, installs the bundled
fonts for the current user, regenerates the per-host skill stubs
(.codex/skills for GPT/Codex, .gemini/skills for Gemini CLI; Claude Code reads
.claude/skills directly) and verifies the result. Afterwards opening Claude
Code, Codex or Gemini CLI at the repository root picks up the same skill set.
It also builds the claude.ai chat skill and the Claude Design design system
(claude_bundles.py) and points git at .githooks so every pull rebuilds them,
re-installs requirements when they changed, and says when a re-upload is due.

So that every clone performs like the reference machine, setup also installs
the optional tools best-effort (playwright + Chromium for screen checks,
OfficeCLI for exported-PPTX verification, Codex CLI for AI images; Node.js LTS
through winget on Windows when npm is missing), exports a two-page INNerGEN
self-test deck, and ends with a plain-Korean readiness summary listing the
only steps left to the user (codex login, claude.ai upload).

Run it with any system Python 3.10+; the root wrappers setup.ps1 / setup.sh
find one for you (setup.ps1 installs Python through winget when none is found).
Safe to re-run: every step is idempotent.

Usage:
    python3 scripts/setup_env.py [options]

Examples:
    python3 .claude/skills/ppt-master/scripts/setup_env.py
    python3 .claude/skills/ppt-master/scripts/setup_env.py --skip-fonts
    python3 .claude/skills/ppt-master/scripts/setup_env.py --recreate
    python3 .claude/skills/ppt-master/scripts/setup_env.py --check
    python3 .claude/skills/ppt-master/scripts/setup_env.py --skip-extras
    python3 .claude/skills/ppt-master/scripts/setup_env.py --deps-if-changed

Dependencies:
    None (only uses standard library; installs requirements.txt into .venv)
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
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
import claude_bundles  # noqa: E402

# scripts/setup_env.py: [0]=scripts [1]=ppt-master [2]=skills [3]=.claude [4]=repo
REPO_ROOT = Path(__file__).resolve().parents[4]
VENV_DIR = REPO_ROOT / ".venv"
REQUIREMENTS = REPO_ROOT / "requirements.txt"
REQUIREMENT_FILES = (REQUIREMENTS, _SCRIPTS_DIR.parent / "requirements.txt")
DEPS_STAMP = VENV_DIR / ".slide-master-requirements"
MIN_PYTHON = (3, 10)

# Imports that prove the core pipeline (SVG → PPTX, PDF/DOCX intake) works.
SMOKE_IMPORTS = ("pptx", "pymupdf", "mammoth", "PIL", "openpyxl")

# Host → (CLI binary, project-level skill directory, context file).
HOSTS = (
    ("Claude Code", "claude", ".claude/skills", "CLAUDE.md"),
    ("GPT (Codex CLI / ChatGPT Codex)", "codex", ".codex/skills", "AGENTS.md"),
    ("Gemini CLI", "gemini", ".gemini/skills", "GEMINI.md"),
)

# Optional npm tools: (binary, pinned package). OfficeCLI gates ppt-template-fill
# and verify-pptx-export; Codex CLI is the default AI-image backend.
NPM_TOOLS = (
    ("officecli", "@officecli/officecli@1.0.135"),
    ("codex", "@openai/codex"),
)
MIN_CODEX = (0, 148, 0)
WINGET_NODE = ["winget", "install", "-e", "--id", "OpenJS.NodeJS.LTS", "--silent",
               "--accept-source-agreements", "--accept-package-agreements"]

SELFTEST_DIR = REPO_ROOT / "tmp" / "setup-selftest"
SELFTEST_FAMILY = "innergen_business"
SELFTEST_PAGES = (("01_cover.svg", "01_cover.svg"), ("s43_issue_tree.svg", "02_s43.svg"))
GUIDE = "설치안내.md"


def _step(msg: str) -> None:
    print(f"\n[setup] {msg}", flush=True)


def venv_python(venv_dir: Path = VENV_DIR) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(cmd: list, quiet: bool = False) -> int:
    print("  $ " + " ".join(str(c) for c in cmd), flush=True)
    out = subprocess.DEVNULL if quiet else None
    try:
        return subprocess.call([str(c) for c in cmd], cwd=REPO_ROOT, stdout=out, stderr=out)
    except OSError as exc:
        print(f"  failed to start: {exc}", file=sys.stderr)
        return 1


def _find(binary: str) -> Optional[str]:
    """shutil.which plus the Windows Node/npm folders a fresh install has not put on PATH yet."""
    found = shutil.which(binary)
    if found or os.name != "nt":
        return found
    dirs = (Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "nodejs",
            Path(os.environ.get("APPDATA", "")) / "npm")
    for folder in dirs:
        for ext in (".cmd", ".exe", ""):
            candidate = folder / f"{binary}{ext}"
            if candidate.is_file():
                return str(candidate)
    return None


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


def requirements_digest() -> str:
    h = hashlib.sha256()
    for path in REQUIREMENT_FILES:
        h.update(path.read_bytes() if path.is_file() else b"")
    return h.hexdigest()[:16]


def install_requirements(py: Path) -> int:
    _step("installing requirements.txt into .venv")
    rc = _run([py, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
    if rc:
        return rc
    rc = _run([py, "-m", "pip", "install", "-r", REQUIREMENTS, "--quiet"])
    if rc == 0:
        DEPS_STAMP.write_text(requirements_digest() + "\n", encoding="utf-8")
    return rc


def deps_if_changed() -> int:
    """Git-hook path: re-install requirements only when requirements*.txt changed."""
    py = venv_python()
    if not py.is_file():
        return 0
    try:
        stamp = DEPS_STAMP.read_text(encoding="utf-8").strip()
    except OSError:
        stamp = ""
    if stamp == requirements_digest():
        return 0
    print("[setup] requirements changed — updating .venv", flush=True)
    return install_requirements(py)


def install_fonts(py: Path) -> int:
    _step("installing bundled fonts for the current user")
    return _run([py, _SCRIPTS_DIR / "install_fonts.py"])


def sync_stubs() -> int:
    _step("regenerating host skill stubs (.codex/skills, .gemini/skills)")
    return sync_codex_stubs.main([])


def build_claude_bundles() -> int:
    _step("building claude.ai chat skill + Claude Design design system (OUTPUTS/)")
    try:
        claude_bundles.report(claude_bundles.build_all(quiet=True))
    except OSError as exc:
        print(f"  bundle build failed: {exc}", file=sys.stderr)
        return 1
    return 0


def enable_python_utf8() -> None:
    """Set PYTHONUTF8=1 for the user so agent-run Python never crashes on cp949."""
    _step("enabling Python UTF-8 mode for this user (PYTHONUTF8=1)")
    if os.name != "nt":
        print("  skipped: only Windows consoles default to a legacy code page")
        return
    if os.environ.get("PYTHONUTF8") == "1":
        print("  already enabled")
        return
    if subprocess.run(["setx", "PYTHONUTF8", "1"], capture_output=True).returncode:
        print("  failed: run `setx PYTHONUTF8 1` once by hand")
        return
    os.environ["PYTHONUTF8"] = "1"
    print("  enabled (applies to terminals and agents started from now on)")


def install_git_hooks() -> None:
    """Point this clone at .githooks unless the user already has hooks of their own."""
    _step("enabling .githooks (rebuild claude.ai bundles and update .venv after git pull)")
    if not (REPO_ROOT / ".git").is_dir() or not shutil.which("git"):
        print("  skipped: not a git clone or git not on PATH")
        return
    git = ["git", "-C", str(REPO_ROOT), "config", "--local"]
    current = subprocess.run(git + ["--get", "core.hooksPath"],
                             capture_output=True, text=True).stdout.strip()
    own = [h.name for h in (REPO_ROOT / ".git" / "hooks").glob("*")
           if h.is_file() and not h.name.endswith(".sample")]
    if current == ".githooks":
        print("  already enabled")
    elif current or own:
        print(f"  skipped: existing hooks ({current or ', '.join(own)}); "
              "copy .githooks/post-merge next to them to keep both")
    else:
        subprocess.run(git + ["core.hooksPath", ".githooks"], check=False)
        print("  enabled: git config core.hooksPath .githooks")


def ensure_npm() -> Optional[str]:
    npm = _find("npm")
    if npm or os.name != "nt" or not shutil.which("winget"):
        return npm
    _step("npm not found — installing Node.js LTS with winget")
    _run(WINGET_NODE)
    npm = _find("npm")
    if npm:
        # Child processes (npm's own node, the self-test) need the new folders on PATH.
        extra = [str(Path(npm).parent), str(Path(os.environ.get("APPDATA", "")) / "npm")]
        os.environ["PATH"] = os.pathsep.join(extra + [os.environ.get("PATH", "")])
    return npm


def install_extras(py: Path) -> bool:
    """Install the optional tools; returns True when anything new was installed."""
    _step("installing optional tools (screen checks, PPTX verification, AI images)")
    installed = False
    if _run([py, "-c", "import playwright"], quiet=True):
        installed |= _run([py, "-m", "pip", "install", "playwright", "--quiet"]) == 0
    _run([py, "-m", "playwright", "install", "chromium"])
    had_npm = bool(_find("npm"))
    npm = ensure_npm()
    if not npm:
        print("  npm not found — skipped OfficeCLI and Codex CLI; "
              "install Node.js LTS (https://nodejs.org) and re-run setup")
        return installed
    installed |= not had_npm
    for binary, package in NPM_TOOLS:
        if binary == "codex" and _codex_outdated():
            installed |= upgrade_codex(npm, package)
        elif _find(binary):
            print(f"  {binary}: already installed")
        else:
            installed |= _run([npm, "install", "-g", package]) == 0
    return installed


def _codex_outdated() -> bool:
    """True when the Codex CLI first on PATH is older than MIN_CODEX.

    The Codex desktop app writes newer settings (e.g. service_tier = "default")
    to ~/.codex/config.toml; 0.129 rejects them, so every `codex exec` fails
    before the prompt runs. 0.148 is the oldest release checked to read them.
    """
    codex = _find("codex")
    if not codex:
        return False
    try:
        out = subprocess.run([codex, "--version"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    found = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    return bool(found) and tuple(int(x) for x in found.groups()) < MIN_CODEX


def upgrade_codex(npm: str, package: str) -> bool:
    """Upgrade the shadowing Codex CLI (winget copy first on Windows, else npm)."""
    print("  codex: older than %d.%d.%d, which ~/.codex/config.toml needs — upgrading" % MIN_CODEX)
    codex = _find("codex") or ""
    if os.name == "nt" and "winget" in codex.lower() and _find("winget"):
        _run(["winget", "upgrade", "-e", "--id", "OpenAI.Codex", "--silent",
              "--accept-source-agreements", "--accept-package-agreements"])
    else:
        _run([npm, "install", "-g", package])
    ok = not _codex_outdated()
    print(f"  codex: {'ok' if ok else 'still too old — reinstall Codex CLI'}")
    return ok


def smoke_test(py: Path) -> int:
    _step("verifying core imports inside .venv")
    code = "import " + ", ".join(SMOKE_IMPORTS) + "; print('  imports ok')"
    return _run([py, "-c", code])


def self_test(py: Path) -> bool:
    """Scaffold a two-page INNerGEN deck and export it to a real PPTX."""
    _step("exporting a two-page INNerGEN self-test deck (tmp/setup-selftest)")
    chat = claude_bundles.BUNDLES["chat"]
    start_deck = chat["out"] / chat["folder"] / "scripts" / "start_deck.py"
    if not start_deck.is_file():
        import build_chat_skill
        with open(os.devnull, "w", encoding="utf-8") as sink:
            stdout, sys.stdout = sys.stdout, sink
            try:
                build_chat_skill.build(chat["out"].resolve())
            finally:
                sys.stdout = stdout
    pptx = SELFTEST_DIR / "exports" / "selftest.pptx"
    check = ("import sys; from pptx import Presentation; "
             "p = Presentation(sys.argv[1]); "
             "sys.exit(0 if len(p.slides) == 2 and all(len(s.shapes) > 5 for s in p.slides) else 1)")
    ok = _run([py, start_deck, "--family", SELFTEST_FAMILY, "--out", SELFTEST_DIR, "--force"]) == 0
    if ok:
        for src, dst in SELFTEST_PAGES:
            shutil.copy2(SELFTEST_DIR / "templates" / src, SELFTEST_DIR / "svg_output" / dst)
        ok = (_run([py, _SCRIPTS_DIR / "svg_to_pptx.py", SELFTEST_DIR, "-o", pptx, "-q"]) == 0
              and _run([py, "-c", check, pptx]) == 0)
    print(f"  {'ok' if ok else 'FAILED'}: {pptx.relative_to(REPO_ROOT)}")
    return ok


def _codex_logged_in() -> bool:
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return (home / "auth.json").is_file()


def readiness(py: Path, core_ok: bool, fonts_ok: bool, restart: bool = False) -> int:
    """Print the plain-Korean summary the agent relays to the user; returns 0 when the core works."""
    has_playwright = py.is_file() and _run([py, "-c", "import playwright"], quiet=True) == 0
    image_key = (REPO_ROOT / ".env").is_file() or any(
        os.environ.get(k) for k in ("OPENAI_API_KEY", "GEMINI_API_KEY", "IMAGE_BACKEND"))
    codex = _find("codex")
    rows = [
        ("완료" if core_ok else "실패", "장표 만들기 · PPTX 내보내기",
         "시험 장표 2쪽을 PPTX로 만들어 확인" if core_ok else "위 오류를 확인한 뒤 설치를 다시 실행"),
        ("완료" if fonts_ok else "확인 필요", "글꼴 (Pretendard · IBM Plex Sans KR · 나눔스퀘어 네오)",
         "" if fonts_ok else "install_fonts.py 다시 실행"),
        ("완료" if has_playwright else "확인 필요", "화면 검사 도구 (playwright)",
         "" if has_playwright else "설치를 다시 실행"),
        ("완료" if _find("officecli") else "확인 필요", "PPTX 검증 도구 (OfficeCLI)",
         "" if _find("officecli") else "Node.js LTS 설치 후 설치를 다시 실행"),
    ]
    if image_key or (codex and _codex_logged_in()):
        rows.append(("완료", "AI 이미지 생성", ""))
    elif codex:
        rows.append(("사용자 할 일", "AI 이미지 생성",
                     "터미널에서 `codex login` 실행 → 열리는 브라우저에서 ChatGPT 계정으로 로그인 (한 번만)"))
    else:
        rows.append(("확인 필요", "AI 이미지 생성", "Node.js LTS 설치 후 설치를 다시 실행"))
    state = claude_bundles.load_state()
    rows.append(("안내", "claude.ai 채팅 · Claude Design",
                 "이미 올린 claude.ai 계정이면 할 일 없음. 다른 계정이면 "
                 f"{GUIDE} 4번대로 ZIP 두 개를 한 번 올리기" if state.get("chat") else
                 f"{GUIDE} 4번 참고"))
    print("\n" + "=" * 20 + " 설치 결과 " + "=" * 20)
    for mark, label, note in rows:
        print(f"  [{mark}] {label}" + (f" — {note}" if note else ""))
    todo = [r for r in rows if r[0] in ("실패", "확인 필요", "사용자 할 일")]
    if core_ok:
        print('\n  이제 이렇게 요청하면 됩니다: "이너젠 스타일로 <자료 경로> 컨설팅 장표 만들어줘"')
    if todo:
        print(f"  남은 일 {len(todo)}개는 위 표의 설명대로 하면 됩니다 (자세한 안내: {GUIDE}).")
    if restart:
        print("  새로 설치한 도구를 AI 앱이 인식하도록, 지금 쓰는 AI 앱(Claude·Codex 등)을 한 번 껐다 켜 주세요.")
    return 0 if core_ok else 1


def report_hosts() -> None:
    _step("host readiness")
    for label, binary, skill_dir, context in HOSTS:
        found = "found" if shutil.which(binary) else "not on PATH"
        print(f"  - {label}: `{binary}` {found}; skills {skill_dir}/, rules {context}")


def check_only() -> int:
    py = venv_python()
    if not py.is_file():
        print(f"[setup] missing {py.relative_to(REPO_ROOT)} — run setup without --check")
        return 1
    core_ok = smoke_test(py) == 0 and sync_codex_stubs.check() == 0 and self_test(py)
    claude_bundles.report(claude_bundles.load_state())
    report_hosts()
    return readiness(py, core_ok, fonts_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create .venv, install dependencies, fonts and optional tools, sync the "
                    "Claude/Codex/Gemini skill sets, and verify with a self-test deck.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--recreate", action="store_true",
                        help="delete and rebuild .venv from scratch")
    parser.add_argument("--skip-fonts", action="store_true",
                        help="do not install the bundled fonts")
    parser.add_argument("--skip-extras", action="store_true",
                        help="do not install playwright / OfficeCLI / Codex CLI (or Node.js)")
    parser.add_argument("--skip-claude-bundles", action="store_true",
                        help="do not build the claude.ai chat skill / Claude Design bundles")
    parser.add_argument("--check", action="store_true",
                        help="verify an existing setup (self-test deck included) without installing")
    parser.add_argument("--deps-if-changed", action="store_true",
                        help="re-install requirements only if they changed (git hooks)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    if sys.version_info < MIN_PYTHON:
        print(f"[setup] Python {'.'.join(map(str, MIN_PYTHON))}+ required, "
              f"found {sys.version.split()[0]}", file=sys.stderr)
        return 1
    if args.deps_if_changed:
        return deps_if_changed()
    if args.check:
        return check_only()

    py = ensure_venv(args.recreate)
    if install_requirements(py):
        print("[setup] pip install failed — see the output above", file=sys.stderr)
        return 1
    fonts_ok = True
    if not args.skip_fonts and install_fonts(py):
        fonts_ok = False
        print("[setup] font install reported a problem — decks still build, "
              "but text metrics may differ; re-run install_fonts.py later",
              file=sys.stderr)
    if sync_stubs() or sync_codex_stubs.check():
        return 1
    if smoke_test(py):
        return 1
    enable_python_utf8()
    restart = install_extras(py) if not args.skip_extras else False
    if not args.skip_claude_bundles:
        build_claude_bundles()
        install_git_hooks()
    core_ok = self_test(py)
    report_hosts()
    return readiness(py, core_ok, fonts_ok, restart)


if __name__ == "__main__":
    raise SystemExit(main())
