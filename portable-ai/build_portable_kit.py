#!/usr/bin/env python3
"""
Build the portable INNerGEN deck kit for ChatGPT (Custom GPT / Projects) and
Gemini (Gems) from the Claude innergen-deck skill sources, so the role
instructions, design tokens, layout slots, company facts and content rules
stay identical across tools.

Usage:
    python3 portable-ai/build_portable_kit.py            # writes portable-ai/kit/

Output (10 files; 00_orchestrator.md is pasted as instructions, the other
nine are uploaded as knowledge files):
    00_orchestrator.md 01_planner.md 02_writer.md 03_designer.md 04_qa.md
    design-tokens.md layout-catalog.md company-facts-v28.md
    standard-decks-v28.md content-requirements-v25.md

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SKILL = REPO / "claude-skills" / "innergen-deck"
OUT = HERE / "kit"
FAMILIES = {
    "innergen_lecture": "기본 이너젠 — 교육·강의·세미나",
    "innergen_business": "사업소개서·회사소개·컨설팅 보고",
    "innercarry": "이너캐리 — 제품·SaaS 소개",
}
REFS = ("company-facts-v28.md", "standard-decks-v28.md", "content-requirements-v25.md")
FRAME_USE = {
    "01_cover": "표지", "02_toc": "목차(교육 계열 전용)", "02b_toc_pages": "목차",
    "02c_section_divider": "장 구분(PART)", "03a_content": "기본 본문", "03b_content_final": "본문+결론 박스",
    "03c_content_split": "좌우 분할(설명+도식)", "03d_content_dual": "두 칸 비교·병렬", "03e_content_table": "표",
    "03f_content_kpi": "핵심 숫자 3개", "03g_content_process": "단계 흐름", "04_ending": "맺음·연락처",
    "s01_exec_summary": "핵심 요약 카드 4개+종합", "s02_findings_insights": "발견 사항→시사점", "s03_chart_insight": "차트+해설",
    "s04_chart_table_strip": "차트+표 띠", "s05_entity_matrix": "대상×속성 매트릭스", "s06_principle_matrix": "원칙×기준 매트릭스",
    "s07_asis_tobe_effect": "As-Is→To-Be→효과", "s08_phase_roadmap": "단계별 로드맵", "s09_year_timeline": "연도 타임라인",
    "s10_maturity_heatmap": "성숙도 히트맵", "s11_list_zoom": "목록+확대 설명", "s12_actor_checklist": "주체별 체크리스트",
    "s13_key_takeaways": "핵심 시사점", "s14_task_structure": "과제 구조도", "s15_vertical_chevron": "세로 단계(쉐브론)",
    "s16_period_applicability": "기간별 적용 대상", "s17_decision_tree": "의사결정 트리", "s18_keyword_grid": "키워드 격자",
    "s19_compare_implication": "비교+시사점", "s20_self_check": "자가진단", "s21_guidance_focus": "지침 핵심",
    "s22_case_capture": "사례 화면 캡처", "s23_key_summary": "핵심 정리",
    "s43_issue_tree": "이슈 트리", "s44_hypothesis_workplan": "가설·작업계획", "s45_scqa_storyline": "SCQA 스토리라인",
    "s46_driver_tree": "드라이버 트리", "s47_waterfall_bridge": "워터폴 브리지", "s48_macc_curve": "한계감축비용(MACC) 곡선",
    "s49_pathway_wedge": "감축 경로 웨지", "s50_materiality_matrix": "중대성 매트릭스", "s51_risk_heatmap": "리스크 히트맵",
    "s52_scenario_matrix": "시나리오 매트릭스", "s53_harvey_compare": "하비볼 비교", "s54_raci_matrix": "RACI 매트릭스",
    "s55_stakeholder_map": "이해관계자 지도", "s56_three_horizons": "3 Horizons", "s57_nine_box": "9-Box", "s58_operating_model": "운영 모델",
}


def _lock(family: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    cur = None
    for line in (SKILL / "locks" / f"{family}.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = sections.setdefault(line[3:].strip(), {})
        elif cur is not None and line.startswith("- ") and ":" in line:
            k, v = line[2:].split(":", 1)
            cur[k.strip()] = v.strip()
    return sections


def design_tokens() -> str:
    md = ["# 이너젠 디자인 토큰 (계열별)", "",
          "> `build_portable_kit.py`가 Claude 스킬의 lock 파일에서 만든다. 손으로 고치지 말고 원본 lock을 고친 뒤 다시 만든다.",
          "> 색은 아래 값만 쓴다. 다른 컨설팅사 브랜드 색·로고를 쓰지 않는다. 크기 단위 px(1pt = 1.333px).", ""]
    for fam, label in FAMILIES.items():
        lk = _lock(fam)
        md += [f"## {fam} — {label}", "",
               f"- 캔버스: {lk.get('canvas', {}).get('viewBox', '')} ({lk.get('canvas', {}).get('format', '')})",
               f"- 글꼴: {lk.get('typography', {}).get('font_family', '')}", "",
               "| 색 이름 | 값 |", "|---|---|"]
        md += [f"| {k} | {v} |" for k, v in lk.get("colors", {}).items()]
        md += ["", "| 글자 역할 | 크기(px) |", "|---|---|"]
        md += [f"| {k} | {v} |" for k, v in lk.get("typography", {}).items() if k not in ("font_family", "code_family")]
        vs = lk.get("visual_style", {}).get("visual_style_behavior")
        if vs:
            md += ["", f"모양: {vs}"]
        md.append("")
    return "\n".join(md)


def _skill_labels() -> dict[str, str]:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in re.finditer(r"`(s\d{2}_[a-z0-9_]+)`\s*\(([^)]+)\)", text)}


def layout_catalog() -> str:
    labels = _skill_labels()
    maps = {f: json.loads((SKILL / "templates" / "decks" / f"{f}.json").read_text(encoding="utf-8")) for f in FAMILIES}
    base = maps["innergen_business"]
    ids = sorted({Path(k).stem for m in maps.values() for k in m if k.endswith(".svg")})
    md = ["# 레이아웃 목록과 칸(슬롯) 이름", "",
          "> `build_portable_kit.py`가 Claude 스킬 템플릿에서 만든다. 디자이너는 아래 id와 칸 이름만 쓴다.",
          "> 세 계열이 같은 목록을 쓰며 `02_toc`만 교육 계열 전용이다(나머지 계열은 `02b_toc_pages`).",
          "> 공통 칸: PAGE_TITLE(제목) · KEY_MESSAGE(거버닝) · SECTION_NAME · SOURCE(출처) · PAGE_NUM.", "",
          "| 레이아웃 id | 쓰임 | 전용 칸 |", "|---|---|---|"]
    common = {"PAGE_TITLE", "KEY_MESSAGE", "SECTION_NAME", "SOURCE", "PAGE_NUM", "CONTENT_AREA"}
    for lid in ids:
        src = base.get(f"templates/{lid}.svg") or next(m[f"templates/{lid}.svg"] for m in maps.values() if f"templates/{lid}.svg" in m)
        slots = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", src)) - common)
        use = FRAME_USE.get(lid) or labels.get(lid) or lid.split("_", 1)[1].replace("_", " ")
        md.append(f"| `{lid}` | {use} | {', '.join(slots)} |")
    md += ["", "칸 이름의 숫자(_1, _2 …)는 반복 칸이다. 내용이 칸 수보다 적으면 남는 번호를 빼고, 많으면 쪽을 나눈다."]
    return "\n".join(md) + "\n"


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for f in sorted((HERE / "roles").glob("*.md")):
        shutil.copy2(f, OUT / f.name)
    for name in REFS:
        shutil.copy2(SKILL / "references" / name, OUT / name)
    (OUT / "design-tokens.md").write_text(design_tokens(), encoding="utf-8")
    (OUT / "layout-catalog.md").write_text(layout_catalog(), encoding="utf-8")
    files = sorted(OUT.iterdir())
    print(f"[portable_kit] {len(files)} files -> {OUT.relative_to(REPO)}")
    for f in files:
        print(f"  {f.name:32s} {f.stat().st_size:>7,d} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
