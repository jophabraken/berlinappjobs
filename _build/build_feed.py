# -*- coding: utf-8 -*-
"""/feed.xml: Atom feed of the newest jobs (by date posted), linking to our job pages where they exist.
Feeds a job-alert newsletter (RSS-to-email, e.g. Buttondown) and feed readers; linked from every page's <head>."""
import os, sys, json, datetime
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_programmatic.py'), encoding='utf-8').read()
exec(SRC[:SRC.index('def jsonld(objs):')])   # esc(), COS, SITE, OUT, DATA, TODAY
try: JOBPAGE = json.load(open(os.path.join(DATA, 'jobpages_map.json')))
except Exception: JOBPAGE = {}
jobs = []
for c in COS:
    for jb in c.get('jobs') or []:
        if jb.get('p') and jb.get('u'): jobs.append((jb['p'], c, jb))
jobs.sort(key=lambda x: x[0], reverse=True)
items = []
for p, c, jb in jobs[:100]:
    link = SITE + JOBPAGE[jb['u']] if jb['u'] in JOBPAGE else jb['u']
    co = c['n'].split('|')[0].strip(); loc = jb.get('loc') or c.get('city') or ''
    extra = ' · '.join(x for x in (loc, 'English' if jb.get('lang') == 'en' else 'Deutsch', (jb.get('sal') or '').split('•')[0].strip()) if x)
    items.append(f'<entry><title>{esc(jb["t"])} at {esc(co)}</title><link href="{esc(link)}"/><id>{esc(link)}</id>'
                 f'<updated>{p[:10]}T00:00:00Z</updated><summary>{esc(extra)}</summary></entry>')
feed = ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">'
        '<title>Berlin App Jobs: new jobs at Germany\'s top app companies</title>'
        f'<link href="{SITE}/"/><link rel="self" href="{SITE}/feed.xml"/><id>{SITE}/feed.xml</id>'
        f'<updated>{TODAY}T00:00:00Z</updated>' + ''.join(items) + '</feed>\n')
open(os.path.join(OUT, 'feed.xml'), 'w', encoding='utf-8').write(feed)
print('feed.xml', len(items), 'jobs')
