/* Structured checks, independent of diagram drawing or Office rendering. */
(function () {
  'use strict';

  const states = ['예정', '진행', '완료', '대기', '지연', '미확인', '해당 없음'];
  const approvals = ['미제출', '제출', '검토 중', '보완', '승인', '미확인'];
  const unknown = /미확정|미확인|확인 후|확정 후|확인 필요|검토 필요/;

  function nonempty(value) { return typeof value === 'string' && value.trim().length > 0; }
  function known(value) { return nonempty(value) && !unknown.test(value); }
  function dateValue(value) {
    if (!nonempty(value) || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const parts = value.split('-').map(Number);
    const result = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
    return result.getUTCFullYear() === parts[0] && result.getUTCMonth() === parts[1] - 1 &&
      result.getUTCDate() === parts[2] ? result.getTime() : null;
  }

  function check(project) {
    const result = [];
    function add(severity, code, message, field) { result.push({severity: severity, code: code, message: message, field: field}); }
    if (!project || typeof project !== 'object') {
      add('error', 'SCHEMA', '도표 데이터가 올바른 객체가 아닙니다.', 'project');
      return result;
    }
    const catalog = globalThis.ReportCatalog;
    const own = function (object, key) { return !!object && Object.prototype.hasOwnProperty.call(object, key); };
    for (const pair of [['business', 'businesses'], ['stage', 'stages'], ['type', 'types']]) {
      if (!catalog || !own(catalog[pair[1]], project[pair[0]])) add('error', 'TYPE', '지원하는 ' + pair[0] + ' 값을 선택하세요.', pair[0]);
    }
    if (!nonempty(project.title)) add('warning', 'TITLE', '도표 제목이 없습니다.', 'title');
    if (dateValue(project.asOf) === null) add('error', 'DATE', '기준일은 유효한 YYYY-MM-DD 날짜여야 합니다.', 'asOf');
    const profile = catalog && own(catalog.businesses, project.business) ? catalog.businesses[project.business] : null;
    if (profile) {
      for (const key of Object.keys(profile.contextFields)) {
        if (!known((project.context || {})[key])) add('warning', 'CONTEXT', profile.contextFields[key] + '을 현재 사업 자료로 확인하세요.', 'context.' + key);
      }
    }
    if (!Array.isArray(project.tasks)) {
      add('error', 'TASKS', '과업 목록이 배열이 아닙니다.', 'tasks');
      return result;
    }
    if (!project.tasks.length) add('warning', 'TASKS_EMPTY', '과업을 한 개 이상 입력하세요.', 'tasks');
    if (project.tasks.some(function (task) { return !task || typeof task !== 'object' || Array.isArray(task); })) {
      add('error', 'TASK_SCHEMA', '각 과업은 ID·내용·상태를 가진 객체여야 합니다.', 'tasks');
      return result;
    }
    const taskIds = new Set();
    project.tasks.forEach(function (task, index) {
      const field = 'tasks.' + index;
      if (!nonempty(task.id)) add('error', 'ID', '과업 ID가 없습니다.', field + '.id');
      else if (taskIds.has(task.id)) add('error', 'DUPLICATE_ID', '과업 ID가 중복됩니다: ' + task.id, field + '.id');
      taskIds.add(task.id);
      for (const key of ['name', 'owner', 'input', 'activity', 'output', 'gate']) {
        if (!nonempty(task[key])) add('warning', 'TASK_FIELD', '과업 ' + (task.id || index + 1) + '의 ' + key + ' 항목이 비어 있습니다.', field + '.' + key);
      }
      if (!states.includes(task.status)) add('error', 'STATUS', '알 수 없는 과업 상태입니다.', field + '.status');
      if (!approvals.includes(task.approval)) add('error', 'APPROVAL_STATUS', '알 수 없는 검토·승인 상태입니다.', field + '.approval');
      for (const key of ['start', 'end', 'actualStart', 'actualEnd']) {
        if (task[key] !== undefined && task[key] !== null && task[key] !== '' && dateValue(task[key]) === null) add('error', 'DATE', '유효한 YYYY-MM-DD 날짜를 입력하세요.', field + '.' + key);
      }
      for (const pair of [['start', 'end'], ['actualStart', 'actualEnd']]) {
        const start = dateValue(task[pair[0]]), end = dateValue(task[pair[1]]);
        if (start !== null && end !== null && start > end) add('error', 'DATE_ORDER', '시작일이 종료일보다 늦습니다.', field + '.' + pair[1]);
      }
      if (nonempty(task.actualEnd) && !nonempty(task.actualStart)) add('warning', 'ACTUAL_START', '실제 종료일에 대응하는 실제 시작일이 없습니다.', field + '.actualStart');
      const basis = dateValue(project.asOf);
      if (basis !== null && dateValue(task.actualEnd) !== null && dateValue(task.actualEnd) > basis) add('error', 'FUTURE_ACTUAL', '기준일 이후의 종료일을 실제 완료로 기록할 수 없습니다.', field + '.actualEnd');
      if (task.status === '완료' && (!known(task.evidence) || !known(task.output) || dateValue(task.actualEnd) === null)) add('warning', 'COMPLETION_EVIDENCE', '완료 상태의 산출물·근거·실제 종료일을 확인하세요.', field + '.status');
      if (task.approval === '승인' && !known(task.evidence)) add('error', 'APPROVAL_EVIDENCE', '승인 상태에는 확인 가능한 승인 근거가 필요합니다.', field + '.evidence');
      if (task.status === '미확인' && task.progress !== undefined && task.progress !== null && task.progress !== '') add('error', 'UNKNOWN_PROGRESS', '미확인 상태를 숫자 진행률로 변환하지 마세요.', field + '.progress');
      if (!Array.isArray(task.dependsOn)) add('error', 'DEPENDENCY_SCHEMA', '선행 과업은 ID 배열로 입력하세요.', field + '.dependsOn');
    });
    const byId = new Map(project.tasks.map(function (task) { return [task.id, task]; }));
    project.tasks.forEach(function (task, index) {
      for (const dependency of Array.isArray(task.dependsOn) ? task.dependsOn : []) {
        if (!taskIds.has(dependency)) add('error', 'MISSING_DEPENDENCY', '선행 과업을 찾을 수 없습니다: ' + dependency, 'tasks.' + index + '.dependsOn');
        else if (dependency === task.id) add('error', 'SELF_DEPENDENCY', '과업은 자신을 선행 과업으로 참조할 수 없습니다.', 'tasks.' + index + '.dependsOn');
        else {
          const predecessor = byId.get(dependency);
          const previousEnd = dateValue(predecessor.end), start = dateValue(task.start);
          if (previousEnd !== null && start !== null && start < previousEnd) add('warning', 'OVERLAP_DEPENDENCY', '선행 과업 종료 전 시작합니다. 병렬 수행·부분 인계 근거를 확인하세요.', 'tasks.' + index + '.start');
        }
      }
    });
    const visited = new Set(), active = new Set(), cycles = new Set();
    function visit(id) {
      if (active.has(id)) { cycles.add(id); return; }
      if (visited.has(id) || !byId.has(id)) return;
      active.add(id);
      const deps = byId.get(id).dependsOn;
      for (const dependency of Array.isArray(deps) ? deps : []) visit(dependency);
      active.delete(id); visited.add(id);
    }
    for (const id of taskIds) visit(id);
    if (cycles.size) add('error', 'DEPENDENCY_CYCLE', '선행 과업 연결에 순환이 있습니다: ' + Array.from(cycles).join(', '), 'tasks');

    const scope = project.scope || {};
    if (!nonempty(scope.purpose)) add('warning', 'PURPOSE', '수행 목적을 입력하세요.', 'scope.purpose');
    const items = function (value) { return (Array.isArray(value) ? value : String(value || '').split(/[\n;]+/)).map(function (x) { return String(x).trim(); }).filter(Boolean); };
    const included = new Set(items(scope.included));
    for (const excluded of items(scope.excluded)) {
      if (included.has(excluded)) add('error', 'SCOPE_CONFLICT', '같은 범위가 포함과 제외에 모두 있습니다: ' + excluded, 'scope.excluded');
    }
    if (!included.size) add('warning', 'SCOPE_EMPTY', '포함 범위를 입력하세요.', 'scope.included');

    if (project.type === 'procedure') {
      const graph = catalog.parseGraph(project);
      if (graph.rows.length < 2 || graph.rows.length > 5) {
        add('error', 'GRAPH_PHASES', '추진절차는 2~5단계로 작성하세요.', 'graphText');
      }
      graph.rows.forEach(function (row, phaseIndex) {
        const field = 'graphText.' + (phaseIndex + 1);
        if (!nonempty(row.title)) add('error', 'GRAPH_TITLE', '단계 제목이 비어 있습니다.', field);
        if (row.nodes.length < 1 || row.nodes.length > 4 || row.nodes.some(function (node) { return !nonempty(node); })) {
          add('error', 'GRAPH_NODES', '각 단계에 비어 있지 않은 작업 상자 1~4개를 입력하세요.', field);
        }
        row.nodes.forEach(function (node) {
          if (node.length > 34) add('warning', 'GRAPH_TEXT_FIT', '작업 상자 문구가 길어 그림에서 생략될 수 있습니다: ' + node.slice(0, 24), field);
        });
      });
      const linkKeys = new Set();
      graph.links.forEach(function (link, index) {
        const field = 'graphLinks.' + (index + 1);
        if (link.invalid) { add('error', 'GRAPH_LINK_FORMAT', '추가 연결은 1.2 > 3.1 형식으로 입력하세요: ' + link.raw, field); return; }
        const from = graph.rows[link.fromPhase - 1], to = graph.rows[link.toPhase - 1];
        if (!from || !to || link.fromNode < 1 || link.toNode < 1 || link.fromNode > from.nodes.length || link.toNode > to.nodes.length) {
          add('error', 'GRAPH_LINK_TARGET', '존재하는 단계·상자 번호를 연결하세요: ' + link.raw, field);
        }
        if (link.fromPhase === link.toPhase && link.fromNode === link.toNode) add('error', 'GRAPH_SELF_LINK', '상자를 자기 자신에게 연결할 수 없습니다.', field);
        if (linkKeys.has(link.raw)) add('error', 'GRAPH_DUPLICATE_LINK', '같은 연결이 중복됩니다: ' + link.raw, field);
        linkKeys.add(link.raw);
        if (link.toPhase < link.fromPhase) add('warning', 'GRAPH_REVIEW_LOOP', '역방향 연결은 재검토·반복 조건을 함께 확인하세요: ' + link.raw, field);
      });
    }

    const parameters = Array.isArray(project.parameters) ? project.parameters : [];
    const parameterIds = new Set();
    const parameterById = new Map();
    parameters.forEach(function (parameter, index) {
      const field = 'parameters.' + index;
      if (!parameter || typeof parameter !== 'object' || Array.isArray(parameter)) {
        add('error', 'PARAMETER_SCHEMA', '각 인자는 ID·기호·정의를 가진 객체여야 합니다.', field);
        return;
      }
      if (!nonempty(parameter.id) || parameterIds.has(parameter.id)) add('error', 'PARAMETER_ID', '인자 ID가 없거나 중복됩니다.', field + '.id');
      parameterIds.add(parameter.id);
      if (nonempty(parameter.id)) parameterById.set(parameter.id, parameter);
      for (const key of ['symbol', 'name', 'unit', 'source', 'frequency', 'qaqc']) {
        if (!known(parameter[key])) add('warning', 'PARAMETER_FIELD', '인자 ' + (parameter.id || index + 1) + '의 ' + key + ' 항목을 현재 사업에서 확인하세요.', field + '.' + key);
      }
    });
    const equationIds = new Set();
    const equations = Array.isArray(project.equations) ? project.equations : [];
    equations.forEach(function (equation, index) {
      const field = 'equations.' + index;
      if (!equation || typeof equation !== 'object' || Array.isArray(equation)) {
        add('error', 'EQUATION_SCHEMA', '각 수식은 ID·원문·연결 인자를 가진 객체여야 합니다.', field);
        return;
      }
      if (!nonempty(equation.id) || equationIds.has(equation.id)) add('error', 'EQUATION_ID', '수식 ID가 없거나 중복됩니다.', field + '.id');
      equationIds.add(equation.id);
      if (!nonempty(equation.latex)) add('error', 'EQUATION_EMPTY', '편집 가능한 수식 원문이 없습니다.', field + '.latex');
      if (!Array.isArray(equation.parameterIds) || !equation.parameterIds.length) add('error', 'EQUATION_PARAMETERS', '수식에서 사용하는 인자를 연결하세요.', field + '.parameterIds');
      for (const id of Array.isArray(equation.parameterIds) ? equation.parameterIds : []) {
        if (!parameterIds.has(id)) add('error', 'MISSING_PARAMETER', '수식에 연결한 인자를 찾을 수 없습니다: ' + id, field + '.parameterIds');
        else {
          const symbol = parameterById.get(id).symbol;
          if (nonempty(symbol) && nonempty(equation.latex) && !equation.latex.replace(/\s+/g, '').includes(symbol.replace(/\s+/g, ''))) {
            add('error', 'EQUATION_SYMBOL', '연결한 인자 기호가 수식 원문에 없습니다: ' + symbol, field + '.latex');
          }
        }
      }
    });
    if (project.business === 'reduction' && project.type === 'method' && !equations.length) add('warning', 'REDUCTION_EQUATION', '감축 수행방법에는 시나리오 수식과 모니터링 인자 연결을 확인하세요.', 'equations');
    return result;
  }

  globalThis.ReportQA = {check: check};
}());
