#!/usr/bin/env python3
"""
PPT Master - Claude Design System Builder

Packages the INNerGEN presentation design (three template families) as a
design-system folder for Claude Design (claude.ai/design): a README with the
brand rules, colour/type tokens as CSS and JSON (fallback font Malgun Gothic;
font files only with --with-fonts), the logos,
every family's layout SVGs with its design_spec.md, the INNerGEN rule
documents, and HTML preview cards. Each preview's first line is an
`<!-- @dsCard group="..." -->` marker so the Design System pane can index it.
The repository pipeline is unchanged; this only copies and summarises it.

Usage:
    python3 scripts/build_design_system.py [options]

Examples:
    python3 .claude/skills/ppt-master/scripts/build_design_system.py
    python3 .claude/skills/ppt-master/scripts/build_design_system.py --with-fonts -o OUTPUTS/claude-design

Dependencies:
    None (only uses standard library)
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Optional

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from console_encoding import configure_utf8_stdio  # noqa: E402

# scripts/build_design_system.py: [0]=scripts [1]=ppt-master [2]=skills [3]=.claude [4]=repo
SKILL_ROOT = _SCRIPTS_DIR.parent
REPO_ROOT = _SCRIPTS_DIR.parents[3]
STYLE_DIR = REPO_ROOT / "docs" / "styles" / "innergen"
DECKS = SKILL_ROOT / "templates" / "decks"
FONT_DIR = SKILL_ROOT / "assets" / "fonts"
FALLBACK_FONT = "Malgun Gothic"  # default when the family font is not installed (user decision 2026-10-14)
BUNDLE_NAME = "innergen-design-system"
DEFAULT_OUT = REPO_ROOT / "OUTPUTS" / "claude-design"

FAMILIES = ("innergen_lecture", "innergen_business", "innercarry")
FONT_FILES = {
    "IBMPlexSansKR": ("IBMPlexSansKR-Regular.ttf", "IBMPlexSansKR-Medium.ttf",
                      "IBMPlexSansKR-SemiBold.ttf", "IBMPlexSansKR-Bold.ttf", "LICENSE.txt"),
    "Pretendard": ("Pretendard-Regular.otf", "Pretendard-Medium.otf",
                   "Pretendard-SemiBold.otf", "Pretendard-Bold.otf", "LICENSE.txt"),
}
FONT_FACES = (  # (family, file, weight)
    ("IBM Plex Sans KR", "IBMPlexSansKR/IBMPlexSansKR-Regular.ttf", 400),
    ("IBM Plex Sans KR", "IBMPlexSansKR/IBMPlexSansKR-Medium.ttf", 500),
    ("IBM Plex Sans KR", "IBMPlexSansKR/IBMPlexSansKR-SemiBold.ttf", 600),
    ("IBM Plex Sans KR", "IBMPlexSansKR/IBMPlexSansKR-Bold.ttf", 700),
    ("Pretendard", "Pretendard/Pretendard-Regular.otf", 400),
    ("Pretendard", "Pretendard/Pretendard-Medium.otf", 500),
    ("Pretendard", "Pretendard/Pretendard-SemiBold.otf", 600),
    ("Pretendard", "Pretendard/Pretendard-Bold.otf", 700),
)
REFERENCE_DOCS = (
    "design-standard-v17.md", "structured-slides-v18.md", "consulting-structures-v19.md",
    "content-architecture-v20.md", "design-governing-v11.md", "design-wrapping-v15.md",
    "innergen-profile-matrix-v16.md", "qaqc-v21.md",
)
# Layout gallery cards: (group, title, filename predicate).
GALLERIES = (
    ("기본 장표", "표지·목차·장 구분·본문·마무리", lambda n: not n.startswith("s")),
    ("구조화 장표", "s01–s23 보고·진단 구조", lambda n: n.startswith("s") and int(n[1:3]) <= 23),
    ("구조화 장표", "s24–s42 보고 생애주기·세미나", lambda n: n.startswith("s") and 24 <= int(n[1:3]) <= 42),
    ("컨설팅 도식", "s43–s58 컨설팅 도식 16종", lambda n: n.startswith("s") and int(n[1:3]) >= 43),
)
ROSTER_ROW = re.compile(r"^\| `([\w.]+\.svg)` \| `([\w-]+)` / ([^|]+?) \|", re.M)


def _git_commit() -> str:
    head = REPO_ROOT / ".git" / "HEAD"
    try:
        ref = head.read_text(encoding="utf-8").strip()
        if ref.startswith("ref: "):
            return (REPO_ROOT / ".git" / ref[5:]).read_text(encoding="utf-8").strip()[:7]
        return ref[:7]
    except OSError:
        return "unknown"


def family_tokens(standard: dict) -> dict:
    """Per-family colour, type and zone tokens from design-standard-v17.json."""
    px = standard["density_presets"]["compact"]["px_by_canvas"]
    out = {}
    for fam in FAMILIES:
        p = standard["profiles"][fam]
        colors = dict(p["colors"])
        colors.update(p.get("extra_colors") or {})
        out[fam] = {
            "label": p["label"], "canvas": p["canvas"], "canvas_px": p["canvas_px"],
            "canvas_pt": p.get("canvas_pt"), "font": p["font"], "fallback": p.get("fallback", "Malgun Gothic"),
            "colors": colors, "text_colors": p.get("text_colors", {}),
            "type_px": px.get(p["canvas"], {}), "zones_px": p["zones_px"],
        }
    return out


def roster(fam: str) -> list[tuple[str, str]]:
    spec = (DECKS / fam / "templates" / "design_spec.md").read_text(encoding="utf-8")
    return [(f, name.strip()) for f, _key, name in ROSTER_ROW.findall(spec)]


def write_tokens(bundle: Path, tokens: dict, fonts: bool) -> None:
    out = bundle / "tokens"
    out.mkdir()
    (out / "tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    css = ["/* INNerGEN design tokens - generated by build_design_system.py; do not hand-edit. */"]
    if fonts:
        for family, file, weight in FONT_FACES:
            css.append(f"@font-face {{ font-family: '{family}'; src: url('../fonts/{file}'); "
                       f"font-weight: {weight}; font-display: swap; }}")
    else:
        css.append(f"/* No font files bundled: installed {', '.join(sorted({f for f, _, _ in FONT_FACES}))} "
                   f"render as-is, otherwise text falls back to '{FALLBACK_FONT}'. */")
    for fam, t in tokens.items():
        css.append(f"\n[data-family=\"{fam}\"] {{")
        css.append(f"  --font: '{t['font']}', '{FALLBACK_FONT}', sans-serif;")
        css.append(f"  --canvas-w: {t['canvas_px'][0]}px; --canvas-h: {t['canvas_px'][1]}px;")
        for name, value in t["colors"].items():
            css.append(f"  --color-{name.replace('_', '-')}: {value};")
        for name, value in t["text_colors"].items():
            css.append(f"  --text-{name.replace('_', '-')}: {value};")
        for name, value in t["type_px"].items():
            css.append(f"  --size-{name.replace('_', '-')}: {round(value, 2)}px;")
        css.append("}")
    (out / "colors_and_type.css").write_text("\n".join(css) + "\n", encoding="utf-8")


def copy_templates(bundle: Path) -> None:
    for fam in FAMILIES:
        dst = bundle / "templates" / fam
        dst.mkdir(parents=True)
        for src in sorted((DECKS / fam / "templates").glob("*")):
            if src.suffix == ".svg":
                text = src.read_text(encoding="utf-8").replace('href="../images/', 'href="../../assets/images/')
                (dst / src.name).write_text(text, encoding="utf-8")
            elif src.name == "design_spec.md":
                shutil.copy2(src, dst / src.name)
    images = bundle / "assets" / "images"
    images.mkdir(parents=True)
    for src in sorted((DECKS / "innergen_business" / "images").glob("*.png")):
        shutil.copy2(src, images / src.name)


def _page(group: str, title: str, body: str, fam: str = "innergen_business") -> str:
    return (f'<!-- @dsCard group="{group}" -->\n<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title>'
            '<link rel="stylesheet" href="../tokens/colors_and_type.css"><style>'
            'body{margin:0;padding:20px;background:#fff;color:#1e293b;font-family:var(--font)}'
            'h1{font-size:18px;margin:0 0 4px}p.sub{margin:0 0 16px;color:#64748b;font-size:12px}'
            '.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(var(--thumb,300px),1fr))}'
            'figure{margin:0}figure svg{width:100%;height:auto;border:1px solid #e2e8f0;display:block}'
            'figcaption{font-size:11px;color:#475569;margin-top:4px}'
            '.sw{display:flex;align-items:center;gap:10px;font-size:12px}.chip{width:44px;height:30px;'
            'border:1px solid #e2e8f0;border-radius:4px}table{border-collapse:collapse;font-size:12px}'
            'td,th{border-bottom:1px solid #e2e8f0;padding:6px 10px;text-align:left}'
            f'</style></head><body data-family="{fam}"><h1>{html.escape(title)}</h1>{body}</body></html>\n')


def write_previews(bundle: Path, tokens: dict) -> int:
    out = bundle / "previews"
    out.mkdir()
    count = 0
    for fam, t in tokens.items():
        chips = "".join(
            f'<div class="sw"><div class="chip" style="background:{v}"></div><b>{k}</b> {v}</div>'
            for k, v in t["colors"].items())
        (out / f"colors-{fam}.html").write_text(_page(
            "Colors", f"{t['label']} 색", f'<p class="sub">{t["canvas"]} · 역할별 색 토큰</p>'
            f'<div class="grid" style="--thumb:220px">{chips}</div>', fam), encoding="utf-8")
        rows = "".join(
            f'<tr><th>{k}</th><td>{round(v, 1)}px</td><td style="font-size:{v}px;'
            f'font-weight:{700 if k in ("title", "governing", "cover_title", "subheading") else 400}">'
            '이너젠 장표 Aa 123</td></tr>' for k, v in t["type_px"].items())
        (out / f"type-{fam}.html").write_text(_page(
            "Type", f"{t['label']} 글자", f'<p class="sub">{t["font"]} · 컴팩트 밀도 · 거버닝 1줄</p>'
            f'<table>{rows}</table>', fam), encoding="utf-8")
        count += 2
        names = roster(fam)
        for i, (group, title, keep) in enumerate(GALLERIES, 1):
            figs = []
            for fname, label in names:
                if not keep(fname):
                    continue
                svg = (bundle / "templates" / fam / fname).read_text(encoding="utf-8")
                svg = svg.replace('href="../../assets/', 'href="../assets/')
                figs.append(f"<figure>{svg}<figcaption>{html.escape(fname)} · "
                            f"{html.escape(label)}</figcaption></figure>")
            if not figs:
                continue
            (out / f"slides-{fam}-{i}.html").write_text(_page(
                group, f"{t['label']} · {title}",
                f'<p class="sub">{t["canvas_px"][0]}×{t["canvas_px"][1]} · '
                f'{{{{TOKEN}}}} 자리는 내용 슬롯</p><div class="grid">{"".join(figs)}</div>', fam), encoding="utf-8")
            count += 1
    return count


def write_readme(bundle: Path, tokens: dict, standard: dict, version: dict, fonts: bool) -> None:
    fam_rows = "\n".join(
        f"| `{fam}` | {t['label']} | {t['canvas_px'][0]}×{t['canvas_px'][1]} ({t['canvas']}) | {t['font']} | "
        f"`{t['colors']['primary']}` / `{t['colors']['accent']}` | {len(roster(fam))} |"
        for fam, t in tokens.items())
    color_rows = "\n".join(
        f"| {k} | " + " | ".join(f"`{tokens[f]['colors'].get(k, '—')}`" for f in FAMILIES) + " |"
        for k in tokens["innergen_business"]["colors"])
    type_rows = "\n".join(
        f"| {k} | " + " | ".join(f"{round(tokens[f]['type_px'].get(k, 0), 1)}px" for f in FAMILIES) + " |"
        for k in tokens["innergen_business"]["type_px"])
    names = roster("innergen_business")
    catalog = "\n".join(f"- `{f}` {label}" for f, label in names)
    font_line = ("`fonts/` — IBM Plex Sans KR, Pretendard (SIL OFL 1.1)" if fonts else
                 f"글꼴 파일은 넣지 않았습니다. 계열 글꼴(IBM Plex Sans KR·Pretendard)이 설치돼 있지 않으면 "
                 f"기본 글꼴 **맑은 고딕({FALLBACK_FONT})**으로 표시합니다. 위계는 굵기·크기로 유지합니다.")
    text = f"""# INNerGEN 디자인 시스템

이너젠(INNerGEN) 장표의 색·글꼴·화면 영역·레이아웃 기준입니다. Slide Master 저장소
(`docs/styles/innergen/`, `templates/decks/`)에서 자동 생성했습니다. 손으로 고치지 말고 저장소에서
`build_design_system.py`를 다시 실행하세요.

- 버전: 표준 v{standard.get('version')} rev.{standard.get('revision')} · 커밋 `{version['commit']}` · 내용 해시 `{version['hash']}`
- 세 계열은 같은 파일명·같은 슬롯 토큰을 쓰고 캔버스·글꼴·색만 다릅니다.

## 계열

| 계열 | 이름 | 캔버스(px) | 글꼴 | 주색 / 강조 | 레이아웃 |
|---|---|---|---|---|---|
{fam_rows}

## 디자인 원칙

1. **제목 → 거버닝 → 본문 → 출처** 네 층을 모든 본문 장에 둡니다. 거버닝은 **한 줄**(주어+판단+수치), 최대 18pt.
2. **컴팩트 밀도가 기본**: 본문 12pt 내외, 표·라벨 9.5–10.5pt. 글자를 줄여 맞추지 말고 구조나 장을 바꿉니다.
3. **한 덱 한 글꼴 가족**. 굵기로 위계를 만듭니다(400/700, 중간 굵기는 설치 이름 사용).
4. **색은 역할로만**: primary·band_dark는 제목 바·머리행·기준값, accent는 판단·핵심 수치 한두 곳,
   panel·pale·governing_fill은 배경·보조 계열입니다. alert는 경고에만 씁니다. 장식용 그라데이션·그림자는 쓰지 않습니다.
5. **출처·기준 시점·단위**를 장 하단 출처 영역에 적습니다. 고객명·수치·로고는 예시로 재사용하지 않습니다.
6. 컨설팅 도식(s43–s58)은 구조만 빌립니다. 막대·점·웨지는 실제 수치 비례로 그리고, 산식이 안 맞으면 막대 차트로 바꿉니다.
7. 수평 논리: 거버닝만 이어 읽어도 결론이 나와야 합니다. 수직 논리: 본문은 그 장 거버닝만 지지합니다.

## 색 토큰

| 역할 | 뉴 · 교육/강의(lecture) | 뉴 · 사업/회사 소개(business) | 이너캐리(innercarry) |
|---|---|---|---|
{color_rows}

## 글자 크기 (컴팩트, px)

| 역할 | 뉴 · 교육/강의 | 뉴 · 사업/회사 소개 | 이너캐리 |
|---|---|---|---|
{type_rows}

## 레이아웃 카탈로그 (이너젠 뉴 사업소개 기준, 세 계열 공통 파일명)

{catalog}

## 파일 구성

- `tokens/colors_and_type.css` · `tokens/tokens.json` — `[data-family="<계열>"]` 아래 CSS 변수
- `templates/<계열>/*.svg` — 레이아웃 원형(`{{{{TOKEN}}}}` = 내용 슬롯), `design_spec.md` — 슬롯·영역 계약
- `previews/*.html` — 색·글자·레이아웃 미리보기 카드
- `reference/*.md` — 이너젠 규칙 문서 원문(구조화 장표, 컨설팅 구조, 거버닝, 줄바꿈, QA/QC)
- {font_line}
- `assets/images/` — 이너젠 로고·일러스트
"""
    (bundle / "README.md").write_text(text, encoding="utf-8")


def content_hash(bundle: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.name not in ("README.md", "VERSION.json"):
            h.update(path.relative_to(bundle).as_posix().encode())
            h.update(path.read_bytes())
    return h.hexdigest()[:12]


def build(out_dir: Path, fonts: bool = False) -> Path:
    bundle = out_dir / BUNDLE_NAME
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    standard = json.loads((STYLE_DIR / "design-standard-v17.json").read_text(encoding="utf-8"))
    tokens = family_tokens(standard)
    write_tokens(bundle, tokens, fonts)
    copy_templates(bundle)
    if fonts:
        for folder, files in FONT_FILES.items():
            (bundle / "fonts" / folder).mkdir(parents=True)
            for name in files:
                shutil.copy2(FONT_DIR / folder / name, bundle / "fonts" / folder / name)
    ref = bundle / "reference"
    ref.mkdir()
    for name in REFERENCE_DOCS:
        shutil.copy2(STYLE_DIR / name, ref / name)
    cards = write_previews(bundle, tokens)
    version = {"name": BUNDLE_NAME, "commit": _git_commit(), "hash": content_hash(bundle),
               "standard": f"v{standard.get('version')} rev.{standard.get('revision')}", "cards": cards}
    write_readme(bundle, tokens, standard, version, fonts)
    (bundle / "VERSION.json").write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archive = out_dir / f"{BUNDLE_NAME}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(out_dir).as_posix())
    print(f"[build_design_system] {len(FAMILIES)} families, {cards} preview card(s), hash {version['hash']}")
    return archive


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the INNerGEN design-system folder/ZIP for Claude Design.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-o", "--out", type=Path, default=DEFAULT_OUT,
                        help=f"output directory (default: {DEFAULT_OUT.relative_to(REPO_ROOT)})")
    parser.add_argument("--with-fonts", action="store_true",
                        help="bundle the font files (~10 MB; over claude.ai's browser upload limit)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = build(out_dir, fonts=args.with_fonts)
    print(f"[build_design_system] wrote {archive} ({archive.stat().st_size / 1_000_000:.1f} MB)")
    print("[build_design_system] upload: claude.ai/design → 디자인 시스템 만들기/업데이트 → 폴더 또는 ZIP 첨부")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
