# 이너젠 근거·차트·구조 장표 규칙 v16 (2026-10-13)

[프로필 매트릭스 v16](innergen-profile-matrix-v16.md)에서 정한 업무·단계·전달 방식에 맞춰 **어떤 차트·구조 장표를 쓰고, 어떤 기관의 자료를 어떻게 인용하는지** 정한다. 차트 유형의 상세 계약(데이터 형태·인코딩·금지 변형)은 [v14](design-contracts-v14.md)와 [전체 JSON](design-contracts-v14.json), 구조 사전은 [v12](design-body-v12.md)를 따른다. 이 문서는 그 위에서 선택 순서와 이너젠 화면 적용값을 정한다.

## 1. 선택 순서

1. 장표가 답할 **독자 질문**을 한 문장으로 쓴다("2035년까지 감축 경로는 어떤가?").
2. 질문 유형으로 차트·구조를 고른다(§2). 데이터 형태가 맞지 않으면 그다음 후보로 내려간다.
3. 데이터를 **1차 기관 자료**에서 가져오고(§4), 값·단위·기준연도를 기록한다.
4. 이너젠 색·글자 규칙(§3)으로 편집 가능한 차트를 그린다.
5. 거버닝에 차트가 말하는 결론, 출처 줄에 근거를 쓴다.

장식용 차트는 만들지 않는다. 숫자가 2–3개뿐이면 차트 대신 수치 타일(`03f_content_kpi`)이나 표를 쓴다.

## 2. 질문 → 차트·구조 대응표

`charts/` 열은 `.claude/skills/ppt-master/templates/charts/`의 참고 SVG다. 그대로 복사하지 않고 구조만 참고해 이너젠 색·글자로 다시 그린다.

### 2.1 수치 차트

| 독자 질문 | v14 ID | charts/ | 이너젠 적용 예 |
|---|---|---|---|
| 무엇이 가장 큰가, 순위는 | CH01 가로 막대 | `horizontal_bar_chart.svg` | 국가별 배출량, 부문별 투자, 감축 수단별 감축량 |
| 소수 범주 크기 비교 | CH02 세로 막대 | `column_chart.svg` | 연도별 투자액(5–8개 연도) |
| 범주 안 계열 비교 | CH03 묶은 막대 | `grouped_bar_chart.svg` | 전년 vs 올해 평가 점수 |
| 전체와 구성의 절대량 | CH04 누적 막대 | `stacked_bar_chart.svg` | 연도별 Scope 1·2·3, 부문별 국가 배출 |
| 같은 전체 안 구성비 | CH05 100% 누적 | `stacked_bar_chart.svg` | 제품 생애주기 단계별 비중 |
| 시간 추이 | CH06 선 | `line_chart.svg` | 기온 편차, CO₂ 농도, 배출권 가격 |
| 시간별 규모 | CH07 면적 | `area_chart.svg` | 누적 설치 용량 |
| 시간별 전체와 구성 | CH08 누적 면적 | `stacked_area_chart.svg` | 에너지원별 발전량 |
| 한 시점 구성 | CH09 도넛 | `donut_chart.svg` | 올해 Scope 3 카테고리 구성(6개 이하) |
| 시작→종료 증감 요인 | CH10 워터폴 | `waterfall_chart.svg` | 기준연도→목표연도 감축 수단별 기여, 전년 대비 증감 요인 |
| 범위·불확실성 | CH11 하한·상한 | `dumbbell_chart.svg` | 국가 목표 53–61%, 재무 영향 범위 |
| 분포 | CH12·CH13 | `histogram_chart.svg`, `box_plot_chart.svg` | 사업장별 원단위 분포 |
| 두 변수 관계 | CH14 산점도 | `scatter_chart.svg` | 매출 vs 배출량 |
| 두 변수 + 규모 | CH15 버블 | `bubble_chart.svg` | 감축비용 vs 감축량(버블=투자액) |
| 입력 변화의 영향 | CH16 토네이도 | `butterfly_chart.svg` | LCA 민감도, 탄소가격 민감도 |
| 시나리오별 경로 | CH17 시나리오 선 | `line_chart.svg` | BAU / 목표 / 1.5°C 경로 |
| 행×열 값 차이 | CH18 히트맵 | `heatmap_chart.svg` | 사업장×리스크 유형, 공시 항목×준비도 |
| 같은 기준의 여러 패널 | CH19 스몰멀티플 | `line_chart.svg` ×N | 국가별 탄소가격 추이 |
| 단위가 다른 두 추이 | CH20 이중축 | `dual_axis_line_chart.svg` | 배출량(막대) + 원단위(선) |
| 목표 대비 실적 | — | `bullet_chart.svg`, `progress_bar_chart.svg` | 감축 목표 달성률, 프로젝트 진행률 |
| 흐름의 양 | — | `sankey_chart.svg` | 에너지 투입 → 배출원 → Scope |
| 위계 구성 | — | `treemap_chart.svg` | 기후테크 분야별 투자 비중 |

### 2.2 구조 장표

| 장표 목적 | v14 RCP | charts/ | 이너젠 소개자료 레이아웃 |
|---|---|---|---|
| 개념 관계·정의 | RCP01 | `concentric_circles.svg`, `mind_map.svg` | 03c |
| 규칙·조건·예외 | RCP02 | `feature_matrix_table.svg` | 03e |
| 판단 → 후속 조치 | RCP03 | `top_down_tree.svg` | 03a |
| 요구사항 → 사례 → 적용 | RCP05 | `comparison_columns.svg` | 03d |
| 기간별 비교·영향 경로 | RCP06 | `timeline.svg` | 03a |
| 경계 비교(Scope, 조직/운영) | RCP07 | `venn_diagram.svg`, `layered_architecture.svg` | 03c |
| 수치 + 해설 + 측정 기준 | RCP09 | 차트 + 해설 | 03c |
| 실적·목표·전망 구분 | RCP10 | `line_chart.svg`(실선/점선) | 03e |
| 업무분해 + 데이터 요청 | RCP11 | `consulting_table.svg` | 03e |
| 계산 워크스루 | RCP12 | `numbered_steps.svg` | 03g |
| 긴 절차: 전체 + 세부 | RCP13 | `chevron_process.svg`, `process_flow.svg` | 03g |
| 질문·답·근거 | RCP14 | `quadrant_text_bullets.svg` | 03b |
| 적용 시기표 | RCP16 | `gantt_chart.svg`, `project_schedule_table.svg` | 03e |
| 진단·근거·운영·개선 | RCP17 | `harvey_balls_table.svg` | 03e |
| 모델 결과 + 전제 + 범위 | RCP19 | 차트 + 전제 카드 | 03c |
| 벤치마크 | RCP20 | `horizontal_bar_chart.svg` | 03e |
| 반복 보고(현재·다음·결정) | RCP21 | `comparison_columns.svg` | 03d |
| 평가기준·근거·의견 | RCP23 | `consulting_table.svg` | 03e |
| 우선순위 판단 | — | `matrix_2x2.svg` | 03c |
| 로드맵 | — | `roadmap_vertical.svg`, `timeline.svg` | 03a |
| 수행 체계 | — | `team_roster.svg`, `top_down_tree.svg` | 03d |

## 3. 이너젠 차트 화면 규칙

| 항목 | 이너젠 소개자료(v4.2 블루) | 이너젠 보고서 | 이너캐리 |
|---|---|---|---|
| 1순위 계열 | `#2F62F0` | `#0F243F` | `#2F62F0` |
| 2순위 계열 | `#7B9BF7` | `#808080` | `#7B9BF7` |
| 비교·과거·기타 | `#94A3B8` | `#BFBFBF` | `#94A3B8` |
| 강조 값 | `#0B1739` Bold 라벨 | 검정 Bold | `#0B1739` Bold |
| 위험·미달 | `#FF0000` (값 하나에만) | `#FF0000` | `#991B1B` |
| 표 머리글 | `#0B1739` 바탕 흰 글자 | `#F2F2F2` 바탕 검정 글자 | `#EEF2FF` 바탕 남색 글자 |
| 격자선 | `#E2E8F0` 가로선만 | `#BFBFBF` 가로선만 | `#E2E8F0` |

- 계열은 4개까지. 넘으면 상위 3개 + "기타"로 묶거나 스몰멀티플로 나눈다.
- 막대 차트는 0에서 시작. 선 차트는 축을 자를 수 있으나 축 값에 표시한다.
- 범례보다 **직접 라벨**을 우선한다(선 끝, 막대 끝에 값).
- 단위는 축 제목 또는 차트 제목 끝 괄호에 쓴다: `(백만 tCO₂eq)`, `(원/tCO₂eq)`, `(°C, 1850–1900년 대비)`.
- 실적은 실선·진한 색, 목표·전망은 점선·연한 색으로 구분하고 범례에 "목표", "전망"을 쓴다.
- 강조할 막대 하나만 1순위 색, 나머지는 회색 계열로 두면 메시지가 빨리 읽힌다.
- 차트 안 글자 16px 이상, 데이터 라벨 18px 권장.
- 차트는 편집 가능하게 만든다. PowerPoint 기본 차트 개체가 필요하면 `data-pptx-native="chart"`와 `<metadata>` JSON으로 작성하고 `--native-objects`로 내보낸다. JSON 안의 `&`는 `&amp;`로 쓴다.

## 4. 공신력 있는 출처 목록

1차 기관 자료를 우선한다. 언론 보도는 1차 자료를 찾는 단서로만 쓰고, 1차 자료를 찾지 못하면 장표에 "보도 기준"이라고 쓴다.

### 4.1 기후 과학·배출

| 기관 | 대표 자료 | 쓰는 수치 | 주기 |
|---|---|---|---|
| IPCC | AR6 종합보고서(SYR), WG1–3 SPM | 탄소예산, 감축 경로, 위험 수준 | 약 6–7년(AR7 진행 중) |
| WMO | State of the Global Climate, Global Annual to Decadal Climate Update | 연 평균기온 편차, 1.5°C 초과 확률 | 매년 |
| NOAA GML | Mauna Loa CO₂ 월·연 평균 | CO₂ 농도(ppm) | 매월 |
| Copernicus C3S | Global Climate Highlights | 연·월 기온 편차 | 매년·매월 |
| UNEP | Emissions Gap Report | 국가 감축목표와 1.5/2°C 경로 격차 | 매년 |
| Global Carbon Project | Global Carbon Budget | 화석연료 CO₂ 배출, 잔여 탄소예산 | 매년 |
| 온실가스종합정보센터(GIR) | 국가 온실가스 인벤토리 보고서, 잠정 배출량 | 한국 총배출·부문별 배출 | 매년 |

### 4.2 정책·제도·탄소가격

| 기관 | 대표 자료 | 쓰는 수치 |
|---|---|---|
| UNFCCC | NDC 등록부, COP 결정문, 6.4조 감독기구 | 국가 목표, 국제 합의 일정, 6.4조 크레딧 |
| 기후에너지환경부·국가법령정보센터 | 탄소중립기본법·배출권거래법 및 시행령, 배출권 할당계획 | 국가 목표, 할당량, 의무 대상 |
| 한국거래소(KRX) 배출권시장 | 시장 일별 통계 | KAU·KCU·KOC 가격·거래량 |
| 세계은행 | State and Trends of Carbon Pricing | 탄소가격제 수, 배출 비중, 수입 |
| ICAP | Emissions Trading Worldwide: Status Report | 운영 중인 ETS 수, 가격 |
| EU 집행위원회 | CBAM·EU ETS·CSRD/옴니버스 공식 문서 | 적용 일정, 대상, 가격 |
| 금융위원회·KSSB | 지속가능성 공시 로드맵, 공시기준서 | 의무화 시점·대상 |
| ISSB(IFRS 재단) | IFRS S1·S2, 관할권 채택 현황 | 공시 요구사항 |

### 4.3 에너지·투자·시장

| 기관 | 대표 자료 | 쓰는 수치 |
|---|---|---|
| IEA | World Energy Outlook, World Energy Investment, Global Energy Review | 에너지 투자, 시나리오(STEPS·APS·NZE), 재생에너지 용량 |
| BNEF | Energy Transition Investment Trends | 연간 에너지전환 투자, 부문·국가별 |
| IRENA | Renewable Capacity Statistics, Renewable Power Generation Costs | 재생에너지 용량, 균등화 발전비용 |
| NGFS | 기후 시나리오 | 전환·물리 리스크 시나리오 |
| CDP | 연간 결과·채점 방법론 | 공시 기업 수, 등급 기준 |
| SBTi | Target Dashboard, 기업 넷제로 기준 | 목표 승인 기업 수, 기준 요건 |
| 중소벤처기업부·사회적기업진흥원 | 벤처·소셜벤처 실태조사 | 국내 소셜벤처 수·매출·투자 |

### 4.4 인용 형식

| 위치 | 형식 | 예 |
|---|---|---|
| 장표 출처 줄 | `출처: 기관, 「자료명」(발간연월), 기준연도·단위` | `출처: WMO, 「State of the Global Climate 2025」(2026.3), 1850–1900년 대비 °C` |
| 재가공 차트 | `… 를 바탕으로 이너젠 재구성` | `출처: BNEF(2026.1) 자료를 바탕으로 이너젠 재구성` |
| 여러 출처 | 세미콜론으로 구분, 2개까지 장표에, 나머지는 부록 | `출처: NOAA GML(2026.6); Copernicus C3S(2026.1)` |
| 잠정·전망 | 수치 옆에 `(잠정)`, `(전망)`, `(목표)` | `6억 8,571만 톤(2025, 잠정)` |
| 보도 기준 | 1차 자료를 못 찾은 경우 | `출처: ○○일보(2026.9.12) 보도 기준` |

### 4.5 데이터 처리 규칙

- 값은 원 자료의 단위·정밀도를 유지한다. 단위를 바꾸면 원값·식·결과를 프로젝트 노트에 남긴다.
- 출처마다 수치가 다르면 기준(연도·경계·방법) 차이를 먼저 확인하고, 해결되지 않으면 범위로 쓰고 결과 보고의 "확인 필요" 목록에 넣는다.
- 결측값을 0으로 쓰지 않는다. 빈칸 + 각주로 표시한다.
- 오래된 참고 자료의 제도·일정을 최신으로 단정하지 않는다. 작성일 기준 최신 공식 자료를 다시 확인하고 기준일을 쓴다.
- 원 보고서 그림을 캡처할 때는 데이터가 공개되지 않은 경우에 한하고, 그림 번호까지 출처에 쓴다(`IPCC AR6 SYR SPM Figure SPM.1`). 데이터가 공개되어 있으면 다시 그린다.
- 이전 고객의 배출량·매출·로고는 근거 자료가 아니다. 현재 프로젝트에서 받은 자료만 쓴다.

## 5. 업무별 기본 차트 세트

한 덱에 같은 질문이 반복되면 같은 차트 유형·색·축을 유지한다.

| 업무 | 기본 세트 |
|---|---|
| CDP·기후공시 | 점수 추이(CH06) · 항목×준비도 히트맵(CH18) · 진단표(RCP17) · 보완 일정(간트) |
| 규제 대응 | 적용 시기표(RCP16) · 가격 추이(CH06) · 대상 판단도(RCP03) · 비용 영향 범위(CH11) |
| 감축사업·상쇄 | 감축 워터폴(CH10) · 시나리오 경로(CH17) · 수단별 비용·감축량 버블(CH15) · 방법론 절차(RCP13) |
| 인벤토리 | Scope 누적 막대(CH04) · 증감 워터폴(CH10) · 에너지 흐름 생키 · 경계 도식(RCP07) |
| LCA·제품탄소 | 단계별 100% 누적(CH05) · 민감도 토네이도(CH16) · 시스템 경계도(RCP07) |
| 기후리스크 | 시나리오 경로(CH17) · 사업장×리스크 히트맵(CH18) · 발생가능성×영향 매트릭스 · 재무 영향 범위(CH11) |
| ESG 평가 대응 | 평가 체계 표(RCP23) · 전년 대비 묶은 막대(CH03) · 갭 하비볼 표 |
| 기후·ESG 교육 | 기온·CO₂ 추이(CH06) · 부문별 배출(CH04) · 제도 연혁(timeline) · 개념 지도(RCP01) · 질문 장표(RCP14) |
| 기후테크·소셜벤처 | 투자 추이(CH02) · 분야 비중(CH09/treemap) · 기회 매트릭스(2×2) · 사례 비교(RCP05) |
