# -*- coding: utf-8 -*-
import json, os, re, html as htmlmod, unicodedata, collections
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

CSS="""
:root{--bg:#F7F6EF;--surface:#fff;--ink:#131310;--muted:#52524A;--faint:#75756B;--line:#131310;--accent:#FFD400;--chip:#F1EFE3}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#131310;--surface:#1D1D18;--ink:#F4F1E0;--muted:#B8B5A3;--faint:#8A887B;--line:#4A4940;--chip:#26261F}}
*{box-sizing:border-box}html{scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Archivo,system-ui,sans-serif;font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:inherit}
#top{position:sticky;top:0;z-index:20;background:#131310}
#top .bar{max-width:900px;margin:0 auto;padding:11px 20px;display:flex;align-items:center;gap:14px}
.wordmark{display:flex;font-weight:900;font-size:13px;letter-spacing:.04em;text-transform:uppercase;text-decoration:none;line-height:1}
.wordmark .a{background:#FFD400;color:#131310;padding:7px 9px}.wordmark .b{background:#fff;color:#131310;padding:7px 9px;border-left:2.5px solid #131310}
#top .spacer{flex:1}#top .nav{color:#B8B5A3;text-decoration:none;font-weight:700;font-size:13px;margin-left:14px}#top .nav:hover{color:#FFD400}
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
footer{margin-top:52px;border-top:1px solid var(--line);padding-top:16px;color:var(--faint);font-size:13px;line-height:1.9}
footer a{color:var(--muted);text-decoration:none;margin-right:16px;border-bottom:1px solid var(--line)}footer a:hover{color:var(--accent)}
.secnote{color:var(--faint);font-size:13px;margin:2px 0 14px}
"""

def head(title, desc, url, extra=""):
    return f"""<!doctype html><html lang="de"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Berlin App Jobs">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{url}">
<link rel="icon" href="{FAV}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;800;900&display=swap">
<style>{CSS}</style>{extra}
</head><body>
<div id="top"><div class="bar"><a class="wordmark" href="/"><span class="a">Berlin</span><span class="b">App Jobs</span></a>
<div class="spacer"></div><a class="nav" href="/jobs/">Jobs</a><a class="nav" href="/companies/">Companies</a><a class="nav" href="/guides/">Guides</a></div></div>
<div class="wrap">"""

FOOT=('<footer><div style="margin-bottom:10px">'
      '<a href="/">Job board</a><a href="/companies/">Companies</a><a href="/jobs/">Jobs by role & city</a><a href="/guides/">Guides</a>'
      '</div><div>Berlin App Jobs, jobs at the companies behind Germany\'s top apps. Live weekly from company hiring systems.</div></footer>')

# jobs per company city (city pages exist only for cities with >= 10 jobs, see city_pages below)
CITY_JOBS=collections.Counter()
for _c in COS:
    if _c.get('city'): CITY_JOBS[_c['city']]+=len(_c.get('jobs') or [])

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
for c in comps:
    slug=slugify(c['n'])
    base=slug; k=2
    while slug in used: slug=f"{base}-{k}"; k+=1
    used.add(slug)
    c['_slug']=slug
    city=c.get('city','') or ''
    njobs=len(c.get('jobs',[])); total=c.get('total',njobs) or njobs
    apps=c.get('apps',[]) or []
    appnames=", ".join(a['t'] for a in apps[:3])
    title=f"{c['n']} Jobs 2026 - offene Stellen | Berlin App Jobs"
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
    doc=head(title,desc,url,extra="\n"+jsonld(ld))
    doc+=f'<nav class="crumb"><a href="/">Home</a> / <a href="/companies/">Companies</a> / {esc(c["n"])}</nav>'
    doc+=f'<h1>Jobs bei {esc(c["n"])}</h1>'
    doc+=f'<p class="sub">{esc(desc)}</p>'
    doc+=f'<div class="meta">'+(f'<span class="pill">{esc(city)}</span>' if city else '')+(f'<span class="pill">{njobs or total} offene Stellen</span>')+f'<span>Aktualisiert {TODAY}</span></div>'
    doc+=apphtml+roleshtml
    doc+='<div style="margin-top:18px">'+cta+' '+citylink+'</div>'
    doc+=FOOT+'</div></body></html>'
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
             url)
    doc+='<nav class="crumb"><a href="/">Home</a> / Companies</nav>'
    doc+=f'<h1>App-Unternehmen mit offenen Stellen</h1>'
    doc+=f'<p class="sub">Die {len(company_index)} Unternehmen hinter Deutschlands meistgenutzten Apps, die aktuell einstellen. Jede Firma mit ihren Apps, offenen Rollen und Direktbewerbung.</p>'
    doc+=f'<div class="grid">{cards}</div>'+FOOT+'</div></body></html>'
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

def role_rows(jobs, limit=100):
    out=""
    for jb in jobs[:limit]:
        co=jb['_co']; coslug=jb.get('_coslug')
        colink=f'/companies/{coslug}/' if coslug else '#'
        jpu=JOBPAGE.get(jb.get("u",""))
        out+=((f'<a class="row" href="{jpu}">' if jpu else f'<a class="row" href="{esc(jb.get("u","#"))}" target="_blank" rel="noopener nofollow">')+
              f'<div class="m"><div class="t">{esc(jb["t"])}</div>'
              f'<div class="d">{esc(co)}{" &middot; "+esc(jb.get("loc","")) if jb.get("loc") else ""}</div></div>'
              +(f'<span class="apply">Details</span></a>' if jpu else f'<span class="apply">Bewerben &#8599;</span></a>'))
    return out

rc_index=[]
for (d,city),jl in sorted(rc_pages,key=lambda x:-len(x[1])):
    dslug,dname=DISC[d]; cslug=city_slug(city)
    slug=f"{dslug}/{cslug}"; rc_index.append((d,city,dname,slug,len(jl)))
    url=f"{SITE}/jobs/{slug}/"
    title=f"{dname}-Jobs in {city} ({len(jl)} offen) 2026 | Berlin App Jobs"
    desc=f"{len(jl)} offene {dname}-Stellen bei App-Unternehmen in {city}. Live aus den Bewerbungssystemen, mit Direktbewerbung. Aktualisiert {TODAY}."
    cos=sorted({jb['_co'] for jb in jl})
    ld=[jobposting_list(jl), breadcrumb([("Home",SITE+"/"),("Jobs",SITE+"/jobs/"),(f"{dname} in {city}",url)])]
    doc=head(title,desc,url,extra="\n"+jsonld(ld))
    doc+=f'<nav class="crumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / {esc(dname)} in {esc(city)}</nav>'
    doc+=f'<h1>{esc(dname)}-Jobs in {esc(city)}</h1>'
    doc+=f'<p class="sub">{esc(desc)}</p>'
    doc+=f'<div class="meta"><span class="pill">{len(jl)} offene Stellen</span><span class="pill">{len(cos)} Unternehmen</span></div>'
    doc+=f'<a class="cta" href="/?disc={d}&amp;city={esc(quote(city))}">Diese Stellen im Jobboard filtern &rarr;</a>'
    doc+=f'<h2>Offene {esc(dname)}-Stellen in {esc(city)}</h2>'+role_rows(jl)
    doc+=f'<h2>Unternehmen, die einstellen</h2><p class="secnote">'+", ".join(esc(x) for x in cos[:40])+'</p>'
    if CITY_JOBS.get(city, 0) >= 10: doc+=f'<div style="margin-top:16px"><a class="nav" style="color:var(--accent);margin:0" href="/jobs/{cslug}/">Alle App-Jobs in {esc(city)} &rarr;</a></div>'
    doc+=FOOT+'</div></body></html>'
    dd=os.path.join(jobs_dir,dslug,cslug); os.makedirs(dd,exist_ok=True)
    open(os.path.join(dd,"index.html"),"w",encoding='utf-8').write(doc)

city_index=[]
for city,jl in sorted(city_pages,key=lambda x:-len(x[1])):
    cslug=city_slug(city); city_index.append((city,cslug,len(jl)))
    url=f"{SITE}/jobs/{cslug}/"
    title=f"App-Jobs in {city} ({len(jl)} offen) 2026 | Berlin App Jobs"
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
    doc=head(title,desc,url,extra="\n"+jsonld(ld))
    doc+=f'<nav class="crumb"><a href="/">Home</a> / <a href="/jobs/">Jobs</a> / {esc(city)}</nav>'
    doc+=f'<h1>App-Jobs in {esc(city)}</h1>'
    doc+=f'<p class="sub">{esc(desc)}</p>'
    doc+=f'<div class="meta"><span class="pill">{len(jl)} offene Stellen</span><span class="pill">{len(cos)} Unternehmen</span></div>'
    doc+=f'<a class="cta" href="/?city={esc(quote(city))}">Alle {city}-Stellen im Jobboard &rarr;</a>'
    if rl: doc+=f'<h2>Nach Disziplin</h2><div class="grid">{rl}</div>'
    doc+=f'<h2>Neueste offene Stellen</h2>'+role_rows(jl,limit=60)
    doc+=FOOT+'</div></body></html>'
    dd=os.path.join(jobs_dir,cslug); os.makedirs(dd,exist_ok=True)
    open(os.path.join(dd,"index.html"),"w",encoding='utf-8').write(doc)

# jobs hub
def jobs_hub():
    url=f"{SITE}/jobs/"
    citycards="".join(f'<a class="card" href="/jobs/{cslug}/"><div class="ct">App-Jobs in {esc(city)}</div><div class="cd">{n} offene Stellen</div></a>' for city,cslug,n in city_index)
    rolecards="".join(f'<a class="card" href="/jobs/{slug}/"><div class="ct">{esc(dname)} in {esc(city)}</div><div class="cd">{n} offene Stellen</div></a>' for d,city,dname,slug,n in rc_index)
    doc=head("App-Jobs nach Rolle und Stadt | Berlin App Jobs",
             "App-Jobs in Deutschland nach Disziplin und Stadt: Entwickler, Produkt, Design, Data, Marketing und mehr, in Berlin, Muenchen, Hamburg und weiteren Staedten.",
             url)
    doc+='<nav class="crumb"><a href="/">Home</a> / Jobs</nav>'
    doc+='<h1>App-Jobs nach Rolle und Stadt</h1>'
    doc+='<p class="sub">Offene Stellen bei den Unternehmen hinter Deutschlands Top-Apps, aufgeschluesselt nach Disziplin und Stadt. Jede Seite live aus den Bewerbungssystemen.</p>'
    doc+='<h2>Nach Stadt</h2><div class="grid">'+citycards+'</div>'
    doc+='<h2>Nach Rolle und Stadt</h2><div class="grid">'+rolecards+'</div>'
    doc+=FOOT+'</div></body></html>'
    open(os.path.join(jobs_dir,"index.html"),"w",encoding='utf-8').write(doc)
jobs_hub()

# ============ SITEMAP (full) ============
urls=[(SITE+"/","1.0"),(SITE+"/guides/","0.8"),(SITE+"/companies/","0.8"),(SITE+"/jobs/","0.8")]
for g in GUIDES: urls.append((f'{SITE}/guides/{g["slug"]}/',"0.7"))
for n,slug,city,nj,total in company_index: urls.append((f'{SITE}/companies/{slug}/',"0.6"))
for d,city,dname,slug,n in rc_index: urls.append((f'{SITE}/jobs/{slug}/',"0.6"))
for city,cslug,n in city_index: urls.append((f'{SITE}/jobs/{cslug}/',"0.6"))
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u,p in urls: sm+=f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{p}</priority></url>\n'
sm+='</urlset>\n'
open(os.path.join(OUT,"sitemap.xml"),"w",encoding='utf-8').write(sm)

print("company pages:",len(company_index))
print("role x city pages:",len(rc_index))
print("city pages:",len(city_index))
print("sitemap urls:",len(urls))
