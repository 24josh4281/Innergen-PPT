"""Native editable equations: SVG <text data-pptx-equation> -> OMML text box.

The SVG carries the LaTeX source in ``data-pptx-equation`` and preview tspans
for browser rendering. Export replaces the whole <text> with a PowerPoint
equation text box (``a14:m`` inside ``mc:AlternateContent``) so the formula
stays editable in Insert > Equation. The ``mc:Fallback`` branch holds the
Unicode linear form for consumers without Office Math support.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

from omml_math import (
    A14_NS,
    MC_NS,
    EquationError,
    equation_height_factor,
    estimate_width_em,
    linear_text,
    pptx_math_paragraph,
    pptx_rpr,
)

from .context import ConvertContext, ShapeResult
from .utils import (
    _get_attr, _xml_escape, ctx_x, ctx_y, parse_font_family, parse_hex_color,
    parse_svg_length, px_to_emu, svg_length_x, svg_length_y,
)

EQUATION_ATTR = 'data-pptx-equation'
PX_PER_PT = 4.0 / 3.0


def is_equation_text(elem: ET.Element) -> bool:
    return bool((elem.get(EQUATION_ATTR) or '').strip())


def _shape_xml(shape_id: int, name: str, xfrm: str, body_pr: str, paragraph: str) -> str:
    return (
        f'<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{_xml_escape(name)}"/>'
        f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        f'<p:spPr>{xfrm}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        f'<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        f'<p:txBody>{body_pr}<a:lstStyle/>{paragraph}</p:txBody></p:sp>'
    )


def convert_equation(elem: ET.Element, ctx: ConvertContext) -> ShapeResult:
    """Convert an equation-carrier <text> to a native OMML text box."""
    latex = elem.get(EQUATION_ATTR, '').strip()
    elem_id = elem.get('id') or 'equation'
    try:
        linear = linear_text(latex)
        width_em = estimate_width_em(latex)
        height_factor = equation_height_factor(latex)
    except EquationError as exc:
        raise ValueError(f'{elem_id}: {exc}') from exc

    x = ctx_x(svg_length_x(elem.get('x'), ctx), ctx)
    y = ctx_y(svg_length_y(elem.get('y'), ctx), ctx)
    font_px = parse_svg_length(_get_attr(elem, 'font-size', ctx), 16, font_size=16) * ctx.scale_y
    anchor = _get_attr(elem, 'text-anchor', ctx) or 'start'
    color = parse_hex_color(_get_attr(elem, 'fill', ctx) or '#000000') or '000000'
    fonts = parse_font_family(_get_attr(elem, 'font-family', ctx) or '')
    ea_font = fonts.get('ea') or fonts.get('latin')
    bold = (_get_attr(elem, 'font-weight', ctx) or '400') in ('bold', '600', '700', '800', '900')

    width = max(width_em * font_px, font_px)
    height = height_factor * font_px * 1.25
    # The SVG y is the baseline of the main line; tall structures (fractions,
    # limits) grow symmetrically around the math axis.
    top = y - font_px * 0.95 - (height_factor - 1.0) * font_px * 0.5
    if anchor == 'middle':
        left, align = x - width / 2, 'ctr'
    elif anchor == 'end':
        left, align = x - width, 'r'
    else:
        left, align = x, 'l'

    size_pt = font_px / PX_PER_PT
    rpr = pptx_rpr(size_pt, color=color, ea_font=ea_font, bold=bold)
    end_rpr = f'<a:endParaRPr lang="en-US" sz="{int(round(size_pt * 100))}" dirty="0"/>'
    xfrm = (
        f'<a:xfrm><a:off x="{px_to_emu(left)}" y="{px_to_emu(top)}"/>'
        f'<a:ext cx="{px_to_emu(width)}" cy="{px_to_emu(height)}"/></a:xfrm>'
    )
    body_pr = (
        '<a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0" rtlCol="0">'
        '<a:spAutoFit/></a:bodyPr>'
    )
    shape_id = ctx.claim_shape_id(elem.get('data-pptx-shape-id'), elem.get('data-pptx-shape-scope'))
    name = f'Equation {elem_id}'
    math_paragraph = pptx_math_paragraph(latex, rpr, align=align, end_rpr=end_rpr)
    algn_attr = f' algn="{align}"' if align != 'l' else ''
    fallback_paragraph = (
        f'<a:p><a:pPr{algn_attr}/><a:r><a:rPr lang="en-US" sz="{int(round(size_pt * 100))}" dirty="0">'
        f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
        f'<a:latin typeface="Cambria Math"/></a:rPr><a:t>{_xml_escape(linear)}</a:t></a:r></a:p>'
    )
    xml = (
        f'<mc:AlternateContent xmlns:mc="{MC_NS}" xmlns:a14="{A14_NS}">'
        f'<mc:Choice Requires="a14">{_shape_xml(shape_id, name, xfrm, body_pr, math_paragraph)}</mc:Choice>'
        f'<mc:Fallback>{_shape_xml(shape_id, name, xfrm, body_pr, fallback_paragraph)}</mc:Fallback>'
        f'</mc:AlternateContent>'
    )
    off_x, off_y = px_to_emu(left), px_to_emu(top)
    return ShapeResult(
        xml=xml,
        bounds_emu=(off_x, off_y, off_x + px_to_emu(width), off_y + px_to_emu(height)),
    )
