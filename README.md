# Innergen PPT Automation

Innergen PPT Automation is a local web app for turning ESG / climate consulting content into INNerGEN-style PowerPoint decks.

The workflow is designed for non-developers:

1. Paste or upload source content.
2. Let the app create a slide-by-slide storyboard.
3. Review title, governing message, layout, and QA warnings.
4. Approve the storyboard.
5. Generate and download a real `.pptx` file.
6. Optionally generate a ChatGPT prompt for further refinement.

## What This Repo Provides

- INNerGEN BI-based PPTX generation
- Consulting-style slide structure matching
- Storyboard review before PPT creation
- Layout QA rules for text overflow, overlap, font size, Korean line breaks, and repeated layouts
- PPTX browser download plus local server-side export
- ChatGPT prompt generator with four modes:
  - One-shot PPT generation
  - Storyboard upgrade
  - PPT QA review
  - pptxgenjs code implementation
- API execution is paused by default. Generated prompts are intended to be copied into a ChatGPT chat window.

## Quick Start

```powershell
git clone https://github.com/24josh4281/Innergen-PPT.git
cd Innergen-PPT
npm install
npm run verify:setup
npm run dev
```

Open the URL shown in the terminal. The default Vite port is usually:

```text
http://127.0.0.1:5177
```

If that port is already in use, Vite may choose another port. In this Codex workspace the app has also been run at:

```text
http://127.0.0.1:5180
```

## Build Check

```powershell
npm run build
```

This checks TypeScript and creates the production bundle in `dist/`.

## Reproducible Setup Check

For new users, run this once after `npm install`:

```powershell
npm run verify:setup
```

This verifies Node/npm availability, required onboarding documents, `.gitignore` safety rules, and a production build. It is the fastest way to check whether another user's Codex workspace is ready to reproduce the same PPT automation workflow.

## Recommended User Flow

1. Choose an 업무 시나리오 such as proposal, kickoff, interim report, final report, evidence pack, or training.
2. Paste the project content or upload source files.
3. Click `1. Storyboard 설계`.
4. Review each slide:
   - 상단 제목
   - Governing message
   - 추천 구조
   - 본문 구조화 항목
   - QA warnings
5. Click `2. 수정 반영 / QA` after editing.
6. Check `Storyboard를 확인했고 이 구조로 PPTX를 생성합니다.`
7. Click `3. PPTX 생성`.
8. Download the generated PPTX.

## ChatGPT Prompt Flow

Use this when you want to continue refinement inside a ChatGPT chat window rather than connecting an API key.

1. Create or revise the storyboard.
2. Click `GPT 프롬프트 생성`.
3. Select one of the prompt modes:
   - `한큐 PPT 생성`
   - `Storyboard 고도화`
   - `PPT QA 리뷰`
   - `PPTX 코드 구현`
4. Click `복사` or `MD 저장`.
5. Paste the prompt into ChatGPT.

## API Status

Direct GPT API execution is intentionally paused.

`.env.example` includes:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5
ENABLE_GPT_API=false
```

Keep `ENABLE_GPT_API=false` unless you intentionally want server-side API calls. This prevents accidental upload of client confidential data.

## Quality Standard

Every deck should satisfy these rules:

- Minimum body font size: 11pt
- Prefer 14pt or higher when space allows
- No text overflow
- No object overlap
- No character-by-character Korean wrapping
- Short labels such as `검토`, `산출`, `관리`, `주의`, `L1`, `L2` stay on one line
- Title and governing message are separate
- Governing message is a consulting claim, not a topic label
- Body bullets are meaningful and not lazy placeholders
- Max 5 bullets per slide
- Long box text is converted into bullets or tables
- Arrows and connectors stay behind text
- Internal production notes are excluded from body slides

## Reference Structure DB

The app now stores consulting deck structures by business type and meeting type.

Current profile examples:

- `reduction + kickoff` -> `reduction-kickoff-starstech`
- `reduction + final` -> `reduction-final-methodology`
- `regulatory + review` -> `regulatory-review-evidence`
- `disclosure + interim` -> `disclosure-interim-score`

This prevents the generator from copying the same layout repeatedly. The planner first chooses the profile, then applies the matching slide archetype sequence and QA rules.

Reference source files can be indexed without copying originals. The index includes both:

- `INPUTS/PPT 장표 레퍼런스`: business/report-specific references such as CDP, reduction projects, regulatory response, and GHG inventory
- `INPUTS/PPT 장표 참고(구조화)`: consulting benchmark and structure references

```powershell
npm run references:index
npm run references:topn
npm run references:refresh
node scripts\build-reference-slide-index.mjs --dry-run
```

The generated index is stored at `docs/reference-source-index.json`. It keeps file paths, classification, slide titles, inferred archetypes, confidence, tags, and review status only. Full slide body text is not stored. All accessible INPUT references are treated as `approved-sample` structure references.

`docs/reference-structure-topn.json` summarizes approved samples into representative Top N structures by business type and report type. The generator uses these approved Top N profiles before falling back to generic template sequences.

`docs/standard-deck-flows.json` locks the first production-ready rhythms:

- `reduction/kickoff`: 감축사업 착수보고
- `disclosure/proposal`: CDP·기후공시 제안서
- `regulatory/final`: 온실가스 인벤토리/규제대응 최종보고

These standard flows are used before Top N. They define the fixed sequence from cover and contents through body proof objects, conclusion, and schedule/action slides.

Logo policy: references are used only for structure, slide format, logic flow, storyline, layout pattern, proof-object placement, and information hierarchy. Logos and brand marks from companies other than INNerGEN are excluded from learning and must not be copied into generated decks.

Reference-style QA can be run with a profile ID:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\reference-style-qa.ps1 `
  -CandidateImageDir "docs\generated\starstech\starstech_phase1_carbon_methodology_report_innergen-render-qa\slides" `
  -ReferenceImageDir "C:\Users\24jos\Downloads\(회의) 스타스테크 폐산 재활용 기술에 대한 온실가스 감축 방법론 개발_260410_ver1.3-render-qa\slides" `
  -ProfileId reduction-kickoff-starstech
```

## Useful Docs

- [Codex Onboarding](docs/codex-onboarding.md)
- [ChatGPT Prompt Generator](docs/gpt-ppt-prompt-generator.md)
- [One-shot Structure and QA Rules](docs/one-shot-structure-qa-rules.md)
- [10 PDCA Improvement Report](docs/10-pdca-improvement-report.md)
- [Quality Improvement Plan](docs/innergen-ppt-quality-improvement-plan.md)
- [Reference Structure DB](docs/reference-structure-db.json)
- [Reference Source Index](docs/reference-source-index.json)
- [Reference Structure Top N](docs/reference-structure-topn.json)
- [Standard Deck Flows](docs/standard-deck-flows.json)
- [Starstech Reference Gap Analysis](docs/starstech-reference-gap-analysis.md)

## Important Safety Note

Do not paste client confidential data, unpublished emissions data, pricing, personal information, or restricted documents into external AI tools unless your organization permits it.

The local PPTX generation flow can run without an OpenAI API key.
