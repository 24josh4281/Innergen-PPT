"""INNerGEN original proposal frame (v35) templates, measured from the OCI 261030 final proposal (780x540pt -> 1040x720px)."""
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / 'templates' / 'decks' / 'innergen' / 'templates'
FONT = 'IBM Plex Sans KR, Malgun Gothic, sans-serif'
NAVY, GRID, FAINT, BLUE, GREY, MUTED = '#0F243F', '#2E4059', '#F2F2F2', '#2F6DB5', '#7F7F7F', '#A6A6A6'
HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1040 720" '
        'data-pptx-master="innergen-master-13x9" data-pptx-master-name="이너젠 오리지널 13:9" '
        'data-pptx-layout="{key}" data-pptx-layout-name="{name}">\n'
        '<rect id="master-bg" x="0" y="0" width="1040" height="720" fill="#FFFFFF" data-pptx-layer="master" data-pptx-editable="false"/>\n')
LAY = ' data-pptx-layer="layout" data-pptx-editable="false"'


def ph(gid, kind, bounds, x, y, size, weight, fill, token, idx=None, anchor='start', vanchor=None):
    i = f' data-pptx-placeholder-idx="{idx}"' if idx is not None else ''
    a = f' data-pptx-placeholder-anchor="{vanchor}"' if vanchor else ''
    return (f'<g id="{gid}" data-pptx-placeholder="{kind}"{a}{i} data-pptx-placeholder-bounds="{bounds}">'
            f'<text id="{gid}-carrier" data-pptx-placeholder-carrier="true" x="{x}" y="{y}" text-anchor="{anchor}" '
            f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" fill="{fill}">{token}</text></g>\n')


def faint_lines(ys):
    return ''.join(f'<line id="faint-h-{y}" x1="0" y1="{y}" x2="1040" y2="{y}" stroke="{FAINT}" stroke-width="1"{LAY}/>\n' for y in ys)



def chrome(page=True):
    s = faint_lines((11, 25))
    s += f'<path id="header-strip" d="M0 53.3 H866.7 L853.3 66.7 H0 Z" fill="{NAVY}"{LAY}/>\n'
    s += ''.join(f'<line id="header-grid-v-{x}" x1="{x}" y1="54" x2="{x}" y2="66" stroke="{GRID}" stroke-width="0.6"{LAY}/>\n'
                 for x in range(16, 860, 16))
    s += f'<line id="header-grid-h" x1="0" y1="60" x2="858" y2="60" stroke="{GRID}" stroke-width="0.6"{LAY}/>\n'
    s += faint_lines((661, 676, 692, 707))
    s += f'<image id="footer-logo" x="30" y="666" width="72" height="44" xlink:href="../images/innergen-logo-cover-blue.png" preserveAspectRatio="xMidYMid meet"{LAY}/>\n'
    s += (f'<text id="footer-tagline" x="116" y="693" font-family="{FONT}" font-size="10.67" font-weight="700" fill="#000000"{LAY}>'
          'Innovative Ideas │ Better Solution</text>\n')
    s += (f'<text id="footer-copyright" x="1013" y="693" text-anchor="end" font-family="{FONT}" font-size="10.67" font-weight="400" fill="{GREY}"{LAY}>'
          'Copyright © 2026 INNerGEN Co Ltd. All rights reserved.</text>\n')
    if page:
        s += ph('page-number', 'slide-number', '490 676 60 24', 520, 693, 12, 400, '#000000', '{{PAGE_NUM}}', idx=9, anchor='middle')
    return s


def title(gid, token='{{PAGE_TITLE}}'):
    return ph(gid, 'title', '20 6 760 44', 23, 39, 26.67, 700, '#000000', token)


def content():
    s = HEAD.format(key='innergen-proposal-content', name='이너젠 오리지널 제안 본문') + chrome()
    s += f'<circle id="governing-marker-back" cx="36" cy="88" r="9" fill="#BFBFBF"{LAY}/>\n'
    s += f'<circle id="governing-marker-front" cx="47" cy="88" r="9" fill="{NAVY}"{LAY}/>\n'
    s += title('content-title')
    s += ph('content-key-message', 'body', '62 72 950 32', 64, 94, 17.33, 700, '#000000', '{{KEY_MESSAGE}}', idx=1)
    s += ph('content-area', 'body', '44 112 952 528', 61, 133, 16, 400, '#000000', '{{CONTENT_AREA}}', idx=3, vanchor='top')
    s += ph('content-source', 'footer', '44 640 952 18', 44, 653, 10.67, 400, '#595959', '{{SOURCE}}', idx=4)
    return s + '</svg>\n'


def contents(key, name, current):
    s = HEAD.format(key=key, name=name) + chrome()
    s += f'<image id="contents-logo" x="110" y="200" width="300" height="300" xlink:href="../images/innergen-logo-cover-blue.png" preserveAspectRatio="xMidYMid meet"{LAY}/>\n'
    s += title('contents-title', 'CONTENTS')
    nums = ['I', 'II', 'III', 'IV']
    for i, n in enumerate(nums, 1):
        y = 210 + (i - 1) * 76
        on = current in (None, i)
        fill, weight = (NAVY, 700) if on else (MUTED, 400)
        s += f'<line id="toc-rule-{i}" x1="640" y1="{y + 16}" x2="990" y2="{y + 16}" stroke="#BFBFBF" stroke-width="1"{LAY}/>\n'
        s += ph(f'toc-item-{i}', 'body', f'640 {y - 30} 350 40', 645, y, 24, weight, fill, f'{n}. {{{{TOC_ITEM_{i}_TITLE}}}}', idx=i)
    return s + '</svg>\n'


def cover():
    s = HEAD.format(key='innergen-proposal-cover', name='이너젠 오리지널 제안 표지')
    s += f'<rect id="cover-bottom-band" x="0" y="628" width="1040" height="92" fill="{NAVY}"{LAY}/>\n'
    s += ''.join(f'<line id="cover-grid-v-{x}" x1="{x}" y1="629" x2="{x}" y2="720" stroke="{GRID}" stroke-width="0.6"{LAY}/>\n'
                 for x in range(24, 1040, 24))
    s += (f'<text id="cover-band-tags" x="520" y="682" text-anchor="middle" font-family="{FONT}" font-size="16" font-weight="700" fill="#FFFFFF"{LAY}>'
          'CO₂   │   Consulting   │   Client</text>\n')
    s += f'<image id="cover-logo" x="460" y="400" width="120" height="120" xlink:href="../images/innergen-logo-cover-blue.png" preserveAspectRatio="xMidYMid meet"{LAY}/>\n'
    s += ph('cover-date', 'body', '760 14 262 46', 1016, 34, 16, 700, '#000000', '{{DATE}}', idx=2, anchor='end')
    s += ph('cover-title', 'title', '100 140 840 150', 520, 210, 37.33, 700, '#000000', '{{TITLE}}', anchor='middle')
    s += ph('cover-subtitle', 'subtitle', '100 300 840 60', 520, 340, 21.33, 400, '#595959', '{{SUBTITLE}}', idx=1, anchor='middle')
    return s + '</svg>\n'


def ending():
    s = HEAD.format(key='innergen-proposal-ending', name='이너젠 오리지널 제안 마무리')
    s += f'<rect id="ending-bottom-band" x="0" y="660" width="1040" height="60" fill="{NAVY}"{LAY}/>\n'
    s += f'<rect id="ending-card" x="560" y="400" width="400" height="220" rx="14" fill="#FFFFFF" stroke="#BFBFBF" stroke-width="6"{LAY}/>\n'
    s += f'<image id="ending-logo" x="590" y="440" width="120" height="120" xlink:href="../images/innergen-logo-cover-blue.png" preserveAspectRatio="xMidYMid meet"{LAY}/>\n'
    s += (f'<text id="ending-contact-label" x="80" y="430" font-family="{FONT}" font-size="13.33" font-weight="700" fill="#595959"{LAY}>Contact Us</text>\n')
    s += ph('ending-message', 'title', '200 140 640 120', 520, 225, 69.33, 700, NAVY, 'Thank you!', anchor='middle')
    s += ph('ending-contact', 'body', '80 445 440 170', 80, 470, 14.67, 400, '#595959', '{{CONTACT}}', idx=1, vanchor='top')
    s += ph('ending-person', 'body', '730 450 210 130', 730, 500, 16, 700, '#000000', '{{PERSON}}', idx=2, vanchor='top')
    s += ph('ending-address', 'footer', '40 672 960 36', 520, 696, 13.33, 700, '#FFFFFF', '{{ADDRESS}}', idx=3, anchor='middle')
    return s + '</svg>\n'


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    files = {'01d_cover_proposal.svg': cover(),
             '02d_toc_proposal.svg': contents('innergen-proposal-toc', '이너젠 오리지널 제안 목차', None),
             '03d_chapter_proposal.svg': contents('innergen-proposal-chapter', '이너젠 오리지널 제안 장 구분', 1),
             '04d_content_proposal.svg': content(),
             '05d_ending_proposal.svg': ending()}
    for n, s in files.items():
        # paint order: master/layout shapes first, then placeholders
        lines = s.splitlines(keepends=True)
        body = lines[1:-1]
        fixed = [l for l in body if 'data-pptx-placeholder=' not in l] + [l for l in body if 'data-pptx-placeholder=' in l]
        (OUT / n).write_text(lines[0] + ''.join(fixed) + lines[-1], encoding='utf-8')
        print(n)
