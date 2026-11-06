# -*- coding: utf-8 -*-
"""Honest <lastmod> in sitemap.xml (6 Nov 2026). build_programmatic.py writes every URL with the data date, so all
~1,400 URLs claimed a change every day; Google then ignores lastmod (Search Console read sitemap.xml only every few
weeks). This last build step keeps a URL's previous lastmod unless the page itself changed: its title, meta description
or the main content (between the board header and the site footer), ignoring the daily "updated <date>" stamps.
Signatures are kept in _build/data/sitemap_lastmod.json. sitemap-jobs.xml already does this (build_jobpages.py)."""
import hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT, DATA, TODAY

SITE = 'https://berlinappjobs.com'
STORE = os.path.join(DATA, 'sitemap_lastmod.json')
SM = os.path.join(OUT, 'sitemap.xml')
_mon = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
y, m, d = (int(x) for x in TODAY.split('-'))
STAMPS = [TODAY, f'{d} {_mon[m - 1]} {y}', f'{d}.{m:02d}.{y}', f'{d:02d}.{m:02d}.{y}']   # data date as the pages print it

def sig(path):
    f = os.path.join(OUT, path, 'index.html') if path else os.path.join(OUT, 'index.html')
    try: h = open(f, encoding='utf-8').read()
    except OSError: return None
    parts = [re.search(r'<title>(.*?)</title>', h, re.S), re.search(r'<meta name="description" content="([^"]*)"', h)]
    i, j = h.find('<div class="wrap"'), h.find('<footer')
    body = h[i:j] if 0 <= i < j else h
    s = '\n'.join(p.group(1) if p else '' for p in parts) + body
    for st in STAMPS: s = s.replace(st, '')
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def main():
    try: xml = open(SM, encoding='utf-8').read()
    except OSError: print('no sitemap.xml'); return
    try: old = json.load(open(STORE, encoding='utf-8'))
    except (OSError, ValueError): old = {}
    new, changed = {}, 0
    def fix(m):
        nonlocal changed
        url = m.group(1); path = url.replace(SITE, '').strip('/')
        s = sig(path); prev = old.get(url)
        lm = prev[1] if prev and s and prev[0] == s and prev[1] <= TODAY else TODAY
        if lm == TODAY: changed += 1
        new[url] = [s, lm]
        return f'<loc>{url}</loc><lastmod>{lm}</lastmod>'
    xml = re.sub(r'<loc>([^<]+)</loc><lastmod>[^<]*</lastmod>', fix, xml)
    open(SM, 'w', encoding='utf-8').write(xml)
    json.dump(new, open(STORE, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    print(f'sitemap.xml lastmod: {changed} of {len(new)} URLs changed on {TODAY}')

if __name__ == '__main__': main()
