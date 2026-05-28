# 한큐 PPT 생성을 위한 구조화 및 QA 규칙

작성일: 2026-05-22

## 목적

사용자가 자료를 한 번 넣었을 때 바로 원하는 수준에 가까운 이너젠 스타일 컨설팅 PPT가 나오도록 입력 구조, 장표 구조화, QA 규칙을 고정한다.

## 핵심 원칙

한큐 생성 품질은 생성 모델보다 입력과 검증 구조에 더 크게 좌우된다. 따라서 다음 3가지를 동시에 고정한다.

1. 입력 브리프: 문서 유형, 대상, 의사결정, 반드시 보존할 수치/원문을 명확히 입력한다.
2. 구조화 규칙: 각 슬라이드는 하나의 역할과 하나의 governing message를 가진다.
3. QA 게이트: Storyboard 단계와 PPTX 렌더링 단계에서 각각 통과해야 한다.

## 한큐 입력 브리프

```text
# 한큐 PPT 생성 브리프

## 1. 기본 조건
문서 유형:
대상 독자:
목표:
톤:

## 2. 반드시 유지할 원문/수치
- 수치, 단위, 기준연도, 기간, 기관명
- 출처 또는 원문 유지가 필요한 문장
- 미확인/가정/추정으로 남겨야 하는 내용

## 3. 슬라이드별 내용
슬라이드 1: 제목
핵심 메시지:
근거/내용:
-
-
-
원하는 구조:

---
슬라이드 2: 제목
핵심 메시지:
근거/내용:
-
-
-
원하는 구조:

## 4. 디자인/품질 요구
- 제목과 governing message 분리
- 한 슬라이드 bullet 최대 5개
- 박스 안 긴 문장은 bullet로 분리
- 한글 단어 글자 단위 줄바꿈 금지
- 최소 폰트 11pt 이상
- 이너젠 BI 색상 유지
```

## 문서 유형별 구조화

| 문서 유형 | 권장 흐름 | 핵심 구조 |
| --- | --- | --- |
| 컨설팅 제안서 | Why → Value → Scope → Methodology → Deliverables → Team/Governance → Schedule → Next step | Why/What/How, 3 Reasons, Integrated Scope, Method Chevron, Work Scope Table |
| 착수보고 | Objective → Scope alignment → Workplan → Data request → R&R → Risk/Issue → Communication | Executive Summary, Integrated Scope, Data Request Tracker, Team/Governance |
| 중간보고 | Progress snapshot → Key findings → Issues → Decision required → Next actions | KPI Dashboard, Traffic-Light, Issue Tree, Evidence to Action |
| 최종보고 | Executive conclusion → Evidence → Before/After → Implications → Roadmap → Operating model | Executive Summary, Impact Factoid, Before/After, As-Is/To-Be Gap |
| 교육자료 | Learning objective → Concept → Case → Practice → Checklist → Q&A | Training Curriculum, Case Study, Evidence Grid |

## QA Gate

| Gate | 규칙 | 실패 시 증상 |
| --- | --- | --- |
| Input | 문서 유형, 독자, 목표 의사결정, 보존 수치가 있어야 한다. | 예쁜 요약 PPT처럼 보인다. |
| Story | 각 슬라이드는 제목과 governing message를 분리한다. | 주장이 약하고 본문처럼 보인다. |
| Structure | 각 슬라이드는 문제, 근거, 비교, 방법론, 산출물, 의사결정 중 하나의 역할을 가진다. | 카드형 장표만 반복된다. |
| Layout | 내용 성격에 맞는 구조를 선택한다. 절차는 process, 선택지는 matrix, 변화는 before/after, 이슈는 issue tree. | 모든 내용이 bullet/card로만 나열된다. |
| Density | 본문 bullet은 최대 5개, 박스 안 긴 문장은 bullet로 분리한다. | 작은 글씨, 넘침, 비어 보이는 장표가 생긴다. |
| Korean readability | 짧은 한글 단어와 L1/L2 라벨은 한 줄 유지한다. | 글자 단위 줄바꿈으로 전문성이 떨어진다. |
| Brand | 이너젠 navy/sky/white, Malgun Gothic, 11pt 이상을 유지한다. | 레퍼런스와 색감/폰트가 어긋난다. |
| Render QA | PPTX XML QA와 PowerPoint 렌더링 QA를 통과한다. | 실제 PowerPoint에서 깨질 수 있다. |

## 앱 반영 사항

- `src/oneShotQuality.ts`: 한큐 입력 템플릿, 구조화 규칙, QA gate, 준비도 점수.
- `src/qa.ts`: Storyboard QA에 한큐 준비도 점수와 개선 action 연결.
- `src/main.ts`: 한큐 입력 버튼, 한큐 생성 구조화 규칙 패널, QA summary 반영.

## 운영 방식

1. 사용자는 업무 시나리오를 고른다.
2. 한큐 입력 템플릿에 맞춰 내용을 넣는다.
3. Storyboard QA에서 한큐 준비도 점수와 경고를 확인한다.
4. 경고가 있으면 생성 전 수정한다.
5. PPTX 생성 후 렌더링 QA를 통과한 파일만 최종 사용한다.

## Visual Density And Alignment QA Addendum

- Table cells must not look empty. If a body cell has only one or two short lines inside a tall row, lower row height, increase font size to 12.5-14pt, or add a judgment/evidence/meaning/status column.
- A table row should read as a designed row, not as text floating inside a large box. Body rows need consistent vertical rhythm and compact internal padding.
- Numbered process rows must reserve a fixed number column. The number and body text must share the same rowY/rowH and use vertical middle alignment.
- If long text wraps, the row height must be increased before export. Do not let the number stay centered while the body text wraps from a different top position.
- Badges, chips, and small labels must place the text box on the exact same y/h as the shape and use `valign=middle`.
- Boundary, scenario, and before/after slides should use dense row structures with aligned dividers, not loosely placed text boxes.
- `alignmentRiskCount` must be zero. If it is non-zero, regenerate the slide with fixed number columns, shared rowY/rowH, and middle-aligned labels/chips.
- Render QA must also write `issues[]`. Each issue must include the failed slide number, object id/name, coordinates (`x/y/w/h`), related object coordinates when applicable, reason, and remediation.
- If `issues[]` is non-empty, the deck is not final. Use the issue coordinates to adjust the exact object instead of guessing from the whole slide.
- Use the approved reference samples as the balance target: table body 12-14pt, compact rows 0.55-0.95in, narrow category/status columns, and a wider evidence/content column.
