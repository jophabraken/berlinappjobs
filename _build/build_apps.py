# -*- coding: utf-8 -*-
""""Who makes this app?" pages: /apps/<slug>/ (German) and /en/apps/<slug>/ (English), the /apps/ lookup hub and the
game studios hub (/apps/spiele/, /en/apps/games/).

Called from build_programmatic.py (build(globals()) right before the sitemap), so it reuses that file's head(), footer,
company slugs and job-page map, and its URLs land in sitemap.xml. Which apps get a page: apps_data.py.
Facts come only from our data (Google Play developer, city, installs, live jobs) and from data/apps_curated.json
(parent companies, each with a source). No ratings markup: Play ratings aren't reviews collected on this site.
Job links carry data-umami-event so Umami counts app page -> job clicks."""
import collections, html as htmlmod, json, os, re
from urllib.parse import quote
import apps_data

EXTRA_CSS = """<style>
.lead{font-size:17px;line-height:1.55;max-width:68ch;margin:4px 0 10px}
.facts{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px;background:var(--surface);border:1.5px solid var(--line);border-radius:9px;padding:14px 16px;margin:8px 0 6px;font-size:14.5px}
.facts dt{color:var(--faint);font-weight:700}.facts dd{margin:0}
@media (max-width:560px){.facts{grid-template-columns:1fr;gap:2px}.facts dd{margin-bottom:8px}}
.apphead{display:flex;gap:14px;align-items:center}.apphead img{width:64px;height:64px;border-radius:14px;flex:none;border:1.5px solid var(--line)}
.store{display:inline-block;border:1.5px solid var(--line);border-radius:6px;padding:4px 10px;font-size:12.5px;font-weight:700;text-decoration:none;margin:0 6px 4px 0;background:var(--surface)}
.faq h3{font-size:16px;margin:18px 0 4px}.faq p{margin:0 0 6px;max-width:68ch}
.search{width:100%;font:inherit;font-size:17px;padding:14px 16px;border:2px solid var(--line);border-radius:9px;background:var(--surface);margin:10px 0 4px}
.search:focus{outline:3px solid var(--accent);outline-offset:1px}
.atab{width:100%;border-collapse:collapse;font-size:14px;margin-top:10px}
.atab th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--faint);border-bottom:2px solid var(--line);padding:6px 8px}
.atab td{border-bottom:1px solid #DEDBCB;padding:8px;vertical-align:top}.atab td.n{color:var(--faint);width:2.5em}
.atab a{font-weight:700}.atab .co{color:var(--muted)}.atab .jb{white-space:nowrap;font-weight:700;font-size:12.5px}
@media (max-width:640px){.atab .ci,.atab th.ci{display:none}}
.empty{display:none;color:var(--muted);padding:12px 0}
</style>"""

SEARCH_JS = """<script>(function(){var q=document.getElementById('appq'),rows=document.querySelectorAll('#apptab tbody tr'),e=document.getElementById('appempty');
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')}
var keys=[];for(var i=0;i<rows.length;i++)keys.push(norm(rows[i].getAttribute('data-s')||''));
function run(){var v=norm(q.value.trim()),n=0;for(var i=0;i<rows.length;i++){var on=!v||keys[i].indexOf(v)>-1;rows[i].style.display=on?'':'none';if(on)n++}e.style.display=n?'none':'block'}
q.addEventListener('input',run);var p=new URLSearchParams(location.search).get('q');if(p){q.value=p;run()}})();</script>"""


def build(G):
    SITE, OUT, DATA, TODAY = G['SITE'], G['OUT'], G['DATA'], G['TODAY']
    esc, head, jsonld, breadcrumb = G['esc'], G['head'], G['jsonld'], G['breadcrumb']
    FOOT, FOOT_EN, JOBPAGE, DISC, ROLE_EN = G['FOOT'], G['FOOT_EN'], G['JOBPAGE'], G['DISC'], G['ROLE_EN']
    short_name, city_slug, CITY_JOBS, COS = G['short_name'], G['city_slug'], G['CITY_JOBS'], G['COS']
    cur = apps_data.curated(DATA)
    OWN, GAME = cur.get('owners') or {}, set(cur.get('game_companies') or [])
    pages = apps_data.app_pages(COS, DATA)
    SLUG = {a['id']: s for c, a, s in pages}
    bs = open(os.path.join(DATA, 'board_data.js'), encoding='utf-8').read()
    def _const(name):
        i = bs.find(f'const {name} = ')
        if i < 0: return {}
        j = bs.find('\nconst ', i + 5); j = len(bs) if j < 0 else j
        return json.loads(bs[i + len(f'const {name} = '):j].strip().rstrip(';'))
    ICONS, IOS = _const('ICONS'), _const('IOS')
    CO_PAGE = {id(c): c['_slug'] for c in G['comps'] if c.get('_slug')}       # tier <= 2 companies have a page
    hiring = [c for c in G['comps'] if c.get('jobs')]                        # already sorted: most jobs first
    def co_href(c, lang):
        s = CO_PAGE.get(id(c)); return f"{'/en' if lang == 'en' else ''}/companies/{s}/" if s else None
    def app_href(a, lang):
        s = SLUG.get(a.get('id')); return f"{'/en' if lang == 'en' else ''}/apps/{s}/" if s else None
    def is_game(c): return c.get('n') in GAME
    def name_of(a): return apps_data.short_title(a.get('t'))
    def inst(a): return a.get('i') or ''
    def n_txt(n, one, many): return f"{n} {one if n == 1 else many}"
    def home(pre): return '/'   # the homepage is bilingual; there is no /en/ page

    out_urls = []
    def write(rel, doc):
        d = os.path.join(OUT, *rel.strip('/').split('/')); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(doc)

    def fit(*opts):
        for x in opts:
            if len(x) <= 62: return x
        return opts[-1]

    def job_rows(jobs, de, ev, show_co=False, city=''):
        T = lambda x, y: x if de else y
        h = ''
        for jb in jobs:
            jpu = JOBPAGE.get(jb.get('u', ''))
            dd = (DISC.get(jb.get('d', ''), ('', ''))[1]) if de else ROLE_EN.get(jb.get('d', ''), DISC.get(jb.get('d', ''), ('', ''))[1])
            sub = (esc(short_name(jb['_c']['n'])) + ' &middot; ' if show_co else '') + esc(jb.get('loc') or (jb['_c'].get('city') if show_co else city) or '') + (' &middot; ' + esc(dd) if dd and not show_co else '')
            h += ((f'<a class="row" href="{jpu}" data-umami-event="{ev}">' if jpu else f'<a class="row" href="{esc(jb.get("u", "#"))}" target="_blank" rel="noopener nofollow" data-umami-event="{ev}">')
                  + f'<div class="m"><div class="t">{esc(jb["t"])}</div><div class="d">{sub}</div></div>'
                  + ('<span class="apply">Details</span></a>' if jpu else f'<span class="apply">{T("Bewerben", "Apply")} &#8599;</span></a>'))
        return h

    def co_cards(cs, de, lang, ev):
        return '<div class="grid">' + ''.join(
            f'<a class="card" href="{co_href(o, lang)}" data-umami-event="{ev}"><div class="ct">{esc(short_name(o["n"]))}</div><div class="cd">'
            + (esc(o.get('city')) + ' &middot; ' if o.get('city') else '')
            + (n_txt(len(o['jobs']), 'offene Stelle', 'offene Stellen') if de else n_txt(len(o['jobs']), 'open role', 'open roles'))
            + (' &middot; ' + esc(name_of(o['apps'][0])) if o.get('apps') else '') + '</div></a>' for o in cs if co_href(o, lang)) + '</div>'

    # ---------- one app page ----------
    def app_page(c, a, slug, lang):
        de = lang == 'de'; T = lambda x, y: x if de else y
        pre = '' if de else '/en'
        name, con, legal = name_of(a), short_name(c['n']), c.get('legal') or c['n']
        city = c.get('city') or ''
        jobs = c.get('jobs') or []; n = len(jobs)
        n_en = sum(1 for j in jobs if j.get('lang') == 'en')
        own = OWN.get(c['n']) or {}
        parent, note = own.get('parent'), own.get('de' if de else 'en')
        game = is_game(c)
        url = f"{SITE}{pre}/apps/{slug}/"
        alt = {'de': f"{SITE}/apps/{slug}/", 'en': f"{SITE}/en/apps/{slug}/"}
        jt = f" ({n} Jobs)" if n else ''
        title = fit(T(f"Wer steckt hinter {name}? {con}{jt}", f"Who Makes {name}? {con}{jt}"),
                    T(f"Wer steckt hinter {name}? {con}", f"Who Makes {name}? {con}"),
                    T(f"Wer steckt hinter {name}?", f"Who Makes {name}?"))
        if len(title) <= 45: title += " | Berlin App Jobs"
        if de:
            desc = (f"{name} kommt von {con}" + (f" ({city})" if city else '') + (f", Teil von {parent}" if parent else '') + ". "
                    + (f"{con} hat gerade {n_txt(n, 'offene Stelle', 'offene Stellen')}, direkt aus dem Bewerbungssystem." if n
                       else "Dazu: weitere Apps der Firma und App-Firmen, die gerade einstellen."))
        else:
            desc = (f"{name} is made by {con}" + (f" ({city})" if city else '') + (f", part of {parent}" if parent else '') + ". "
                    + (f"{con} has {n_txt(n, 'open role', 'open roles')} right now, straight from their hiring system." if n
                       else "Plus: more apps by the company and app companies that are hiring now."))
        if n:
            jobs_sent = T(f"{esc(con)} hat gerade <b>{n_txt(n, 'offene Stelle', 'offene Stellen')}</b>", f"{esc(con)} has <b>{n_txt(n, 'open role', 'open roles')}</b> right now")
            jobs_sent += (T(", alle auf Englisch.", ", all in English.") if n_en == n else
                          T(f", {n_en} davon auf Englisch.", f", {n_en} of them in English.") if n_en else '.')
        else:
            jobs_sent = T(f"{esc(con)} hat gerade keine offenen Stellen bei uns, ähnliche Firmen aber schon (siehe unten).",
                          f"{esc(con)} has no open roles with us right now, but similar companies do (see below).")
        lead = (T(f"<b>{esc(name)}</b> kommt von <b>{esc(con)}</b>", f"<b>{esc(name)}</b> is made by <b>{esc(con)}</b>")
                + (f" ({esc(city)})" if city else '') + '. ' + (esc(note) + ' ' if note else '') + jobs_sent)
        icon = ICONS.get(a.get('id')) or (c.get('icon') if (c.get('icon') or '').startswith('data:image') else '')
        ios = IOS.get(a.get('id')) or {}
        stores = (f'<a class="store" href="https://play.google.com/store/apps/details?id={quote(a["id"])}" target="_blank" rel="noopener nofollow">Google Play &#8599;</a>'
                  + (f'<a class="store" href="{esc(ios["url"])}" target="_blank" rel="noopener nofollow">App Store &#8599;</a>' if ios.get('url') else ''))
        ch = co_href(c, lang)
        facts = [('App', esc(htmlmod.unescape(a['t']))),
                 (T('Entwickler (Google Play)', 'Developer (Google Play)'), (f'<a href="{ch}">{esc(c["n"])}</a>' if ch else esc(c['n'])) + (f' &middot; {esc(legal)}' if legal != c['n'] else ''))]
        if city: facts.append((T('Standort', 'Location'), esc(city)))
        if inst(a): facts.append((T('Downloads', 'Installs'), esc(inst(a)) + T(' bei Google Play', ' on Google Play')))
        if parent:
            facts.append((T('Gehört zu', 'Part of'), esc(parent) + (T(f' (seit {own["since"]})', f' (since {own["since"]})') if own.get('since') else '')
                          + f' &middot; <a href="{esc(own["source"])}" target="_blank" rel="noopener nofollow">{T("Quelle", "Source")}</a>'))
        facts.append((T('Kategorie', 'Category'), T('Spiel', 'Game') if game else 'App'))
        facts.append(('Stores', stores))
        facts.append((T('Offene Stellen', 'Open roles'), (f'<a href="{ch}" data-umami-event="app-company">{n}</a>' if ch and n else str(n)) + T(f' (Stand {TODAY})', f' (as of {TODAY})')))
        body = f'<nav class="crumb"><a href="{home(pre)}">Home</a> / <a href="{pre}/apps/">Apps</a> / {esc(name)}</nav>'
        body += '<div class="apphead">' + (f'<img src="{esc(icon)}" alt="" width="64" height="64">' if icon else '') + f'<h1>{T("Wer steckt hinter", "Who makes")} {esc(name)}?</h1></div>'
        body += f'<p class="lead">{lead}</p>'
        body += f'<h2>{T("Steckbrief", "Fact sheet")}</h2><dl class="facts">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts) + '</dl>'
        if n:
            disc = collections.Counter(j.get('d') for j in jobs)
            dn = (lambda d: DISC[d][1]) if de else (lambda d: ROLE_EN.get(d, DISC[d][1]))
            top = [f"{dn(d)} ({k})" for d, k in disc.most_common() if d in DISC][:3]
            body += f'<h2>{T("Jobs bei", "Jobs at")} {esc(con)} ({n})</h2>'
            body += f'<p class="secnote">{(T("Vor allem ", "Mostly ") + esc(", ".join(top)) + ". ") if top else ""}{T("Live aus dem Bewerbungssystem, mit Direktbewerbung.", "Live from their hiring system, apply directly.")}</p>'
            body += job_rows(jobs[:12], de, 'app-job', city=city)
            if ch: body += f'<a class="cta" href="{ch}" data-umami-event="app-company">{T(f"Alle {n} Stellen bei {esc(con)}", f"All {n} roles at {esc(con)}")} &rarr;</a>'
            else: body += f'<a class="cta" href="/?q={esc(quote(c["n"]))}" data-umami-event="app-company">{T("Im Jobboard ansehen", "See them on the job board")} &rarr;</a>'
        else:
            if game:
                peers, label = [o for o in hiring if is_game(o)][:8], T('Game-Studios, die gerade einstellen', 'Game studios hiring now')
            else:
                peers = [o for o in hiring if city and o.get('city') == city][:8]
                label = T(f'App-Firmen in {esc(city)}, die gerade einstellen', f'App companies in {esc(city)} hiring now')
                if len(peers) < 3: peers, label = hiring[:8], T('App-Firmen, die gerade einstellen', 'App companies hiring now')
            body += f'<h2>{label}</h2><p class="secnote">{T(f"{esc(con)} hat gerade keine offenen Stellen bei uns. Diese Firmen schon:", f"{esc(con)} has no open roles with us right now. These companies do:")}</p>'
            body += co_cards(peers, de, lang, 'app-peer')
            if game: body += f'<a class="cta" href="{pre}/apps/{T("spiele", "games")}/">{T("Alle Game-Studios in Deutschland", "All game studios in Germany")} &rarr;</a>'
            elif city and CITY_JOBS.get(city, 0) >= 10: body += f'<a class="cta" href="{pre}/jobs/{city_slug(city)}/">{T(f"Alle App-Jobs in {esc(city)}", f"All app jobs in {esc(city)}")} &rarr;</a>'
        others = [o for o in (c.get('apps') or []) if o.get('id') != a.get('id') and o.get('t')][:8]
        if others:
            body += f'<h2>{T("Weitere Apps von", "More apps by")} {esc(con)}</h2><div class="applist">'
            for o in others:
                h = app_href(o, lang); lab = esc(name_of(o)) + (f' &middot; {esc(inst(o))}' if inst(o) else '')
                body += f'<a href="{h}">{lab}</a>' if h else f'<a href="https://play.google.com/store/apps/details?id={quote(o["id"])}" target="_blank" rel="noopener nofollow">{lab}</a>'
            body += '</div>'
        if game:
            rel, rh = [r for r in pages if is_game(r[0]) and r[0] is not c][:8], T('Mehr Spiele aus Deutschland', 'More games made in Germany')
        else:
            rel = [r for r in pages if not is_game(r[0]) and r[0] is not c and city and r[0].get('city') == city][:8]
            rh = T(f'Mehr Apps aus {esc(city)}', f'More apps from {esc(city)}')
            if len(rel) < 4: rel, rh = [r for r in pages if not is_game(r[0]) and r[0] is not c][:8], T('Mehr Apps aus Deutschland', 'More apps made in Germany')
        if rel:
            body += f'<h2>{rh}</h2><div class="applist">' + ''.join(f'<a href="{pre}/apps/{s2}/">{T("Wer steckt hinter", "Who makes")} {esc(name_of(a2))}?</a>' for c2, a2, s2 in rel) + '</div>'
        faq = [(T(f"Wer hat {name} entwickelt?", f"Who made {name}?"),
                T(f"{name} wird von {legal} entwickelt und bei Google Play veröffentlicht" + (f". Standort laut Google Play: {city}" if city else '') + ".",
                  f"{name} is developed by {legal} and published on Google Play" + (f". Location on Google Play: {city}" if city else '') + "."))]
        if parent:
            faq.append((T(f"Zu welchem Konzern gehört {con}?", f"Who owns {con}?"), T(f"{con} gehört zu {parent}.", f"{con} is part of {parent}.") + (' ' + note if note else '')))
        faq.append((T(f"Stellt {con} gerade ein?", f"Is {con} hiring?"),
                    (T(f"Ja, {con} hat aktuell {n_txt(n, 'offene Stelle', 'offene Stellen')} (Stand {TODAY}). Die Stellen kommen direkt aus dem Bewerbungssystem der Firma.",
                       f"Yes, {con} has {n_txt(n, 'open role', 'open roles')} right now (as of {TODAY}), straight from the company's hiring system.")
                     if n else T(f"Gerade nicht: Wir finden aktuell keine offenen Stellen bei {con}. Auf dieser Seite stehen ähnliche Firmen, die einstellen.",
                                 f"Not right now: we don't find open roles at {con} at the moment. This page lists similar companies that are hiring."))))
        body += '<section class="faq"><h2>FAQ</h2>' + ''.join(f'<h3>{esc(q)}</h3><p>{esc(x)}</p>' for q, x in faq) + '</section>'
        org = {"@context": "https://schema.org", "@type": "Organization", "name": legal, "alternateName": con,
               **({"url": SITE + ch} if ch else {}),
               **({"address": {"@type": "PostalAddress", "addressLocality": city, "addressCountry": "DE"}} if city else {}),
               **({"parentOrganization": {"@type": "Organization", "name": parent}} if parent else {})}
        ld = [breadcrumb([("Home", SITE + home(pre)), ("Apps", f"{SITE}{pre}/apps/"), (name, url)]), org,
              {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                  {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
        doc = head(title, desc, url, extra='\n' + EXTRA_CSS + '\n' + jsonld(ld), lang=lang, alt=alt, active='companies')
        doc += body + '</div>' + (FOOT if de else FOOT_EN) + '</body></html>'
        write(f"{pre}/apps/{slug}/", doc); out_urls.append(url)

    for c, a, s in pages:
        app_page(c, a, s, 'de'); app_page(c, a, s, 'en')

    # ---------- hubs: the lookup tool (/apps/) and game studios (/apps/spiele/) ----------
    allapps = sorted(((c, a) for c in COS for a in (c.get('apps') or []) if a.get('t') and apps_data.installs(a) >= 100_000),
                     key=lambda r: (-apps_data.installs(r[1]), name_of(r[1]).lower()))
    n_cos = len({id(c) for c, a in allapps})
    def table(items, lang):
        de = lang == 'de'
        rows = ''
        for k, (c, a) in enumerate(items):
            h = app_href(a, lang) or co_href(c, lang)
            nm = esc(name_of(a)); n = len(c.get('jobs') or [])
            cell = f'<a href="{h}">{nm}</a>' if h else nm
            s = f"{name_of(a)} {htmlmod.unescape(a['t'])} {c['n']}"
            rows += (f'<tr data-s="{esc(s)}"><td class="n">{k + 1}</td><td>{cell}<div class="co">{esc(short_name(c["n"]))}</div></td>'
                     f'<td class="ci">{esc(c.get("city") or "")}</td><td>{esc(inst(a))}</td><td>{(f"<span class=jb>{n} Jobs</span>" if n else "")}</td></tr>')
        return (f'<table class="atab" id="apptab"><thead><tr><th>#</th><th>{"App &amp; Firma" if de else "App &amp; company"}</th>'
                f'<th class="ci">{"Standort" if de else "Location"}</th><th>{"Downloads" if de else "Installs"}</th><th>Jobs</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>')
    def num(x, de): return f"{x:,}".replace(',', '.') if de else f"{x:,}"
    games = [(c, a) for c, a in allapps if is_game(c)]
    studios = [o for o in hiring if is_game(o)]
    gjobs = [dict(j, _c=o) for o in studios for j in o['jobs']]
    for lang in ('de', 'en'):
        de = lang == 'de'; T = lambda x, y: x if de else y; pre = '' if de else '/en'
        # /apps/
        url = f"{SITE}{pre}/apps/"; N = num(len(allapps), de)
        title = T(f"Wer steckt hinter der App? {N} Apps & ihre Firmen", f"Who Makes This App? {N} Apps & Their Companies")
        desc = T(f"Finde heraus, welche Firma hinter einer App steckt und ob sie gerade einstellt. {N} Apps von {n_cos} Firmen in Deutschland, nach Downloads sortiert.",
                 f"Find out which company makes an app and whether it is hiring. {N} apps from {n_cos} companies in Germany, sorted by installs.")
        body = f'<nav class="crumb"><a href="{home(pre)}">Home</a> / Apps</nav>'
        body += f'<h1>{T("Wer steckt hinter der App?", "Who makes this app?")}</h1>'
        body += ('<p class="sub">' + T(f"Tippe den Namen einer App ein und sieh, welche Firma dahinter steckt, wo sie sitzt und ob sie gerade einstellt. {N} Apps von {n_cos} Firmen in Deutschland, sortiert nach Downloads bei Google Play.",
                                      f"Type the name of an app to see which company makes it, where it is based and whether it is hiring. {N} apps from {n_cos} companies in Germany, sorted by installs on Google Play.") + '</p>')
        body += f'<input class="search" id="appq" type="search" placeholder="{T("App-Name, z. B. Forge of Empires", "App name, e.g. Forge of Empires")}" aria-label="{T("App suchen", "Search apps")}" autocomplete="off">'
        body += f'<p class="secnote"><a href="{pre}/apps/{T("spiele", "games")}/">{T("Nur Spiele: Game-Studios in Deutschland", "Games only: game studios in Germany")} &rarr;</a></p>'
        body += table(allapps, lang)
        body += f'<p class="empty" id="appempty">{T("Keine App gefunden. Wir listen Apps von Firmen mit Sitz in Deutschland.", "No app found. We list apps by companies based in Germany.")}</p>'
        body += f'<p class="secnote">{T("Quelle: Google Play (Entwickler, Downloads). Offene Stellen live aus den Bewerbungssystemen der Firmen, Stand", "Source: Google Play (developer, installs). Open roles live from the companies&#39; hiring systems, as of")} {TODAY}.</p>'
        ld = [breadcrumb([("Home", SITE + home(pre)), ("Apps", url)]),
              {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": k + 1, "url": f"{SITE}{pre}/apps/{s}/", "name": name_of(a)} for k, (c, a, s) in enumerate(pages[:100])]}]
        doc = head(title, desc, url, extra='\n' + EXTRA_CSS + '\n' + jsonld(ld), lang=lang, alt={'de': f"{SITE}/apps/", 'en': f"{SITE}/en/apps/"}, active='companies')
        doc += body + SEARCH_JS + '</div>' + (FOOT if de else FOOT_EN) + '</body></html>'
        write(f"{pre}/apps/", doc); out_urls.append(url)
        # /apps/spiele/ + /en/apps/games/
        hs = T('spiele', 'games'); url = f"{SITE}{pre}/apps/{hs}/"
        title = T(f"Game-Studios in Deutschland: Wer macht welches Spiel? ({len(gjobs)} Jobs)", f"Game Studios in Germany: Who Makes Which Game ({len(gjobs)} Jobs)")
        title = fit(title, T("Game-Studios in Deutschland: Wer macht welches Spiel?", "Game Studios in Germany: Who Makes Which Game"))
        desc = T(f"Welche Firma steckt hinter Candy Crush, Forge of Empires und Co.? {len(games)} Spiele, die Studios dahinter und {len(gjobs)} offene Stellen bei Game-Studios in Deutschland.",
                 f"Which company makes Candy Crush, Forge of Empires and co.? {len(games)} games, the studios behind them and {len(gjobs)} open roles at game studios in Germany.")
        body = f'<nav class="crumb"><a href="{home(pre)}">Home</a> / <a href="{pre}/apps/">Apps</a> / {T("Spiele", "Games")}</nav>'
        body += f'<h1>{T("Game-Studios in Deutschland", "Game studios in Germany")}</h1>'
        body += ('<p class="sub">' + T(f"Welche Firma steckt hinter welchem Spiel, und wer stellt gerade ein? {len(games)} Spiele aus Deutschland nach Downloads, und {len(studios)} Studios mit offenen Stellen.",
                                      f"Which company makes which game, and who is hiring? {len(games)} games made in Germany by installs, and {len(studios)} studios with open roles.") + '</p>')
        body += f'<h2>{T("Studios, die gerade einstellen", "Studios hiring now")}</h2>' + co_cards(studios, de, lang, 'games-studio')
        body += f'<h2>{T("Offene Stellen bei Game-Studios", "Open roles at game studios")} ({len(gjobs)})</h2>' + job_rows(gjobs[:40], de, 'games-job', show_co=True)
        body += f'<h2>{T("Spiele und ihre Studios", "Games and their studios")}</h2>'
        body += f'<input class="search" id="appq" type="search" placeholder="{T("Spiel suchen, z. B. Candy Crush", "Search a game, e.g. Candy Crush")}" aria-label="{T("Spiel suchen", "Search games")}" autocomplete="off">'
        body += table(games, lang) + f'<p class="empty" id="appempty">{T("Kein Spiel gefunden.", "No game found.")}</p>'
        body += f'<p class="secnote"><a href="{pre}/apps/">{T("Alle Apps: Wer steckt hinter der App?", "All apps: who makes this app?")} &rarr;</a></p>'
        ld = [breadcrumb([("Home", SITE + home(pre)), ("Apps", f"{SITE}{pre}/apps/"), (T("Spiele", "Games"), url)])]
        doc = head(title, desc, url, extra='\n' + EXTRA_CSS + '\n' + jsonld(ld), lang=lang, alt={'de': f"{SITE}/apps/spiele/", 'en': f"{SITE}/en/apps/games/"}, active='companies')
        doc += body + SEARCH_JS + '</div>' + (FOOT if de else FOOT_EN) + '</body></html>'
        write(f"{pre}/apps/{hs}/", doc); out_urls.append(url)
    print(f"app pages: {len(pages)} x 2 | hub apps: {len(allapps)} | games: {len(games)} | game studios hiring: {len(studios)} ({len(gjobs)} jobs)")
    return out_urls
