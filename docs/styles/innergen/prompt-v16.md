# 재사용 요청문 v16 — 이너젠·이너캐리 장표

아래 요청문을 Claude Code 또는 Codex에 그대로 붙여 넣고 `[ ]`만 바꾼다. 선택 기준은 [프로필 매트릭스 v16](innergen-profile-matrix-v16.md), 차트·출처 규칙은 [근거·차트 규칙 v16](innergen-evidence-charts-v16.md)에 있다.

```text
[자료 경로 또는 주제]로 장표를 만들어줘.
- 스타일: [이너젠 보고서 | 이너젠 소개자료 | 이너캐리]
- 업무 성격: [CDP·기후공시 | 규제 대응 | 감축사업·상쇄 | 인벤토리 | LCA·제품탄소 | 기후리스크 | ESG 평가 대응 | 기후·ESG 교육 | 기후테크·소셜벤처]
- 보고 단계: [제안 | 착수 | 중간 | 최종 | 교육·워크숍 | 경영진 브리핑]
- 전달 방식: [발표형 | 교육형(강의) | 교육형(배포 교재) | 제안형 | 보고형(읽기용)]
- 청중·시간: [예: 대학생 60명, 90분]
- 고객·행사 로고: [경로 또는 없음]
docs/styles/innergen/innergen-profile-matrix-v16.md와 innergen-evidence-charts-v16.md 기준으로
업무별 필수 장표를 넣고, 수치는 1차 기관 자료로 최신값을 확인해 출처(기관·자료명·발간연월·기준연도·단위)를 달아줘.
목차·장 구분·거버닝·본문 배치는 docs/styles/innergen/content-architecture-v20.md의 덱 유형 골격을 따라줘.
차트와 표는 편집 가능하게 만들고, 확인하지 못한 수치는 따로 알려줘.
완성 뒤 scripts/innergen_qaqc.py --deck-type [유형]으로 점검해 ERROR 0을 확인하고 남은 WARN을 알려줘.
```

## 짧은 예

| 요청 | 선택 결과 |
|---|---|
| "이너젠 소개자료 스타일로 기후공시 사내 교육 40장" | 이너젠 소개자료 · `cdp_disclosure` · `education` · 교육형(강의) · `innergen_lecture` 템플릿 |
| "A사 인벤토리 최종보고서 이너젠 스타일로" | 이너젠 보고서 · `inventory` · `final` · 보고형(읽기용) · `innergen` 템플릿(격자형 기본) |
| "K-ETS 대응 컨설팅 제안 발표 15분" | 이너젠 소개자료 · `regulatory` · `proposal` · 제안형 |
| "이너캐리 도입 제안서" | 이너캐리 · `inventory` 또는 `cdp_disclosure` · `proposal` · 제안형 · `ppt43` |
