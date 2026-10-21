---
name: ppt-content-group-centering
description: Fix top-heavy text inside PowerPoint cards, KPI tiles, callout boxes and TOC pages, and empty bands at the page bottom — 상단 쏠림 / 카드 안 여백 불균형 / 텍스트 상자 상하 여백 / 목차 하단 공백 / 본문 하단 공백. Treat the number, label and description inside a background box as one content group and center that group vertically with equal top and bottom padding, keeping left alignment and inner spacing; fill the TOC zone (as a table where possible) and the content zone so no empty band is left above the source or footer line. Use while generating or reviewing any SVG/PPTX deck, and when the user says 여백이 위아래 다르다, 아래가 비었다, 하단 공백이 크다, 가운데 정렬, 목차 아래가 비었다.
---

# 콘텐츠 그룹 가운데 정렬 (상단 쏠림 · 목차 하단 공백 · 본문 하단 공백)

## 1. 문제 이름

| 이름 | 코드 | 증상 | 원인 |
|---|---|---|---|
| **상단 쏠림** (콘텐츠 그룹 수직 중앙 정렬 실패, top-heavy content block) | CB01 | 배경 상자 안 숫자·제목·설명이 위에 붙고, 마지막 줄 아래만 넓게 빈다 | 요소마다 상자 위쪽 기준으로 좌표를 잡거나 글상자를 위쪽 고정(anchor top)으로 둔다. 상자 높이가 남는 만큼 공백이 모두 아래로 간다 |
| **목차 하단 공백** (TOC bottom void) | CB02 | 목차 행이 위쪽에서 끝나고 바닥선 위가 넓게 빈다 | 템플릿의 고정 행 간격(예: 6행 기준)을 장 수가 적을 때도 그대로 쓴다 |
| **본문 하단 공백** (page bottom void) | CB03 | 본문 개체가 위쪽에서 끝나고 출처 줄(없으면 바닥선) 위가 넓게 빈다 | 글자·행·카드 크기를 작게 잡고, 남는 높이를 아래에 그대로 둔다 |

한 줄 정의: **상자 안의 내용은 한 덩어리로 보고, 그 덩어리를 상자 가운데에 둔다.** 요소마다 따로 가운데 정렬하지 않는다.

## 2. 규칙 (생성할 때 지킨다)

1. **컨테이너와 콘텐츠 그룹을 나눈다.** 배경 사각형이 컨테이너다. 그 안의 숫자·라벨·설명·아이콘이 하나의 콘텐츠 그룹이다. 상자 가장자리에 붙은 장식(위 강조선, 머리띠, 왼쪽 막대, 모서리 태그, 테두리)은 그룹에서 뺀다.
2. **보이는 글자 높이로 잰다.** 글상자 높이가 아니라 글리프 높이로 계산한다. 한 줄의 보이는 범위는 다음과 같다(IBM Plex Sans KR · Pretendard · 맑은 고딕 실측).
   - 한글이 있는 줄: `기준선 − 0.78 × 글자크기` ~ `기준선 + 0.12 × 글자크기`
   - 숫자·대문자만 있는 줄: `기준선 − 0.72 × 글자크기` ~ `기준선 + 0.02 × 글자크기`
3. **그룹 전체를 한 번에 옮긴다.**
   - `그룹 높이 = 마지막 줄 아래 − 첫 줄 위`
   - `목표 위치 = 상자 위 + (상자 높이 − 그룹 높이) / 2`
   - `이동량 = 목표 위치 − 현재 첫 줄 위`
   - 모든 요소의 y에 같은 이동량을 더한다. x 좌표, 요소 사이 간격, 왼쪽 정렬은 바꾸지 않는다.
4. **머리 영역이 있는 카드**(제목 + 구분선 1개 + 본문)는 제목을 위에 둔다. 구분선 아래 본문만 `구분선 ~ 상자 아래` 범위의 가운데에 둔다. 구분선이 둘 이상이면 행 구분선이므로, 목록 전체(구분선 포함)를 한 덩어리로 옮긴다.
5. **허용 오차**: |위 여백 − 아래 여백| ≤ max(6px, 상자 높이의 12%). 위·아래 모두 최소 안전 여백(작은 카드 12px, 일반 카드 16px) 이상이어야 한다.
6. **넘칠 때**: 글자를 줄이기 전에 줄바꿈 → 요소 간격 → 상자 높이 순서로 조정한다. 최소 글자 크기는 지킨다. 해결이 안 되면 억지로 넣지 말고 원인과 대안(상자 키우기, 문구 줄이기)을 보고한다.
7. **목차는 영역을 채운다.**
   - `행 간격 = (목차 영역 아래 − 첫 행 위) / 장 수`로 행을 고르게 나눈다.
   - 마지막 행 아래부터 바닥선(꼬리말 선)까지는 페이지 높이의 10% 이하로 남긴다.
   - 행이 너무 높아 보이면 빈 공간을 남기지 말고 행 안에 정보를 더한다. 예: 장마다 쪽별 세부 줄, 설명 2줄, 쪽 범위 강조.
   - 구조화(structured) 템플릿에서는 장 수에 맞는 목차 레이아웃 변형(예: `…-toc-pages-4`)을 쓰거나 새 레이아웃 키를 등록한다. 같은 레이아웃 키에서 자리 경계만 바꾸면 계약 오류가 난다.
   - 목차는 가능하면 **표**(장 · 제목/내용 · 쪽)로 만든다. 셀은 세로 가운데 정렬(`valign: ctr`)이고 행 높이가 영역을 나눠 갖는다. SVG 경로에서는 `data-pptx-native="table"` 표지를 달고 `--native-objects`로 내보낸다.
8. **본문은 영역 바닥까지 쓴다.** 본문 페이지의 마지막 개체 아래부터 출처 줄(없으면 바닥선)까지는 페이지 높이의 6% 이하로 남긴다.
   - 순서: 본문 글자 한 단계 키우기(최소 크기 이상) → 행·카드·이미지 높이 늘리기 → 마지막에 맺음 메시지 띠(한 줄 요약 개체) 추가.
   - 개체 하나를 더 넣을 만큼 남지 않으면 새 개체를 만들지 말고 위 두 단계로 채운다.
   - 이너캐리는 출처 줄 y712, 바닥선 y728, 쪽 번호 y752, 본문 영역 y156–696이다(2026-10-21 변경). 다른 유형도 각 유형의 본문 영역 바닥까지 쓴다.
9. **짧은 라벨은 도형 안에 직접 쓴다.** 알약 태그, 머리띠 제목, 번호 배지, 한 줄 메시지 띠처럼 줄바꿈·넘침 위험이 없는 글자는 별도 글상자로 겹쳐 두지 않고 그 도형의 텍스트로 넣는다(PowerPoint에서 도형을 클릭해 바로 고칠 수 있고, 글상자가 도형 밖으로 삐져나오지 않는다).
   - SVG 경로: `<g data-pptx-text-shape="ctr">` 안에 `rect`(또는 `circle`·`ellipse`) 하나와 `text` 하나만 둔다. 내보낼 때 한 도형으로 합쳐지고, 글자 x 위치가 좌우 안쪽 여백, `ctr`이 세로 가운데 정렬이 된다(`t`·`b`도 가능).
   - 여러 줄 본문, 숫자+라벨+설명처럼 여러 요소가 한 카드에 들어가는 경우, 글이 길어 줄바꿈될 수 있는 경우는 지금처럼 별도 글상자로 두고 2번·3번 규칙(그룹 가운데 정렬)을 따른다.
10. **침범 금지**: 도형 안 글자·알약이 배경 칸 경계를 넘거나 닿지 않게 한다. 칸 높이는 고정값이 아니라 안에 들어갈 줄 수로 계산한다(`줄 수 × 줄 높이 + (줄 수 − 1) × 간격 + 위아래 여백`). 남는 높이는 칸끼리 나눠 갖는다.
11. **편집 가능성 유지**: 텍스트를 그림으로 만들지 않는다. 글꼴·상자 폭·마스터는 바꾸지 않는다.

## 3. 이 저장소(PPT Master)에서의 실행

SVG를 쓴 뒤, PPTX로 내보내기 전에 실행한다.

```bash
python .claude/skills/ppt-master/scripts/content_balance_check.py <project_path>        # 보고만
python .claude/skills/ppt-master/scripts/content_balance_check.py <project_path> --fix  # CB01 자동 보정
```

- `--fix`는 상단 쏠림으로 판정된 그룹을 한 번에 같은 양만큼 아래로 옮긴다.
- 다음 경우는 보고만 한다.
  - 구조화 템플릿의 자리(placeholder) 글자: 템플릿과 자리 경계에서 고친다.
  - 경로(path)나 변형(transform)이 들어간 그룹: 직접 옮긴다.
  - 목차 하단 공백(CB02): 위 7번 규칙대로 행을 다시 나눈다.
  - 본문 하단 공백(CB03): 위 8번 규칙대로 글자·행 높이를 키우거나 맺음 메시지 띠를 넣는다.
- 보정한 뒤에는 렌더 이미지를 다시 보고 확인한다. `verify_deck.py`가 이 검사를 경고로 다시 실행한다.
- 저장소 밖(스킬 ZIP)에서는 같은 검사기가 `scripts/content_balance_check.py`에 들어 있다. SVG 폴더나 SVG 파일 경로를 넘긴다.

## 4. 이미 만들어진 PPTX를 고칠 때

- `scripts/list_pptx_shapes.py <file.pptx>`: 도형 이름과 좌표를 나열한다.
- `scripts/center_pptx_cards.py --input <file.pptx> --config <cards.json>`: 기본은 시뮬레이션(dry run)이다. `--apply`를 붙여야 별도 파일 `<이름>_centered.pptx`를 만든다. 매핑 예시는 `assets/cards.example.json`이다.
- 이 도구는 도형 경계로 계산하고 글리프 높이로는 재지 않는다. 결과는 반드시 렌더해서 눈으로 확인한다.

## 5. 결과 보고

다음 네 가지를 나눠 적는다. 렌더 확인을 못 했으면 "검증 미수행"이라고 쓴다.

- 상단 쏠림 보정 수
- 남은 항목과 그 이유
- 목차 하단 공백 · 본문 하단 공백 여부
- 렌더 확인 여부

계산식·예외·체크리스트: [`references/GEOMETRY_AND_QA.md`](references/GEOMETRY_AND_QA.md)
엔진별 구현(SVG · python-pptx · PptxGenJS · VBA): [`references/IMPLEMENTATION_GUIDE.md`](references/IMPLEMENTATION_GUIDE.md)
다른 도구에 붙여 넣을 지침(ChatGPT · Claude 채팅 · Cowork): [`platforms/`](platforms/)
