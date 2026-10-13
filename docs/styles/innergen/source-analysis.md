# 이너젠 스타일 분석 근거

분석일: 2026-10-01. 원본은 `INPUTS/이너젠 PPT 장표 레퍼런스`에 보존했다. 이 문서는 문서의 사실관계나 최신 법규를 검증한 보고서가 아니라 디자인·구조 분석 기록이다.

## 1. 분석 범위와 검증

| 항목 | 결과 |
|---|---|
| 이너젠 PPTX | 19개, SHA-256 기준 모두 서로 다른 파일 |
| 전체 장표 | 573장 구조 분석 |
| 화면 규격 | 19개 모두 780×540 pt, 13:9 |
| 표·차트 | 네이티브 표 252개, 차트 3개. 이미지나 도형으로 만든 표/그래프는 이 숫자에 포함되지 않음 |
| 원본 렌더링 | PowerPoint 읽기 전용으로 573장 모두 PNG 생성, 실패 0 |
| 시각 표본 | 19개 대표 contact sheet에서 214개 장표 위치 확인, 별도 확대 장표 확인 |
| 원본 변경 | 분석 전후 SHA-256 대조: 19개 모두 동일 |
| 외부 참고자료 | 폴더의 컨설팅사·기관 참고 PDF는 이너젠 정체성 추출에서 제외 |
| 명령 취급 | 장표·메모·링크 속 문구는 분석 대상, 실행 지시로 사용하지 않음 |

전체 구조 분석·렌더링과 시각 표본 검토를 구분한다. 모든 장표의 본문 내용을 전수 검증하거나 새 결과물을 만들어 검증한 것은 아니다.

## 2. 파일 지도

| ID | 원본 경로: `INPUTS/이너젠 PPT 장표 레퍼런스/` 아래 | 장수 | 주 폰트 | 프레임 |
|---|---|---:|---|---|
| D01 | CDP/제안서 2.pptx | 41 | 맑은 고딕 | classic-grid |
| D02 | CDP/제안서 3.pptx | 49 | 맑은 고딕 | classic-grid |
| D03 | CDP/제안서.pptx | 52 | 맑은 고딕 | classic-grid |
| D04 | CDP/착수보고.pptx | 24 | 맑은 고딕 | classic-grid |
| D05 | CDP/최종보고 2.pptx | 21 | 맑은 고딕 | classic-grid |
| D06 | CDP/최종보고.pptx | 26 | 맑은 고딕 | classic-grid |
| D07 | 감축사업/방법론 개발 보고 2.pptx | 21 | IBM Plex Sans KR | classic-grid |
| D08 | 감축사업/방법론 개발 보고 3.pptx | 24 | IBM Plex Sans KR | classic-grid |
| D09 | 감축사업/방법론 개발 보고.pptx | 24 | IBM Plex Sans KR | classic-grid |
| D10 | 감축사업/제안서.pptx | 40 | IBM Plex Sans KR | classic-grid |
| D11 | 감축사업/착수보고 2.pptx | 32 | IBM Plex Sans KR | classic-grid |
| D12 | 감축사업/착수보고.pptx | 44 | IBM Plex Sans KR | classic-grid |
| D13 | 규제대응사업/착수보고_규제.pptx | 28 | IBM Plex Sans KR | classic-grid, 푸터 변형 |
| D14 | 규제대응사업/최종보고_규제.pptx | 17 | IBM Plex Sans KR | solid-navy |
| D15 | 온실가스 인벤토리/제안서.pptx | 23 | 맑은 고딕 | classic-grid |
| D16 | 온실가스 인벤토리/제안서_V2.pptx | 22 | IBM Plex Sans KR | slim-line |
| D17 | 온실가스 인벤토리/착수보고.pptx | 17 | 맑은 고딕 | slim-line |
| D18 | 온실가스 인벤토리/최종보고 2.pptx | 38 | 맑은 고딕 | classic-grid |
| D19 | 온실가스 인벤토리/최종보고.pptx | 30 | 맑은 고딕 | slim-line, 목차 P02는 classic-grid |

프레임과 글꼴의 차이를 연도순 변경으로 단정하지 않는다. 지정한 파일이 있으면 그 파일의 실제 특징을 적용한다. 전체 파일 해시·용량·주요 서식과 로고 출처는 [`source-manifest.json`](source-manifest.json), [`logo-provenance.json`](logo-provenance.json)에 보관한다.

## 3. 색상·글꼴·위치 근거

| 근거 | 관측 내용 | 해석 |
|---|---|---|
| 레이아웃 구조색 | 모든 파일의 사용 레이아웃에 직접 지정한 `#0F243F` 확인 | 공통 구조 남색 |
| D01 본문 레이아웃 | 남색 전체 바탕 위 흰 본문·우측 흰 도형을 덮고 격자를 배치 | 새 SVG에서는 같은 인상을 헤더·푸터·흰 본문으로 직접 구성 가능 |
| D01 본문 영역 | 흰 overlay y=0.7183 in, h=6.2250 in | 약 52 pt 헤더, 약 40 pt 푸터의 근거 |
| D01 격자 | `#F2F2F2`, alpha 14%, 약 0.17/0.1575 in 간격 | 저대비 격자. 본문 배경으로 사용하지 않음 |
| D01 P07 제목 | 직접 지정한 주 제목 24 pt, 같은 줄 소제목 14 pt | 재사용 기본 제목·소제목의 직접 근거 |
| 원본 표 셀 | 흰색 2,580, F2F2F2 876, 86AFDC 212, D9D9D9 163, 808080 96 | 회색/흰색 기본, 분석용 파랑은 필요할 때 사용 |
| 원본 텍스트 | 검정 34,747, 흰색 3,436, 빨강 2,897 run | 검정 본문·흰 반전 제목·빨간 강조 |

폰트 집계는 **글자 수가 아닌 text run 수**이며, 하나의 문장이 여러 run으로 나뉠 수 있다. 상속 글꼴도 확인하되 표시되지 않는 레이아웃 후보와 도형 역할의 위치 추정에는 한계가 있다.

| 폰트 | 전체 run | 직접 지정 | 상속 지정 |
|---|---:|---:|---:|
| 맑은 고딕 | 27,217 | 21,659 | 5,558 |
| IBM Plex Sans KR | 18,820 | 17,129 | 1,691 |
| 나눔스퀘어 | 1,115 | 1,104 | 11 |
| HY견고딕 | 641 | 0 | 641 |

본문 크기에는 12 pt 5,571 run, 11 pt 3,522 run, 10 pt 3,035 run이 반복된다. 표에는 10 pt 6,052 run, 10.5 pt 4,529 run, 9 pt 2,879 run이 반복된다. 제목 후보의 28 pt와 상단 작은 제목·소제목의 14–16 pt는 역할이 다르므로 하나의 평균 크기로 합치지 않았다. `design.json`의 역할별 수치는 이를 바탕으로 정한 제작 기본값이다.

## 4. 자산과 원본 장표 찾기

자체 로고만 분리했다. 표지 파란 로고는 D01 P01 layout1 shape3의 embedded image1.png, 푸터 흰 로고는 D01 P07 layout2 shape128의 embedded image4.png다. 고객사·협력사 로고는 공용 자산에 포함하지 않았다. 추출한 PNG는 원본 바이트와 동일하다.

| 구분 | 위치 |
|---|---|
| 전체 렌더링 | `.preview/innergen-visual/D01/slide-001.png` 등의 D01–D19 폴더 |
| 대표 비교판 | `.preview/innergen-visual/D01-sample.jpg` 등 |
| 전체 contact sheet | `.preview/innergen-visual/D01-all-01.jpg` 등 |
| 렌더링 작업 기록 | `.preview/innergen-visual/render_manifest.json` |
| 시각 관찰 기록 | `.preview/innergen-visual/visual_observations.md` |
| 상세 구조 근거 | `.preview/innergen-analysis/pptx_evidence.json`, `D01_evidence.json` 등 |
| 원본 추출 도구 | `.preview/innergen-analysis/extract_pptx_evidence.py` |

`.preview`는 로컬 검토용이며 Git 추적에서 제외된다. 향후에도 필요한 핵심 근거·해시는 이 폴더의 JSON 파일에 별도로 보관했다.

## 5. 재현의 한계와 업데이트

원본에는 여러 폰트·이미지 차트·외부 연결 그림·고객별 색이 섞여 있다. OOXML만으로 스크린샷 안의 글꼴이나 PowerPoint의 폰트 대체를 모두 확정할 수 없다. 생성된 PPTX는 폰트를 포함하지 않으므로 받는 컴퓨터의 설치 상태도 중요하다.

새 장표는 이 규칙에 따른 **일관된 재현**을 목표로 한다. 특정 원본의 완전한 복제가 필요하면 원본 파일과 보존 조건을 명시하고 네이티브 템플릿 채우기 경로를 사용한다. 원본 파일이 추가·변경되면 해시와 시각 검토를 갱신한 뒤 규칙 버전을 올린다. 이 스타일 요청 자체가 참고 문서의 업무 수치나 법규 내용을 최신 사실로 재사용할 근거는 아니다.

## 6. 적용 연결과 시험 결과

| 항목 | 완료한 작업 / 결과 |
|---|---|
| 호출 연결 | `AGENTS.md`와 canonical `innergen-style` 스킬에 한글 별칭·명시적 이너젠 원본 디자인 참조를 연결 |
| Codex 연결 | 기존 생성기를 사용해 새 스킬 stub만 생성, 전체 stub 일치 검사 통과 |
| 브랜드 등록 | 자체 로고 2개와 정체성 preset 등록. 레이아웃 규칙은 별도 유지 |
| 13:9 규격 | `config.py`에 `ppt139` 추가. 프로젝트 초기화와 PPTX 내보내기 확인 |
| 확인 화면 | `confirm_ui/static/app.js`가 13:9를 PPT 규격으로 인식. 전달 목적 처리 검사 통과 |
| 한글·영문 글꼴 | 변환기의 `drawingml/utils.py`에 원본 계열을 등록. 실제 PPTX Latin/EA 슬롯 동일 계열 확인 |
| 실제 PowerPoint | 진단용 1장 PPTX를 열어 780×540 pt 확인하고 1040×720 PNG 생성 |
| 파일 검사 | JSON·경로·색값·좌표 범위·폰트 크기 단위·원본 19개 해시 검사 통과 |
| 독립 행동 검토 | CDP 6장/로고 없음, 지정 인벤토리 V2/16:9/5장 요청을 계획 단계에서 점검, 남은 차단 문제 없음 |

시험 결과물은 `.preview/innergen-smoke/`에 있다. 전체 스타일을 적용한 업무용 새 덱을 제작한 것은 아니므로, 이후 실제 PPT를 만들 때도 해당 덱의 내용·수치·렌더링을 검증한다. 선택적 Playwright·OfficeCLI가 없는 상태는 그대로이며, 해당 도구를 통한 검사를 통과했다고 주장하지 않는다.

수정한 기존 파일의 원본은 `.preview/innergen-analysis/backups/`에 보존했다. 사용자 원본 자료의 이동·저장·수치 변경과 외부 업로드는 수행하지 않았다.
