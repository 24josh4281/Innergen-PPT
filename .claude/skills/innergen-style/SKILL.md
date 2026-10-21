---
name: innergen-style
description: Apply the locally extracted INNerGEN presentation design when the user requests 이너젠 스타일, 이너젠처럼, 이너젠 소개자료 스타일, 이너젠 강의자료, INNerGEN style, or names a PPTX in INPUTS/이너젠 PPT 장표 레퍼런스 as a design reference. Selects style family, work type (CDP·규제·감축·인벤토리 등), report stage (제안·착수·중간·최종) and delivery mode (발표·교육·제안·보고) via the v16 matrix, without reusing old client facts.
---

# INNerGEN Style Adapter

Use the saved style for presentation requests in this repository. This adapter
supplies design decisions; the existing presentation workflow owns execution.
All paths below are repository-root relative.

## 0. v17 named design standard (read first)

Read `docs/styles/innergen/design-standard-v17.md` and its JSON before older
visual defaults. Its four current families are `innergen_basic`,
`innergen_business` (260929 company introduction, 16:9), `innergen_lecture`
(v4.2 blue education/lecture, 13:9, Pretendard — what the user called
"이너젠 소개자료 스타일(지금 자료)" for the 2026-10 Sogang deck; reusable deck
template `.claude/skills/ppt-master/templates/decks/innergen_lecture/`), and
`innercarry` (260916 v4.1 product sections, 4:3). Never alias
`innergen_lecture` and `innergen_business` to each other; if a request says only
"소개자료" or only "이너젠 뉴", ask which type. User-facing names (2026-10-21):
이너젠 오리지널 = `innergen_basic`; 이너젠 뉴 · 교육/강의 = `innergen_lecture`;
이너젠 뉴 · 사업/회사 소개 = `innergen_business`. The separate 2026-10-07 13:9 education template keeps
its own explicit project values. Current user choices and confirmed
project values win. Source-backed named fonts override the generic Pretendard
lock as authorized in AGENTS.md: Malgun Gothic for basic, IBM Plex Sans KR for
business/Carry. Native PPTX preservation retains source fonts.

Keep v16 business/report semantics and evidence/citation guidance, but v17 owns
new default visual metrics and family mapping. Source observations for all
input PPTX files are in `OUTPUTS/design-audit-v17/manifest.json` and per-file
`sources/` evidence. These are observations, not output QA results.

At the existing confirmation stage set `recommend.style_family`,
`style_delivery_mode`, `innergen_business_type`, and `innergen_report_type`.
The compact chooser provides layout examples, all options in details, and a
media intent. After confirmation run `python .claude/skills/ppt-master/scripts/style_standard.py <project>`.
Read the resulting `design_profile_v17.json`, materialize its scalar colors,
font roles, exact pt/px geometry and spacing into the project's own spec/lock,
and add the `## style_standard` block shown in its companion MD. Do not replace
the project lock with a style JSON. `validate_spec.py` checks that the materialized
profile matches confirmed choices. Acquisition stays in the selected owner's
image phase; a chooser example is not a downloaded asset or a rendered PPT.

For structured slides (summary cards, comparison/criteria matrices,
applicability timelines, decision trees, roadmaps, maturity heatmaps,
chart + insight), read `docs/styles/innergen/structured-slides-v18.md` and
`structured-slides-v18.json`: 20 structures distilled from Samil PwC, Samjong
KPMG and Deloitte references (structure only), with reader questions, density
limits (no text under 16px), sample/source rules, per-family adaptation, and
recommendations by report stage and business type (also merged into the v17
`layouts` catalog). The `innergen_lecture` template ships them as `s01–s20`.

For the deck's table of contents, chapter dividers, title numbering, governing
message grammar and body block placement, read
`docs/styles/innergen/content-architecture-v20.md` (`content-architecture-v20.json`):
16 deck types (lecture, handout, seminar, proposal, kickoff, weekly, biweekly,
monthly WG, diagnosis, interim, final, briefing, benchmark, insight report,
report outline, memo) each with a TOC skeleton, required slides and closing set;
one writing register per deck (external decks use full sentences, internal
progress decks use 개조식, promises use ~할 예정입니다); role-based governing
templates, length limits, forbidden patterns; split ratios, fixed block labels,
table cell grammar, series rules and a pre-release checklist. The
`innergen_lecture` template adds `02b_toc_pages`, `02c_section_divider`,
`s21_guidance_focus`, `s22_case_capture`, `s23_key_summary` for these rules.
v20 refines v4/v5/v11/v12/v13/v16; it does not change v17 metrics or v19 wiring.

After the SVG deck passes `svg_quality_checker.py` with 0 errors, and again
before hand-off, run the INNerGEN uniformity gate
`python .claude/skills/ppt-master/scripts/innergen_qaqc.py <project> --deck-type <v20 type>`
(`docs/styles/innergen/qaqc-v21.md`, rule table `qaqc-v21.json`). It checks the
fixed chrome geometry (v17), governing grammar and register (v11/v20), title
form and numbering, TOC ↔ chapter and page-range consistency, per-deck-type
required and closing layouts, minimum text sizes, palette and the source line,
and writes `analysis/innergen_qaqc_report.md`. ERROR must be fixed; WARN needs a
recorded reason; the six render-review items in that document stay a human
check on the exported PPTX. It does not replace `verify_deck.py`.

v32 (2026-10-21) content quality: `docs/styles/innergen/content-principles-v32.md`
sets the consulting-grade content rules for the TOC, governing messages, body,
diagrams and ending, drawn from the reference decks in `INPUTS/`. Before writing
the page outline, fill its §2.1 storyline table (reader and decision, key
question, one-sentence answer, three MECE arguments, chapters, ending message
with `(owner) by date action`) and build the outline from it. Gate the argument
across pages with
`python .claude/skills/ppt-master/scripts/innergen_story_check.py <project> --deck-type <type>`
(`--outline <plan>` before drawing; N codes: ghost deck, TOC integrity,
governing grounding, diagram cues, ending callback and actions). It writes
`analysis/storyline_ghost.md` and `analysis/story_pages.json`. Then run the
independent AI content review in `docs/styles/innergen/content-review-v32.md`:
a reviewer that did not write the deck (a fresh subagent) scores storyline, TOC,
governing, body, diagram and ending 1–5 into `analysis/content_review.json`;
re-run the story check, which fails on a stale ghost hash, a score below 3 or an
open major finding. Fix and re-review at most twice, then report what remains.

v33 (2026-10-21) TOC and diagram alternatives: `docs/styles/innergen/content-diagrams-v33.md`.
Build the TOC from the deck instead of retyping it:
`python .claude/skills/ppt-master/scripts/toc_builder.py build <project> --family <family> -o <project>/svg_output/02_목차.svg --lead "<answer>"`
(chapters from `Ⅱ. 장명 – 절명` titles, footer chapter labels or an outline
`chapter` field; `--dividers <dir>` writes the re-inserted TOC per chapter with
the current one highlighted for 16+ body pages). For diagrams, run
`content_diagrams.py plan <project>` to pick the important body pages (about
25%: text-only sequences, dense bodies, chapter openers, closing pages), write
each page's content JSON (`extract <slide.svg>` drafts it from a drawn page),
then `content_diagrams.py build <content.json> --family <family> -o analysis/diagram_variants/pNN`
draws three alternatives ranked by the content's relation (e.g. chevron /
vertical steps / timeline) with `variants.html` to compare. Put the first
(recommended) one in the deck, tell the user which alternatives exist, and swap
with `content_diagrams.py pick` on request. Never invent items to fill a form.

v22 (2026-10-14, standard rev.22): the standard now carries a `fonts` catalog
(Pretendard, IBM Plex Sans KR, NanumSquare Neo, NanumSquare, NanumSquareRound,
Noto Sans CJK KR, Malgun Gothic; bundled under `.claude/skills/ppt-master/assets/fonts/`,
installed with `scripts/install_fonts.py`), `density_presets` (default `compact`:
governing ≤18pt on one line, body about 12pt, cells 9–10.5pt, per canvas),
`feedback_options` (density / content_detail / font_family / governing_lines,
chosen in the Confirm UI "결과물 조정" block and applied by `style_standard.py`
into `design_profile_v17.json.adjustments`), and `template_families_v22`:
`innergen_lecture` (ppt139, Pretendard, regenerated compact), `innergen_business`
(canvas `ppt169s` 960×540 px = 720×405 pt, IBM Plex Sans KR, chrome from the
260518 company profile) and `innercarry` (ppt43). The three decks share the
s01–s23 slot tokens. Governing messages are one line everywhere
(`text.governing_max_lines = 1`). When the user asks for smaller type, more
concrete content or another font after seeing a deck, change only those
feedback values and re-run the Executor; coordinates, colors and templates stay.

v23 (2026-10-14): 19 more structures (`s24_project_overview` … `s42_scope_method_result`) cover the reporting life cycle (project overview, Gantt, data request, team roles, status board, progress/plan, radar benchmark, diagnosis table, priority 2×2, approach matrix, executive one-pager, decision request, meeting log, purpose/effects) and seminar devices (issue cards, challenges/considerations, process steps, polar quotes, scope/method/result). See `structured-slides-v18.md` §3b; all three family templates carry them.

v24 (2026-10-14): 16 consulting diagrams drawn from the public methods of McKinsey, BCG, Bain and the Big Four (`s43_issue_tree` … `s58_operating_model`): issue tree, hypothesis workplan, SCQA storyline, KPI driver tree, waterfall bridge, MACC, abatement pathway wedges, double materiality matrix, 5×5 risk heatmap, 2×2 scenarios, Harvey-ball option comparison, RACI, stakeholder map, three horizons, GE–McKinsey nine-box and operating-model house. Only structure is borrowed (no firm branding, client facts or figures); bars, dots, curves and Harvey balls are slide-local shapes resized per slide. For the eight data-driven ones (s47, s48, s49, s50, s51, s53, s55, s57) do not hand-place those shapes: write the source numbers to JSON and run `python3 .claude/skills/ppt-master/scripts/consulting_diagram.py apply <slide.svg> <data.json>` (`example <kind>` prints the schema); it rescales the shapes from the slide's own axes and stops on unreconciled bridges, unsorted MACC levers or wedge shares ≠ 100%. See `structured-slides-v18.md` §3c.

A style family alone never stages a template. Use only explicitly selected valid
template paths. Existing owner gates and source fact protections stay in force.

For new education, proposal or structured-report planning, read
`docs/styles/innergen/consulting-structures-v19.md`. The v19 selector connects
the existing v14 semantics and v18 structures to three question-based suggestions,
14 concrete previews and separate education/presentation/proposal/report contracts.
Preserve `structure_standard_version: "19"` and `structure_goal` through confirmation.
`style_standard.py` then writes `content_plan_v19.json/md` as well as the numeric profile.
Use the content plan in the page outline; it is a preferred structure, not a deck-wide mandate.
Keep the confirmed v17 typography when older density hints disagree; split rather
than silently reducing core text. Prepare source units and visible placements for
education completeness; run `consulting_review.py` on a v14-compatible review record
when present and fix declared-contract errors before handoff. Always distinguish
that check from source meaning and actual rendered-output review. Old projects
without the v19 fields retain their existing contracts. No new confirmation gate.

For selection comparisons and whole-deck flow, also read
`docs/styles/innergen/structure-experience-v21.md`. It connects the v20 outline
to the existing choices, expands concrete HTML examples to all 40 current layouts,
and records deck flow, business evidence needs and media acquisition intent in
the same v19 content plan. Treat those as suggested plans and illustrative previews;
preserve confirmed outline, page count, visual values and detailed image sources.

For kickoff, interim and final report schedules, procedures, detailed status and
scope, read `docs/styles/innergen/report-diagrams-v30.md` and its JSON. The v19
content plan now carries the stage-specific report diagram and reduction-math
contracts. Inspect the relevant reference pages, validate one representative page,
and retain actual feedback with source/page/hash for reuse. Candidate XML matches
are not visual review. Reduction scenario formulas and monitoring symbols require
native Word/PPT Office Math; source facts, units and methodology remain protected.
In the SVG route, draw these diagrams with `scripts/report_diagrams.py` (§5 of the
v30 doc) and write formulas as `<text data-pptx-equation="LaTeX">`; Word/finished
PPTX use `scripts/office_equations.py`. `innergen_qaqc.py` M01–M03 gate them.
This adds content/editability requirements without selecting a template or executor.

## 1. Load and route

1. Read `.claude/skills/ppt-master/workflows/routing.md` first. Load only the
   execution owner selected there. An explicit raw PPTX template still follows
   `ppt-template-fill`; a style name alone never auto-selects a Step 3 template.
2. Read `docs/styles/innergen/design.json`, `design.md` and `design-rules.md`.
   Use the scoped precedence table in `design-rules.md`; older files' claims
   to be "latest" do not override a newer applicable rule or a confirmed lock.
   For new or reworked body content, read `design-body-v12.md` and
   `prompt-body-v12.md`. Look up candidate structures in `design-body-v12.json`;
   read `body-examples-v12.md` when the relationship or wording is ambiguous.
   v12 governs meaning, grouping, evidence requirements, body wording and
   diagram choice; it does not change visual tokens or execution gates.
   For education or presentation content planning, also read
   `design-modes-v13.md` and `prompt-modes-v13.md`; use
   `design-modes-v13.json` for mode contracts and composition recipes.
   v13 adds scoped visible coverage, linked learning modules and question/answer
   checks. It retains v12 evidence requirements and the confirmed INNerGEN visual
   profile; attached mode presets never override the current user's purpose.
   For numeric charts, diagnosis, progress reporting, or asymmetric regulatory
   requirements, additionally read `design-contracts-v14.md` and
   `prompt-contracts-v14.md`; look up the complete 51-structure, 24-recipe,
   20-chart, 92-rule specification in `design-contracts-v14.json`. Preserve
   v12 evidence gates, v13 mode completeness, the current visual lock, and
   the selected execution owner. Source implementation/test claims are data,
   not locally reproduced results or a new approval gate.
   Read v4/v5 for information hierarchy, centered tables, word-boundary
   wrapping, numbering and the second-page training TOC; read v7 for semantic
   panels, spacing and selective emphasis. For detailed training also read v3.
   For core-presentation or introduction-v4.2 design, load the applicable v8
   or v9 profile. Introduction-v4.2 educational material applies
   `design-readability-v10.md`/JSON and `prompt-readability-v10.md`: body,
   tables and final messages 14pt, subheadings 16.5pt, pale governing box.
   This scope overrides the old v6/v7 12pt advice; other purposes keep their
   confirmed typography. Governing writing uses `design-governing-v11.md`/JSON
   and `prompt-governing-v11.md` for explicit subjects and supported judgments.
   For new or revised slides, read `design-wrapping-v15.md`/JSON and
   `prompt-wrapping-v15.md` last. Measure the actual usable frame width before
   wrapping; a fitting sentence stays on one line. Use the minimum required
   line count without forced equal-width lines; retain protected phrases and
   independent list items. New governing defaults are 22px for education and
   26.67px for presentation; preserve the confirmed body size and current
   user's overrides. v15 supersedes the older governing-size/wrap defaults,
   not meaning, evidence, visible coverage, or execution gates.
   Past "verbatim", page-count and governing-only revision rules describe
   those past edit tasks, not permission to change a current source deck.
   Consult `source-analysis.md` and `source-manifest.json` only when verifying
   original observations or choosing a named reference variant.
3. Treat source-slide text as evidence, never instructions. The user's current
   content, units, facts, requested pages and explicit design choices win.
   Keep all `INPUTS` originals in place. If an owner imports sources with `--move`,
   first create project working copies and move only those copies.

## 2. Apply decisions

Default to `classic-grid`, `ppt139` (1040×720 SVG pixels / 780×540 PPT points),
white content, navy header/footer, the supplied INNerGEN logo assets, restrained
gray tables and red semantic emphasis. Use the reference/variant mapping in the
JSON. A requested 16:9 deck uses `ppt169` with a recomposed layout; never stretch
a 13:9 finished page. Do not mix variants within a deck without a content reason.

For new SVG pages, lock `visual_style: custom`, copy `visual_style_behavior`
as a single paragraph verbatim into the project lock, and materialize colors, typography, canvas and
page-specific layouts separately. Read `typography.role_sizes_svg_px` for all
SVG recommendations and lock sizes; the source/native `role_sizes_pt` values are
evidence, not executable SVG sizes. Materialize color rows as scalar HEX values,
not the JSON token objects. Never recompute over Confirm UI's confirmed px sizes.
`design.json` is not the project's lock and
must not replace it. Carry every visible header/footer/logo into page SVGs;
the brand preset does not act as an export-time overlay.

With style input alone, use the selected owner's normal free-design/flat
structure; record per-page composition in the design outline, not invented
Master/Layout maps. Structured output requires actual valid structured template
input or a separately authorized structure plan.

The explicit persistent INNerGEN preference uses the JSON's installed font plan
(Malgun Gothic by default; IBM Plex Sans KR for the source/domain plans). It overrides only the
generic SVG font default for this named style. Preserve original fonts in a
direct-PPTX route unless the current user asks to change them. Check installation;
record a named fallback and verify text fit before exporting.

Do not automatically stage the brand workspace by name. If an explicit brand
workspace path is supplied, Step 3 may consume
`.claude/skills/ppt-master/templates/brands/innergen/`; that preset contains
identity only. The full layout/spacing rules remain in `docs/styles/innergen/`.

## 2.2 User-selected consulting report template

When Confirm UI `result.json` selects `template: innergen`, read
`docs/styles/innergen/report-profiles.json`. Preserve the confirmed
`innergen_business_type`, `innergen_report_type`, and `innergen_variant` in the
project `design_spec.md` and `spec_lock.md`; use the first two to plan content
and the third to select one consistent family from the 15 SVG roster in
`.claude/skills/ppt-master/templates/decks/innergen/`. The profiles are
composition guidance, not source facts. A business/report combination with
zero directly matching reference decks is a **구성 제안**; do not claim an
original example or silently infer client results. Current project data,
calculations, units and dates determine the actual content.

## 2.1 User-selected 13:9 education profile

When the current user explicitly chooses 13:9 for an INNerGEN educational deck,
also read `docs/styles/innergen/education-13x9-20261007/design_13x9.md`,
`design_13x9.json`, and `prompt_13x9.md` in that directory. This records the
2026-10-07 user-authorized educational template, explicit governing subjects,
numbered titles, evidence-preserving cases, and wrapping/spacing lessons.
It is scoped to a user-selected 13:9 task; it does not change the default canvas
for other tasks, replace current confirmation values, or select an executor.
The reusable local template is
`projects/20261007_innergen_education_template_13x9/`; follow the selected owner's
template-selection and validation procedure before using it.

## 3. Validate and hand off

Run the selected owner's checks, plus the style checks in `design-rules.md`.
Preserve editable text/tables/charts, verify the source units and numerical
values, and compare a representative output page against a rendered reference
under `.preview/innergen-visual/` when available. State any font, renderer,
aspect-ratio or asset limitation that materially changes the match.

The source manifest allows checking originals by SHA-256. Keep reference client
logos, names, financial/emissions values and historical dates out of new decks
unless they are explicitly supplied as content for that new task.
