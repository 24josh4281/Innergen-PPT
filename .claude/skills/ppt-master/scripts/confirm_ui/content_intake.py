#!/usr/bin/env python3
"""
PPT Master - Chapter Content Intake

Extend the existing local confirmation server with chapter notes and attachments.
Material submission never approves generation. Final confirmation is bound to the
current complete slide overview and consumed material-response ID.

Usage:
    Loaded by confirm_ui/server.py; no standalone CLI.

Examples:
    See scripts/docs/confirm_ui.md for materials/review payloads.

Dependencies:
    flask (the existing confirmation-server dependency)
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import jsonify, request

MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_SUFFIXES = {
    ".pptx", ".ppt", ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".xlsm",
    ".csv", ".tsv", ".txt", ".md", ".json", ".png", ".jpg", ".jpeg", ".webp",
}


def _current_info(project: Path, read_json) -> dict:
    payload = read_json(project / "confirm_ui/recommendations.json")
    info = payload.get("content_intake", {})
    return info if isinstance(info, dict) else {}


def content_revision(info: dict) -> str:
    """Bind a user's action to the exact agent-authored proposal shown."""
    clean = {k: v for k, v in info.items()
             if k not in {"view_revision", "saved_response", "approval_error", "pending_attachments", "saved_edits"}}
    return hashlib.sha256(json.dumps(clean, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _chapters(info: dict) -> dict:
    chapters = info.get("chapters", [])
    if not isinstance(chapters, list) or not chapters:
        raise ValueError("목차별 입력 항목을 먼저 작성해 주세요.")
    result = {}
    for chapter in chapters:
        if not isinstance(chapter, dict):
            raise ValueError("목차 항목 형식이 잘못되었습니다.")
        cid = chapter.get("id", "")
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cid):
            raise ValueError("목차 ID 형식이 잘못되었습니다.")
        if cid == "shared" or cid in result or not isinstance(chapter.get("title"), str) or not chapter["title"].strip():
            raise ValueError("목차 ID는 중복 없이, 제목과 함께 작성해 주세요.")
        result[cid] = chapter
    return result


def clean_review_edits(raw, slide_count: int) -> dict:
    """Validate live per-slide edits from the outline review (never an approval)."""
    if raw is None:
        return {"slides": {}, "overall": ""}
    if not isinstance(raw, dict):
        raise ValueError("개요 수정 내용 형식이 잘못되었습니다.")
    overall = raw.get("overall", "")
    if not isinstance(overall, str) or len(overall) > 5000:
        raise ValueError("전체 추가 내용은 5,000자 이하로 입력해 주세요.")
    slides = raw.get("slides", {})
    if not isinstance(slides, dict):
        raise ValueError("장표별 수정 내용 형식이 잘못되었습니다.")
    clean = {}
    for page, item in slides.items():
        if not (isinstance(page, str) and page.isdecimal() and 1 <= int(page) <= slide_count):
            raise ValueError("수정한 장표 번호가 개요와 맞지 않습니다. 화면을 새로고침해 주세요.")
        if not isinstance(item, dict) or set(item) - {"title", "core_message", "content", "additions"}:
            raise ValueError(f"{page}번 장표의 수정 항목을 확인해 주세요.")
        out = {}
        for key, limit in (("title", 200), ("core_message", 1000), ("additions", 5000)):
            if key in item:
                if not isinstance(item[key], str) or len(item[key]) > limit:
                    raise ValueError(f"{page}번 장표의 입력 형식이나 길이(제목 200자·핵심 메시지 1,000자·추가 내용 5,000자)를 확인해 주세요.")
                if item[key].strip():
                    out[key] = item[key].strip()
        if "content" in item:
            body = item["content"]
            if not isinstance(body, list) or len(body) > 40 or any(not isinstance(t, str) or len(t) > 1000 for t in body):
                raise ValueError(f"{page}번 장표의 들어갈 내용을 확인해 주세요.")
            body = [t.strip() for t in body if t.strip()]
            if body:
                out["content"] = body
        if out:
            clean[page] = out
    return {"slides": clean, "overall": overall.strip()}


def _saved_edits(project: Path, read_json, revision: str) -> dict:
    path = project / "confirm_ui/review_edits.json"
    record = read_json(path) if path.is_file() else {}
    return record.get("edits", {}) if record.get("revision") == revision else {}


def _latest(project: Path, read_json) -> dict:
    path = project / "confirm_ui/intake_latest.json"
    return read_json(path) if path.is_file() else {}


def _attachment_index(project: Path, read_json) -> dict:
    path = project / "confirm_ui/intake_attachments.json"
    return read_json(path) if path.is_file() else {"files": []}


def prepare_content_payload(data: dict, project: Path, read_json) -> None:
    """Add revision and prior response context without approving content."""
    info = data.get("content_intake")
    if not isinstance(info, dict) or info.get("phase") not in {"materials", "review"}:
        return
    info["view_revision"] = content_revision(info)
    if info.get("phase") == "materials" or info.get("unified"):
        info["pending_attachments"] = [f for f in _attachment_index(project, read_json)["files"]
                                       if f.get("revision") == info["view_revision"]]
    latest = _latest(project, read_json)
    if latest:
        info["saved_response"] = latest
    if info.get("phase") == "review":
        saved = _saved_edits(project, read_json, info["view_revision"])
        if saved:
            info["saved_edits"] = saved
    error = _review_error(info, latest) if info.get("phase") == "review" else None
    if error:
        info["approval_error"] = error


def _review_error(info: dict, latest: dict) -> str | None:
    if not info.get("unified") and (not latest or latest.get("status") != "materials_submitted_not_approved"):
        return "목차별 추가 입력 또는 '추가 자료 없음' 응답을 먼저 확인해 주세요."
    if not info.get("unified") and info.get("materials_response_id") != latest.get("id"):
        return "목차별 최신 입력을 반영한 개요가 필요합니다. 채팅으로 돌아가 개요 갱신을 요청해 주세요."
    if info.get("blocking_gaps"):
        return "제작 전에 확인할 정보가 남아 있습니다. 개요의 확인 필요 항목을 먼저 정리해 주세요."
    try:
        chapters = _chapters(info)
    except ValueError as exc:
        return str(exc)
    slides = info.get("slides", [])
    if not isinstance(slides, list) or not slides:
        return "전체 슬라이드 개요가 필요합니다."
    if not isinstance(info.get("anchor_values", {}), dict):
        return "개요에 사용한 대상·용도 조건을 확인해 주세요."
    for number, slide in enumerate(slides, 1):
        if not isinstance(slide, dict) or type(slide.get("page")) is not int or slide["page"] != number:
            return "슬라이드 개요는 1번부터 실제 제작 순서대로 모두 보여 주세요."
        if slide.get("chapter_id") not in chapters:
            return f"{number}번 슬라이드의 목차 연결이 필요합니다."
        for key in ("title", "core_message", "visual", "source_summary"):
            if not isinstance(slide.get(key), str) or not slide[key].strip():
                return f"{number}번 슬라이드의 제목·핵심 메시지·표현 방식·출처 구분을 모두 작성해 주세요."
        body = slide.get("content")
        if not isinstance(body, list) or not body or any(not isinstance(t, str) or not t.strip() for t in body):
            return f"{number}번 슬라이드에 들어갈 구체적인 내용을 작성해 주세요."
    represented = {s["chapter_id"] for s in slides}
    omissions = info.get("omitted_chapters", {})
    if not isinstance(omissions, dict):
        return "제외한 목차와 이유를 정리해 주세요."
    for cid in chapters:
        if cid not in represented and not omissions.get(cid):
            return "모든 목차를 개요에 연결하거나 제외 이유를 보여 주세요."
    return None


def content_confirmation_error(payload: dict, project: Path, read_json) -> str | None:
    """Reject material-stage approval and stale or incomplete slide reviews."""
    info = _current_info(project, read_json)
    if info.get("phase") == "materials":
        return "추가 정보 제출은 PPT 제작 승인이 아닙니다. 슬라이드별 개요를 먼저 확인해 주세요."
    if info.get("phase") != "review":
        return None
    error = _review_error(info, _latest(project, read_json))
    if error:
        return error
    if payload.get("content_outline_approved") is not True:
        return "슬라이드별 개요에 대한 최종 확인이 필요합니다."
    if payload.get("content_review_token") != content_revision(info):
        return "개요가 변경되었습니다. 화면을 새로고침하여 최신 개요를 확인해 주세요."
    try:
        clean_review_edits(payload.get("content_review_edits"), len(info["slides"]))
    except ValueError as exc:
        return str(exc)
    if info.get("unified"):
        entries = payload.get("content_materials", [])
        if not isinstance(entries, list) or len(entries) > 1:
            return "추가 자료 형식이 잘못되었습니다."
        index = {f["id"]: f for f in _attachment_index(project, read_json)["files"]}
        selected = []
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("chapter_id") != "shared":
                return "추가 자료는 전체 개요에 첨부해 주세요."
            if not isinstance(entry.get("text", ""), str) or len(entry.get("text", "")) > 100000:
                return "추가 내용이 너무 깁니다."
            ids = entry.get("attachments", [])
            if not isinstance(ids, list) or any(not isinstance(fid, str) or fid not in index for fid in ids):
                return "첨부 파일을 다시 확인해 주세요."
            for fid in ids:
                f = index[fid]
                if f.get("revision") != content_revision(info) or f.get("chapter_id") != "shared":
                    return "변경 전 개요에 첨부한 파일입니다. 다시 첨부해 주세요."
                if not (project / f["path"]).is_file():
                    return "첨부 파일을 찾을 수 없습니다. 다시 첨부해 주세요."
                selected.append(f)
        payload["content_material_files"] = selected
        payload["content_reconciliation_required"] = True
        return None
    count = str(payload.get("page_count", "")).strip()
    if count.isdecimal() and int(count) != len(info["slides"]):
        return "장수를 변경하셨습니다. 변경한 장수에 맞춰 슬라이드 개요를 다시 구성한 뒤 최종 확인해 주세요."
    for key, expected in info.get("anchor_values", {}).items():
        if payload.get(key) != expected:
            return f"개요 조건 불일치 ({key}): 개요 기준 '{expected}', 현재 선택 '{payload.get(key)}'. 변경한 조건으로 개요를 갱신한 뒤 최종 확인해 주세요."
    return None


def register_content_routes(app, project: Path, read_json, write_json) -> None:
    """Register local attachment and material-response APIs in the existing app."""
    lock = threading.Lock()

    def validate_action(payload: dict) -> tuple[dict, dict]:
        if request.headers.get("Origin") and request.headers["Origin"] != request.host_url.rstrip("/"):
            raise ValueError("현재 제작 화면에서만 자료를 제출해 주세요.")
        info = _current_info(project, read_json)
        if info.get("phase") != "materials" and not (info.get("phase") == "review" and info.get("unified")):
            raise ValueError("목차별 자료 입력 단계에서만 제출할 수 있습니다.")
        if payload.get("revision") != content_revision(info):
            raise ValueError("목차가 변경되었습니다. 최신 목차를 다시 확인해 주세요.")
        return info, _chapters(info)

    @app.route("/api/intake/review_edits", methods=["POST"])
    def review_edits():
        try:
            if request.content_length and request.content_length > 1024 * 1024:
                return jsonify({"error": "수정 내용은 1MB 이하로 입력해 주세요."}), 413
            if request.headers.get("Origin") and request.headers["Origin"] != request.host_url.rstrip("/"):
                raise ValueError("현재 제작 화면에서만 수정할 수 있습니다.")
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                raise ValueError("개요 수정 내용 형식이 잘못되었습니다.")
            info = _current_info(project, read_json)
            if info.get("phase") != "review":
                raise ValueError("슬라이드 개요 확인 단계에서만 수정할 수 있습니다.")
            if payload.get("revision") != content_revision(info):
                raise ValueError("개요가 변경되었습니다. 화면을 새로고침해 주세요.")
            edits = clean_review_edits(payload.get("edits"), len(info.get("slides", [])))
            record = {"schema": "slide_review_edits.v1", "revision": payload["revision"], "edits": edits,
                      "saved_at": datetime.now(timezone.utc).isoformat(),
                      "status": "draft_not_approved", "generation_authorized": False}
            with lock:
                write_json(project / "confirm_ui/review_edits.json", record)
            return jsonify({"status": record["status"], "slides": len(edits["slides"])})
        except (OSError, ValueError, KeyError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/intake/upload", methods=["POST"])
    def upload():
        try:
            if request.content_length and request.content_length > MAX_UPLOAD_BYTES + 1024 * 1024:
                return jsonify({"error": "파일은 한 개당 100MB 이하로 첨부해 주세요."}), 413
            _, chapters = validate_action(request.form)
            cid = request.form.get("chapter_id")
            if cid not in chapters and cid != "shared":
                raise ValueError("첨부할 목차를 선택해 주세요.")
            file = request.files.get("file")
            if file is None or not file.filename:
                raise ValueError("첨부 파일이 없습니다.")
            original_name = re.split(r"[/\\]", file.filename)[-1][:240]
            suffix = Path(original_name).suffix.lower()
            if suffix not in ALLOWED_SUFFIXES:
                raise ValueError("PPT·PDF·문서·표·텍스트·이미지 파일을 첨부해 주세요.")
            raw = file.stream.read(MAX_UPLOAD_BYTES + 1)
            if len(raw) > MAX_UPLOAD_BYTES:
                return jsonify({"error": "파일은 한 개당 100MB 이하로 첨부해 주세요."}), 413
            if not raw:
                raise ValueError("빈 파일은 첨부할 수 없습니다.")
            digest = hashlib.sha256(raw).hexdigest()
            with lock:
                index = _attachment_index(project, read_json)
                for prior in index["files"]:
                    if prior["sha256"] == digest and prior["chapter_id"] == cid:
                        if (project / prior["path"]).is_file():
                            prior["revision"] = request.form.get("revision")
                            write_json(project / "confirm_ui/intake_attachments.json", index)
                            return jsonify({"file": prior, "reused": True})
                folder = (project / "sources/intake").resolve()
                if not folder.is_relative_to(project.resolve()):
                    raise ValueError("프로젝트 자료 폴더의 위치를 확인해 주세요.")
                folder.mkdir(parents=True, exist_ok=True)
                file_id = "UP-" + uuid.uuid4().hex
                target = folder / (file_id + suffix)
                with target.open("xb") as stream:
                    stream.write(raw)
                record = {"id": file_id, "chapter_id": cid, "name": original_name,
                          "path": target.relative_to(project).as_posix(), "sha256": digest,
                          "bytes": len(raw), "read_status": "unread", "revision": request.form.get("revision")}
                index["files"].append(record)
                write_json(project / "confirm_ui/intake_attachments.json", index)
            return jsonify({"file": record, "reused": False})
        except (OSError, ValueError, KeyError) as exc:
            return jsonify({"error": str(exc)}), 400

    @app.route("/api/intake/materials", methods=["POST"])
    def materials():
        try:
            if request.content_length and request.content_length > 4 * 1024 * 1024:
                return jsonify({"error": "설명은 나눠서 입력해 주세요. 입력량 한도는 4MB입니다."}), 413
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                raise ValueError("목차별 입력 형식이 잘못되었습니다.")
            _, chapters = validate_action(payload)
            choice = payload.get("additional_information")
            if choice not in {"yes", "no"}:
                raise ValueError("추가 입력·첨부 여부를 선택해 주세요.")
            entries = payload.get("entries", [])
            if not isinstance(entries, list):
                raise ValueError("목차별 입력은 목록으로 제출해 주세요.")
            with lock:
                files = {f["id"]: f for f in _attachment_index(project, read_json)["files"]}
                seen = set()
                for entry in entries:
                    if not isinstance(entry, dict) or entry.get("chapter_id") not in {*chapters, "shared"}:
                        raise ValueError("입력 내용과 목차를 연결해 주세요.")
                    cid = entry["chapter_id"]
                    if cid in seen:
                        raise ValueError("동일 목차의 입력을 하나로 합쳐 주세요.")
                    seen.add(cid)
                    if not isinstance(entry.get("text", ""), str) or len(entry.get("text", "")) > 100000:
                        raise ValueError("설명은 목차별로 100,000자 이하로 입력해 주세요.")
                    ids = entry.get("attachments", [])
                    if not isinstance(ids, list) or any(not isinstance(i, str) or i not in files for i in ids):
                        raise ValueError("첨부 파일을 먼저 저장해 주세요.")
                    if any(files[i]["chapter_id"] not in {cid, "shared"} for i in ids):
                        raise ValueError("첨부 파일의 목차 연결을 확인해 주세요.")
                if choice == "no" and any(e.get("text", "").strip() or e.get("attachments") for e in entries):
                    raise ValueError("추가 입력이 있으면 '추가할 정보가 있습니다'를 선택해 주세요.")
                if choice == "yes" and not any(e.get("text", "").strip() or e.get("attachments") for e in entries):
                    raise ValueError("설명이나 파일을 하나 이상 추가하거나 '추가 자료 없음'을 선택해 주세요.")
                response_id = "IN-" + uuid.uuid4().hex
                selected = {i for e in entries for i in e.get("attachments", [])}
                record = {"schema": "chapter_material_response.v27", "id": response_id,
                          "revision": payload["revision"], "additional_information": choice,
                          "entries": entries, "files": [files[i] for i in sorted(selected)],
                          "submitted_at": datetime.now(timezone.utc).isoformat(),
                          "status": "materials_submitted_not_approved", "generation_authorized": False}
                write_json(project / f"confirm_ui/intake_responses/{response_id}.json", record)
                write_json(project / "confirm_ui/intake_latest.json", record)
            return jsonify({"status": record["status"], "id": response_id,
                            "message": "자료를 저장했습니다. 채팅으로 돌아가면 슬라이드별 개요를 구성합니다."})
        except (OSError, ValueError, KeyError) as exc:
            return jsonify({"error": str(exc)}), 400
