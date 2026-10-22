"""Run: python -m unittest discover -s tests -p 'test_*.py' -v"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "claude-skills/innergen-deck/scripts"
sys.path.insert(0, str(SCRIPTS))
from card_layout import apply_card_layout, layout_svg, CardLayoutError, wrap_text
from svg_to_pptx.drawingml.converter import convert_svg_to_slide_shapes
from svg_to_pptx.pptx_package.template_structure import parse_template_slide

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main", "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}

def fixture(body="짧은 설명", number="250만 톤", height=260):
    from xml.sax.saxutils import escape
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" data-pptx-page-role="content">
<rect id="card" x="20" y="30" width="320" height="{height}" fill="#F2F2F2" data-card-members="title number body" data-card-padding="12" data-card-gap="8"/>
<text id="title" x="32" y="55" font-size="16" fill="#041E42">사업 현황</text>
<text id="number" x="32" y="95" font-size="28" fill="#041E42">{escape(number)}</text>
<g id="body" data-card-slot-bounds="20 110 320 150"><text x="32" y="125" font-size="14" fill="#041E42">{escape(body)}</text></g>
</svg>'''

class CardTests(unittest.TestCase):
    def check_geometry(self, svg):
        root = ET.fromstring(svg)
        report = apply_card_layout(root)[0]
        self.assertAlmostEqual(report["top"], report["bottom"])
        self.assertGreaterEqual(report["top"], 12)
        boxes = report["members"]
        for a, b in zip(boxes, boxes[1:]):
            self.assertAlmostEqual(b["y"] - a["y"] - a["h"], 8)
        for box in boxes:
            self.assertGreaterEqual(box["x"], 32)
            self.assertLessEqual(box["x"] + box["w"], 328)
            self.assertLessEqual(box["y"] + box["h"], 30 + 260 - 12)
        return root, report

    def test_short_medium_long_and_explicit_newlines(self):
        heights = []
        for body in ("짧은 설명", "활동자료 수집 및 배출량 산정 결과 확인", "배출량 산정 결과 확인\n근거 자료 검토 및 담당자 확인\n추가 보완 항목과 제출 일정 관리"):
            root, report = self.check_geometry(fixture(body))
            heights.append(report["members"][-1]["h"])
            # Idempotence is needed when a pre-laid-out preview is exported.
            again = apply_card_layout(root)[0]
            self.assertEqual(report, again)
        self.assertGreater(heights[-1], heights[0])

    def test_known_total_height(self):
        _, report = self.check_geometry(fixture())
        # 16*1.5 + 28*1.5 + 14*1.5 + two 8px gaps = 103px.
        self.assertEqual(report["top"], (260 - 103) / 2)

    def test_overflow_is_atomic(self):
        root = ET.fromstring(fixture("설명\n" * 30))
        before = ET.tostring(root)
        with self.assertRaisesRegex(CardLayoutError, "content height"):
            apply_card_layout(root)
        self.assertEqual(before, ET.tostring(root))

    def test_unbreakable_word_does_not_split_into_characters(self):
        with self.assertRaisesRegex(CardLayoutError, "word exceeds"):
            layout_svg(fixture("가" * 60))
        self.assertEqual(wrap_text("46%", 50, 20), ["46%"])

    def test_empty_content_leaves_no_phantom_gap(self):
        root = ET.fromstring(fixture(""))
        report = apply_card_layout(root)[0]
        self.assertEqual(len(report["members"]), 2)
        self.assertEqual(report["top"], (260 - 24 - 42 - 8) / 2)

    def test_missing_duplicate_and_transformed_members_fail(self):
        for source in (fixture().replace('title number body', 'title missing'), fixture().replace('title number body', 'title title'), fixture().replace('<g id="body"', '<g transform="translate(0 2)" id="body"'), fixture().replace('data-card-padding="12"', 'data-card-padding="-1"')):
            with self.assertRaises(CardLayoutError):
                layout_svg(source)

    def test_legacy_and_unfilled_template_unchanged(self):
        source = fixture().replace(' data-card-members="title number body"', '')
        self.assertEqual(layout_svg(source), source)
        root = ET.fromstring(fixture("{{DESCRIPTION}}"))
        before = ET.tostring(root)
        self.assertEqual(apply_card_layout(root), [])
        self.assertEqual(before, ET.tostring(root))

    def test_native_export_keeps_three_editable_frames_and_left_alignment(self):
        root, report = self.check_geometry(fixture("첫째 근거 확인\n둘째 자료 검토"))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "01_card.svg"
            path.write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
            xml, *_ = convert_svg_to_slide_shapes(path)
        native = ET.fromstring(xml)
        text_shapes = [e for e in native.findall('.//p:sp', NS) if e.find('p:txBody', NS) is not None]
        self.assertEqual(len(text_shapes), 3)
        for shape, expected in zip(text_shapes, report["members"]):
            off = shape.find('p:spPr/a:xfrm/a:off', NS)
            ext = shape.find('p:spPr/a:xfrm/a:ext', NS)
            self.assertAlmostEqual(int(off.get('y')) / 9525, expected['y'], places=3)
            self.assertAlmostEqual(int(ext.get('cy')) / 9525, expected['h'], places=3)
            self.assertIsNone(shape.find('.//a:spAutoFit', NS))
            self.assertTrue(all(p.get('algn') == 'l' for p in shape.findall('.//a:pPr', NS)))
        self.assertEqual(len(native.findall('.//p:pic', NS)), 0)
        paragraphs = text_shapes[-1].findall('p:txBody/a:p', NS)
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(''.join(paragraphs[0].itertext()).strip(), '첫째 근거 확인')

    def test_per_member_gaps_are_preserved(self):
        root = ET.fromstring(fixture().replace('id="title"', 'id="title" data-card-gap-after="18"'))
        report = apply_card_layout(root)[0]
        a, b, c = report['members']
        self.assertAlmostEqual(b['y'] - a['y'] - a['h'], 18)
        self.assertAlmostEqual(c['y'] - b['y'] - b['h'], 8)
        self.assertEqual(report['top'], report['bottom'])

    def test_blank_line_survives_native_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'card.svg'
            path.write_text(fixture('첫 줄\n\n끝 줄'), encoding='utf-8')
            xml, *_ = convert_svg_to_slide_shapes(path)
        native = ET.fromstring(xml)
        bodies = native.findall('.//p:sp/p:txBody', NS)
        self.assertEqual(len(bodies[-1].findall('a:p', NS)), 3)

    def test_v30_all_three_families_and_noncard_templates_preserved(self):
        # Build reproducibility and exact preservation of unrelated templates.
        spec = importlib.util.spec_from_file_location("v30", ROOT / "docs/innergen-v30/build_templates_v30.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        result = module.build(ROOT / "claude-skills/innergen-deck", None, False)
        self.assertEqual(sum(len(v) for v in result.values()), 30)
        for family in module.FAMILIES:
            path = f"claude-skills/innergen-deck/templates/decks/{family}.json"
            data = json.loads((ROOT / path).read_text())
            baseline = json.loads(subprocess.check_output(["git", "show", f"83e30835aee9b8116c1ac987218e7876eadf9695:{path}"], cwd=ROOT))
            for name, svg in data.items():
                if not any(f"s{i}_" in name for i in range(65, 75)):
                    continue
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / 'template.svg'
                    path.write_text(svg, encoding='utf-8')
                    unfilled = parse_template_slide(path, 1)
                    # All tokens become a compact one-line value; layout at export.
                    import re
                    filled = re.sub(r"\{\{[^}]+\}\}", "확인", svg)
                    laid_out = layout_svg(filled)
                    path.write_text(laid_out, encoding='utf-8')
                    ready = parse_template_slide(path, 1)
                    self.assertEqual([e.contract_signature() for e in unfilled.elements], [e.contract_signature() for e in ready.elements])
            for name in baseline:
                if not any(f"s{i}_" in name for i in range(65, 75)):
                    self.assertEqual(data[name], baseline[name], name)

if __name__ == '__main__':
    unittest.main()
