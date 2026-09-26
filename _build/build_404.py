# -*- coding: utf-8 -*-
"""The site's 404 page (/404.html). GitHub Pages serves it, with a 404 status, for any URL that doesn't exist.
Most visitors who land here followed a link to a job that has closed (closed jobs' pages are removed each
week), so it says that and sends them to current openings. noindex; all links are absolute because the page
is served at whatever URL was requested."""
import os, re, sys
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_programmatic.py'), encoding='utf-8').read()
exec(SRC[:SRC.index('def jsonld(objs):')])   # CSS, head(), FOOT_EN, esc(), city_slug(), COS, SITE, OUT, CITY_JOBS

n_jobs = sum(len(c.get('jobs') or []) for c in COS)
cities = [(c, city_slug(c), n) for c, n in CITY_JOBS.most_common(8)
          if n >= 10 and os.path.isdir(os.path.join(OUT, 'jobs', city_slug(c)))][:6]
city_links = ''.join(f'<a class="card" href="/jobs/{s}/"><div class="ct">App jobs in {esc(c)}</div><div class="cd">{n} open roles</div></a>'
                     for c, s, n in cities)
doc = head("Page not found | Berlin App Jobs", "This page doesn't exist (anymore). Browse current jobs at Germany's app companies.",
           SITE + "/404.html", extra='\n<meta name="robots" content="noindex">')
doc = doc.replace('<link rel="canonical" href="' + SITE + '/404.html">\n', '')   # a 404 has no canonical URL
doc += ('<h1 style="margin-top:34px">This page isn\'t here (anymore)</h1>'
        '<p class="sub">If you followed a link to a job, it has most likely been filled or closed: we remove closed roles every day. '
        f'There are <b>{n_jobs:,}</b> open roles on the board right now.</p>'
        '<p class="sub" lang="de">Diese Seite gibt es nicht (mehr). Falls du einem Link zu einer Stelle gefolgt bist, ist sie vermutlich '
        'besetzt oder geschlossen. Hier findest du alle aktuellen Stellen.</p>'
        '<a class="cta" href="/">See all open jobs &rarr;</a>'
        + (f'<h2>Jobs by city</h2><div class="grid">{city_links}</div>' if city_links else '')
        + '<h2>Or browse</h2><div class="grid">'
          '<a class="card" href="/companies/"><div class="ct">All app companies</div><div class="cd">Who is hiring, with their apps</div></a>'
          '<a class="card" href="/jobs/"><div class="ct">Jobs by role &amp; city</div><div class="cd">Engineering, product, design, data and more</div></a>'
          '<a class="card" href="/guides/"><div class="ct">Guides</div><div class="cd">Salaries, English-speaking jobs, how to get hired</div></a>'
          '</div>'
        + '</div>' + FOOT_EN + '</body></html>')
open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(doc)
print('404.html', len(doc.encode()), 'bytes;', len(cities), 'city links')
