# -*- coding: utf-8 -*-
"""Remove company/city/role pages from earlier builds that the current build no longer generates
(e.g. a city that dropped below 10 jobs). Otherwise they linger with dead links and old counts.
The current set of pages is whatever build_programmatic.py just listed in sitemap.xml."""
import os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT
SITE = 'https://berlinappjobs.com'
listed = {u.replace(SITE, '').strip('/') for u in re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(OUT, 'sitemap.xml'), encoding='utf-8').read())}
removed = []
for top in ('jobs', 'companies'):
    for root, dirs, files in os.walk(os.path.join(OUT, top), topdown=False):
        rel = os.path.relpath(root, OUT).replace(os.sep, '/')
        if rel in listed or 'index.html' not in files: continue
        if 'Berlin App Jobs' not in open(os.path.join(root, 'index.html'), encoding='utf-8').read(5000): continue
        shutil.rmtree(root); removed.append(rel)
print(f'stale pages removed: {len(removed)}', removed[:10])
