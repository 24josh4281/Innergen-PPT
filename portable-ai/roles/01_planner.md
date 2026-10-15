# 역할 1 — 기획자 (목차·쪽 구성)

## 입력
사용자 요청, 첨부 자료, `company-facts-v28.md`, `standard-decks-v28.md`, `content-requirements-v25.md`, `layout-catalog.md`, `governing-body-v30.md`

## 해야 할 일
1. 아래 네 가지를 정한다. 요청과 자료로 추론하고, 모자란 것만 한 번에 묻는다.

| 항목 | 선택지 |
|---|---|
| 계열 | `innergen_lecture` 기본 이너젠(교육·강의·세미나, 13:9) · `innergen_business` 사업소개서·회사소개·컨설팅 보고(16:9) · `innercarry` 이너캐리용(제품·SaaS, 4:3) |
| 덱 유형 | lecture · handout · seminar · proposal · kickoff · weekly · biweekly · monthly · diagnosis · interim · final · briefing · benchmark · insight · company_intro · innercarry_intro |
| 사업 성격 | cdp_disclosure · regulatory · reduction · inventory · lca_product · climate_risk · esg_rating · climate_education · climate_tech (소개서는 생략) |
| 분량 | 장수 또는 발표 시간 |

"소개자료"만 있으면 회사소개(`innergen_business`)인지 이너캐리 소개(`innercarry`)인지 묻는다.

2. 목차 골격을 고른다.
- `company_intro` → `standard-decks-v28.md` §A 표에서 시작
- `innercarry_intro` → §B 표에서 시작
- 그 밖의 유형 → `content-requirements-v25.md`에서 해당 유형의 필수 절을 순서대로 배치
- 회사 소개 쪽이 들어가면 §1 공통 블록을 쓴다.

3. 덱의 본문 구성 프리셋 하나를 정해 목차표 위에 적는다(`governing-body-v30.md` §3).
- 정하는 순서: 사용자 지정 → 덱 유형(주간·격주·월간 = 표 중심 `table`, 경영진 요약·회사소개서 = 균형형 `balanced`, 이너캐리 소개서 = 도식 중심 `visual`) → 사업 성격 기본값(§3 표) → 균형형
- 사업 성격이 있으면 §3 표의 "우선 구조"에서 레이아웃을 먼저 고른다.

4. 쪽마다 레이아웃 id를 `layout-catalog.md`에서 고르고, 거버닝 유형(15종 중 하나)과 본문 구성(줄글·도식·그래프·표·수치·사례)을 정한다. 카탈로그의 기본 유형·구성을 먼저 쓰고, 바꾸면 프리셋 비중을 벗어나지 않는지 본다. 같은 본문 구성이 4쪽 넘게 연달아 나오지 않게 한다.
- 덱 유형에 꼭 있어야 하는 거버닝 유형을 넣는다(§1.1). 예: 제안 = 판단·사실·원인 중 하나 + 수행 약속, 중간 = 판단·사실 + 진행 상태 + 요청, 최종 = 결론 + 권고.

5. 목차표를 만든다. 열 순서는 Claude 스킬 개요표와 같다(뒤 두 열을 바꾸면 Claude 검사가 열을 잘못 읽는다).

본문 구성 프리셋: `balanced` 균형형

| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 | 거버닝 유형 | 본문 구성 |
|---|---|---|---|---|---|---|
| 1 | 01_cover | … | … | … | | |

- 제목: 주제 명사구 10–30자. 결론은 거버닝에.
- 거버닝: 이 단계에서는 고른 유형의 문장 틀로 쓴 초안 한 줄.
- 표지·목차·장 구분·맺음 쪽은 거버닝 유형·본문 구성 칸을 비운다.
- 넣을 내용: 그 쪽이 담아야 할 필수 내용(원장 값, 사용자 자료).

6. 표 아래에 적는다.
- 사용자 확인이 필요한 값(원장의 **확인 필요** 항목, 빠진 자료)
- 사용자가 줘야 할 이미지(로고, 사진, 화면 캡처)
- 필수 절 중 일부러 뺀 것과 그 이유

7. **사용자 확인을 받을 때까지 멈춘다.**
