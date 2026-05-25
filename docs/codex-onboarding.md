# Codex Onboarding for Innergen PPT Automation

이 문서는 다른 사용자가 Codex에서 이 GitHub repo만 연결해도 같은 PPT 자동화 성과를 재현할 수 있도록 만든 운영 가이드입니다.

## 1. 준비물

- Windows PC 권장
- Node.js 20 이상 권장
- Git
- PowerPoint 설치 권장
  - PPTX 생성은 PowerPoint 없이도 가능
  - 렌더링 QA는 PowerPoint가 있으면 더 정확함
- Codex 또는 유사한 로컬 코딩 에이전트

API 키는 필수 아님. 현재 기본 흐름은 로컬 PPTX 생성과 ChatGPT 채팅창용 프롬프트 복사 방식입니다.

## 2. Codex에서 repo 열기

Codex에서 GitHub repo를 workspace로 엽니다.

```text
https://github.com/24josh4281/Innergen-PPT
```

처음 열면 Codex에게 이렇게 지시합니다.

```text
AGENTS.md와 README.md를 먼저 읽고, 이 repo의 PPT 자동화 워크플로우를 그대로 따라줘.
나는 비개발자이므로 변경 전에는 목적, 위험, 검증 방법을 짧게 설명하고 진행해줘.
```

## 3. 설치

```powershell
npm install
npm run verify:setup
```

`verify:setup`은 Node/npm, 필수 문서, ignore 규칙, build 가능 여부를 한 번에 확인합니다.

## 4. 실행

```powershell
npm run dev
```

터미널에 표시되는 URL을 엽니다. 보통 아래 중 하나입니다.

```text
http://127.0.0.1:5177
http://127.0.0.1:5180
```

## 5. 기본 사용법

1. 왼쪽 입력 패널에서 고객사, 프로젝트명, 문서 유형을 입력합니다.
2. 업무 시나리오를 선택합니다.
3. 원문 내용을 붙여넣거나 파일을 업로드합니다.
4. `1. Storyboard 설계`를 누릅니다.
5. 오른쪽에서 장표별 내용을 검토합니다.
6. 필요한 경우 제목, governing message, 추천 구조, 본문 항목을 수정합니다.
7. `2. 수정 반영 / QA`를 누릅니다.
8. 품질 점수와 경고를 확인합니다.
9. 승인 체크박스를 선택합니다.
10. `3. PPTX 생성`을 누릅니다.
11. 생성된 PPTX를 다운로드합니다.

## 6. ChatGPT 프롬프트 활용법

PPTX 생성 전후로 ChatGPT에서 더 정교하게 다듬고 싶으면:

1. Storyboard를 만든 뒤 `GPT 프롬프트 생성`을 누릅니다.
2. 목적에 맞는 모드를 선택합니다.
3. `복사` 또는 `MD 저장`을 누릅니다.
4. ChatGPT 채팅창에 붙여넣습니다.

권장 모드:

| 상황 | 사용할 모드 |
|---|---|
| 한 번에 PPT 제작 지시를 만들 때 | 한큐 PPT 생성 |
| 장표 제목과 메시지만 더 다듬을 때 | Storyboard 고도화 |
| 생성된 PPT 캡처를 다시 검토할 때 | PPT QA 리뷰 |
| 개발형 GPT에게 PPTX 코드 생성을 맡길 때 | PPTX 코드 구현 |

## 7. 품질 검증

일반 검증:

```powershell
npm run verify:setup
npm run build
```

구조 샘플 deck 생성:

```powershell
npm run samples:layout
```

PowerPoint 렌더링 QA:

```powershell
npm run qa:pptx-render
```

렌더링 QA는 PowerPoint 설치와 파일 경로 조건이 필요할 수 있습니다.

## 8. 좋은 입력 예시

```text
슬라이드 1: 컨설팅 목적
핵심 메시지: 글로벌 공시와 고객 요구가 강화되면서 Scope 1/2/3, 목표, 검증 대응을 통합해야 합니다.
근거/내용:
- SBTi 검증, CDP 평가, 기후리스크 분석을 분리 대응하면 자료 중복과 일정 리스크가 커집니다.
- 기준연도, 조직경계, 배출계수, 증빙 위치를 하나의 관리 체계로 정리해야 합니다.
- 최종 산출물은 의사결정, 외부 제출, 검증 대응에 동시에 활용되어야 합니다.
---
슬라이드 2: 수행 범위
핵심 메시지: 본 과업은 진단, 자료 취합, 분석, 검토, 제출 준비까지 하나의 체계로 수행합니다.
근거/내용:
- 배출량 산정 기준과 데이터 수집 체계를 점검합니다.
- CDP 문항별 요구사항과 증빙 현황을 연결합니다.
- 기후리스크 분석 결과를 보고서와 경영진 의사결정에 활용합니다.
```

## 9. 운영 원칙

- 원문 수치와 단위는 임의로 바꾸지 않습니다.
- 고객사 기밀자료는 외부 AI 도구에 붙여넣기 전 내부 기준을 확인합니다.
- ChatGPT API 직접 호출은 기본 보류 상태입니다.
- 최종 PPT는 반드시 사람이 한 번 검토합니다.
- 실패 사례가 나오면 해당 장표를 reference로 저장하고 QA 규칙을 개선합니다.

## 10. Codex에게 맡길 수 있는 작업

다른 사용자는 Codex에게 아래처럼 요청하면 됩니다.

```text
이 repo의 AGENTS.md 기준으로 실행해줘.
내가 붙여넣은 내용을 이너젠 스타일 컨설팅 PPT로 구조화하고, Storyboard QA 후 PPTX로 생성해줘.
오버플로우, 겹침, 한글 줄바꿈, 폰트 크기 문제를 반드시 검토해줘.
```

또는:

```text
이 자료를 바탕으로 ChatGPT 채팅창용 프롬프트를 만들어줘.
한큐 PPT 생성 모드와 QA 리뷰 모드를 둘 다 만들어줘.
```

## 11. 문제 해결

### PPTX 다운로드가 안 될 때

- 브라우저 팝업/다운로드 차단을 확인합니다.
- 다운로드 패널의 수동 링크를 누릅니다.
- `docs/generated/user-exports` 폴더를 확인합니다.

### 글자가 작거나 여백이 많을 때

- Storyboard의 본문 항목을 줄이고 핵심 메시지를 강화합니다.
- 추천 구조를 표, 프로세스, 비교 매트릭스, 로드맵 등으로 바꿉니다.
- `PPT QA 리뷰` 프롬프트 모드로 다시 검토합니다.

### API 키 관련 안내가 뜰 때

현재 기본 운영에서는 API를 쓰지 않습니다. `ENABLE_GPT_API=false`가 정상입니다.

## 12. 성공 기준

다른 사람이 이 repo를 열었을 때 성공 기준은 다음과 같습니다.

- `npm install` 성공
- `npm run dev` 성공
- 웹앱 접속 성공
- Storyboard 생성 성공
- QA 경고 확인 가능
- PPTX 다운로드 성공
- ChatGPT 프롬프트 생성 가능
- API 없이도 기본 업무 수행 가능
