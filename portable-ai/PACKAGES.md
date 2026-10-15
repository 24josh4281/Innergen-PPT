# GPT·Gemini 패키지 정리

| 항목 | GPT용 | Gemini용 |
|---|---|---|
| 패키지 | `dist/innergen-gpt-kit.zip` | `dist/innergen-gemini-kit.zip` |
| 넣는 곳 | 맞춤형 GPT(또는 ChatGPT 프로젝트) | Gem |
| 지침 칸 | `INSTRUCTIONS.md` (약 1,600자) | `INSTRUCTIONS.md` (같은 내용) |
| 지식 파일 | `knowledge/` 7개 | `knowledge/` 7개 |
| 시작 문구 | `starters.txt` → Conversation starters | `starters.txt` → 복사해서 요청 |
| 역할별로 나누기 | `roles-split/` → GPT 4개 | `roles-split/` → Gem 4개 |
| 필요한 요금제·설정 | 맞춤형 GPT를 만들 수 있는 유료 요금제 | Gem 사용 가능 계정(Workspace는 관리자 허용 필요) |
| 설치 방법 | 패키지 안 `INSTALL.md` | 패키지 안 `INSTALL.md` |
| 예상 결과물 | `EXPECTED-OUTPUTS.md` (두 패키지 공통) | 같음 |

## 결과물 (두 서비스 공통)

1. 본문 구성 프리셋 한 줄과 목차표 `| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 | 거버닝 유형 | 본문 구성 |`, 확인 질문. 여기서 멈추고 사용자 확인을 기다립니다.
2. 쪽별 문구: 제목, 한 줄 거버닝, 본문, 출처
3. 슬롯 명세 JSON: Claude 스킬에 그대로 붙여 넣는 형식
4. 검사표: R·B·F·M·D·G·T·Q 코드, `ERROR n · WARN n · INFO n · PASS/FAIL`

편집 가능한 PPTX 파일은 만들지 않습니다. 목차표와 JSON을 Claude innergen-deck 스킬에 붙여 넣으면 같은 레이아웃으로 PPTX가 만들어집니다.

## 다시 만들기

```bash
python3 portable-ai/build_portable_kit.py
```
