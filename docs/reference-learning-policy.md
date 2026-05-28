# Reference Learning Policy

## Purpose

This repository uses uploaded PPT/PDF references to improve INNerGEN PPT automation quality by learning reusable consulting structure, not external brand identity.

## What to Learn

- Slide structure and page composition
- Report/storyline flow by business type and meeting type
- Governing-message logic
- Table, process, timeline, scorecard, equation, and evidence placement patterns
- Information hierarchy, density, and consulting-style proof-object selection

## What Not to Learn

- Non-INNerGEN company logos
- Consulting-firm logos and brand marks
- Client logos and client-specific corporate identity systems
- External brand colors as the generated deck's main BI

## Current Source Groups

- `INPUTS/PPT 장표 레퍼런스/CDP`
- `INPUTS/PPT 장표 레퍼런스/감축사업`
- `INPUTS/PPT 장표 레퍼런스/규제대응사업`
- `INPUTS/PPT 장표 레퍼런스/온실가스 인벤토리`
- `INPUTS/PPT 장표 참고(구조화)`

## Standard Deck Flows

The first locked flows are:

- `reduction/kickoff`: 감축사업 착수보고
- `disclosure/proposal`: CDP·기후공시 제안서
- `regulatory/final`: 온실가스 인벤토리/규제대응 최종보고

These flows use approved samples as evidence but keep only INNerGEN BI in generated decks.

## Review Status

The user has approved all accessible INPUT references as good structure samples. Newly indexed accessible slides are therefore stored as `approved-sample`.

Missing files remain `missing` until their paths are restored.

## Output Quality Rules Added After Starstech PDCA

- Do not treat `no overflow` as `good design`. A slide can pass overflow QA and still fail visually when large cells or cards look empty.
- For table-heavy slides, reduce row height or raise body font to 12.5-14pt when the cell contains only one or two short lines. If the row remains sparse, add a judgment, evidence, implication, owner, status, or decision column instead of leaving blank vertical space.
- For numbered row structures, use a fixed number column and align the number and body text to the same row height. The number must not float above or below the text baseline.
- For long Korean/English mixed phrases, keep phrase-level wrapping by giving the row enough height. Do not squeeze wrapped text into a single-line text box.
- Badge and chip text must use the same height as the containing shape with vertical middle alignment. A badge such as `Boundary` must sit visually centered inside the box.
- If a reference structure is selected but the actual output looks sparse, the generator must choose a denser table, row, or summary-bar structure before final QA.
- Alignment is part of design quality, not a cosmetic afterthought. Number labels, row body text, chips, labels, badges, and summary bars must use shared rowY/rowH and vertical middle alignment.
- The approved sample DB should inform aesthetic balance: table body font generally 12-14pt, compact body rows generally 0.55-0.95in, and evidence columns should receive the widest width while category and judgment/status columns stay compact.
- Any output with `alignmentRiskCount > 0`, `tableWhitespaceRiskCount > 0`, or `sparseContainerCount > 0` is not final-quality even if there is no overflow.
- Render QA reports must preserve object-level failure detail in `issues[]`: slide, object id/name, coordinates, related object, reason, and remediation. This makes the next correction target a specific box/row/chip rather than the whole slide.
