# Adaptive Presentation Intake

`presentation_intake.py` organizes agent-reviewed content metadata into questions,
type-specific outline suggestions and evidence-link checks. The runtime behavior
is defined in [`presentation-intake.md`](../../references/presentation-intake.md).

## Brief schema

Write this after reading the relevant chat and files. Fields have a value and a
basis: `user` means explicitly supplied by the user (including standing choices),
`source` means supported by linked evidence, and `inferred` means an agent proposal
with a reason. An inferred value is never silently promoted to a confirmed fact.

```json
{
  "schema": "presentation_brief.v26",
  "fields": {
    "objective": {"value": "검토 안건의 승인", "basis": "user"},
    "audience": {"value": "실무 검토위원", "basis": "user"},
    "deck_type": {"value": "interim", "basis": "user"},
    "business_type": {"value": "cdp_disclosure", "basis": "user"},
    "scope": {"value": "증빙 수집 현황", "basis": "user"},
    "as_of": {"value": "2026-10-14", "basis": "source", "evidence": ["E1"]},
    "achievements": {"value": "검토 이슈 확인", "basis": "source", "evidence": ["E1"]},
    "decision": {"value": "증빙 검토 담당 지정", "basis": "user"}
  },
  "sources": [
    {"id": "S1", "path": "projects/demo/sources/progress.md", "role": "content",
     "read_status": "read", "read_locations": ["검토 이슈"]}
  ],
  "evidence": [
    {"id": "E1", "source_id": "S1", "locator": "검토 이슈", "kind": "text", "coverage": "required"}
  ],
  "conflicts": [],
  "page_count": 12
}
```

| Optional input | Contract |
|---|---|
| `user_outline` | Array of page objects with `title`; exact user titles/order win over the catalog |
| `page_count` | Exact integer if the user requested an exact count; omit for an unconfirmed estimate |
| Source `url` / `conversation` | Alternative to a local path, not an excuse to claim an unread file was read |
| Source `remaining_locations` | Unread coverage for partial files |
| Evidence `kind: numeric` | Requires `unit` and `period`; raw value stays at its owning source location |
| Evidence `kind: regulatory` | Requires `jurisdiction` and `version` |
| Conflict | `summary`, `status: unresolved/resolved`; resolved entries require `resolution_basis` |

The 16 deck IDs and 13 business IDs are in `docs/presentation-intake-v26.json`.
Unknown IDs fail clearly; other business work uses `general`. Do not keyword-match
a report type automatically from a file name. The agent interprets the actual task.

## User-selected sequence (v29)

Missing report/business classification is asked first as one bundle. Once it is
known, propose the TOC and offer optional files or one short note before
writing the complete slide overview. `plan` adds a `workflow_v27` block with the
sequence and draft `chapter_requests`. Replace generic chapter names/questions
with the agent's concrete interpretation; treat requests as optional hints, not
required form fields. The compatibility `workflow_v27` object carries `version:
29` and `intake_mode: file_first_optional`. After classification, read supplied
content first and show at most one required follow-up question; optional style,
time and delivery preferences are not mandatory questions. Brief `chapters[]` carries
agent-authored IDs, titles, purposes and requests. The existing final confirmation
must review all slides. File submission alone never approves production.

The page and local attachment protocol are documented in
[`confirm_ui.md`](./confirm_ui.md) under v29. Browse and drag/drop share the local
upload API; the UI derives legacy yes/no from actual input without another choice.
The parser/classifier does not author
slides, interpret attachments or create a generation approval.

## Commands and outputs

```bash
python3 scripts/presentation_intake.py plan <brief.json> -o <analysis_dir>
python3 scripts/presentation_intake.py check <brief.json> <outline.json> -o <new_report.json>
```

`plan` writes `intake_plan_v26.json/md`. Changed inputs get `_r2`, `_r3`, etc.;
identical input, planner/catalog version and source hashes reuse the completed
plan without regeneration. A missing Markdown companion is repaired without
overwriting the JSON plan.
`check` refuses to overwrite an existing report. Neither command edits a source,
launches a browser, changes a design lock or authorizes PPT generation.

Readiness means `needs_answers`, `needs_source_reading` or `ready_for_owner_review`.
It never means approved. The current owner still owns confirmation and final QA.
The plan's `content_intake` object is suitable for the existing Confirm UI after
the agent replaces generic chapter labels with its concrete recommended outline.

## Outline schema

```json
{
  "pages": [
    {
      "title": "검토 담당을 지정해야 증빙 확인을 완료할 수 있습니다",
      "purpose": "검토 지연의 원인과 의사결정 안건을 연결합니다",
      "layout_reason": "담당·자료·기한의 관계를 표로 보여 줍니다",
      "claims": [
        {"id": "C1", "status": "sourced", "evidence": ["E1"]}
      ]
    }
  ],
  "omitted_evidence": {}
}
```

Use `sourced`, `derived`, `assumption`, `illustrative` or `pending` claim status.
Derived claims require input evidence, formula and explicit assumptions.
Assumptions/examples/pending claims require an intended `visible_label` and remain
warnings rather than confirmed results. Required source units need a visible claim
placement or an explicit omission reason. The agent must map every substantive
message into the claim records and check the actual original meaning.

The helper checks declared traceability, not numerical accuracy, source truth,
legal applicability or rendered layout. A successful metadata check is not final
deck verification.
