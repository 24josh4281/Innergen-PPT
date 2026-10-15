# innergen-deck 스킬 v23 반영 점검 (2026-10-15)

## 1. 비교 대상

| 항목 | 내용 |
|---|---|
| 비교한 스킬 | claude.ai에 설치된 `innergen-deck` (이 세션에 동기화된 사본, 2026-10-15) |
| 기준 규칙 | 스킬에 동봉된 `content-architecture-v20.md`(v23·v24 절), `design-standard-v17.md`(v22·v23 절), `qaqc-v21.json`(rev.23) |
| 확인하지 못한 것 | slide-master 원본 저장소의 `OUTPUTS/claude-chat-skill/innergen-deck.zip`과 `build_chat_skill.py`. 이 세션에서 접근 가능한 저장소 목록에 slide-master가 없고, `Slide-Master-Workspace`(2026-10-08 백업)에는 해당 파일이 없다. 그래서 원본 zip이 아니라 **실제로 claude.ai에서 쓰이는 설치본**을 기준으로 비교했다. |

## 2. 차이 요약

| 영역 | 설치본 상태 | 판정 |
|---|---|---|
| 템플릿 (3계열) | `innergen_lecture` 71개, `innergen_business`·`innercarry` 각 70개 파일. s01–s58 모두 포함 (v23 s24–s42, v24 s43–s58) | 반영됨 |
| `start_deck.py` 스캐폴드 | 3계열 모두 `templates/`에 s01–s58 58개 구조 생성 | 반영됨 |
| PPTX 변환 | s24–s42 19장을 3계열 각각 변환, 19/19 성공 | 정상 |
| 규칙 문서 | v20 §v23·§v24, v17 §v22·계열 템플릿 표 포함 | 반영됨 |
| QA 규칙표 | `qaqc-v21.json` version 23, 덱 유형별 필수 레이아웃·마무리 세트에 v23 구조 포함 | 반영됨 |
| **SKILL.md 구조 목록** | §3에 `s01`–`s23`만 나열. s24–s58 없음, 덱 유형별 우선 구조 안내 없음 | **누락 → 갱신** |
| **SKILL.md 레이아웃 설명** | "same in every family"라고 적었지만 `02_toc`는 `innergen_lecture`에만 있음 | **오류 → 수정** |
| **QA 레이아웃 인식** | `innergen_qaqc.py`는 SVG 루트의 `data-pptx-layout`으로 레이아웃을 판별하는데, 채팅판 템플릿에는 이 속성이 없고 SKILL.md는 추가를 금지한다. 그 결과 목차(O01), 필수 레이아웃(S03), 마무리 세트(S02) 검사가 **항상 경고**를 낸다. 즉 v23 필수 세트 규칙이 채팅판에서는 사실상 작동하지 않았다. | **결함 → 수정** |

결함 재현: 표지·목차·s24·s25·s26·마무리로 구성한 착수(kickoff) 덱에서, 수정 전에는 "목차 장표가 없습니다"와 "필수 레이아웃 없음" 4건, 마무리 세트 경고 1건이 나왔다.

## 3. 바꾼 것

1. `SKILL.md` §3: 레이아웃 목록을 프레임 12종 + s01–s58 전체로 확장하고 v23·v24 구조에 한글 이름을 붙였다. 덱 유형별 우선 구조 표(v20 §v23·§v24 그대로)와 QA rev.23 필수 레이아웃 요약을 더했다. `02_toc`는 교육 계열 전용이라고 명시했다.
2. `SKILL.md` §5: 페이지 파일명을 `NN_<레이아웃 id>.svg`(예: `05_s24_project_overview.svg`)로 정했다. 접미사는 `__` 뒤에 붙인다.
3. `scripts/innergen_qaqc.py`: `data-pptx-layout`이 없으면 위 파일명에서 레이아웃 id를 읽는다(`_layout_from_filename`). 목차 판별에 `toc`·`toc-pages`도 인정한다. 속성이 있는 전체 파이프라인 덱의 동작은 그대로다.

## 4. 검증

| 검사 | 결과 |
|---|---|
| 착수 덱(위 구성) × 3계열, 수정 후 `innergen_qaqc --deck-type kickoff` | S03·S02 경고 0건, 목차 인식됨. 남은 O01은 목차 자리표시자(`{{TOC_n_TITLE}}`)를 채우지 않아 생긴 것으로 정상 |
| 파일명 해석 | `05_s24_project_overview`→`s24-project-overview`, `02_02b_toc_pages`→`toc-pages`, `03_03b_content_final`→`content-final`, 레이아웃 id 없는 이름은 빈 값(기존과 동일) |
| s24–s42 PPTX 변환 × 3계열 | 각 19/19 성공 |

## 5. 남은 일

- 원본은 slide-master 저장소의 `build_chat_skill.py`다. 같은 변경(SKILL.md 본문, `innergen_qaqc.py` 대체 판별)을 그쪽 생성기와 원본 스크립트에도 넣어야 다음 재빌드에서 되돌아가지 않는다.
- claude.ai 업로드는 하지 않았다. 묶음 파일은 프로젝트 폴더 `innergen-deck/innergen-deck.zip`에 있다.
- v24 구조(s43–s58)는 QA 필수 세트에는 아직 없다(rev.23 기준). 필요하면 규칙표를 rev.24로 올려야 한다.
