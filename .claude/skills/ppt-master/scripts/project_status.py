#!/usr/bin/env python3
"""
PPT Master - Project Status Board

Scans every deck project under projects/ and reports how far each one has
progressed (source -> plan -> confirm -> author -> QA -> export), whether the
latest PPTX is older than the working SVGs, and which decks have stalled.
Writes a JSON snapshot for agents and a self-contained HTML board for people.
The CODEX hub (B:/CODEX/_HUB/hub.py) imports collect() for its Slide Master tab.

Usage:
    python3 scripts/project_status.py [projects_dir] [--json OUT] [--html OUT] [--print]

Examples:
    python3 scripts/project_status.py
    python3 scripts/project_status.py projects --print
    python3 scripts/project_status.py projects --html projects/_dashboard/작성현황.html

Dependencies:
    None (only uses standard library)
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
DEFAULT_PROJECTS = REPO_ROOT / "projects"
DEFAULT_OUT_DIR = DEFAULT_PROJECTS / "_dashboard"

ACTIVE_DAYS = 3          # 내보내기 전이라도 이 기간 안에 손댔으면 '작성 중'
EXPORT_SLACK = 120       # 내보내기 직후 정리(노트·로그) 정도는 재내보내기로 보지 않는다(초)
STAGES = ["자료", "기획", "확인", "작성", "검사", "내보내기"]
STATUS_LABEL = {
    "active": "작성 중",
    "waiting": "확인 대기",
    "reexport": "다시 내보내기 필요",
    "done": "완료",
    "stalled": "멈춤",
}
STATUS_ORDER = ["active", "waiting", "reexport", "stalled", "done"]
FAMILY_LABEL = {
    "innergen_basic": "이너젠 오리지널",
    "innergen_business": "이너젠 뉴비즈",
    "innergen_lecture": "이너젠 교육",
    "innercarry": "이너캐리",
}
MARKERS = ("svg_output", "exports", "spec_lock.md", "design_spec.md", "build", "project_meta.json")
DATE_RE = re.compile(r"(20\d{2})(\d{2})(\d{2})")


# 같은 프로세스(현황판 서버)가 30초마다 다시 부를 때 바뀌지 않은 파일은 다시 열지 않는다.
# Windows의 os.scandir는 항목의 수정 시각·크기를 함께 주므로 목록만으로 바뀜을 안다.
_READ_CACHE: dict = {}


def _entries(d: str) -> dict:
    try:
        return {e.name: e for e in os.scandir(d)}
    except OSError:
        return {}


def _mt(e) -> float:
    try:
        return e.stat().st_mtime
    except (OSError, AttributeError):
        return 0.0


def _files(d: str, exts: tuple = (), depth: int = 1) -> list:
    """(name, path, mtime, size) for files under d, up to depth levels."""
    out = []
    for e in _entries(d).values():
        try:
            if e.is_file():
                if not exts or e.name.lower().endswith(exts):
                    st = e.stat()
                    out.append((e.name, e.path, st.st_mtime, st.st_size))
            elif e.is_dir() and depth > 1:
                out.extend(_files(e.path, exts, depth - 1))
        except OSError:
            continue
    return out


def _read(e, limit: int = 0) -> str:
    """Text of a DirEntry, cached by (path, mtime, size)."""
    if e is None:
        return ""
    try:
        st = e.stat()
    except OSError:
        return ""
    key = (st.st_mtime, st.st_size, limit)
    hit = _READ_CACHE.get(e.path)
    if hit and hit[0] == key:
        return hit[1]
    try:
        with open(e.path, encoding="utf-8", errors="replace") as fh:
            text = fh.read(limit) if limit else fh.read()
    except OSError:
        text = ""
    _READ_CACHE[e.path] = (key, text)
    return text


def _json(e) -> dict:
    try:
        v = json.loads(_read(e) or "{}")
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


def _iso_ts(s) -> float:
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _first_heading(text: str) -> str:
    for line in text.splitlines()[:8]:
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _lock_field(text: str, key: str) -> str:
    m = re.search(rf"^- {re.escape(key)}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def _family(prof: dict, lock_text: str, confirm: dict) -> tuple:
    fam, mode = prof.get("family", ""), prof.get("delivery_mode", "")
    if not fam:
        name = ((confirm.get("color") or {}).get("name") or "")
        if name.startswith("v17-"):
            fam = name[4:]
    if not fam:
        behavior = _lock_field(lock_text, "visual_style_behavior")
        if "이너캐리" in behavior or "INNerCarry" in behavior:
            fam = "innercarry"
        elif "뉴비즈" in behavior or "이너젠 비즈" in behavior:
            fam = "innergen_business"
        elif "이너젠" in behavior and ("강의" in behavior or "교육" in behavior):
            fam = "innergen_lecture"
        elif "이너젠" in behavior or "INNerGEN" in behavior:
            fam = "innergen_basic"
    return fam, mode


def _title(spec_text: str, name: str, meta: dict, pptx: list) -> str:
    t = _first_heading(spec_text)
    if t:
        return t
    for fname, *_ in pptx:
        stem = Path(fname).stem
        if re.search(r"[가-힣]", stem):
            return re.sub(r"_+", " ", stem)
    return meta.get("title") or name


def project_status(proj: Path, now: float) -> dict | None:
    pd = str(proj)
    top = _entries(pd)
    if not top.keys() & set(MARKERS):
        return None

    def sub(n: str) -> str:
        return os.path.join(pd, n)

    def has(n: str) -> bool:
        return n in top

    cui = _entries(sub("confirm_ui")) if has("confirm_ui") else {}
    meta = _json(top.get("project_meta.json"))
    confirm = _json(cui.get("result.json"))
    session = _json(cui.get("session.json"))
    lock_text = _read(top.get("spec_lock.md"))
    spec_text = _read(top.get("design_spec.md"), 600)

    svgs = _files(sub("svg_output"), (".svg",)) if has("svg_output") else []
    finals = _files(sub("svg_final"), (".svg",)) if has("svg_final") else []
    notes = _files(sub("notes"), (".md", ".txt")) if has("notes") else []
    build = _files(sub("build"), depth=2) if has("build") else []
    sources = (_files(sub("sources"), depth=2) if has("sources") else []) + \
              (_files(sub("analysis")) if has("analysis") else [])
    exports = _files(sub("exports")) if has("exports") else []
    pptx = sorted((f for f in exports if f[0].lower().endswith(".pptx")), key=lambda x: -x[2])
    pdfs = [f for f in exports if f[0].lower().endswith(".pdf")]

    plan_names = [n for n in ("design_spec.md", "spec_lock.md", "outline.md", "contents_plan.json",
                              "content_plan_v19.json") if n in top]
    plan_mtime = max((_mt(top[n]) for n in plan_names), default=0.0)
    svg_mtime = max((f[2] for f in svgs + finals), default=0.0)
    work_mtime = max([svg_mtime, plan_mtime] + [f[2] for f in notes + build])
    export_mtime = pptx[0][2] if pptx else 0.0
    last = max(work_mtime, export_mtime, max((f[2] for f in sources), default=0.0),
               max((_mt(e) for e in top.values()), default=0.0))

    qc = _json(top.get(".qc_pass.json"))
    qc_ts = _iso_ts(qc.get("passed_at", "")) if qc else 0.0
    qc_fresh = bool(qc_ts) and qc_ts + 5 >= max((f[2] for f in svgs), default=0.0)
    spec_pass = _json(top.get(".spec_pass.json"))
    # spec_lock.md는 기획 확인이 끝난 뒤에 쓰이므로 확인 완료로 본다
    confirmed = session.get("status") == "done" or bool(confirm) or bool(spec_pass) or has("spec_lock.md")
    route = "svg" if svgs or finals else ("direct" if build or pptx else "svg")

    stages = {
        "자료": bool(sources) or has("images"),
        "기획": bool(plan_names),
        "확인": confirmed,
        "작성": bool(svgs or finals or build),
        "검사": qc_fresh if route == "svg" else bool(pptx),
        "내보내기": bool(pptx),
    }
    if pptx:
        status = "reexport" if work_mtime > export_mtime + EXPORT_SLACK else "done"
    elif now - last <= ACTIVE_DAYS * 86400:
        waiting = str(session.get("status", "")).startswith("waiting") and not svgs
        status = "waiting" if waiting else "active"
    else:
        status = "stalled"
    if status == "done":
        nxt = ""
    elif status == "reexport":
        nxt = "내보내기"
    else:
        nxt = next((s for s in STAGES if not stages[s]), "")

    fam, mode = _family(_json(top.get("design_profile_v17.json")), lock_text, confirm)
    created = meta.get("created", "")
    if not created:
        m = DATE_RE.search(proj.name)
        created = "".join(m.groups()) if m else ""
    planned = str(confirm.get("page_count") or spec_pass.get("pages") or "")
    return {
        "id": proj.name,
        "path": pd,
        "title": _title(spec_text, proj.name, meta, pptx),
        "created": created,
        "canvas": meta.get("canvas_format") or _lock_field(lock_text, "format"),
        "family": fam,
        "family_label": FAMILY_LABEL.get(fam, fam or "기타"),
        "delivery_mode": mode,
        "route": route,
        "pages": len(finals) or len(svgs),
        "pages_planned": int(planned) if planned.isdigit() else None,
        "notes": len(notes),
        "stages": stages,
        "next": nxt,
        "status": status,
        "status_label": STATUS_LABEL[status],
        "qc_passed_at": qc_ts or None,
        "last": last,
        "work_mtime": work_mtime or None,
        "exports": [{"name": n, "path": p, "mtime": m, "size": z} for n, p, m, z in pptx[:6]],
        "export_count": len(pptx),
        "pdf_count": len(pdfs),
    }


def collect(projects_dir: Path | str = DEFAULT_PROJECTS) -> dict:
    root = Path(projects_dir)
    now = time.time()
    t0 = time.time()
    items = []
    for e in sorted(os.scandir(root), key=lambda x: x.name) if root.is_dir() else []:
        if not e.is_dir() or e.name.startswith(("_", ".")):
            continue
        try:
            st = project_status(Path(e.path), now)
        except OSError:
            continue
        if st:
            items.append(st)
    items.sort(key=lambda x: -x["last"])
    week = now - 7 * 86400
    counts = {k: sum(1 for i in items if i["status"] == k) for k in STATUS_ORDER}
    fams = {}
    for i in items:
        fams[i["family_label"]] = fams.get(i["family_label"], 0) + 1
    summary = {
        "total": len(items),
        "counts": counts,
        "exported_week": sum(1 for i in items if i["exports"] and i["exports"][0]["mtime"] >= week),
        "touched_week": sum(1 for i in items if i["last"] >= week),
        "pages_week": sum(i["pages"] for i in items if i["exports"] and i["exports"][0]["mtime"] >= week),
        "families": dict(sorted(fams.items(), key=lambda kv: -kv[1])),
    }
    return {"generated": now, "root": str(root), "summary": summary, "projects": items,
            "status_label": STATUS_LABEL, "stages": STAGES, "seconds": round(time.time() - t0, 2)}


# ───────────── 단독 HTML 현황판 (서버 없이 열리는 한 파일) ─────────────

HTML_TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slide Master 작성현황</title>
<style>
  :root { --bg:#F5F7FB; --card:#fff; --line:#E3E7EF; --ink:#1B2333; --muted:#6B7385; --navy:#1F3A68; --blue:#2F6FE4;
          --active:#2F9E5B; --waiting:#E08A1E; --reexport:#C4602B; --stalled:#9AA3B5; --done:#5B6B8A; }
  * { box-sizing:border-box; } body { margin:0; font-family:Pretendard,"IBM Plex Sans KR","Malgun Gothic",sans-serif; background:var(--bg); color:var(--ink); font-size:14px; }
  header { display:flex; align-items:baseline; gap:12px; padding:18px 24px 6px; } h1 { margin:0; font-size:20px; color:var(--navy); }
  header small { color:var(--muted); } main { padding:8px 24px 40px; max-width:1400px; }
  .kpis { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; margin:10px 0 14px; }
  .kpi { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px; cursor:pointer; }
  .kpi.on { outline:2px solid var(--blue); } .kpi .n { font-size:24px; font-weight:700; } .kpi .l { color:var(--muted); font-size:12px; margin-top:2px; }
  .bar { display:flex; gap:8px; align-items:center; margin-bottom:10px; flex-wrap:wrap; }
  input[type=search] { flex:1; min-width:220px; padding:8px 10px; border:1px solid var(--line); border-radius:8px; font:inherit; }
  select { padding:7px; border:1px solid var(--line); border-radius:8px; font:inherit; background:#fff; }
  table { width:100%; border-collapse:collapse; background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden; }
  th, td { padding:9px 10px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; } th { background:#F0F3F9; font-size:12px; color:var(--muted); font-weight:600; }
  .t { font-weight:600; } .sub { color:var(--muted); font-size:12px; margin-top:2px; word-break:break-all; }
  .stb { display:inline-block; padding:2px 8px; border-radius:10px; color:#fff; font-size:12px; white-space:nowrap; }
  .chip { display:inline-block; padding:1px 7px; border-radius:9px; background:#EEF2FA; color:var(--navy); font-size:12px; margin-right:4px; white-space:nowrap; }
  .stg { display:flex; gap:3px; } .stg i { width:22px; height:8px; border-radius:3px; background:#E3E7EF; display:block; } .stg i.ok { background:var(--blue); }
  .stg i.nx { background:#fff; border:1.5px dashed var(--blue); } a { color:var(--blue); text-decoration:none; } a:hover { text-decoration:underline; }
  button.cp { border:1px solid var(--line); background:#fff; border-radius:6px; padding:2px 7px; font:inherit; font-size:12px; cursor:pointer; }
  .n { text-align:right; white-space:nowrap; }
</style></head><body>
<header><h1>Slide Master 작성현황</h1><small id="gen"></small></header>
<main>
  <div class="kpis" id="kpis"></div>
  <div class="bar"><input type="search" id="q" placeholder="제목·프로젝트 폴더 검색">
    <select id="fam"><option value="">모든 스타일</option></select>
    <select id="days"><option value="7">최근 7일</option><option value="30" selected>최근 30일</option><option value="90">90일</option><option value="99999">전체</option></select></div>
  <table><thead><tr><th>상태</th><th>장표</th><th>스타일</th><th>단계</th><th class="n">쪽</th><th>최신 PPTX</th><th>마지막 작업</th></tr></thead><tbody id="rows"></tbody></table>
</main>
<script>
const D = __DATA__;
const C = { active:'var(--active)', waiting:'var(--waiting)', reexport:'var(--reexport)', stalled:'var(--stalled)', done:'var(--done)' };
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fu = (p) => 'file:///' + p.replace(/\\\\/g, '/').split('/').map(encodeURIComponent).join('/').replace('%3A', ':');
const when = (t) => { if (!t) return ''; const d = new Date(t * 1000); return `${d.getMonth()+1}/${d.getDate()} ${d.toTimeString().slice(0,5)}`; };
let F = { st:'', q:'', fam:'', days:30 };
document.getElementById('gen').textContent = `갱신 ${new Date(D.generated*1000).toLocaleString('ko-KR')} · 프로젝트 ${D.summary.total}개 · ${D.root}`;
const fs = document.getElementById('fam'); Object.keys(D.summary.families).forEach((f) => fs.insertAdjacentHTML('beforeend', `<option>${esc(f)}</option>`));
function kpis() {
  const s = D.summary, k = [['', '전체', s.total], ...['active','waiting','reexport','stalled','done'].map((x) => [x, D.status_label[x], s.counts[x]])];
  document.getElementById('kpis').innerHTML = k.map(([x, l, n]) => `<div class="kpi ${F.st === x ? 'on' : ''}" data-st="${x}"><div class="n" style="color:${x ? C[x] : 'var(--navy)'}">${n}</div><div class="l">${esc(l)}</div></div>`).join('');
}
function rows() {
  const lim = Date.now() / 1000 - F.days * 86400, q = F.q.toLowerCase();
  const list = D.projects.filter((p) => (!F.st || p.status === F.st) && (!F.fam || p.family_label === F.fam) && p.last >= lim && (!q || (p.title + ' ' + p.id).toLowerCase().includes(q)));
  document.getElementById('rows').innerHTML = list.map((p) => {
    const e = p.exports[0];
    const stg = D.stages.map((s) => `<i class="${p.stages[s] ? 'ok' : (s === p.next ? 'nx' : '')}" title="${esc(s)}${p.stages[s] ? ' 완료' : ''}"></i>`).join('');
    return `<tr><td><span class="stb" style="background:${C[p.status]}">${esc(p.status_label)}</span></td>
      <td><div class="t">${esc(p.title)}</div><div class="sub"><a href="${fu(p.path)}">${esc(p.id)}</a> <button class="cp" data-cp="${esc(p.path)}">경로</button></div></td>
      <td><span class="chip">${esc(p.family_label)}</span>${p.canvas ? `<span class="chip">${esc(p.canvas)}</span>` : ''}</td>
      <td><div class="stg">${stg}</div><div class="sub">${p.next ? '다음: ' + esc(p.next) : '모든 단계 끝'}</div></td>
      <td class="n">${p.pages || ''}${p.pages_planned && p.pages_planned !== p.pages ? ` / ${p.pages_planned}` : ''}</td>
      <td>${e ? `<a href="${fu(e.path)}" title="${esc(e.path)}">${esc(e.name)}</a><div class="sub">${when(e.mtime)}${p.export_count > 1 ? ` · 파일 ${p.export_count}개` : ''}</div>` : '<span class="sub">아직 없음</span>'}</td>
      <td>${when(p.last)}</td></tr>`;
  }).join('') || '<tr><td colspan="7" class="sub">조건에 맞는 프로젝트가 없습니다.</td></tr>';
}
document.addEventListener('click', (e) => {
  const k = e.target.closest('[data-st]'); if (k) { F.st = k.dataset.st; kpis(); rows(); return; }
  const c = e.target.closest('[data-cp]'); if (c) navigator.clipboard.writeText(c.dataset.cp);
});
document.getElementById('q').addEventListener('input', (e) => { F.q = e.target.value; rows(); });
fs.addEventListener('change', (e) => { F.fam = e.target.value; rows(); });
document.getElementById('days').addEventListener('change', (e) => { F.days = Number(e.target.value); rows(); });
kpis(); rows();
</script></body></html>
"""


def render_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return HTML_TEMPLATE.replace("__DATA__", payload)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_outputs(data: dict, out_dir: Path | str = DEFAULT_OUT_DIR) -> dict:
    out = Path(out_dir)
    j, h = out / "status.json", out / "작성현황.html"
    _write(j, json.dumps(data, ensure_ascii=False, indent=1))
    _write(h, render_html(data))
    return {"json": str(j), "html": str(h)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Slide Master 프로젝트 작성현황")
    ap.add_argument("projects_dir", nargs="?", default=str(DEFAULT_PROJECTS))
    ap.add_argument("--out-dir", default=None, help="status.json·작성현황.html 위치 (기본 projects/_dashboard)")
    ap.add_argument("--print", action="store_true", help="진행 중인 프로젝트를 표로 출력")
    args = ap.parse_args()
    data = collect(args.projects_dir)
    out = write_outputs(data, args.out_dir or Path(args.projects_dir) / "_dashboard")
    s = data["summary"]
    print(f"프로젝트 {s['total']}개 · " + " · ".join(f"{STATUS_LABEL[k]} {s['counts'][k]}" for k in STATUS_ORDER)
          + f" · {data['seconds']}초")
    if args.print:
        for p in data["projects"]:
            if p["status"] in ("active", "waiting", "reexport"):
                print(f"  [{p['status_label']}] {p['id']} — 다음: {p['next'] or '-'} · {p['pages']}쪽")
    print(f"HTML: {out['html']}\nJSON: {out['json']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
