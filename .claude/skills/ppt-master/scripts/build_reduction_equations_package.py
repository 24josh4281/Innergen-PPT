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
        AGENTS.md, CHATGPT.md    Codex entry, ChatGPT sandbox adapter
        dist/<name>.zip          Claude skill ZIP (claude.ai upload)
        dist/<name>-chatgpt/     ChatGPT ZIP, project instructions, guide

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
EDITOR = ["server.py", "start_equation_editor.ps1", "serve_tailscale.ps1","static/index.html", "static/app.js", "static/style.css"]
# (text in the repo SKILL.md, replacement in the package). Each must exist, so a
# SKILL.md edit that breaks the rewrite fails the build instead of shipping repo paths.
SKILL_REWRITES = [
    ("도구 위치: `.claude/skills/ppt-master/scripts/`. `.venv`가 있으면 `.venv\\Scripts\\python.exe`로 실행한다.",
     "도구 위치: 이 스킬 폴더의 `scripts/`(아래 명령의 스크립트는 모두 이 폴더 기준). 실행 환경별 준비:\n\n"
     "- **내 PC (Claude Code·Codex)**: 처음 한 번 `setup.ps1`(Windows) 또는 `sh setup.sh`로 `.venv`를 만들고 그 Python으로 실행한다.\n"
     "- **claude.ai 채팅·Cowork**: 설치 단계는 건너뛴다. `python-pptx`가 없을 때만 `pip install python-pptx`. "
     "결과 파일은 `/mnt/user-data/outputs/`에 저장해 링크로 준다. 웹 편집기(1장 7단계)는 쓸 수 없으니 수식은 LaTeX로, "
     "인자는 채팅 표로 보여 주고 고칠 점을 받는다.\n"
     "- **ChatGPT**: `CHATGPT.md`를 먼저 읽고 그 바꿔 읽기 표를 따른다."),
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

| 쓰는 곳 | 방법 |
|---|---|
| Claude Code (모든 프로젝트) | `git clone <이 저장소> %USERPROFILE%\\.claude\\skills\\reduction-equations` 후 그 폴더에서 `setup.ps1` |
| Codex CLI (GPT) | `git clone <이 저장소> %USERPROFILE%\\.codex\\skills\\reduction-equations` 후 `setup.ps1`. 이 저장소 안에서 Codex를 열면 `AGENTS.md`도 읽습니다 |
| claude.ai 채팅·Cowork | 설정 → 기능 → 스킬에서 `reduction-equations.zip` 업로드 |
| ChatGPT 채팅·프로젝트 | `dist/reduction-equations-chatgpt/설치방법.md` — 같은 폴더의 ZIP과 프로젝트 지침 |

## 팀용 웹 편집기 (Tailscale 주소)

항상 켜 두는 PC에 Tailscale을 설치·로그인한 뒤, 이 저장소를 받아 `setup.ps1`을 실행하고 아래를 한 번 실행합니다.

```
powershell -ExecutionPolicy Bypass -File scripts\\equation_editor\\serve_tailscale.ps1 -Install
```

같은 Tailscale 네트워크의 누구나 `https://<PC이름>.<tailnet>.ts.net:10001/`에서 수식을 입력하고
**Word 내보내기·PPT 내보내기** 버튼으로 바로 받습니다. 그 PC에 로그인할 때마다 자동으로 켜집니다.
포트는 `-HttpsPort 10002`처럼 바꿀 수 있고, 해제는 `-Uninstall`입니다.

ZIP은 `dist/` 폴더에 있습니다. GitHub에서 파일을 열고 다운로드 버튼(Download raw file)을 누르면 됩니다.

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

AGENTS_MD = """# AGENTS.md

이 저장소는 감축사업 수식·모니터링 인자 자동화 스킬이다. 작업 절차는 `SKILL.md`가 정한다.
Codex(GPT)는 수식·모니터링 인자·기호 정의표·데이터/인자 표 요청을 받으면 `SKILL.md`를 먼저 읽고 그대로 따른다.

- Python: `.venv`가 없으면 `setup.ps1`(Windows) 또는 `sh setup.sh`를 먼저 실행하고, 이후 `.venv`의 Python으로 실행한다.
- 수식은 Word·PPT 네이티브 Office Math로만 만든다. 그림·일반 텍스트 수식은 결과물이 아니다.
- 원문에 없는 계수·값·출처를 지어내지 않는다.
- 이 저장소는 Slide Master에서 생성된다. 여기서 고친 코드는 다음 생성 때 덮어써진다.
"""

GPT_PACKAGE = "reduction-equations-chatgpt.zip"
GPT_INSTRUCTIONS_FILE = "chatgpt-project-instructions.txt"
# ChatGPT project instructions accept about 8,000 characters.
MAX_INSTRUCTION_CHARS = 8000

GPT_INSTRUCTIONS = """당신은 감축사업(온실가스 감축 방법론·사업계획서·모니터링 보고서·인증위원회 발표) 수식·모니터링 인자 작성 도우미다.

프로젝트 파일 reduction-equations-chatgpt.zip에 도구가 들어 있다. 수식·모니터링 인자·모니터링 계획·기호 정의표·데이터/인자 표 요청이 오면:
1. Python 도구로 ZIP을 /mnt/data/re 에 풀고 reduction-equations/CHATGPT.md, 이어서 reduction-equations/SKILL.md를 읽는다. 그 절차를 따른다.
2. 수식은 반드시 Word·PowerPoint에서 편집 가능한 수식(Office Math)으로 만든다. 그림·일반 텍스트 수식은 결과물이 아니다.
3. 서식은 사용자가 말한 것을 따른다(KCS = 대한상의 탄소감축인증센터, 환경부 = 환경부 외부사업 방법론). 말하지 않았으면 첨부 원본의 서식을, 원본도 없으면 KCS로 만든 뒤 바꿀 수 있다고 알린다.
4. 원문에 없는 계수·값·출처를 지어내지 않는다. 빈칸은 비워 두고 경고로 알린다.
5. 결과는 Word(.docx)와 PowerPoint(.pptx) 다운로드 링크로 주고, 수식 수·인자 수·남은 경고를 짧게 보고한다.

ZIP이 보이지 않으면 이 채팅에 reduction-equations-chatgpt.zip을 다시 첨부해 달라고 한다.
"""

CHATGPT_MD = """# ChatGPT에서 실행하기

`SKILL.md`를 ChatGPT의 Python 도구에서 실행할 때 바꿔 읽을 점이다. 여기 없는 내용은 `SKILL.md`를 따른다.

## 준비 (채팅마다 한 번)

```python
import glob, os, subprocess, sys, zipfile
src = glob.glob('/mnt/data/reduction-equations-chatgpt*.zip')[0]
zipfile.ZipFile(src).extractall('/mnt/data/re')
TOOLS = '/mnt/data/re/reduction-equations/scripts'
ENV = dict(os.environ, PYTHONUTF8='1')
import pptx  # 없으면 "코드 실행 환경에 python-pptx가 없다"고 알리고 멈춘다

def run(script, *args):
    p = subprocess.run([sys.executable, f'{TOOLS}/{script}', *args], capture_output=True, text=True, env=ENV)
    print(p.stdout, p.stderr)
    return p.returncode
```

## 바꿔 읽기

| SKILL.md | ChatGPT |
|---|---|
| `python monitoring_plan.py import 원본 -o plan.json` | `run('monitoring_plan.py', 'import', '/mnt/data/<첨부 파일>', '-o', '/mnt/data/work/plan.json')` |
| `projects/<사업>/notes/` | `/mnt/data/work/` |
| `projects/<사업>/exports/` | `/mnt/data/exports/` |
| 사용자가 준 원본 | 채팅에 첨부된 `/mnt/data/<파일명>` |
| 빠른 텍스트 `plan.txt` | `/mnt/data/work/plan.txt`에 써서 `from-text` |
| `setup.ps1`, `.venv` | 쓰지 않는다 |
| 1장 6단계 렌더 확인 | `soffice`가 있으면 PDF로 바꿔 페이지 이미지를 보고, 없으면 "렌더 미확인"이라고 보고한다 |
| 1장 7단계 웹 편집기 | 쓸 수 없다. 수식은 LaTeX(`$$…$$`)로, 인자는 채팅 표로 보여 주고 고칠 점을 받아 계획 파일을 고친 뒤 새 버전으로 다시 낸다 |

## 결과 전달

- 파일은 `/mnt/data/exports/`에 새 버전 이름(`_v1`, `_v2` …)으로 저장하고 다운로드 링크(`sandbox:/mnt/data/exports/<파일명>`)를 준다.
- 수식 수, 인자 수(산출·모니터링·고정), 남은 WARN, 서식, `verify` 수식 개수를 짧게 보고한다.
"""

GPT_GUIDE = """# ChatGPT용 감축사업 수식 도구 설치

설치 없이 ChatGPT 안에서 감축사업 수식·모니터링 인자 표를 Word·PowerPoint 편집 가능 수식으로 만드는 패키지입니다.

## 들어 있는 것

| 파일 | 쓰는 곳 |
|---|---|
| `reduction-equations-chatgpt.zip` | 프로젝트 파일로 올리거나 채팅에 첨부 |
| `chatgpt-project-instructions.txt` | 프로젝트 지침에 붙여 넣기 |

## 준비

- ChatGPT 설정에서 **코드 실행(데이터 분석·Code interpreter)** 이 켜져 있어야 합니다.
- Work(Business·Enterprise) 계정은 관리자가 이 기능을 꺼 두었을 수 있습니다.

## 설치 (프로젝트 방식, 권장)

1. ChatGPT 왼쪽 메뉴에서 **새 프로젝트**를 만듭니다. 이름 예: `감축사업 수식`.
2. 프로젝트 **지침(Instructions)** 에 `chatgpt-project-instructions.txt` 내용을 그대로 붙여 넣습니다.
3. 프로젝트 **파일**에 `reduction-equations-chatgpt.zip`을 올립니다.
4. 프로젝트 안에서 새 채팅을 열고 요청합니다. 예: "이 방법론 수식이랑 모니터링 인자 표 KCS 서식으로 워드·PPT 만들어줘" (원본 .docx·.pptx 첨부)

AI가 "ZIP이 보이지 않는다"고 하면 그 채팅에 ZIP을 한 번 더 첨부합니다.

## 설치 없이 한 번만 쓰기

새 채팅에 ZIP을 첨부하고 지침 내용을 첫 메시지로 붙여 넣은 뒤 요청을 이어서 적습니다.

## 한계

- 웹 편집기는 ChatGPT에서 쓸 수 없습니다. 수식과 표를 채팅에서 보여 주면 고칠 점을 말로 알려 주세요.
- 계산값·계수의 정확성은 검증하지 않습니다. 수식 구조와 기호·단위 대응만 확인합니다.
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
    put("AGENTS.md", AGENTS_MD)
    put("CHATGPT.md", CHATGPT_MD)
    put("examples/plan_example.txt", example_text())
    for name in SCRIPTS:
        put(f"scripts/{name}", (_SCRIPTS_DIR / name).read_bytes())
    for rel in EDITOR:
        data = (_SCRIPTS_DIR / "equation_editor" / rel).read_bytes()
        if rel.endswith(".ps1") and not data.startswith(b"\xef\xbb\xbf"):
            data = b"\xef\xbb\xbf" + data      # Windows PowerShell 5.1 needs the BOM for Korean text
        put(f"scripts/equation_editor/{rel}", data)
    return written


# Top-level files each archive leaves out: the Claude skill ZIP has no GPT adapter,
# and the ChatGPT ZIP runs in a sandbox with no setup or repository files.
CLAUDE_SKIP = {"AGENTS.md", "CHATGPT.md", ".gitignore", ".gitattributes"}
GPT_SKIP = {"AGENTS.md", "setup.ps1", "setup.sh", "README.md", ".gitignore", ".gitattributes"}


def write_zip(tree: Path, files: list[Path], archive: Path, skip: set[str]) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    tmp = archive.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(files):
            rel = path.relative_to(tree)
            if rel.parts[0] not in skip:
                z.write(path, f"{NAME}/{rel.as_posix()}")
    tmp.replace(archive)


def write_gpt_package(tree: Path, files: list[Path], out_dir: Path) -> Path:
    if len(GPT_INSTRUCTIONS) > MAX_INSTRUCTION_CHARS:
        raise SystemExit(f"ChatGPT instructions are {len(GPT_INSTRUCTIONS)} characters; "
                         f"ChatGPT accepts {MAX_INSTRUCTION_CHARS}")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_zip(tree, files, out_dir / GPT_PACKAGE, GPT_SKIP)
    (out_dir / GPT_INSTRUCTIONS_FILE).write_text(GPT_INSTRUCTIONS, encoding="utf-8")
    (out_dir / "설치방법.md").write_text(GPT_GUIDE, encoding="utf-8")
    return out_dir


def check_gpt_zip(archive: Path) -> None:
    """Unpack the ChatGPT ZIP the way CHATGPT.md does and run it without setup."""
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(archive).extractall(tmp)
        tools = Path(tmp) / NAME / "scripts"
        plan, out = Path(tmp) / "plan.json", Path(tmp) / "gpt.docx"
        for args in (["monitoring_plan.py", "from-text", str(Path(tmp) / NAME / "examples" / "plan_example.txt"),
                      "-o", str(plan)],
                     ["monitoring_plan.py", "docx", str(plan), "-o", str(out)],
                     ["office_equations.py", "verify", str(out), "--expect", "3"]):
            proc = subprocess.run([sys.executable, "-I", "-X", "utf8", str(tools / args[0]), *args[1:]],
                                  capture_output=True, text=True, encoding="utf-8")
            if proc.returncode:
                raise SystemExit(f"ChatGPT ZIP check failed: {' '.join(args)}\n{proc.stdout}\n{proc.stderr}")
        print(f"  ok  ChatGPT ZIP unpacks and runs ({archive.name})")


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
    parser.add_argument("--zip", type=Path, default=None, help="skill ZIP path (default: <out>/dist/<name>.zip)")
    parser.add_argument("--gpt-out", type=Path, default=None,
                        help="ChatGPT package folder (default: <out>/dist/reduction-equations-chatgpt)")
    parser.add_argument("--check", action="store_true", help="run the packaged scripts end to end")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    out = args.out.resolve()
    if out == REPO or REPO in out.parents and ".claude" in out.parts:
        raise SystemExit("--out must not point inside the repository's skill folders")
    files = build_tree(out)
    archive = (args.zip or out / "dist" / f"{NAME}.zip").resolve()
    write_zip(out, files, archive, CLAUDE_SKIP)
    gpt_dir = write_gpt_package(out, files, (args.gpt_out or out / "dist" / f"{NAME}-chatgpt").resolve())
    print(f"OK  package {out}  ({len(files)} files)")
    print(f"OK  skill zip {archive}")
    print(f"OK  ChatGPT package {gpt_dir}")
    if args.check:
        self_check(out)
        check_gpt_zip(gpt_dir / GPT_PACKAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
