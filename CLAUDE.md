# CLAUDE.md

This file is the project entry point for Claude Code. The ppt-master skill lives at `.claude/skills/ppt-master/` and is auto-discovered by Claude Code.

> **Cross-harness (multi-host)**: [`AGENTS.md`](AGENTS.md) is the Codex (GPT) execution-rules layer and [`GEMINI.md`](GEMINI.md) the Gemini CLI layer — both reference this file as SSOT and only add enforcement, so content edits here do not need mirroring there. `.codex/skills/` and `.gemini/skills/` hold **generated** discovery stubs: after editing any `.claude/skills/<name>/SKILL.md` frontmatter, run `python3 .claude/skills/ppt-master/scripts/sync_codex_stubs.py` (regenerates both; never hand-edit stubs; `preflight.py` fails while they are stale). Skill content itself lives only in `.claude/skills/`. Do not add a shared `.agents/skills/` set — Codex and Gemini CLI both scan it, so it would shadow the per-host sets.
>
> **Python environment**: `setup.ps1` / `setup.sh` create `.venv/`, install dependencies and fonts, and sync the host stubs. When `.venv/` exists, run repository scripts with its interpreter (`.venv\Scripts\python.exe` on Windows, `.venv/bin/python` elsewhere) instead of the system `python3`/`python`. Python runs in UTF-8 mode (`PYTHONUTF8=1`: `.claude/settings.json` for Claude Code, a user variable from setup elsewhere) because Windows consoles default to cp949 and crash on Korean output; read PDFs with PyMuPDF (`fitz`).

**Route before full-load (mandatory)**: for a presentation request, first read
[`.claude/skills/ppt-master/workflows/routing.md`](.claude/skills/ppt-master/workflows/routing.md).
Select the route there, then read only the selected execution owner(s) in full.
Do not preload the main SVG skill for a direct-PPTX route. For a repository edit,
read the owner of the contract being changed; the main skill is authoritative only
for the main SVG family and the shared SVG steps that explicitly invoke it.

## Project Overview

PPT Master is a presentation workflow package with SVG-authoring and direct-PPTX
route families. The main SVG family uses Strategist → Image_Generator → Executor
to convert source documents into editable DrawingML. Direct-PPTX routes preserve
an existing PowerPoint package and use their own execution gates.

**Main SVG Pipeline**: `Source Document → Create Project → [Template] → Strategist confirmation stage → [Image_Generator] → Executor Live Preview → Quality Check → Post-processing → Export PPTX`

**Route selection authority**:
[`.claude/skills/ppt-master/workflows/routing.md`](.claude/skills/ppt-master/workflows/routing.md)
owns the complete matrix and wins over every summary below.

| Selected family | Full execution owner(s) |
|---|---|
| New SVG-authored deck or PPTX re-architecture | [Main `ppt-master/SKILL.md`](.claude/skills/ppt-master/SKILL.md) |
| Existing PPTX, strict 1:1 wording/page preservation with visual redesign | [`beautify-pptx.md`](.claude/skills/ppt-master/workflows/beautify-pptx.md), then the main skill only at its explicit shared-SVG handoff |
| Raw PPTX template plus new material/topic | [`ppt-template-fill/SKILL.md`](.claude/skills/ppt-template-fill/SKILL.md) only |
| Finished PPTX, stable visible content/layout, add notes/audio/timing/transitions | [`native-enhance-pptx/SKILL.md`](.claude/skills/native-enhance-pptx/SKILL.md), then its required execution workflow |
| Reusable template creation or another standalone workflow | The selected workflow; load another owner only at an explicit handoff |

An ambiguous PPTX optimization request stays in the router until its one
discriminator question resolves whether the deck is 1:1 beautify or
re-architectable source. Do not load either full owner before that answer.

## Execution Ownership

- The selected skill or workflow owns its confirmations, preflight, validation,
  recovery, export, and completion gates. This root file adds none.
- Shared scripts do not transfer gate ownership between SVG and direct-PPTX
  families.
- Topic research, template creation, and post-route workflows load the next
  owner only when their own procedure declares a handoff.

## Font Policy (install-local, standing preference)

- Every SVG-authored deck uses **Pretendard** as the fixed font family — do not propose or pick other families unless the user explicitly asks in the current conversation. Hierarchy comes from weight/size, not family switching. Direct-PPTX routes preserve source fonts unless their selected owner says otherwise. Full contract: [`strategist.md §g` install-local font lock](.claude/skills/ppt-master/references/strategist.md).
- **Named INNerGEN families (2026-10-14, user decision)**: `innergen_business` (회사소개, 16:9 `ppt169s`) and `innercarry` use **IBM Plex Sans KR**; `innergen_lecture` keeps Pretendard. The standard's `fonts` catalog (`docs/styles/innergen/design-standard-v17.json` rev.22) also lists NanumSquare Neo / NanumSquare / NanumSquareRound / Noto Sans CJK KR as user-selectable through the Confirm UI feedback option `font_family`. Bundled files: `assets/fonts/{Pretendard,IBMPlexSansKR,NanumSquareNeo}/`; install user-level with `python3 .claude/skills/ppt-master/scripts/install_fonts.py`. Compact density (governing ≤18pt on one line, body 13pt = 17.33px since 2026-10-22) is the default for these families.
- Stack: `Pretendard, "Malgun Gothic", sans-serif`; intermediate weights use installed family names (`"Pretendard Medium"`, `"Pretendard SemiBold"`, etc.).
- Font files are bundled at [`.claude/skills/ppt-master/assets/fonts/Pretendard/`](.claude/skills/ppt-master/assets/fonts/Pretendard/) (SIL OFL) and installed user-level on this machine. PPTX does not embed fonts — decks shared to other machines need Pretendard installed there.

## User-authorized report diagrams and editable reduction equations

For kickoff, interim and final reports, apply
[`report-diagrams-v30.md`](docs/styles/innergen/report-diagrams-v30.md) when
planning schedules, procedures, detailed status and scope. Read reference pages,
reuse their structural relationships, and keep source/page/hash plus actual
output feedback for later work. A reference index is not visual review or model
retraining. Keep the selected route, current content and confirmed design values.

For reduction projects, scenario equations and monitoring-parameter symbols must
remain native editable Office Math in Word and PPT (`m:oMath`, PPT `a14:m`).
PNG, outline shapes and plain text alone do not meet this requirement. Use the
same source formulas in both formats; verify equation structure, parameter/unit
mapping, and actual rendering/editing separately from calculation correctness.
For a methodology or business plan in Word, build it with `office_equations.py docx
--kind methodology|business_plan`, or run `inject-docx` on the user's own draft
(see the v30 doc). This user-authorized requirement takes precedence over the
generic formula-PNG default. Preserve originals and do not invent methodology, coefficients or results.

## Setup and Update Requests (new PC)

Users are non-technical; they typically give only the git URL and ask to install it or
to "가상환경 설정해줘". The user guide is [`설치안내.md`](설치안내.md).

1. **Clone branch `slide-master`**:
   `git clone -b slide-master https://github.com/24josh4281/Innergen-PPT.git slide-master`.
   `slide-master` is the default branch (since 2026-10-21), so a plain clone works;
   branch `main` is a different project (a web app with `package.json` and no
   `.claude/skills/ppt-master`). If a `main` checkout was made by mistake,
   clone `slide-master` beside it and work there. A user who wants that web app
   (*Innergen PPT Automation*) needs `git clone -b main …` instead. On Windows without git:
   `winget install -e --id Git.Git`.
2. **Run setup from the repository root** —
   `powershell -ExecutionPolicy Bypass -File .\setup.ps1` (Windows) or `sh setup.sh`.
   It is idempotent and installs everything itself (Python via winget, `.venv`,
   fonts, playwright + Chromium, Node.js LTS, OfficeCLI, Codex CLI, claude.ai
   bundles, git hooks), then exports a self-test deck. Allow several minutes; do
   not replace it with manual steps.
3. **Relay the final `설치 결과` block in plain Korean**, without commands the user
   does not need. For a `사용자 할 일` row, say exactly what to do: `codex login` is
   the user's own browser sign-in — never enter credentials for them. For
   claude.ai chat / Claude Design, follow [`설치안내.md`](설치안내.md) §4.
4. **Hand off**: tell the user to open the cloned folder in their agent and give the
   example request printed by setup.
5. **Status / update**: "설치 점검해줘" → `setup.ps1 --check` (`sh setup.sh --check`);
   "최신으로 업데이트해줘" → `python .claude/skills/ppt-master/scripts/update_repo.py`
   (pull + dependency sync; the git hooks rebuild the claude.ai bundles), then
   `--check`. Any failed check → re-run setup.

## Required Conventions

- **Repo-wide style rules** — when editing prompt files under [`.claude/skills/ppt-master/references/`](.claude/skills/ppt-master/references/), Python under [`.claude/skills/ppt-master/scripts/`](.claude/skills/ppt-master/scripts/), or any other code/prose in the repo, follow the matching style rule in [`docs/rules/`](docs/rules/).
- **Markdown language consistency** — Markdown files under `.claude/skills/ppt-master/workflows/`, `.claude/skills/ppt-master/references/`, and `docs/` are currently single-language per directory. New files mirror the language of their siblings; do not mix English scaffolding with Chinese paragraphs (or vice versa) inside one file. Chat replies are unaffected.

## Compatibility Boundary

- This repository is a workflow/skill package, not an app or service scaffold.
- Do NOT assume generic-project conventions like `.worktrees/`, `tests/`, or mandatory branch setup unless the user explicitly requests them.
- On conflict with a generic coding skill, prioritize the selected repo-local
  execution owner. The main [`ppt-master/SKILL.md`](.claude/skills/ppt-master/SKILL.md)
  has that role only when routing selected the main SVG family or an explicit
  shared-SVG handoff.

## Execution Pointers

Commands and defaults belong to the selected owner; use these pointers instead
of treating a root-level command list as a gate checklist.

| Work | Runtime authority |
|---|---|
| Route selection | [`routing.md`](.claude/skills/ppt-master/workflows/routing.md) |
| Main SVG generation and re-architecture | [`ppt-master/SKILL.md`](.claude/skills/ppt-master/SKILL.md) |
| Strict 1:1 SVG beautify | [`beautify-pptx.md`](.claude/skills/ppt-master/workflows/beautify-pptx.md) and only the shared main steps it invokes |
| Raw template fill | [`ppt-template-fill/SKILL.md`](.claude/skills/ppt-template-fill/SKILL.md) |
| Finished-PPTX native enhancement | [`native-enhance-pptx/SKILL.md`](.claude/skills/native-enhance-pptx/SKILL.md) |
| Standalone workflow inventory | [`workflows/index.md`](.claude/skills/ppt-master/workflows/index.md) |

## Core Directories

- `.claude/skills/ppt-master/SKILL.md` — main SVG workflow authority.
- `.claude/skills/ppt-template-fill/SKILL.md` — raw-template direct-PPTX authority.
- `.claude/skills/native-enhance-pptx/SKILL.md` — finished-PPTX enhancement entry owner.
- `.claude/skills/ppt-master/references/` — role definitions and technical specifications.
- `.claude/skills/ppt-master/scripts/` — runnable tool scripts.
- `.claude/skills/ppt-master/scripts/docs/` — topic-focused script docs.
- `.claude/skills/ppt-master/templates/` — layout templates, chart templates, icon library, brand presets.
- `.claude/skills/ppt-master/workflows/` — standalone workflow files.
- `docs/` — user-facing documentation (FAQ, installation, technical design, templates guide, audio narration).
- `docs/rules/` — repo-wide style rules.
- `projects/` — user project workspace.
