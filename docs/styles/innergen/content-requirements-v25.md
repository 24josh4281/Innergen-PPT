# 이너젠 보고 유형 × 사업 성격 목차·필수 내용 v25 (2026-10-15)

보고 유형(deck_type)마다 **목차 골격**(빠지면 안 되는 절과 순서)과 **꼭 들어갈 내용**, 사업 성격(business_type)마다 **업무별 필수 내용**을 한 표로 묶었다. 기계용 값은 [content-requirements-v25.json](content-requirements-v25.json)이고, `scripts/innergen_content_check.py`(장표 계획 단계)와 `scripts/innergen_qaqc.py`(완성 덱, R·B·Q 코드)가 같은 표를 읽는다.

- 근거: [v20](content-architecture-v20.md) §2 목차 골격·§8 마무리 세트·§6.6 셀 문법, [v16](innergen-profile-matrix-v16.md) §3 업무별 필수 장표·§4 보고 단계별 "반드시 들어갈 것", [report-profiles.json](report-profiles.json) focus·evidence_rule, 저장소 `docs/standard-deck-flows.json`. 새 범주를 만들지 않고 이 문서들에 이미 있는 유형만 옮겼다.
- 우선순위: 현재 사용자 요청 → 프로젝트 `spec_lock.md` → v20·v16 → 이 표. 이 표는 v20·v16을 검사 가능한 형태로 바꾼 것이므로, 두 문서를 고치면 이 표도 같이 고친다.
- 대상 밖: report_outline(보고서 구성안), memo(A4 요약 메모).

## 1. 판정 방식

| 대상 | 판정 |
|---|---|
| section | 한 절은 레이아웃 id가 layouts 중 하나를 포함하거나, 장표의 제목·거버닝·큰 글씨(20px 이상) 텍스트가 keywords 정규식에 걸리면 있다고 본다. 표지·목차·장 구분·맺음 장표의 텍스트와 푸터 라벨은 키워드 판정에서 뺀다(목차·장 구분·푸터가 장 이름을 담기 때문). |
| item | pattern(하나라도) 또는 all_of(모두)가 덱 본문 전체 텍스트에 걸리면 있다고 본다. where가 section:<id>이면 그 절로 판정된 장표 안에서만 찾는다. where가 titles면 본문 장표 제목만 본다. 대소문자 무시. |
| order | order에 적힌 절은 처음 나타나는 장 번호가 이 순서를 따라야 한다(같은 장은 허용). |
| stages | business item의 stages가 없으면 모든 보고 유형에 적용한다. 있으면 그 보고 유형에서만 검사한다. |

| 코드 | 내용 | 수준 |
|---|---|---|
| R00 | 보고 유형 미지정 | WARN |
| R01 | 목차 필수 절 없음 | ERROR |
| R02 | 절 순서가 골격과 다름 | WARN |
| R03 | 보고 유형의 꼭 들어갈 내용 없음 | 항목별(ERROR = v16 "반드시") |
| R04 | 기본 장수 범위의 절반 미만·1.5배 초과 | INFO |
| B00 | 사업 성격 미지정·알 수 없음 | 보고형 WARN, 교육형 INFO |
| B01 | 사업 성격의 필수 내용 없음 | 항목별(정체성 항목 ERROR, 나머지 WARN) |
| Q01 | 자리표시자 `{{…}}`·TBD·`///` 잔재 | ERROR |
| Q02 | 금지 표현(본문 제목의 보고 단계명, 세미나 Q&A 장표) | WARN |

- 장표 계획 단계(`--outline`)에서는 본문이 아직 없으므로 R03·B01의 ERROR를 WARN으로 낮춘다. 계획표의 다섯째 열 "넣을 내용"에 필수 내용을 적어 두면 그 단계에서 해소된다. R01(필수 절)은 계획 단계에서도 ERROR다.
- `innergen_qaqc.py`는 이 표가 다루는 보고 유형에서 기존 S03(필수 레이아웃)과 O01(목차 없음) 경고를 R01로 대신한다.

## 2. 보고 유형별 목차 골격과 꼭 들어갈 내용

### `lecture` 교육·강의(투사)  ·  기본 30–90장  ·  근거: v20 §2.1·§8, v16 §4 education

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 목차 | ● | toc | — |
| 학습 목표 | ● | — | `학습\s?목표\|Learning\s?Objective` |
| 배경·제도(왜 지금인가) | ● | chart-insight · keyword-grid · year-timeline · content-kpi · quote-opener | `배경\|왜 지금\|제도\|동향\|현황` |
| 요소별 요구사항 + 핵심 Focus | ● | guidance-focus | `요구\s?사항\|핵심\s?Focus` |
| 사례 | ● | case-capture | `사례\|배울\s?점\|Case` |
| 우리 과제(자가진단·과제 목록) | 선택 | — | `우리\s?(회사\|과제)\|과제\s?목록` |
| 핵심 정리 | ● | key-summary | `핵심\s?정리\|Key\s?Summary` |
| Key Questions 자가진단 | ● | self-check | `Key\s?Questions\|자가\s?진단` |
| Q&A·다음 단계 | ● | — | `Q\s?&\s?A\|질의\|다음\s?단계\|2차\s?교육\|자문\s?안내` |
| 맺음 | ● | ending | — |

순서: 목차 → 학습 목표 → 배경·제도(왜 지금인가) → 요소별 요구사항 + 핵심 Focus → 핵심 정리 → Key Questions 자가진단 → Q&A·다음 단계

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 최신 수치의 기준일 | WARN | deck | v16 §4 education 반드시 |
| 요구사항 장표의 핵심 Focus 칸 | WARN | 절: requirements | v20 §6.4 |
| 사례 장표의 배울 점 칸 | WARN | 절: cases | v20 §6.4 |

### `handout` 교육·배포 교재  ·  기본 30–90장  ·  근거: v20 §2.1·§8 (lecture와 같은 골격)

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 목차 | ● | toc | — |
| 학습 목표 | ● | — | `학습\s?목표\|Learning\s?Objective` |
| 배경·제도(왜 지금인가) | ● | chart-insight · keyword-grid · year-timeline · content-kpi · quote-opener | `배경\|왜 지금\|제도\|동향\|현황` |
| 요소별 요구사항 + 핵심 Focus | ● | guidance-focus | `요구\s?사항\|핵심\s?Focus` |
| 사례 | ● | case-capture | `사례\|배울\s?점\|Case` |
| 우리 과제(자가진단·과제 목록) | 선택 | — | `우리\s?(회사\|과제)\|과제\s?목록` |
| 핵심 정리 | ● | key-summary | `핵심\s?정리\|Key\s?Summary` |
| Key Questions 자가진단 | ● | self-check | `Key\s?Questions\|자가\s?진단` |
| Q&A·다음 단계 | ● | — | `Q\s?&\s?A\|질의\|다음\s?단계\|2차\s?교육\|자문\s?안내` |
| 맺음 | ● | ending | — |

순서: 목차 → 학습 목표 → 배경·제도(왜 지금인가) → 요소별 요구사항 + 핵심 Focus → 핵심 정리 → Key Questions 자가진단 → Q&A·다음 단계

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 최신 수치의 기준일 | WARN | deck | v16 §4 education 반드시 |
| 요구사항 장표의 핵심 Focus 칸 | WARN | 절: requirements | v20 §6.4 |
| 사례 장표의 배울 점 칸 | WARN | 절: cases | v20 §6.4 |

### `seminar` 세미나·강연·발표  ·  기본 15–30장  ·  근거: v20 §2.2·§8

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 개념 정의 또는 질문 1장 | 선택 | quote-opener · issue-cards | `정의\|무엇인가\|\?` |
| 목차 | ● | toc | — |
| 배경·개념 | ● | content-kpi · chart-insight | `배경\|개념\|정의\|왜 지금\|리스크` |
| 제도·동향 | ● | keyword-grid · entity-matrix · period-applicability · year-timeline | `제도\|동향\|요구\s?사항\|적용\s?시기\|규제` |
| 분석·사례 | ● | case-capture · vertical-chevron · compare-implication · challenges-considerations · process-steps-detail | `사례\|분석\|고려\s?사항\|어려움` |
| 대응·준비 | ● | phase-roadmap · process-steps-detail · vertical-chevron | `대응\|준비\|로드맵` |
| 결론(질문 + 방향 3개) | ● | key-takeaways | `결론\|방향\|Takeaway` |
| 감사·연락처 | ● | ending | — |

순서: 목차 → 배경·개념 → 제도·동향 → 분석·사례 → 대응·준비 → 결론(질문 + 방향 3개)

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| Q&A 장표를 따로 두지 않음(질문은 본문 자가진단으로) | FORBID | titles | v20 §2.2 |

### `proposal` 제안서·제안 발표  ·  기본 12–25장  ·  근거: v20 §2.3·§8, v16 §4 proposal, report-profiles proposal

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 고객 과제·배경 | ● | issue-tree · scqa-storyline · content-final | `고객\s?과제\|과제\|배경\|목적\|Issue` |
| 제도·시장 근거 | 선택 | chart-insight · content-table · year-timeline | `제도\|시장\|근거\|동향` |
| 핵심 쟁점 | 선택 | exec-summary · issue-cards | `쟁점\|핵심\s?이슈` |
| 목표와 범위(안/밖) | ● | scope-method-result · content-dual · project-overview | `범위\|목표\|Scope` |
| 접근 방법·단계 | ● | task-structure · vertical-chevron · approach-matrix · hypothesis-workplan · process-steps-detail | `접근\|방법론\|추진\s?(방안\|전략)\|수행\s?(방안\|방법)\|단계` |
| 산출물 | ● | — | `산출물\|성과품\|납품\|Deliverable` |
| 일정 | ● | gantt-schedule · phase-roadmap | `일정\|마일스톤\|Schedule` |
| 수행 체계·인력 | ● | team-roles · raci-matrix | `수행\s?체계\|투입\s?인력\|참여\s?인력\|조직\|PM\|역할` |
| 이너젠 실적·차별점 | ● | — | `실적\|차별\|강점\|레퍼런스\|Why\s?INNerGEN\|수행\s?경험` |
| 기대효과 | ● | asis-tobe-effect · purpose-effects | `기대\s?효과\|효과` |
| 다음 단계(Way forward) | 선택 | key-takeaways | `Way\s?forward\|다음\s?단계\|향후` |
| 맺음 | ● | ending | — |

순서: 고객 과제·배경 → 목표와 범위(안/밖) → 접근 방법·단계 → 산출물 → 일정 → 수행 체계·인력

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 범위 안/밖 구분 | ERROR | deck | v16 §4 proposal 반드시 |
| 산출물 목록 | ERROR | deck | v16 §4 proposal 반드시 |
| 필요한 협조(고객 역할) | WARN | deck | v16 §4 proposal 반드시, report-profiles flow |

### `kickoff` 착수보고  ·  기본 10–20장  ·  근거: v20 §2.4·§8·§10, v16 §4 kickoff, report-profiles kickoff

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 목차 | ● | toc | — |
| 배경·현황(As-Is) | ● | chart-insight · purpose-effects · scqa-storyline | `배경\|현황\|As[-\s]?Is` |
| 대상·범위·기준 | ● | project-overview · task-structure · content-dual | `범위\|대상\|기준\s?연도\|경계\|Scope` |
| 목적·기대효과 | ● | purpose-effects | `목적\|기대\s?효과\|목표` |
| 추진방안(과업별 접근·상세) | ● | vertical-chevron · process-steps-detail · approach-matrix · hypothesis-workplan · task-structure | `추진\s?방안\|접근\|수행\s?계획\|방법론\|과업\s?[①②③]` |
| 수행 일정(간트) | ● | gantt-schedule · phase-roadmap | `일정\|마일스톤\|간트\|Schedule` |
| 데이터 수집 요청 | ● | data-request · actor-checklist | `자료\s?요청\|데이터\s?(수집\s?)?요청\|요청\s?자료\|Data\s?Request` |
| 참여 인력·역할 | ● | team-roles · raci-matrix · stakeholder-map | `인력\|역할\|담당\|수행\s?체계\|커뮤니케이션\|R&R` |
| 관리방안(QA/QC·보안·성과품) | 선택 | — | `QA\s?/?\s?QC\|품질\|보안\|성과품\|관리\s?방안` |
| 결정 요청·다음 일정 | ● | decision-request | `결정\|의사\s?결정\|안건\|다음\s?일정` |
| 맺음 | ● | ending | — |

순서: 목차 → 배경·현황(As-Is) → 대상·범위·기준 → 추진방안(과업별 접근·상세) → 수행 일정(간트) → 데이터 수집 요청 → 결정 요청·다음 일정

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 기준연도·경계·적용 기준 | ERROR | deck | v16 §4 kickoff 반드시 |
| 자료 요청 항목의 기한 | ERROR | 절: data_request | v16 §4 kickoff 반드시 |
| 자료 요청 담당자 | ERROR | 절: data_request | v16 §4 kickoff 반드시 |
| 의사결정 안건 | ERROR | deck | v16 §4 kickoff 반드시 |
| 착수·중간·최종 마일스톤 | WARN | deck | v20 §2.4 |

### `weekly` 주간 진행보고  ·  기본 10–20장  ·  근거: v20 §2.5·§8

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 목차 | 선택 | toc | — |
| 이번 주 맥락 | 선택 | chart-insight | `맥락\|동향\|이번\s?주` |
| 이번 주 진행 | ● | progress-plan · status-board | `진행\|현황\|완료\|수행\s?내용` |
| Wrap-up 비교·판단 | 선택 | compare-implication · period-applicability | `Wrap[-\s]?up\|비교\|정리` |
| 향후 추진 계획 | ● | progress-plan · actor-checklist | `향후\|다음\s?주\|추진\s?계획\|예정` |
| 고객 판단·요청 사항 | ● | decision-request | `요청\|결정\|판단\s?사항\|확인\s?사항` |

순서: 이번 주 진행 → 향후 추진 계획

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 상태·일자 괄호 표기 | WARN | deck | v20 §5.3 진행 상태, §9-5 |
| 추가 요청 항목 | WARN | deck | v20 §2.5 |

### `biweekly` 격주 미팅 자료  ·  기본 2–3장  ·  근거: v20 §2.6·§8

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 진행현황 | 향후계획 2열표 | ● | progress-plan · content-dual · status-board | `진행\s?현황\|향후\s?계획` |
| 수행 일정 간트(현재 주차) | ● | gantt-schedule · phase-roadmap | `일정\|간트` |
| 첨부 산출물 | 선택 | — | `첨부\|산출물\|Appendix` |

순서: 진행현황 | 향후계획 2열표 → 수행 일정 간트(현재 주차)

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 요청·결정 행 | WARN | deck | v20 §8 격주 |
| 상태·일자 괄호 표기 | WARN | deck | v20 §2.6 |

### `monthly` 월간 WG·진행현황  ·  기본 25–50장  ·  근거: v20 §2.7·§8

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 과업 현황판 | ● | status-board · phase-roadmap | `현황판\|과업\s?현황\|추진\s?현황` |
| 교육 장(동향·기준·사례) | 선택 | guidance-focus · case-capture | `동향\|기준\|사례` |
| 과업별 수행 현황·결과 | ● | vertical-chevron · chart-insight · entity-matrix · compare-implication · content-table | `수행\s?현황\|분석\s?결과\|결과\|Gap` |
| 운영 현황(WG·교육·상담 실적) | ● | meeting-log | `운영\|교육\s?실적\|상담\|회의\s?실적\|WG\|워킹\s?그룹` |
| 향후 추진 일정 | ● | gantt-schedule · phase-roadmap | `향후\s?(추진\s?)?일정\|간트\|일정` |
| Appendix | 선택 | — | `Appendix\|부록` |

순서: 과업 현황판 → 과업별 수행 현황·결과 → 운영 현황(WG·교육·상담 실적) → 향후 추진 일정

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 상태 배지(완료/진행 중/예정) | ERROR | deck | v20 §2.7·§6.6 |
| 실적표(회차·일자·참석·주제·의견) | WARN | 절: operation | v20 §8 |

### `diagnosis` 진단·개선과제 도출  ·  기본 30–50장  ·  근거: v20 §2.8·§8

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 진단 Framework·Key Questions | ● | keyword-grid · self-check · issue-tree · driver-tree · seven-s-alignment | `진단\s?(관점\|프레임\|Framework)\|Framework\|Key\s?Questions\|분석\s?프레임` |
| 기준 × 현황 × 개선과제 요약 | ● | diagnosis-table · principle-matrix · maturity-heatmap | `기준\|현황\|Gap\|갭\|진단` |
| 개선과제 상세(AS-IS → TO-BE) | ● | asis-tobe-effect · vertical-chevron · operating-model · swimlane-controls | `AS[-\s]?IS\|TO[-\s]?BE\|개선\s?과제` |
| 영역별 진단·실행과제·사례 | 선택 | actor-checklist · case-capture | `실행\s?과제\|\[?참고\]?\|사례` |
| 개선과제 종합(우선순위) | ● | priority-matrix · entity-matrix · nine-box | `우선\s?순위\|용이성\|효과성\|추진\s?여부\|종합` |
| Appendix | 선택 | — | `Appendix\|부록` |

순서: 진단 Framework·Key Questions → 기준 × 현황 × 개선과제 요약 → 개선과제 상세(AS-IS → TO-BE) → 개선과제 종합(우선순위)

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 추진여부 선택란(금년/차년/검토) | ERROR | deck | v20 §8 진단 |
| Gap 셀 문법(부재/미흡/미제시/불일치) | WARN | deck | v20 §6.6 |

### `interim` 중간보고  ·  기본 10–18장  ·  근거: v20 §2.9, v16 §4 interim (원본 레퍼런스 없음: 구성 제안)

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 요약 | ● | exec-summary · exec-one-pager · content-kpi · scqa-storyline | `요약\|Summary` |
| 진행 현황 | ● | status-board · phase-roadmap · progress-plan | `진행\s?(현황\|률)\|진척\|추진\s?현황` |
| 잠정 결과 | ● | chart-insight · entity-matrix · content-table · waterfall-bridge · value-chain-hotspot | `잠정\|중간\s?결과\|분석\s?결과\|결과` |
| 확인된 사실 vs 미확정 | ● | content-dual · compare-implication | `확인된\|미확정\|확정\s?사항` |
| 이슈·리스크 | ● | risk-heatmap · challenges-considerations · content-final | `이슈\|리스크\|쟁점` |
| 결정 요청 | ● | decision-request | `결정\s?요청\|의사\s?결정\|승인\s?요청` |
| 다음 단계 | ● | vertical-chevron · phase-roadmap · gantt-schedule | `다음\s?단계\|향후\|Next` |
| 맺음 | 선택 | ending | — |

순서: 요약 → 진행 현황 → 잠정 결과 → 이슈·리스크 → 결정 요청 → 다음 단계

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 진행률 근거 | ERROR | deck | v16 §4 interim 반드시 |
| 잠정 수치의 상태 표기(잠정·검증 전) | ERROR | deck | v16 §4 interim 반드시 |
| 결정 요청 문장 | ERROR | deck | v16 §4 interim 반드시 |

### `final` 최종보고  ·  기본 20–40장  ·  근거: v20 §2.9·§8, v16 §4 final, report-profiles final

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 요약(결론 먼저) | ● | exec-summary · exec-one-pager · content-kpi · scqa-storyline | `요약\|결론\|Summary` |
| 목차 | ● | toc | — |
| 과업 개요(배경·목적·범위) | ● | task-structure · project-overview · purpose-effects | `과업\s?개요\|추진\s?배경\|목적\|범위` |
| 방법·기준 | ● | vertical-chevron · scope-method-result · process-steps-detail · swimlane-controls | `방법\|기준\|방법론\|산정\s?기준\|접근` |
| 결과 | ● | chart-insight · entity-matrix · content-table · waterfall-bridge · value-chain-hotspot · profit-pool · sensitivity-tornado · chart-table-strip | `결과\|분석\|산정\s?결과` |
| 시사점(종합 → 개별) | 선택 | key-takeaways | `시사점\|Implication` |
| 검증·한계 | ● | — | `검증\|한계\|제약\|불확실` |
| 잔여 과제·인계·로드맵 | ● | priority-matrix · phase-roadmap · pathway-wedge · three-horizons | `잔여\|인계\|향후\s?과제\|로드맵\|개선\s?과제\|Roadmap` |
| 부록 | 선택 | — | `부록\|Appendix` |
| 맺음 | ● | ending | — |

순서: 요약(결론 먼저) → 방법·기준 → 결과 → 검증·한계 → 잔여 과제·인계·로드맵

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 결과 수치의 단위 | ERROR | 절: results | v16 §4 final 반드시(결과마다 근거 출처·단위) |
| 한계 명시 | ERROR | deck | v16 §4 final 반드시 |
| 잔여 과제의 담당 | WARN | deck | v16 §4 final 반드시 |

### `briefing` 경영진 요약·브리핑  ·  기본 1–8장  ·  근거: v20 §2.10, v16 §4 briefing

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 한 장 요약(결과 요약) | ● | exec-one-pager · exec-summary · content-kpi · scqa-storyline | `요약\|Summary\|결과` |
| 선택지 비교 | 선택 | harvey-compare · compare-implication · scenario-matrix · decision-tree | `선택지\|대안\|옵션\|Option` |
| 권고안 | ● | — | `권고\|제안\|추천\|Recommendation` |
| 결정 요청 | ● | decision-request | `결정\|승인` |

순서: 한 장 요약(결과 요약) → 권고안 → 결정 요청

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 결정해야 할 것 1문장 | ERROR | deck | v16 §4 briefing 반드시 |
| 선택지별 비용·효과·리스크 | WARN | deck | v16 §4 briefing 반드시 |

### `benchmark` 벤치마킹  ·  기본 10–20장  ·  근거: v20 §2.11

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| Approach(대상·방법·프레임) | ● | approach-matrix · content-split | `Approach\|대상\|방법\|프레임` |
| 분석 주안점 Key Questions | ● | self-check | `Key\s?Questions\|주안점` |
| 결과 Overview(Key Findings) | ● | radar-benchmark · chart-insight | `Overview\|Key\s?Findings\|결과` |
| 비교 히트맵 | 선택 | maturity-heatmap · harvey-compare | `히트맵\|비교` |
| 영역별 Gap표 | ● | compare-implication · diagnosis-table | `Gap\|갭` |
| [Back-up] 사례 | 선택 | case-capture | `Back[-\s]?up\|사례` |

순서: Approach(대상·방법·프레임) → 분석 주안점 Key Questions → 결과 Overview(Key Findings) → 영역별 Gap표

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| Gap 셀 문법(부재/미흡/미제시/불일치) | ERROR | deck | v20 §6.6 |

### `insight` 인사이트 리포트  ·  기본 20–45장  ·  근거: v20 §2.12·§8

| 절 | 필수 | 인정 레이아웃 | 제목·거버닝 키워드 |
|---|---|---|---|
| 표지 | ● | cover | — |
| 목차 | ● | toc | — |
| 배경 장(개념·경쟁·연혁·지표) | ● | keyword-grid · year-timeline · chart-insight | `배경\|경쟁\|연혁\|동향\|개념` |
| 이슈 개요 카드 | ● | exec-summary · issue-cards | `이슈\|Issue` |
| 범주 매핑 | 선택 | entity-matrix · materiality-matrix | `매핑\|범주` |
| 이슈별 현황·제도·영향 | ● | content-table · chart-insight · period-applicability · experience-curve | `현황\|제도\|영향\|전망` |
| Key Takeaways | ● | key-takeaways · key-summary | `Takeaway\|시사점\|대응\s?방향` |
| 저자·연락처 | 선택 | ending | `연락처\|저자\|Contact` |

순서: 목차 → 배경 장(개념·경쟁·연혁·지표) → 이슈 개요 카드 → 이슈별 현황·제도·영향 → Key Takeaways

| 꼭 들어갈 내용 | 수준 | 찾는 곳 | 근거 |
|---|---|---|---|
| 면책 문구 | WARN | deck | v20 §2.12·§8 |

## 3. 사업 성격별 필수 내용

`stages`가 비어 있으면 모든 보고 유형에서 검사한다. 단계 배정은 v16 필수 장표를 보고 단계의 성격(제안·착수는 범위와 계획, 중간·최종은 결과)에 맞춰 나눈 것으로, 원본 레퍼런스가 없는 조합은 구성 제안이다.

### `cdp_disclosure` CDP·기후공시 (별칭: disclosure, cdp)

독자 질문: 어떤 항목을 어떤 근거로 공시해야 하고, 지금 어디가 부족한가. 근거: v16 §3 cdp_disclosure, report-profiles focus·evidence_rule.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 적용 기준·공시 연도 | ERROR | 전체 |
| 문항·요구사항 지도 | WARN | proposal, kickoff, diagnosis, interim, final, lecture, handout, seminar |
| 항목별 근거 자료 | WARN | kickoff, diagnosis, interim, final |
| 현황 진단(답변 현황·Gap) | WARN | proposal, diagnosis, interim, final, benchmark |
| 점수·등급 추이 | WARN | proposal, final, benchmark, briefing |
| 보완 과제·일정 | WARN | diagnosis, interim, final, briefing |

### `regulatory` 규제 대응 (별칭: regulation, kets, ets)

독자 질문: 어떤 의무가 언제부터 누구에게 적용되며, 놓치면 무엇이 생기는가. 근거: v16 §3 regulatory, report-profiles focus·evidence_rule.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 적용 제도 | ERROR | 전체 |
| 적용 대상·기준값 | WARN | 전체 |
| 의무 시점(시행·제출 기한) | ERROR | 전체 |
| 산정·보고·검증 절차 | WARN | proposal, kickoff, interim, final, lecture, handout, seminar, diagnosis |
| 비용·가격 영향 | WARN | final, briefing, seminar, lecture, handout, insight |
| 대응 체크리스트·쟁점 | WARN | kickoff, interim, final, seminar, lecture, handout, diagnosis |
| 공식 기관 출처 | WARN | 전체 |

### `reduction` 감축사업·상쇄 (별칭: offset)

독자 질문: 얼마를 어떤 수단으로 언제까지 줄이며, 비용·인정 여부는 어떤가. 근거: v16 §3 reduction, report-profiles focus·evidence_rule, standard-deck-flows reduction-kickoff.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 기준선·사업 경계 | ERROR | 전체 |
| 감축 수단별 감축량 | WARN | proposal, kickoff, interim, final, briefing |
| 방법론·MRV | WARN | proposal, kickoff, interim, final |
| 감축 경로·로드맵 | WARN | interim, final, briefing |
| 한계감축비용 | WARN | final, briefing |
| 인정·추가성·리스크 | WARN | proposal, kickoff, interim, final |
| 감축량 단위·기준기간 | ERROR | kickoff, interim, final, briefing |

### `inventory` 온실가스 인벤토리 (별칭: ghg, ghg_inventory)

독자 질문: 경계 안의 배출량이 얼마이고, 어디서 나오며, 숫자를 믿을 수 있는가. 근거: v16 §3 inventory, report-profiles focus·evidence_rule, standard-deck-flows ghg-inventory-final.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 조직·운영 경계 | ERROR | 전체 |
| 배출원·활동자료 목록 | WARN | kickoff, interim, final, diagnosis |
| Scope별 배출량 | ERROR | interim, final, briefing |
| 연도 증감 요인 | WARN | final, briefing |
| 배출계수·데이터 품질 | WARN | kickoff, interim, final, diagnosis |
| 데이터 요청 | WARN | kickoff |
| 배출량 단위 | ERROR | interim, final, briefing |

### `lca_product` LCA·제품 탄소발자국 (별칭: lca, pcf)

독자 질문: 제품 하나의 배출이 생애주기 어디에 몰려 있고, 무엇을 바꾸면 줄어드는가. 근거: v16 §3 lca_product.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 기능단위·시스템 경계 | ERROR | 전체 |
| 단계별 배출 | WARN | interim, final, briefing, lecture, handout, seminar |
| 핫스팟 | WARN | interim, final, briefing |
| 민감도 | WARN | final |
| 인증·검증 경로 | WARN | proposal, kickoff, final |

### `climate_risk` 기후리스크·시나리오 (별칭: risk, tcfd_risk)

독자 질문: 어떤 시나리오에서 어느 사업장·사업이 얼마나 영향을 받는가. 근거: v16 §3 climate_risk.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 시나리오 정의 | ERROR | 전체 |
| 리스크 목록·평가 기준 | WARN | kickoff, diagnosis, interim, final, lecture, handout, seminar |
| 영향 평가(히트맵) | WARN | interim, final, briefing |
| 재무 영향 범위 | WARN | final, briefing |
| 대응 전략 | WARN | final, briefing |

### `esg_rating` ESG 평가 대응 (별칭: esg, ecovadis)

독자 질문: 평가 기준 대비 우리 근거가 무엇이 있고, 점수를 올릴 항목은 무엇인가. 근거: v16 §3 esg_rating.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 평가 체계 | ERROR | 전체 |
| 항목별 근거 매핑 | WARN | kickoff, diagnosis, interim, final |
| 갭 진단 | WARN | diagnosis, interim, final, benchmark |
| 개선 우선순위 | WARN | diagnosis, final, briefing |
| 일정 | WARN | proposal, kickoff, final |

### `climate_education` 기후·ESG 교육 (별칭: education, training)

독자 질문: 기후 상황과 제도가 어떻게 움직이며, 나와 회사는 무엇을 해야 하는가. 근거: v16 §3 climate_education.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 관측 사실 | WARN | 전체 |
| 국제 합의 | WARN | 전체 |
| 국가 목표 | WARN | 전체 |
| 제도 흐름 | WARN | 전체 |
| 산업·직무 연결 | WARN | 전체 |
| 질문·정리 | WARN | 전체 |

### `climate_tech` 기후테크·소셜벤처 (별칭: climatetech)

독자 질문: 어떤 분야에 돈이 몰리고, 국내 생태계와 기회는 무엇인가. 근거: v16 §3 climate_tech.

| 필수 내용 | 수준 | 검사하는 보고 유형 |
|---|---|---|
| 정의·분류 | WARN | 전체 |
| 투자 추이 | WARN | 전체 |
| 분야별 비중 | WARN | 전체 |
| 국내 지원 제도 | WARN | lecture, handout, seminar, insight, proposal, final, briefing |
| 사례 | WARN | 전체 |
| 리스크 | WARN | 전체 |

## 4. 사용법

```bash
# 장표 계획(outline)을 그리기 전에 검사
python3 ${SKILL_DIR}/scripts/innergen_content_check.py --outline /tmp/<deck>/outline.md --deck-type kickoff --business-type inventory
# 완성 덱(SVG) 검사 — C·G·T·O·S에 R·B·Q가 더해진다
python3 ${SKILL_DIR}/scripts/innergen_qaqc.py /tmp/<deck> --deck-type kickoff --business-type inventory --family innergen_business
# 유형 목록
python3 ${SKILL_DIR}/scripts/innergen_content_check.py --list
```

계획표는 `| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 |` 다섯 열의 Markdown 표(첫 열이 쪽 번호인 행만 읽음)나 `[{page, layout, title, governing, body}]` JSON이다. `design_spec.md`에 `deck_type`(또는 `innergen_report_type`)과 `innergen_business_type`을 적어 두면 `innergen_qaqc.py`가 인자 없이 읽는다.

키워드 판정의 한계: 정규식은 단어가 있는지만 본다. 내용이 맞는지(수치가 옳은지, 기한이 현실적인지)는 사람이 본다. 키워드가 다른 말로 쓰여 놓치는 경우가 있으면 JSON의 해당 정규식에 그 말을 더한다.
