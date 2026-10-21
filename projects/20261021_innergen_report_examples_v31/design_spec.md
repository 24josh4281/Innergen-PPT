# INNerGEN Report Diagram Examples - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | INNerGEN Report Diagram Examples |
| Canvas Format | PPT 13:9, 1040×720 |
| Page Count | 3 |
| Target Audience | ESG·기후 컨설팅 보고서 작성자와 고객 실무자 |
| Use Case | 착수·중간·최종 대표 도표와 편집 가능한 감축 수식의 가상 예시 |
| Delivery Purpose | text |
| Design Style | INNerGEN basic / classic-grid |
| Content Strategy | 승인된 3장 개요 유지. 원본 고객 내용·수치 미사용 |
| Created Date | 2026-10-21 |

Chat confirmation approved revision `report-examples-v31-review-1`. This is a three-page
example collection, not three complete reports. No cover, TOC, ending, notes or client facts.
The internal mode is briefing to preserve neutral report reading; the approved content is unchanged.
deck_type: memo

## II. Canvas Specification

- Dimensions: 1040 × 720; viewBox: `0 0 1040 720`.
- Margins: 33.3333. Header: 0,0,1040,69.3333; footer: 0,666.6667,1040,53.3333.
- Title: 33.3333,9.3333,780,48. Governing: 33.3333,86.6667,973.3333,80.
- Body: 33.3333,182.6667,973.3333,452. Source: 33.3333,645.3333,906.6667,16.
- Page: 957.3333,685.3333,49.3333,18.6667.

## III. Visual Theme

- Mode: briefing.
- Visual style: custom.
- Visual style behavior: Preserve the source-backed INNerGEN classic-grid report frame with a narrow gridded header and footer, rectangular content zones, aligned phase columns, restrained rules and a single-line governing statement; hierarchy uses weight and scale within one family, with no shadows, rounded card collection or decorative imagery.

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #FFFFFF | Page and inverse text |
| Primary | #0F243F | Header, footer, phase bands, actual schedule |
| Accent | #0F243F | Structural emphasis |
| Text | #000000 | Body |
| Text secondary | #595959 | Source, annotation |
| Panel | #F2F2F2 | Scope and table headings |
| Border | #BFBFBF | Rules and planned schedules |
| Alert | #FF0000 | Basis date and unresolved markers |

## IV. Typography System

- Title, body and emphasis stacks: `Malgun Gothic, sans-serif`.
- Formula family: `Cambria Math`; code family: `Consolas, monospace`.
- Installed fonts must be available to receiving machines. PPTX fonts are not embedded.
- All sizes below are unitless SVG px; the named profile takes precedence over generic ramps.

| Role | Size | Weight |
| --- | ---: | ---: |
| Title | 32 | 700 |
| Governing / lead | 22 | 700 |
| Body | 16 | 400 |
| Table / note | 14 | 400 |
| Subheading | 17.333333333333332 | 700 |
| Source | 12 | 400 |
| Page | 13.333333333333334 | 700 |
| Section label | 14.666666666666666 | 700 |
| Formula | 24 | 400 |

The governing sentence stays on one line. Table labels may wrap at phrase boundaries.
Formula LaTeX remains in SVG `data-pptx-equation`; preview and native OMML must agree.

## V. Layout Principles

- Fixed source-backed chrome and shared vertical zones on all three pages.
- P01: left scope zone and four phase columns. Each phase has three activity nodes; vertical and cross-phase orthogonal arrows express actual sequence and handoff. Detailed inputs, outputs and gates remain in the traceable source/brief.
- P02: task-owner-state schedule table, six relative weeks, planned and actual bars, as-of line.
- P03: scenario equation block and monitoring-symbol definition rows above review/handover steps.
- Common task IDs and status words; no invented percent progress or actual legal deadlines.
- Thin arrows encode sequence only. Scope containment is not represented as time sequence.

## VI. Icon Usage Specification

No icons are used. The approved built-in library is tabler-outline with an empty inventory.
The INNerGEN footer is typographic text. No reference client logos or images are imported.

## VII. Visualization Reference List

Catalog read: 76 templates

| Page | Template | Path | Summary-quote | Usage |
| --- | --- | --- | --- | --- |
| P01 | process_flow | templates/charts/process_flow.svg | "Pick for 3-8 sequential steps connected by simple arrows — approval workflows, customer onboarding, request handling, lifecycle stages. Skip if cyclical (use circular_stages) or stages produce named outputs (use pipeline_with_stages)." | Four phase columns with three editable activity nodes and orthogonal connections |
| P02 | project_schedule_table | templates/charts/project_schedule_table.svg | "Pick for table-style task tracker (task / owner / status / timeline). Skip for true Gantt with dependencies (use gantt_chart) or schedule without ownership (use roadmap_vertical)." | Four task rows with ownership, state and six relative week columns; not a quantitative percentage chart |
| P03 | no-template-match | — | — | Scenario equations and math-bearing parameter definitions require native Office Math; custom composed rows |

Runners-up considered:
- pipeline_with_stages: superseded for P01 by the user's graph-type clarification and the directly inspected CDP procedure reference.
- gantt_chart: rejected for P02 because the example has four tasks and no dependency graph.
- basic_table: rejected for P03 because native equation carriers and review flow are central, not plain text cells.

## VIII. Image Resource List

No image rows. No formula PNGs. No AI or web image acquisition.

## IX. Content Outline

#### Slide 01 - 수행범위와 단계별 추진절차
- Filename: 01_kickoff_cdp.svg
- **Title**: 수행범위와 단계별 추진절차
- **Core message**: CDP 대응의 합의 범위와 단계별 작업·선후·인계 흐름.
- **Cover impact**: 승인 범위의 개요와 실제 작업 흐름을 첫 장에서 함께 읽게 한다. 별도 표지는 없음.
- Governing: CDP 대응은 요구사항 확인부터 답변 확정까지 단계별로 수행할 예정입니다.
- **Layout**: Left scope + four-stage process graph with three activity nodes per stage and orthogonal arrows.
- Content: 대상 조직·기간·문항 범위는 미확정; 요구사항 확인 → 근거 수집 → 답변 작성·검토 → 고객 확정.
- Evidence: sources/brief.md and approved overview; user-supplied `INPUTS/이너젠 PPT 장표 레퍼런스/CDP/추진절차.pptx` slide 1 is structural design only. Its source hash and observed structure are in the editor's `analysis/reference_structure.md`.
- Status: 가상 예시 · CDP 착수.

#### Slide 02 - 기준일별 수행일정과 보완 현황
- Filename: 02_interim_regulatory.svg
- **Title**: 기준일별 수행일정과 보완 현황
- **Core message**: The same task IDs tie relative-week plan, actuals, status and corrections together.
- Governing: 계획·실적·보완 현황은 같은 과업 ID와 기준일로 관리합니다.
- **Layout**: Task-owner-state table + six-week bars + correction row.
- Content: W1–W6, W3-end as-of; applicability/data/review/submission preparation. Actual legal dates are not invented.
- Evidence: approved overview; D12 slide42 is design only. Interim structure is a proposal.
- Status: 가상 예시 · 규제 중간.

#### Slide 03 - 감축량 산정방법과 검증·인계 체계
- Filename: 03_final_reduction.svg
- **Title**: 감축량 산정방법과 검증·인계 체계
- **Core message**: Scenario expressions, parameter definitions and verification evidence are linked.
- Governing: 시나리오 수식과 모니터링 인자를 검증 근거에 연결해 인계합니다.
- **Layout**: Native formula block + parameter definitions + three-step review/handover flow.
- Content: Generic example ER_y = BE_y − PE_y − LE_y; BE_y = EG_y × EF_BL,y. Parameter symbols are native equations. No methodology or measured values are asserted.
- Evidence: explicitly illustrative formula spec in sources/equations.json. No reference client facts.
- Status: 가상 예시 · 감축 최종 구성 제안, not a claim of project acceptance.

## X. Speaker Notes

None requested.

## style_standard
- version: 17
- family: innergen_basic
- delivery_mode: report_reading
- profile_file: design_profile_v17.json
