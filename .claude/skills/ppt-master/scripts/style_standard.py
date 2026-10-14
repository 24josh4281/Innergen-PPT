#!/usr/bin/env python3
"""
PPT Master - Named Design Standard

Load v17 and materialize its chosen profile without replacing project locks.
Confirmed user choices always override recommendations; no template is staged.

Usage:
    python scripts/style_standard.py projects/my-project
    python scripts/style_standard.py --check

Dependencies:
    None (standard library only)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from consulting_structure import (
    build_plan,
    load_catalog,
    validate_choice,
    write_plan,
)

STANDARD_PATH = Path(__file__).resolve().parents[4] / 'docs/styles/innergen/design-standard-v17.json'


def load_standard():
    data = json.loads(STANDARD_PATH.read_text(encoding='utf-8'))
    catalog = load_catalog()
    data['consulting_structure'] = catalog
    for key, layout in catalog['layouts'].items():
        data['layouts'][key] = {**data['layouts'].get(key, {}), **layout}
    return data


def validate_standard(data):
    errors = []
    for family, profile in data['profiles'].items():
        w, h = profile['canvas_pt']
        if any(abs(pt - px * .75) > .001 for pt, px in zip(profile['canvas_pt'], profile['canvas_px'])):
            errors.append(f'{family}: canvas unit mismatch')
        for role, (x, y, rw, rh) in profile['zones_pt'].items():
            if min(x, y, rw, rh) < 0 or x + rw > w or y + rh > h:
                errors.append(f'{family}/{role}: outside canvas')
            px = profile['zones_px'][role]
            if any(abs(a - b * .75) > .001 for a, b in zip((x,y,rw,rh), px)):
                errors.append(f'{family}/{role}: geometry units differ')
    for mode, values in data['modes'].items():
        for role, pt in values['pt'].items():
            if abs(pt - values['px'][role] * .75) > .001:
                errors.append(f'{mode}/{role}: font units differ')
    return errors


def validate_selection(payload, data=None):
    data = data or load_standard()
    if payload.get('style_family') is None or payload.get('style_family') == '':
        return []
    errors = []
    fields = {'style_family':'profiles','style_delivery_mode':'modes',
              'innergen_business_type':'business_types','innergen_report_type':'report_types',
              'layout_choice':'layouts','media_mode':'media_modes'}
    for field, catalog in fields.items():
        if not isinstance(payload.get(field), str) or payload.get(field) not in data[catalog]:
            errors.append(f'Unknown {field}: {payload.get(field)}')
    errors.extend(validate_choice(payload, data.get('consulting_structure')))
    ty = payload.get('typography') or {}
    if isinstance(ty, dict):
        sizes = ty.get('sizes') or {}
        if not isinstance(sizes, dict):
            errors.append('Typography sizes must be an object.')
            sizes = {}
        values = dict(sizes)
        if 'body_size' in ty: values['body_size'] = ty['body_size']
        for role,value in values.items():
            try:
                valid = math.isfinite(float(value)) and float(value) > 0
            except (ValueError, TypeError):
                valid = False
            if not valid: errors.append(f'Invalid positive px size for {role}: {value}')
        if ty.get('body_size_unit', 'px') != 'px':
            errors.append('Confirmed typography must use px; convert pt before submitting.')
    else:
        errors.append('Typography must be an object.')
    return errors


def source_digest(payload):
    keys = ('style_family','style_delivery_mode','innergen_business_type','innergen_report_type',
            'layout_choice','media_mode','canvas','typography','color','image_usage','image_notes',
            'structure_goal','structure_standard_version')
    values = {k:payload[k] for k in keys if k in payload}
    return hashlib.sha256(json.dumps(values,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def resolve(payload, data=None):
    data = data or load_standard()
    errors = validate_selection(payload, data)
    if errors: raise ValueError('; '.join(errors))
    family = payload['style_family']
    profile = data['profiles'][family]
    mode = data['modes'][payload['style_delivery_mode']]
    result = {'version':data['version'],'family':family,'delivery_mode':payload['style_delivery_mode'],
              'profile':profile,'typography_pt':dict(mode['pt']),'typography_px':dict(mode['px']),
              'spacing_pt':data['spacing_pt'],'text_rules':data['text'],
              'business':data['business_types'][payload['innergen_business_type']],
              'report':data['report_types'][payload['innergen_report_type']],
              'layout':data['layouts'][payload['layout_choice']],
              'media':data['media_modes'][payload['media_mode']], 'media_rules':data['media_rules'],
              'confirmed_choices':payload,'selection_sha256':source_digest(payload),
              'standard_sha256':hashlib.sha256(STANDARD_PATH.read_bytes()).hexdigest(),
              'geometry_status':'standard profile; recompose for a confirmed custom canvas',
              'execution_note':'Input to design_spec.md/spec_lock.md; does not replace either file or authorize skipping owner gates.'}
    ty = payload.get('typography') or {}
    # A family may pin role sizes its fixed template geometry depends on.
    for role, pt in (profile.get('typography_pt_overrides') or {}).get(payload['style_delivery_mode'], {}).items():
        result['typography_pt'][role] = float(pt)
        result['typography_px'][role] = float(pt) / .75
    result['font'] = (ty.get('body') or {}).get('cjk') or profile['font']
    result['heading_font'] = (ty.get('heading') or {}).get('cjk') or result['font']
    result['text_colors'] = dict(profile['text_colors'])
    result['colors'] = dict(profile['colors'])
    mapping = {'background':'background','secondary_bg':'panel','primary':'primary',
               'accent':'accent','secondary_accent':'muted','body_text':'text'}
    for role,value in ((payload.get('color') or {}).get('palette') or {}).items():
        if role in mapping: result['colors'][mapping[role]] = value
    # Roles that use the profile text color follow an edited text color; accent roles keep theirs.
    for role in ('body','governing','table'):
        if profile['text_colors'].get(role) == profile['colors']['text']:
            result['text_colors'][role] = result['colors']['text']
    result['layout_selection_scope'] = 'preferred structure; choose other evidence-appropriate structures per page'
    for key,value in (ty.get('sizes') or {}).items():
        target = {'subtitle':'governing','annotation':'note'}.get(key,key)
        # Explicit semantic roles win over legacy aliases.
        if key in ('subtitle','annotation') and target in ty.get('sizes',{}): continue
        if target in result['typography_px']:
            result['typography_px'][target] = float(value)
            result['typography_pt'][target] = float(value) * .75
    if ty.get('body_size') is not None:
        result['typography_px']['body'] = float(ty['body_size'])
        result['typography_pt']['body'] = float(ty['body_size']) * .75
    result['canvas'] = payload.get('canvas') or profile['canvas']
    if result['canvas'] != profile['canvas']:
        result['geometry_status'] = 'REQUIRES_RECOMPOSITION: confirmed canvas differs; do not reuse profile coordinates'
    if str(payload.get('structure_standard_version', '')) == '19':
        result['content_structure'] = build_plan(payload, data)
    return result


def check_project(project):
    result_file = project / 'confirm_ui/result.json'
    if not result_file.exists(): return []
    payload = json.loads(result_file.read_text(encoding='utf-8'))
    if not payload.get('style_family'): return []
    errors = validate_selection(payload)
    profile_file = project / 'design_profile_v17.json'
    if not profile_file.exists():
        return errors + ['Run style_standard.py <project> to materialize the confirmed named profile.']
    profile = json.loads(profile_file.read_text(encoding='utf-8'))
    if profile.get('selection_sha256') != source_digest(payload):
        errors.append('design_profile_v17.json is stale relative to confirmed choices.')
    if profile.get('standard_sha256') != hashlib.sha256(STANDARD_PATH.read_bytes()).hexdigest():
        errors.append('design_profile_v17.json is stale relative to the standard.')
    if str(payload.get('structure_standard_version', '')) == '19':
        expected = build_plan(payload, load_standard()) if not errors else None
        if expected and profile.get('content_structure') != expected:
            errors.append('design_profile_v17.json has stale structure choices; run style_standard.py <project>.')
        plan_file = project / 'content_plan_v19.json'
        if not plan_file.exists():
            errors.append('Missing content_plan_v19.json; run style_standard.py <project>.')
        elif expected and json.loads(plan_file.read_text(encoding='utf-8')) != expected:
            errors.append('content_plan_v19.json is stale relative to confirmed choices or structure catalog.')
        review_file = project / 'analysis/source_review_v19.json'
        if review_file.exists():
            try:
                from consulting_review import review
                content = review(json.loads(review_file.read_text(encoding='utf-8')))
                errors.extend('Content contract: ' + error for error in content['errors'])
            except (ImportError, ValueError, TypeError, KeyError) as exc:
                errors.append(f'Cannot check source_review_v19.json: {exc}; use the workspace Python and v14 schema.')
    lock = project / 'spec_lock.md'
    if lock.exists():
        content = lock.read_text(encoding='utf-8')
        match = re.search(r'^## style_standard\s*\n(.*?)(?=^## |\Z)', content, re.M | re.S)
        if not match:
            errors.append('spec_lock.md must record ## style_standard with the version, family and profile file.')
        else:
            for key,value in {'version':'17','family':payload.get('style_family'),
                              'delivery_mode':payload.get('style_delivery_mode'),
                              'profile_file':'design_profile_v17.json'}.items():
                if not re.search(r'^-\s*'+key+r':\s*'+re.escape(str(value))+r'\s*$', match.group(1), re.M):
                    errors.append(f'spec_lock.md style_standard must record {key}: {value}')
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path, nargs='?')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    data = load_standard()
    errors = validate_standard(data)
    if errors: raise SystemExit('\n'.join(errors))
    if args.check:
        print('PASS: canvases, zones and pt/px role sizes')
        return 0
    if not args.project: parser.error('project or --check required')
    payload = json.loads((args.project/'confirm_ui/result.json').read_text(encoding='utf-8'))
    if (payload.get('status') != 'confirmed' or payload.get('notApplied') or
            payload.get('stage', 'final') != 'final'):
        print('Final confirmed choices are required. A simulation or intermediate stage cannot be applied.')
        return 1
    profile = resolve(payload,data)
    dest = args.project/'design_profile_v17.json'
    dest.write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md = '# 선택된 디자인 수치 기준\n\n' + data['profiles'][payload['style_family']]['label'] + '\n\n'
    md += '| 역할 | PPT pt | SVG px |\n|---|---:|---:|\n'
    md += '\n'.join(f'| {k} | {v:.3f} | {profile["typography_px"][k]:.3f} |' for k,v in profile['typography_pt'].items())
    md += '\n\n글꼴: '+profile['font']+'\n\n'+profile['geometry_status']+'\n\n'
    md += '아래 항목을 프로젝트 잠금에 기록하고 JSON의 색·여백·영역을 프로젝트 명세에 옮긴다.\n\n'
    md += '```\n## style_standard\n- version: 17\n- family: '+profile['family']+'\n- delivery_mode: '+profile['delivery_mode']+'\n- profile_file: design_profile_v17.json\n```\n'
    (args.project/'design_profile_v17.md').write_text(md,encoding='utf-8')
    if profile.get('content_structure'):
        write_plan(args.project, profile['content_structure'])
    print(dest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
