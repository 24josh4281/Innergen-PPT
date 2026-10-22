# 보고 단계별 구조화 도표와 레퍼런스 개선 기록 v30

2026-10-21 사용자 요청을 반영한다. [기계용 기준](report-diagrams-v30.json)은
착수·중간·최종의 수행일정·추진절차·세부현황·수행범위를 작성할 때 사용한다.
현재 자료·확정 목차·장수·디자인 잠금값과 선택한 실행 경로를 유지한다.
도표 네 종류를 무조건 네 장으로 늘리지 않는다. 필요한 내용을 합치거나 나누되
정보의 관계와 단계별 판단 기준을 보존한다.

## 1. 보고 단계와 도표 선택

| 주제 | 착수 | 중간 | 최종 |
|---|---|---|---|
| 수행일정 | 과업별 계획·자료 제출·검토 마일스톤 | 기준일과 계획·실적·전망, 지연과 회복 조치 | 계획 대비 실제 완료, 변경 사유와 잔여 조치 |
| 추진절차 | 단계 구역·복수 작업 상자·선후 연결 | 완료·진행·대기 위치와 재작업·다음 단계 | 실제 수행 절차·검증·시정·인계 |
| 세부현황 | 확보 자료·미확정·자료 요청 | 과업별 실적·근거·잠정 결과·이슈·결정 | 산출물 버전·검증 결과·한계·잔여 과제 |
| 수행범위 | 대상·기간·포함·제외·인수 기준 | 합의 범위 대비 변경·승인·미수행 | 승인 범위 대비 완료·부분완료·제외·인계 |

내용 생성은 원문 과업 분해부터 시작한다. 과업 ID를 부여하고 활동·입력·담당·기간·
산출물·검토 조건을 대응시킨다. 이후 시간은 간트, 선후는 단계도, 포함은 구조도,
현황 비교는 매트릭스로 표현한다. 정보가 없으면 항목을 만들어 채우지 말고 미확정과
자료 요청으로 남긴다. 활동명만 나열한 카드에 화살표를 붙이는 것으로 절차를 완성하지 않는다.

사용자가 2026-10-21 제공한 `CDP/추진절차.pptx`를 직접 렌더해 확인한 추진절차의
핵심은 **상위 단계 구역, 단계별 여러 작업 상자, 세로 화살표와 구역 간 직각 연결선**이다.
이를 카드 여러 개에 본문을 채우는 도표와 구분한다. 단계 제목·작업 상자·연결 관계를
구조화해 생성하고, 실제 업무의 분기·되돌림은 조건과 함께 표기한다. 참조 파일의 고객
로고·문장·수치·일정은 새 사업 사실로 가져오지 않는다.

단계의 상세 명세에는 목적·입력·활동·산출물·담당·검토 조건을 대응시킨다.
상위 단계 띠와 하위 활동의 정렬, 과업군과 일정 행의 대응, 범위와 절차의 병렬 배치는
레퍼런스에서 확인한 구성이다. 계열별 색·글꼴·여백은 현재 명세를 따른다.
복잡하면 상세 장이나 부록으로 나누고, 내용을 줄이거나 글꼴을 임의로 축소하지 않는다.

진행률은 분모·가중치·기준일이 있을 때만 사용한다. 미확인은 미이행이나 0%가 아니다.
계획·실적·전망과 제출·검토·승인은 다른 상태로 표시한다. 색에 상태 의미를 맡기지
말고 문자와 범례를 함께 쓴다. 날짜·단위·범위·근거와 담당·기한을 대조한다.

## 2. 레퍼런스 중심의 반복 개선

모델 가중치를 재학습하는 기능이 아니라, 확인한 레퍼런스 구조와 산출물 피드백을
파일로 남겨 다음 작업에서 다시 사용하는 절차다. 자동 예약·외부 업로드를 만들지 않는다.

1. `report_reference_learning.py scan`으로 파일 SHA256와 슬라이드 위치, 도형·표·연결선
   개수를 색인한다. 바뀌지 않은 파일은 다시 분석하지 않는다. 잠금 파일 `~$`는 제외한다.
2. 주제와 보고 단계에 맞는 후보 1~3쪽을 고른다. 원본 페이지나 기존 렌더를 읽고
   구조·정보 순서·밀도·정렬을 관찰한다. XML 키워드 후보와 실제 이미지 검토를 구분한다.
3. 프로젝트 `analysis/report_reference_review.json`에 소스 SHA256·쪽, 관찰한 관계,
   현재 과업에 적용할 구조·변경 이유를 기록한다. 고객 문장·수치·로고는 옮기지 않는다.
4. 대표 장표 1쪽을 먼저 작성·검증하고, 통과한 구성을 같은 관계의 장표에 적용한다.
   전체 필수 검수는 선택한 실행 경로가 담당한다.
5. 사용자의 실제 피드백이나 렌더 결함이 있을 때만 `record`로 전후 파일과 개선점을
   기록한다. 기록을 다음 프로젝트에서 검토하되 특정 프로젝트의 문구·숫자를 규칙으로
   일반화하지 않는다. 오류가 없으면 의무적으로 반복 생성하지 않는다.

색인은 디자인 품질·내용 해석·계산 검증의 증거가 아니다. 기준 JSON의 레퍼런스 ID는
[원본 목록](source-manifest.json)에 연결된다. 원본에 중간보고로 직접 명명된 덱이 없고,
감축 방법론 개발 보고서를 최종보고로 단정할 수 없으므로 해당 구성은 제안으로 표시한다.

```powershell
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/report_reference_learning.py scan --root "INPUTS/이너젠 PPT 장표 레퍼런스" --output OUTPUTS/report-reference-learning-v30/index.json
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/report_reference_learning.py record projects/example/analysis/report_reference_review.json --ledger OUTPUTS/report-reference-learning-v30/reviews.jsonl
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/report_reference_learning.py recall --ledger OUTPUTS/report-reference-learning-v30/reviews.jsonl --subject schedule
```

검토 기록에는 `source`, `source_sha256`, `slide`, `subject`, `observation`,
`adaptation`, `before`, `after`, `result`, `feedback`을 쓴다. `before`·`after`는 실제로
확인한 파일 경로다. `result`는 `improved`, `unchanged`, `unresolved` 중 하나이며,
기록 도구가 검토 자체를 대신하지 않는다. 경로는 저장소 루트 기준이다.
`recall`은 해당 주제의 최근 검토 중 원본과 개선 후 파일의 해시가 유지된 기록만
반환한다. 오래되거나 사라진 증거는 재사용 후보에서 제외하고 그 개수를 알린다.
미해결 기록도 보존하여 같은 실패를 성공 사례로 반복 적용하지 않게 한다.

## 3. 감축사업의 편집 가능한 수식

시나리오는 베이스라인·사업·누출의 해당 여부와 감축량을 구분하고, 각 식에 방법론의
판본·절·수식 번호를 연결한다. `ER = BE − PE − LE` 같은 일반 예시를 모든 사업에
적용되는 산식으로 확정하지 않는다. 누출을 0으로 놓으려면 적용 근거가 필요하다.

모니터링 인자는 기호·정의·단위·경계·기간·출처·방법·주기·담당·QA/QC·결측 처리와
사용 수식 ID를 대응시킨다. 고정값과 실측값, 산출값을 구분한다. 원문에 없는 계수·
진행률·검교정 주기·허용 오차를 생성하지 않는다.

Word는 `m:oMath`, PowerPoint는 `a14:m` 안의 `m:oMath`를 사용한다.
아래첨자·위첨자·분수·합계와 인자 기호가 수식 편집 대상으로 남아야 한다.
그림·일반 텍스트·윤곽선으로만 만든 식을 편집 가능한 수식으로 보고하지 않는다.
두 파일은 같은 수식 원문을 사용하고 식별자별 구조·기호·괄호·인자·단위 대응을
대조한다. 수식 객체 존재, Office에서의 렌더·편집, 계산·방법론의 정확성은 각각
검증 상태를 기록한다. 구조 검사를 실제 Office 편집 확인으로 표시하지 않는다.

Office 수식의 PPT 포장 방식은 [Microsoft Office Math 명세](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-odrawxml/38b13e1f-1102-4bb7-819a-dd5d9abdb176)를 따른다.
수식 전용 글꼴은 본문 글꼴과 별도 확인한다. 편집 지원 도구가 없는 실행 환경에서는
수식 원문과 미검증 사유를 보존하고 편집 요건을 충족했다고 선언하지 않는다.

현재 작업 폴더의 수식 실행 도구는 `scripts/omml_math.py`와
`scripts/office_equations.py`다. 감축사업의 같은 JSON 명세에서 Word를 작성하고,
PPT의 전용 수식·인자 슬롯을 치환한다. SVG 경로는 `data-pptx-equation`에 수식 원문을
담고 페이지에 미리보기 내용을 함께 작성한다. 슬롯 치환·수식 포장은 해당 경로의
산출 단계에서 수행하며 원본 또는 기존 내보내기 파일에 덮어쓰지 않는다.

```powershell
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py docx <현재사업_수식명세.json> -o <새버전.docx>
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py inject-pptx <수식슬롯이_있는_작업본.pptx> <현재사업_수식명세.json> -o <새버전.pptx>
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py verify <새버전.docx>
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py verify <새버전.pptx>
```

방법론·사업계획서 Word는 두 방식으로 만든다. 새로 쓰는 문서는 `docx --kind methodology`
또는 `--kind business_plan`으로 장 구성(개요 표, 산정식, 연도별 예상 감축량 표, 모니터링
인자 표)을 만들고, 비어 있는 칸은 회색 `(입력)`·`(작성: …)`으로 남긴다. 장 구성은 일반적인
상쇄 방법론·사업계획서 순서이므로 제출 전 해당 제도의 공식 서식과 대조한다. 예상 감축량
값은 명세에 적은 값만 넣고 계산하지 않는다. `example --kind <종류>`가 명세 틀을 출력한다.

이미 작성 중인 Word 초안은 `inject-docx`로 처리한다. 수식 자리에 `{{eq:식ID}}`(단독 문단은
번호 붙은 수식, 문장 안은 인라인), `{{sym:인자ID}}`, `{{where:시나리오ID}}`(여기서 목록),
`{{monitoring}}`·`{{fixed}}`(인자 표), `$$LaTeX$$`, `$LaTeX$`를 적는다. `--convert-plain`은
Word 아래첨자로 입력한 기존 텍스트 수식(예: `ERy = BEy − PEy (식 3)`)과 문장 속 기호(`BEy`)도
변환한다. CO2·CH4 같은 화학식은 텍스트로 둔다. 번호는 문서의 `(식 n)` 형식을 이어 붙인다.
나머지 문단·스타일·표·그림은 바꾸지 않고, 원본이 아닌 새 파일에만 저장한다.

```powershell
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py example --kind business_plan > <사업_수식명세.json>
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py docx <사업_수식명세.json> -o <사업계획서_v1.docx>
.venv/Scripts/python.exe .claude/skills/ppt-master/scripts/office_equations.py inject-docx <방법론_초안.docx> [<수식명세.json>] -o <방법론_수식_v1.docx> --convert-plain
```

`verify`의 객체 개수·일반 텍스트 탐지는 수식별 원문 일치 검사를 대신하지 않는다.
특히 `--expect`를 사용하더라도 누락한 식과 중복된 다른 식이 상쇄되지 않는지 별도로
대조한다. 이 문서와 작성 계획의 수식 규칙은 유지하되, 동시 작업 중인 수식 구현 파일은
덮어쓰지 않고 현재 도구의 도움말·실행 결과를 확인하여 사용한다.

## 4. 실행 연결과 한계

`consulting_structure.py`의 기존 v19 계획에는 `report_diagram_contract`와 감축사업의
`reduction_editability_contract`가 추가된다. 기준 파일은 계획 해시에 포함되어 오래된
계획을 감지한다. 이 파일은 콘텐츠·도표 선택 지침이며 페이지 생성기나 템플릿 자동
설치 기능이 아니다. 원본 PPTX 채움은 원본 레이아웃 안에서 표현 가능한 구성을 고르고,
새 도표가 필요하면 현재 경로의 지원 범위를 설명한다. 다른 경로의 검수·승인 단계를
가져오지 않는다. Word 제작 시에도 수식 요건을 적용하며 문서 자체 검수를 유지한다.

## 5. 도표 생성기 `report_diagrams.py`

보고 단계 도표 5종을 계열 크롬(`03a_content.svg`) 안에 바로 그리는 생성기다. 데이터 JSON의
`stage`(kickoff·interim·final)와 계열(`innergen_business`·`innergen_lecture`·`innercarry`)에 맞춰
글자 크기 사다리·색·행 높이를 정하고, 결과 SVG는 일반 SVG 경로로 내보낸다.

| 종류 | 구성 | 단계별 표현 |
|---|---|---|
| `schedule` | 과업군·세부 과업 간트, 월·반월·주 단위, 비고·산출물 열, 하단 보고 행 | 착수=계획 막대, 중간=계획 윤곽+실적 채움+기준일 선, 지연·보완은 붉은색 |
| `procedure` | 단계 셰브론, 주체별 레인, 노드 격자와 꺾은 연결선, 산출물 행 | `current_phase`·`this_report_phase`로 이번 보고 범위 표시 |
| `status` | 과업·진행 현황·향후 계획 열 + 상태어(완료·진행 중·예정·보완·지연), 요청 띠 | 중간·최종 보고 |
| `issues` | 이슈·영향·조치·요청·기한·상태 열 | 중간 보고 |
| `scope` | `modules`(모듈+산출물·기한) · `matrix`(포함·선택·제외+범위 밖) · `deliverables`(산출물 6칸) | 착수·최종 보고 |

```bash
python3 .claude/skills/ppt-master/scripts/report_diagrams.py example schedule > data.json
python3 .claude/skills/ppt-master/scripts/report_diagrams.py check data.json
python3 .claude/skills/ppt-master/scripts/report_diagrams.py build data.json --family innergen_business -o svg_output/05_schedule.svg
```

`check`는 날짜 형식, 기간 밖 막대, 23행 초과, 착수·최종 보고 행 누락, 중간 보고의 기준일 누락,
진척률 숫자(`progress_pct`, 근거 없는 %를 막기 위해 금지), 강조 2개 초과, 단계와 맞지 않는
거버닝 시제를 막는다. `build --mode auto`는 프로젝트 `spec_lock.md`의
`pptx_structure.mode`를 읽어 flat이면 구조 속성을 제거한다. 생성 SVG도 `svg_quality_checker.py`와
`innergen_qaqc.py`를 그대로 통과해야 하며, 렌더 검토(글자 겹침·막대 위치)는 생략하지 않는다.
