# -*- coding: utf-8 -*-
"""/about/ (how the board works: sources, refresh, rules, corrections) and, when configured in site_config.py,
/impressum/ (§ 5 DDG). Trust pages: Google's guidance asks sites to show who is behind them, how content is made,
and how to reach them; the Impressum is a legal requirement in Germany."""
import os, sys
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_programmatic.py'), encoding='utf-8').read()
exec(SRC[:SRC.index('def jsonld(objs):')])   # CSS, head(), FOOT, FOOT_EN, esc(), COS, SITE, OUT, TODAY
import site_config

n_jobs = sum(len(c.get('jobs') or []) for c in COS)
n_cos = sum(1 for c in COS if c.get('jobs'))
n_en = sum(1 for c in COS for j in c.get('jobs') or [] if j.get('lang') == 'en')
n_sal = sum(1 for c in COS for j in c.get('jobs') or [] if j.get('sal'))
mail = esc(site_config.CONTACT_EMAIL)

url = SITE + '/about/'
doc = head("About Berlin App Jobs: where the jobs come from", "How Berlin App Jobs works: which companies are listed, where every job comes from, "
           "how often it is refreshed, and how employers can correct or remove a listing.", url, lang="en")
doc += f'''<nav class="crumb"><a href="/">Home</a> / About</nav>
<h1>About Berlin App Jobs</h1>
<p class="sub">Berlin App Jobs lists open roles at the companies behind Germany's most-used mobile apps: {n_jobs:,} roles at {n_cos} companies right now,
{n_en:,} of them advertised in English. It is an independent project from Berlin, not a recruitment agency. Sponsored placements, if any, are always labeled.</p>
<h2>Which companies are listed</h2>
<p>Companies come from the Google Play top charts (all categories, German storefront): every developer with a German business address,
plus the German offices of companies headquartered elsewhere. Install figures are Google Play lifetime brackets.</p>
<h2>Where every job comes from</h2>
<p>Each job is read directly from the company's own hiring system (for example Greenhouse, Lever, Ashby, Personio, SmartRecruiters,
Recruitee or softgarden) or its careers page. We don't write or rewrite job ads. The apply button always goes to the company's own
application page, and you apply directly with the company.</p>
<h2>How current it is</h2>
<p>All feeds are re-checked every day. Jobs that a company has closed are removed from the board and their pages are taken down.
The last update was on {esc(B.get("checked", TODAY))}.</p>
<h2>Salaries</h2>
<p>We only show a salary when the company publishes one in its ad ({n_sal} of the current roles). We never estimate salaries.</p>
<h2>Duplicates and filters</h2>
<p>Repeat postings with the same title and city appear once. Manual roles (driving, warehouse, cleaning) are left out, since the board is
about working on apps. Pages for a city or role only exist when there are enough live jobs to make them useful.</p>
<h2>For employers: corrections and removal</h2>
<p>If a listing is wrong, outdated, or you'd like your company removed, email <a href="mailto:{mail}">{mail}</a>. Changes go live with the next daily update.</p>
<h2>Contact</h2>
<p><a href="mailto:{mail}">{mail}</a>''' + (' &middot; <a href="/impressum/">Impressum</a>' if site_config.IMPRESSUM else '') + '''</p>
<h2 lang="de">Kurz auf Deutsch</h2>
<p lang="de">Berlin App Jobs zeigt offene Stellen bei den Unternehmen hinter Deutschlands meistgenutzten Apps, täglich direkt aus ihren
Bewerbungssystemen. Wir schreiben keine Anzeigen um, schätzen keine Gehälter und du bewirbst dich immer direkt beim Unternehmen.
Korrekturen oder Entfernung einer Anzeige: <a href="mailto:''' + mail + '">' + mail + '</a>.</p>'
doc += '</div>' + FOOT_EN + '</body></html>'
os.makedirs(os.path.join(OUT, 'about'), exist_ok=True)
open(os.path.join(OUT, 'about', 'index.html'), 'w', encoding='utf-8').write(doc)

imp = site_config.IMPRESSUM
if imp:
    u = SITE + '/impressum/'
    d = head("Impressum | Berlin App Jobs", "Impressum und Kontakt von Berlin App Jobs (Angaben gemäß § 5 DDG).", u,
             extra='\n<meta name="robots" content="noindex, follow">')
    d += ('<nav class="crumb"><a href="/">Home</a> / Impressum</nav><h1>Impressum</h1><h2>Angaben gemäß § 5 DDG</h2><p>'
          + '<br>'.join(esc(imp[k]) for k in ('name', 'street', 'city') if imp.get(k)) + '</p><h2>Kontakt</h2><p>'
          + (f'E-Mail: <a href="mailto:{esc(imp["email"])}">{esc(imp["email"])}</a>' if imp.get('email') else '')
          + (f'<br>Telefon: {esc(imp["phone"])}' if imp.get('phone') else '') + '</p>'
          + ('<h2>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV</h2><p>' + '<br>'.join(esc(imp[k]) for k in ('name', 'street', 'city') if imp.get(k)) + '</p>')
          + '</div>' + FOOT + '</body></html>')
    os.makedirs(os.path.join(OUT, 'impressum'), exist_ok=True)
    open(os.path.join(OUT, 'impressum', 'index.html'), 'w', encoding='utf-8').write(d)
print('about page written' + (' + impressum' if imp else ' (no impressum configured)'))
