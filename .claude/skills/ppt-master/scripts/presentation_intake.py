#!/usr/bin/env python3
"""
PPT Master - Presentation Intake Planner

Turn agent-reviewed brief metadata into prioritized questions, source requests
and a type-specific outline recommendation. Never read binary source content,
infer business facts, approve a plan, or generate slides. See
references/presentation-intake.md for the agent's interpretation contract.

Usage:
    python scripts/presentation_intake.py plan <brief.json> -o <analysis_dir>
    python scripts/presentation_intake.py check <brief.json> <outline.json>

Examples:
    python scripts/presentation_intake.py plan projects/demo/analysis/brief_v26.json -o projects/demo/analysis

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parents[3]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from console_encoding import configure_utf8_stdio  # noqa: E402

CATALOG_PATH = ROOT / "docs/presentation-intake-v26.json"


def read_object(path: Path) -> dict:
    """Read UTF-8 JSON and reject non-object inputs."""
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def load_catalog() -> tuple[dict, dict]:
    """Load intake guidance and the existing architecture authority."""
    catalog = read_object(CATALOG_PATH)
    architecture = read_object(ROOT / catalog["architecture"])
    if set(catalog["deck_types"]) != set(architecture["deck_types"]):
        raise ValueError("Intake deck types differ from the v20 architecture; reconcile the catalog.")
    return catalog, architecture


def field_value(brief: dict, key: str) -> object:
    """Return a value only from the structured brief field."""
    return brief.get("fields", {}).get(key, {}).get("value")


def _source_path(source: dict) -> Path | None:
    if not source.get("path"):
        return None
    path = Path(source["path"])
    return path if path.is_absolute() else ROOT / path


def validate_brief(brief: dict, catalog: dict) -> list[str]:
    """Check metadata traceability without claiming source meaning was verified."""
    errors = []
    if brief.get("schema") != "presentation_brief.v26":
        errors.append("Set schema to presentation_brief.v26.")
    fields = brief.get("fields", {})
    if not isinstance(fields, dict):
        return errors + ["fields must be an object."]
    authored = brief.get("user_outline")
    if authored is not None and (not isinstance(authored, list) or
                                any(not isinstance(p, dict) or not p.get("title") for p in authored)):
        errors.append("user_outline must be an array of titled page objects.")
    count = brief.get("page_count")
    if count is not None and (type(count) is not int or count < 1):
        errors.append("page_count must be a positive exact integer; put timing/range preferences in fields.timing.")
    for key, field in fields.items():
        if key not in catalog["fields"] or not isinstance(field, dict):
            errors.append(f"Unknown or malformed brief field: {key}.")
            continue
        if field.get("value") in (None, "", []):
            continue
        if field.get("basis") not in {"user", "source", "inferred"}:
            errors.append(f"{key}: basis must be user, source or inferred.")
        if field.get("basis") == "inferred" and not field.get("reason"):
            errors.append(f"{key}: give the inference reason.")
        if field.get("basis") == "source" and not field.get("evidence"):
            errors.append(f"{key}: source-based fields require evidence references.")
    deck_type = field_value(brief, "deck_type")
    business = field_value(brief, "business_type")
    if deck_type and deck_type not in catalog["deck_types"]:
        errors.append(f"Unknown deck_type: {deck_type}; use a catalog ID.")
    if business and business not in catalog["business_types"]:
        errors.append(f"Unknown business_type: {business}; use general for other work.")
    sources = brief.get("sources", [])
    if not isinstance(sources, list) or any(not isinstance(s, dict) for s in sources):
        return errors + ["sources must be an array of objects."]
    source_ids = [s.get("id") for s in sources]
    if any(not sid for sid in source_ids) or len(set(source_ids)) != len(source_ids):
        errors.append("Each source needs a unique non-empty id.")
    for source in sources:
        sid = source.get("id", "?")
        if source.get("role") not in {"content", "design", "context"}:
            errors.append(f"{sid}: set role to content, design or context.")
        if source.get("read_status") not in {"read", "partial", "unread", "failed"}:
            errors.append(f"{sid}: set read_status to read, partial, unread or failed.")
        if not source.get("path") and not source.get("url") and not source.get("conversation"):
            errors.append(f"{sid}: provide path, URL or conversation reference.")
        if source.get("read_status") in {"read", "partial"} and not source.get("read_locations"):
            errors.append(f"{sid}: record locations actually read.")
        path = _source_path(source)
        if path and not path.is_file() and source.get("read_status") in {"read", "partial"}:
            errors.append(f"{sid}: file unavailable: {path}; correct the path or record read_status as failed.")
    evidence = brief.get("evidence", [])
    if not isinstance(evidence, list) or any(not isinstance(e, dict) for e in evidence):
        return errors + ["evidence must be an array of source pointers."]
    evidence_ids = [e.get("id") for e in evidence]
    if any(not eid for eid in evidence_ids) or len(set(evidence_ids)) != len(evidence_ids):
        errors.append("Each evidence pointer needs a unique non-empty id.")
    by_source = {s.get("id"): s for s in sources}
    for item in evidence:
        eid = item.get("id", "?")
        source = by_source.get(item.get("source_id"))
        if not source or not item.get("locator"):
            errors.append(f"{eid}: reference an existing source and a precise locator.")
            continue
        if source.get("read_status") not in {"read", "partial"}:
            errors.append(f"{eid}: unread source cannot support evidence.")
        if source.get("role") == "design":
            errors.append(f"{eid}: design references cannot supply current business facts.")
        if item.get("kind") not in {"text", "numeric", "regulatory", "image"}:
            errors.append(f"{eid}: choose text, numeric, regulatory or image kind.")
        if item.get("kind") == "numeric" and (not item.get("unit") or not item.get("period")):
            errors.append(f"{eid}: numeric pointers require unit and period; use explicit not-applicable when justified.")
        if item.get("kind") == "regulatory" and (not item.get("jurisdiction") or not item.get("version")):
            errors.append(f"{eid}: regulatory pointers require jurisdiction and version.")
    for key, field in fields.items():
        if isinstance(field, dict):
            for eid in field.get("evidence", []):
                if eid not in evidence_ids:
                    errors.append(f"{key}: unknown evidence pointer {eid}.")
    conflicts = brief.get("conflicts", [])
    if not isinstance(conflicts, list) or any(not isinstance(c, dict) for c in conflicts):
        return errors + ["conflicts must be an array of objects."]
    for conflict in conflicts:
        if conflict.get("status") not in {"unresolved", "resolved"} or not conflict.get("summary"):
            errors.append("Each conflict needs summary and unresolved/resolved status.")
        if conflict.get("status") == "resolved" and not conflict.get("resolution_basis"):
            errors.append("Resolved conflicts require a resolution_basis.")
    return errors


def build_plan(brief: dict) -> dict:
    """Prioritize unanswered questions and suggest a sourced content plan."""
    catalog, architecture = load_catalog()
    errors = validate_brief(brief, catalog)
    if errors:
        raise ValueError("\n".join(errors))
    deck_id = field_value(brief, "deck_type")
    business_id = field_value(brief, "business_type") or "general"
    type_guide = catalog["deck_types"].get(deck_id, {})
    required = ["deck_type", "business_type", "objective", "audience", "scope"] + type_guide.get("fields", [])
    candidates = []
    unresolved = [c for c in brief.get("conflicts", []) if c["status"] == "unresolved"]
    for idx, conflict in enumerate(unresolved):
        candidates.append({"id": "conflict_" + str(idx + 1), "priority": 1000 - idx,
                           "required": True, "question": conflict["summary"] + " 어느 자료를 기준으로 할까요?",
                           "why": "서로 다른 값을 자동 선택하지 않습니다."})
    for key in dict.fromkeys(required + ["business_type", "timing", "delivery", "style"]):
        field = brief.get("fields", {}).get(key, {})
        if field.get("value") not in (None, "", []) and field.get("basis") != "inferred":
            continue
        definition = copy.deepcopy(catalog["fields"][key])
        definition.update({"id": key, "required": key in required})
        if field.get("value") not in (None, "", []):
            definition["question"] = f"{field['value']}로 이해했습니다. " + definition["question"]
            definition["proposed_value"] = field["value"]
        candidates.append(definition)
    candidates.sort(key=lambda q: (not q["required"], -q["priority"]))
    classifiers = [q for q in candidates if q["id"] in {"deck_type", "business_type"}]
    missing_required = [q["id"] for q in candidates if q["required"]]
    source_checks = []
    for source in brief.get("sources", []):
        status = source["read_status"]
        row = {"id": source["id"], "role": source["role"], "read_status": status,
               "read_locations": source.get("read_locations", []),
               "remaining_locations": source.get("remaining_locations", [])}
        path = _source_path(source)
        if path and path.is_file():
            row["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        if status in {"unread", "failed"}:
            row["next_action"] = "담당 에이전트가 파일을 읽거나 읽기 실패 원인을 확인합니다."
        elif status == "partial":
            row["next_action"] = "사용할 내용의 원문 위치를 확인합니다. 전체 파일 학습 완료로 표현하지 않습니다."
        source_checks.append(row)
    content_unread = any(s["role"] == "content" and s["read_status"] in {"unread", "failed"}
                         for s in source_checks)
    # Read supplied content before burdening the user with another questionnaire.
    first_questions = (classifiers if classifiers else [] if content_unread else
                       [q for q in candidates if q["required"]][:1])
    remaining_questions = [q for q in candidates if q not in first_questions]
    type_record = architecture["deck_types"].get(deck_id, {})
    base = architecture["deck_types"].get("lecture", {}) if deck_id == "handout" else type_record
    outline = copy.deepcopy(brief.get("user_outline") or base.get("toc", []))
    must_have = ["핵심 지표(검증 가능한 원값이 있을 때)" if t == "큰 숫자 3개" else t
                 for t in base.get("must_have", [])]
    if deck_id == "handout":
        must_have.append("조건·예외를 문장으로 보존")
    business = catalog["business_types"][business_id]
    chapters = copy.deepcopy(brief.get("chapters") or [
        {"id": f"ch{index:02d}", "title": title,
         "purpose": "이 목차에 들어갈 요점과 근거를 정리합니다.",
         "requests": ["이 목차에서 강조할 내용이 있으면 짧게 적어주세요. (선택)"]}
        for index, title in enumerate(type_guide.get("key_slides", []), 1)
    ])
    readiness = ("needs_answers" if classifiers else "needs_source_reading" if content_unread else
                 "needs_answers" if missing_required else "ready_for_owner_review")
    fingerprint = hashlib.sha256(json.dumps(brief, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    fingerprint.update(Path(__file__).read_bytes())
    fingerprint.update(CATALOG_PATH.read_bytes())
    fingerprint.update((ROOT / catalog["architecture"]).read_bytes())
    for source in source_checks:
        fingerprint.update(source.get("sha256", "").encode("ascii"))
    toc_labels = ([item.get("title") or item.get("chapter", "") for item in outline]
                  if isinstance(outline, list) else [outline])
    content_summary = {
        "revision": fingerprint.hexdigest(), "title": "자료 해석과 권장 구성",
        "known": [str(field["value"]) for field in brief.get("fields", {}).values()
                  if field.get("value") and field.get("basis") in {"user", "source"}][:4],
        "outline": toc_labels, "key_slides": type_guide.get("key_slides", [])[:6],
        "gaps": [q["question"] for q in candidates if q["required"]][:3],
        "sources": [f"{s['id']} / {s['role']} / {s['read_status']} / {s['read_locations']}"
                    for s in source_checks],
        "note": "구성 제안입니다. 대상·유형·분량을 바꾸면 제작 전에 목차를 다시 조정합니다."
    }
    return {
        "schema": "presentation_intake_plan.v26", "input_sha256": fingerprint.hexdigest(),
        "status": "suggested_not_confirmed", "readiness": readiness,
        "known_fields": brief.get("fields", {}), "deck_type": deck_id,
        "business_type": business_id, "questions": first_questions,
        "question_context": "before_toc_classification" if classifiers else "after_toc_with_chapter_input",
        "remaining_questions": remaining_questions, "missing_required": missing_required,
        "source_checks": source_checks, "evidence": brief.get("evidence", []),
        "conflicts": brief.get("conflicts", []), "proposed_toc": outline,
        "outline_basis": "current_user" if brief.get("user_outline") else "v20_reference_skeleton",
        "key_slides": type_guide.get("key_slides", []), "must_have": must_have,
        "requested_materials": type_guide.get("materials", []),
        "business_evidence_requests": business["evidence"], "business_modules": business["modules"],
        "cautions": [business["caution"],
                     "목차·장수·가정은 해당 제작 경로의 기존 확인 단계에서 검토합니다."],
        "page_count": {"user_constraint": brief.get("page_count"),
                       "reference_only": type_record.get("pages"),
                       "note": "자료량·시간·전달 방식으로 다시 제안하며 참고 장수로 강제하지 않습니다."},
        "generation_authorized": False,
        "workflow_v27": {
            "version": "29", "intake_mode": "file_first_optional",
            "phase": "classify" if classifiers else "chapter_inputs",
            "sequence": ["보고 형태·사업 성격 확인", "권장 목차 제안", "선택 파일·메모 / 기존 정보로 진행",
                         "자료 해석·전체 슬라이드 개요", "최종 확인", "PPT 제작·검수"],
            "additional_question": "파일이나 짧은 메모를 넣어주세요. 추가 입력 없이 진행해도 괜찮아요.",
            "chapter_requests": chapters,
            "note": "파일을 먼저 해석하고 꼭 필요한 빈칸만 하나씩 확인합니다. 목차별 입력은 선택이며 자료 제출은 제작 승인이 아닙니다."
        },
        "content_intake": content_summary,
        "needs_agent_synthesis": "원문 해석·주장 작성·의미 검수는 에이전트 작업입니다. 이 도구는 메타데이터만 점검합니다."
    }


def render_plan(plan: dict) -> str:
    """Render the compact Korean analysis companion."""
    rows = ["# PPT 제작 질문·구성 제안 v26", "", "상태: " + plan["readiness"],
            "이 문서는 제작 전 구성 제안이며 승인·원문 의미 검수 결과가 아닙니다.", "",
            "## 확인된 정보", ""]
    for key, field in plan["known_fields"].items():
        if field.get("basis") in {"user", "source"}:
            rows.append(f"- {key}: {field.get('value')} ({field.get('basis')})")
    inferred = [(key, f) for key, f in plan["known_fields"].items() if f.get("basis") == "inferred"]
    if inferred:
        rows += ["", "## 아직 확정되지 않은 추정", ""]
        rows += [f"- {key}: {f.get('value')} — {f.get('reason')}" for key, f in inferred]
    rows += ["", "## 이번에 필요한 질문(유형 확인은 함께, 이후 필요한 질문 1개)", ""]
    for q in plan["questions"]:
        rows.append(f"- {q['question']} — {q['why']}")
    rows += ["", "## 목차 제안", "", json.dumps(plan["proposed_toc"], ensure_ascii=False, indent=2),
             "", "## 주로 쓰는 장표", ""]
    rows += ["- " + item for item in plan["key_slides"]]
    rows += ["", "## 자료 요청 후보(읽은 자료와 대조해 실제 빈칸만 요청)", ""]
    rows += ["- " + item for item in plan["requested_materials"] + plan["business_evidence_requests"]]
    rows += ["", "## 사업별 본문 모듈", ""] + ["- " + t for t in plan["business_modules"]]
    rows += ["", "## 자료 읽기·출처 기록", ""]
    rows += [f"- {s['id']}: {s['role']} / {s['read_status']} / {s['read_locations']}"
             for s in plan["source_checks"]]
    rows += ["", "## 적용 한계", ""] + ["- " + t for t in plan["cautions"]]
    return "\n".join(rows) + "\n"


def check_outline(brief: dict, outline: dict) -> dict:
    """Check evidence links, unresolved claims and explicit outline preservation."""
    catalog, _ = load_catalog()
    errors = validate_brief(brief, catalog)
    warnings = []
    if errors:
        return {"passed": False, "errors": errors, "warnings": warnings}
    pages = outline.get("pages", [])
    if not isinstance(pages, list) or not pages or any(not isinstance(p, dict) for p in pages):
        return {"passed": False, "errors": errors + ["Outline needs a non-empty pages array."], "warnings": []}
    evidence_ids = {e["id"] for e in brief.get("evidence", [])}
    claims_seen = set()
    used = set()
    for index, page in enumerate(pages, 1):
        if not page.get("title") or not page.get("purpose") or not page.get("layout_reason"):
            errors.append(f"P{index:02d}: title, purpose and layout_reason are required.")
        claims = page.get("claims", [])
        if not isinstance(claims, list) or any(not isinstance(c, dict) for c in claims):
            errors.append(f"P{index:02d}: claims must be an array of objects.")
            continue
        for claim in claims:
            cid = claim.get("id")
            if not cid or cid in claims_seen:
                errors.append(f"P{index:02d}: claims need unique non-empty IDs.")
            claims_seen.add(cid)
            status = claim.get("status")
            links = claim.get("evidence", [])
            if not isinstance(links, list) or any(not isinstance(e, str) for e in links):
                errors.append(f"P{index:02d}/{cid}: evidence must be an array of IDs.")
                continue
            if status in {"sourced", "derived"} and not links:
                errors.append(f"P{index:02d}/{cid}: substantive claims require evidence.")
            if status == "derived" and (not claim.get("formula") or not claim.get("assumptions")):
                errors.append(f"P{index:02d}/{cid}: derived claims need formula and assumptions.")
            if status in {"assumption", "illustrative", "pending"}:
                if not claim.get("visible_label"):
                    errors.append(f"P{index:02d}/{cid}: assumptions/examples/pending claims need a visible label.")
                warnings.append(f"P{index:02d}/{cid}: {status}; not a confirmed project result.")
            elif status not in {"sourced", "derived"}:
                errors.append(f"P{index:02d}/{cid}: unknown claim status.")
            for eid in links:
                if eid not in evidence_ids:
                    errors.append(f"P{index:02d}/{cid}: unknown evidence {eid}.")
                used.add(eid)
    omitted = outline.get("omitted_evidence", {})
    if not isinstance(omitted, dict):
        errors.append("omitted_evidence must map evidence IDs to omission reasons.")
        omitted = {}
    for item in brief.get("evidence", []):
        if item.get("coverage") == "required" and item["id"] not in used and not omitted.get(item["id"]):
            errors.append(f"Required source unit {item['id']} has no visible placement or omission reason.")
    if any(c["status"] == "unresolved" for c in brief.get("conflicts", [])):
        errors.append("Resolve source conflicts or remove affected claims before finalizing the outline.")
    authored = brief.get("user_outline")
    if isinstance(authored, list) and [p.get("title") for p in pages] != [p.get("title") for p in authored]:
        errors.append("Current user-authored page order/titles changed; preserve them or obtain the user's revision.")
    limit = brief.get("page_count")
    if isinstance(limit, int) and len(pages) != limit:
        errors.append(f"User requested {limit} pages; outline has {len(pages)}.")
    return {"passed": not errors, "errors": errors, "warnings": warnings,
            "checked_pages": len(pages), "checked_claims": len(claims_seen),
            "scope": "Evidence metadata and declared coverage only; source meaning and rendered PPT are not checked."}


def build_parser() -> argparse.ArgumentParser:
    """Build the side-effect-free help interface."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan", help="Plan questions and recommended structures from a reviewed brief.")
    plan.add_argument("brief", type=Path)
    plan.add_argument("-o", "--output", type=Path, required=True)
    check = sub.add_parser("check", help="Check an agent-written page outline's evidence links.")
    check.add_argument("brief", type=Path)
    check.add_argument("outline", type=Path)
    check.add_argument("-o", "--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the planner without overwriting source inputs or existing versions."""
    configure_utf8_stdio()
    args = build_parser().parse_args(argv)
    try:
        brief = read_object(args.brief)
        if args.command == "check":
            result = check_outline(brief, read_object(args.outline))
            rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if args.output:
                if args.output.exists():
                    raise ValueError(f"Output exists: {args.output}; use a new report filename.")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(rendered, encoding="utf-8")
            print(rendered, end="")
            return 0 if result["passed"] else 1
        plan = build_plan(brief)
        args.output.mkdir(parents=True, exist_ok=True)
        target = args.output / "intake_plan_v26.json"
        suffix = 1
        while target.exists():
            old = read_object(target)
            if old.get("input_sha256") == plan["input_sha256"]:
                if not target.with_suffix(".md").is_file():
                    target.with_suffix(".md").write_text(render_plan(plan), encoding="utf-8")
                    print(f"REPAIRED COMPANION: {target.with_suffix('.md')}")
                    return 0
                print(f"UNCHANGED: {target}")
                return 0
            suffix += 1
            target = args.output / f"intake_plan_v26_r{suffix}.json"
        target.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        target.with_suffix(".md").write_text(render_plan(plan), encoding="utf-8")
        print(f"{plan['readiness']}: {target}; {len(plan['questions'])} questions; not confirmed")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
