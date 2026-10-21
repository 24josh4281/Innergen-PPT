# 컨설팅 도식 v27 참조 자료와 적용 기록 (2026-10-15)

구조화 장표 s59–s64를 만들 때 확인한 공개 자료다. 확인일은 모두 2026-10-15이고, 각 회사의 공식 사이트(또는 공동 발간 기관 사이트)에 공개된 페이지만 썼다. 원문 문구·수치·로고·도식 이미지는 옮기지 않았고, 견본의 회사·수치는 모두 가상이다. "확인한 내용"은 페이지 본문에서 직접 읽은 것만 적었고, 본문에 없어 이너젠이 정한 부분은 "이너젠 설계"로 따로 적었다.

v24(s43–s58)·v25 참조 기록은 [structured-slides-v18.md §3c](structured-slides-v18.md)와 `OUTPUTS/consulting-reference-upgrade-v25/참조자료_적용기록.md`에 있다.

| 구조 | 회사 | 자료 | 발행 |
|---|---|---|---|
| s59 가치사슬 핫스팟 | McKinsey | [Enduring Ideas: The business system](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/enduring-ideas-the-business-system) | 2009-06-01 |
| s59 가치사슬 핫스팟 | BCG · WEF | [Net-Zero Challenge: The supply chain opportunity](https://www.weforum.org/publications/net-zero-challenge-the-supply-chain-opportunity/) · [BCG 해설](https://www.bcg.com/publications/2021/fighting-climate-change-with-supply-chain-decarbonization) | 2021-01 |
| s60 프로핏 풀 | Bain | [Profit pools: A fresh look at strategy](https://www.bain.com/insights/profit-pools-a-fresh-look-at-strategy/) · [How to map your industry's profit pool](https://www.bain.com/insights/how-to-map-your-industrys-profit-pool/) | 1998-05-01 |
| s61 학습곡선 | BCG | [The Experience Curve](https://www.bcg.com/publications/1968/business-unit-strategy-growth-experience-curve) | 1968-01-01 |
| s62 민감도 토네이도 | KPMG | [Climate scenario analysis](https://kpmg.com/uk/en/home/insights/2023/05/climate-scenario-analysis.html) | 2023-05(URL 기준, 본문 날짜 없음) |
| s63 스윔레인 통제 | Deloitte | [Using the COSO Framework to Establish Internal Controls Over Sustainability Reporting](https://dart.deloitte.com/USDART/home/publications/deloitte/heads-up/2023/coso-framework-for-internal-controls-over-sustainability) | 2023-04-21 |
| s63 스윔레인 통제 | EY | [지속가능성 보고 통제 안내(PDF)](https://www.ey.com/content/dam/ey-unified-site/ey-com/es-es/insights/rethinking-sustainability/documents/ey-sust-reporting-controls.pdf) | 2025-12(v25에서 확인) |
| s64 7-S 정합성 | McKinsey | [Enduring Ideas: The 7-S Framework](https://www.mckinsey.com/capabilities/strategy-and-corporate-finance/our-insights/enduring-ideas-the-7-s-framework) · [How to create an effective operating model](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/a-new-operating-model-for-a-new-world) | 2008-03-01 · 2025-06-18 |

## s59 · 가치사슬 단계별 핫스팟

- 확인한 내용: McKinsey 비즈니스 시스템은 제품 개발부터 고객 서비스까지 회사가 가치를 만들고 전달하는 단계를 늘어놓고, 단계마다 "지금 어떻게 하는가, 더 나은 방법이 있는가, 경쟁사는 어떻게 하는가"를 묻는다. 단계 수는 고정돼 있지 않다. WEF·BCG 보고서는 공급망(가치사슬) 단위로 배출을 나눠 감축 기회를 찾는다.
- 이너젠 설계: 단계 5개 셰브론, 단계별 배출 비중 막대, "주요 활동·개선 기회" 두 행, 핫스팟 점선 1곳, 시사점 바.

## s60 · 가변폭 막대(프로핏 풀)

- 확인한 내용: Bain(Gadiesh·Gilbert, HBR 1998)은 산업 전체 이익이 가치사슬·구간별로 어떻게 나뉘는지 보는 "프로핏 풀" 관점을 제시한다.
- 확인하지 못한 내용: 두 Bain 페이지 본문에는 도식의 축 정의(가로축·세로축·막대 폭의 의미)가 글로 적혀 있지 않다. 원문 도표는 확인하지 않았다.
- 이너젠 설계: 막대 폭 = 매출·물량 비중(합 100%), 높이 = 이익률 또는 배출 집약도. 축의 의미를 `AXIS_X`·`AXIS_Y`에 반드시 적게 했다.

## s61 · 학습곡선

- 확인한 내용: BCG(Bruce Henderson, 1968)는 "누적 경험이 두 배가 될 때마다 비용이 일정 비율 내려간다"고 쓰고, 그 폭을 대개 20–30%로 든다. 비용에는 R&D·영업·간접비까지 포함해야 한다고 적는다.
- 확인하지 못한 내용: 페이지 본문에는 축과 로그 눈금이 적혀 있지 않다.
- 이너젠 설계: 두 축 로그 눈금, 점(실측)+추세선, 학습률·배증 횟수·예상 단가의 핵심 수치 3칸, 함의 칸. 견본의 학습률 18%는 가상 값이다.

## s62 · 민감도 토네이도

- 확인한 내용: KPMG는 시나리오의 점 추정이 불확실성을 가린다고 지적하고, 시나리오 안의 확률을 바꿔 보는 민감도 분석과 극단값 민감도 분석을 권한다. 금리·물가·자산가격 같은 동인과 기술·정책 가정을 바꿔 보라고 적는다.
- 확인하지 못한 내용: 페이지에 토네이도 차트라는 도식 형식은 나오지 않는다.
- 이너젠 설계: 가정 6행, 기준선 좌우로 하한·상한 막대, 범위 열, 기준 시나리오 메모, 결론 바. 범위가 큰 순서로 정렬한다.

## s63 · 스윔레인 프로세스+통제 지점

- 확인한 내용: Deloitte는 COSO 내부통제 체계를 지속가능성 보고에 적용할 때 흐름도·표준 운영 절차·위험통제매트릭스로 프로세스 통제를 문서화하고, 프로세스 책임자의 역할을 분명히 하라고 쓴다. EY 안내는 근거·검토·승인 추적을 다룬다(v25에서 확인).
- 이너젠 설계: 주체 4개 레인 × 단계 5개, 활동 상자와 연결선, 통제 표식 C1–C3와 아래 설명 칸.

## s64 · 7-S 정합성 진단

- 확인한 내용: McKinsey 7-S(1970년대 말 도입)는 조직 효과성에서 구조보다 "조정"을 중시하며, 요소들이 서로 얽혀 위계가 없으므로 한 요소만 바꾸기 어렵다고 설명한다(2008). 2025년 운영모델 글은 일곱 요소를 shared values, strategy, structure, systems, style, skills, staff로 적는다.
- 이너젠 설계: 공유가치를 가운데 둔 연결망, 하드(전략·구조·시스템)·소프트(스타일·인력·역량) 색 구분, 요소별 현재 상태와 정합 판단(정합/보완/충돌) 표, 강조 행 1개. 하드·소프트 구분은 널리 쓰이는 분류이며 위 두 페이지 본문에서는 확인하지 않았다.

## 접근 한계

- 원문 PDF·도표 이미지는 내려받거나 배포하지 않았다. WEF 보고서 PDF 본문은 이번에 열어 보지 않았고, 발간 페이지와 BCG 해설 제목까지만 확인했다.
- KPMG 페이지에는 본문 발행일이 없다. URL의 `2023/05`를 발행 시점으로 적었다.
