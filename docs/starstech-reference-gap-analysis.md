# Starstech Reference Gap Analysis

## Purpose

This document records the PDCA Check/Act findings for the Starstech report deck sample. The user's reference deck is treated as the quality baseline for visual grammar, density, and consulting-slide composition.

## Reference Baseline

- Source file: `C:/Users/24jos/Downloads/(회의) 스타스테크 폐산 재활용 기술에 대한 온실가스 감축 방법론 개발_260410_ver1.3.pptx`
- Rendered slides: 24
- Visual grammar:
  - Navy grid header band with large white chapter title
  - White logo zone at top-right with STARs logo
  - Navy grid footer band with INNerGEN logo, tagline, copyright, page icon
  - Dense body area with large tables, phase blocks, or equation diagrams
  - Strong section marker below header using two dots and bold Korean subtitle
  - Conclusion bands or boxed final judgement near the bottom

## Gap Findings

| Area | Gap Observed | Impact | Action Taken |
|---|---|---|---|
| Brand chrome | Earlier output used a simple navy bar and thin footer, unlike the reference deck | Looked generic and AI-generated | Added navy grid header/footer, STARs logo, INNerGEN footer logo, page icon |
| Cover layout | Earlier output used full navy cover, while reference uses white cover with top rule and bottom navy band | Did not feel like the provided Starstech deck | Rebuilt cover to follow reference cover structure |
| Contents slide | Earlier contents slide was plain text-only | Missed reference's image-led composition | Added INNerGEN isometric illustration and right-side section list |
| Process slide | Earlier process was simple 4-card layout | Too clean and sparse versus reference | Rebuilt into reference-like phase bars and 4-column process blocks |
| Main table slide | Earlier table was too small with weak row hierarchy | Did not match consulting report density | Expanded table width/height and bolded first-column assessment labels |
| Legal additionality slide | Earlier slide had excessive blank space | Low information density | Added structured section panels and larger body copy |
| Schedule slide | Earlier slide had overlap and low density | Unacceptable rendering defect | Rebuilt as dense phase table plus timeline band; fixed period/output collision |
| QA method | XML font QA failed even for the reference deck | Wrong gate for reference-following decks | Added reference-style QA based on rendered image band/density metrics |

## Current QA Results

### Render QA

- PPTX opens and renders to PNG successfully.
- Slide count: 12
- Overlap risk count: 0
- Raw hyphen bullet count: 0
- Strict font-size QA still fails because this rule is not calibrated to the reference deck.

### Reference Style QA

- Score: 86
- Status: `warn`
- Remaining warnings:
  - Slide 08: content-density-low
  - Slide 12: content-density-low

### Slide-Type Mapping

The reference QA now accepts an explicit slide map so each generated slide can be compared to the closest reference archetype rather than the same page number only.

Example Starstech map:

`1:1,2:2,3:3,4:4,5:5,6:7,7:8,8:12,9:12,10:13,11:20,12:9`

This is important because a generated 12-page deck compresses a 24-page reference deck; page-number comparison creates false failures.

## Next Improvement Plan

1. Expand the slide-type map into a reusable archetype registry, not a command-line string. `Implemented in docs/reference-structure-db.json and src/referenceStructureDb.ts.`
2. Split QA into two gates:
   - Mechanical QA: open, render, overlap, overflow, Korean word break, one-word wrap
   - Reference QA: chrome fidelity, body density, title/footer presence, conclusion band, table dominance
3. Expand the structure library with extracted Starstech archetypes:
   - Cover
   - Contents with illustration
   - Phase process
   - Full-width assessment table
   - Baseline alternative table
   - Equation concept map
   - Boundary comparison
   - Requested data table
   - Workplan table and timeline
4. For future one-shot generation, choose the archetype first, then place content. Do not start from generic cards.
5. Treat a reference deck as a visual contract: preserve header/footer, slide rhythm, body density, and proof-object style before optimizing text.

## Implemented Reference Structure DB

- Added a reusable structure DB for `businessType + meetingType` combinations.
- Added the first Starstech-based profile: `reduction-kickoff-starstech`.
- Connected the profile to:
  - deck planning archetype sequence
  - web template display
  - GPT prompt generator
  - reference-style QA via `-ProfileId`
- This means future runs can use `-ProfileId reduction-kickoff-starstech` instead of manually passing `1:1,2:2,...`.
