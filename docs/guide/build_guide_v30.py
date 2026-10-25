#!/usr/bin/env python3
"""Build the Korean unified-confirmation training PDF from versioned content.

Usage: python docs/guide/build_guide_v30.py [--sample] [--font-dir DIR]
Example: python docs/guide/build_guide_v30.py --font-dir C:/Windows/Fonts
Dependencies: reportlab. Font directory must contain malgun.ttf/malgunbd.ttf.
"""

import argparse
import json
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

WIDTH, HEIGHT = 1040, 720
HERE = Path(__file__).resolve().parent


def paragraph(pdf, text, x, top, width, size, color, bold=False, max_height=120):
    style = ParagraphStyle(
        "guide", fontName="GuideBold" if bold else "Guide", fontSize=size,
        leading=size * 1.5, textColor=colors.HexColor(color), wordWrap="CJK",
    )
    item = Paragraph(escape(text), style)
    _, height = item.wrap(width, HEIGHT)
    if height > max_height or top + height > HEIGHT - 30:
        raise ValueError(f"Text exceeds frame: {text[:70]}")
    item.drawOn(pdf, x, HEIGHT - top - height)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--font-dir", type=Path, default=Path("C:/Windows/Fonts"))
    args = parser.parse_args(argv)
    for name, filename in (("Guide", "malgun.ttf"), ("GuideBold", "malgunbd.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(args.font_dir / filename)))
    data = json.loads((HERE / "unified-guide-v30.json").read_text(encoding="utf-8"))
    pages = data["pages"][:1] if args.sample else data["pages"]
    target = (HERE.parents[1] / "tmp/pdfs/unified-guide-sample.pdf" if args.sample
              else HERE / "Slide_Master_단계별_사용안내_v30.pdf")
    target.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(target), pagesize=(WIDTH, HEIGHT), pageCompression=1)
    pdf.setTitle("Slide Master 단계별 사용안내 v30")
    pdf.setAuthor("INNerGEN / Slide Master")
    for number, page in enumerate(pages, 1):
        pdf.setFillColor(colors.HexColor("#0B1739"))
        pdf.rect(0, HEIGHT - 52, WIDTH, 52, fill=1, stroke=0)
        paragraph(pdf, "SLIDE MASTER / 사용 안내 교육자료", 44, 15, 700, 12, "#FFFFFF", True)
        paragraph(pdf, "v30 · 2026-10-25", 830, 15, 180, 12, "#FFFFFF")
        paragraph(pdf, page["title"], 44, 78, 950, 27, "#0B1739", True)
        paragraph(pdf, page["subtitle"], 44, 126, 950, 14, "#52647D")
        for index, (title, body) in enumerate(page["cards"]):
            top = 177 + index * 156
            pdf.setFillColor(colors.HexColor("#F2F5FC"))
            pdf.roundRect(44, HEIGHT - top - 140, 952, 140, 10, fill=1, stroke=0)
            paragraph(pdf, title, 64, top + 14, 910, 18, "#2F62F0", True, 35)
            paragraph(pdf, body, 64, top + 53, 910, 16, "#23334A", max_height=76)
        paragraph(pdf, "기준: Slide Master 통합 확인 절차 · 예시 문구는 교육용", 44, 670, 800, 10, "#52647D")
        paragraph(pdf, f"{number:02d} / {len(pages):02d}", 916, 670, 80, 10, "#52647D")
        pdf.showPage()
    pdf.save()
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
