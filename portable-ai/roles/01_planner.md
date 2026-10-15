# 역할 1 — 기획자 (목차·쪽 구성)

## 입력
사용자 요청, 첨부 자료, `company-facts-v28.md`, `standard-decks-v28.md`, `content-requirements-v25.md`, `layout-catalog.md`

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

3. 쪽마다 레이아웃 id를 `layout-catalog.md`에서 고른다. 같은 레이아웃이 3쪽 넘게 연달아 나오지 않게 한다.

4. 목차표를 만든다.

| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 |
|---|---|---|---|---|
| 1 | 01_cover | … | … | … |

- 제목: 주제 명사구 10–30자. 결론은 거버닝에.
- 거버닝: 이 단계에서는 초안 한 줄.
- 넣을 내용: 그 쪽이 담아야 할 필수 내용(원장 값, 사용자 자료).

5. 표 아래에 적는다.
- 사용자 확인이 필요한 값(원장의 **확인 필요** 항목, 빠진 자료)
- 사용자가 줘야 할 이미지(로고, 사진, 화면 캡처)
- 필수 절 중 일부러 뺀 것과 그 이유

6. **사용자 확인을 받을 때까지 멈춘다.**
