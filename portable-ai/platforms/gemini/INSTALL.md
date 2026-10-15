# 이너젠 장표 도우미 — Gemini 설치 방법

패키지: `innergen-gemini-kit.zip` (압축을 풀면 아래 구성)

| 폴더·파일 | 쓰는 곳 |
|---|---|
| `INSTRUCTIONS.md` | Gem 편집 화면의 **지침(Instructions)** 칸에 붙여 넣기 |
| `knowledge/` 9개 파일 | Gem **지식(Knowledge)** 에 추가 |
| `starters.txt` | 처음 쓸 때 복사해 쓰는 요청 예시 |
| `roles-split/` | 역할별 Gem 4개로 나눠 쓸 때만 사용 |
| `EXPECTED-OUTPUTS.md` | 결과물 예시(올리지 않아도 됨) |

공식 도움말: [Use Gems in Gemini Apps](https://support.google.com/gemini/answer/15146780?hl=en). Workspace 계정은 관리자가 Gem 기능을 꺼 두었을 수 있습니다. 화면 이름은 Google이 바꿀 수 있습니다.

## A. Gem 하나로 쓰기 (권장)

1. gemini.google.com 왼쪽 메뉴 **Gem 탐색(Explore Gems)** → **Gem 만들기(New Gem)**
2. **이름**: `이너젠 장표 도우미`
3. **지침**: `INSTRUCTIONS.md` 내용을 전부 붙입니다.
4. **지식** → 파일 추가: `knowledge/` 폴더의 9개 파일을 올립니다. 파일 수 한도에 걸리면 `knowledge/`의 `01`–`04` 역할 파일 4개 대신 패키지 맨 위의 `roles-merged.md` 1개를 올려 6개로 줄입니다.
5. 오른쪽 미리보기 창에서 `회사소개서 4장짜리 짧은 버전 만들어줘`로 시험해 목차표가 나오고 확인을 기다리는지 봅니다.
6. **저장**. 공유하면 받는 사람도 지식 파일 내용을 보게 되니 회사 내부 범위에서만 공유합니다.

## B. 역할별 Gem 4개로 쓰기 (선택)

`roles-split/`의 `01`–`04` 파일을 Gem마다 지침에 넣고, 지식에는 공통 5개 파일(`design-tokens.md`, `layout-catalog.md`, `company-facts-v28.md`, `standard-decks-v28.md`, `content-requirements-v25.md`)을 똑같이 올립니다. 앞 Gem의 결과를 다음 Gem 대화에 붙여 넣는 방식입니다.

## Gemini에서 알아 둘 점

- Gem은 지식 파일을 매번 전부 읽지 않을 수 있습니다. 회사 숫자가 원장과 다르게 나오면 "company-facts-v28.md 값으로 다시 확인해줘"라고 요청합니다.
- Google Docs·Slides로 내보내기는 되지만 이너젠 템플릿 디자인은 적용되지 않습니다. 디자인이 들어간 PPTX는 Claude 스킬에서 만듭니다.

## 업데이트

회사 정보·표준 목차가 바뀌면 Gem 편집 화면에서 기존 지식 파일을 지우고 새 패키지의 `knowledge/` 파일을 다시 올립니다.
