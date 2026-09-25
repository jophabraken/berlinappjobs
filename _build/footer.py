# -*- coding: utf-8 -*-
"""The site-wide footer, the same on every page (homepage, company, city, role x city, job, guide and 404 pages).

Built like the footers of large job boards (StepStone, Indeed, Glassdoor, Welcome to the Jungle): a brand block,
then link columns for the hub pages people search for: jobs by city, jobs by role, companies hiring, guides.
Every link is a plain crawlable <a href> to a page that exists and is indexable, with descriptive anchor text,
so link equity from every page flows to the hubs. It is kept to about 35 links (no keyword lists).

build_programmatic.py calls site_footer() once per language and exposes the result as FOOT (German) and FOOT_EN;
the other generators take those two strings from it. The rules for which pages exist are the same as in
build_programmatic.py: a city page needs 10+ jobs, a role x city page 5+, a company page needs parsed jobs."""
import collections, re, html as htmlmod

def _esc(s): return htmlmod.escape(str(s), quote=True)
LEGAL = re.compile(r'\s+(?:GmbH\s*&\s*Co\.?\s*KG(?:aA)?|GmbH|AG|SE|KG|KGaA|UG|mbH|e\.\s?V\.|Ltd\.?|Inc\.?|B\.V\.|S\.A\.)(?=\s|$|,).*$')
def short_name(n):
    n = n.split('|')[0].strip()
    return LEGAL.sub('', n).strip() or n
ROLE_ORDER = ['eng', 'product', 'design', 'data', 'marketing', 'sales', 'support', 'people', 'health']

ROLE_EN = {'eng': 'Developer', 'product': 'Product management', 'design': 'Design', 'data': 'Data & analytics',
           'marketing': 'Marketing', 'sales': 'Sales', 'support': 'Customer support', 'people': 'People & HR', 'health': 'Health'}

CSS = """<style>
footer.sfoot{border:0;padding:0;line-height:1.6}.sfoot a{margin:0;border:0}
.sfoot{background:#131310;color:#B8B5A3;margin-top:56px;font:14px/1.6 Archivo,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.sfoot a{color:#F4F1E0;text-decoration:none}.sfoot a:hover{color:#FFD400;text-decoration:underline}
.sf-in{max-width:1140px;margin:0 auto;padding:44px 20px 26px}
.sf-top{display:grid;grid-template-columns:minmax(220px,1.15fr) 3fr;gap:40px}
.sf-wm{display:inline-flex;font:900 13px/1 Archivo,sans-serif;letter-spacing:.04em;text-transform:uppercase}
.sf-wm span{padding:7px 9px;color:#131310}.sf-wm span:first-child{background:#FFD400}.sf-wm span+span{background:#fff;border-left:2.5px solid #131310}
.sfoot .sf-wm:hover{text-decoration:none}
.sf-brand p{margin:14px 0 0;max-width:34ch}.sf-brand .sf-upd{font-size:12.5px;color:#8A887B}
.sf-cta{display:inline-block;margin-top:16px;background:#FFD400;color:#131310!important;font-weight:800;font-size:13.5px;border-radius:6px;padding:9px 14px}
.sfoot .sf-cta:hover{text-decoration:none;background:#fff}
.sf-cols{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:28px}
.sf-h{font:800 12px/1.2 Archivo,sans-serif;letter-spacing:.07em;text-transform:uppercase;color:#FFD400;margin:0 0 12px}
.sf-cols ul{list-style:none;margin:0;padding:0}.sf-cols li{margin:0 0 7px;line-height:1.35}
.sf-cols .sf-all a{color:#B8B5A3;font-weight:700}
.sf-bot{display:flex;flex-wrap:wrap;gap:8px 22px;justify-content:space-between;border-top:1px solid #3A3A33;margin-top:36px;padding-top:18px;font-size:12.5px;color:#8A887B}
.sf-bot nav a{color:#B8B5A3;margin-left:16px}.sf-bot nav a:first-child{margin-left:0}
@media (max-width:860px){.sf-top{grid-template-columns:1fr;gap:30px}.sf-cols{grid-template-columns:repeat(2,minmax(0,1fr));gap:26px 20px}}
</style>"""

T = {
    'en': dict(tag="Live jobs at the companies behind Germany's top apps, pulled every week straight from their own hiring systems. Apply directly, no middleman.",
               upd="{n:,} open roles · updated {d}", cta="Browse all jobs &rarr;",
               h_city="Jobs by city", h_role="Jobs in Berlin", h_cos="Companies hiring", h_guides="Guides",
               city="App jobs in {x}", role="{x} jobs in Berlin", co="{x} jobs",
               all_city="All cities &amp; roles &rarr;", all_berlin="All jobs in Berlin &rarr;", cos="Companies", all_cos="All companies &rarr;", all_guides="All guides &rarr;",
               src="Jobs come from each company's own hiring system. Install figures: Google Play.",
               board="Job board", contact="Contact"),
    'de': dict(tag="Aktuelle Jobs bei den Unternehmen hinter Deutschlands Top-Apps, jede Woche direkt aus ihren Bewerbungssystemen. Direkt bewerben, ohne Vermittler.",
               upd="{n:,} offene Stellen · aktualisiert {d}", cta="Alle Jobs ansehen &rarr;",
               h_city="Jobs nach Stadt", h_role="Jobs in Berlin", h_cos="Top-Arbeitgeber", h_guides="Ratgeber",
               city="App-Jobs in {x}", role="{x}-Jobs in Berlin", co="Jobs bei {x}",
               all_city="Alle Städte &amp; Bereiche &rarr;", all_berlin="Alle Jobs in Berlin &rarr;", cos="Unternehmen", all_cos="Alle Unternehmen &rarr;", all_guides="Alle Ratgeber &rarr;",
               src="Die Stellen kommen aus den Bewerbungssystemen der Unternehmen. Downloadzahlen: Google Play.",
               board="Jobboard", contact="Kontakt"),
}

def site_footer(lang, COS, guides, slugify, city_slug, disc, checked=''):
    t = T['de' if lang == 'de' else 'en']
    # cities with a city page (10+ jobs, grouped by company city as in build_programmatic.py)
    city_jobs = collections.Counter()
    for c in COS:
        if c.get('city'): city_jobs[c['city']] += len(c.get('jobs') or [])
    cities = [x for x, n in city_jobs.most_common() if n >= 10][:8]
    # role x Berlin pages (5+ jobs)
    roles = collections.Counter(jb.get('d') for c in COS if (c.get('city') or '') == 'Berlin' for jb in c.get('jobs') or [])
    roles = [d for d in ROLE_ORDER if d in disc and roles.get(d, 0) >= 5][:7]   # fixed order: core app roles first
    # companies with an indexable page, in build_programmatic.py's order and with its slug de-duplication
    comps = [c for c in COS if c.get('tier', 3) <= 2 and c.get('n')]
    comps.sort(key=lambda c: (-(len(c.get('jobs', [])) or 0), -(c.get('v') or 0)))
    used, slugs = set(), {}
    for c in comps:
        s = slugify(c['n']); base, k = s, 2
        while s in used: s = f"{base}-{k}"; k += 1
        used.add(s); slugs[id(c)] = s
    top = [c for c in comps if c.get('jobs')][:8]
    # guides in the page's language first
    gl = [g for g in guides if g.get('lang') == lang] + [g for g in guides if g.get('lang') != lang]
    gl = gl[:6]
    n_jobs = sum(len(c.get('jobs') or []) for c in COS)

    def col(h, items, all_href, all_label):
        lis = ''.join(f'<li><a href="{href}">{label}</a></li>' for href, label in items)
        return f'<div><p class="sf-h">{h}</p><ul>{lis}<li class="sf-all"><a href="{all_href}">{all_label}</a></li></ul></div>'
    role_name = (lambda d: disc[d][1]) if lang == 'de' else (lambda d: ROLE_EN.get(d, disc[d][1]))
    cols = (col(t['h_city'], [(f'/jobs/{city_slug(x)}/', t['city'].format(x=_esc(x))) for x in cities], '/jobs/', t['all_city'])
            + col(t['h_role'], [(f'/jobs/{disc[d][0]}/{city_slug("Berlin")}/', t['role'].format(x=_esc(role_name(d)))) for d in roles], f'/jobs/{city_slug("Berlin")}/', t['all_berlin'])
            + col(t['h_cos'], [(f'/companies/{slugs[id(c)]}/', t['co'].format(x=_esc(short_name(c['n'])))) for c in top], '/companies/', t['all_cos'])
            + col(t['h_guides'], [(f'/guides/{_esc(g["slug"])}/', _esc(g['title'])) for g in gl], '/guides/', t['all_guides']))
    year = (checked or '2026')[-4:] if (checked or '')[-4:].isdigit() else '2026'
    return (CSS + '<footer class="sfoot"><div class="sf-in"><div class="sf-top">'
            '<div class="sf-brand"><a class="sf-wm" href="/" aria-label="Berlin App Jobs"><span>Berlin</span><span>App Jobs</span></a>'
            f'<p>{t["tag"]}</p><p class="sf-upd">{t["upd"].format(n=n_jobs, d=_esc(checked))}</p>'
            f'<a class="sf-cta" href="/">{t["cta"]}</a></div>'
            f'<nav class="sf-cols" aria-label="{_esc(t["h_city"])}, {_esc(t["h_cos"])}, {_esc(t["h_guides"])}">{cols}</nav></div>'
            f'<div class="sf-bot"><span>&copy; {year} Berlin App Jobs. {t["src"]}</span>'
            f'<nav aria-label="Berlin App Jobs"><a href="/">{t["board"]}</a><a href="/companies/">{t["cos"]}</a>'
            f'<a href="/guides/">{t["h_guides"]}</a><a href="mailto:jophabraken@gmail.com">{t["contact"]}</a></nav></div>'
            '</div></footer>')
