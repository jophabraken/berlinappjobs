# -*- coding: utf-8 -*-
"""Favicon files at the site root, drawn from one vector shape: a yellow rounded square with a black "B"
(Archivo Black glyph outline). Standard library only, so CI needs nothing extra.
Writes favicon.svg, favicon.ico (16/32/48), favicon-96x96.png and apple-touch-icon.png (180, square corners;
iOS rounds them itself) and logo.png (512, the logo in the homepage's Organization structured data).
Files are only rewritten when their bytes change.
Then points every generated page at these files: the generators still emit an inline data: SVG icon, which
browsers show but Google Search ignores (it needs a crawlable favicon URL). In the same pass every page gets the
social preview image (og-image.png at the site root, 1200x630, committed as a file) for LinkedIn/Slack/WhatsApp.
Runs last in build_all.py."""
import os, re, struct, zlib, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT

ICONS = ('<link rel="icon" href="/favicon.ico" sizes="48x48">'
         '<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
         '<link rel="icon" href="/favicon-96x96.png" type="image/png" sizes="96x96">'
         '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
SOCIAL = ('<meta property="og:image" content="https://berlinappjobs.com/og-image.png">'
          '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
          '<meta property="og:image:alt" content="Berlin App Jobs: jobs at Germany\'s top app companies">'
          '<meta name="twitter:card" content="summary_large_image">'
          '<meta name="twitter:image" content="https://berlinappjobs.com/og-image.png">')
TWITTER_CARD = re.compile(r'<meta name="twitter:card" content="[^"]*">\n?')
INLINE = re.compile(r'<link rel="icon" href="data:image/svg\+xml,[^"]*">')

YELLOW, INK = (0xFF, 0xD4, 0x00), (0x13, 0x13, 0x10)
# "B" from Archivo Black, font units (y up), placed in a 100x100 box by translate/scale below.
B_PATH = ('M722 519Q722 392 607 359V355Q738 325 738 183Q738 129 711.5 87.5Q685 46 639.0 23.0Q593 0 538 0H74V688H532'
          'Q584 688 627.5 666.5Q671 645 696.5 606.0Q722 567 722 519ZM295 420H447Q469 420 483.5 435.5Q498 451 498 474V484'
          'Q498 506 483.0 521.5Q468 537 447 537H295ZM295 160H463Q485 160 499.5 175.5Q514 191 514 214V224Q514 247 499.5 262.5'
          'Q485 278 463 278H295Z')
TX, TY, S = 14.59, 80.00, 0.08721   # font units -> 0..100 box (glyph 60 high, centred)

def glyph_polys(steps=8):
    """Flatten the path (M/L/H/V/Q/Z) into closed polygons in the 0..100 box."""
    polys, cur, x, y = [], [], 0.0, 0.0
    for cmd, args in re.findall(r'([MLHVQZ])([^MLHVQZ]*)', B_PATH):
        a = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', args)]
        if cmd == 'M':
            if cur: polys.append(cur)
            x, y = a; cur = [(x, y)]
        elif cmd == 'L': x, y = a; cur.append((x, y))
        elif cmd == 'H': x = a[0]; cur.append((x, y))
        elif cmd == 'V': y = a[0]; cur.append((x, y))
        elif cmd == 'Q':
            cx, cy, ex, ey = a
            for i in range(1, steps + 1):
                t = i / steps
                cur.append(((1-t)**2*x + 2*(1-t)*t*cx + t*t*ex, (1-t)**2*y + 2*(1-t)*t*cy + t*t*ey))
            x, y = ex, ey
        elif cmd == 'Z':
            if cur: polys.append(cur); cur = []
    if cur: polys.append(cur)
    return [[(TX + px*S, TY - py*S) for px, py in p] for p in polys]

def rounded_rect(r, steps=10):
    import math
    pts = []
    for cx, cy, a0 in ((100-r, r, -90), (100-r, 100-r, 0), (r, 100-r, 90), (r, r, 180)):
        for i in range(steps + 1):
            a = math.radians(a0 + 90*i/steps); pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return [pts]

def coverage(polys, n, ss=4):
    """Even-odd scanline fill with ss x ss supersampling -> n x n coverage values 0..1."""
    N = n * ss; acc = [[0]*n for _ in range(n)]
    edges = [(p[i], p[(i+1) % len(p)]) for p in polys for i in range(len(p))]
    for row in range(N):
        yy = (row + 0.5) * 100 / N; xs = []
        for (x0, y0), (x1, y1) in edges:
            if (y0 <= yy < y1) or (y1 <= yy < y0):
                xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            c0 = max(0, int(xs[k] * N / 100 + 0.5)); c1 = min(N, int(xs[k+1] * N / 100 + 0.5))
            for col in range(c0, c1): acc[row // ss][col // ss] += 1
    return [[v / (ss*ss) for v in r] for r in acc]

def render(n, corner=True):
    bg = coverage(rounded_rect(18) if corner else [[(0, 0), (100, 0), (100, 100), (0, 100)]], n)
    fg = coverage(glyph_polys(), n)
    px = []
    for j in range(n):
        for i in range(n):
            f = fg[j][i]
            px.append(tuple(round(YELLOW[c]*(1-f) + INK[c]*f) for c in range(3)) + (round(255*max(bg[j][i], f)),))
    return px

def png(n, px):
    raw = b''.join(b'\0' + bytes(v for p in px[j*n:(j+1)*n] for v in p) for j in range(n))
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

def ico(pngs):
    """ICO container with PNG-compressed entries (supported by all current browsers and Google)."""
    head = struct.pack('<HHH', 0, 1, len(pngs)); off = 6 + 16*len(pngs); dirs = b''; data = b''
    for n, d in pngs:
        dirs += struct.pack('<BBBBHHII', n % 256, n % 256, 0, 0, 1, 32, len(d), off + len(data)); data += d
    return head + dirs + data

def svg():
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='18' fill='#FFD400'/>"
            f"<path transform='translate({TX} {TY}) scale({S} -{S})' fill='#131310' d='{B_PATH}'/></svg>\n").encode()

def write(name, data):
    p = os.path.join(OUT, name)
    if os.path.exists(p) and open(p, 'rb').read() == data: return False
    open(p, 'wb').write(data); return True

if __name__ == '__main__':
    files = {'favicon.svg': svg(),
             'favicon.ico': ico([(n, png(n, render(n))) for n in (16, 32, 48)]),
             'favicon-96x96.png': png(96, render(96)),
             'apple-touch-icon.png': png(180, render(180, corner=False)),
             'logo.png': png(512, render(512, corner=False))}
    changed = [k for k, v in files.items() if write(k, v)]
    pages = 0
    for root, dirs, names in os.walk(OUT):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_')) and d != 'node_modules']
        for nm in names:
            if not nm.endswith('.html'): continue
            p = os.path.join(root, nm); h = open(p, encoding='utf-8').read()
            if not INLINE.search(h): continue
            new = INLINE.sub(ICONS + SOCIAL, TWITTER_CARD.sub('', h), count=1)
            if new != h: open(p, 'w', encoding='utf-8').write(new); pages += 1
    print('pages pointed at favicon + social image files:', pages)
    print('icons:', ', '.join(f'{k} {len(v):,} B' for k, v in files.items()), '| changed:', changed or 'none')
