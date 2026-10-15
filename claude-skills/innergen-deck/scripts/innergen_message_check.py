#!/usr/bin/env python3
"""
INNerGEN message gate - governing message type per page and body composition
preset per deck (v30).

The page plan names, for each page, the governing message type the writer chose
(14 types: 정의·개념, 현황·사실, 비교·차이, 원인·동인, 분석·판단, 요구사항·기준,
사례 교훈, 권고·실행, 전망·기대효과, 진행 상태, 요청·결정, 수행 약속, 장 도입,
결론·종합) and the body style (줄글형, 도식형, 그래프형, 표형, 수치형, 사례형).
The deck picks a body preset (narrative / visual / data / table / balanced),
by default from its business type. This gate checks each governing sentence
against the elements its type needs and the deck's style mix against the preset.
Rules: references/governing-body-v30.json, explained in governing-body-v30.md.

    M00  no governing types chosen; checked against each layout's default type  INFO
    M01  governing type missing or unknown on a content page               WARN
    M02  governing lacks an element its type needs                          WARN
    M03  type needs a number / date / deadline and has none                 WARN (INFO if only recommended)
    M04  no explicit subject at the start (types that need one)             WARN
    M05  type does not suit the layout or the deck type                     INFO
    M06  deck lacks a type its deck type needs; one type dominates          WARN / INFO
    D00  body preset unknown                                                 WARN
    D01  chosen body style differs from the layout's style                   WARN
    D02  deck style mix outside the preset's range                           WARN (over) / INFO (under)
    D03  prose page too long (lines, bullets per block)                      WARN
    D04  same body style on more pages in a row than allowed                 INFO

Usage:
    python3 scripts/innergen_message_check.py --outline plan.md --deck-type final --business-type reduction
    python3 scripts/innergen_message_check.py --outline plan.md --body-preset data
    python3 scripts/innergen_message_check.py --list        # types, styles, presets
    (finished decks: innergen_qaqc.py runs this gate and reads <project>/outline.md)

Outline columns (Markdown table, header row required for the new columns):
    | 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 | 거버닝 유형 | 본문 구성 |
A type cell takes the id (judgment), number (5) or Korean label (분석·판단, 판단);
a style cell takes 도식형 / 도식 / diagram and so on. JSON outlines use the keys
governing_type and body_style.

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

REPO = _SCRIPTS_DIR.parents[min(3, len(_SCRIPTS_DIR.parents) - 1)]
SPEC_PATH = REPO / "docs/styles/innergen/governing-body-v30.json"
# Standalone skill bundles ship the spec beside the skill.
if not SPEC_PATH.is_file():
    SPEC_PATH = _SCRIPTS_DIR.parent / "references/governing-body-v30.json"

FRAME_TOKENS = ("cover", "toc", "section-divider", "ending")
TYPE_HEADERS = ("거버닝 유형", "거버닝유형", "유형", "governing_type", "type")
STYLE_HEADERS = ("본문 구성", "본문구성", "구성", "body_style", "style")
HEADER_FIRST = ("쪽", "page", "#", "p", "no")


def load_spec(path: Path | None = None) -> dict | None:
    p = path or SPEC_PATH
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def _key(s: str) -> str:
    return re.sub(r"[\s·・,/()\-_]", "", (s or "").strip().strip("`").lower())


def resolve_type(spec: dict, value: str | None) -> str | None:
    """'judgment' / '5' / 'M5' / '분석·판단' / '판단' -> 'judgment'; '' -> None; unknown -> '?<value>'."""
    v = (value or "").strip().strip("`")
    if not v or v in ("-", "–"):
        return None
    k = _key(v)
    for tid, t in spec["governing_types"].items():
        names = [tid, t["label"], str(t["no"]), f"m{t['no']}", f"gt{t['no']}"] + t.get("aliases", [])
        if k in {_key(n) for n in names}:
            return tid
    return "?" + v


def resolve_style(spec: dict, value: str | None) -> str | None:
    v = (value or "").strip().strip("`")
    if not v or v in ("-", "–"):
        return None
    k = _key(v)
    for sid, s in spec["body_styles"].items():
        if k in {_key(n) for n in [sid, s["label"], str(s["no"])] + s.get("aliases", [])}:
            return sid
    return "?" + v


def layout_key(layout: str) -> str:
    """'s24-project-overview' -> 's24'; 'content-kpi' stays; frame pages -> their token."""
    m = re.match(r"^(s\d{2})\b", layout or "")
    if m:
        return m.group(1)
    for tok in ("content-final", "content-table", "content-kpi", "content-process", "content-split",
                "content-dual", "content", "section-divider", "toc-pages", "toc", "cover", "ending"):
        if (layout or "").startswith(tok):
            return tok
    return layout or ""


class MsgPage:
    """One page as this gate needs it, planned (outline) or drawn (SVG)."""

    def __init__(self, index: int, layout: str, title: str = "", governing: str = "",
                 gtype: str | None = None, style: str | None = None, body_lines: list[str] | None = None,
                 shapes: int | None = None):
        self.index, self.layout = index, (layout or "").lower()
        self.title, self.governing = title or "", governing or ""
        self.gtype, self.style = gtype, style
        self.body_lines = body_lines  # None at outline stage
        self.shapes = shapes

    @property
    def is_frame(self) -> bool:
        return any(tok in self.layout for tok in FRAME_TOKENS)


# ---------------------------------------------------------------- outline
def _split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load_outline(path: Path, spec: dict) -> list[MsgPage]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        rows = data.get("pages", data) if isinstance(data, dict) else data
        out = []
        for i, r in enumerate(rows, 1):
            n = int(r.get("page", i))
            out.append(MsgPage(n, _outline_layout(n, str(r.get("layout", ""))), r.get("title", ""),
                               r.get("governing", ""), resolve_type(spec, r.get("governing_type")),
                               resolve_style(spec, r.get("body_style"))))
        return out
    cols: dict[str, int] = {}
    out = []
    for line in raw.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = _split_row(s)
        first = _key(cells[0]) if cells else ""
        if first in HEADER_FIRST and len(cells) >= 4:
            names = [_key(c) for c in cells]
            cols = {}
            for i, nm in enumerate(names):
                if nm in {_key(h) for h in TYPE_HEADERS}:
                    cols["type"] = i
                elif nm in {_key(h) for h in STYLE_HEADERS}:
                    cols["style"] = i
            continue
        if not cells or not re.fullmatch(r"P?\d{1,3}", cells[0].strip("`")):
            continue
        n = int(cells[0].strip("`").lstrip("P"))
        cells += [""] * (max(4, *(v + 1 for v in cols.values())) - len(cells)) if cols else [""] * (4 - len(cells))
        out.append(MsgPage(n, _outline_layout(n, cells[1]), cells[2].strip("`"), cells[3].strip("`"),
                           resolve_type(spec, cells[cols["type"]]) if "type" in cols else None,
                           resolve_style(spec, cells[cols["style"]]) if "style" in cols else None))
    return out


def outline_choices(path: Path, spec: dict) -> dict[int, tuple[str | None, str | None]]:
    """Page number -> (governing type, body style) chosen in the plan."""
    if not path.is_file():
        return {}
    return {p.index: (p.gtype, p.style) for p in load_outline(path, spec)}


def _outline_layout(n: int, cell: str) -> str:
    cell = cell.strip().strip("`").removesuffix(".svg")
    cell = re.sub(r"^\d+_(?=(?:0\d[a-z]?|s\d{2})_)", "", cell)
    m = re.match(r"^((?:0\d[a-z]?|s\d{2})_[a-z0-9_]+?)(?:__.*)?$", cell)
    if m:
        return re.sub(r"^(?:0\d[a-z]?)_", "", m.group(1)).replace("_", "-")
    return cell.lower().replace("_", "-")


# ---------------------------------------------------------------- SVG pages
_SHAPES = ("rect", "path", "circle", "ellipse", "polygon", "polyline", "line")


def pages_from_svg(pages, fam: dict, choices: dict[int, tuple] | None = None) -> list[MsgPage]:
    """Adapt innergen_qaqc.Page objects; body = text and shapes between the
    governing line and the source line."""
    choices = choices or {}
    top = fam["governing"]["baseline"] + 6
    bottom = fam["source"]["baseline"] - fam["source"].get("size", 11)
    out = []
    for p in pages:
        skip = {id(x) for x in (p.title, p.governing, p.source, p.footer_label, p.page_number) if x is not None}
        lines = []
        for t in p.texts:
            if id(t) in skip or not t["text"] or not (top < t["y"] < bottom):
                continue
            lines.extend(t["lines"])
        shapes = 0
        for el in p.root.iter():
            tag = el.tag.rsplit("}", 1)[-1]
            if tag not in _SHAPES:
                continue
            try:
                y = float(el.get("y") or el.get("cy") or el.get("y1") or "nan")
            except ValueError:
                y = float("nan")
            if tag in ("path", "polygon", "polyline") or (top < y < bottom):
                shapes += 1
        gtype, style = choices.get(p.index, (None, None))
        out.append(MsgPage(p.index, p.layout + (" " + p.role if p.role else ""),
                           p.title["text"] if p.title else "", p.governing["text"] if p.governing else "",
                           gtype, style, body_lines=lines, shapes=shapes))
    return out


# ---------------------------------------------------------------- checks
def _rx(p: str) -> re.Pattern:
    return re.compile(p, re.IGNORECASE)


def layout_style(spec: dict, page: MsgPage) -> str | None:
    key = layout_key(page.layout)
    st = spec["layout_styles"].get(key)
    if st:
        return st
    if key in ("content", "content-split", "content-dual"):
        if page.shapes is None:
            return None
        return "diagram" if page.shapes >= spec.get("diagram_shape_threshold", 8) else "prose"
    return None


def pick_preset(spec: dict, deck_type: str | None, business_type: str | None, preset: str | None) -> tuple[str, str]:
    """(preset id, why). Order: explicit body_preset > deck type > business type > balanced."""
    if preset:
        return preset, "지정"
    if deck_type and deck_type in spec["deck_presets"]:
        return spec["deck_presets"][deck_type], f"덱 유형 {deck_type} 기본"
    if business_type and business_type in spec["business_presets"]:
        return spec["business_presets"][business_type]["preset"], f"사업 성격 {business_type} 기본"
    return "balanced", "기본값"


def check(pages: list[MsgPage], deck_type: str | None, business_type: str | None, spec: dict, add,
          body_preset: str | None = None, number_rx: str = r"[0-9０-９]|％|%", outline: bool = False) -> dict:
    """Run M/D checks; `add(level, code, page, message)` records each finding."""
    types = spec["governing_types"]
    content = [p for p in pages if not p.is_frame]
    chosen_any = any(p.gtype for p in pages)
    inferred = 0
    used: list[tuple[int, str]] = []

    # ---- M: governing message type per page
    for p in content:
        lk = layout_key(p.layout)
        suits = spec["layout_types"].get(lk, [])
        t = p.gtype
        soft = False
        if t is None:
            if chosen_any:
                add("WARN", "M01", p.index, "거버닝 유형이 비어 있습니다 — 14개 유형 중 하나를 고르세요 (--list)")
            if not suits:
                continue
            t, soft = suits[0], True
            inferred += 1
        elif t.startswith("?"):
            add("WARN", "M01", p.index, f"알 수 없는 거버닝 유형 '{t[1:]}' (선택지: {', '.join(v['label'] for v in types.values())})")
            continue
        used.append((p.index, t))
        spec_t = types[t]
        g = p.governing.strip()
        lvl = "INFO" if soft else "WARN"
        tag = f"[{spec_t['label']}{' 추정' if soft else ''}]"
        if not g:
            continue  # G01 (qaqc) or the plan reports a missing governing message
        end_rx = spec.get("sentence_end_pattern")
        if end_rx and not _rx(end_rx).search(g):
            add(lvl, "M02", p.index, f"{tag} 명사구로 끝납니다 — 판단이 담긴 문장으로 (예: {spec_t['example']})")
        for c in spec_t["checks"]:
            if not _rx(c["pattern"]).search(g):
                add("INFO" if soft else c.get("level", "WARN"), "M02", p.index,
                    f"{tag} {c['label']}이(가) 없습니다 — 틀: {spec_t['frame']}")
        need = spec_t.get("number", "none")
        if need != "none":
            nrx = spec_t.get("number_pattern", number_rx)
            if not _rx(nrx).search(g):
                what = spec_t.get("number_label", "핵심 수치")
                level = "WARN" if need == "required" and not soft else "INFO"
                add(level, "M03", p.index, f"{tag} {what}가 없습니다 — 예: {spec_t['example']}")
        if spec_t.get("subject") and not _rx(spec.get("subject_pattern", r"^.{0,24}?(은|는|이|가)\s")).search(g):
            add(lvl, "M04", p.index, f"{tag} 첫 구절에 주어(○○은/는/이/가)가 없습니다 (v11 §2)")
        if suits and t not in suits and not soft:
            names = ", ".join(types[s]["label"] for s in suits)
            add("INFO", "M05", p.index, f"{tag} {lk} 레이아웃에는 보통 {names} 유형을 씁니다")
    rules = spec["deck_type_rules"].get(deck_type or "", {})
    if rules:
        have = {t for _, t in used}
        for group in rules.get("need_any", []):
            if not have & set(group):
                labels = " 또는 ".join(types[g]["label"] for g in group)
                add("WARN" if chosen_any else "INFO", "M06", 0, f"{deck_type} 덱에 '{labels}' 거버닝이 한 장도 없습니다")
        for idx, t in used:
            if t in rules.get("avoid", []):
                add("INFO", "M05", idx, f"{deck_type} 덱에 어울리지 않는 유형입니다: {types[t]['label']}")
    mix = spec["mix"]
    if len(used) >= mix["min_content_pages"]:
        top, c = Counter(t for _, t in used).most_common(1)[0]
        if c / len(used) > mix["max_share_single_type"]:
            add("INFO", "M06", 0, f"본문 거버닝의 {c/len(used):.0%}가 한 유형({types[top]['label']})입니다 — 수평 논리 점검")
    if content and not chosen_any:
        add("INFO", "M00", 0, f"거버닝 유형을 고르지 않아 레이아웃 기본 유형으로 추정해 검사했습니다({inferred}장). 개요표에 '거버닝 유형' 열을 쓰면 WARN으로 검사합니다")

    # ---- D: body composition
    pid, why = pick_preset(spec, deck_type, business_type, body_preset)
    preset = spec["presets"].get(pid)
    if preset is None:
        add("WARN", "D00", 0, f"본문 구성 프리셋 '{pid}'을 알 수 없습니다 (선택지: {', '.join(spec['presets'])})")
    styles: list[tuple[int, str]] = []
    compat = spec.get("compatible_styles", {})
    for p in content:
        ls = layout_style(spec, p)
        st = p.style
        if st and st.startswith("?"):
            add("WARN", "D01", p.index, f"알 수 없는 본문 구성 '{st[1:]}' (선택지: {', '.join(v['label'] for v in spec['body_styles'].values())})")
            st = None
        if st and ls and st != ls and st not in compat.get(ls, []):
            add("WARN", "D01", p.index, f"본문 구성을 {spec['body_styles'][st]['label']}으로 골랐는데 레이아웃 {layout_key(p.layout)}은 {spec['body_styles'][ls]['label']}입니다 — 레이아웃을 바꾸거나 구성을 고치세요")
        final = st or ls
        if final:
            styles.append((p.index, final))
        if final == "prose" and p.body_lines is not None:
            lim = spec["prose_limits"]
            if len(p.body_lines) > lim["max_body_lines"]:
                add("WARN", "D03", p.index, f"줄글 본문이 {len(p.body_lines)}줄입니다(상한 {lim['max_body_lines']}) — 표·도식으로 나누세요")
            run = 0
            for ln in p.body_lines:
                run = run + 1 if re.match(r"^\s*([-•·▪■□○●◦]|\d+[.)])\s*", ln) else 0
                if run == lim["max_bullets_per_block"] + 1:
                    add("WARN", "D03", p.index, f"불릿이 한 묶음에 {lim['max_bullets_per_block']}개를 넘습니다")
    if preset and len(styles) >= 4:
        n = len(styles)
        cnt = Counter(s for _, s in styles)
        for sid, (lo, hi) in preset["mix"].items():
            share = cnt.get(sid, 0) / n
            label = spec["body_styles"][sid]["label"]
            if share > hi + 1e-9:
                add("WARN", "D02", 0, f"{label}이 {share:.0%}로 프리셋 '{preset['label']}' 상한 {hi:.0%}를 넘습니다")
            elif share < lo - 1e-9:
                add("INFO", "D02", 0, f"{label}이 {share:.0%}로 프리셋 '{preset['label']}' 하한 {lo:.0%}에 못 미칩니다")
        if len(cnt) < preset.get("min_styles", 0):
            add("WARN", "D02", 0, f"본문 구성이 {len(cnt)}종뿐입니다(균형형은 {preset['min_styles']}종 이상)")
    run, prev = 0, None
    for idx, s in styles:
        run = run + 1 if s == prev else 1
        prev = s
        if run == spec.get("max_consecutive_style", 3) + 1:
            add("INFO", "D04", idx, f"{spec['body_styles'][s]['label']}이 {run}장 연속입니다 — 리듬 점검")
    prefer = spec["business_presets"].get(business_type or "", {}).get("prefer", {})
    return {"preset": pid, "preset_reason": why, "types_chosen": chosen_any,
            "type_counts": dict(Counter(t for _, t in used)), "style_counts": dict(Counter(s for _, s in styles)),
            "prefer": prefer}


# ---------------------------------------------------------------- CLI
def print_list(spec: dict) -> None:
    print("거버닝 유형 (--outline '거버닝 유형' 열에 번호·id·이름):")
    for tid, t in spec["governing_types"].items():
        need = {"required": "수치 필수", "recommended": "수치 권장", "none": ""}[t.get("number", "none")]
        print(f"  {t['no']:>2} {tid:15s} {t['label']:8s} {need:6s} 틀: {t['frame']}")
        print(f"     예: {t['example']}")
    print("본문 구성 ('본문 구성' 열):")
    for sid, s in spec["body_styles"].items():
        print(f"  {s['no']} {sid:8s} {s['label']:5s} {s['use']}")
    print("프리셋 (--body-preset 또는 design_spec.md body_preset):")
    for pid, p in spec["presets"].items():
        mix = ", ".join(f"{spec['body_styles'][k]['label']} {lo:.0%}–{hi:.0%}" for k, (lo, hi) in p["mix"].items() if hi > 0)
        print(f"  {pid:9s} {p['label']} · {p['who']} · {mix}")
    print("사업 성격 → 기본 프리셋:")
    for bid, b in spec["business_presets"].items():
        pref = " / ".join(f"{spec['body_styles'][k]['label']} {'·'.join(v)}" for k, v in b["prefer"].items())
        print(f"  {bid:18s} {b['preset']:9s} 우선 구조: {pref}")


def main(argv=None) -> int:
    try:
        from console_encoding import configure_utf8_stdio
        configure_utf8_stdio()
    except ImportError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outline", type=Path, help="page plan (.md table or .json)")
    ap.add_argument("--deck-type", default=None)
    ap.add_argument("--business-type", default=None)
    ap.add_argument("--body-preset", default=None, help="narrative|visual|data|table|balanced")
    ap.add_argument("--list", action="store_true", help="print governing types, body styles and presets")
    ap.add_argument("--strict", action="store_true", help="fail on WARN too")
    args = ap.parse_args(argv)
    spec = load_spec()
    if spec is None:
        print(f"[message_check] spec not found: {SPEC_PATH}")
        return 2
    if args.list:
        print_list(spec)
        return 0
    if not args.outline:
        ap.error("--outline is required (finished decks are checked by innergen_qaqc.py)")
    pages = load_outline(args.outline, spec)
    if not pages:
        print("[message_check] no page rows found (rows must start with a page number)")
        return 2
    found: list[tuple] = []
    res = check(pages, args.deck_type, args.business_type, spec, lambda *a: found.append(a),
                body_preset=args.body_preset, outline=True)
    for lvl, code, page, msg in sorted(found, key=lambda x: ({"ERROR": 0, "WARN": 1, "INFO": 2}[x[0]], x[2])):
        print(f"[{lvl}] {code} {'P%02d' % page if page else '덱'} {msg}")
    errs = sum(1 for f in found if f[0] == "ERROR")
    warns = sum(1 for f in found if f[0] == "WARN")
    pref = res["prefer"]
    print(f"[message_check] 프리셋 {res['preset']} ({res['preset_reason']}) · 유형 {res['type_counts']} · 구성 {res['style_counts']}")
    if pref:
        print("[message_check] 이 사업 성격에서 우선 쓸 구조: " + " / ".join(f"{spec['body_styles'][k]['label']} {'·'.join(v)}" for k, v in pref.items()))
    print(f"[message_check] ERROR {errs} · WARN {warns} · " + ("FAIL" if errs or (args.strict and warns) else "PASS"))
    return 1 if errs or (args.strict and warns) else 0


if __name__ == "__main__":
    raise SystemExit(main())
