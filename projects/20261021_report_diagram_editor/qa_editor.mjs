import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const root = new URL('./dist/', import.meta.url);
const sandbox = {};
sandbox.globalThis = sandbox;
for (const name of ['catalog.js', 'qaqc.js']) {
  vm.runInNewContext(fs.readFileSync(new URL(name, root), 'utf8'), sandbox, {filename: name});
}
const {ReportCatalog: C, ReportQA: Q} = sandbox;
const copy = value => JSON.parse(JSON.stringify(value));
const errors = value => Q.check(value).filter(issue => issue.severity === 'error').map(issue => issue.code);

let checked = 0;
for (const business of Object.keys(C.businesses)) {
  for (const stage of Object.keys(C.stages)) {
    for (const type of Object.keys(C.types)) {
      const example = C.makeExample(business, stage, type);
      const before = JSON.stringify(example);
      assert.equal(errors(example).length, 0, `${business}/${stage}/${type}: ${errors(example)}`);
      assert.equal(JSON.stringify(example), before, 'QA must not change original values');
      if (type === 'procedure') {
        const graph = C.parseGraph(example);
        assert.equal(graph.rows.length, 4);
        assert.equal(graph.rows.every(row => row.nodes.length === 3), true);
      }
      checked++;
    }
  }
}

const base = C.makeExample('reduction', 'final', 'procedure');
const cases = [
  ['DATE', p => { p.asOf = '2026-13-02'; }],
  ['DATE_ORDER', p => { p.tasks[0].start = '2026-11-09'; p.tasks[0].end = '2026-11-02'; }],
  ['FUTURE_ACTUAL', p => { p.tasks[0].actualEnd = '2027-01-01'; }],
  ['DUPLICATE_ID', p => { p.tasks[1].id = p.tasks[0].id; }],
  ['MISSING_DEPENDENCY', p => { p.tasks[1].dependsOn = ['missing']; }],
  ['DEPENDENCY_CYCLE', p => { p.tasks[0].dependsOn = ['T02']; }],
  ['APPROVAL_EVIDENCE', p => { p.tasks[0].approval = '승인'; p.tasks[0].evidence = ''; }],
  ['SCOPE_CONFLICT', p => { p.scope.excluded = p.scope.included.split('\n')[0]; }],
  ['MISSING_PARAMETER', p => { p.equations[0].parameterIds.push('unknown'); }],
  ['EQUATION_SYMBOL', p => { p.equations[0].latex = 'ER_y = BE_y - PE_y'; }],
  ['GRAPH_PHASES', p => { p.graphText = '한 단계 | 한 상자'; }],
  ['GRAPH_NODES', p => { p.graphText = '단계1 | 상자1 | 상자2 | 상자3 | 상자4 | 상자5\n단계2 | 상자1'; }],
  ['GRAPH_LINK_FORMAT', p => { p.graphLinks = '1->2'; }],
  ['GRAPH_LINK_TARGET', p => { p.graphLinks = '1.8 > 2.1'; }],
];
for (const [code, change] of cases) {
  const p = copy(base);
  change(p);
  assert.ok(errors(p).includes(code), `${code}: expected QA error, got ${errors(p)}`);
}
console.log(`PASS ${checked} combinations; ${cases.length} anomaly classes; input unchanged`);
