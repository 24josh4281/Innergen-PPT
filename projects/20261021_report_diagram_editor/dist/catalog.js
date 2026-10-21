/* Shared report-diagram vocabulary. All example content is fictional. */
(function () {
  'use strict';

  const businesses = {
    cdp: {
      label: 'CDP 대응',
      contextFields: {
        reportingYear: '응답 연도', questionnaireVersion: '질문서 판본',
        modules: '대상 모듈', organizationBoundary: '대상 조직·경계'
      },
      phases: [
        ['요구사항 확인', '질문서·기존 응답', '문항·모듈과 응답 범위 확인', '요구사항 목록', '연도·판본·범위 확인'],
        ['근거 수집·갭 진단', '문항별 요청 자료', '증빙·기간·누락과 보완 항목 대조', '근거·갭 목록', '출처·기간·담당 대응'],
        ['답변 작성·검토', '요구사항·검토된 증빙', '주장과 증빙을 연결하고 답변 검토', '답변 초안·검토 이력', '주장과 증빙 일치'],
        ['확정·제출 준비', '검토된 답변·보완 이력', '고객 확정과 제출 상태를 구분해 관리', '확정 답변·제출 기록', '승인과 제출 기록 각각 확인']
      ],
      procedureRows: [
        ['요구사항 확인', '대상·범위 확인', '질문서·기존 응답 분석', '작성 방향 확정'],
        ['근거 수집·진단', '자료 요청', '증빙·활동자료 정리', '누락·갭 점검'],
        ['답변 작성·검증', '문항별 답변 초안', '주장·증빙 대조', '보완 의견 반영'],
        ['확정·제출', '고객 승인', '최종 답변 정리', '제출 기록·인계']
      ],
      included: '대상 문항·모듈 확인\n문항별 증빙·답변 검토\n보완 과제와 승인 흐름',
      excluded: '평가점수·등급 취득 보장\n미확정 자료를 실제 실적으로 확정'
    },
    regulatory: {
      label: '규제 대응',
      contextFields: {
        regime: '적용 제도', jurisdiction: '관할', standardVersion: '기준 판본',
        basisDate: '근거 기준일', applicabilityBasis: '적용 조건·예외 판단 근거', legalDue: '법정기한'
      },
      phases: [
        ['대상·의무 확인', '공식 기준·적용 판단 자료', '대상·조건·예외와 의무 확인', '적용 판단·의무 목록', '현재 공식 근거와 적용 조건 확인'],
        ['자료 수집·점검', '의무별 요청 자료', '기간·경계·누락과 보완 항목 점검', '요구자료·보완 목록', '원값·경계·기간 대응'],
        ['산정·검토', '검토된 활동자료·적용 기준', '산정 방법과 단위·결과 대조', '산정·검토 결과', '기준·원값·단위 확인'],
        ['검증·제출·이행', '검토 결과·검증·승인 자료', '검증·제출·이행 상태를 각각 관리', '검증·제출·이행 기록', '법정·내부기한과 승인 상태 구분']
      ],
      procedureRows: [
        ['적용성 검토', '대상·제도 확인', '조건·예외 검토', '의무 목록 정리'],
        ['자료 수집', '원자료 요청', '기간·경계 대조', '누락·보완 정리'],
        ['산정·검토', '적용 기준 확인', '원값·단위 대조', '산정 결과 검토'],
        ['검증·이행', '검증 의견 반영', '승인·제출 구분', '이행 기록 인계']
      ],
      included: '적용 대상·조건·의무 확인\n자료 수집·산정·검토\n검증·제출·이행 상태 관리',
      excluded: '확인되지 않은 법정기한 단정\n조건·예외 검토 없는 적용 확정'
    },
    reduction: {
      label: '감축사업',
      contextFields: {
        methodology: '적용 방법론', methodologyVersion: '방법론 판본',
        projectBoundary: '사업 경계', baselinePeriod: '기준선 대상기간', monitoringPeriod: '모니터링 기간'
      },
      phases: [
        ['경계·적용성 검토', '사업 기술·경계·방법론 자료', '기준선·대안·적용 조건 검토', '경계·적용성 검토', '현재 사업의 경계·적용 근거 확인'],
        ['시나리오·산정 설계', '적용 방법론·활동자료 목록', '시나리오 수식과 인자·단위 대응', '수식·인자 대응 명세', '방법론 절·수식 번호·단위 확인'],
        ['모니터링·자료 검토', '인자 명세·측정·기록 자료', '출처·주기·QA/QC와 결측 처리 검토', '모니터링·자료 검토 기록', '원값·주기·결측·불확도 대응'],
        ['산정·검증·인계', '확정 자료·산정·검증 기록', '시나리오별 결과와 근거를 연결해 인계', '산정·검증·인계 기록', '원값·계수·수식·결과 추적']
      ],
      procedureRows: [
        ['경계·적용성', '사업 경계 확인', '방법론 조건 검토', '기준선 범위 확정'],
        ['산정 설계', '시나리오 구분', '수식·인자 연결', '단위·기간 대조'],
        ['모니터링', '측정·기록 계획', '원값·결측 점검', 'QA/QC 기록'],
        ['검증·인계', '산정 결과 대조', '검증 의견 반영', '근거·잔여 과제 인계']
      ],
      included: '기준선·사업·누출 시나리오 검토\n수식·인자·단위·기간 대응\n모니터링·검증·인계',
      excluded: '근거 없는 누출 0 확정\n추가성 충족·감축실적 인정 보장'
    }
  };

  const stages = {
    kickoff: {label: '착수', focus: '계획·범위·자료 요청·검토 조건'},
    interim: {label: '중간', focus: '기준일·계획 대비 실적·잠정 결과·조치'},
    final: {label: '최종', focus: '실제 수행·검증·한계·잔여 과제·인계'}
  };
  const types = {
    overview: {label: '수행개요', structure: '목적·대상·범위·산출물 매핑'},
    procedure: {label: '추진절차', structure: '단계별 활동 상자와 선후·분기 연결 그래프'},
    schedule: {label: '수행일정', structure: '과업별 계획·실적 간트와 검토 마일스톤'},
    method: {label: '수행방법', structure: '대상·자료 → 수행 방법 → 산출물·검토'}
  };
  const leads = {
    kickoff: '가상 예시: 단계별 입력·활동·산출물과 검토 조건을 확정할 예정입니다.',
    interim: '가상 예시: 완료·진행·미확인 항목을 기준일과 근거에 따라 구분해 관리합니다.',
    final: '가상 예시: 수행한 범위와 방법, 검증 근거 및 잔여 과제를 연결해 인계합니다.'
  };
  const datePairs = [
    ['2026-11-02', '2026-11-06'], ['2026-11-09', '2026-11-13'],
    ['2026-11-16', '2026-11-27'], ['2026-11-30', '2026-12-04']
  ];

  function makeExample(business, stage, type) {
    const own = function (object, key) { return Object.prototype.hasOwnProperty.call(object, key); };
    if (!own(businesses, business) || !own(stages, stage) || !own(types, type)) {
      throw new Error('지원하는 사업·보고 단계·도표 유형을 선택하세요.');
    }
    const profile = businesses[business];
    const tasks = profile.phases.map(function (phase, index) {
      const done = stage === 'final' || (stage === 'interim' && index < 2);
      const active = stage === 'interim' && index === 2;
      return {
        id: 'T0' + (index + 1), name: phase[0], owner: '가상 담당 ' + (index + 1),
        input: phase[1], activity: phase[2], output: phase[3], gate: phase[4],
        evidence: done ? '가상 예시 증빙 E0' + (index + 1) : '',
        status: done ? '완료' : active ? '진행' : stage === 'interim' ? '대기' : '예정',
        approval: done ? '검토 중' : '미제출',
        start: datePairs[index][0], end: datePairs[index][1],
        actualStart: done || active ? datePairs[index][0] : '',
        actualEnd: done ? datePairs[index][1] : '',
        dependsOn: index ? ['T0' + index] : []
      };
    });
    const parameters = business === 'reduction' ? [
      ['BE', 'BE_y', '베이스라인 배출량'], ['PE', 'PE_y', '사업 배출량'],
      ['LE', 'LE_y', '누출 배출량'], ['ER', 'ER_y', '감축량']
    ].map(function (row) {
      return {
        id: row[0], symbol: row[1], name: row[2], unit: 'tCO2e/대상기간(미확정)',
        source: '현재 사업 산정명세·근거 미확정', frequency: '적용 방법론 확인 후 확정',
        qaqc: '원값·수식·단위 대조. 세부 검토 기준은 현재 사업에서 확정'
      };
    }) : [];
    return {
      version: 1, business: business, stage: stage, type: type,
      title: '[가상 예시] ' + profile.label + ' ' + stages[stage].label + ' · ' + types[type].label,
      lead: leads[stage],
      asOf: stage === 'final' ? '2026-12-04' : stage === 'kickoff' ? '2026-11-02' : '2026-11-20',
      context: Object.fromEntries(Object.keys(profile.contextFields).map(function (key) { return [key, '미확정']; })),
      tasks: tasks,
      graphText: profile.procedureRows.map(function (row) { return row.join(' | '); }).join('\n'),
      graphLinks: '',
      scope: {
        purpose: '가상 예시: ' + profile.label + '의 과업·근거·산출물과 검토 조건을 연결합니다.',
        included: profile.included, excluded: profile.excluded
      },
      parameters: parameters,
      equations: business === 'reduction' ? [{
        id: 'eq_reduction', latex: 'ER_y = BE_y - PE_y - LE_y', parameterIds: ['ER', 'BE', 'PE', 'LE']
      }] : []
    };
  }

  function parseGraph(project) {
    const rows = String(project.graphText || '').split(/\r?\n/).map(function (line) { return line.trim(); })
      .filter(Boolean).map(function (line) {
        const cells = line.split('|').map(function (cell) { return cell.trim(); });
        return {title: cells[0] || '', nodes: cells.slice(1)};
      });
    const links = String(project.graphLinks || '').split(/\r?\n/).map(function (line) { return line.trim(); })
      .filter(Boolean).map(function (line) {
        const match = line.match(/^(\d+)\.(\d+)\s*>\s*(\d+)\.(\d+)$/);
        return match ? {fromPhase: Number(match[1]), fromNode: Number(match[2]),
          toPhase: Number(match[3]), toNode: Number(match[4]), raw: line} : {raw: line, invalid: true};
      });
    return {rows: rows, links: links};
  }

  globalThis.ReportCatalog = {businesses: businesses, stages: stages, types: types,
    makeExample: makeExample, parseGraph: parseGraph};
}());
