# 엔진별 구현

## 1. 공통 절차

```text
container = 배경 상자 (가장자리 장식 제외, 머리띠가 있으면 그 아래부터)
items     = 콘텐츠 요소의 "보이는" 범위 (글상자 범위 아님)
items     = 줄바꿈·요소 간격을 먼저 확정
block     = union(items)
if block.height > container.height − padTop − padBottom: 넘침 → 보고
shiftY    = container.top + (container.height − block.height)/2 − block.top
items.y  += shiftY        # 모두 같은 값
렌더 → 눈 검수
```

## 2. SVG 작성 (PPT Master Executor)

카드를 그릴 때 첫 줄 기준선을 아래처럼 계산한다. 위쪽 고정값(예: 상자 위 + 30px)을 쓰지 않는다.

```text
lines   = [(글자크기 s_i, 줄간격 lh_i)]       # 위에서 아래 순서
ink_top = 0.78·s_1                             # 첫 줄 기준선 위로 보이는 높이
height  = ink_top + Σ(lh_i, i≥2) + 0.12·s_n    # 그룹의 보이는 높이
first_baseline = box_top + (box_h − height)/2 + ink_top
```

예: 상자 y=156, h=132. 줄은 숫자 37.33px, 라벨 16px(+32), 설명 13.33px(+26)이다.

- ink_top = 29.1
- height = 29.1 + 32 + 26 + 1.6 = 88.7
- first_baseline = 156 + (132 − 88.7)/2 + 29.1 = 206.75

쓴 뒤에는 `content_balance_check.py`로 확인한다.

## 3. python-pptx

- 글상자 높이를 글자에 맞게 정한다: `word_wrap` 확정 → 줄 수 × 줄간격.
- 상자마다 `vertical_anchor = MIDDLE`만 거는 것으로는 그룹 정렬이 되지 않는다. 글상자가 둘 이상이면 효과가 없다.
- 하나의 글상자에 숫자와 설명을 두 단락으로 넣었다면, 그 글상자를 배경과 같은 크기로 두고 `MSO_ANCHOR.MIDDLE`을 쓰면 된다. 단락 간격으로 요소 사이를 조절한다.

## 4. PptxGenJS

`addText` 때 `margin: 0`을 주고 줄 수에 맞춰 `h`를 계산한다. 생성 후 그룹 전체의 y에 같은 delta를 더한다. 한 글상자에 여러 단락을 넣는 경우는 `valign: "middle"`과 배경 크기의 글상자를 쓴다.

## 5. PowerPoint VBA / COM

콘텐츠만 그룹으로 묶고 배경은 그룹에 넣지 않는다.

```vb
grp.Top = bg.Top + (bg.Height - grp.Height) / 2
```

## 6. 기존 PPTX 보정 도구

```bash
pip install python-pptx
python scripts/list_pptx_shapes.py 기존.pptx --slide 3
python scripts/center_pptx_cards.py --input 기존.pptx --config cards.json             # 시뮬레이션
python scripts/center_pptx_cards.py --input 기존.pptx --config cards.json --apply     # 기존_centered.pptx
```

- 지정한 슬라이드·도형 이름만 옮긴다. 원본은 덮어쓰지 않는다.
- 도형 경계로 계산한다. 글상자가 글자보다 크면 결과가 눈에 덜 맞을 수 있다. 렌더 확인이 필수다.
- 이름 규칙 예: `SL03_KPI01_BG`, `SL03_KPI01_VALUE`, `SL03_KPI01_DESC`.

## 7. 결과 보고 형식

| 쪽 · 상자 | 처리 | 위 여백 | 아래 여백 | 안전 여백 | 렌더 확인 |
|---|---|---|---|---|---|
| 3 / KPI01 | 보정 | 23px | 23px | 통과 | 완료 |
