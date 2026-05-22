# INNerGEN PPT Quality Improvement Plan

## P - Plan

- Lock the visual system to INNerGEN BI before applying any reference-deck structure.
- Use consulting references only for storyline, proof-object selection, and slide skeletons.
- Keep all generated PPT text editable and PowerPoint-compatible.
- Allow adaptive typography, but never generate text below 11pt.

## D - Do

- Brand palette: navy `#041E42`, medium blue `#13387B`, sky blue `#00A9E0`, light gray, white, rare red/orange accents.
- Font: `Malgun Gothic` as the default PowerPoint-safe Korean font, controlled in one constant for later replacement.
- Layout: title in the navy header, governing message in the white area below the title, body proof object under that.
- Density: reduce empty space by expanding body objects and using structure-specific layouts rather than repeated card grids.
- Main-deck rule: no internal notes such as source preservation labels, original visual reference labels, or QA comments.
- Bullet rule: never output raw `- text` as a fake bullet in PPT; use native PowerPoint bullet paragraphs or convert the content into table rows.
- Overflow rule: if a text box cannot fit at 11pt, compress the message, split it into rows, or move detail into supporting structure instead of shrinking below 11pt.
- Consulting rule: user bullets are source material, not final slide prose. Each slide must produce one claim and one proof object.

## C - Check

- Build must pass TypeScript and Vite checks.
- Static PPT scan must confirm that every explicit PPT font size flows through the minimum-font helper.
- Generated sample PPTX must have valid zip/XML relationships.
- Visual review should focus on color drift, Korean word splitting, overflow, object overlap, and excessive whitespace.
- Static text scan must show no mojibake tokens from corrupted Korean encodings in generated source files.

## A - Act

- Keep `DESIGN.md` as the single design source of truth.
- When a new reference deck is added, update only structure rules unless the user explicitly asks to change BI.
- Add future QA automation for contact-sheet scoring and per-slide text-box overflow estimation.
