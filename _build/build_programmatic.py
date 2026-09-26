# -*- coding: utf-8 -*-
import json, os, re, html as htmlmod, unicodedata, collections, datetime
from urllib.parse import quote

SITE="https://berlinappjobs.com"
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT, DATA, TODAY
FAV=("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
     "%3Crect width='100' height='100' rx='18' fill='%23FFD400'/%3E%3Ctext x='50' y='73' "
     "font-family='Arial,sans-serif' font-size='68' font-weight='900' text-anchor='middle' "
     "fill='%23131310'%3EB%3C/text%3E%3C/svg%3E")

# ---- load board ----
s=open(os.path.join(DATA,'board_data.js'),encoding='utf-8').read()
i=s.find('const BOARD = '); j=s.find('const CHARTS', i)
B=json.loads(s[i+len('const BOARD = '):j].rstrip().rstrip(';').rstrip())
COS=B['companies']

# ---- guides (for sitemap + cross-link) ----
gjs=open(os.path.join(DATA,'guides_data.js'),encoding='utf-8').read()
GUIDES=json.loads(gjs[gjs.find('=')+1:].strip().rstrip(';'))

def esc(s): return htmlmod.escape(str(s), quote=True)

def slugify(name, strip_legal=True):
    n=name
    if strip_legal:
        n=re.sub(r'\b(GmbH & Co\.? KG|GmbH & Co KG|GmbH|AG|SE|mbH|Inc\.?|Ltd\.?|LLC|e\.?V\.?|Co\.?|KG|Stiftung|& Co|Group|Holding|Deutschland|Verlag)\b','',n, flags=re.I)
    n=n.replace('&',' and ')
    n=(n.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss')
        .replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue'))
    n=unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode('ascii')
    n=re.sub(r'[^a-zA-Z0-9]+','-',n).strip('-').lower()
    n=re.sub(r'-+','-',n)
    return n or 'company'

def city_slug(city):
    return slugify(city, strip_legal=False)

DISC={
 'eng':('entwickler','Entwickler'),
 'product':('product-management','Product Management'),
 'design':('design','Design'),
 'data':('data','Data und Analytics'),
 'marketing':('marketing','Marketing'),
 'sales':('sales','Sales'),
 'support':('support','Customer Support'),
 'people':('people','People und HR'),
 'health':('health','Health'),
}

import header as site_hdr   # the same header as the job board, on every static page
CSS=site_hdr.CSS+"""
:root{--bg:#F7F6EF;--surface:#fff;--ink:#131310;--muted:#52524A;--faint:#75756B;--line:#131310;--accent:#FFD400;--chip:#F1EFE3}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#131310;--surface:#1D1D18;--ink:#F4F1E0;--muted:#B8B5A3;--faint:#8A887B;--line:#4A4940;--chip:#26261F}}
*{box-sizing:border-box}html{scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Archivo,system-ui,sans-serif;font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit}
.wrap{max-width:900px;margin:0 auto;padding:0 20px 80px}
.crumb{font-size:13px;color:var(--faint);margin:22px 0 6px}.crumb a{color:var(--faint);text-decoration:none}.crumb a:hover{color:var(--accent)}
h1{font-family:Archivo;font-weight:900;font-size:clamp(26px,4.6vw,38px);line-height:1.12;letter-spacing:-.01em;margin:6px 0 8px;text-wrap:balance}
.sub{color:var(--muted);font-size:15px;margin:0 0 6px;max-width:65ch}
.meta{color:var(--faint);font-size:13px;margin:6px 0 18px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.pill{background:var(--chip);color:var(--muted);border-radius:999px;padding:3px 10px;font-size:12px;font-weight:700}
h2{font-family:Archivo;font-weight:800;font-size:20px;margin:30px 0 10px}
.cta{display:inline-flex;align-items:center;gap:9px;background:#FFD400;color:#131310;border:2px solid #131310;border-radius:8px;padding:12px 18px;font-family:Archivo;font-weight:800;font-size:15px;text-decoration:none;margin:6px 0}
.cta:hover{background:#131310;color:#FFD400}
.row{display:flex;align-items:center;gap:12px;background:var(--surface);border:1.5px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:8px;text-decoration:none}
.row:hover{background:var(--chip)}
.row .m{flex:1;min-width:0}
.row .t{font-weight:700;font-size:15px}
.row .d{color:var(--muted);font-size:12.5px;margin-top:2px}
.row .apply{flex:none;background:#FFD400;color:#131310;border:1.5px solid #131310;border-radius:6px;padding:7px 12px;font-weight:800;font-size:12.5px;text-decoration:none;white-space:nowrap}
.row .apply:hover{background:#131310;color:#FFD400}
.ic{width:46px;height:46px;border-radius:8px;flex:none;background:var(--chip)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;margin-top:8px}
.card{display:block;text-decoration:none;border:1.5px solid var(--line);border-radius:9px;padding:15px;background:var(--surface)}
.card:hover{background:var(--chip)}
.card .ct{font-family:Archivo;font-weight:800;font-size:16px;line-height:1.2}
.card .cd{color:var(--muted);font-size:13px;margin-top:5px}
.applist a{display:inline-flex;align-items:center;gap:7px;border:1.5px solid var(--line);border-radius:8px;padding:8px 12px;margin:0 8px 8px 0;text-decoration:none;background:var(--surface);font-weight:600;font-size:13.5px}
.applist a:hover{background:var(--chip)}
.secnote{color:var(--faint);font-size:13px;margin:2px 0 14px}
"""

def alt_links(alt):
    """hreflang pairs for pages that exist in German and English: alt = {'de': url, 'en': url}."""
    return ''.join(f'<link rel="alternate" hreflang="{k}" href="{v}">' for k, v in (alt or {}).items())

_COUNTS = []
def site_counts():
    """(open roles, companies hiring): the same numbers as in the board's header."""
    if not _COUNTS:
        _COUNTS.extend([sum(len(c.get('jobs') or []) for c in COS), sum(1 for c in COS if (c.get('tier') or 9) <= 2)])
    return _COUNTS

def head(title, desc, url, extra="", lang="de", alt=None, active="jobs"):
    return f"""<!doctype html><html lang="{lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Berlin App Jobs">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">
<link rel="icon" href="{FAV}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800;900&display=swap">
<link rel="alternate" type="application/atom+xml" title="New app jobs" href="/feed.xml">{alt_links(alt)}
<style>{CSS}</style>{extra}
</head><body>
{''.join(site_hdr.site_header(lang, active, {k: v.replace(SITE, '') for k, v in (alt or {}).items()}, *site_counts()))}
<div class="wrap">"""

# site-wide footer (footer.py): FOOT for German pages, FOOT_EN for English ones
from footer import site_footer, ROLE_EN_SLUG, ROLE_EN, short_name
FOOT=site_footer('de', COS, GUIDES, slugify, city_slug, DISC, B.get('checked',''))
FOOT_EN=site_footer('en', COS, GUIDES, slugify, city_slug, DISC, B.get('checked',''))

# jobs per company city (city pages exist only for cities with >= 10 jobs, see city_pages below)
CITY_JOBS=collections.Counter()
for _c in COS:
    if _c.get('city'): CITY_JOBS[_c['city']]+=len(_c.get('jobs') or [])

# month shown in hub-page titles ("… (Sept. 2026)"), from the date of the job data
_MDE = ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sept.', 'Okt.', 'Nov.', 'Dez.']
_MEN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
_d = datetime.date.fromisoformat(TODAY)
MONTH_DE, MONTH_EN = f"{_MDE[_d.month-1]} {_d.year}", f"{_MEN[_d.month-1]} {_d.year}"
def fit_title(t):
    """Add " | Berlin App Jobs" (18 chars) only if the whole title stays within ~63 chars, where Google cuts it."""
    return t + " | Berlin App Jobs" if len(t) <= 45 else t

def jsonld(objs):
    return '\n'.join('<script type="application/ld+json">'+json.dumps(o,ensure_ascii=False)+'</script>' for o in objs)

def breadcrumb(items):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
        {"@type":"ListItem","position":k+1,"name":n,"item":u} for k,(n,u) in enumerate(items)]}

def jobposting_list(jobs, limit=50):
    # Plain ItemList only. Google allows JobPosting markup solely on single-job pages,
    # so list pages must not carry it (risk of a manual action). Items link to our job page when one exists.
    el=[]
    for k,jb in enumerate(jobs[:limit]):
        el.append({"@type":"ListItem","position":k+1,"name":jb["t"],"url":JOBPAGE.get(jb.get("u",""), jb.get("u",""))})
    return {"@context":"https://schema.org","@type":"ItemList","itemListElement":el}

JOBPAGE={}  # filled by build_jobpages.py mapping (ats url -> our /job/ url)
try:
    JOBPAGE=json.load(open(os.path.join(DATA,'jobpages_map.json')))
except Exception:
    pass
os.makedirs(OUT, exist_ok=True)

# ============ COMPANY PAGES ============
comp_dir=os.path.join(OUT,"companies"); os.makedirs(comp_dir, exist_ok=True)
used=set(); company_index=[]
comps=[c for c in COS if c.get('tier',3)<=2 and c.get('n')]
# sort by roles then installs
comps.sort(key=lambda c:(-(len(c.get('jobs',[])) or 0), -(c.get('v') or 0)))
for c in comps:   # slugs first, so pages can link to similar companies
    slug=slugify(c['n'])
    base=slug; k=2
    while slug in used: slug=f"{base}-{k}"; k+=1
    used.add(slug)
    c['_slug']=slug
NOINDEX=[]   # company pages without parsed jobs: kept for visitors and links, hidden from Google (thin content)
_truthy=lambda v: v is True or str(v).strip().lower() in ('true','1','yes')
def _join(xs):
    xs=list(xs); return xs[0] if len(xs)==1 else ', '.join(xs[:-1])+' und '+xs[-1]
def company_overview(c, city, jobs):
    """A short, factual summary from the company's own job data (no guessing), plus similar employers."""
    n=len(jobs); name=esc(c['n'])
    disc=collections.Counter(j.get('d') for j in jobs)
    top=[f"{DISC[d][1]} ({k})" for d,k in disc.most_common() if d in DISC][:3]
    en=sum(1 for j in jobs if j.get('lang')=='en'); rem=sum(1 for j in jobs if _truthy(j.get('rem')))
    sal=sum(1 for j in jobs if j.get('sal')); entry=sum(1 for j in jobs if j.get('s') in ('intern','junior'))
    senior=sum(1 for j in jobs if j.get('s') in ('senior','lead'))
    locs=collections.Counter(re.split(r'[,/|(]',j.get('loc') or city or '')[0].strip() or city for j in jobs)
    p=[f"{name} sucht aktuell {n} {'Person' if n==1 else 'Leute'}" + (f", vor allem in {_join(top)}." if top else ".")]
    if en==n: p.append("Alle Anzeigen sind auf Englisch, Deutsch ist hier meist keine Voraussetzung.")
    elif en: p.append(f"{en} von {n} Anzeigen sind auf Englisch ({round(100*en/n)} %), der Rest auf Deutsch.")
    else: p.append("Alle Anzeigen sind auf Deutsch, gute Deutschkenntnisse werden also meist erwartet.")
    lv=[]
    if entry: lv.append(f"{entry} für Einsteiger (Praktikum, Werkstudent, Junior)")
    if senior: lv.append(f"{senior} für Senior- und Lead-Rollen")
    if lv: p.append("Davon "+_join(lv)+".")
    if rem: p.append(f"{rem} {'Stelle ist' if rem==1 else 'Stellen sind'} remote oder hybrid möglich.")
    p.append(f"{sal} {'Anzeige nennt' if sal==1 else 'Anzeigen nennen'} ein Gehalt." if sal else "Keine der Anzeigen nennt ein Gehalt.")
    if len(locs)>1: p.append("Standorte: "+_join(esc(l) for l,_ in locs.most_common(4) if l)+".")
    apps=[a for a in c.get('apps') or [] if a.get('t')][:2]
    if apps: p.append("Bekannt für "+_join(f"{esc(htmlmod.unescape(a['t']))}"+(f" ({esc(a['i'])} Downloads bei Google Play)" if a.get('i') else '') for a in apps)+".")
    html='<h2>Überblick</h2><p>'+' '.join(p)+'</p>'
    peers=[o for o in comps if o is not c and o.get('jobs') and (o.get('city') or '')==city][:6]
    same_city=len(peers)>=3
    if not same_city: peers=[o for o in comps if o is not c and o.get('jobs')][:6]
    if peers:
        html+=f'<h2>Ähnliche Arbeitgeber{(" in "+esc(city)) if city and same_city else ""}</h2><div class="applist">'
        html+=''.join(f'<a href="/companies/{o["_slug"]}/">{esc(o["n"])} &middot; {len(o["jobs"])} Stellen</a>' for o in peers)+'</div>'
    return html
for c in comps:
    slug=c['_slug']
    city=c.get('city','') or ''
    njobs=len(c.get('jobs',[])); total=c.get('total',njobs) or njobs
    apps=c.get('apps',[]) or []
    appnames=", ".join(a['t'] for a in apps[:3])
    title=(fit_title(f"{short_name(c['n'])} Jobs: {njobs} offene Stellen ({MONTH_DE})") if njobs
           else f"{c['n']} Jobs 2026 - offene Stellen | Berlin App Jobs")
    desc=(f"Offene Stellen bei {c['n']}"+(f" in {city}" if city else "")+f". "
          + (f"{njobs} Rollen live aus dem Bewerbungssystem, mit Direktbewerbung." if njobs else f"{total} offene Stellen.")
          + (f" Team hinter {apps[0]['t']}." if apps else ""))
    url=f"{SITE}/companies/{slug}/"
    # apps block
    apphtml=""
    if apps:
        apphtml='<h2>Apps</h2><div class="applist">'
        for a in apps[:8]:
            play=f"https://play.google.com/store/apps/details?id={a['id']}" if a.get('id') else None
            inst=f" &middot; {esc(a['i'])}" if a.get('i') else ""
            if play: apphtml+=f'<a href="{esc(play)}" target="_blank" rel="noopener nofollow">{esc(a["t"])}{inst}</a>'
            else: apphtml+=f'<span class="applist"><a>{esc(a["t"])}{inst}</a></span>'
        apphtml+='</div>'
    # roles block
    roleshtml=""
    if njobs:
        roleshtml='<h2>Offene Stellen ('+str(njobs)+')</h2>'
        for jb in c['jobs']:
            dloc=esc(jb.get('loc','') or city); dd=DISC.get(jb.get('d',''),('','') )[1]
            jpu=JOBPAGE.get(jb.get("u",""))
            roleshtml+=((f'<a class="row" href="{jpu}">' if jpu else f'<a class="row" href="{esc(jb.get("u","#"))}" target="_blank" rel="noopener nofollow">')+
                        f'<div class="m"><div class="t">{esc(jb["t"])}</div>'
                        f'<div class="d">{dloc}{" &middot; "+esc(dd) if dd else ""}</div></div>'
                        +(f'<span class="apply">Details</span></a>' if jpu else f'<span class="apply">Bewerben &#8599;</span></a>'))
    else:
        roleshtml=(f'<h2>Offene Stellen</h2><p class="sub">{c["n"]} hat aktuell rund {total} offene Stellen. '
                   f'Diese werden noch nicht einzeln geparst.</p>'
                   f'<a class="cta" href="{esc(c.get("careers") or "#")}" target="_blank" rel="noopener nofollow">Alle {total} Stellen auf der Karriereseite &#8599;</a>')
    for jb in c.get('jobs',[]): jb['_co']=c['n']
    ld=[{"@context":"https://schema.org","@type":"Organization","name":c['n'],"url":url,
         **({"address":{"@type":"PostalAddress","streetAddress":c.get('addr',''),"addressLocality":city,"addressCountry":"DE"}} if c.get('addr') else {})},
        breadcrumb([("Home",SITE+"/"),("Companies",SITE+"/companies/"),(c['n'],url)])]
    if njobs: ld.append(jobposting_list([dict(jb,_co=c['n']) for jb in c['jobs']]))
    cta=(f'<a class="cta" href="/?q={esc(quote(c["n"]))}">Diese Firma im Jobboard ansehen &rarr;</a>')
    citylink=f'<a class="nav" style="color:var(--accent);margin:0" href="/jobs/{city_slug(city)}/">Mehr App-Jobs in {esc(city)}</a>' if city and njobs and CITY_JOBS.get(city, 0) >= 10 else ''  # only cities that get a page
    if not njobs: NOINDEX.append(f"companies/{slug}")
    doc=head(title,desc,url,extra=("\n"+'<meta name="robots" content="noindex, follow">' if not njobs else "")+"\n"+jsonld(ld),active="companies")
    doc+=f'<nav class="crumb"><a href="/">Home</a> / <a href="/companies/">Companies</a> / {esc(c["n"])}</nav>'
    doc+=f'<h1>Jobs bei {esc(c["n"])}</h1>'
    doc+=f'<p class="sub">{esc(desc)}</p>'
    doc+=f'<div class="meta">'+(f'<span class="pill">{esc(city)}</span>' if city else '')+(f'<span class="pill">{njobs or total} offene Stellen</span>')+f'<span>Aktualisiert {TODAY}</span></div>'
    doc+=(company_overview(c, city, c['jobs']) if njobs else '')+apphtml+roleshtml
    doc+='<div style="margin-top:18px">'+cta+' '+citylink+'</div>'
    doc+='</div>'+FOOT+'</body></html>'
    d=os.path.join(comp_dir,slug); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding='utf-8').write(doc)
    company_index.append((c['n'],slug,city,njobs,total))

# companies hub
def companies_hub():
    url=f"{SITE}/companies/"
    cards=""
    for n,slug,city,nj,total in company_index:
        cards+=(f'<a class="card" href="/companies/{slug}/"><div class="ct">{esc(n)}</div>'
                f'<div class="cd">'+(esc(city)+' &middot; ' if city else '')+ (f'{nj} offene Stellen' if nj else f'{total} Stellen')+'</div></a>')
    doc=head("App-Unternehmen in Deutschland: alle Firmen & Jobs | Berlin App Jobs",
             f"Alle {len(company_index)} Unternehmen hinter Deutschlands Top-Apps mit offenen Stellen. Apps, Rollen, Standort und Direktbewerbung.",
             url, active="companies")
    doc+='<nav class="crumb"><a href="/">Home</a> / Companies</nav>'
    doc+=f'<h1>App-Unternehmen mit offenen Stellen</h1>'
    doc+=f'<p class="sub">Die {len(company_index)} Unternehmen hinter Deutschlands meistgenutzten Apps, die aktuell einstellen. Jede Firma mit ihren Apps, offenen Rollen und Direktbewerbung.</p>'
    doc+=f'<div class="grid">{cards}</div>'+'</div>'+FOOT+'</body></html>'
    open(os.path.join(comp_dir,"index.html"),"w",encoding='utf-8').write(doc)
companies_hub()

# ============ ROLE x CITY + CITY PAGES ============
jobs_dir=os.path.join(OUT,"jobs"); os.makedirs(jobs_dir,exist_ok=True)
# build (disc,city)->jobs and city->jobs using company city
rc=collections.defaultdict(list); citymap=collections.defaultdict(list); citycos=collections.defaultdict(set)
for c in COS:
    city=c.get('city','') or ''
    for jb in c.get('jobs',[]):
        d=jb.get('d','')
        j2=dict(jb,_co=c['n'],_coslug=c.get('_slug'))
        if city:
            if d in DISC: rc[(d,city)].append(j2)
            citymap[city].append(j2)
            citycos[city].add(c['n'])

rc_pages=[(k,v) for k,v in rc.items() if len(v)>=5]
city_pages=[(city,jl) for city,jl in citymap.items() if len(jl)>=10]

def role_rows(jobs, limit=100, lang="de"):
    out=""
    for jb in jobs[:limit]:
        co=jb['_co']; coslug=jb.get('_coslug')
        colink=f'/companies/{coslug}/' if coslug else '#'
        jpu=JOBPAGE.get(jb.get("u",""))
        out+=((f'<a class="row" href="{jpu}">' if jpu else f'<a class="row" href="{esc(jb.get("u","#"))}" target="_blank" rel="noopener nofollow">')+
              f'<div class="m"><div class="t">{esc(jb["t"])}</div>'
              f'<div class="d">{esc(co)}{" &middot; "+esc(jb.get("loc","")) if jb.get("loc") else ""}</div></div>'
              +(f'<span class="apply">Details</span></a>' if jpu else f'<span class="apply">{"Apply" if lang=="en" else "Bewerben"} &#8599;</span></a>'))
    return out

rc_index=[]
for (d,city),jl in sorted(rc_pages,key=lambda x:-len(x[1])):
    dslug,dname=DISC[d]; cslug=city_slug(city)
    slug=f"{dslug}/{cslug}"; rc_index.append((d,city,dname,slug,len(jl)))
    url=f"{SITE}/jobs/{slug}/"
    title=fit_title(f"{dname}-Jobs in {city}: {len(jl)} offene Stellen ({MONTH_DE})")
    desc=f"{len(jl)} offene {dname}-Stellen bei App-Unternehmen in {city}. Live aus den Bewerbungssystemen, mit Direktbewerbung. Aktualisiert {TODAY}."
    cos=sorted({jb['_co'] for jb in jl})
    ld=[jobposting_list(jl), breadcrumb([("Home",SITE+"/"),("Jobs",SITE+"/jobs/"),(f"{dname} in {city}",url)])]
    doc=head(title,desc,url,extra="\n"+jsonld(ld),alt={'de':url,'en':f"{SITE}/en/jobs/{ROLE_EN_SLUG[d]}/{cslug}/"})
    doc+=f'<nav class="crumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / {esc(dname)} in {esc(city)}</nav>'
    doc+=f'<h1>{esc(dname)}-Jobs in {esc(city)}</h1>'
    doc+=f'<p class="sub">{esc(desc)}</p>'
    doc+=f'<div class="meta"><span class="pill">{len(jl)} offene Stellen</span><span class="pill">{len(cos)} Unternehmen</span></div>'
    doc+=f'<a class="cta" href="/?disc={d}&amp;city={esc(quote(city))}">Diese Stellen im Jobboard filtern &rarr;</a>'
    doc+=f'<h2>Offene {esc(dname)}-Stellen in {esc(city)}</h2>'+role_rows(jl)
    doc+=f'<h2>Unternehmen, die einstellen</h2><p class="secnote">'+", ".join(esc(x) for x in cos[:40])+'</p>'
    if CITY_JOBS.get(city, 0) >= 10: doc+=f'<div style="margin-top:16px"><a class="nav" style="color:var(--accent);margin:0" href="/jobs/{cslug}/">Alle App-Jobs in {esc(city)} &rarr;</a></div>'
    doc+='</div>'+FOOT+'</body></html>'
    dd=os.path.join(jobs_dir,dslug,cslug); os.makedirs(dd,exist_ok=True)
    open(os.path.join(dd,"index.html"),"w",encoding='utf-8').write(doc)

# ---- extra German/English list pages: platform (iOS, Android) and English-speaking jobs per city ----
SKILLS = [('ios', 'ios-entwickler', 'iOS-Entwickler', 'ios-developer', 'iOS developer', re.compile(r'\bios\b|\bswift\b', re.I)),
          ('android', 'android-entwickler', 'Android-Entwickler', 'android-developer', 'Android developer', re.compile(r'\bandroid\b|\bkotlin\b', re.I)),
          ('mobile', 'mobile-entwickler', 'Mobile-Entwickler', 'mobile-developer', 'Mobile developer',
           re.compile(r'\bios\b|\bswift\b|\bandroid\b|\bkotlin\b|\bflutter\b|react native|\bmobile\b|\bapp[- ]?(entwickler|developer|engineer)', re.I))]
extra_pages = []   # (kind, city, de_slug, de_name, en_slug, en_name, jobs)
for city, jl in citymap.items():
    for key, ds, dn, es, en_, rx in SKILLS:
        sj = [j for j in jl if j.get('d') == 'eng' and rx.search(j.get('t') or '')]
        if len(sj) >= 5: extra_pages.append((key, city, f"{ds}/{city_slug(city)}", dn, f"{es}/{city_slug(city)}", en_, sj))
    ej = [j for j in jl if j.get('lang') == 'en']
    if len(ej) >= 10:
        extra_pages.append(('english', city, f"englischsprachig/{city_slug(city)}", 'Englischsprachige', f"english-speaking/{city_slug(city)}", 'English-speaking', ej))
extra_pages.sort(key=lambda x: -len(x[6]))
extra_index = [(k, city, dn, ds, len(jl)) for k, city, ds, dn, es, en_, jl in extra_pages]   # German: (kind, city, name, slug, n)
for kind, city, ds, dn, es, en_, jl in extra_pages:
    url = f"{SITE}/jobs/{ds}/"
    if kind == 'english':
        h1 = f"Englischsprachige App-Jobs in {city}"
        title = fit_title(f"Englischsprachige Jobs in {city}: {len(jl)} Stellen ({MONTH_DE})")
        desc = (f"{len(jl)} Stellen bei App-Unternehmen in {city}, deren Anzeige auf Englisch ist: Deutsch ist hier meist keine "
                f"Voraussetzung. Live aus den Bewerbungssystemen, aktualisiert {TODAY}.")
    else:
        h1 = f"{dn}-Jobs in {city}"
        title = fit_title(f"{dn}-Jobs in {city}: {len(jl)} offene Stellen ({MONTH_DE})")
        desc = f"{len(jl)} offene {dn}-Stellen bei App-Unternehmen in {city}. Live aus den Bewerbungssystemen, mit Direktbewerbung. Aktualisiert {TODAY}."
    cos = sorted({jb['_co'] for jb in jl})
    ld = [jobposting_list(jl), breadcrumb([("Home", SITE+"/"), ("Jobs", SITE+"/jobs/"), (h1, url)])]
    doc = head(title, desc, url, extra="\n"+jsonld(ld), alt={'de': url, 'en': f"{SITE}/en/jobs/{es}/"})
    doc += f'<nav class="crumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / {esc(h1)}</nav><h1>{esc(h1)}</h1><p class="sub">{esc(desc)}</p>'
    doc += f'<div class="meta"><span class="pill">{len(jl)} Stellen</span><span class="pill">{len(cos)} Unternehmen</span></div>'
    doc += f'<h2>Offene Stellen</h2>' + role_rows(jl)
    doc += f'<h2>Unternehmen, die einstellen</h2><p class="secnote">' + ", ".join(esc(x) for x in cos[:40]) + '</p>'
    doc += f'<div style="margin-top:16px"><a class="nav" style="color:var(--accent);margin:0" href="/jobs/{city_slug(city)}/">Alle App-Jobs in {esc(city)} &rarr;</a></div>'
    doc += '</div>' + FOOT + '</body></html>'
    dd = os.path.join(jobs_dir, *ds.split('/')); os.makedirs(dd, exist_ok=True)
    open(os.path.join(dd, "index.html"), "w", encoding='utf-8').write(doc)

city_index=[]
for city,jl in sorted(city_pages,key=lambda x:-len(x[1])):
    cslug=city_slug(city); city_index.append((city,cslug,len(jl)))
    url=f"{SITE}/jobs/{cslug}/"
    title=fit_title(f"App-Jobs in {city}: {len(jl)} offene Stellen ({MONTH_DE})")
    desc=f"{len(jl)} offene Stellen bei App-Unternehmen in {city}: Engineering, Produkt, Design, Data, Marketing und mehr. Direktbewerbung, aktualisiert {TODAY}."
    dcount=collections.Counter(jb['d'] for jb in jl)
    cos=sorted({jb['_co'] for jb in jl})
    disc_links=""
    for d,n in dcount.most_common():
        if d in DISC and (d,city) in dict(((a,b),1) for a,b in [(k) for k in rc]) : pass
    # links to role pages that exist for this city
    rl=""
    for d,c2,dname,slug,n in rc_index:
        if c2==city:
            rl+=f'<a class="card" href="/jobs/{slug}/"><div class="ct">{esc(dname)}</div><div class="cd">{n} offene Stellen</div></a>'
    ld=[jobposting_list(jl), breadcrumb([("Home",SITE+"/"),("Jobs",SITE+"/jobs/"),(f"App-Jobs in {city}",url)])]
    doc=head(title,desc,url,extra="\n"+jsonld(ld),alt={'de':url,'en':f"{SITE}/en/jobs/{cslug}/"})
    extra_links=''.join(f'<a class="card" href="/jobs/{x[3]}/"><div class="ct">{esc(x[2])}{" Jobs" if x[0]=="english" else "-Jobs"}</div><div class="cd">{x[4]} offene Stellen</div></a>'
                        for x in extra_index if x[1]==city)
    doc+=f'<nav class="crumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / {esc(city)}</nav>'
    doc+=f'<h1>App-Jobs in {esc(city)}</h1>'
    doc+=f'<p class="sub">{esc(desc)}</p>'
    doc+=f'<div class="meta"><span class="pill">{len(jl)} offene Stellen</span><span class="pill">{len(cos)} Unternehmen</span></div>'
    doc+=f'<a class="cta" href="/?city={esc(quote(city))}">Alle {city}-Stellen im Jobboard &rarr;</a>'
    if rl or extra_links: doc+=f'<h2>Nach Disziplin</h2><div class="grid">{extra_links}{rl}</div>'
    doc+=f'<p class="secnote" style="margin-top:10px"><a href="/en/jobs/{cslug}/" hreflang="en">English version: app jobs in {esc(city)} &rarr;</a></p>'
    doc+=f'<h2>Neueste offene Stellen</h2>'+role_rows(jl,limit=60)
    doc+='</div>'+FOOT+'</body></html>'
    dd=os.path.join(jobs_dir,cslug); os.makedirs(dd,exist_ok=True)
    open(os.path.join(dd,"index.html"),"w",encoding='utf-8').write(doc)

# jobs hub
def jobs_hub():
    url=f"{SITE}/jobs/"
    citycards="".join(f'<a class="card" href="/jobs/{cslug}/"><div class="ct">App-Jobs in {esc(city)}</div><div class="cd">{n} offene Stellen</div></a>' for city,cslug,n in city_index)
    rolecards="".join(f'<a class="card" href="/jobs/{slug}/"><div class="ct">{esc(dname)} in {esc(city)}</div><div class="cd">{n} offene Stellen</div></a>' for d,city,dname,slug,n in rc_index)
    rolecards="".join(f'<a class="card" href="/jobs/{slug}/"><div class="ct">{esc(dname)}{"-Jobs" if k!="english" else " Jobs"} in {esc(city)}</div><div class="cd">{n} Stellen</div></a>' for k,city,dname,slug,n in extra_index)+rolecards
    doc=head("App-Jobs nach Rolle und Stadt | Berlin App Jobs",
             "App-Jobs in Deutschland nach Disziplin und Stadt: Entwickler, Produkt, Design, Data, Marketing und mehr, in Berlin, Muenchen, Hamburg und weiteren Staedten.",
             url, alt={'de':url,'en':SITE+"/en/jobs/"})
    doc+='<nav class="crumb"><a href="/">Home</a> / Jobs</nav>'
    doc+='<h1>App-Jobs nach Rolle und Stadt</h1>'
    doc+='<p class="sub">Offene Stellen bei den Unternehmen hinter Deutschlands Top-Apps, aufgeschluesselt nach Disziplin und Stadt. Jede Seite live aus den Bewerbungssystemen.</p>'
    doc+='<h2>Nach Stadt</h2><div class="grid">'+citycards+'</div>'
    doc+='<h2>Nach Rolle und Stadt</h2><div class="grid">'+rolecards+'</div>'
    doc+='</div>'+FOOT+'</body></html>'
    open(os.path.join(jobs_dir,"index.html"),"w",encoding='utf-8').write(doc)
jobs_hub()

# ============ ENGLISH HUB PAGES (/en/jobs/...) ============
# Two thirds of the jobs are advertised in English, and English queries ("ios developer jobs berlin",
# "english speaking jobs berlin") are where a niche board can rank. Same pages, same thresholds as the German ones,
# each linked to its German twin with hreflang.
en_dir = os.path.join(OUT, "en", "jobs"); os.makedirs(en_dir, exist_ok=True)
en_urls = []
def en_page(rel, title, h1, desc, jl, crumb, de_rel, body_extra="", limit=100):
    url = f"{SITE}/en/jobs/{rel}/" if rel else f"{SITE}/en/jobs/"
    cos = sorted({jb['_co'] for jb in jl}) if jl else []
    ld = ([jobposting_list(jl)] if jl else []) + [breadcrumb([("Home", SITE+"/"), ("Jobs", SITE+"/en/jobs/")] + ([(crumb, url)] if rel else []))]
    doc = head(title, desc, url, extra="\n"+jsonld(ld), lang="en", alt={'de': f"{SITE}/jobs/{de_rel}/" if de_rel else f"{SITE}/jobs/", 'en': url})
    doc += (f'<nav class="crumb"><a href="/">Home</a> / ' + (f'<a href="/en/jobs/">Jobs</a> / {esc(crumb)}' if rel else 'Jobs') + '</nav>'
            f'<h1>{esc(h1)}</h1><p class="sub">{esc(desc)}</p>')
    if jl:
        n_en = sum(1 for j in jl if j.get('lang') == 'en')
        doc += (f'<div class="meta"><span class="pill">{len(jl)} open roles</span><span class="pill">{len(cos)} companies</span>'
                + (f'<span class="pill">{n_en} advertised in English</span>' if n_en and n_en < len(jl) else '') + '</div>')
    doc += body_extra
    if jl:
        doc += '<h2>Open roles</h2>' + role_rows(jl, limit=limit, lang="en")
        doc += '<h2>Companies hiring</h2><p class="secnote">' + ", ".join(esc(x) for x in cos[:40]) + '</p>'
    doc += '</div>' + FOOT_EN + '</body></html>'
    dd = os.path.join(en_dir, *rel.split('/')) if rel else en_dir; os.makedirs(dd, exist_ok=True)
    open(os.path.join(dd, "index.html"), "w", encoding='utf-8').write(doc)
    en_urls.append(url)

def tcase(x): return ' '.join(w[:1].upper() + w[1:] for w in x.split())   # 'Mobile developer' -> 'Mobile Developer' (titles)
def en_card(href, label, n): return f'<a class="card" href="{href}"><div class="ct">{esc(label)}</div><div class="cd">{n} open roles</div></a>'
en_extra = [(k, city, en_, es, len(jl)) for k, city, ds, dn, es, en_, jl in extra_pages]
for d, city, dname, slug, n in rc_index:
    jl = rc[(d, city)]; cs = city_slug(city); role = ROLE_EN.get(d, dname)
    en_page(f"{ROLE_EN_SLUG[d]}/{cs}", fit_title(f"{tcase(role)} Jobs in {city}: {n} open roles ({MONTH_EN})"), f"{role} jobs in {city}",
            f"{n} open {role.lower()} roles at app companies in {city}, live from their hiring systems. Apply directly. Updated {TODAY}.",
            jl, f"{role} in {city}", slug,
            body_extra=f'<a class="cta" href="/?disc={d}&amp;city={esc(quote(city))}">Filter these jobs on the board &rarr;</a>')
for k, city, ds, dn, es, en_, jl in extra_pages:
    if k == 'english':
        h1 = f"English-speaking app jobs in {city}"
        title = fit_title(f"English-speaking Jobs in {city}: {len(jl)} roles ({MONTH_EN})")
        desc = (f"{len(jl)} roles at app companies in {city} whose job ad is in English, so German is usually not required. "
                f"Live from the companies' hiring systems, updated {TODAY}.")
    else:
        h1 = f"{en_} jobs in {city}"
        title = fit_title(f"{tcase(en_)} Jobs in {city}: {len(jl)} open roles ({MONTH_EN})")
        desc = f"{len(jl)} open {en_} roles at app companies in {city}, live from their hiring systems. Apply directly. Updated {TODAY}."
    en_page(es, title, h1, desc, jl, h1, ds)
for city, cslug, n in city_index:
    jl = citymap[city]
    cards = ''.join(en_card(f"/en/jobs/{es}/", f"{en_} jobs in {city}", m) for k, c2, en_, es, m in en_extra if c2 == city)
    cards += ''.join(en_card(f"/en/jobs/{ROLE_EN_SLUG[d]}/{cslug}/", ROLE_EN.get(d, dname), m) for d, c2, dname, slug, m in rc_index if c2 == city)
    n_en = sum(1 for j in jl if j.get('lang') == 'en')
    en_page(cslug, fit_title(f"App Jobs in {city}: {n} open roles ({MONTH_EN})"), f"App jobs in {city}",
            f"{n} open roles at app companies in {city}, {n_en} of them advertised in English: engineering, product, design, data, "
            f"marketing and more. Live from their hiring systems, updated {TODAY}.",
            jl, city, cslug, limit=60,
            body_extra=(f'<a class="cta" href="/?city={esc(quote(city))}">All {esc(city)} jobs on the board &rarr;</a>'
                        + (f'<h2>By role</h2><div class="grid">{cards}</div>' if cards else '')))
en_page("", "App Jobs in Germany by Role and City | Berlin App Jobs", "App jobs by role and city",
        "Open roles at the companies behind Germany's top apps, by role and city: developer, product, design, data, marketing and more, "
        "in Berlin, Munich, Hamburg and other cities. Live from the companies' hiring systems.",
        [], "", "",
        body_extra=('<h2>By city</h2><div class="grid">' + ''.join(en_card(f"/en/jobs/{cs}/", f"App jobs in {c}", n) for c, cs, n in city_index) + '</div>'
                    '<h2>By role and city</h2><div class="grid">'
                    + ''.join(en_card(f"/en/jobs/{es}/", f"{en_} jobs in {c}", m) for k, c, en_, es, m in en_extra)
                    + ''.join(en_card(f"/en/jobs/{ROLE_EN_SLUG[d]}/{city_slug(c)}/", f"{ROLE_EN.get(d, dn)} jobs in {c}", m) for d, c, dn, slug, m in rc_index)
                    + '</div>'))

# ============ SITEMAP (full) ============
urls=[(SITE+"/","1.0"),(SITE+"/guides/","0.8"),(SITE+"/companies/","0.8"),(SITE+"/jobs/","0.8")]
for g in GUIDES: urls.append((f'{SITE}/guides/{g["slug"]}/',"0.7"))
for n,slug,city,nj,total in company_index:
    if nj: urls.append((f'{SITE}/companies/{slug}/',"0.6"))   # pages without parsed jobs are noindex, so not in the sitemap
json.dump(sorted(NOINDEX), open(os.path.join(DATA,'noindex_pages.json'),'w'), indent=0)   # cleanup_stale.py keeps these
for d,city,dname,slug,n in rc_index: urls.append((f'{SITE}/jobs/{slug}/',"0.6"))
for city,cslug,n in city_index: urls.append((f'{SITE}/jobs/{cslug}/',"0.6"))
for k,city,dname,slug,n in extra_index: urls.append((f'{SITE}/jobs/{slug}/',"0.6"))
for u in en_urls: urls.append((u,"0.6"))
urls.append((f'{SITE}/about/',"0.3"))
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u,p in urls: sm+=f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{p}</priority></url>\n'
sm+='</urlset>\n'
open(os.path.join(OUT,"sitemap.xml"),"w",encoding='utf-8').write(sm)

print("company pages:",len(company_index))
print("role x city pages:",len(rc_index))
print("city pages:",len(city_index))
print("extra (iOS/Android/English-speaking) pages:",len(extra_index),"| English hub pages:",len(en_urls))
print("sitemap urls:",len(urls))
