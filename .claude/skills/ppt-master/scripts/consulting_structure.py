#!/usr/bin/env python3
"""
PPT Master - Consulting Structure Planning

Connect the source-backed v14 vocabulary to v19 education/proposal choices.
See docs/styles/innergen/structure-experience-v21.md for the comparison extension.
No slide SVGs are generated. The v19 selection contract remains compatible.

Usage:
    python scripts/consulting_structure.py check
    python scripts/consulting_structure.py plan projects/my-project
    python scripts/consulting_structure.py preview --output OUTPUTS/structure-preview.html

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parents[3]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from console_encoding import configure_utf8_stdio  # noqa: E402

CATALOG_PATH = ROOT / 'docs/styles/innergen/consulting-structures-v19.json'
EXPERIENCE_PATH = ROOT / 'docs/styles/innergen/structure-experience-v21.json'
ARCHITECTURE_PATH = ROOT / 'docs/styles/innergen/content-architecture-v20.json'


def load_catalog() -> dict:
    """Read the operational catalog without changing the source vocabulary."""
    catalog = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    experience = json.loads(EXPERIENCE_PATH.read_text(encoding='utf-8'))
    architecture = json.loads(ARCHITECTURE_PATH.read_text(encoding='utf-8'))
    for key, layout in experience['layouts'].items():
        catalog['layouts'][key] = {**catalog['layouts'].get(key, {}), **layout}
    experience['deck_stories'] = {}
    modes = ['education_lecture', 'education_handout', 'presentation', 'proposal', 'report_reading']
    reports = ['proposal', 'kickoff', 'interim', 'final', 'education', 'briefing']
    for mode in modes:
        for report in reports:
            deck_id = deck_type(mode, report)
            source = architecture['deck_types'][deck_id]
            base = architecture['deck_types']['lecture'] if deck_id == 'handout' else source
            required = list(base['must_have'])
            required = ['핵심 지표(확인된 원값이 있을 때)' if item == '큰 숫자 3개' else item
                        for item in required]
            if deck_id == 'handout':
                required += ['조건·예외를 문장으로 보존', '질문·정답·이유를 가시적으로 배치']
            experience['deck_stories'][mode + '|' + report] = {
                'deck_type': deck_id, 'label': source['label'],
                'reader_question': source['reader_question'],
                'governing_style': source['governing_style'],
                'flow': experience['deck_flows'][deck_id],
                'must_have': required, 'reference_toc': base['toc'],
                'status': 'suggested_outline_not_confirmed_page_count',
                'note': '사용 방식·보고 성격으로 추정한 구성입니다. 현재 요청·확정 목차·장수가 우선합니다. 수치·사례는 확인된 자료가 있을 때만 넣습니다.'
            }
    catalog['experience'] = experience
    return catalog


def deck_type(mode: str, report: str) -> str:
    """Map existing choices to a suggested v20 deck type without another question."""
    if mode in {'education_lecture', 'education_handout'}:
        return 'lecture' if mode == 'education_lecture' else 'handout'
    if mode == 'proposal' or report == 'proposal':
        return 'proposal'
    if report == 'education':
        return 'seminar'
    if report in {'kickoff', 'interim', 'final', 'briefing'}:
        return report
    return 'seminar' if mode == 'presentation' else 'kickoff'


def catalog_digest() -> str:
    digest = hashlib.sha256()
    for path in (CATALOG_PATH, EXPERIENCE_PATH, ARCHITECTURE_PATH):
        digest.update(path.name.encode('utf-8') + b'\0' + path.read_bytes() + b'\0')
    return digest.hexdigest()


# v24: consulting-diagram goals for business types without an earlier report-based rule.
V24_BUSINESS_GOALS = {'reduction': 'decarbonization', 'climate_risk': 'materiality_risk',
                      'esg_rating': 'materiality_risk', 'climate_tech': 'strategy_portfolio'}


def effective_goal(selection: dict) -> str:
    """Resolve a suggested goal, preserving an explicit user question."""
    if selection.get('structure_goal', 'auto') != 'auto':
        return selection['structure_goal']
    mode = selection.get('style_delivery_mode', '')
    report = selection.get('innergen_report_type', '')
    if mode.startswith('education_'):
        return 'education'
    if mode == 'proposal' or report == 'proposal':
        return 'proposal'
    if report == 'interim':
        return 'progress'
    if selection.get('innergen_business_type') == 'regulatory':
        return 'requirements'
    if report == 'final':
        return 'diagnosis'
    if report == 'kickoff':
        return 'problem_solving'
    business = selection.get('innergen_business_type', '')
    if business in V24_BUSINESS_GOALS:
        return V24_BUSINESS_GOALS[business]
    return 'overview'


def content_mode(selection: dict) -> str:
    mode = selection.get('style_delivery_mode', '')
    if mode.startswith('education_'):
        return 'education'
    if mode in {'presentation', 'proposal'}:
        return mode
    return 'report'


def validate_choice(selection: dict, catalog: dict | None = None) -> list[str]:
    """Validate opt-in fields; old project selections remain valid."""
    catalog = catalog or load_catalog()
    errors = []
    version = selection.get('structure_standard_version')
    if version is not None and str(version) != catalog['version']:
        errors.append('Unknown structure_standard_version; use 19 or omit for a legacy project.')
    goal = selection.get('structure_goal', 'auto')
    if not isinstance(goal, str) or goal not in catalog['goals']:
        errors.append('Unknown structure_goal; choose a listed reader question.')
    if 'structure_goal' in selection and version is None:
        errors.append('structure_goal requires structure_standard_version: 19.')
    return errors


def build_plan(selection: dict, standard: dict) -> dict:
    """Materialize a preferred structure and its evidence requirements."""
    catalog = standard.get('consulting_structure') or load_catalog()
    errors = validate_choice(selection, catalog)
    if errors:
        raise ValueError('; '.join(errors))
    goal = effective_goal(selection)
    candidates = catalog['goals'][goal]['layouts']
    layout_id = selection.get('layout_choice') or candidates[0]
    if layout_id not in standard['layouts']:
        raise ValueError(f'Unknown layout_choice: {layout_id}')
    layout = standard['layouts'][layout_id]
    mode = content_mode(selection)
    plan = {
        'version': catalog['version'], 'catalog_sha256': catalog_digest(),
        'status': 'planning_contract_not_rendered_content',
        'requested_goal': selection.get('structure_goal', 'auto'), 'effective_goal': goal,
        'goal_label': catalog['goals'][goal]['label'],
        'mode': mode, 'mode_contract': catalog['mode_contracts'][mode],
        'preferred_layout': layout_id, 'layout_label': layout['label'],
        'candidate_layouts': candidates,
        'candidate_reason': '독자 질문과 사용 목적에 따른 구성 제안. 원문 관계·근거 확인 후 장별 선택.',
        'recipe_ids': layout.get('recipe_ids', []), 'semantic_ids': layout.get('semantic_ids', []),
        'required_evidence': layout.get('required_evidence', ['원문에서 구조의 관계와 필수 필드를 확인']),
        'protect': layout.get('protect', ['원문 조건·예외·상태·단위·범위를 보존']),
        'qa_rules': catalog['qa_rules'],
        'visual_authority': catalog['visual_authority'],
        'coverage_status': 'source_inventory_and_actual_output_not_reviewed',
        'scope': '덱 전체에 같은 구조를 강제하지 않음. 선택한 구조는 선호 예시이며 장별 근거에 따라 변경.',
        'authoring_handoff': 'design_spec.md에 학습/판단 질문, 근거 ID, 구조·모듈·조건 위치를 기록. 기존 실행 경로 유지.'
    }
    experience = catalog.get('experience')
    if experience:
        story_key = selection['style_delivery_mode'] + '|' + selection['innergen_report_type']
        media = dict(experience['media_plans'][selection['media_mode']])
        suggested_sources = standard['media_modes'][selection['media_mode']]['image_usage']
        actual_sources = selection.get('image_usage', suggested_sources)
        media.update(mode=selection['media_mode'], image_usage=actual_sources,
                     image_notes=selection.get('image_notes', ''), acquisition_status='not_started',
                     detailed_source_override=set(actual_sources) != set(suggested_sources),
                     source_rule='상세 이미지 출처 선택이 우선. 실제 획득은 기존 실행 경로의 이미지 단계에서 수행.')
        plan.update(experience_version=experience['version'],
                    deck_story=experience['deck_stories'][story_key],
                    business_requirements=standard['business_types'][selection['innergen_business_type']]['required'],
                    media_plan=media)
    return plan


def plan_markdown(plan: dict) -> str:
    lines = ['# 교육·제안·구조화 작성 계획', '',
             f"- 작성 목적: {plan['goal_label']}",
             f"- 정보 모드: {plan['mode_contract']['label']}",
             f"- 선호 구조: {plan['layout_label']}",
             '- 상태: 구성 계획. 실제 자료 내용·의미·PPT 출력 검수 전.', '',
             '## 모듈 구성', '']
    lines += [f'{i}. {label}' for i, label in enumerate(plan['mode_contract']['modules'], 1)]
    if plan.get('deck_story'):
        story = plan['deck_story']
        lines += ['', '## 전체 자료 흐름', '', f"구성 제안: {story['label']}", '', story['note'], '']
        lines += [f'- {label}: {value}' for label, value in zip(['도입', '본문', '마무리'], story['flow'])]
        lines += ['', f"문체: {story['governing_style']}", '', '필수 내용:', '']
        lines += [f'- {value}' for value in story['must_have']]
        lines += ['', '## 사업별 확인 항목', '']
        lines += [f'- {value}' for value in plan['business_requirements']]
        media = plan['media_plan']
        lines += ['', '## 도식·그림 작성 계획', '', media['result'], '',
                  '- 필요한 자료: ' + ' · '.join(media['inputs']),
                  '- 진행 순서: ' + ' → '.join(media['steps']),
                  '- 선택된 이미지 출처: ' + ', '.join(media['image_usage']),
                  '- 상태: 아직 검색·생성·삽입하지 않음.', '', media['limit'], '', media['source_rule']]
        if media['detailed_source_override']:
            lines += ['', '상세 출처 선택이 간편 선택과 다릅니다. 확정된 상세 출처에 맞춰 작성합니다.']
    for title, values in [('필수 근거', plan['required_evidence']), ('보존 항목', plan['protect']),
                          ('정보 모드의 보존 항목', plan['mode_contract']['must_preserve']),
                          ('검수 항목', plan['qa_rules'])]:
        lines += ['', f'## {title}', ''] + [f'- {v}' for v in values]
    lines += ['', '## 분할·가시적 배치', '', plan['mode_contract']['overflow'], '',
              plan['mode_contract']['coverage'], '', plan['visual_authority'], '', plan['scope'], '']
    return '\n'.join(lines)


def write_plan(project: Path, plan: dict) -> None:
    """Write generated planning sidecars after the existing confirmation."""
    (project / 'content_plan_v19.json').write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (project / 'content_plan_v19.md').write_text(plan_markdown(plan), encoding='utf-8')


def validate_catalog(standard: dict) -> list[str]:
    catalog = standard['consulting_structure']
    source = json.loads((ROOT / catalog['source_catalog']).read_text(encoding='utf-8'))
    semantic_ids = {v['id'] for v in source['taxonomy']['templates']}
    recipe_ids = {v['id'] for v in source['composition_recipes']}
    errors = []
    for key, layout in catalog['layouts'].items():
        if set(layout.get('semantic_ids', [])) - semantic_ids or set(layout.get('recipe_ids', [])) - recipe_ids:
            errors.append(f'{key}: unresolved source ID')
        if not layout.get('required_evidence') or not layout.get('protect'):
            errors.append(f'{key}: missing evidence/protection contract')
        preview = layout['preview']
        if 'rows' in preview and any(len(row) != len(preview['headers']) for row in preview['rows']):
            errors.append(f'{key}: preview row/header mismatch')
    for key, goal in catalog['goals'].items():
        if key == 'auto':
            continue
        if len(goal['layouts']) != 3 or len(set(goal['layouts'])) != 3:
            errors.append(f'{key}: exactly three distinct recommendations required')
        if set(goal['layouts']) - set(standard['layouts']):
            errors.append(f'{key}: unknown recommended layout')
    for key, layout in standard['layouts'].items():
        if not layout.get('preview') or not layout.get('required_evidence') or not layout.get('protect'):
            errors.append(f'{key}: missing illustrative preview or evidence contract')
    for story in catalog['experience']['deck_stories'].values():
        if len(story['flow']) != 3 or not story['must_have']:
            errors.append(f"{story['deck_type']}: missing opening/body/closing or required content")
    if set(standard['media_modes']) != set(catalog['experience']['media_plans']):
        errors.append('Media intent and plan catalogs differ.')
    return errors


def write_preview(output: Path, standard: dict) -> None:
    """Package the real chooser as a standalone offline simulation."""
    css = (SCRIPTS / 'confirm_ui/static/innergen_studio.css').read_text(encoding='utf-8')
    js = (SCRIPTS / 'confirm_ui/static/innergen_studio.js').read_text(encoding='utf-8')
    data = json.dumps(standard, ensure_ascii=False).replace('</', '<\\/')
    html = '''<!doctype html><html lang="ko"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>교육·제안 장표 구조 비교</title>
<style>body{margin:0;background:#f1f4f8;color:#172638;font:16px 'Malgun Gothic',sans-serif}
header,main{max-width:1280px;margin:auto;padding:24px}header p{line-height:1.7;color:#475569}
h1{font-size:30px;margin:8px 0}header button{font:inherit;padding:10px 16px;background:white;border:1px solid #94a3b8;border-radius:6px;cursor:pointer}
CSS</style><header><p>SLIDE MASTER · 구조 비교 v21</p><h1>교육은 이해·적용까지, 제안은 실행·확인까지</h1>
<p>사용 방식을 고르면 추천 구조 3개가 바뀝니다. 같은 디자인에서 구조와 설명의 차이를 확인하세요.<br>
이 화면은 가상 예시입니다. 선택 내용을 저장해도 기존 프로젝트에는 자동 적용되지 않습니다.</p>
<button id="save">선택 내용 저장</button><span id="save-status" role="status"></span></header><main id="studio"></main>
<script>JS</script><script>
const data=DATA;
const state={style_family:'innergen_basic',style_delivery_mode:'education_handout',innergen_business_type:'cdp_disclosure',innergen_report_type:'education',media_mode:'diagram',structure_goal:'auto',structure_standard_version:'19'};
InnergenStudio.apply(data,state,'style_family',state.style_family);
state.layout_choice=InnergenStudio.recommended(data,state)[0];
function draw(){const host=document.getElementById('studio');host.replaceChildren();InnergenStudio.mount(host,{data,state,onChange:(field,value)=>{const active=document.activeElement&&document.activeElement.getAttribute('aria-label');InnergenStudio.apply(data,state,field,value);draw();if(active){Array.from(host.querySelectorAll('[aria-label]')).find(el=>el.getAttribute('aria-label')===active)?.focus();}}});}
document.getElementById('save').onclick=()=>{const choice=Object.fromEntries(Object.entries(state).filter(([key])=>!key.startsWith('studio_')));Object.assign(choice,{status:'simulation_selection',notApplied:true});const url=URL.createObjectURL(new Blob([JSON.stringify(choice,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='구조_선택_v21.json';a.click();URL.revokeObjectURL(url);document.getElementById('save-status').textContent=' 선택 파일 저장 요청됨 · 프로젝트 미적용';};
draw();</script></html>'''
    html = html.replace('CSS', css).replace('JS</script>', js + '</script>').replace('DATA;', data + ';')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check', help='Check catalog references and preview dimensions.')
    plan_parser = sub.add_parser('plan', help='Materialize confirmed content structure choices.')
    plan_parser.add_argument('project', type=Path)
    preview_parser = sub.add_parser('preview', help='Build an offline simulation of the actual chooser.')
    preview_parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    from style_standard import load_standard, validate_selection

    standard = load_standard()
    errors = validate_catalog(standard)
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    if args.command == 'check':
        print('PASS: structure IDs, evidence contracts, recommendation sets and table dimensions')
    elif args.command == 'preview':
        write_preview(args.output, standard)
        print(args.output)
    else:
        selection = json.loads((args.project / 'confirm_ui/result.json').read_text(encoding='utf-8'))
        errors = validate_selection(selection, standard)
        if (selection.get('status') != 'confirmed' or selection.get('notApplied') or
                selection.get('stage', 'final') != 'final'):
            errors.append('Final confirmed choices are required. A simulation download is not confirmation.')
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        write_plan(args.project, build_plan(selection, standard))
        print(args.project / 'content_plan_v19.md')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
