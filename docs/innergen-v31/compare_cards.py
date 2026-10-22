#!/usr/bin/env python3
"""Reproduce card length comparisons via the production native SVG exporter."""
import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'claude-skills/innergen-deck/scripts'
sys.path.insert(0, str(SCRIPTS))
from card_layout import apply_card_layout

SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)

CASES = [
    ('짧은 내용', '사업 현황', '46%', '배출량 산정 완료'),
    ('두 줄 설명', '자료 검토', '128건', '활동자료 수집 및 배출량 검토\n증빙 자료와 담당자 확인'),
    ('긴 내용', '개선 과제 이행 현황', '2026년', '보완 자료 수집과 산정 근거 확인\n추가 검토 항목 및 제출 일정 관리\n담당자별 진행 현황 확인'),
]

def slide(after):
    header = '콘텐츠 묶음 수직 중앙 정렬' if after else '기존 고정 좌표 배치'
    rows = [f'<svg xmlns="{SVG}" viewBox="0 0 960 540" data-pptx-page-role="content">',
            '<rect x="0" y="0" width="960" height="540" fill="#FFFFFF"/>',
            f'<text x="34" y="48" font-family="Malgun Gothic" font-size="24" font-weight="700" fill="#041E42">{header}</text>']
    for index, (label, title, number, body) in enumerate(CASES):
        x = 34 + index * 300
        rows.extend([
            f'<text x="{x}" y="91" font-family="Malgun Gothic" font-size="14" fill="#595959">{label}</text>',
            f'<rect id="card-{index}" x="{x}" y="110" width="280" height="360" fill="#F2F2F2" data-card-members="title-{index} number-{index} body-{index}" data-card-gap="14" data-card-padding="18"/>',
            f'<text id="title-{index}" x="{x+18}" y="145" font-family="Malgun Gothic" font-size="17" font-weight="700" fill="#041E42">{title}</text>',
            f'<text id="number-{index}" x="{x+18}" y="191" font-family="Malgun Gothic" font-size="30" font-weight="700" fill="#00A9E0">{number}</text>',
            f'<text id="body-{index}" x="{x+18}" y="236" font-family="Malgun Gothic" font-size="15" fill="#041E42">'])
        for i, line in enumerate(body.split('\n')):
            rows.append(f'<tspan x="{x+18}" dy="{22.5 if i else 0}">{escape(line)}</tspan>')
        rows.append('</text>')
    rows.append('</svg>')
    root = ET.fromstring('\n'.join(rows))
    report = apply_card_layout(root) if after else []
    if not after:
        # Deliberately keep the parent renderer's authored fixed positions.
        for rect in root.findall(f'{{{SVG}}}rect'):
            rect.attrib.pop('data-card-members', None)
    return ET.tostring(root, encoding='unicode'), report


def main():
    out = ROOT / 'docs/generated/cards-v31/svg'
    for version in ('before', 'after'):
        project = out / version
        (project / 'svg_output').mkdir(parents=True, exist_ok=True)
        svg, report = slide(version == 'after')
        (project / 'svg_output/01_cards.svg').write_text(svg, encoding='utf-8')
        (project / 'spec_lock.md').write_text('## pptx_structure\n- mode: flat\n', encoding='utf-8')
        if report:
            (out / 'geometry.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        subprocess.run([sys.executable, str(SCRIPTS / 'svg_to_pptx.py'), str(project), '--no-notes'], check=True)
    comparison = out.parent / 'comparison'
    (comparison / 'svg_output').mkdir(parents=True, exist_ok=True)
    (comparison / 'spec_lock.md').write_text('## pptx_structure\n- mode: flat\n', encoding='utf-8')
    for index, version in enumerate(('before', 'after'), 1):
        (comparison / 'svg_output' / f'{index:02d}_{version}.svg').write_bytes(
            (out / version / 'svg_output/01_cards.svg').read_bytes())
    subprocess.run([sys.executable, str(SCRIPTS / 'svg_to_pptx.py'), str(comparison), '--no-notes'], check=True)
    print(out)

if __name__ == '__main__':
    main()
