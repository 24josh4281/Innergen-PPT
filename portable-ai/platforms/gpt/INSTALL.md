# 이너젠 장표 도우미 — ChatGPT 설치 방법

패키지: `innergen-gpt-kit.zip` (압축을 풀면 아래 구성)

| 폴더·파일 | 쓰는 곳 |
|---|---|
| `INSTRUCTIONS.md` | GPT 편집 화면의 **Instructions** 칸에 붙여 넣기 (약 1,600자, 8,000자 한도 안) |
| `knowledge/` 9개 파일 | **Knowledge** 에 업로드 |
| `starters.txt` | **Conversation starters** 칸에 한 줄씩 |
| `roles-split/` | 역할별 GPT 4개로 나눠 쓸 때만 사용 |
| `EXPECTED-OUTPUTS.md` | 결과물 예시(올리지 않아도 됨) |

## A. GPT 하나로 쓰기 (권장)

맞춤형 GPT를 만들려면 유료 요금제(Plus·Team·Enterprise 등)가 필요합니다. 화면 이름은 OpenAI가 바꿀 수 있습니다.

1. ChatGPT 왼쪽 메뉴 **GPT** → **만들기(+ Create)** → 위쪽 **구성(Configure)** 탭을 엽니다.
2. **이름**: `이너젠 장표 도우미` · **설명**: `이너젠·이너캐리 스타일 장표의 목차·문구·슬롯 명세·검수표를 만듭니다`
3. **Instructions**: `INSTRUCTIONS.md` 내용을 전부 복사해 붙입니다.
4. **Conversation starters**: `starters.txt`의 네 줄을 하나씩 넣습니다.
5. **Knowledge** → **파일 업로드**: `knowledge/` 폴더의 9개 파일을 모두 올립니다.
6. **기능(Capabilities)**: 웹 검색은 끄기를 권장합니다(회사 숫자는 원장에서만 가져오게 하려는 목적). 캔버스는 켜 두면 긴 문구를 고치기 편합니다. 코드 인터프리터는 꺼도 됩니다.
7. 오른쪽 위 **만들기/업데이트** → 공유 범위는 **나만 보기** 또는 **링크가 있는 사용자**를 고릅니다. 회사 내부 정보가 들어 있으니 **GPT 스토어 공개는 하지 않습니다.**
8. 시험: 대화창에 `회사소개서 4장짜리 짧은 버전 만들어줘`를 입력해 1단계 목차표가 나오고 확인을 기다리는지 봅니다.

## B. ChatGPT 프로젝트로 쓰기 (팀 공유가 쉬움)

1. 왼쪽 메뉴 **프로젝트** → **새 프로젝트** `이너젠 장표`
2. 프로젝트 **지침(Instructions)** 에 `INSTRUCTIONS.md`를 붙입니다.
3. 프로젝트 **파일**에 `knowledge/` 9개를 올립니다.
4. 원본 PPT나 보고서 자료는 대화마다 첨부합니다.

## C. 역할별 GPT 4개로 쓰기 (선택)

`roles-split/`의 파일을 GPT마다 Instructions에 넣고, Knowledge는 4개 GPT 모두 `knowledge/`의 공통 파일 5개(`design-tokens.md`, `layout-catalog.md`, `company-facts-v28.md`, `standard-decks-v28.md`, `content-requirements-v25.md`)를 똑같이 올립니다.

| GPT 이름 | Instructions | 넘겨줄 것 |
|---|---|---|
| 이너젠 기획자 | `01_planner.md` | 확정 목차표 → 작성자 |
| 이너젠 작성자 | `02_writer.md` | 쪽별 문구 → 디자이너 |
| 이너젠 디자이너 | `03_designer.md` | 슬롯 명세 JSON → Claude 또는 검수자 |
| 이너젠 검수자 | `04_qa.md` | 검사표 |

앞 단계 결과를 다음 GPT 대화창에 붙여 넣는 방식입니다.

## 업데이트

회사 정보·표준 목차가 바뀌면 새 패키지의 `knowledge/` 파일로 바꿔 올립니다(같은 이름 파일은 지우고 다시 업로드).
