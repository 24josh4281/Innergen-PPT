# INNerGEN PPT Automation - 10 PDCA Improvement Report

Generated: 2026-05-22

## Objective

Improve the PPT automation product so future decks are less likely to show overflow, broken Korean labels, repeated AI-like layouts, weak governing messages, or unclear user workflow.

## PDCA Improvement Cycles

| No. | Plan | Do | Check | Act |
| --- | --- | --- | --- | --- |
| 01 | Stop long text boxes from overflowing. | Added shared rule that converts long box text into bullet text. | Render QA confirms overflow risk 0. | Use the same box policy for all new layouts. |
| 02 | Keep short Korean labels and level labels on one line. | Added narrow single-word risk detection in PPTX QA. | Render QA confirms narrow text risk 0. | Treat short labels as fixed-width, single-line objects. |
| 03 | Make governing messages more consulting-like. | Added QA check for claim/action signals. | UI now warns when a message reads like description. | Users revise messages before PPT generation. |
| 04 | Separate document flows by use case. | Added proposal/kickoff/interim/final/evidence/training scenarios. | UI scenario panel verified by browser screenshot. | Future uploads can be routed through these scenario presets. |
| 05 | Reduce repeated layout patterns. | Added deck-level repeated archetype QA. | Storyboard QA now flags excessive repetition. | Users can switch structures before export. |
| 06 | Control body volume and box fit. | Added section label, section length, and box-fit checks. | Storyboard QA shows actionable warnings. | Dense slides should be split or moved to appendix. |
| 07 | Show clear improvement actions, not only scores. | Added global QA chips and recommendation list. | UI displays deck-level pass/warn/fail chips. | Users can iterate with "수정 반영 / QA". |
| 08 | Productize real consulting workflows. | Added use-case DB and UI buttons with sample inputs and outputs. | Browser screenshot confirms scenario panel. | Use cases become the entry point for non-developer users. |
| 09 | Keep regression QA based on rendered samples. | Updated sample generation script and render QA script. | All archetype and layout-family sample books pass. | Every future layout expansion should run the same scripts. |
| 10 | Preserve quality improvement history. | Added this report and in-app PDCA quality board. | Build and render QA completed after documentation. | Next cycles should start from real failed PPT examples. |

## Files Changed

- `src/qualityPolicy.ts`: central quality policy, 10 PDCA cycles, text fit helpers, recommendations.
- `src/ppt.ts`: PPT generator now uses shared bullet conversion policy.
- `src/qa.ts`: Storyboard QA now includes deck-level checks, message claim checks, section label checks, and box-fit risk.
- `src/pptxQa.ts`: PPTX package QA now includes narrow single-word risk.
- `src/main.ts`: UI now shows use cases, PDCA quality board, global QA chips, and improvement actions.
- `src/style.css`: UI styling for PDCA board and enhanced QA summary.
- `scripts/build-layout-sample-deck.ps1`: sample builder now patches new shared modules.
- `scripts/render-pptx-qa.ps1`: render QA now reports narrow text risk.

## Validation

| Validation | Result |
| --- | --- |
| TypeScript/Vite build | Pass |
| Layout-family sample book | 13 slides, score 100, pass |
| All-archetype sample book | 50 slides, score 100, pass |
| Minimum font | 11pt |
| Below-min-font count | 0 |
| Raw hyphen count | 0 |
| Overflow risk count | 0 |
| Overlap risk count | 0 |
| Narrow text risk count | 0 |
| PowerPoint image rendering | Pass |
| UI screenshot | Pass |

## Generated QA Outputs

- `docs/generated/layout-samples-20260522-10pdca-final/layout-family-sample-book.pptx`
- `docs/generated/layout-samples-20260522-10pdca-final/all-archetype-sample-book.pptx`
- `docs/generated/layout-samples-20260522-10pdca-final/layout-family-render-qa/qa-report.json`
- `docs/generated/layout-samples-20260522-10pdca-final/all-archetype-render-qa/qa-report.json`
- `docs/generated/layout-samples-20260522-10pdca-final/ui-qa/app-home.png`

## Remaining Risks

- Storyboard QA can detect many likely problems, but final visual quality still benefits from rendered PNG review.
- The current product still uses rule-based text transformation. It does not yet perform full slide-by-slide human-level art direction.
- Real uploaded PDF/PPTX content may contain tables or figures that require more specialized extraction and visual placement.

## Recommended Next PDCA Inputs

Use actual failed PPT examples as the next improvement dataset:

1. A slide with Korean labels breaking into characters.
2. A slide with dense table text.
3. A slide with long governing message.
4. A slide with repeated card layouts.
5. A slide where the design is technically clean but not consulting-grade.
