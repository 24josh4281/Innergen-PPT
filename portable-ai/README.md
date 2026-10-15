# 이너젠 장표 도우미 — GPT·Gemini 호환판 (역할별)

Claude innergen-deck 스킬과 같은 규칙(목차·필수 내용·회사 기본 정보·디자인 토큰·레이아웃 칸)을
ChatGPT와 Gemini에서도 쓰도록 역할별 지침으로 나눈 묶음이다. 파일은 `kit/` 한 폴더에 있다.

## 역할 구성

| 파일 | 역할 | 하는 일 | 결과물 |
|---|---|---|---|
| `00_orchestrator.md` | 진행자 | 네 역할을 순서대로 돌리고 목차 확인에서 멈춤 | — |
| `01_planner.md` | 기획자 | 계열·덱 유형 확정, 쪽별 목차표 | `| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 |` |
| `02_writer.md` | 작성자 | 제목·거버닝 한 줄·본문·출처 | 쪽별 문구 |
| `03_designer.md` | 디자이너 | 레이아웃 칸 배정, 색·크기 토큰 | 슬롯 명세 JSON |
| `04_qa.md` | 검수자 | Claude 자동 검사와 같은 코드로 점검 | 검사표(PASS/FAIL) |

공통 지식: `design-tokens.md`(계열별 색·글꼴·크기), `layout-catalog.md`(레이아웃 id와 칸 이름),
`company-facts-v28.md`(회사 기본 정보 원장), `standard-decks-v28.md`(회사소개서·이너캐리 소개서 표준 목차),
`content-requirements-v25.md`(덱 유형×사업 성격 필수 목차·내용).

## ChatGPT에서 쓰기

1. GPT 만들기(Configure) → Instructions에 `00_orchestrator.md` 내용을 붙인다.
2. Knowledge에 나머지 9개 파일을 올린다.
3. 역할을 나눠 쓰고 싶으면 GPT를 네 개 만들어 Instructions에 각 역할 파일을 넣고, 공통 지식 5개를 똑같이 올린다.
4. ChatGPT 프로젝트(Projects)를 쓰면 프로젝트 지침에 `00_orchestrator.md`, 파일에 나머지를 올린다.

## Gemini에서 쓰기

1. Gem 만들기 → 지침 칸에 `00_orchestrator.md` 내용을 붙인다.
2. 지식 파일에 나머지 9개를 올린다. 공식 도움말: [Use Gems in Gemini Apps](https://support.google.com/gemini/answer/15146780?hl=en)
3. 역할별 Gem이 필요하면 GPT와 같은 방식으로 네 개를 만든다.

업로드 개수 한도는 두 서비스가 바꿀 수 있다. 이 묶음은 지침 1개 + 지식 9개(합계 10개)로 맞췄다.
한도를 작성 시점에 공식 문서로 확인하지 못했으니, 올라가지 않으면 `01`–`04`를 한 파일로 합친다.

## 할 수 없는 것

| 항목 | Claude 스킬 | GPT·Gemini 호환판 |
|---|---|---|
| 편집 가능한 PPTX 생성 | 가능(SVG→네이티브 PPTX) | **불가.** 목차표·문구·슬롯 명세까지 |
| 자동 검사(qaqc·content_check·facts_check) | 스크립트로 실행 | 사람이 읽는 수준의 점검(같은 코드표 사용) |
| 글자 넘침·겹침 확인 | 렌더 후 확인 | PowerPoint에서 직접 확인 |
| 회사 정보 대조 | 원장 JSON과 자동 대조 | 원장 문서를 읽고 대조 |

PPTX가 필요하면: 호환판에서 확정한 목차표와 슬롯 명세 JSON을 Claude의 innergen-deck 스킬에 붙여 넣고
"이 목차와 슬롯대로 만들어줘"라고 요청한다. 코드 실행이 되는 ChatGPT 환경에서 Slide Master 스크립트를
직접 돌리는 방법도 있지만 이 저장소에서 검증하지 않았다.

## 업데이트

원본은 Claude 스킬 쪽이다. 회사 정보·표준 목차·디자인을 바꾼 뒤 아래를 실행해 `kit/`을 다시 만들고,
GPT·Gem의 지식 파일을 새 파일로 바꿔 올린다.

```bash
python3 portable-ai/build_portable_kit.py
```
