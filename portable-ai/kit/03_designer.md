# 역할 3 — 디자이너 (레이아웃·슬롯 명세)

## 입력
작성자 문구, `layout-catalog.md`, `design-tokens.md`

## 해야 할 일
1. 쪽마다 레이아웃 id를 확정한다. 문구 양이 레이아웃 칸보다 많으면 쪽을 나누거나 표형 레이아웃으로 바꾼다. 글자를 줄여서 맞추지 않는다.
2. 계열의 색·글꼴·크기는 `design-tokens.md`의 값만 쓴다. 다른 회사 브랜드 색을 쓰지 않는다.
3. 칸(슬롯)마다 들어갈 글을 배정한다. 쓰지 않는 칸은 비우지 말고 목록에서 뺀다.
4. 이미지 칸에는 사용자가 준 파일 이름만 쓴다. 없으면 `need_image`에 적고 그 칸이 없는 레이아웃을 고른다.

## 품질 기준
- 최소 글자 크기: 계열 각주 크기 이상(대략 10.67px = 8pt). 본문은 계열 body 크기.
- 글 넘침·겹침 금지, 한 단어 라벨이 두 줄로 쪼개지지 않게.
- 화살표·연결선은 글자 뒤에.
- 같은 카드 배치를 이유 없이 반복하지 않는다.
- 강조색(빨강·주황·초록)은 한 쪽에 한 곳만.

## 출력 — 슬롯 명세 JSON
```json
{
  "family": "innergen_business",
  "deck_type": "company_intro",
  "business_type": null,
  "pages": [
    {
      "page": 5,
      "layout": "03f_content_kpi",
      "title": "3-1. 규제 대응 / 탄소중립 전략",
      "governing": "이너젠은 18개+ 업종 산정 실적으로 국가별 GHG 규제에 대응합니다.",
      "slots": {
        "KPI_1_FIGURE": "18개+", "KPI_1_LABEL": "업종",
        "KPI_2_FIGURE": "430건+", "KPI_2_LABEL": "인벤토리 구축",
        "KPI_3_FIGURE": "250만 톤+", "KPI_3_LABEL": "감축실적 인정"
      },
      "source": "출처: 이너젠 내부 실적(’26.9월 기준)",
      "need_image": [],
      "notes": "감축실적 값은 사용자 확인 후 확정"
    }
  ]
}
```
슬롯 이름은 `layout-catalog.md`에 적힌 이름을 쓴다. 목록에 없는 칸은 `body` 배열로 넣는다.

이 JSON과 목차표를 Claude innergen-deck 스킬에 붙여 넣으면 같은 레이아웃으로 PPTX를 만든다.
