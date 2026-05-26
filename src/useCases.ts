export interface ProductUseCase {
  id: string;
  label: string;
  shortLabel: string;
  documentType: string;
  businessType?: string;
  meetingType?: string;
  purpose: string;
  audience: string;
  tone: string;
  projectTitle: string;
  workflow: string[];
  outputs: string[];
  sampleInput: string;
}

export const productUseCases: ProductUseCase[] = [
  {
    id: "reduction-kickoff",
    label: "감축사업 착수회의",
    shortLabel: "감축착수",
    documentType: "착수보고",
    businessType: "감축사업",
    meetingType: "착수회의",
    purpose: "프로젝트 착수",
    audience: "고객사 실무진",
    tone: "실무 보고서",
    projectTitle: "온실가스 감축사업 방법론 개발 착수보고",
    workflow: ["감축사업 개요 입력", "경계·베이스라인·MRV 쟁점 정리", "자료요청과 검증 일정 매칭", "착수회의 PPTX 생성"],
    outputs: ["감축사업 목표", "Boundary/Baseline", "MRV 방법론", "자료요청 및 일정"],
    sampleInput: `감축사업 착수회의
프로젝트 목적은 신규 감축사업의 방법론 개발 가능성과 감축량 산정 체계를 검토하는 것입니다.
핵심 쟁점은 사업 경계, 베이스라인, 누출 가능성, 모니터링 데이터, 검증 가능성입니다.
초기 자료는 설비 사양, 운전 데이터, 기준연도 활동자료, 계측 위치, 기존 배출량 산정 근거입니다.
수행 절차는 경계 설정, 베이스라인 검토, 감축량 산정식 설계, MRV 계획, 검증 대응 순서입니다.
착수 후 우선 과제는 자료 요청 확정, 데이터 소유자 지정, 산정 가정 검토 일정 합의입니다.`
  },
  {
    id: "regulatory-review",
    label: "규제대응 검토 회의",
    shortLabel: "규제검토",
    documentType: "중간보고",
    businessType: "규제대응사업",
    meetingType: "검토 회의",
    purpose: "현황 진단",
    audience: "고객사 실무진",
    tone: "실무 보고서",
    projectTitle: "배출권거래제 명세서 검토 회의",
    workflow: ["명세서/산정계획서 쟁점 입력", "오류·증빙·보완 요청 분리", "검토회의용 의사결정 표 정리", "PPTX 생성"],
    outputs: ["검토 쟁점", "보완 자료", "제출 리스크", "후속 조치"],
    sampleInput: `규제대응 검토 회의
현재 명세서 작성본에서 일부 사업장의 월별 활동자료와 원천 증빙 연결이 부족합니다.
검토 쟁점은 배출계수 적용 기준, 신설·폐쇄시설 처리, 단위 변환, 내부 승인 이력입니다.
보완 요청은 원천자료 링크 재확인, 담당자 승인 메일 확보, 산정 파일 버전 고정입니다.
제출 리스크는 검증기관 질의 증가, 보완 기간 부족, 자료 재제출 가능성입니다.
회의에서 결정할 사항은 보완 책임자, 제출 기한, 최종 검토 기준입니다.`
  },
  {
    id: "disclosure-interim",
    label: "CDP·기후공시 중간보고",
    shortLabel: "공시중간",
    documentType: "중간보고",
    businessType: "CDP·기후공시사업",
    meetingType: "중간보고",
    purpose: "현황 진단",
    audience: "고객사 임원",
    tone: "임원 요약",
    projectTitle: "CDP 및 기후공시 대응 중간보고",
    workflow: ["문항별 진척 입력", "Gap·증빙·답변 품질 점검", "우선 보완 레버 도출", "중간보고 PPTX 생성"],
    outputs: ["진척 대시보드", "문항 Gap", "증빙 현황", "우선 보완 과제"],
    sampleInput: `CDP 기후공시 중간보고
현재 CDP 문항별 답변 초안은 작성되었으나 Scope 3 산정 근거와 기후리스크 재무영향 설명이 부족합니다.
주요 Gap은 지표 목표, 리스크 관리 절차, 공급망 데이터, 내부 검토 이력입니다.
증빙은 이사회 보고자료, 에너지 사용량, 배출량 산정표, 리스크 평가 결과, 정책 문서로 구성됩니다.
우선 보완 과제는 점수 영향이 큰 문항의 증빙 연결, 답변 논리 강화, 누락 자료 재요청입니다.
다음 단계는 고위험 문항 리뷰, 답변본 QA, 제출 전 경영진 검토입니다.`
  },
  {
    id: "rfp-proposal",
    label: "입찰/RFP 제안서 자동화",
    shortLabel: "제안서",
    documentType: "컨설팅 제안서",
    businessType: "CDP·기후공시사업",
    meetingType: "착수회의",
    purpose: "제안·입찰 대응",
    audience: "고객사 임원",
    tone: "고급 컨설팅 제안서",
    projectTitle: "ESG·기후 대응 통합 자문 제안서",
    workflow: ["RFP/PDF 업로드", "요구사항·평가기준 추출", "제안 논리와 수행방법론 매칭", "Storyboard 승인 후 PPTX 생성"],
    outputs: ["Executive summary", "Project approach", "Scope & deliverables", "Team & schedule"],
    sampleInput: `RFP 대응 제안서
고객은 ESG 공시, 기후리스크, 온실가스 데이터 관리 체계를 통합적으로 개선해야 합니다.
제안 핵심은 단순 보고서 작성이 아니라 데이터 수집-검증-공시-개선 실행까지 이어지는 운영 체계 구축입니다.
범위: 현황 진단, 요구사항 매핑, 데이터 갭 분석, 실행 로드맵, 산출물 제작
차별점: 규제 대응 경험, 검증 대응 체크리스트, 고객사 부서 협업 체계, 산출물 QA
기대효과: 제출 안정성 향상, 내부 검토 시간 단축, 향후 공시 대응 기반 확보`
  },
  {
    id: "kickoff",
    label: "착수보고 자동화",
    shortLabel: "착수",
    documentType: "착수보고",
    businessType: "규제대응사업",
    meetingType: "착수회의",
    purpose: "프로젝트 착수",
    audience: "고객사 실무진",
    tone: "실무 보고서",
    projectTitle: "온실가스·ESG 대응 프로젝트 착수보고",
    workflow: ["계약/제안 범위 입력", "업무 범위·일정·R&R 정리", "자료요청과 QA 기준 설정", "Kick-off deck 생성"],
    outputs: ["프로젝트 배경", "업무 범위", "자료 요청 목록", "일정 및 커뮤니케이션 체계"],
    sampleInput: `착수보고
프로젝트 목적은 온실가스 산정과 증빙 관리 체계를 안정적으로 운영하는 것입니다.
수행 범위는 활동자료 취합, 산정 로직 검토, 내부 검토, 보완 대응, 제출본 제작으로 구성됩니다.
초기 위험은 자료 누락, 단위 불일치, 담당 부서 미지정, 일정 지연입니다.
관리 방식은 주간 회의, 이슈 로그, 자료 제출 현황표, 산출물 버전 관리로 운영합니다.
착수 이후 2주 내 자료 요청 목록과 담당자 매핑을 확정해야 합니다.`
  },
  {
    id: "progress",
    label: "중간보고·이슈 관리",
    shortLabel: "중간",
    documentType: "중간보고",
    businessType: "규제대응사업",
    meetingType: "중간보고",
    purpose: "현황 진단",
    audience: "고객사 실무진",
    tone: "실무 보고서",
    projectTitle: "프로젝트 중간보고 및 이슈 대응",
    workflow: ["진행 현황 입력", "이슈·리스크·의사결정 분리", "조치 계획과 담당자 연결", "보고용 PPTX 생성"],
    outputs: ["진행률 요약", "이슈 트리", "의사결정 필요사항", "다음 단계"],
    sampleInput: `중간보고
현재 활동자료 취합률은 70% 수준이며 일부 부서의 증빙 제출이 지연되고 있습니다.
주요 이슈는 단위 불일치, 배출계수 기준 확인 필요, 사업장별 담당자 응답 지연입니다.
우선 조치는 미제출 부서 재요청, 계수 출처 확인, QA 체크리스트 기준 확정입니다.
다음 단계는 산정 파일 1차 검토, 오류 목록 공유, 보완 요청서 발송입니다.
의사결정 필요사항은 제출 기한, 누락 자료 처리 기준, 최종 검토 책임자 지정입니다.`
  },
  {
    id: "final-report",
    label: "최종보고 자동화",
    shortLabel: "최종",
    documentType: "최종보고",
    businessType: "CDP·기후공시사업",
    meetingType: "최종보고",
    purpose: "의사결정 보고",
    audience: "고객사 임원",
    tone: "임원 요약",
    projectTitle: "ESG·기후 대응 최종보고",
    workflow: ["분석 결과 입력", "핵심 메시지와 근거 연결", "성과·한계·로드맵 재구성", "최종 보고 PPTX 생성"],
    outputs: ["핵심 결론", "주요 분석 결과", "개선 과제", "이행 로드맵"],
    sampleInput: `최종보고
프로젝트 결과 데이터 취합과 검토 체계는 개선되었으나 일부 증빙 관리 절차는 지속 보완이 필요합니다.
핵심 성과는 자료 요청 체계 표준화, 오류 유형 식별, 제출본 QA 기준 수립입니다.
잔여 리스크는 담당자 변경, 원천자료 링크 누락, 배출계수 업데이트 관리입니다.
권고사항은 정기 데이터 취합 일정 운영, 증빙팩 템플릿 관리, 내부 검토 체크리스트 적용입니다.
다음 과제는 자동화 파일 고도화와 부서별 교육 운영입니다.`
  },
  {
    id: "assurance-pack",
    label: "검증·증빙 대응팩",
    shortLabel: "증빙",
    documentType: "중간보고",
    businessType: "규제대응사업",
    meetingType: "검토 회의",
    purpose: "실행계획 수립",
    audience: "검증기관",
    tone: "실무 보고서",
    projectTitle: "온실가스 검증 대응 증빙팩",
    workflow: ["산정 파일·증빙 목록 입력", "누락·중복·단위 리스크 탐지", "검증 질문 대응 구조화", "증빙팩 PPTX 생성"],
    outputs: ["검증 대응 현황", "증빙 매핑표", "오류 유형", "보완 요청 목록"],
    sampleInput: `검증 대응
검증기관은 활동자료 출처, 배출계수 적용 근거, 단위 변환 로직, 내부 검토 이력을 확인할 예정입니다.
현재 리스크는 일부 사업장의 원천자료 링크 누락, 월별 사용량 합계 검증 미완료, 담당자 승인 이력 부족입니다.
증빙팩은 산정표, 청구서, 계수 출처, 검토 로그, 보완 요청 이력으로 구성합니다.
우선 보완 항목은 고위험 사업장 증빙 재확인, 단위 환산식 검토, 제출 파일 버전 고정입니다.
목표는 검증 질의 대응 시간을 줄이고 제출본 신뢰도를 높이는 것입니다.`
  },
  {
    id: "training",
    label: "교육·워크숍 자료",
    shortLabel: "교육",
    documentType: "교육자료",
    businessType: "CDP·기후공시사업",
    meetingType: "검토 회의",
    purpose: "실행계획 수립",
    audience: "고객사 실무진",
    tone: "워크숍 자료",
    projectTitle: "ESG·기후 데이터 관리 교육자료",
    workflow: ["교육 주제 입력", "개념·사례·체크리스트 분리", "워크숍 흐름 구성", "교육용 PPTX 생성"],
    outputs: ["핵심 개념", "실무 사례", "체크리스트", "Q&A"],
    sampleInput: `교육자료
교육 목적은 부서 담당자가 온실가스 활동자료와 증빙을 정확히 제출하도록 돕는 것입니다.
핵심 개념은 활동자료, 배출계수, 단위 변환, 증빙 출처, 내부 검토 기록입니다.
실무 오류는 단위 혼용, 월별 합계 불일치, 누락 자료, 담당자 변경 미반영입니다.
워크숍은 개념 설명, 오류 사례, 제출 양식 작성, QA 체크리스트 실습 순서로 진행합니다.
교육 후 산출물은 부서별 자료 제출 체크리스트와 담당자별 보완 과제입니다.`
  }
];

export function getUseCase(id: string) {
  return productUseCases.find((useCase) => useCase.id === id) ?? productUseCases[0];
}
