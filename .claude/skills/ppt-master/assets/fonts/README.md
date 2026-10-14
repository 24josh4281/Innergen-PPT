# Bundled Fonts

## Pretendard (locked deck font on this install)

[Pretendard](https://github.com/orioncactus/pretendard) v1.3.9 — SIL Open Font License 1.1
(`Pretendard/LICENSE.txt`). Korean + Latin coverage in one family; the fixed typography
choice for every deck generated in this repo (see `references/strategist.md §g`
install-local font lock).

Bundled static cuts (OTF): Light(300) / Regular(400) / Medium(500) / SemiBold(600) /
Bold(700) / ExtraBold(800). The full 9-weight set is available from the upstream release.

### Family names as installed on Windows

| SVG `font-family` | Weight | Notes |
|---|---|---|
| `Pretendard` | 400 / 700 via `font-weight` | Regular and Bold fold into one family |
| `Pretendard Light` | use normal weight | separate installed family name |
| `Pretendard Medium` | use normal weight | separate installed family name |
| `Pretendard SemiBold` | use normal weight | separate installed family name |
| `Pretendard ExtraBold` | use normal weight | separate installed family name |

Recommended deck stack: `Pretendard, "Malgun Gothic", sans-serif` (tail is browser-preview
fallback only; the converter exports Pretendard into both the Latin and EA typeface slots —
registered in `scripts/svg_to_pptx/drawingml/utils.py DUAL_SCRIPT_FONTS`).

### Installing on another machine

PPTX files do **not** embed fonts. A deck opened on a machine without Pretendard falls back
to a system font. To install: select all files in `Pretendard/` → right-click → **Install**
(Windows), or download from https://github.com/orioncactus/pretendard (macOS/Linux
supported upstream). SIL OFL permits free redistribution with the license file.

## IBM Plex Sans KR (INNerGEN 회사소개 · INNerCarry families, v22)

[IBM Plex](https://github.com/IBM/plex) — SIL OFL 1.1 (`IBMPlexSansKR/LICENSE.txt`). Bundled cuts:
Regular(400) / Medium(500) / SemiBold(600) / Bold(700). Installed family names: `IBM Plex Sans KR`
(Regular + Bold via `font-weight`), `IBM Plex Sans KR Medium`, `IBM Plex Sans KR SemiBold`.
Stack: `"IBM Plex Sans KR", "Malgun Gothic", sans-serif`.

## NanumSquare Neo (selectable, v22)

[나눔글꼴](https://hangeul.naver.com/fonts) — SIL OFL 1.1 (`NanumSquareNeo/LICENSE.txt`). Bundled cuts:
Regular / Bold / ExtraBold. Installed family names: `NanumSquare Neo`, `NanumSquare Neo Bold`,
`NanumSquare Neo ExtraBold` (Light / Heavy available upstream).

## Installed-only families (not bundled)

NanumSquare, NanumSquareRound (Naver, OFL) and Noto Sans CJK KR (Google, OFL; ~17 MB per weight) are
installed on this machine and listed in the standard's `fonts` catalog. Install them elsewhere from the
upstream archives with the script below.

## Installing (any family, user-level, no admin)

```bash
python3 .claude/skills/ppt-master/scripts/install_fonts.py                 # every bundled family
python3 .claude/skills/ppt-master/scripts/install_fonts.py --family IBMPlexSansKR
python3 .claude/skills/ppt-master/scripts/install_fonts.py --dir "~/Downloads/NotoSansCJKkr-hinted.zip"
```

Windows: copies into `%LOCALAPPDATA%\Microsoft\Windows\Fonts` and registers HKCU; macOS: `~/Library/Fonts`;
Linux: `~/.local/share/fonts`. Selection rules and defaults per family: `docs/styles/innergen/design-standard-v17.md` v22.
