# -*- coding: utf-8 -*-
"""Sanity checks for the generated site. Exit code 1 on any hard failure.
Usage: python3 _build/check_site.py [site_dir]   (default: repo root)"""
import os, re, sys, glob, xml.etree.ElementTree as ET
ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SITE = 'https://berlinappjobs.com'
fail, warn = [], []
pages = [p for p in glob.glob(os.path.join(ROOT, '**', 'index.html'), recursive=True) if '/_build/' not in p and '/.git/' not in p]
def url_of(p):
    rel = os.path.relpath(p, ROOT)[:-len('index.html')]
    return SITE + '/' + rel
def file_of(path):
    path = path.split('#')[0].split('?')[0]
    if not path.startswith('/'): return None
    f = os.path.join(ROOT, path.lstrip('/'))
    return f if os.path.exists(f) or os.path.exists(os.path.join(f, 'index.html')) else False
counts = {k: len(glob.glob(os.path.join(ROOT, k, '*', 'index.html'))) for k in ('job', 'companies', 'guides')}
titles = {}
try:   # pages build_programmatic.py deliberately marks noindex (company pages without parsed jobs)
    import json; NOINDEX_OK = set(json.load(open(os.path.join(ROOT, '_build', 'data', 'noindex_pages.json'))))
except (FileNotFoundError, ValueError): NOINDEX_OK = set()
broken = set()
for p in pages:
    h = open(p, encoding='utf-8').read()
    u = url_of(p)
    for tag, rx in (('title', r'<title>'), ('meta description', r'<meta name="description"'), ('canonical', r'<link rel="canonical"')):
        n = len(re.findall(rx, h))
        if n != 1: fail.append(f'{u}: {n}× {tag}')
    nh1 = len(re.findall(r'<h1\b', re.sub(r'<script\b.*?</script>', '', h, flags=re.S)))
    if nh1 != 1: warn.append(f'{u}: {nh1}× h1')
    t = re.search(r'<title>(.*?)</title>', h, re.S)
    if t: titles.setdefault(t.group(1).strip(), []).append(u)
    if re.search(r'<meta name="robots" content="[^"]*noindex', h) and u.replace(SITE + '/', '').strip('/') not in NOINDEX_OK:
        warn.append(f'{u}: noindex')
    body = re.sub(r'<script\b.*?</script>', '', h, flags=re.S)
    for href in re.findall(r'href="(/[^"#?]*)', body):
        if file_of(href) is False: broken.add((u, href))
for t, us in titles.items():
    if len(us) > 1: warn.append(f'duplicate title on {len(us)} pages: "{t[:70]}" e.g. {us[0]}')
for u, href in sorted(broken)[:50]: fail.append(f'broken internal link on {u}: {href}')
for sm in ('sitemap.xml', 'sitemap-jobs.xml'):
    f = os.path.join(ROOT, sm)
    try:
        locs = [e.text for e in ET.parse(f).getroot().iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    except Exception as e:
        fail.append(f'{sm}: {e}'); continue
    missing = [l for l in locs if file_of(l.replace(SITE, '') or '/') is False]
    if missing: fail.append(f'{sm}: {len(missing)} URLs without a page, e.g. {missing[0]}')
    print(f'{sm}: {len(locs)} URLs')
home = os.path.join(ROOT, 'index.html')
if os.path.getsize(home) > 250_000: fail.append(f'homepage HTML is {os.path.getsize(home):,} bytes (limit 250 KB)')
if not re.search(r'<a href="/job/', open(home, encoding='utf-8').read()): fail.append('homepage has no crawlable /job/ links')
print(f'pages: {len(pages)} · job pages {counts["job"]} · company pages {counts["companies"]} · guides {counts["guides"]}')
for w in warn[:40]: print('WARN', w)
if len(warn) > 40: print(f'WARN … {len(warn) - 40} more')
for f in fail: print('FAIL', f)
print('OK' if not fail else f'{len(fail)} failure(s)')
sys.exit(1 if fail else 0)
