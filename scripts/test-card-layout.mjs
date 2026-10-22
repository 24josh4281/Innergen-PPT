import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtemp, readFile, readdir, writeFile, rm, mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import JSZip from 'jszip';

const root = resolve(import.meta.dirname, '..');
const tmp = await mkdtemp(join(root, '.card-tests-'));
try {
  execFileSync(process.execPath, [join(root, 'node_modules/typescript/bin/tsc'), '--noEmit', 'false', '--rootDir', 'src', '--outDir', tmp], { cwd: root, stdio: 'inherit' });
  for (const name of await readdir(tmp)) {
    if (!name.endsWith('.js')) continue;
    const path = join(tmp, name);
    await writeFile(path, (await readFile(path, 'utf8')).replace(/from "(\.\/[^"]+)"/g, 'from "$1.js"'));
  }
  const { layoutCard, wrapCardText } = await import(pathToFileURL(join(tmp, 'cardLayout.js')));
  const frame = { x: 1, y: 1, w: 3, h: 4 };
  const make = text => [{ id: 'title', text: '사업 현황', size: 16, gapAfter: .15 }, { id: 'number', text: '250만 톤', size: 28, gapAfter: .2 }, { id: 'body', text, size: 14 }];
  for (const text of ['짧은 설명', '활동자료 수집 및 배출량 산정 결과 확인', '산정 결과 확인\n근거 자료 검토\n제출 일정 관리']) {
    const placed = layoutCard(frame, make(text), .2);
    assert.equal(placed.length, 3);
    assert.ok(Math.abs(placed[0].y - frame.y - (frame.y + frame.h - placed.at(-1).y - placed.at(-1).h)) < 1e-8);
    for (let i = 0; i < placed.length; i++) {
      const p = placed[i];
      assert.ok(p.x >= 1.2 && p.x + p.w <= 3.8 + 1e-8);
      assert.ok(p.y >= 1.2 && p.y + p.h <= 4.8);
      if (i) assert.ok(Math.abs(p.y - placed[i-1].y - placed[i-1].h - make(text)[i-1].gapAfter) < 1e-8);
    }
  }
  assert.throws(() => layoutCard(frame, make('설명\n'.repeat(40))), /높이 초과/);
  assert.throws(() => layoutCard(frame, make('가'.repeat(100))), /단어 폭 초과/);
  assert.throws(() => layoutCard({ ...frame, h: NaN }, make('설명')));
  assert.throws(() => layoutCard(frame, [{ id: 'a', text: '설명', size: 10 }]));
  assert.throws(() => layoutCard(frame, [{ id: 'a', height: -1 }]));
  assert.deepEqual(wrapCardText('46%', 1, 20), ['46%']);
  assert.equal(layoutCard(frame, [...make(''), { id: 'empty', text: '' }]).length, 2);

  // Exercise real production routing and verify emitted native coordinates.
  const { buildPptxBlob } = await import(pathToFileURL(join(tmp, 'ppt.js')));
  const { getRule } = await import(pathToFileURL(join(tmp, 'patterns.js')));
  const { analyzePptxPackage } = await import(pathToFileURL(join(tmp, 'pptxQa.js')));
  const meta = { clientName: '가상 B사', projectTitle: '카드 정렬 검증', documentType: '검증 견본', dateLabel: '2026.10.22' };
  const slides = ['proposal-need-three-cards', 'dashboard-kpi-takeaway', 'consulting-executive-summary'].map((id, i) => ({
    index: i + 1, title: '사업 현황', claimTitle: '사업별 검토 현황', governingMessage: '자료 검토 결과에 따른 후속 일정 관리',
    sections: ['범위: 배출량 확인', '자료: 활동자료 수집 및 배출량 산정 결과 확인', '일정: 담당자 확인 및 추가 보완 자료 제출 일정 관리'],
    bullets: ['배출량 46% 확인', '활동자료 수집 및 산정 결과 확인', '담당자 확인 및 제출 일정 관리'], archetype: getRule(id), warnings: []
  }));
  const { blob } = await buildPptxBlob(meta, slides);
  const zip = await JSZip.loadAsync(await blob.arrayBuffer());
  let checked = 0;
  for (const name of Object.keys(zip.files).filter(n => /^ppt\/slides\/slide\d+\.xml$/.test(n))) {
    const xml = await zip.file(name).async('string');
    const cards = [...xml.matchAll(/<p:sp>.*?<\/p:sp>/gs)].filter(m => /name="(?:card-\d+-|metric-|panel-)/.test(m[0]));
    const byCard = new Map();
    for (const [shape] of cards) {
      const id = shape.match(/name="([^"]+)"/)[1];
      const off = shape.match(/<a:off x="(\d+)" y="(\d+)"/);
      const ext = shape.match(/<a:ext cx="(\d+)" cy="(\d+)"/);
      assert.ok(off && ext);
      assert.match(shape, /algn="l"/);
      assert.doesNotMatch(shape, /<a:(?:spAutoFit|normAutofit)/);
      const group = id.match(/^(card-\d+|metric|panel)/)[1];
      const boxes = byCard.get(group) ?? [];
      boxes.push({ y: +off[2] / 914400, h: +ext[2] / 914400 }); byCard.set(group, boxes); checked++;
    }
    for (const [key, boxes] of byCard) {
      const top = key.startsWith('card-') ? 2.03 : 1.55;
      const height = key.startsWith('card-') ? 4.07 : 4.55;
      assert.ok(Math.abs(boxes[0].y - top - (top + height - boxes.at(-1).y - boxes.at(-1).h)) < .002);
      for (let i = 1; i < boxes.length; i++) assert.ok(boxes[i].y >= boxes[i-1].y + boxes[i-1].h);
    }
  }
  assert.ok(checked >= 26);
  const qa = await analyzePptxPackage(blob);
  const cardOverlap = qa.issues.filter(i => i.type === 'overlap' && /card-|metric-|panel-/.test(`${i.objectName} ${i.relatedObjectName}`));
  assert.deepEqual(cardOverlap, []);
  assert.equal(qa.sparseContainerCount, 0);
  assert.equal(qa.overflowRiskCount, 0);
  assert.equal(qa.ellipsisCount, 0);
  const out = join(root, 'docs/generated/cards-v31/web'); await mkdir(out, { recursive: true });
  await writeFile(join(out, 'after.pptx'), Buffer.from(await blob.arrayBuffer()));
  await writeFile(join(out, 'qa.json'), JSON.stringify(qa, null, 2));

  // Exact before/after route comparison against the parent PR's renderer.
  const ts = await import('typescript');
  const oldSource = execFileSync('git', ['show', '83e30835aee9b8116c1ac987218e7876eadf9695:src/ppt.ts'], { cwd: root, encoding: 'utf8' });
  const oldJs = ts.transpileModule(oldSource, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } }).outputText.replace(/from "(\.\/[^"]+)"/g, 'from "$1.js"');
  await writeFile(join(tmp, 'ppt-before.js'), oldJs);
  const old = await import(pathToFileURL(join(tmp, 'ppt-before.js')));
  const before = await old.buildPptxBlob(meta, slides);
  const beforeQa = await analyzePptxPackage(before.blob);
  assert.ok(beforeQa.sparseContainerCount > 0); // original KPI/panel imbalance still detected
  // A renamed top-heavy card must not bypass sparse-container QA just by name.
  const shiftedZip = await JSZip.loadAsync(await blob.arrayBuffer());
  const metricXml = await shiftedZip.file('ppt/slides/slide4.xml').async('string');
  shiftedZip.file('ppt/slides/slide4.xml', metricXml.replace(/<p:sp>.*?<\/p:sp>/gs, shape => {
    if (!/name="metric-/.test(shape)) return shape;
    return shape.replace(/(<a:off x="\d+" y=")(\d+)(")/, (_, a, y, b) => a + (Number(y) - Math.round(.8 * 914400)) + b);
  }));
  const shifted = new Blob([await shiftedZip.generateAsync({ type: 'uint8array' })]);
  assert.ok((await analyzePptxPackage(shifted)).sparseContainerCount > 0);
  await writeFile(join(out, 'before.pptx'), Buffer.from(await before.blob.arrayBuffer()));
  console.log(`PASS: card layout invariants, boundary failures, ${checked} native editable production text frames, overlap regression, before/after PPTX`);
} finally { await rm(tmp, { recursive: true, force: true }); }
