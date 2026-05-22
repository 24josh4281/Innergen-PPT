export interface ProductUseCase {
  id: string;
  label: string;
  shortLabel: string;
  documentType: string;
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
    id: "rfp-proposal",
    label: "입찰/RFP 제안서 자동화",
    shortLabel: "제안서",
    documentType: "컨설팅 제안서",
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
