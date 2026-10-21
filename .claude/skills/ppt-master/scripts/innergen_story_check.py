#!/usr/bin/env python3
"""
PPT Master - INNerGEN storyline & content-quality gate (v32)

Reads a deck as a consultant would: the table of contents, the governing
messages in order (the "ghost deck"), how each governing is grounded in its
page and in the source documents, whether diagram pages carry the relation
they draw, and whether the closing answers the opening with concrete next
actions. innergen_qaqc.py checks each page's grammar and chrome; this script
checks the argument across pages. Rules and lexicons live in
docs/styles/innergen/content-principles-v32.json (described in
content-principles-v32.md).

It also gates the independent AI content review (content-review-v32.md): the
reviewer reads analysis/storyline_ghost.md, scores the five roles and writes
analysis/content_review.json; --review checks that record is complete, cites
the current ghost-deck hash and clears the score floor.

Usage:
    python3 scripts/innergen_story_check.py <project_path> [--deck-type proposal]
        [--outline <plan.md|plan.json>]   # plan stage: check the outline before drawing
        [--review analysis/content_review.json] [--sources sources/] [--strict]

Outputs:
    <project>/analysis/storyline_ghost.md        ghost deck for the reviewer
    <project>/analysis/story_pages.json          every page's visible text for the reviewer
    <project>/analysis/story_check_report.md/.json
    exit 1 on ERROR (or WARN with --strict)

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
from console_encoding import configure_utf8_stdio  # noqa: E402
import innergen_content_check as content_check  # noqa: E402
import innergen_qaqc as qaqc  # noqa: E402

REPO = _SCRIPTS_DIR.parents[min(3, len(_SCRIPTS_DIR.parents) - 1)]
RULES_PATH = REPO / "docs/styles/innergen/content-principles-v32.json"
# Standalone skill bundles (build_chat_skill.py) ship the rule table beside the skill.
if not RULES_PATH.is_file():
    RULES_PATH = _SCRIPTS_DIR.parent / "references/content-principles-v32.json"

ROLE_WORDS = {
    "cover": ("cover", "표지"),
    "toc": ("toc", "목차", "contents", "agenda"),
    "divider": ("section-divider", "divider", "chapter", "간지", "장구분"),
    "ending": ("ending", "맺음", "thank", "감사"),
}


# ---------------------------------------------------------------- page model
class StoryPage:
    """Title, governing and body text of one page, drawn or planned."""

    def __init__(self, index: int, name: str, layout: str, title: str, governing: str,
                 body: list[str], toc_items: list[str] | None = None, slots: dict | None = None,
                 has_source: bool = False):
        self.index, self.name, self.layout = index, name, (layout or "").lower()
        self.has_source = has_source
        self.title, self.governing = title.strip(), governing.strip()
        self.body = [b for b in body if b and b not in (self.title, self.governing)]
        self.toc_items = toc_items or []
        self.slots = slots or {}
        key = f"{self.layout} {name}".lower()
        self.role = next((r for r, words in ROLE_WORDS.items() if any(w in key for w in words)), "content")

    @property
    def body_text(self) -> str:
        return " ".join(self.body)

    @property
    def all_text(self) -> str:
        return " ".join([self.title, self.governing, self.body_text])


def _group_text(page: "qaqc.Page", keys: tuple[str, ...], skip: tuple[str, ...] = ("rule", "line", "bar")) -> str:
    # A slot id sits on the <text> itself or on its parent <g>; the text id wins.
    for field in ("id", "group"):
        for t in page.texts:
            gid = (t[field] or "").lower()
            if gid and any(k in gid for k in keys) and not any(s in gid for s in skip) and t["text"]:
                return t["text"]
    return ""


def pages_from_project(project: Path, rules: dict) -> list[StoryPage]:
    """Parse svg_output with innergen_qaqc's page model; fall back to slot ids
    (`page-title`, `governing`) when the family geometry does not match."""
    files = sorted((project / "svg_output").glob("*.svg")) or sorted((project / "svg_final").glob("*.svg"))
    raw = [qaqc.Page(p, i + 1) for i, p in enumerate(files)]
    if not raw:
        return []
    qrules = json.loads(qaqc.RULES_PATH.read_text(encoding="utf-8"))
    family = None
    prof = project / "design_profile_v17.json"
    if prof.exists():
        try:
            family = json.loads(prof.read_text(encoding="utf-8")).get("family")
        except (OSError, ValueError):
            family = None
    detected = qaqc.detect_family(raw, family, qrules)
    fam = qrules["families"].get(detected) or qrules["families"]["innergen_lecture"]
    out = []
    for p in raw:
        p.bind(fam)
        title = _group_text(p, ("page-title", "title")) or (p.title["text"] if p.title else "")
        governing = _group_text(p, ("governing", "key-message")) or (p.governing["text"] if p.governing else "")
        skip = {id(x) for x in (p.footer_label, p.page_number, p.source) if x is not None}
        body = [t["text"] for t in p.texts if t["text"] and id(t) not in skip
                and not re.search(r"footer|page-number|source", (t["group"] or t["id"] or "").lower())]
        if not title:  # largest bold text in the top band
            top = [t for t in p.texts if t["text"] and t["y"] < fam["canvas"][1] * 0.18]
            if top:
                title = max(top, key=lambda t: t["size"])["text"]
        toc_items = [t["text"] for t in p.texts
                     if any(re.match(r"toc-(item-)?\d+-title", t[k] or "") for k in ("id", "group"))]
        if p.page_number is not None:
            skip.add(id(p.page_number))
        if not toc_items and re.search(r"toc|목차|contents|agenda", f"{p.layout} {p.path.stem}", re.I):
            # Untemplated TOC: chapter rows are the numbered lines that are not page ranges.
            numbered = re.compile(rules["toc"]["numbering_regex"])
            toc_items = [t["text"] for t in p.texts if t["text"] and id(t) not in skip
                         and "page-number" not in (t["id"] or "") and numbered.match(t["text"])
                         and re.search(r"[가-힣A-Za-z]{2,}", numbered.sub("", t["text"]))]
            if not toc_items:  # number and name in separate <text> runs
                rows = sorted((t for t in p.texts if t["text"]), key=lambda t: (round(t["y"]), t["x"]))
                for a, b in zip(rows, rows[1:]):
                    if (re.fullmatch(r"[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[IVX]{1,4}|0?\d", a["text"].strip(" .")) and abs(a["y"] - b["y"]) < 4
                            and re.search(r"[가-힣A-Za-z]{2,}", b["text"])):
                        toc_items.append(f"{a['text']} {b['text']}")
        slots = {}
        for key in rules["ending"]["message_slots"]:
            txt = _group_text(p, (key,), skip=())
            if txt:
                slots[key] = txt
        drawn = p.root.get("data-content-diagram")  # content_diagrams.py variant picked into the deck
        layout = p.layout + " " + (p.role or "") + (f" content-diagram-{drawn.replace('_', '-')}" if drawn else "")
        out.append(StoryPage(p.index, p.path.stem, layout, title, governing,
                             body, toc_items, slots, has_source=p.source is not None))
    return out


def pages_from_outline(path: Path) -> list[StoryPage]:
    out = []
    for p in content_check.load_outline(path):
        body = [t for t in p.texts if t not in (p.title, p.governing)]
        toc_items = []
        if p.is_toc:
            toc_items = [s.strip() for b in body for s in re.split(r"[/·\n]|\s{2,}|→", b) if s.strip()]
        out.append(StoryPage(p.index, p.layout, p.layout, p.title, p.governing, body, toc_items))
    return out


# ---------------------------------------------------------------- text helpers
_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(%|％|%p|배|개|곳|건|명|종|만|억|조|천|tCO2e?q?|톤|t|MW|GW|kWh|MWh|GWh|원|년|월|일|분기|차|단계)?")
_STOP = set("및 등 의 를 을 이 가 은 는 에 에서 으로 로 와 과 도 한 할 수 있 있는 위한 위해 통해 대한 관련 대상 기반 경우 합니다 입니다 있습니다 예정입니다 필요합니다 함 임 됨 것 그 이번 본 각 전 후 내 중 및".split())


def numbers(text: str) -> list[tuple[str, str]]:
    """(normalized value, unit) pairs; bare 1-digit numbers and years-as-labels are kept."""
    out = []
    for m in _NUM.finditer(text or ""):
        val = m.group(1).replace(",", "")
        unit = (m.group(2) or "").replace("％", "%")
        if len(val) == 1 and not unit:
            continue
        out.append((val, unit))
    return out


def tokens(text: str) -> set[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9+\-]{1,}|[가-힣]{2,}", text or "")
    out = set()
    for w in words:
        w = re.sub(r"(으로|에서|에게|까지|부터|이며|하고|하여|해야|합니다|입니다|됩니다|했습니다|이다|으로써|의|을|를|은|는|이|가|와|과|도|로|에)$", "", w)
        if len(w) >= 2 and w not in _STOP:
            out.add(w.lower())
    return out


def overlap(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


# ---------------------------------------------------------------- report
class Report(qaqc.Report):
    pass


def ghost_deck(pages: list[StoryPage]) -> str:
    lines = ["# Ghost deck — 제목 | 거버닝만으로 읽는 스토리라인", "",
             "이 파일은 innergen_story_check.py가 만든다. AI 내용 검토(content-review-v32.md)는 이 파일과 본문 텍스트를 읽고 점수를 매긴다.", ""]
    for p in pages:
        if p.role == "toc":
            items = " / ".join(p.toc_items) or p.body_text[:160]
            lines.append(f"- **P{p.index:02d} [목차]** {items}")
        elif p.role in ("cover", "divider", "ending"):
            lines.append(f"- **P{p.index:02d} [{p.role}]** {p.title or p.body_text[:80]}")
        else:
            gov = p.governing or "(거버닝 없음)"
            lines.append(f"- P{p.index:02d} {p.title} | {gov}")
            for k, v in p.slots.items():
                lines.append(f"  - {k}: {v}")
    return "\n".join(lines) + "\n"


def page_dump(pages: list[StoryPage]) -> list[dict]:
    """Full visible text per page for the reviewer; part of the review hash."""
    return [{"page": p.index, "role": p.role, "layout": p.layout.strip(), "title": p.title,
             "governing": p.governing, "slots": p.slots, "toc_items": p.toc_items, "body": p.body}
            for p in pages]


def _hash(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- checks
def run(pages: list[StoryPage], deck_type: str | None, rules: dict, source_text: str,
        review: dict | None, ghost_sha: str, plan_stage: bool,
        corpus: list[tuple[str, str]] | None = None) -> Report:
    rep = Report()
    backup_rx = re.compile(rules["story"]["backup_label_regex"])
    for p in pages:  # [참고]·[첨부]·[Back-up] pages hold raw evidence, not the argument
        if p.role == "content" and backup_rx.search(p.title):
            p.role = "backup"
    content = [p for p in pages if p.role == "content"]
    if not content:
        rep.add("ERROR", "N00", 0, "본문 장표를 찾지 못했습니다(svg_output·svg_final이 비었거나 계획표에 본문 행이 없음)")
        return rep
    soft = "WARN" if plan_stage else "ERROR"

    # ---- N0: the ghost deck must be readable
    with_gov = [p for p in content if p.governing]
    share = len(with_gov) / len(content)
    if share < rules["story"]["min_governing_share"]:
        rep.add("ERROR", "N01", 0, f"거버닝이 있는 본문 장표가 {share:.0%}입니다 — 거버닝만 읽어 스토리가 이어져야 합니다")
    claims = [p for p in with_gov if re.search(rules["story"]["claim_ending_regex"], p.governing.rstrip(" .)"))
              or re.search(r"\([^)]*(?:완료|예정|중)\)\s*$", p.governing)]
    if with_gov and len(claims) / len(with_gov) < rules["story"]["min_claim_share"]:
        topics = [p.index for p in with_gov if p not in claims]
        rep.add(soft, "N02", 0, f"거버닝 {len(with_gov)}개 중 {len(topics)}개가 판단 문장이 아닌 주제·명사구입니다"
                f"(P{', P'.join('%02d' % i for i in topics[:8])}{'…' if len(topics) > 8 else ''}) — 거버닝만 읽으면 결론이 보여야 합니다")

    # ---- N1: TOC (count, parallel noun phrases, length, chapters carry the story)
    tr = rules["toc"]
    toc = next((p for p in pages if p.role == "toc" and p.toc_items), None)
    if toc:
        items = [re.sub(tr["numbering_regex"], "", i).strip(" .-–") for i in toc.toc_items]
        items = [i for i in items if i]
        lo, hi = tr["chapter_count"]
        if not lo <= len(items) <= hi:
            rep.add("WARN", "N10", toc.index, f"목차 장이 {len(items)}개입니다(권장 {lo}–{hi}개, MECE로 묶기)")
        for it in items:
            n = len(it.replace(" ", ""))
            if n > tr["max_chars"]:
                rep.add("WARN", "N11", toc.index, f"목차 장명이 {n}자입니다(≤{tr['max_chars']}): '{it[:30]}'")
            if re.search(tr["sentence_regex"], it):
                rep.add("WARN", "N11", toc.index, f"목차 장명은 명사구로(문장·질문 금지): '{it[:30]}'")
            if it.lower() in tr["generic_items"]:
                rep.add("WARN", "N12", toc.index, f"목차 장명 '{it}'이 일반 항목명입니다 — 이 덱의 대상·쟁점을 넣으세요")
        # Each chapter should be argued by at least one governing in the deck.
        govs = " ".join(p.governing + " " + p.title for p in content)
        for it in items:
            if tokens(it) and overlap(it, govs) == 0:
                rep.add("WARN", "N13", toc.index, f"목차 장 '{it[:24]}'의 핵심어가 본문 제목·거버닝에 없습니다")
        # Chapter breadcrumbs ("II. 장명 – 절명") must name a TOC chapter; reused pages keep stale tags.
        crumb = re.compile(r"^\s*([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+|[IVX]{1,4})\.\s*([^–\-|/]+)")
        for p in content + [q for q in pages if q.role == "backup"]:
            m = crumb.match(p.title) or next((crumb.match(b) for b in p.body[:3] if crumb.match(b)), None)
            if m and max((overlap(m.group(2), it) for it in items), default=0) < 0.5:
                rep.add("WARN", "N14", p.index, f"장 표시 '{m.group(0).strip()[:30]}'가 목차의 어느 장과도 맞지 않습니다(재사용 장표의 태그 미갱신?)")
    attach = {}
    for p in pages:
        for m in re.finditer(r"(?:첨부|Appendix|부록)\s*(\d+)\s*[.:]", p.title):
            attach.setdefault(m.group(1), []).append(p.index)
    for no, idx in attach.items():
        idx = sorted(set(idx))
        if len(idx) > 1 and max(idx) - min(idx) + 1 > len(idx):  # same number on non-adjacent pages
            rep.add("WARN", "N15", idx[-1], f"첨부 {no} 번호가 떨어진 장(P{', P'.join('%02d' % i for i in idx)})에 중복됩니다")

    # ---- N2: governing quality beyond per-page grammar
    gr = rules["governing"]
    for p in with_gov:
        g = p.governing
        if re.search(gr["description_regex"], g):
            rep.add("WARN", "N20", p.index, f"거버닝이 내용 소개입니다(판단·시사점 없음): '{g[:40]}'")
        filler = [w for w in gr["filler_words"] if w in g]
        if len(filler) >= gr["filler_max"]:
            rep.add("WARN", "N21", p.index, f"거버닝에 상투어 {len(filler)}개({', '.join(filler)}) — 대상·수치·기준으로 바꾸세요")
        if not plan_stage:
            body = p.body_text + " " + " ".join(p.slots.values())
            missing = [v + u for v, u in numbers(g) if v not in body.replace(",", "")]
            if missing:
                where = [m for m in missing if m.rstrip("%배개곳건명종만억조천톤년월일분기차단계").split(".")[0] not in source_text.replace(",", "")]
                level = "WARN"
                msg = f"거버닝 수치 {', '.join(missing)}가 같은 장표 본문에 없습니다 — 근거(표·차트·출처)를 본문에 두세요"
                if source_text and where:
                    msg += f"; 원문(sources)에서도 찾지 못함: {', '.join(where)}"
                rep.add(level, "N22", p.index, msg)
    if not plan_stage:
        for p in content:
            if (len(numbers(p.body_text)) >= rules["body"]["numbers_need_source"]
                    and not re.search(rules["body"]["source_regex"], p.all_text + " " + " ".join(p.slots.values()))
                    and not p.has_source):
                rep.add("WARN", "N24", p.index, "수치가 많은 장표에 출처·단위·기준시점 표기가 없습니다")
    for p in pages:
        if re.search(rules["body"]["credential_regex"], p.all_text):
            rep.add("WARN", "N25", p.index, "계정·비밀번호 요청 문구가 있습니다 — '시스템 접근 권한 협의'로 바꾸세요")
    # ---- numbering and order integrity (reused pages break these first)
    split = {}
    for p in content + [q for q in pages if q.role == "backup"]:
        m = re.search(r"\((\d+)\s*/\s*(\d+)\)", p.title)
        if m:
            key = re.sub(r"\(\d+\s*/\s*\d+\)", "", p.title).strip()
            split.setdefault(key, []).append((p.index, int(m.group(1)), int(m.group(2))))
    for key, rows in split.items():
        ks, ns = [k for _, k, _ in rows], {n for _, _, n in rows}
        if len(ns) > 1 or len(set(ks)) < len(ks) or ks != sorted(ks):
            rep.add("WARN", "N16", rows[0][0], f"분할 표기(k/N)가 맞지 않습니다: '{key[:24]}' {[f'{k}/{n}' for _, k, n in rows]}")
    chap = [(p.index, int(m.group(1))) for p in content
            if (m := re.match(r"^\s*(\d{1,2})\.\s*[가-힣A-Za-z]", p.title))]
    prev = 0
    for idx, no in chap:
        if no > prev + 1:
            rep.add("WARN", "N16", idx, f"장 번호가 {prev}. 다음에 {no}.로 건너뜁니다")
        prev = max(prev, no)
    if ending_idx := [p.index for p in pages if p.role == "ending"]:
        after = [p.index for p in pages if p.index > ending_idx[0] and p.role == "content"]
        if after:
            rep.add("WARN", "N17", after[0], "맺음 장표 뒤에 본문 장표가 있습니다 — 부록은 [참고]·Appendix로 표시하세요")
    for p in content:
        for m in re.finditer(r"(\d{4})년[^.。]{0,40}?\1년\s*대비", p.all_text):
            rep.add(soft, "N26", p.index, f"같은 연도끼리 비교합니다: '{m.group(0)[:40]}'")
        if deck_type in rules["governing"]["final_stage_types"] and re.search(r"\(?예정\)?\s*$|예정입니다\s*$", p.governing) \
                and not re.search(r"향후|다음|차년|후속|제언", p.title + p.governing):
            rep.add("WARN", "N27", p.index, "최종 단계 결과 장표의 거버닝이 '예정'입니다 — 완료형과 완료 일자로")
        if re.search(rules["governing"]["estimate_regex"], p.governing) and numbers(p.governing) \
                and not re.search(rules["governing"]["caveat_regex"], p.all_text):
            rep.add("WARN", "N28", p.index, "추정·전망 수치에 가정·추정치 단서가 없습니다")
    if corpus:
        for p in with_gov:
            for other, gov in corpus:
                if len(p.governing) >= 20 and qaqc._similar(p.governing, gov) >= 0.9:
                    rep.add("WARN", "N29", p.index, f"다른 프로젝트({other})의 거버닝과 같은 문장입니다 — 이 과업의 수치·대상으로 다시 쓰세요")
                    break
    # adjacent governing should progress, not restate
    for a, b in zip(with_gov, with_gov[1:]):
        if overlap(a.governing, b.governing) >= gr["adjacent_overlap_max"] and len(tokens(b.governing)) >= 4:
            rep.add("WARN", "N23", b.index, f"앞 장(P{a.index:02d}) 거버닝과 핵심어가 거의 같습니다 — 다음 논점으로 진행하세요")

    # ---- N3: diagram page carries the relation it draws
    for p in content:
        for spec in rules["diagram"]["relations"].values():
            if any(k in p.layout for k in spec["layouts"]):
                if not re.search(spec["cue_regex"], p.all_text, re.I):
                    rep.add("WARN", "N30", p.index, f"{spec['label']} 도식({p.layout.split()[0]})에 필요한 표지가 본문에 없습니다: {spec['need']}")
                break

    # ---- N4: ending answers the opening with concrete actions
    en = rules["ending"]
    closing = [p for p in content[-en["closing_window"]:]]
    closing_text = " ".join(p.governing + " " + p.body_text + " " + " ".join(p.slots.values()) for p in closing)
    ending_pages = [p for p in pages if p.role == "ending"]
    closing_text += " " + " ".join(p.all_text for p in ending_pages)
    opening = content[:en["opening_window"]]
    opening_text = " ".join(p.title + " " + p.governing for p in opening)
    if overlap(opening_text, closing_text) < en["callback_min_overlap"]:
        rep.add("WARN", "N40", closing[-1].index,
                "마무리가 첫 장의 과제·질문으로 돌아오지 않습니다 — 도입의 핵심어로 결론을 다시 말하세요")
    needs_action = deck_type in en["action_deck_types"] or deck_type is None
    if needs_action:
        # An action names its owner and its date in the same line; a date in one
        # schedule row and an owner in another do not make a next step.
        lines = [t for p in closing + ending_pages for t in [p.title, p.governing, *p.body, *p.slots.values()] if t]
        has_when = any(re.search(en["when_regex"], t) for t in lines)
        has_who = any(re.search(en["who_regex"], t) for t in lines)
        paired = any(re.search(en["when_regex"], t) and re.search(en["who_regex"], t) for t in lines)
        if not paired:
            miss = [n for n, ok in (("기한", has_when), ("주체", has_who)) if not ok] or ["주체와 기한을 한 줄에 둔"]
            rep.add(soft if deck_type in en["action_deck_types"] else "WARN", "N41", closing[-1].index,
                    f"마지막 {en['closing_window']}장의 다음 행동에 {'·'.join(miss)} 표시가 없습니다 — '(주체) 기한까지 행동'으로")
    for p in closing:  # a thank-you ending page is fine; a closing *message* must be concrete
        for ph in en["generic_phrases"]:
            if ph in p.all_text and not re.search(en["when_regex"], p.all_text):
                rep.add("WARN", "N42", p.index, f"맺음 문구 '{ph}'가 구체 행동 없이 쓰였습니다")
                break
    if deck_type not in en["closing_exempt_types"] and not any(re.search(en["closing_title_regex"], p.title + " " + " ".join(p.slots)) for p in closing):
        rep.add("WARN", "N44", closing[-1].index, "마지막 본문 장표들에 결론·시사점·다음 단계 장표가 없습니다(연락처·사례로 끝남)")
    if closing and not (closing[-1].governing or closing[-1].slots):
        rep.add("WARN", "N43", closing[-1].index, "마지막 본문 장표에 결론 메시지(거버닝 또는 결론 박스)가 없습니다")

    # ---- N5: independent AI content review record
    if review is not None:
        check_review(review, ghost_sha, rules, rep, len(pages))
    elif not plan_stage:
        rep.add("WARN", "N50", 0, "AI 내용 검토 기록(analysis/content_review.json)이 없습니다 — content-review-v32.md 절차로 검토자를 따로 실행하세요")
    return rep


def check_review(review: dict, ghost_sha: str, rules: dict, rep: Report, n_pages: int) -> None:
    rv = rules["review"]
    if review.get("ghost_sha256") != ghost_sha:
        rep.add("ERROR", "N51", 0, f"검토 기록이 현재 덱과 다릅니다(ghost {review.get('ghost_sha256')} ≠ {ghost_sha}) — 수정 후 다시 검토하세요")
    if review.get("reviewer") in (None, "", "author"):
        rep.add("ERROR", "N51", 0, "검토자는 작성자와 다른 독립 실행이어야 합니다(reviewer 값)")
    scores = review.get("scores", {})
    for role in rv["roles"]:
        s = scores.get(role)
        if not isinstance(s, dict) or not isinstance(s.get("score"), (int, float)):
            rep.add("ERROR", "N52", 0, f"검토 기록에 '{role}' 점수가 없습니다")
            continue
        if not s.get("evidence"):
            rep.add("ERROR", "N52", 0, f"'{role}' 점수에 근거 장(evidence)이 없습니다")
        if s["score"] < rv["min_score"]:
            rep.add("ERROR", "N53", 0, f"AI 검토 '{role}' {s['score']}점 < {rv['min_score']} — 지적 사항 수정 후 재검토")
        elif s["score"] < rv["target_score"]:
            rep.add("WARN", "N53", 0, f"AI 검토 '{role}' {s['score']}점(목표 {rv['target_score']})")
    for f in review.get("findings", []):
        page = f.get("page", 0) if isinstance(f.get("page"), int) else 0
        if not f.get("fix"):
            rep.add("WARN", "N54", page, f"검토 지적에 수정안이 없습니다: {str(f.get('issue', ''))[:40]}")
        if f.get("severity") == "major" and f.get("status") != "fixed":
            rep.add("ERROR", "N54", page, f"주요 지적 미해결: {str(f.get('issue', ''))[:60]}")
        if page and page > n_pages:
            rep.add("WARN", "N54", page, "검토 지적의 장 번호가 덱 범위를 벗어납니다")


# ---------------------------------------------------------------- io
def load_sources(project: Path, sources: Path | None) -> str:
    root = sources or project / "sources"
    if not root.exists():
        return ""
    parts = []
    for f in sorted(root.rglob("*.md")):
        try:
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(parts)


def load_corpus(project: Path) -> list[tuple[str, str]]:
    """Governing messages of sibling projects (their last story_pages.json)."""
    out = []
    for f in project.resolve().parent.glob("*/analysis/story_pages.json"):
        if f.parents[1] == project.resolve():
            continue
        try:
            rows = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out += [(f.parents[1].name, r["governing"]) for r in rows if r.get("governing")]
    return out


def write_report(project: Path, rep: Report, summary: dict, ghost: str) -> None:
    out = project / "analysis"
    out.mkdir(exist_ok=True)
    (out / "storyline_ghost.md").write_text(ghost, encoding="utf-8")
    md = [f"# INNerGEN 스토리라인·내용 검사 — {project.name}", "",
          f"- 덱 유형: {summary.get('deck_type') or '미지정'} · 단계: {summary['stage']} · 장수 {summary['pages']} (본문 {summary['content_pages']})"
          f" · ghost {summary['ghost_sha256']}",
          f"- ERROR {summary['errors']} · WARN {summary['warnings']} · INFO {summary['infos']}", "",
          "| 수준 | 코드 | 장 | 내용 |", "|---|---|---|---|"]
    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for it in sorted(rep.items, key=lambda i: (order[i["level"]], i["page"], i["code"])):
        md.append(f"| {it['level']} | {it['code']} | {('P%02d' % it['page']) if it['page'] else '덱'} | {it['message']} |")
    md += ["", "코드: N0 고스트 덱 · N1 목차 · N2 거버닝 논리·근거 · N3 도식 관계 · N4 마무리 · N5 AI 내용 검토 기록. "
           "규칙: content-principles-v32.json, 설명: content-principles-v32.md, 검토 절차: content-review-v32.md"]
    (out / "story_check_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / "story_check_report.json").write_text(
        json.dumps({"summary": summary, "items": rep.items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    configure_utf8_stdio()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", type=Path)
    ap.add_argument("--deck-type", default=None)
    ap.add_argument("--outline", type=Path, default=None, help="plan-stage outline (md table or json) instead of svg_output")
    ap.add_argument("--review", type=Path, default=None, help="AI content review record (default: analysis/content_review.json if present)")
    ap.add_argument("--sources", type=Path, default=None, help="source markdown folder (default: <project>/sources)")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    project = args.project
    plan_stage = args.outline is not None
    pages = pages_from_outline(args.outline) if plan_stage else pages_from_project(project, rules)
    deck_type = args.deck_type
    spec = project / "design_spec.md"
    if deck_type is None and spec.exists():
        m = re.search(r"(?:deck_type|innergen_report_type)\*{0,2}\s*\|?\s*[:|]\s*`?\**(\w+)", spec.read_text(encoding="utf-8"))
        deck_type = m.group(1) if m else None
    ghost = ghost_deck(pages)
    dump = json.dumps(page_dump(pages), ensure_ascii=False, indent=1)
    ghost_sha = _hash(ghost, dump)
    (project / "analysis").mkdir(exist_ok=True)
    (project / "analysis/story_pages.json").write_text(dump + "\n", encoding="utf-8")
    review = None
    review_path = args.review or (project / "analysis/content_review.json")
    if not plan_stage and review_path.exists():
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            review = {}
            print(f"[innergen_story_check] review JSON unreadable: {exc}")
    rep = run(pages, deck_type, rules, load_sources(project, args.sources), review, ghost_sha, plan_stage,
              load_corpus(project))
    summary = {"project": str(project), "deck_type": deck_type, "stage": "outline" if plan_stage else "deck",
               "pages": len(pages), "content_pages": sum(1 for p in pages if p.role == "content"),
               "ghost_sha256": ghost_sha, "errors": rep.count("ERROR"), "warnings": rep.count("WARN"),
               "infos": rep.count("INFO")}
    write_report(project, rep, summary, ghost)
    for it in rep.items:
        if it["level"] != "INFO":
            print(f"[{it['level']}] {it['code']} P{it['page']:02d} {it['message']}")
    print(f"[innergen_story_check] {summary['stage']} · {deck_type or '-'} · {summary['pages']} pages · ghost {ghost_sha} · "
          f"ERROR {summary['errors']} · WARN {summary['warnings']} · report: {project / 'analysis/story_check_report.md'}")
    if summary["errors"] or (args.strict and summary["warnings"]):
        print("[innergen_story_check] FAIL")
        return 1
    print("[innergen_story_check] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
