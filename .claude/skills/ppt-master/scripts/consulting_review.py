#!/usr/bin/env python3
"""
PPT Master - Consulting Content Contract Review

Check declared education coverage, logic, diagram evidence and v3 review records.
Reuse the saved v14 schemas. This does not parse raw prose or prove source truth.
See docs/styles/innergen/consulting-structures-v19.md for the authoring handoff.

Usage:
    python scripts/consulting_review.py review_package.json --output review_result.json

Dependencies:
    jsonschema (already available in the workspace environment)
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from console_encoding import configure_utf8_stdio  # noqa: E402

CONTRACT_PATH = SCRIPTS.parents[3] / 'docs/styles/innergen/design-contracts-v14.json'


def review(package: dict) -> dict:
    """Check declared records without rewriting content or numerical values."""
    if not isinstance(package, dict):
        return _report(['schema: review input must be a JSON object'], [], [])
    from jsonschema import Draft202012Validator

    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))
    errors, warnings, coverage = [], [], []
    def check_finite(value, location: str = 'input') -> None:
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(f'{location}: non-finite numeric value')
        elif isinstance(value, dict):
            for key, child in value.items():
                check_finite(child, f'{location}/{key}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                check_finite(child, f'{location}/{index}')
    check_finite(package)
    document = package.get('document', package)
    is_package = 'document' in package
    schema = contract['review_schemas']['review_package' if is_package else 'dual_view']
    for issue in Draft202012Validator(schema).iter_errors(package):
        errors.append(f"schema/{'/'.join(map(str, issue.path))}: {issue.message}")
    if is_package:
        for issue in Draft202012Validator(contract['review_schemas']['dual_view']).iter_errors(document):
            errors.append(f"document/{'/'.join(map(str, issue.path))}: {issue.message}")
    if errors:
        return _report(errors, warnings, coverage)

    def unique(items: list[dict], name: str) -> dict:
        counts = Counter(item['id'] for item in items)
        for key, count in counts.items():
            if count > 1:
                errors.append(f'{name}: duplicate ID {key}')
        return {item['id']: item for item in items}

    def source(record: dict, label: str, locator: str = 'source_locator') -> None:
        if record['source_id'] not in sources:
            errors.append(f'{label}: unknown source {record["source_id"]}')
        if not record.get(locator, '').strip():
            errors.append(f'{label}: missing source locator')

    sources = unique(document['sources'], 'sources')
    units = unique(document['units'], 'units')
    logic = unique(document['logic_contracts'], 'logic')
    semantics = {item['id'] for item in contract['taxonomy']['templates']}
    recipes = {item['id'] for item in contract['composition_recipes']}
    for key, unit in units.items():
        source(unit, key)
        if unit['source_id'] in sources and unit['source_page'] > sources[unit['source_id']]['pages']:
            errors.append(f'{key}: page outside source')
        if set(unit['same_slide_dependencies']) - set(units):
            errors.append(f'{key}: unknown same-slide dependency')
    for key, item in logic.items():
        source(item, key)
        if set(item['operand_unit_ids']) - set(units):
            errors.append(f'{key}: unknown logical operand')
    scope_reviewed = document['scope_contract']['source_manifest_reviewed']
    if not scope_reviewed:
        warnings.append('원문 범위·정보 목록의 완전성 미검토. 배치율의 백분율을 표시하지 않습니다.')
    for view in document['views']:
        visible, text_by_unit, slide_unit_sets = set(), {}, []
        unique(view['slides'], f"{view['mode']}/slides")
        for slide in view['slides']:
            sid = slide['id']
            if set(slide['structure_ids']) - semantics or slide['recipe_id'] not in recipes:
                errors.append(f'{sid}: unknown structure/recipe')
            unique(slide['blocks'], f'{sid}/blocks')
            page_units = set()
            for block in slide['blocks']:
                if set(block['unit_ids']) - set(units):
                    errors.append(f'{sid}/{block["id"]}: unknown unit')
                is_visible = (slide['exported'] and not slide['hidden'] and block['export_visible']
                              and block['location'] in {'body', 'appendix'})
                if is_visible:
                    page_units.update(block['unit_ids'])
                    for uid in block['unit_ids']:
                        text_by_unit.setdefault(uid, []).append(block['text'])
            visible.update(page_units)
            slide_unit_sets.append((sid, page_units))
        required = {uid for uid, unit in units.items() if unit['in_scope'] and
                    unit['required_in_education' if view['mode'] == 'education' else 'decision_critical']}
        missing = required - visible
        if missing:
            errors.append(f"{view['mode']}: required units not visibly placed: {', '.join(sorted(missing))}")
        for uid in visible & set(units):
            combined = re.sub(r'\s+', '', ' '.join(text_by_unit[uid]))
            for alternatives in units[uid]['guard_groups']:
                if not any(re.sub(r'\s+', '', phrase) in combined for phrase in alternatives):
                    errors.append(f'{view["mode"]}/{uid}: protected phrase group missing: {alternatives}')
            for sid, page_units in slide_unit_sets:
                if uid in page_units and set(units[uid]['same_slide_dependencies']) - page_units:
                    errors.append(f'{sid}/{uid}: same-slide condition/exception missing')
        bindings = {item['logic_id']: item for item in view['logic_bindings']}
        if len(bindings) != len(view['logic_bindings']):
            errors.append(f'{view["mode"]}: duplicate logic binding')
        for lid, binding in bindings.items():
            if lid not in logic:
                errors.append(f'{view["mode"]}: unknown logic {lid}')
            elif (binding['operator'] != logic[lid]['operator'] or
                  set(binding['operand_unit_ids']) != set(logic[lid]['operand_unit_ids'])):
                errors.append(f'{view["mode"]}/{lid}: changed AND/OR operator or operands')
        for lid, item in logic.items():
            if set(item['operand_unit_ids']) & required and lid not in bindings:
                errors.append(f'{view["mode"]}/{lid}: missing logic binding')
        count = len(required & visible)
        coverage.append({'mode': view['mode'], 'required_unique_units': len(required),
                         'declared_visible_unique_units': count,
                         'declared_visible_percent': round(count/len(required)*100, 2)
                         if required and scope_reviewed else None,
                         'basis': 'declared exported/visible fields; actual PPT/PDF not checked'})

    if is_package:
        for kind in ['metrics', 'charts', 'diagnostics', 'progress', 'relations']:
            unique(package[kind], kind)
        metrics = {item['id']: item for item in package['metrics']}
        for item in metrics.values():
            source(item, item['id'])
            pop = item['population']
            if pop['n_total'] is not None and pop['n_valid'] is not None and pop['n_valid'] > pop['n_total']:
                errors.append(f'{item["id"]}: valid sample exceeds total sample')
            if item['aggregation'] == 'share' and not item['denominator_description']:
                errors.append(f'{item["id"]}: share requires a denominator definition')
            if pop['n_valid'] is None and not pop['unknown_reason']:
                errors.append(f'{item["id"]}: missing valid sample/unknown reason')
        for item in package['charts']:
            _check_chart(item, metrics, contract, errors)
        for item in package['diagnostics']:
            key = item['id']
            source(item, key)
            for evidence in item['operation_evidence'] + item['completion_evidence']:
                source(evidence, key, 'locator')
            if item['operating_status'] != 'unknown' and not item['operation_evidence']:
                errors.append(f'{key}: operating assertion requires evidence')
            if item['conclusion_kind'] == 'operating_gap':
                direct = [e for e in item['operation_evidence'] if e['method'] != 'public_document']
                if item['operating_status'] != 'confirmed_absent' or not direct:
                    errors.append(f'{key}: public absence is not proof of an operating gap')
            if item['recommendation_status'] == 'implemented' and not item['completion_evidence']:
                errors.append(f'{key}: implemented action requires completion evidence')
        for item in package['progress']:
            key = item['id']
            for evidence in item['completion_evidence']:
                source(evidence, key, 'locator')
            try:
                as_of = date.fromisoformat(item['as_of'])
                finish = date.fromisoformat(item['actual_finish']) if item['actual_finish'] else None
            except ValueError:
                errors.append(f'{key}: use exact ISO dates for as_of/actual_finish')
                continue
            if item['status'] == 'completed' and (finish is None or not item['completion_evidence']):
                errors.append(f'{key}: completed status requires finish date and evidence')
            if finish and finish > as_of:
                errors.append(f'{key}: actual finish is after the reporting date')
            if item['production_ready'] and item['unresolved_placeholders']:
                errors.append(f'{key}: unresolved draft fields in production-ready record')
        for item in package['relations']:
            ids = [item['from_unit'], item['to_unit']] + item['evidence_unit_ids']
            if set(ids) - set(units):
                errors.append(f'{item["id"]}: unknown relation unit')
            if item['asserted_as_fact'] and (not item['evidence_unit_ids'] or item['kind'] == 'editorial_reading'):
                errors.append(f'{item["id"]}: factual connection requires source evidence')
        for item in package['applicability']:
            if item['unit_id'] not in units:
                errors.append('applicability: unknown unit')
            if item['source_target'] != item['assigned_target']:
                errors.append(f'{item["unit_id"]}: changed source target/asymmetry')
    return _report(errors, warnings, coverage)


def _check_chart(item: dict, metrics: dict, contract: dict, errors: list[str]) -> None:
    key, variant, values = item['id'], item['variant_id'], item['values']
    if variant not in {x['id'] for x in contract['chart_variants']}:
        errors.append(f'{key}: unknown chart variant')
    if set(item['metric_ids']) - set(metrics):
        errors.append(f'{key}: unknown metric')
    if item['intended_use'] == 'production' and item['data_origin'] != 'source_data':
        errors.append(f'{key}: production chart cannot use placeholder/illustrative data')
    if item['data_origin'] != 'source_data' and not item['data_label']:
        errors.append(f'{key}: illustrative data requires a visible label')
    if item['missing_policy'] == 'zero_fill':
        errors.append(f'{key}: missing values cannot be filled with zero')
    if any(v is not None and not math.isfinite(v) for v in values):
        errors.append(f'{key}: non-finite chart value')
    if variant in {'CH01', 'CH02', 'CH03', 'CH04', 'CH05'} and item.get('value_axis_min') != 0:
        errors.append(f'{key}: bar chart requires explicit zero baseline')
    if variant in {'CH05', 'CH09'}:
        if variant == 'CH05' and item.get('expected_total') != 100:
            errors.append(f'{key}: percent composition requires an explicit total of 100')
        if not item.get('is_partition') or not values or any(v is None or v < 0 for v in values):
            errors.append(f'{key}: composition requires a complete nonnegative partition')
        elif 'expected_total' not in item or not math.isclose(sum(values), item['expected_total'],
                                                            abs_tol=item.get('rounding_tolerance', 0), rel_tol=0):
            errors.append(f'{key}: composition sum does not match declared total')
    if variant == 'CH10':
        if not all(k in item for k in ['start', 'deltas', 'end']):
            errors.append(f'{key}: waterfall requires start/deltas/end')
        elif not math.isclose(item['start'] + sum(item['deltas']), item['end'], abs_tol=1e-8, rel_tol=1e-9):
            errors.append(f'{key}: waterfall start + changes != end')
    if variant == 'CH11':
        if item.get('interval_kind', 'unknown') == 'unknown' or not item.get('intervals'):
            errors.append(f'{key}: interval kind and bounds required')
        if any(x['lower'] > x['upper'] for x in item.get('intervals', [])):
            errors.append(f'{key}: reversed interval bounds')
        if item.get('interval_kind') == 'confidence_interval' and 'confidence_level' not in item:
            errors.append(f'{key}: confidence interval requires the supplied confidence level')
    if variant == 'CH15' and (item.get('size_encoding') != 'area' or not item.get('size_legend')
                              or not item.get('sizes')
                              or any(v < 0 for v in item.get('sizes', []))):
        errors.append(f'{key}: bubble requires area encoding, legend and nonnegative sizes')
    if variant == 'CH19' and item.get('direct_comparison'):
        panels = item.get('panels', [])
        axes = {(p['y_min'], p['y_max']) for p in panels}
        if len(panels) < 2 or len(axes) != 1:
            errors.append(f'{key}: directly compared panels require one common axis')
        if any(p['metric_id'] not in metrics or p['y_min'] >= p['y_max'] for p in panels):
            errors.append(f'{key}: invalid panel metric or axis bounds')
        definitions = {(metrics[p['metric_id']]['unit'], metrics[p['metric_id']]['period'],
                        metrics[p['metric_id']]['aggregation']) for p in panels if p['metric_id'] in metrics}
        if len(definitions) > 1:
            errors.append(f'{key}: directly compared panels have inconsistent units/period/aggregation')
    if variant == 'CH20' and (len(item.get('axes', [])) != 2 or not item.get('approval_reason')
                              or not item.get('alternative_review')):
        errors.append(f'{key}: dual axis requires two labeled axes and a documented reason/alternative')


def _report(errors: list[str], warnings: list[str], coverage: list[dict]) -> dict:
    return {'status': 'FAIL' if errors else 'PASS_DECLARED_CONTRACT', 'errors': errors,
            'warnings': warnings, 'declared_coverage': coverage,
            'manual_review_required': ['원문 정보 목록의 완전성', '문장 의미와 근거의 진실성',
                                       '차트 원자료·모형 적합성', '실제 PPT/PDF 글꼴·잘림·겹침·읽기 순서'],
            'not_implemented': ['임의 원문 자동 의미 추출', '법규 현행성·적정성 인증', '51종 범용 PPT 렌더링'],
            'scope': '기존 v2/v3 명시적 계약의 부분 자동 점검. 실제 교육자료 완성·배포 승인 판정이 아님.'}


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if args.output and args.output.resolve() == args.input.resolve():
        parser.error('Choose a separate --output path to preserve the source review record.')
    try:
        package = json.loads(args.input.read_text(encoding='utf-8'))
        if not isinstance(package, dict):
            raise ValueError('The review input must be a JSON object.')
        result = review(package)
    except ImportError:
        print('jsonschema is unavailable. Run with the workspace .venv Python containing jsonschema.', file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Cannot review input: {exc}. Use the saved v14 dual_view/review_package schema.', file=sys.stderr)
        return 2
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
