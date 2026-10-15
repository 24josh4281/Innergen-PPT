#!/usr/bin/env python3
"""
Fill the v30 report diagrams (s65–s74) with a fictional B사 example (예시) and
write a flat deck project per family for QA and preview renders.

Usage:
    python3 docs/innergen-v30/sample_deck_v30.py --skill claude-skills/innergen-deck --out OUT
    then for each OUT/<family>: svg_quality_checker.py, innergen_qaqc.py, svg_to_pptx.py

All names and figures are fictional and marked 예시.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PAGES = [
    ("s65_proposal_understanding", "과업 이해", "B사는 2030 감축 목표 대비 실행 수단이 40% 부족한 상태입니다", "judgment", "diagram", {
        "SITUATION_TITLE": "B사 현황(예시)",
        "SITUATION_BODY": "2030년 배출 30% 감축 공표\n2025년 배출 48만 tCO2eq\n감축 수단 검토 2건에 그침\n공시 의무화 2028년 예정",
        "ISSUE_1_TITLE": "감축 수단 공백", "ISSUE_1_BODY": "목표 대비 수단 확보율 60%\n비용 근거 없는 후보 다수",
        "ISSUE_2_TITLE": "투자 판단 근거 부족", "ISSUE_2_BODY": "수단별 톤당 비용·회수기간 미산정",
        "ISSUE_3_TITLE": "실행 체계 미정", "ISSUE_3_BODY": "담당 조직·과제 관리 기준 없음",
        "RESP_1_TITLE": "감축 수단 풀 20개 구성", "RESP_1_MODULE": "모듈 1", "RESP_1_BODY": "공정·연료·전력 수단을 감축량으로 정량화",
        "RESP_2_TITLE": "MACC·비즈니스 케이스", "RESP_2_MODULE": "모듈 2", "RESP_2_BODY": "톤당 비용과 회수기간으로 우선순위 결정",
        "RESP_3_TITLE": "웨이브 로드맵·과제 정의", "RESP_3_MODULE": "모듈 3", "RESP_3_BODY": "과제별 KPI·책임자·마일스톤 설계",
        "SCOPE": "국내 사업장 4곳 Scope 1·2 · 16주 · 제외: Scope 3 산정, 배출권 거래 대행",
        "SOURCE": "출처: B사 제안요청서(2026.9), 이너젠 분석 · 수치는 예시",
    }),
    ("s66_why_us_pillars", "이너젠 차별화", "이너젠은 감축 실적과 자체 산정 도구로 16주 안에 실행안을 제공할 예정입니다", "promise", "diagram", {
        "VALUE_PROP": "B사 2030 목표를 투자 가능한 과제로 바꾸는 파트너",
        "PILLAR_1_TITLE": "감축사업 실행 경험", "PILLAR_1_BODY": "사업장 감축 설계부터\n인정 신청까지 직접 수행\n방법론·MRV 검토 포함",
        "PILLAR_2_TITLE": "자체 산정 도구", "PILLAR_2_BODY": "수단별 감축량·비용을\n같은 기준으로 비교\n가정 변경 즉시 반영",
        "PILLAR_3_TITLE": "공시 연계", "PILLAR_3_BODY": "감축 경로를 공시 지표와\n같은 기준으로 정리\n검증 대응 자료 동시 작성",
        "PROOF_1_NUM": "40건+", "PROOF_1_LABEL": "감축사업 수행(예시)",
        "PROOF_2_NUM": "2주", "PROOF_2_LABEL": "MACC 1차본 작성(예시)",
        "PROOF_3_NUM": "12개사", "PROOF_3_LABEL": "공시 대응 지원(예시)",
        "FOUNDATION": "전담 PM 1명 · 산정 전문가 2명 · 주간 보고와 격주 경영진 점검",
        "SOURCE": "출처: 이너젠 수행 실적(예시) · 회사 수치는 company-facts 원장에서 확인 후 기입",
    }),
    ("s67_rfp_compliance", "요구사항 대응", "이너젠은 제안요청서 요구사항 6건 중 5건을 그대로 충족할 예정입니다", "promise", "table", {
        "REQ_1": "감축 수단 도출·정량화", "RESP_1": "수단 풀 20개, 사업장별 감축량 산정", "LOC_1": "Ⅲ-1", "FIT_1": "●",
        "REQ_2": "수단별 경제성 분석", "RESP_2": "MACC와 비즈니스 케이스(NPV·회수기간)", "LOC_2": "Ⅲ-2", "FIT_2": "●",
        "REQ_3": "2030 감축 경로", "RESP_3": "웨지 경로와 연도별 감축량", "LOC_3": "Ⅲ-3", "FIT_3": "●",
        "REQ_4": "실행 과제·로드맵", "RESP_4": "과제 정의서 8건, 웨이브 3단계", "LOC_4": "Ⅲ-4", "FIT_4": "●",
        "REQ_5": "임직원 교육 2회", "RESP_5": "교육 2회와 실무 안내서", "LOC_5": "Ⅳ-2", "FIT_5": "●",
        "REQ_6": "Scope 3 산정", "RESP_6": "범위 밖, 후속 과제로 별도 제안", "LOC_6": "Ⅴ", "FIT_6": "○",
        "SUMMARY": "충족 5건 · 대안 제시 1건(Scope 3 후속)",
        "SOURCE": "출처: B사 제안요청서(2026.9) 요구사항 목록 · 예시",
    }),
    ("s68_hypothesis_tracker", "가설 검증 현황", "가설 5개 중 3개는 확인됐고 연료 전환 가설은 수정이 필요합니다", "judgment", "table", {
        "HYPO_1": "공정 개선만으로 15% 감축 가능", "ANALYSIS_1": "설비별 에너지 원단위", "EVIDENCE_1": "사업장 4곳 합산 16% 가능", "VERDICT_1": "확인", "NEXT_1": "투자비 확정",
        "HYPO_2": "LNG 전환이 가장 경제적", "ANALYSIS_2": "연료별 톤당 비용", "EVIDENCE_2": "전기 보일러가 톤당 2만 원 저렴", "VERDICT_2": "수정", "NEXT_2": "전력 단가 재확인",
        "HYPO_3": "재생에너지 PPA 30% 가능", "ANALYSIS_3": "조달 가능 물량", "EVIDENCE_3": "2028년부터 25%까지", "VERDICT_3": "수정", "NEXT_3": "물량 협의",
        "HYPO_4": "폐열 회수 회수기간 3년 내", "ANALYSIS_4": "회수기간 산정", "EVIDENCE_4": "2.6년(잠정)", "VERDICT_4": "확인", "NEXT_4": "현장 실측",
        "HYPO_5": "구매 정책 변경 효과 미미", "ANALYSIS_5": "구매 데이터 분석", "EVIDENCE_5": "자료 수령 대기", "VERDICT_5": "검증 중", "NEXT_5": "자료 9.30",
        "INTERIM_CONCLUSION": "감축 경로의 60%는 확인된 수단으로 설명됨(잠정)",
        "SOURCE": "출처: B사 설비·에너지 자료(2025), 이너젠 분석 · 잠정 수치(예시)",
    }),
    ("s69_issue_risk_log", "이슈·리스크 관리", "MACC 1차 산정 진행 중이며 리스크 5건 중 2건은 결정이 필요함 (10.14 기준)", "status", "table", {
        "MATRIX_NOTE": "표식 R1–R5는 오른쪽 로그와 같음",
        "RISK_1": "전력 단가 자료 지연", "IMPACT_1": "높음", "ACTION_1": "대체 단가로 1차 산정", "OWNER_1": "B사 구매", "DUE_1": "9.30", "STATE_1": "진행",
        "RISK_2": "PPA 물량 불확실", "IMPACT_2": "중간", "ACTION_2": "시나리오 2개로 분리", "OWNER_2": "이너젠", "DUE_2": "10.7", "STATE_2": "진행",
        "RISK_3": "사업장 실측 일정", "IMPACT_3": "중간", "ACTION_3": "원격 자료 우선 검토", "OWNER_3": "B사 설비", "DUE_3": "10.14", "STATE_3": "대기",
        "RISK_4": "경영진 보고 일정 변경", "IMPACT_4": "낮음", "ACTION_4": "보고 자료 1주 전 공유", "OWNER_4": "PMO", "DUE_4": "10.21", "STATE_4": "완료",
        "RISK_5": "투자 한도 미확정", "IMPACT_5": "높음", "ACTION_5": "한도 2안으로 MACC 작성", "OWNER_5": "B사 재무", "DUE_5": "10.10", "STATE_5": "진행",
        "ESCALATION": "R1 전력 단가 자료를 9.30까지 받지 못하면 최종보고 1주 지연 · 재무팀 투자 한도 결정 요청",
        "SOURCE": "출처: 프로젝트 이슈 로그(2026.10.14 기준) · 예시",
    }),
    ("s70_pyramid_summary", "핵심 요약", "B사는 공정·연료·전력 세 수단으로 2030년 30% 감축 목표를 달성할 수 있습니다", "conclusion", "diagram", {
        "MAIN_POINT": "세 수단으로 2030년 30% 감축 가능, 총 투자 420억 원(예시)",
        "KEY_1_TITLE": "공정 개선 16%", "KEY_1_BODY": "투자 회수 3년 내 수단 위주",
        "KEY_2_TITLE": "연료 전환 8%", "KEY_2_BODY": "전기 보일러 우선, LNG 보완",
        "KEY_3_TITLE": "재생에너지 6%", "KEY_3_BODY": "2028년부터 PPA 25%",
        "SUPPORT_1_1": "폐열 회수 회수기간 2.6년", "SUPPORT_1_2": "압축공기 누설 개선", "SUPPORT_1_3": "인버터 교체 120대",
        "SUPPORT_2_1": "톤당 비용 −2만 원", "SUPPORT_2_2": "보일러 6기 교체", "SUPPORT_2_3": "전력 계약 변경 필요",
        "SUPPORT_3_1": "조달 물량 2028년 확보", "SUPPORT_3_2": "자가 태양광 5MW", "SUPPORT_3_3": "REC 보완 구매",
        "NEXT_ACTION": "11월 이사회에 Wave 1 투자 140억 원 승인 안건 상정",
        "SOURCE": "출처: 이너젠 분석(2026.10) · 수치는 예시",
    }),
    ("s71_findings_initiatives", "진단–과제 연계", "개선 과제 5개가 진단 결과 5건을 모두 다루며 과제 ①·④가 핵심입니다", "judgment", "table", {
        "INIT_1": "① 공정\n효율화", "INIT_2": "② 연료\n전환", "INIT_3": "③ 재생\n에너지", "INIT_4": "④ 감축\n전담 조직", "INIT_5": "⑤ 데이터\n관리 체계",
        "FINDING_1": "에너지 원단위 업계 대비 12% 높음", "FINDING_2": "보일러 노후화(평균 18년)", "FINDING_3": "전력 배출 비중 45%",
        "FINDING_4": "감축 과제 책임자 부재", "FINDING_5": "사업장별 자료 기준 상이",
        "MARK_1_1": "●", "MARK_1_5": "◐", "MARK_2_1": "◐", "MARK_2_2": "●", "MARK_3_3": "●", "MARK_3_2": "◐",
        "MARK_4_4": "●", "MARK_5_5": "●", "MARK_5_4": "◐",
        "PRIORITY_1": "1순위 · W1", "PRIORITY_2": "1순위 · W1", "PRIORITY_3": "2순위 · W2", "PRIORITY_4": "1순위 · W1", "PRIORITY_5": "2순위 · W2",
        "MAP_NOTE": "",
        "SOURCE": "출처: 이너젠 진단(2026.9) · 예시",
    }),
    ("s72_initiative_charter", "과제 정의서", "생산기술팀은 2027년까지 공정 효율화로 배출 7.7만 톤을 줄여야 합니다", "recommendation", "table", {
        "CHARTER_ID": "과제 ①", "CHARTER_NAME": "공정 효율화(폐열 회수·인버터)", "OWNER": "책임자: 생산기술팀장(예시)",
        "OBJECTIVE": "2027년까지 Scope 1·2 배출 7.7만 tCO2eq 감축\n에너지 비용 연 38억 원 절감",
        "SCOPE": "포함: 사업장 4곳 폐열 회수, 인버터 교체 120대\n제외: 신규 라인 증설",
        "RISK": "설비 정지 일정 확보(생산 계획 연동)\n전력 단가 변동 시 회수기간 재산정",
        "KPI_1_NAME": "감축량(tCO2eq)", "KPI_1_BASE": "0", "KPI_1_TARGET": "77,000",
        "KPI_2_NAME": "에너지 원단위", "KPI_2_BASE": "100", "KPI_2_TARGET": "88",
        "KPI_3_NAME": "투자 회수기간", "KPI_3_BASE": "–", "KPI_3_TARGET": "3년 내",
        "MS_1_DATE": "'26.12", "MS_1_NAME": "투자 승인", "MS_2_DATE": "'27.3", "MS_2_NAME": "설계 완료",
        "MS_3_DATE": "'27.9", "MS_3_NAME": "1차 설치", "MS_4_DATE": "'27.12", "MS_4_NAME": "효과 검증",
        "RESOURCE": "투자 140억 원 · 전담 4명 · 외부 설계 1건",
        "BENEFIT": "연 7.7만 톤 감축과 에너지 비용 38억 원 절감, 2030 목표의 16%p 기여",
        "SOURCE": "출처: 이너젠 분석(2026.10) · 수치는 예시",
    }),
    ("s73_wave_roadmap", "실행 로드맵", "B사는 2026년 Wave 1에서 회수 3년 내 과제 3건을 먼저 착수해야 합니다", "recommendation", "diagram", {
        "WAVE_1_NAME": "Wave 1 · 즉시 효과", "WAVE_1_PERIOD": "'26.12 – '27.12",
        "WAVE_2_NAME": "Wave 2 · 전환 확대", "WAVE_2_PERIOD": "'28 – '29",
        "WAVE_3_NAME": "Wave 3 · 정착", "WAVE_3_PERIOD": "'30",
        "WS_1": "공정", "WS_2": "연료", "WS_3": "전력", "WS_4": "조직·데이터",
        "ACT_1_1": "폐열 회수·인버터 교체", "ACT_1_2": "공정 자동 제어 확대", "ACT_1_3": "효과 검증·확산",
        "ACT_2_1": "보일러 2기 전기화", "ACT_2_2": "보일러 4기 추가 전환", "ACT_2_3": "잔여 LNG 최적화",
        "ACT_3_1": "자가 태양광 2MW", "ACT_3_2": "PPA 25% 계약", "ACT_3_3": "REC 보완 구매",
        "ACT_4_1": "감축 전담 조직 신설", "ACT_4_2": "사업장 데이터 기준 통일", "ACT_4_3": "공시 검증 대응",
        "MILE_1": "감축 7.7만 톤", "MILE_2": "누적 감축 20%", "MILE_3": "2030 목표 30%",
        "PREREQUISITE": "Wave 1 투자 140억 원 승인(11월 이사회) · 전력 계약 변경 협의",
        "SOURCE": "출처: 이너젠 분석(2026.10) · 예시",
    }),
    ("s74_business_case", "투자 효과", "총 투자 420억 원은 효과 누적으로 2030년에 회수될 것으로 예상됩니다", "outlook", "chart", {
        "AXIS_Y": "단위: 억 원(예시)",
        "BEN_1": "", "BEN_2": "60", "BEN_3": "140", "BEN_4": "210", "BEN_5": "250", "BEN_6": "270",
        "INV_1": "−250", "INV_2": "−140", "INV_3": "−30", "INV_4": "", "INV_5": "", "INV_6": "",
        "YEAR_1": "'26", "YEAR_2": "'27", "YEAR_3": "'28", "YEAR_4": "'29", "YEAR_5": "'30", "YEAR_6": "'31",
        "PAYBACK": "누적 0 → '30 초",
        "KPI_1_VALUE": "420억 원", "KPI_1_LABEL": "총 투자(예시)",
        "KPI_2_VALUE": "3.2년", "KPI_2_LABEL": "단순 회수기간",
        "KPI_3_VALUE": "+310억 원", "KPI_3_LABEL": "NPV(할인율 6%)",
        "ASSUMPTIONS": "전력 단가 연 3% 상승\n배출권 가격 톤당 3만 원\n설비 수명 15년",
        "VERDICT": "Wave 1 투자는 회수 3년 내 수단만으로 구성해 승인 부담을 줄입니다",
        "SOURCE": "출처: 이너젠 분석(2026.10) · 가정·수치는 예시",
    }),
]

FAM_SECTION = {"innergen_business": "Ⅲ. 감축 실행 방안", "innergen_lecture": "Ⅲ. 감축 실행 방안", "innercarry": "감축 실행 방안"}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fill(svg: str, values: dict) -> str:
    def repl_text(m):
        open_tag, token = m.group(1), m.group(2)
        val = values.get(token)
        if val is None:
            return m.group(0)
        size = float(re.search(r'font-size="([\d.]+)"', open_tag).group(1))
        x = re.search(r' x="([\d.]+)"', open_tag).group(1)
        lines = val.split("\n")
        if len(lines) == 1:
            return f"{open_tag}{esc(val)}</text>"
        spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else round(size * 1.35, 2)}">{esc(l)}</tspan>' for i, l in enumerate(lines))
        return f"{open_tag}{spans}</text>"
    svg = re.sub(r'(<text [^>]*>)\{\{([A-Z0-9_]+)\}\}</text>', repl_text, svg)
    # drop placeholders left empty or unknown
    svg = re.sub(r'<g id="[^"]+"[^>]*><text [^>]*>(?:\{\{[A-Z0-9_]+\}\})?</text></g>\n?', "", svg)
    return svg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    for fam in ("innergen_business", "innergen_lecture", "innercarry"):
        proj = args.out / fam
        subprocess.run([sys.executable, str(args.skill / "scripts/start_deck.py"), "--family", fam, "--out", str(proj), "--force"],
                       check=True, stdout=subprocess.DEVNULL)
        rows = ["| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 | 거버닝 유형 | 본문 구성 |", "|---|---|---|---|---|---|---|"]
        for n, (lay, title, gov, gtype, style, vals) in enumerate(PAGES, 1):
            tpl = (proj / "templates" / f"{lay}.svg").read_text(encoding="utf-8")
            v = dict(vals, PAGE_TITLE=title, KEY_MESSAGE=gov, PAGE_NUM=str(n), SECTION_NAME=FAM_SECTION[fam])
            (proj / "svg_output" / f"{n:02d}_{lay}.svg").write_text(fill(tpl, v), encoding="utf-8")
            rows.append(f"| {n} | {lay} | {title} | {gov} | 예시 | {gtype} | {style} |")
        (proj / "outline.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(f"[sample_v30] {fam}: {len(PAGES)} pages → {proj}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
