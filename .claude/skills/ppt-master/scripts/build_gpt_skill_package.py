#!/usr/bin/env python3
"""
PPT Master - GPT Chat and Work Skill Package

Reuse the repository chat export closure and equation tools, with OpenAI-host
entrypoints and explicit capability boundaries. Write a new versioned output
folder; never replace existing distributions or change discovery stubs.
Templates and runtime guidance live in gpt_skill/.

Usage:
    python3 scripts/build_gpt_skill_package.py --out <new-directory>

Examples:
    python3 .claude/skills/ppt-master/scripts/build_gpt_skill_package.py --out OUTPUTS/gpt-skills-20261027_v1

Dependencies:
    Standard library; existing build_chat_skill import-closure discovery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from build_chat_skill import CHAT_SRC, REPO_ROOT, build as build_chat  # noqa: E402
from build_reduction_equations_package import SCRIPTS as EQUATION_SCRIPTS  # noqa: E402
from build_reduction_equations_package import example_text  # noqa: E402
from console_encoding import configure_utf8_stdio  # noqa: E402

SOURCE = _SCRIPTS_DIR / "gpt_skill"
NAMES = ("innergen-deck", "reduction-equations")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def git_text(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], check=True,
                          capture_output=True, encoding="utf-8").stdout.strip()


def archive_tree(root: Path, output: Path, prefix: str = "") -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError(f"Linked package resource: {path}")
            archive.write(path, prefix + path.relative_to(root).as_posix())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Corrupt archive: {output}")
        count = len(archive.namelist())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    write_text(output.with_suffix(".zip.sha256"), f"{digest}  {output.name}")
    return {"file": output.name, "bytes": output.stat().st_size, "files": count, "sha256": digest}


def deck_workflow() -> str:
    text = (CHAT_SRC / "SKILL.chat.md").read_text(encoding="utf-8")
    body = text[text.index("## 1. Brief"):text.index("## Limits of this edition")]
    end_brief = body.index("## 2. Read the rules")
    brief = body[:end_brief]
    brief = brief.replace("and ask once for the rest:", "and state reasonable defaults for the rest:")
    brief = brief.replace('ask which type. Never alias the two.',
                          'infer the family from the task; ask only if the distinction materially affects the result.')
    body = brief + body[end_brief:]
    body = body.replace('`\n` breaks a cell line by meaning', '`\\n` breaks a cell line by meaning')
    return ("# Portable deck workflow\n\nRead `ENVIRONMENT.md` at the skill root first. "
            "Resolve all `references/`, `scripts/` and `${SKILL_DIR}` paths from that root. "
            "The root `SKILL.md` controls environment, scope, intake defaults and latest-rule precedence.\n\n" + body)


def equation_workflow() -> str:
    text = (REPO_ROOT / ".claude/skills/reduction-equations/SKILL.md").read_text(encoding="utf-8")
    text = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)
    text = text.replace("도구 위치: `.claude/skills/ppt-master/scripts/`. `.venv`가 있으면 `.venv\\Scripts\\python.exe`로 실행한다.",
                        "도구 위치: 이 스킬 폴더의 `scripts/`. 실행 환경은 루트 `ENVIRONMENT.md`를 따른다.")
    text = re.sub(r"7\. \*\*사용자가 직접 고치고 싶어 하면\*\*.*?(?=\n\n기존 Word)",
                  "7. 사용자가 고치고 싶어 하면 수식·인자 표를 채팅으로 보여 주고 계획 파일을 수정한다. "
                  "웹 편집기·상시 서비스는 이 패키지에 포함하지 않는다.", text, count=1, flags=re.S)
    text = text.replace("PPT는 `pptx_safe_render.py`(PowerPoint를 닫지 않는 렌더)로, Word는 PDF로 내보내 페이지를 본다.",
                        "사용 가능한 렌더러로 PPT·Word를 PDF로 내보내 페이지를 본다.")
    if ".claude/skills/ppt-master" in text:
        raise ValueError("Equation workflow still depends on repository paths")
    return text


def prepare_skill(skill: Path, kind: str, display: str, description: str) -> None:
    write_text(skill / "SKILL.md", (SOURCE / f"{kind}.md").read_text(encoding="utf-8"))
    shutil.copy2(SOURCE / "environment.md", skill / "ENVIRONMENT.md")
    shutil.copy2(SOURCE / "environment_check.py", skill / "scripts/environment_check.py")
    shutil.copy2(REPO_ROOT / "LICENSE", skill / "LICENSE")
    # JSON strings are also valid quoted YAML scalars, including Korean text.
    write_text(skill / "agents/openai.yaml", "interface:\n"
               f"  display_name: {json.dumps(display, ensure_ascii=False)}\n"
               f"  short_description: {json.dumps(description, ensure_ascii=False)}\n")


def build_package(out: Path, version: str) -> dict:
    out = out.resolve()
    if out.exists():
        raise ValueError("Output already exists; choose a new versioned directory.")
    if not out.is_relative_to(REPO_ROOT / "OUTPUTS"):
        raise ValueError("Use a new directory inside repository OUTPUTS.")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?", version):
        raise ValueError("Version must use semantic version format.")
    source_status = git_text("status", "--porcelain", "--untracked-files=all")
    out.mkdir(parents=True)
    # The existing builder only sees this fresh, owned directory: no prior bundle is removed.
    build_chat(out / "build-source")
    plugin = out / "work-plugin"
    skills = plugin / "skills"
    skills.mkdir(parents=True)
    deck = skills / NAMES[0]
    shutil.copytree(out / "build-source" / NAMES[0], deck)
    prepare_skill(deck, "deck", "이너젠·이너캐리 PPT", "자료를 이너젠·이너캐리 장표로 구성하고 편집 가능한 PPTX로 생성합니다")
    write_text(deck / "references/deck-workflow.md", deck_workflow())
    shutil.copy2(SOURCE / "capabilities.md", deck / "references/capabilities.md")
    write_text(deck / "requirements.txt", "python-pptx\nlxml\nPillow\nopenpyxl\nXlsxWriter\nPyYAML")
    equations = skills / NAMES[1]
    (equations / "scripts").mkdir(parents=True)
    for name in EQUATION_SCRIPTS:
        shutil.copy2(_SCRIPTS_DIR / name, equations / "scripts" / name)
    prepare_skill(equations, "equations", "감축사업 수식·모니터링", "감축사업 수식과 인자 표를 Word·PPT에서 편집 가능한 Office Math로 만듭니다")
    write_text(equations / "references/equation-workflow.md", equation_workflow())
    write_text(equations / "examples/plan_example.txt", example_text())
    write_text(equations / "requirements.txt", "python-pptx")
    manifest = {"name": "slide-master-gpt", "version": version,
                "description": "INNerGEN/INNerCarry editable presentations and GHG reduction equations.",
                "license": "MIT"}
    write_text(plugin / "plugin.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    provenance = {"source_commit": git_text("rev-parse", "HEAD"),
                  "source_branch": git_text("branch", "--show-current"),
                  "created_utc": datetime.now(timezone.utc).isoformat(),
                  "working_tree_changes_included": bool(source_status),
                  "source_status": source_status,
                  "package_version": version,
                  "excluded": ["client inputs", "project outputs", "credentials", "git history", "virtualenv"],
                  "runtime_files": []}
    for path in sorted(plugin.rglob("*")):
        if path.is_file():
            provenance["runtime_files"].append({"path": path.relative_to(plugin).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    write_text(plugin / "package-manifest.json", json.dumps(provenance, ensure_ascii=False, indent=2))
    results = [archive_tree(plugin, out / "Work/slide-master-work-plugin.zip")]
    for name in NAMES:
        results.append(archive_tree(skills / name, out / "Work" / f"{name}.zip", f"{name}/"))
    chat = out / "chat-runtime" / "slide-master-gpt"
    shutil.copytree(plugin, chat)
    write_text(chat / "START.md", "# Slide Master for ChatGPT\n\n"
               "For a named-style PPTX, read `skills/innergen-deck/SKILL.md`. "
               "For formulas and monitoring tables, read `skills/reduction-equations/SKILL.md`. "
               "Each skill has an ENVIRONMENT.md adapter. Do not load both full workflows unless needed.\n")
    results.append(archive_tree(chat, out / "ChatGPT/slide-master-chatgpt.zip", "slide-master-gpt/"))
    instructions = """이 프로젝트는 Slide Master의 이너젠·이너캐리 PPT 제작과 감축수식 도구를 사용한다.
1. 장표 또는 감축수식 파일 생성 요청이면 Python 실행 도구에서 첨부한 slide-master-chatgpt.zip을 찾는다. ZIP이 보이지 않으면 이 채팅에 다시 첨부해 달라고 요청한다. 다른 ZIP을 임의로 고르지 않는다.
2. 새 작업 폴더에 압축을 풀고 slide-master-gpt/START.md를 읽는다. PPT는 skills/innergen-deck/SKILL.md, 수식·모니터링 인자 표는 skills/reduction-equations/SKILL.md를 읽고, 해당 ENVIRONMENT.md와 연결된 절차를 따른다. 기존 작업 폴더·원본을 덮어쓰지 않는다.
3. PPT는 패키지 svg_to_pptx.py로 편집 가능한 PPTX로 만든다. 감축수식은 Word·PPT에서 편집 가능한 Office Math로 만든다. 사용자가 요청한 형식만 만든다.
4. 일반 설정은 요청에서 추론하고 가정을 짧게 알린다. 개요 표를 보여 주고 계속 진행하되 사용자가 사전 확인을 요청했거나 필수 사실이 없으면 그 부분을 확인한다.
5. 출처·원본 수치·단위·날짜를 보존한다. 참고 템플릿의 고객명·수치·스크린샷을 새 사실로 쓰지 않는다. 예시는 예시로 표시한다.
6. 해당 스킬의 검사를 실행하고 오류를 해결한다. 남은 경고와 실제 렌더 확인 여부를 알린다. 내려받을 수 있는 출력 폴더에 새 버전으로 저장하고 실제 파일 링크를 준다.
7. 기존 PPT 양식 그대로 채우기·1:1 재디자인·음성·전환·확인 UI 등 저장소 전용 기능은 패키지 capabilities.md의 한계를 알린다. 지원하지 않는 작업을 조용히 다른 제작 방식으로 바꾸지 않는다.
"""
    write_text(out / "ChatGPT/project-instructions.txt", instructions)
    guide = """# Slide Master GPT 채팅·Work 패키지

현재 작업 폴더의 소스와 미커밋 수정을 반영한 스냅샷입니다. 원본·기존 패키지는 보존했습니다.

## 1. GPT 일반 채팅·프로젝트

1. `ChatGPT/slide-master-chatgpt.zip`을 새 채팅에 첨부합니다.
2. `ChatGPT/project-instructions.txt`를 첫 메시지 또는 프로젝트 지침에 붙여 넣습니다.
3. 원본 자료와 함께 요청합니다. 코드 실행·파일 생성 기능이 필요합니다.
4. 프로젝트 파일이 Python 도구에서 보이지 않으면 같은 ZIP을 현재 채팅에 다시 첨부합니다.

예: “첨부 자료로 이너젠 사업 소개 스타일 제안서 10쪽 만들어줘.”
예: “이 산정식을 KCS 서식의 편집 가능한 Word 수식과 모니터링 인자 표로 만들어줘.”

## 2. Work 스킬

| 파일 | 용도 |
|---|---|
| `Work/innergen-deck.zip` | PPT 제작 스킬 단독 패키지 |
| `Work/reduction-equations.zip` | 수식·모니터링 스킬 단독 패키지 |
| `Work/slide-master-work-plugin.zip` | 두 스킬을 묶은 배포용 플러그인: 루트 plugin.json + skills/ |

Skills의 새 스킬·업로드 기능이 제공되는 계정에서는 필요한 단독 ZIP을 등록하고,
새 Work 채팅에서 `@`로 해당 스킬을 선택합니다. UI와 허용 방식은 계정·관리 정책에 따라 다릅니다.
업로드 UI가 없으면 GPT 채팅 방식을 쓰거나 관리자에게 등록을 요청합니다.
플러그인 ZIP은 배포/등록용이며 일반 채팅 첨부만으로 설치되지는 않습니다.
계정 설치·관리자 배포·외부 업로드는 이번 작업에서 실행하지 않았습니다.

## 3. 포함 범위

- 이너젠 사업 소개·교육/강의·이너캐리 3개 계열의 템플릿, 최신 v34 규칙, 디자인 예시.
- 편집 가능한 PPTX 내보내기와 SVG·구성·스토리·여백 검사.
- 감축수식의 네이티브 Office Math, 기호표·모니터링 표, DOCX/PPTX 가져오기·내보내기.
- 의존성/글꼴 확인 도구, 라이선스, 소스/파일 해시 장부.

## 4. 저장소 전체와의 차이 및 확인할 점

원본 PPT 디자인 유지 채우기, 1:1 재디자인, 오디오·전환, 브라우저 확인 UI,
라이브 미리보기, 팀 웹 편집기는 전체 저장소 환경이 필요합니다.
기본적인 새 덱은 flat 구조이며 개별 텍스트·도형은 편집 가능합니다.
클라이언트 입력·완성 프로젝트·비밀정보·Git 이력은 배포물에 넣지 않았습니다.
글꼴 파일은 포함하지 않았으므로 PPT를 여는 PC에 Pretendard·IBM Plex Sans KR이 필요합니다.
렌더러가 없는 실행 환경은 구조 검사만 가능하며 “렌더 미확인”으로 보고해야 합니다.
수식 검사는 구조·기호·단위 대응 검사이며 배출량 계산값·계수 정확성 보증이 아닙니다.
실제 ChatGPT/Work 계정 업로드와 그 계정의 실행 환경은 별도 확인이 필요합니다.

## 5. 공식 형식 참고

- https://learn.chatgpt.com/docs/build-skills
- https://developers.openai.com/plugins/build/plugins

재생성은 저장소의 `.claude/skills/ppt-master/scripts/build_gpt_skill_package.py`에
새 `--out OUTPUTS/<새 버전 폴더>`와 `--version`을 지정합니다. 기존 배포물 덮어쓰기는 거부합니다.
"""
    write_text(out / "사용방법.md", guide)
    write_text(out / "package-results.json", json.dumps(results, ensure_ascii=False, indent=2))
    return {"output": str(out), "archives": results}


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="new folder under OUTPUTS")
    parser.add_argument("--version", default="1.0.0", help="semantic package version")
    args = parser.parse_args(argv)
    try:
        result = build_package(args.out, args.version)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Package failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
