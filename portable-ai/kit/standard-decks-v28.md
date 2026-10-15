# 표준 덱 v28 — 회사소개서 · 이너캐리 소개서 · 매번 들어가는 장표

두 원본에서 매번 반복되는 장표를 표준 목차로 묶었다. 회사소개서나 이너캐리 소개서를 만들 때는 아래 표를
`outline.md`로 복사해 시작하고, 요청에 맞게 장을 빼거나 더한다. 숫자·연락처·문구는
`company-facts-v28.md`(원본 JSON: `company-facts-v28.json`)에서만 가져온다.

- 원본: `CO260929` = (주)이너젠_회사소개자료_260929_업데이트.pptx, `IC260916` = (이너젠) 이너젠 및 이너캐리 소개 자료_260916_v4.1.pptx
- 덱 유형: `company_intro`(계열 `innergen_business`, 16:9), `innercarry_intro`(계열 `innercarry`, 4:3).
  목차·필수 내용은 `content-requirements-v28-intro.json`이 정하고 `innergen_content_check.py`·`innergen_qaqc.py`가 검사한다.
- 사업 성격(`--business-type`)은 소개서에는 필요 없다. 소개서 안에 특정 사업 제안을 붙일 때만 그 사업 성격을 준다.

## 0. 어느 계열을 쓰나

| 사용자가 말하는 것 | 계열 | 덱 유형 |
|---|---|---|
| 기본 이너젠, 교육·강의, 세미나 자료 | `innergen_lecture` | lecture · handout · seminar |
| 사업소개서, 회사소개서, 제안서, 컨설팅 보고 | `innergen_business` | company_intro · proposal · kickoff · final 등 |
| 이너캐리 소개, SaaS 소개, 도입 제안 | `innercarry` | innercarry_intro |

"소개자료"만 있으면 회사소개(`innergen_business`)인지 이너캐리 소개(`innercarry`)인지 한 번 묻는다.

## 1. 공통 블록 — 어느 덱에 넣어도 같은 내용

| 블록 | 레이아웃 | 들어갈 내용(원장 키) | 주의 |
|---|---|---|---|
| 회사 개요 | `03e_content_table` | company.name_ko · ceo · headcount · founded · address, messages.company_overview | 주요 고객은 원본 로고 이미지를 받아 넣는다. 고객사 이름을 지어내지 않는다 |
| 구성 인원 | `s27_team_roles` | messages.people_overview · people_credentials | 인물 사진·이력은 원본 장표 이미지 또는 사용자가 준 명단만 쓴다 |
| 사업 분야 5 | `s18_keyword_grid` | business_areas | 이너캐리 덱에서는 IT 부문(company.divisions)을 함께 |
| 핵심 숫자 | `03f_content_kpi` | metrics.industries · inventory_projects · methodologies · credits_recognized | `credits_recognized`는 **확인 필요**(250만 vs 300만) |
| 대외 자격·협력 | `s05_entity_matrix` | credentials | 기관 로고는 이미지 파일을 받아 쓴다 |
| CDP·공시 이력 | `s09_year_timeline` | cdp_track_record, metrics.cdp_leadership | 연도별 수상 내역은 **확인 필요** |
| 맺음·연락처 | `04_ending` | messages.closing_philosophy · closing_we_do · slogan, company.address · phone · email | 연락처는 원장 값 그대로 |

## A. 회사소개서 표준 목차 (`company_intro`, `innergen_business`)

CO260929의 흐름(회사 개요 → 구성 인원 → 사업분야 5종 → 맺음)을 따른다. 거버닝은 한 줄(공백 제외 38자 이내, v22) 초안이다. 쓰기 전에 원장 값으로 숫자를 다시 확인한다.

| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 |
|---|---|---|---|---|
| 1 | 01_cover | ㈜ 이너젠 소개자료 | 탄소를 미래자산으로 바라보고, 기업 여건에 적합한 맞춤형 솔루션을 제공합니다. | #탄소배출권 #글로벌 환경공시 #탄소발자국 #IT플랫폼, 로고 |
| 2 | 03e_content_table | 1. 회사 개요 | 이너젠은 5개 분야에 전문성을 갖춘 기후변화 컨설팅사입니다. | 회사명 ㈜이너젠, 대표자 김성은·손권빈(상근 23명), 설립일 2017년 12월 22일, 위치 서울특별시 용산구 서빙고로 17 센트럴파크타워 704호, 주요 고객 로고(이미지) |
| 3 | s27_team_roles | 2. 구성 인원 | 이너젠은 2011년부터 일한 전문인력이 분야별 업무를 전담합니다. | 온실가스 검증심사원, CDM(PACM) 심사원, LCA 검증심사원, CDP 평가위원, 인물 카드(원본 이미지) |
| 4 | s18_keyword_grid | 3. 사업 분야 | 이너젠은 규제 대응부터 RE100 조달까지 탄소 업무 전 영역을 한 팀이 지원합니다. | 규제 대응/탄소중립 전략(TMS·ETS·CBAM), 탄소배출권 자산화(규제·자발적 배출권), 제품 단위 환경성 평가(LCA·PFC·Labeling), 글로벌 환경 공시(CDP·DJSI·SBTi), RE100 전략·조달(REC·PPA) |
| 5 | 03f_content_kpi | 3-1. 규제 대응 / 탄소중립 전략 | 이너젠은 18개+ 업종 산정 실적으로 국가별 GHG 규제에 대응합니다. | 18개+ 업종, 430건+ 인벤토리 구축 및 규제대응, 30개+ 방법론 개발/승인, 250만 톤+ 감축실적 인정(확인 필요), Scope 1·2·3 인벤토리 |
| 6 | s05_entity_matrix | 3-1. 규제 대응 – 전문가·유관기관 협력 | 이너젠은 검증심사원·정부 자문위원과 최신 MRV 기준을 반영합니다. | 검증심사원 4명(검증기관 비상근), 한국에너지공단 위촉 전문가 2명, 대한상의 K-VCM 평가 사무국(2023~현재), 검증기관 협업 |
| 7 | s11_list_zoom | 3-2. 탄소배출권 자산화 – 기술 분야별 경험 | 이너젠은 에너지·냉각부터 자원순환·DAC까지 방법론을 개발했습니다. | 경험1 신규 에너지/열&냉열, 경험2 DC 냉방 에너지, 경험3 에너지/물질 효율 제품, 경험4 자원순환, 고객사명은 공개 동의 확인 |
| 8 | s14_task_structure | 3-2. 탄소시장별 지원 범위 | 이너젠은 K-VCM·G-VCM·외부사업·ITMO 배출권 발급을 지원합니다. | K-VCM(KOC 발급·활용), G-VCM(VCM Carbon Credits), 외부감축사업(기후에너지환경부), ITMO 6.2/6.4 Feasibility Study, 감축기술 인정 가능성 검토 |
| 9 | 03e_content_table | 3-2. 방법론 개발·감축실적 발급 경험 | 이너젠은 방법론 30건, 감축실적 250만 톤 발급 경험을 보유합니다. | 방법론 규제 10건·자발적 20건 완료, 감축실적 발급 규제 200만 톤·자발적 50만 톤, 주요 인정 감축사업(원본 p10 표) |
| 10 | 03d_content_dual | 3-3. 제품 단위 환경성 평가 | 이너젠 LCA Tool은 반복 컨설팅 없이 제품 탄소 성적을 갱신합니다. | SAP/ERP 업로드 방식 자동 산정, 국가별 LCI DB 분리 적용, 공급망·고객사·CBAM 대응, 구축 6개사(석유화학 H社 등) |
| 11 | s09_year_timeline | 3-4. 글로벌 환경 공시 | 이너젠은 2022년부터 매년 11–12개 기업의 CDP 대응을 수행합니다. | ’19 본부 신설, ’20 2개→’22 12개→’25 12개 기업, SBTi 고객 유치·확대·승인, CDP 12개 기업 중 5개 Leadership A(연도 확인 필요) |
| 12 | s06_principle_matrix | 3-5. RE100 전략 분석 & 조달 지원 | 이너젠은 실제 조달 경험으로 실행형 RE100 컨설팅을 제공합니다. | 경험/노하우(PPA·REC 조달, 30MW 이상 계약 PM), 파이프라인(공급·개발 Side 네트워킹), 전문성(PPA 시뮬레이션 모델링 솔루션) |
| 13 | 04_ending | We Do | 컨설팅의 본질은 고객의 여건과 니즈를 고려해 실질적인 가치를 제공하는 것입니다. | 전문 인력이 시작과 끝까지 함께, 시간·비용·Risk 절약 약속, 연락처 02-6273-0489 · innergen@inng.co.kr · (04387) 서빙고로 17 센트럴파크타워 704호 |

변형: 제안서 앞에 붙이는 짧은 회사소개는 2·4·5·13쪽(4장)만 쓴다. 특정 사업 제안이면 그 분야 상세(5–12쪽 중 해당 쪽)만 남기고 `--deck-type proposal --business-type <분야>`로 본 제안을 이어 쓴다.

## B. 이너캐리 소개서 표준 목차 (`innercarry_intro`, `innercarry`)

IC260916의 흐름(PART 00 회사소개 → PART 01 왜 지금인가 → PART 02 서비스 소개 → PART 03 왜 이너젠인가 → PART 04 도입 효과 → 도입 방식·절차 → 맺음)을 따른다.

| 쪽 | 레이아웃 | 제목 | 거버닝 | 넣을 내용 |
|---|---|---|---|---|
| 1 | 01_cover | INNerGEN / INNerCarry 소개자료 | 복잡한 탄소·환경 정보, 이너캐리가 대신 Carry 해드립니다. | ESG 공시 대응 · 온실가스(환경) 정보 · SaaS, 주식회사 이너젠 · www.inng.co.kr |
| 2 | 02b_toc_pages | 목차 | | PART 00 회사소개, PART 01 왜 지금인가, PART 02 이너캐리는 어떤 서비스인가, PART 03 왜 이너젠인가, PART 04 무엇을 얻는가 |
| 3 | 03e_content_table | 이너젠 회사 개요 | 이너젠은 온실가스 규제·공시 대응을 돕는 기후변화 컨설팅사입니다. | 회사명·대표자·인원·설립일·위치(원장), 주요 고객 로고(이미지) |
| 4 | s18_keyword_grid | 이너젠 사업 분야 | 이너젠은 컨설팅 부문 5개 분야와 IT 부문 솔루션을 함께 제공합니다. | 컨설팅 5개 분야(원장 business_areas), IT 부문: 사내망 설치형 솔루션(2019 출시), SaaS 이너캐리(출시 시점 확인 필요) |
| 5 | 02c_section_divider | PART 01 왜 지금인가 | | 서비스 필요성 |
| 6 | s09_year_timeline | 자율 공시에서 법정 공시로 | 법정공시 일정이 확정되면서 기업은 지금부터 데이터 상시 수집 체계를 갖춰야 합니다. | 과거 자율 공시 → 2026 대응 준비 → 2027 회계연도 데이터 상시 수집 → 2028 사업보고서 법정공시(시의성·출처 확인 필요, 출처: 금융위원회 원문 링크와 날짜) |
| 7 | s38_issue_cards | 법정공시가 바꾸는 세 가지 리스크 | 법정공시는 데이터 신뢰성·연결 자회사·법적 책임 세 측면에서 기업 부담을 키웁니다. | RISK 01 재무제표 수준 신뢰성·외부 감사, RISK 02 연결 자회사 동시 사정권, RISK 03 과징금·형사처벌까지 법적 리스크 |
| 8 | s19_compare_implication | 재무 ICFR 통제를 ESG 데이터에 이식 | ESG 데이터가 감사를 통과하려면 ICFR 5대 통제가 필요합니다. | 데이터 취합·연동, 입력자-확인자·마감 락, 배출계수 마스터·버전 관리, 데이터 로그 자동 기록, 이상치 탐지(±30% Red Flag) |
| 9 | s07_asis_tobe_effect | 엑셀·이메일 취합 구조의 한계 | 연 1회 엑셀·이메일 취합 구조로는 외부 감사 근거를 제때 제시하기 어렵습니다. | 연 1회 사후 집계 → 월 단위 상시 마감, 이메일·엑셀 수동 소통 → App·Web 단일 플랫폼, 변경 이력·증빙 원본 즉시 확인, 미등록 자동 알람 |
| 10 | 02c_section_divider | PART 02 이너캐리는 어떤 서비스인가 | | 서비스 소개 |
| 11 | s14_task_structure | 기업의 세 가지 고민과 이너캐리의 해법 | 이너캐리는 인벤토리 설계·현장 데이터 수집·공시용 가공을 한 플랫폼에서 해결합니다. | 복잡한 인벤토리 → 전문 컨설턴트, 흩어진 Data → 전용 App, 공시·규제 맞춤 가공 → Web |
| 12 | 03c_content_split | SaaS 기본, 시스템 연동은 옵션 | 이너캐리는 SaaS를 기본으로 설치형·확장형을 선택해 더합니다. | ① SaaS(기본) 연결회사·협력사 수집, ② 사내 설치형(옵션) ERP 연동, ③ 외부 확장형(옵션) |
| 13 | 03d_content_dual | 현장은 Mobile App, 본사는 PC Web | 이너캐리는 현장 입력과 본사 관리를 나눠 담당자별 업무를 단순하게 만듭니다. | 현장: 촬영·입력, 미등록 알림 / 본사: 통계·현황·계측기기 정보 일괄 관리 |
| 14 | 03g_content_process | 설치형: 수집 → 통합 → 공시 형태 전송 | 설치형은 SaaS·ERP·수기 데이터를 통합해 공시 형태로 보냅니다. | INPUT: SaaS 수집·ERP·Key-in, 처리: 종속회사 통합·Scope1,2,3 산정, OUTPUT: 그룹웨어·회계법인 시스템·정부 시스템(예정), API |
| 15 | 02c_section_divider | PART 03 왜 이너젠인가 | | 이너젠 소개 |
| 16 | 03f_content_kpi | 컨설팅펌이 직접 만든 SaaS | 이너캐리는 10년 차 이상 컨설턴트와 검증위원이 산정 결과를 보증하는 SaaS입니다. | 10년+ 시니어 평균 경력, 4대 표준(국내외 산정지침·ISO 14064·GHG Protocol·IPCC), Full Coverage(배출권거래제~CBAM·CSRD·ISSB) |
| 17 | s12_actor_checklist | 보안과 거버넌스 4축 | 이너캐리는 보안·거버넌스 4축으로 감사인 통제 요구에 맞춥니다. | 감사 로그 자동 기록, 역할별 권한 4단계, 국내 리전 클라우드(네이버클라우드), 개인정보보호법 준수, 이용약관 제15·19·3조 요약 |
| 18 | 02c_section_divider | PART 04 무엇을 얻는가 | | 도입 효과 |
| 19 | s13_key_takeaways | 이너캐리 도입 효과 | 이너캐리는 연 1회 몰아치기를 상시 관리로 바꿔 공시 대응력을 높입니다. | 현장 업무 부하 감소, 본사 주기적 관리, 온실가스 전문 지원, 전사 관리체계(ICFR 수준) 개선, ESG 공시 경쟁력 강화 |
| 20 | s53_harvey_compare | 도입 방식 세 가지 | 기업은 보안 환경에 맞춰 세 가지 도입 방식 중 고를 수 있습니다. | SaaS형(자회사·협력사), 설치형(연결실체·ERP 연동), 하이브리드형(지배기업+종속·협력기업) |
| 21 | s15_vertical_chevron | 가입부터 데이터 전송까지 5단계 | 이너캐리는 회원가입부터 데이터 전송까지 5단계로 운영을 시작합니다. | 회원 가입(법인) → 사용 준비(담당자 초대·App 설치) → 자료 입력(매월 약 5분) → 자료 점검(월별 마감) → 데이터 전송(옵션 API) |
| 22 | s18_keyword_grid | 이너캐리의 다섯 가지 약속 | 이너캐리는 전문가 지원부터 데이터 연계까지 다섯 가지 역할을 약속합니다. | 전문가 지원, 데이터 관리 지원, 기업별 맞춤형 지원, 정확성 보증, 데이터 연계 지원 |
| 23 | 04_ending | Thank you. | 복잡한 탄소·환경 정보, 이너캐리가 대신 Carry 해드립니다. | 고객중심의 온실가스 컨설팅, CONTACT 02-6273-0489 · innergen@inng.co.kr, (04387) 서울특별시 용산구 서빙고로 17, 센트럴파크타워 704호 |

변형: 고객사 맞춤 제안이면 3–4쪽(회사소개)을 빼고 6–9쪽에 그 고객의 규제 일정·자회사 수를 넣는다. 설치형을 제안하지 않으면 14쪽을 뺀다.

## 2. 업데이트 규칙

| 바꾸려는 것 | 고칠 곳 | 확인 |
|---|---|---|
| 회사 숫자·연락처·문구·브랜드 표기(기본 사항) | `company-facts-v28.json`의 value·as_of·source, 숫자면 `checks`의 expect | `innergen_facts_check.py --print-md -o <경로>/company-facts-v28.md`로 이 문서 짝(`company-facts-v28.md`)을 다시 만들고, 기존 PPT는 `--pptx`로 대조 |
| 표준 목차·장 구성(내용) | 이 문서 A·B 표와 `content-requirements-v28-intro.json` | `innergen_content_check.py --outline <표> --deck-type company_intro` |
| 장표 디자인·레이아웃(장표) | Slide Master 원본 `templates/decks/<family>/templates/*.svg`와 lock | `svg_quality_checker.py`, `innergen_qaqc.py` |
