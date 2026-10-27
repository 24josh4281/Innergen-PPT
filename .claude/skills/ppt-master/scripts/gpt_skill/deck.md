---
name: innergen-deck
description: Create editable INNerGEN or INNerCarry PowerPoint decks from supplied material or a researched brief, including consulting reports and training slides. Use when these styles or this Slide Master package are requested. Existing-PPTX template filling and native enhancement require the full repository workflow.
---

# INNerGEN decks for ChatGPT and Work

Create an editable PPTX using this package's SVG export engine. `${SKILL_DIR}`
means the directory containing this file, including when installed under a
plugin. Read [`ENVIRONMENT.md`](./ENVIRONMENT.md) before running a command and
[`references/deck-workflow.md`](./references/deck-workflow.md) for deck creation.
Read the workflow's design references only for the selected family and task.

Use the user's requested language, model, reasoning level and output location.
Infer routine choices from their brief. When no family is specified, recommend
business for consulting/company material, lecture for training, or innercarry
for product material, and proceed with the stated assumption. Ask only for
missing facts that materially prevent the task. Show the outline and continue
unless the user explicitly requested outline approval.

Write each completed slide as an SVG, check page 1 before page 2, run the full
checks and export with `scripts/svg_to_pptx.py`. Keep source facts, numbers,
units, dates and formulas traceable. Reference templates and examples supply
design, not current client facts. Mark illustrative data `예시`. Replace all
template text and sample screenshots; keep a logo only when it matches the
requested brand. Missing current facts remain explicit gaps.

For business and lecture pages, the latest visual rules in
[`references/newbiz-governing-diagrams-v34.md`](./references/newbiz-governing-diagrams-v34.md)
take precedence over older defaults: centered governing sentence, lime emphasis
on key phrases, lime/blue evidence headers. Explicit user choices still win.

Read [`references/capabilities.md`](./references/capabilities.md) when an existing
PPTX, audio, image generation, or another repository capability is requested.
Do not silently replace a requested native-PPTX operation with SVG regeneration.
Reduction equations must remain editable Office Math; use the separately
packaged `reduction-equations` skill when available. A deck request does not
authorize making additional Word files.

Deliver a downloadable PPTX, a short page list, actual check results, any WARN
reasons, illustrative items and font/render limitations. Report self-review as
self-review. Never describe an unperformed render or check as passed.
