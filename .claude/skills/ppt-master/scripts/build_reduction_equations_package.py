#!/usr/bin/env python3
"""
PPT Master - Standalone Reduction-Equations Package

Builds the `reduction-equations` skill as a self-contained package from this
repository, so it can live in its own git repository and be uploaded to
claude.ai / Claude Code / Codex as a skill without the rest of PPT Master.
Slide Master stays the single source: edit the scripts and SKILL.md here, then
rebuild; never edit the generated copy.

Package layout (folder and ZIP):
    reduction-equations/
        SKILL.md                 paths rewritten to the package
        README.md                Korean install/usage guide
        requirements.txt         python-pptx
        setup.ps1, setup.sh      create .venv and install requirements
        scripts/                 math_shorthand, monitoring_plan, omml_math,
                                 office_equations, docx_equations,
                                 console_encoding, server_common,
                                 equation_editor/ (web editor)
        examples/plan_example.txt

Usage:
    python3 scripts/build_reduction_equations_package.py [--out DIR] [--zip FILE] [--check]

Examples:
    python3 .claude/skills/ppt-master/scripts/build_reduction_equations_package.py --check
    python3 .claude/skills/ppt-master/scripts/build_reduction_equations_package.py --out ../reduction-equations --check

Dependencies:
    None (only uses standard library); --check also needs python-pptx
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

REPO = _SCRIPTS_DIR.parents[3]
SKILL_SRC = REPO / ".claude" / "skills" / "reduction-equations" / "SKILL.md"
NAME = "reduction-equations"
SCRIPTS = ["math_shorthand.py", "monitoring_plan.py", "omml_math.py", "office_equations.py",
           "docx_equations.py", "console_encoding.py", "server_common.py"]
EDITOR = ["server.py", "start_equation_editor.ps1", "static/index.html", "static/app.js", "static/style.css"]
# (text in the repo SKILL.md, replacement in the package). Each must exist, so a
# SKILL.md edit that breaks the rewrite fails the build instead of shipping repo paths.
SKILL_REWRITES = [
    ("도구 위치: `.claude/skills/ppt-master/scripts/`. `.venv`가 있으면 `.venv\\Scripts\\python.exe`로 실행한다.",
     "도구 위치: 이 스킬 폴더의 `scripts/`. 처음 한 번 `setup.ps1`(Windows) 또는 `sh setup.sh`로 `.venv`를 만들고, "
     "`.venv`가 있으면 그 Python으로 실행한다."),
    ("PPT는 `pptx_safe_render.py`(PowerPoint를 닫지 않는 렌더)로, Word는 PDF로 내보내 페이지를 본다.",
     "PPT와 Word를 PowerPoint·Word(또는 LibreOffice)에서 PDF로 내보내 페이지를 본다."),
    ("`powershell -ExecutionPolicy Bypass -File .claude/skills/ppt-master/scripts/equation_editor/start_equation_editor.ps1 [--plan plan.json]`",
     "`powershell -ExecutionPolicy Bypass -File scripts/equation_editor/start_equation_editor.ps1 [--plan plan.json]`"
     " (macOS·Linux: `.venv/bin/python scripts/equation_editor/server.py`)"),
]

REQUIREMENTS = "python-pptx>=0.6.21\n"

SETUP_PS1 = """$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) { & py -3 -m venv .venv } else { & python -m venv .venv }
& .\\.venv\\Scripts\\python.exe -m pip install --upgrade pip --quiet
& .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt --quiet
$env:PYTHONUTF8 = '1'
& .\\.venv\\Scripts\\python.exe scripts\\monitoring_plan.py check examples\\plan_example.txt
Write-Host ''
Write-Host '설치 완료. 편집기 실행: powershell -ExecutionPolicy Bypass -File scripts\\equation_editor\\start_equation_editor.ps1'
"""

SETUP_SH = """#!/bin/sh
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip --quiet
.venv/bin/python -m pip install -r requirements.txt --quiet
PYTHONUTF8=1 .venv/bin/python scripts/monitoring_plan.py check examples/plan_example.txt
echo ""
echo "설치 완료. 편집기 실행: .venv/bin/python scripts/equation_editor/server.py"
"""

GITIGNORE = ".venv/\n__pycache__/\n*.pyc\nexports/\n*.docx\n*.pptx\n!examples/*.docx\n!examples/*.pptx\n"

README = """# 감축사업 수식·모니터링 인자 자동화 (reduction-equations)

대충 적은 감축사업 산정식을 **Word·PowerPoint에서 바로 고칠 수 있는 수식(Office Math)** 으로 바꾸고,
기호·정의·단위 표, 모니터링 요약표, 인자별 `데이터/인자` 표를 제출 서식에 맞춰 자동으로 만듭니다.

- 서식: 대한상의 탄소감축인증센터(KCS), 환경부 외부사업 방법론
- 출력: Word(.docx), PowerPoint(.pptx) — 수식·기호는 모두 편집 가능한 수식 개체
- 가져오기: 기존 방법론·사업계획서(.docx), 인증위원회 발표(.pptx)의 수식과 표
- 웹 편집기: 입력하는 대로 수식 미리보기, 인자 표 편집, Word·PPT 내보내기

> 이 저장소는 Slide Master(`.claude/skills/ppt-master/scripts/build_reduction_equations_package.py`)에서
> 생성됩니다. 수정은 Slide Master에서 하고 다시 생성하세요.

## 설치

Windows: `powershell -ExecutionPolicy Bypass -File setup.ps1`
macOS·Linux: `sh setup.sh`

Python 3.10 이상이 필요합니다. `.venv`를 만들고 `python-pptx`를 설치한 뒤 예시를 검사합니다.

## 스킬로 쓰기

- **Claude Code / Codex**: 이 폴더를 `.claude/skills/reduction-equations/`(Codex는 `.codex/skills/`)에 두면 자동 인식됩니다.
- **claude.ai**: 설정 → 기능 → 스킬에서 `reduction-equations.zip`을 올립니다.

"감축사업 수식 만들어줘", "모니터링 인자 표 KCS 서식으로", "환경부 외부사업 서식으로 워드 만들어줘",
"이 방법론 수식 가져와서 PPT로" 같은 요청에 쓰입니다.

## 명령

```
python scripts/monitoring_plan.py from-text examples/plan_example.txt -o plan.json
python scripts/monitoring_plan.py import 방법론.docx -o plan.json
python scripts/monitoring_plan.py check plan.json
python scripts/monitoring_plan.py docx plan.json -o exports/수식_모니터링계획_v1.docx
python scripts/monitoring_plan.py pptx plan.json -o exports/수식_인자_v1.pptx
python scripts/office_equations.py verify exports/수식_모니터링계획_v1.docx
```

서식은 계획 파일의 `options.form`으로 고릅니다: `"kcs"`(기본) 또는 `"moe"`(환경부 외부사업).

## 빠른 입력 규칙

```
# 베이스라인 배출량
> 섹션 설명
BEy = BE_MAT,y + BE_ENE,y
BE_MFG,y = sum_j((Q_PJ,j,y * QW_BL,j) * DHC_PJ,j/DHC_BL,j * EF_BL,MFG,j)
Q_PJ,j,y | y년도 사업필터 순판매량 | 개/년 | 모니터링 | 값
```

| 입력 | 결과 |
|---|---|
| `BE_MFG,y`, `Q_{PJ, j}` | 아래첨자 |
| `BEy`, `n0` | `BE_y`, `n_0` |
| `a * b` | × |
| `A/B` / `a × b / c` | 분수 (빈칸 있는 /는 왼쪽 곱 전체가 분자) |
| `x^2`, `(…)^x_a` | 위첨자 |
| `sum_j(…)` | Σ |
| `bar(DP)_BL,a` | 윗줄 기호 |
| `(식 3)` | 식 번호 |

## 확인 범위와 한계

- 수식 구조, 기호·단위 대응, 수식 개체 생성은 확인합니다. 계산값·계수의 정확성은 확인하지 않습니다.
- 환경부 서식의 표 머리말은 외부사업 방법론의 일반 구성을 따릅니다. 제출 전 최신 공식 서식과 대조하세요.
  다르면 `options.labels`로 해당 문구만 바꿀 수 있습니다.
"""


def skill_text() -> str:
    text = SKILL_SRC.read_text(encoding="utf-8")
    for old, new in SKILL_REWRITES:
        if old not in text:
            raise SystemExit(f"SKILL.md rewrite target missing (update SKILL_REWRITES): {old[:60]}...")
        text = text.replace(old, new)
    if ".claude/skills/ppt-master" in text:
        raise SystemExit("SKILL.md still references .claude/skills/ppt-master after rewriting")
    return text


def example_text() -> str:
    from monitoring_plan import EXAMPLE_TEXT
    return EXAMPLE_TEXT


def build_tree(dest: Path) -> list[Path]:
    """Write the package into dest (kept: .git and anything not generated)."""
    written: list[Path] = []

    def put(rel: str, data: str | bytes, bom: bool = False) -> None:
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = ("﻿" if bom else "") + data
            path.write_bytes(data.encode("utf-8"))
        else:
            path.write_bytes(data)
        written.append(path)

    put("SKILL.md", skill_text())
    put("README.md", README)
    put("requirements.txt", REQUIREMENTS)
    put("setup.ps1", SETUP_PS1, bom=True)
    put("setup.sh", SETUP_SH.replace("\r\n", "\n"))
    put(".gitignore", GITIGNORE)
    put(".gitattributes", "*.sh text eol=lf\n*.ps1 text eol=crlf\n")
    put("examples/plan_example.txt", example_text())
    for name in SCRIPTS:
        put(f"scripts/{name}", (_SCRIPTS_DIR / name).read_bytes())
    for rel in EDITOR:
        data = (_SCRIPTS_DIR / "equation_editor" / rel).read_bytes()
        if rel.endswith(".ps1") and not data.startswith(b"\xef\xbb\xbf"):
            data = b"\xef\xbb\xbf" + data      # Windows PowerShell 5.1 needs the BOM for Korean text
        put(f"scripts/equation_editor/{rel}", data)
    return written


def write_zip(tree: Path, files: list[Path], archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    tmp = archive.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            z.write(path, f"{NAME}/{path.relative_to(tree).as_posix()}")
    tmp.replace(archive)


def self_check(tree: Path) -> None:
    """Run the packaged scripts from a clean copy: example -> docx + pptx -> verify."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / NAME
        shutil.copytree(tree, work, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
        env_py = [sys.executable, "-I", "-X", "utf8"]
        plan = Path(tmp) / "plan.json"
        steps = [
            ["scripts/monitoring_plan.py", "from-text", "examples/plan_example.txt", "-o", str(plan)],
            ["scripts/monitoring_plan.py", "docx", str(plan), "-o", str(Path(tmp) / "out.docx")],
            ["scripts/monitoring_plan.py", "pptx", str(plan), "-o", str(Path(tmp) / "out.pptx")],
            ["scripts/office_equations.py", "verify", str(Path(tmp) / "out.docx"), "--expect", "3"],
            ["scripts/office_equations.py", "verify", str(Path(tmp) / "out.pptx"), "--expect", "3"],
        ]
        for step in steps:
            proc = subprocess.run(env_py + step, cwd=work, capture_output=True, text=True, encoding="utf-8")
            if proc.returncode:
                raise SystemExit(f"self-check failed: {' '.join(step)}\n{proc.stdout}\n{proc.stderr}")
            print(f"  ok  {' '.join(step[:2])} {proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ''}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the standalone reduction-equations skill package.")
    parser.add_argument("--out", type=Path, default=REPO / "OUTPUTS" / NAME,
                        help="package folder (e.g. the standalone git repository); .git is kept")
    parser.add_argument("--zip", type=Path, default=None, help="skill ZIP path (default: <out>/../<name>.zip)")
    parser.add_argument("--check", action="store_true", help="run the packaged scripts end to end")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    out = args.out.resolve()
    if out == REPO or REPO in out.parents and ".claude" in out.parts:
        raise SystemExit("--out must not point inside the repository's skill folders")
    files = build_tree(out)
    archive = (args.zip or out.parent / f"{NAME}.zip").resolve()
    write_zip(out, files, archive)
    print(f"OK  package {out}  ({len(files)} files)")
    print(f"OK  skill zip {archive}")
    if args.check:
        self_check(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
