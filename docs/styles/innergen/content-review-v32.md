# 이너젠 AI 내용 검토 절차 v32 (2026-10-21)

디자인 검사(`svg_quality_checker.py`·`innergen_qaqc.py`)와 규칙 검사(`innergen_story_check.py`)는 글자·위치·정규식으로 판단한다. "이 거버닝이 정말 그 장표의 결론인가", "도식이 내용의 관계를 맞게 그렸는가", "마지막 장이 첫 장의 질문에 답했는가"는 사람이나 AI가 읽어야 판단할 수 있다. 이 문서는 그 판단을 **작성자와 다른 AI 검토자**가 같은 기준으로 하고, 결과를 기록해 게이트로 쓰는 절차다. 원칙은 [content-principles-v32.md](content-principles-v32.md), 기계 규칙은 [content-principles-v32.json](content-principles-v32.json)에 있다.

## 1. 전체 흐름

| 단계 | 누가 | 무엇을 | 산출물 | 통과 기준 |
|---|---|---|---|---|
| ① 스토리라인 설계 | 작성 AI(Strategist) | 핵심 질문·답·근거 3개·장 구성·장표별 거버닝 초안·엔딩 메시지를 먼저 쓴다(원칙 §2) | `design_spec.md` §IX 장표 계획표 | — |
| ② 계획 검사 | 스크립트 | `innergen_story_check.py <project> --outline <계획표>` + `innergen_content_check.py --outline` | `analysis/story_check_report.md` | ERROR 0 |
| ③ 계획 검토 | 독립 AI 검토자 | 고스트 덱(제목·거버닝만)으로 스토리라인·목차·엔딩을 1차 채점 | `analysis/content_review_plan.json` | 각 항목 3점 이상 |
| ④ 장표 작성 | 작성 AI(Executor) | 계획표의 거버닝·결론을 그대로 쓰고 본문 근거·도식을 채운다 | `svg_output/` | — |
| ⑤ 덱 검사 | 스크립트 | `svg_quality_checker.py` → `innergen_qaqc.py` → `innergen_story_check.py` | 각 보고서 | ERROR 0 |
| ⑥ 덱 검토 | 독립 AI 검토자 | 6개 항목 채점·지적·수정안 | `analysis/content_review.json` | 각 항목 3점 이상, major 지적 0 |
| ⑦ 수정·재검토 | 작성 AI → 검토자 | 지적 반영 후 ⑤·⑥ 반복(최대 2회) | 갱신된 기록 | `innergen_story_check.py --review` PASS |

- ③과 ⑥은 작성한 대화 맥락을 물려받지 않은 실행이어야 한다(Claude Code: 새 서브에이전트, Codex/Gemini: 새 세션). 같은 실행이 자기 글을 채점하면 기록의 `reviewer`를 `author`로 적고, 게이트(N51)가 실패한다.
- 검토 기록에는 `innergen_story_check.py`가 출력한 `ghost` 해시를 그대로 적는다. 장표를 고치면 해시가 바뀌므로 오래된 검토는 N51로 막힌다.
- 2회 수정 뒤에도 3점 미만이면 멈추고 사용자에게 남은 지적과 선택지를 보고한다. 점수를 맞추려고 원문에 없는 사실을 만들지 않는다.

## 2. 검토자에게 주는 입력

1. `analysis/storyline_ghost.md` — 목차와 장표별 `제목 | 거버닝`, 결론 칸.
2. `analysis/story_pages.json` — 장표별 전체 텍스트(본문·칸·목차 항목).
3. `analysis/story_check_report.md`·`analysis/innergen_qaqc_report.md` — 규칙 검사 결과(검토자가 같은 지적을 반복하지 않도록).
4. 원문 요약: `sources/*.md` 중 해당 장표에 쓰인 부분, `design_spec.md`의 대상 독자·목적·보고 유형.
5. 이 문서 §3 채점표와 [원칙 문서](content-principles-v32.md).

렌더 이미지는 도식 항목을 볼 때만 필요한 장표를 골라 연다(`exports/` PNG 또는 `verify_deck.py` contact sheet).

## 3. 채점표 (1–5점)

점수: 1 미흡 · 2 보완 필요 · 3 기준 충족 · 4 우수 · 5 레퍼런스 수준. 3점이 통과선이고 목표는 4점이다. 각 점수에는 근거 장 번호(`evidence`)를 2개 이상 적는다.

| 항목(key) | 3점 기준(통과선) | 5점 기준 | 흔한 감점 |
|---|---|---|---|
| `storyline` 스토리라인 | 거버닝만 이어 읽어도 핵심 질문 → 답 → 근거 → 행동이 이어진다. 장 사이에 논리 비약이 없다 | 첫 장 질문에 대한 답이 3장 안에 나오고(답 먼저), 근거 3개가 서로 겹치지 않고 빠짐없다(MECE) | 장표가 자료 순서로 나열됨, 같은 말 반복, 결론이 마지막에만 처음 등장 |
| `toc` 목차 | 장 3–6개, 장명이 명사구로 대등하고 본문 장 구분·제목 번호와 1:1. 목차 순서가 논리 순서(배경→현황→분석→과제→계획) | 장명만 읽어도 이 덱의 대상·쟁점이 보인다(일반명 "개요·결론" 없음) | 장명이 문장·질문, 장 수 과다, 본문에 없는 장, 장명과 본문 불일치 |
| `governing` 거버닝 | 모든 본문 장표가 주어 + 판단(+수치) 한 문장. 제목은 주제, 거버닝은 "그래서 무엇"이다. 수치는 본문 근거와 맞다 | 거버닝마다 비교 기준(전년·목표·기준 대비)이 있고, 독자가 할 일이나 판단이 드러난다 | 명사구·소개문("~을 설명합니다"), 상투어, 본문에 없는 수치, 제목 복사 |
| `body` 본문 | 본문 블록이 거버닝을 뒷받침하는 근거(사실·수치·기준)이며 블록 2–3개, 출처·단위·기준시점이 있다 | 근거 → 해석 → 시사점이 분리되고, 표 셀 문법(현황 긍정·Gap 부정)이 맞다 | 거버닝과 무관한 정보, 같은 내용 반복, 출처 없는 수치, 시사점 없는 표 |
| `diagram` 도식 | 내용의 관계(순서·위계·비교·매트릭스·인과)와 도식 종류가 맞고, 도식 안 라벨이 명사구로 대등하다 | 도식만 봐도 거버닝의 판단이 보인다(강조 한 곳) | 순서 없는 내용에 화살표, 병렬 항목에 피라미드, 축 이름 없는 매트릭스, 장식용 도식 |
| `ending` 엔딩 | 마지막 1–3장이 핵심 메시지 3개 이내로 정리하고 첫 장 질문에 답한다. 보고형은 다음 행동에 주체·기한이 있다 | 결정 요청(안건·선택지·권고·기한)이 한 블록에 모이고, 마지막 문장이 첫 장 과제 문장을 다시 부른다 | "감사합니다"만 있음, 새로운 내용 등장, 막연한 다짐, 기한·담당 없음 |

## 4. 기록 형식 `analysis/content_review.json`

```json
{
  "version": "32",
  "ghost_sha256": "innergen_story_check.py가 출력한 ghost 값",
  "reviewer": "independent-subagent",
  "stage": "deck",
  "scores": {
    "storyline": {"score": 4, "evidence": [3, 7, 15], "note": "답이 3장에 먼저 나오고 근거 3개가 장 구성과 일치"},
    "toc":       {"score": 3, "evidence": [2], "note": "..."},
    "governing": {"score": 3, "evidence": [5, 9], "note": "..."},
    "body":      {"score": 4, "evidence": [6, 11], "note": "..."},
    "diagram":   {"score": 3, "evidence": [8, 12], "note": "..."},
    "ending":    {"score": 2, "evidence": [16], "note": "다음 행동에 담당·기한 없음"}
  },
  "findings": [
    {"page": 16, "role": "ending", "severity": "major", "issue": "다음 단계에 주체·기한 없음",
     "fix": "'이너젠은 11.15까지 산정 결과 초안을 제공하고, 귀사는 11.08까지 활동자료를 회신' 형태로", "status": "open"}
  ]
}
```

- `severity`: `major`(통과 불가: 스토리 단절·사실 근거 없음·엔딩 누락) · `minor`(문장 다듬기) · `info`.
- `status`: 작성 AI가 고친 뒤 `fixed`로 바꾸고 해당 장 번호를 유지한다. 재검토자는 `fixed` 항목을 확인하고 새 해시로 다시 기록한다.
- 검토자는 원문에 없는 사실을 수정안으로 제안하지 않는다. 근거가 필요하면 `fix`에 "원문 확인 필요: …"로 적는다.

## 5. 검토자 지시문(복사해 사용)

> 당신은 이 덱을 작성하지 않은 독립 검토자입니다. `analysis/storyline_ghost.md`, `analysis/story_pages.json`, 규칙 검사 보고서 두 개, `docs/styles/innergen/content-principles-v32.md`, `docs/styles/innergen/content-review-v32.md` §3을 읽고, 대상 독자와 보고 유형(`design_spec.md`)을 확인하세요. 먼저 거버닝만 순서대로 읽고 이 덱의 핵심 질문과 답을 한 문장씩 적은 뒤, 6개 항목을 1–5점으로 채점하세요. 점수마다 근거 장 번호 2개 이상과 이유를 적고, 3점 미만 항목은 고칠 장표·고친 문장(수정안)을 `findings`에 남기세요. 규칙 검사가 이미 지적한 것은 반복하지 말고, 규칙이 못 보는 의미 문제(논리 비약, 근거와 판단의 불일치, 도식-관계 불일치, 엔딩의 답 누락)에 집중하세요. 원문에 없는 수치·사실은 만들지 마세요. 결과를 `analysis/content_review.json`에 §4 형식으로 저장하고, `ghost_sha256`에는 아래 값을 그대로 쓰세요: `<ghost>`.

## 6. 게이트 명령

```bash
python3 .claude/skills/ppt-master/scripts/innergen_story_check.py projects/<project> --deck-type <유형>
# 검토 기록이 있으면 자동으로 읽는다. 다른 위치면 --review <path>
```

| 코드 | 내용 | 수준 |
|---|---|---|
| N50 | 검토 기록 없음 | WARN(전달 전 `--strict`면 실패) |
| N51 | 기록의 해시가 현재 덱과 다름 / 검토자가 작성자 | ERROR |
| N52 | 항목 점수·근거 장 누락 | ERROR |
| N53 | 3점 미만(ERROR) / 4점 미만(WARN) | ERROR / WARN |
| N54 | major 지적 미해결(ERROR), 수정안 없는 지적(WARN) | ERROR / WARN |

## 7. 시험 결과 (2026-10-21)

`20261016_kssb_nhn_proposal_v2`(제안 16장)에 ⑤·⑥을 실제로 돌렸다. 규칙 검사는 ERROR 0이었다(N20 소개형 거버닝 1건, N41 기한 없는 다음 행동 1건). 독립 검토자는 스토리라인·목차·거버닝·본문 3점, 도식·엔딩 2점을 주고 major 3건을 남겼다. P09 거버닝이 본문과 반대 내용인 것, 엔딩에 주체·기한 없음, 단계·일정을 텍스트 행으로만 그린 것이다. 첫째와 셋째는 정규식으로 잡을 수 없는 의미 결함이다. 게이트는 N53·N54로 FAIL을 냈다. 이 결과로 N41을 "주체와 기한이 한 줄에 같이 있어야 함"으로 좁혔다(이전에는 "다음 주기"·"승인까지"가 기한으로 잡혔다).

## 8. 한계

- AI 검토는 같은 계열 모델의 판단이라 사람 검토를 대신하지 않는다. 고객 전달 덱은 이너젠 담당자가 고스트 덱과 엔딩을 한 번 더 읽는다.
- 점수는 비교 기준이다. 같은 덱을 두 번 채점하면 ±1점 차이가 날 수 있으므로 3점 경계의 항목은 근거 문장으로 판단한다.
- 원문 사실 확인은 `sources/` 범위에서만 한다. 원문 밖 최신 제도·수치는 별도 확인 대상이다.
