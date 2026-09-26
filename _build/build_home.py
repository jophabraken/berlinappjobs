# -*- coding: utf-8 -*-
"""Builds the homepage (index.html) from templates/board.html.

The board is a JavaScript app. To make the homepage readable for search engines without
running JavaScript, this script:
  * keeps index.html small: the app code goes to /assets/app.js and the job data to
    /assets/data.js (both loaded with `defer`, cache-busted by content hash);
  * pre-renders real numbers and the newest jobs as plain <a href="/job/..."> links inside
    #list, which the app replaces as soon as it has loaded;
  * writes one clean <head>: title, one meta description, canonical, Open Graph and
    WebSite/Organization structured data.
"""
import json, os, re, sys, hashlib, html as htmlmod
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT, DATA, TPL

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
body = tpl[i_top:i_data]                             # board markup
app = tpl[i_data:].split('<script>', 2)[2]           # the app code
app = app[:app.rindex('</script>')]

# ---- keyword in the H1 (EN + DE), same styling ----
H1_EN = 'Berlin App Jobs: work on an app <em>people actually use.</em>'
H1_DE = 'Berlin App Jobs: Arbeite an einer App, <em>die Menschen wirklich nutzen.</em>'
body = body.replace('<h1 id="introH1">Work on an app <em>people actually use.</em></h1>', f'<h1 id="introH1">{H1_EN}</h1>')
app = app.replace("introH1: 'Work on an app <em>people actually use.</em>'", f"introH1: '{H1_EN}'")
app = app.replace("introH1: 'Arbeite an einer App, <em>die Menschen wirklich nutzen.</em>'", f"introH1: '{H1_DE}'")
assert H1_EN in body and H1_EN in app and H1_DE in app, 'H1 replacement failed: template changed?'

# ---- data for the pre-rendered part ----
i = board_js.find('const BOARD = '); j = board_js.find('const CHARTS', i)
B = json.loads(board_js[i + len('const BOARD = '):j].rstrip().rstrip(';').rstrip())
JOBPAGE = json.load(open(os.path.join(DATA, 'jobpages_map.json'), encoding='utf-8'))
cos = B['companies']
n_jobs = sum(len(c.get('jobs') or []) for c in cos)
n_cos = sum(1 for c in cos if (c.get('tier') or 9) <= 2)   # same rule as the app's 'companies hiring'
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
               f'<p><a href="/jobs/">All {n_jobs:,} roles by city and discipline</a> · <a href="/companies/">All {n_cos} hiring companies</a></p></div>')

body = body.replace('<b id="st-jobs">0</b>', f'<b id="st-jobs">{n_jobs:,}</b>')
body = body.replace('<b id="st-cos">0</b>', f'<b id="st-cos">{n_cos}</b>')
body = body.replace('<div id="count"></div>', f'<div id="count">{n_jobs:,} roles</div>')
body = body.replace('<div id="list"></div>', f'<div id="list">{static_list}</div>')
assert 'seo-pre' in body

# ---- assets (content-hashed for caching) ----
os.makedirs(os.path.join(OUT, 'assets'), exist_ok=True)
# Guides open as their own pages (/guides/<slug>/), so the app only needs title/desc/slug, not each guide's full text.
GUIDES = json.loads(guides_js[guides_js.find('=') + 1:].strip().rstrip(';'))
guides_slim = 'const GUIDES = ' + json.dumps([{k: g.get(k) for k in ('slug', 'lang', 'title', 'desc', 'pair')} for g in GUIDES], ensure_ascii=False) + ';\n'
jobpage_js = 'const JOBPAGE = ' + json.dumps({k: v.replace(SITE, '') for k, v in JOBPAGE.items()}, ensure_ascii=False, separators=(',', ':')) + ';\n'   # job URL -> /job/<slug>/, so cards open the full ad
data_out = board_js.rstrip() + '\n' + guides_slim + jobpage_js + geo_js.rstrip() + '\n'
def asset(name, text):
    h = hashlib.sha1(text.encode('utf-8')).hexdigest()[:10]
    open(os.path.join(OUT, 'assets', name), 'w', encoding='utf-8').write(text)
    return f'/assets/{name}?v={h}'
data_url = asset('data.js', data_out)
app_url = asset('app.js', app.strip() + '\n')

# ---- footer: the site-wide footer from footer.py (crawlable links to the hub pages), English version ----
_PS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_programmatic.py')
_ns = {'__file__': _PS}
_src = open(_PS, encoding='utf-8').read(); exec(_src[:_src.index('def jsonld(objs):')], _ns)
foot = _ns['FOOT_EN']

# ---- head ----
TITLE = "Berlin App Jobs: jobs at the companies behind Germany's top apps"
DESC = (f"{n_jobs:,} live roles at {n_cos} companies behind Germany's top mobile apps: engineering, product, design, data and "
        "marketing jobs in Berlin, Munich, Hamburg and remote. Direct apply, salaries where published.")
ld = {"@context": "https://schema.org", "@graph": [
    {"@type": "WebSite", "@id": SITE + "/#website", "name": "Berlin App Jobs", "alternateName": "berlinappjobs.com", "url": SITE + "/", "inLanguage": ["en", "de"]},
    {"@type": "Organization", "@id": SITE + "/#org", "name": "Berlin App Jobs", "url": SITE + "/",
     "logo": {"@type": "ImageObject", "url": SITE + "/logo.png", "width": 512, "height": 512}}]}
FAV = tpl[tpl.index('<link rel="icon"'):tpl.index('>', tpl.index('<link rel="icon"')) + 1]
head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
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
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" href="{data_url}" as="script">
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
doc = head + body.rstrip() + f'\n<script src="{data_url}" defer></script>\n<script src="{app_url}" defer></script>\n' + foot + '\n</body>\n</html>\n'
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(doc)
print(f'index.html {len(doc.encode()):,} bytes · data.js {len(data_out.encode()):,} · app.js {len(app.encode()):,} · pre-rendered jobs {len(top)} · {n_jobs} roles / {n_cos} companies')
