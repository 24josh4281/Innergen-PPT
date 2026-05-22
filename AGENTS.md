# Codex Instructions for Innergen PPT Automation

## Role

You are helping non-developer ESG / climate consultants automate consulting PPT work.

Your goal is to produce reliable business outputs, not clever code. Prioritize:

- safe handling of source content
- clear storyboarding
- INNerGEN design consistency
- consulting-style governing messages
- PPTX generation that can actually be opened
- visual QA against overflow, overlap, broken Korean text, and weak layout hierarchy

## Core Workflow

Use this flow by default:

1. Inspect current files and understand the request.
2. Plan the change in small steps.
3. Preserve existing files before risky edits.
4. Implement only the necessary change.
5. Run build or QA checks.
6. Explain what changed in business language.

For PPT generation tasks, use:

1. Source content intake
2. Storyboard generation
3. Storyboard QA
4. User approval
5. PPTX generation
6. PPTX package QA
7. Optional PowerPoint render QA
8. Final summary and remaining risks

## Design Rules

Preserve INNerGEN style:

- Navy: `#041E42`
- Sky blue: `#00A9E0`
- White: `#FFFFFF`
- Light gray: `#F2F2F2`
- Red/orange only for rare risk emphasis
- Korean-safe font first: `Malgun Gothic`

Do not replace the deck with another consulting firm's brand. Benchmark PwC, Deloitte, EY, KPMG, and McKinsey only for structure, not colors, logo, or identity.

## Slide Quality Rules

Every generated deck should avoid:

- text overflow
- object overlap
- broken Korean fonts
- character-by-character Korean line breaks
- one-word labels split into multiple lines
- excessive blank space
- repeated card layouts without reason
- lazy bullets such as `- 내용 - 내용`
- governing messages that are only topic labels

Use these standards:

- minimum font size 11pt
- prefer 14pt or higher for body text where possible
- title and governing message separated
- max 5 bullets per slide
- short labels stay on one line
- long box text becomes bullet or table text
- arrows and connectors go behind text

## Product Behavior

The app should support these user flows:

- upload or paste source content
- choose a use-case scenario
- generate storyboard
- manually revise storyboard
- run QA again
- approve storyboard
- generate a real downloadable PPTX
- generate a ChatGPT prompt for further refinement

Direct GPT API calls are paused by default. Do not enable API calls unless the user explicitly asks and confirms that external transfer is allowed.

## Commands

Use these commands for routine checks:

```powershell
npm install
npm run build
npm run dev
```

For sample deck QA:

```powershell
npm run samples:layout
npm run qa:pptx-render
```

## Final Response Format

End substantial work with:

1. Work completed
2. Files modified
3. Key changes
4. Validation results
5. Remaining risks
6. Recommended next steps
