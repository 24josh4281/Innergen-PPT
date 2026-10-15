# 이너젠 장표 QA/QC 체계 v21 — 균일성 점검

작성일 2026-10-14, 규칙표 rev.22(계열 4종·거버닝 한 줄·컴팩트 글자 하한) → rev.23(v23 구조 19종을 덱 유형별 필수·마무리 세트에 반영: 착수 = 과업 개요·간트·자료 요청, 주간·격주 = 진행현황·결정 요청, 진단 = 진단표·우선순위, 최종·브리핑 = 경영진 요약 1장). 규칙표는 [qaqc-v21.json](qaqc-v21.json), 실행 스크립트는 `.claude/skills/ppt-master/scripts/innergen_qaqc.py`.

## 1. 목적과 위치

`svg_quality_checker.py`는 SVG·PPTX 변환 계약(좌표 초과, 플레이스홀더 구조, 글자 폭 추정)을 검사한다. 이 체계는 그 위에 **이너젠 디자인 규칙의 내용·균일성 층**을 더한다. 같은 규칙으로 만든 덱이 사용자마다 달라지는 원인(거버닝 길이·문체, 제목 형식, 목차와 본문 불일치, 고정 요소 위치, 글자 크기, 출처 표기, 마무리 세트)을 자동으로 잡아낸다.

실행 시점은 두 번이다.

| 시점 | 명령 | 통과 기준 |
|---|---|---|
| Executor 마지막 품질 게이트(`svg_quality_checker.py` 0 errors 직후, Step 7 내보내기 전) | `python3 scripts/innergen_qaqc.py <project> --deck-type <유형>` | ERROR 0. WARN은 사유를 적고 넘기거나 수정 |
| 전달 직전(`verify_deck.py` PASS 뒤) | `python3 scripts/innergen_qaqc.py <project> --deck-type <유형> --strict` | WARN까지 0, 또는 남긴 WARN을 전달 메모에 기재 |

출력은 `<project>/analysis/innergen_qaqc_report.md`와 `.json`이다. 이너젠 계열(`innergen_lecture` 등)에서만 쓰며, 다른 스타일에는 적용하지 않는다.

## 2. 실행

```bash
python3 .claude/skills/ppt-master/scripts/innergen_qaqc.py projects/<project> \
  --deck-type lecture            # lecture|handout|seminar|proposal|kickoff|weekly|biweekly|monthly|diagnosis|interim|final|briefing|benchmark|insight
  [--register auto|external|internal]   # 거버닝 문체 기준. auto는 다수 문체를 기준으로 삼음
  [--family innergen_lecture]    # 생략 시 design_profile_v17.json의 family
  [--strict]                     # WARN도 실패로 처리
  [--json out.json]
```

`--deck-type`을 생략하면 `design_spec.md`의 `deck_type:` 값을 읽고, 없으면 유형 의존 검사(필수 레이아웃·마무리 세트)를 건너뛴다.

## 3. 검사 코드

수준: **ERROR**(균일성 위반, 반드시 수정) · **WARN**(규칙 이탈 가능성, 확인 후 수정 또는 사유 기록) · **INFO**(권장 사항).

계열은 `design_profile_v17.json`의 family와 제목 위치로 자동 판별한다: `innergen_lecture`(v22 컴팩트) · `innergen_lecture_v20`(거버닝 2줄 구형) · `innergen_business`(960×540) · `innercarry`(1024×768). `--family`로 강제할 수 있다.

### C. 화면 고정 요소 (v17·v22 좌표, 계열별 `families.<id>`)

| 코드 | 검사 | 수준 |
|---|---|---|
| C01 | 계열 고정 요소(`atoms`: 상단 선·왼쪽 바·거버닝 밑선·푸터 선·로고) 존재 | ERROR |
| C02 | 계열 제목 위치·크기 존재, 색·볼드 | ERROR / WARN |
| C03 | 거버닝 박스(교육 계열만), 거버닝 색·굵기 | ERROR / WARN |
| C04 | 출처 줄: 근거·표·차트 레이아웃에 존재, `출처:`로 시작, 계열 기준선·크기 | WARN |
| C05 | 페이지 번호 위치 = 계열 기준, 번호 = 실제 순번, 푸터·섹션 라벨 한 종류 | ERROR / WARN |
| C06 | 계열 `min_px` 미만 글자(컴팩트: 본문 12px·회사소개/이너캐리 10.67px, 푸터 별도) | WARN |
| C07 | `spec_lock.md`에 없는 색 사용 | WARN |
| C08 | 허용 가족(Pretendard·IBM Plex Sans KR·NanumSquare·Noto Sans·Malgun Gothic) 밖의 글꼴 | ERROR |

표지·맺음·목차·장 구분(`exempt_layout_keywords`)은 C 검사에서 제외한다.

### G. 거버닝 (v11·v20)

| 코드 | 검사 | 수준 |
|---|---|---|
| G01 | 본문 장표에 거버닝 없음 | ERROR |
| G02 | 거버닝이 제목을 반복(유사도 0.9↑) | ERROR |
| G03 | 다른 장표와 같은 거버닝 | ERROR |
| G04 | 계열 `max_lines`(v22: 1줄) 초과(ERROR), 한 줄이 거버닝 영역 폭 초과(WARN) | ERROR / WARN |
| G05 | 문체가 덱 기준과 다름(완결 문장체 ↔ 개조식), 명사 끝맺음 | WARN |
| G06 | 지시어 시작(이는·이를 통해·또한…), 행동 없는 구호, 질문형 | WARN |
| G07 | 수치 없음 | INFO |
| G08 | 12자 미만(명사구) | WARN |

### T. 제목 (v4·v5·v20)

| 코드 | 검사 | 수준 |
|---|---|---|
| T01 | 번호를 뺀 제목 6–34자 | WARN |
| T02 | 제목이 문장으로 끝남(~다/~요/~함/?) | WARN |
| T03 | 장 번호가 일부 장표에만 있음 | WARN |
| T04 | 같은 제목 3장 이상 반복인데 `(n/N)` 없음 | WARN |

### O. 목차 (v5·v20)

| 코드 | 검사 | 수준 |
|---|---|---|
| O01 | 목차 항목에 대응하는 본문 제목·장 구분 없음, 목차 자체가 없음(교육·착수·최종·세미나·리포트) | WARN |
| O02 | 목차 쪽 범위가 순서·총 장수와 맞지 않음 | WARN |

### S. 구조 (v18·v20)

| 코드 | 검사 | 수준 |
|---|---|---|
| S01 | 같은 레이아웃 5장 연속(INFO), 본문의 60% 초과가 한 레이아웃(WARN) | INFO / WARN |
| S02 | 덱 유형별 마무리 세트가 마지막 3장에 없음 | WARN |
| S03 | 덱 유형별 필수 레이아웃 없음(예: lecture = 목차 + 요구사항/사례 + 자가진단/핵심 정리) | WARN |
| S04 | 결론 박스·다음 행동이 거버닝과 거의 같음 | WARN |

## 4. 자동 검사가 못 보는 것 — 렌더 리뷰 6항

스크립트는 SVG 좌표와 글자 폭 추정으로 판단한다. PowerPoint 렌더(`verify_deck.py`의 contact sheet 또는 PowerPoint 내보내기 PNG)를 열어 다음을 사람이 확인한다.

1. 제목·거버닝·출처·푸터가 모든 본문 장표에서 같은 자리에 있는가
2. 거버닝이 두 줄 이내이고 박스 안에서 세로 가운데인가
3. 칸 글자가 넘치거나 잘리지 않는가(표·카드·배지)
4. 강조는 장표당 한 곳인가
5. 같은 질문의 장표가 같은 구조·색·위치인가
6. 사례·예시 수치에 `예시` 표기가 있는가

## 5. 흔한 결과와 처리

| 결과 | 처리 |
|---|---|
| G04 한 줄 초과 | 수식어·괄호를 빼고 주어+판단+수치만 남긴다. 한 줄이 안 되면 범위를 제목으로 옮긴다(v22: 두 줄 금지) |
| G05 문체 혼재 | 외부 덱은 전부 `~합니다`, 내부 진행 덱은 전부 개조식. 약속 문장만 `~할 예정입니다` 허용 |
| G02 제목 반복 | 거버닝을 "그래서 무엇"으로 바꾼다. 제목은 주제, 거버닝은 판단 |
| C06 글자 하한 | 컴팩트 계열은 칸 12px·배지 10.67px, v20 교육 계열은 16px/14px. 템플릿 값을 유지 |
| C05 페이지 번호 불일치 | 장표 삽입·삭제 뒤 `PAGE_NUM`을 다시 매긴다. 목차 쪽 범위(O02)도 함께 |
| S02 마무리 세트 없음 | lecture는 `s23`/`s20`/`03b(Q&A)`, final은 `s13`+`s05`, kickoff·weekly는 `s12`+결정 요청 |
| C07 spec_lock 밖 색 | 차트·캡처용 색은 `spec_lock.md ## colors`에 먼저 등록한다 |

## 6. 규칙표 수정

`qaqc-v21.json`을 고치면 스크립트는 바로 반영한다. 새 계열은 `families`에 좌표·크기를 추가한다(현재 `innergen_lecture`만 정의, 다른 계열은 이 값으로 대체 검사). 덱 유형별 마무리 세트·필수 레이아웃은 `structure.closing_layouts`·`required_layouts`에 `data-pptx-layout` 값으로 적는다. 거버닝 문체 어미·금지 구호·제목 번호 정규식도 같은 파일에 있다.

## 7. 적용 범위와 선후 관계

- v17 수치·v18 구조·v20 문법을 바꾸지 않는다. 그 규칙을 **검사**로 옮긴 것이다.
- `svg_quality_checker.py` 0 errors가 먼저다. 이 검사는 그 다음이며, `verify_deck.py`를 대신하지 않는다.
- 확정된 프로젝트 잠금값(`spec_lock.md`)이 규칙표와 다르면 잠금값이 우선이고, 다른 이유를 전달 메모에 적는다.
- 2026-10-14 견본 결과: 구조화 장표 견본(23장, final, v20 계열) ERROR 0 · 교육형 견본(15장, lecture) v20 계열 ERROR 0 · 회사소개 계열 15장 ERROR 0 · 이너캐리 계열 15장 ERROR 0.

## v25 목차·필수 내용 검사 (2026-10-15)

보고 유형 × 사업 성격별 목차 골격과 꼭 들어갈 내용을 [content-requirements-v25.json](content-requirements-v25.json)으로 분리하고, `innergen_qaqc.py`가 같은 실행에서 R(보고 유형 목차·필수 내용)·B(사업 성격 필수 내용)·Q(자리표시자·잔재·금지 표현) 코드로 검사한다. 장표 계획 단계에서는 `innergen_content_check.py --outline`이 같은 표로 검사한다. 이 표가 다루는 보고 유형에서는 위 S03(필수 레이아웃)과 O01(목차 없음)을 R01이 대신한다. 설명: [content-requirements-v25.md](content-requirements-v25.md).
