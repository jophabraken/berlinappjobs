# -*- coding: utf-8 -*-
"""Builds the homepage (index.html) from templates/board.html.

The board is a JavaScript app. To make the homepage readable for search engines without
running JavaScript, this script:
  * keeps index.html small: the app code goes to /assets/app.js and the job data to
    /assets/data.js (both loaded right after the first paint, cache-busted by content hash);
  * pre-renders real numbers and the newest jobs as plain <a href="/job/..."> links inside
    #list, visible from the first paint, which the app replaces as soon as it has loaded;
  * writes company logos as separate image files (/assets/logos/) that load lazily;
  * uses the self-hosted font from fonts.py (no render-blocking Google Fonts request);
  * writes one clean <head>: title, one meta description, canonical, Open Graph and
    WebSite/Organization structured data.
"""
import json, os, re, sys, hashlib, html as htmlmod
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT, DATA, TPL
import header as site_hdr
import fonts   # self-hosted Archivo (replaces the Google Fonts stylesheet)

SITE = 'https://berlinappjobs.com'
esc = lambda s: htmlmod.escape(str(s), quote=True)
rd = lambda p: open(p, encoding='utf-8').read()

tpl = rd(os.path.join(TPL, 'board.html'))
board_js, guides_js, geo_js = (rd(os.path.join(DATA, f)) for f in ('board_data.js', 'guides_data.js', 'geo_data.js'))

# ---- split the template ----
i_font = tpl.index('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo')
i_top = tpl.index('<div id="top">')
i_data = tpl.index('<script>\n/*__DATA__*/\n</script>')
head_extra = tpl[i_font:i_top]                       # font link + board CSS
head_extra = fonts.HEAD + head_extra[head_extra.index('>') + 1:]   # Google Fonts link -> self-hosted font
body = tpl[i_top:i_data]                             # board markup
app = tpl[i_data:].split('<script>', 2)[2]           # the app code
app = app[:app.rindex('</script>')]

# ---- data for the pre-rendered part ----
i = board_js.find('const BOARD = '); j = board_js.find('const CHARTS', i)
B = json.loads(board_js[i + len('const BOARD = '):j].rstrip().rstrip(';').rstrip())
JOBPAGE = json.load(open(os.path.join(DATA, 'jobpages_map.json'), encoding='utf-8'))
cos = B['companies']
n_jobs = sum(len(c.get('jobs') or []) for c in cos)
n_cos = sum(1 for c in cos if (c.get('tier') or 9) <= 2)   # same rule as the app's 'companies hiring'
n_en = sum(1 for c in cos for jb in c.get('jobs') or [] if jb.get('lang') == 'en')   # same rule as the about page

# ---- keyword + live job count in the H1 (EN + DE), same styling ----
# The count in the H1 matches the title: Google keeps numbers in the search title far more often when the H1 has them too.
H1_EN = f'Berlin App Jobs: {n_jobs:,} jobs at apps <em>people actually use.</em>'
H1_DE = f'Berlin App Jobs: {n_jobs:,}'.replace(',', '.') + ' Jobs bei Apps, <em>die Menschen wirklich nutzen.</em>'
body = body.replace('<h1 id="introH1">Work on an app <em>people actually use.</em></h1>', f'<h1 id="introH1">{H1_EN}</h1>')
app = app.replace("introH1: 'Work on an app <em>people actually use.</em>'", f"introH1: '{H1_EN}'")
app = app.replace("introH1: 'Arbeite an einer App, <em>die Menschen wirklich nutzen.</em>'", f"introH1: '{H1_DE}'")
assert H1_EN in body and H1_EN in app and H1_DE in app, 'H1 replacement failed: template changed?'
rows = []
for c in cos:
    for jb in c.get('jobs') or []:
        u = JOBPAGE.get(jb['u'])
        if u: rows.append((jb.get('p') or '', c, jb, u))
rows.sort(key=lambda r: r[0], reverse=True)
seen, top = set(), []
for p, c, jb, u in rows:           # newest first, max 3 per company so one employer can't fill the list
    k = c['n']
    if sum(1 for x in top if x[1]['n'] == k) >= 3: continue
    top.append((p, c, jb, u))
    if len(top) >= 60: break
items = ''.join(
    f'<li><a href="{esc(u)}">{esc(jb["t"])}</a><span>{esc(c["n"])} · {esc(jb.get("loc") or c.get("city") or "")}</span></li>'
    for p, c, jb, u in top)
static_list = (f'<div class="seo-pre"><h2>Newest app jobs in Berlin and Germany</h2><ul>{items}</ul>'
               f'<p><a href="/jobs/">All {n_jobs:,} roles by city and discipline</a> · <a href="/en/companies/">All {n_cos} hiring companies</a></p></div>')

body = body.replace('<b id="st-jobs">0</b>', f'<b id="st-jobs">{n_jobs}</b>')   # no thousands separator: same as the app and header.py
body = body.replace('<b id="st-cos">0</b>', f'<b id="st-cos">{n_cos}</b>')
body = body.replace('<div id="count"></div>', f'<div id="count">{n_jobs} roles</div>')
# The pre-rendered list shows from the first paint; the app swaps in the full board once data.js has loaded.
# (It used to be hidden behind grey placeholder cards until then, which held the first paint back by ~3 s on phones.)
body = body.replace('<div id="list"></div>', f'<div id="list">{static_list}</div>')
assert 'seo-pre' in body

# ---- assets (content-hashed for caching) ----
os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
# Guides open as their own pages (/guides/<slug>/), so the app only needs title/desc/slug, not each guide's full text.
GUIDES = json.loads(guides_js[guides_js.find('=') + 1:].strip().rstrip(';'))
guides_slim = 'const GUIDES = ' + json.dumps([{k: g.get(k) for k in ('slug', 'lang', 'title', 'desc', 'pair')} for g in GUIDES], ensure_ascii=False) + ';\n'
jobpage_js = 'const JOBPAGE = ' + json.dumps({k: v.replace(SITE, '') for k, v in JOBPAGE.items()}, ensure_ascii=False, separators=(',', ':')) + ';\n'   # job URL -> /job/<slug>/, so cards open the full ad
def asset(name, text):
    h = hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]
    open(os.path.join(OUT, 'assets', name), 'w', encoding='utf-8').write(text)
    return f'/assets/{name}?v={h}'
# Logos (company icons and the chart app icons) arrive in board_data.js as base64 data URIs, ~2 MB in total.
# Each becomes a small image file in /assets/logos/, named by a hash of its bytes (an unchanged logo keeps its URL and
# stays cached across the weekly refresh), and BOARD/ICONS carry that URL. Cards load logos with loading="lazy",
# so a visitor downloads only the logos on screen. (They used to come as one 2 MB script, assets/icons.js.)
# With no ICONS_URL defined, the app knows the logos are already in place (iconsIn = true).
import base64
LOGOS = os.path.join(OUT, 'assets', 'logos'); os.makedirs(LOGOS, exist_ok=True)
EXT = {'image/webp': 'webp', 'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/svg+xml': 'svg'}
used = set()
def logo_url(v):
    m = re.match(r'data:([\w/+.-]+);base64,(.*)$', v or '', re.S)
    if not m or m.group(1) not in EXT: return v          # already a URL (or unknown): leave as is
    raw = base64.b64decode(m.group(2)); name = hashlib.sha1(raw).hexdigest()[:12] + '.' + EXT[m.group(1)]
    p = os.path.join(LOGOS, name); used.add(name)
    if not os.path.exists(p): open(p, 'wb').write(raw)
    return '/assets/logos/' + name
lines = board_js.rstrip().split('\n')
assert any(l.startswith('const BOARD = ') for l in lines) and any(l.startswith('const ICONS = ') for l in lines), 'board_data.js layout changed?'
for c in B['companies']:
    if c.get('icon'): c['icon'] = logo_url(c['icon'])
ch_icons = {k: logo_url(v) for k, v in next(json.loads(l[len('const ICONS = '):].rstrip().rstrip(';')) for l in lines if l.startswith('const ICONS = ')).items()}
lines = ['const BOARD = ' + json.dumps(B, ensure_ascii=False, separators=(',', ':')) + ';' if l.startswith('const BOARD = ')
         else 'const ICONS = ' + json.dumps(ch_icons, ensure_ascii=False, separators=(',', ':')) + ';' if l.startswith('const ICONS = ') else l for l in lines]
for f in os.listdir(LOGOS):                               # logos of companies no longer on the board
    if f not in used:
        try: os.remove(os.path.join(LOGOS, f))
        except OSError: pass
try: os.remove(os.path.join(OUT, 'assets', 'icons.js'))  # the old all-logos script
except OSError: pass
data_out = '\n'.join(lines) + '\n' + guides_slim + jobpage_js + geo_js.rstrip() + '\n'
data_url = asset('data.js', data_out)
app_url = asset('app.js', app.strip() + '\n')

# ---- footer: the site-wide footer from footer.py (crawlable links to the hub pages), English version ----
_PS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_programmatic.py')
_ns = {'__file__': _PS}
_src = open(_PS, encoding='utf-8').read(); exec(_src[:_src.index('def jsonld(objs):')], _ns)
foot = _ns['FOOT_EN']

# ---- head ----
# Title, from SEO split-test evidence (see the project doc claude/title-ctr-research.md): exact live count (beat "2,800+"),
# the English count (what expats search for, our differentiator), "Updated Daily" (+11% vs month/year on listing sites),
# 40-60 chars so Google doesn't cut or rewrite it, colon/commas instead of pipes or brackets. The English part only shows
# while it's true for at least ~45% of roles; otherwise the fallback keeps the "top apps" angle.
if n_jobs and n_en / n_jobs >= 0.45:
    TITLE = f"Berlin App Jobs: {n_jobs:,} Jobs, {n_en:,} in English, Updated Daily"
else:
    TITLE = f"Berlin App Jobs: {n_jobs:,} Jobs at Top Apps, Updated Daily"
# Description: the "top apps" angle with three well-known employers that are hiring right now (most installs, 3+ roles),
# kept under ~160 chars. No salary ranges (they lowered clicks in a job-site test).
def _short(n): return re.sub(r'\s+(SE|N\.V\.|GmbH|AG|Inc\.?|Ltd\.?|B\.V\.)$', '', n.strip())
_known = [_short(c['n']) for c in sorted((c for c in cos if (c.get('tier') or 9) <= 2 and len(c.get('jobs') or []) >= 3),
                                           key=lambda c: -(c.get('v') or 0))[:3]]
DESC = (f"Open roles at the companies behind Germany's top apps, like {_known[0]}, {_known[1]} and {_known[2]}. "
        "Engineering, product, design, data, marketing. Apply directly.") if len(_known) == 3 else \
       (f"{n_jobs:,} live roles at {n_cos} companies behind Germany's top apps: engineering, product, design, data and "
        "marketing in Berlin, Munich, Hamburg and remote. Apply directly.")
ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "@id": SITE + "/#website", "name": "Berlin App Jobs", "alternateName": "berlinappjobs.com", "url": SITE + "/", "inLanguage": ["en", "de"]},
    {"@type": "Organization", "@id": SITE + "/#org", "name": "Berlin App Jobs", "url": SITE + "/",
     "logo": {"@type": "ImageObject", "url": SITE + "/logo.png", "width": 512, "height": 512}}]}
FAV = tpl[tpl.index('<link rel="icon"'):tpl.index('>', tpl.index('<link rel="icon"')) + 1]
head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="color-scheme" content="only light">
<title>{esc(TITLE)}</title>
<meta name="description" content="{esc(DESC)}">
<link rel="canonical" href="{SITE}/">
<link rel="alternate" type="application/atom+xml" title="New app jobs" href="/feed.xml">
{FAV}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Berlin App Jobs">
<meta property="og:title" content="{esc(TITLE)}">
<meta property="og:description" content="{esc(DESC)}">
<meta property="og:url" content="{SITE}/">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{head_extra.rstrip()}
<style>
  .seo-pre h2 {{ font: 800 15px "Archivo", sans-serif; text-transform: uppercase; letter-spacing: .04em; margin: 6px 0 10px; }}
  .seo-pre ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }}
  .seo-pre li {{ background: var(--surface); border: 1.5px solid var(--line); border-radius: 8px; padding: 12px 14px; display: flex; flex-direction: column; gap: 2px; }}
  .seo-pre li a {{ color: var(--ink); font-weight: 700; text-decoration: none; }}
  .seo-pre li span {{ color: var(--muted); font-size: 12.5px; }}
  .seo-pre p {{ margin: 14px 0; font-size: 13.5px; }}
</style>
</head>
<body>
'''
# data.js and app.js load right after the first paint (in order, async=false) instead of as <script defer>, and without
# a <link rel=preload>: a preloaded or deferred 1.5 MB script ran before the page first painted, which held the first
# paint (and the Lighthouse FCP/LCP) back by ~2 s on phones. The pre-rendered list above is what visitors see meanwhile.
# (requestAnimationFrame doesn't run in a background tab, so a plain timer is the fallback.)
loader = ("<script>(function(){var d=0;function go(){if(d)return;d=1;[" + json.dumps(data_url) + "," + json.dumps(app_url) + "].forEach(function(u){"
          "var s=document.createElement('script');s.src=u;s.async=false;document.body.appendChild(s)})}"
          "requestAnimationFrame(function(){setTimeout(go,0)});setTimeout(go,2000)})()</script>")
doc = head + body.rstrip() + '\n' + loader + '\n' + site_hdr.HIDE_JS + '\n' + foot + '\n</body>\n</html>\n'
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(doc)
print(f'index.html {len(doc.encode()):,} bytes · data.js {len(data_out.encode()):,} · logos {len(used)} files · app.js {len(app.encode()):,} · pre-rendered jobs {len(top)} · {n_jobs} roles / {n_cos} companies')
