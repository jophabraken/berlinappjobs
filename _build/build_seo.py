# -*- coding: utf-8 -*-
import json, os, html as htmlmod, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT, DATA, TODAY
from articles_src import ARTICLES as ARTICLES1
from articles_src2 import ARTICLES2
import unicodedata

def _slugify(name):
    n=re.sub(r'\b(GmbH & Co\.? KG|GmbH & Co KG|GmbH|AG|SE|mbH|Inc\.?|Ltd\.?|LLC|e\.?V\.?|Co\.?|KG|Stiftung|& Co|Group|Holding|Deutschland|Verlag)\b','',name, flags=re.I)
    n=n.replace('&',' and ')
    n=(n.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('ß','ss').replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue'))
    n=unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode('ascii')
    return re.sub(r'[^a-zA-Z0-9]+','-',n).strip('-').lower()

_missing=[]
def _colinks(h):
    def rep(m):
        name,label=(m.group(1).split('|',1)+[None])[:2]
        label=label or name
        sl=_slugify(name)
        if os.path.isdir(os.path.join(OUT,'companies',sl)):
            return f'<a href="/companies/{sl}/">{label}</a>'
        _missing.append(name); return label
    return re.sub(r'\[\[([^\]]+)\]\]',rep,h)

# German guides from batch 1 were written with ae/oe/ue transliterations; restore real umlauts in text (not URLs/slugs)
_KEEP={'aktuell','aktuelle','aktuellen','lohnsteuer','steuerklasse','quereinsteiger','quereinstieg','quereinstiegs','quer','bauen','neue','zuerst','steuer','steuern','dauer','abenteuer','feuer','treue','queue','true','value'}
def _uml_word(m):
    w=m.group(0)
    if w.lower() in _KEEP or not re.search(r'ae|oe|ue|Ae|Oe|Ue',w): return w
    if w=='heisst': return 'heißt'
    return w.replace('Ae','Ä').replace('Oe','Ö').replace('Ue','Ü').replace('ae','ä').replace('oe','ö').replace('ue','ü')
def _uml_text(t):
    t=re.sub(r'[A-Za-zÄÖÜäöüß]+',_uml_word,t)
    return t.replace('heisst','heißt')
def _uml_html(h):
    parts=re.split(r'(<[^>]+>)',h)
    return ''.join(p if p.startswith('<') else _uml_text(p) for p in parts)

for _a in ARTICLES1:
    _a.setdefault('date','2026-09-21')
    if _a['lang']=='de':
        for k in ('title','metaTitle','desc','ctaLabel'): _a[k]=_uml_text(_a[k])
        _a['html']=_uml_html(_a['html'])
        _a['faq']=[[_uml_text(q),_uml_text(x)] for q,x in _a['faq']]
for _a in ARTICLES2:
    _a.setdefault('date','2026-09-22')
    _a['html']=_colinks(_a['html'])
ARTICLES = ARTICLES1 + ARTICLES2

SITE = "https://berlinappjobs.com"
GUIDES_DIR = os.path.join(OUT, "guides")
os.makedirs(GUIDES_DIR, exist_ok=True)

# ---- load existing 2 guides from guides_data.js ----
gjs = open(os.path.join(DATA,'guides_data.js'), encoding='utf-8').read()
existing = json.loads(gjs[gjs.find('=')+1:].strip().rstrip(';'))
# idempotent: only keep guides that are NOT regenerated from ARTICLES (dedupe)
_new_slugs = {a["slug"] for a in ARTICLES}
existing = [g for g in existing if g["slug"] not in _new_slugs]
# normalise existing into article dicts (no faq / hreflang; generic CTA)
existing_arts = []
for g in existing:
    if g["lang"]=="de":
        g["title"]=_uml_text(g["title"]); g["desc"]=_uml_text(g.get("desc","")); g["html"]=_uml_html(g.get("html",""))
    existing_arts.append({
        "date": "2026-09-19",
        "slug": g["slug"], "lang": g["lang"], "title": g["title"],
        "metaTitle": g["title"] + " | Berlin App Jobs",
        "desc": g.get("desc",""), "html": g.get("html",""),
        "faq": [], "hreflang": None,
        "ctaHref": "/?city=Berlin" if g["lang"]=="en" else "/",
        "ctaLabel": "Browse the live job board" if g["lang"]=="en" else "Zum Jobboard",
    })

ALL = existing_arts + ARTICLES
by_slug = {a["slug"]: a for a in ALL}

FAV = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
       "%3Crect width='100' height='100' rx='18' fill='%23FFD400'/%3E%3Ctext x='50' y='73' "
       "font-family='Arial,sans-serif' font-size='68' font-weight='900' text-anchor='middle' "
       "fill='%23131310'%3EB%3C/text%3E%3C/svg%3E")

CSS = """
:root{--bg:#F7F6EF;--surface:#fff;--ink:#131310;--muted:#52524A;--faint:#75756B;--line:#131310;--accent:#FFD400;--chip:#F1EFE3}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#131310;--surface:#1D1D18;--ink:#F4F1E0;--muted:#B8B5A3;--faint:#8A887B;--line:#4A4940;--chip:#26261F}}
*{box-sizing:border-box}
html{scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Archivo,system-ui,sans-serif;font-size:17px;line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit}
#top{position:sticky;top:0;z-index:20;background:#131310}
#top .bar{max-width:820px;margin:0 auto;padding:11px 20px;display:flex;align-items:center;gap:14px}
.wordmark{display:flex;font-weight:900;font-size:13px;letter-spacing:.04em;text-transform:uppercase;text-decoration:none;line-height:1}
.wordmark .a{background:#FFD400;color:#131310;padding:7px 9px}
.wordmark .b{background:#fff;color:#131310;padding:7px 9px;border-left:2.5px solid #131310}
#top .spacer{flex:1}
#top .nav{color:#B8B5A3;text-decoration:none;font-weight:700;font-size:13px}
#top .nav:hover{color:#FFD400}
.wrap{max-width:820px;margin:0 auto;padding:0 20px 80px}
.crumb{font-size:13px;color:var(--faint);margin:22px 0 6px}
.crumb a{color:var(--faint);text-decoration:none}.crumb a:hover{color:var(--accent)}
article h1{font-family:Archivo;font-weight:900;font-size:clamp(27px,5vw,40px);line-height:1.12;letter-spacing:-.01em;margin:6px 0 10px;text-wrap:balance}
.meta{color:var(--faint);font-size:13.5px;margin-bottom:8px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.langbadge{font-weight:800;font-size:10px;letter-spacing:.06em;background:var(--chip);color:var(--muted);border-radius:999px;padding:3px 9px}
article h2{font-family:Archivo;font-weight:800;font-size:22px;line-height:1.25;margin:34px 0 10px}
article p{margin:0 0 16px}
article ul{margin:0 0 18px;padding-left:22px}
article li{margin:5px 0}
.cta{display:inline-flex;align-items:center;gap:10px;background:#FFD400;color:#131310;border:2px solid #131310;border-radius:8px;padding:14px 20px;font-family:Archivo;font-weight:800;font-size:16px;text-decoration:none;margin:10px 0 8px}
.cta:hover{background:#131310;color:#FFD400}
.cta .ar{font-size:19px}
.faq{margin-top:40px;border-top:2px solid var(--line);padding-top:8px}
.faq h2{margin-top:20px}
.faq details{border-bottom:1px solid var(--line);padding:6px 0}
.faq summary{cursor:pointer;font-weight:700;font-size:17px;padding:10px 0;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";float:right;color:var(--accent);font-weight:900}
.faq details[open] summary::after{content:"\\2212"}
.faq .a{color:var(--muted);padding:0 0 12px}
.related{margin-top:44px;border-top:2px solid var(--line);padding-top:16px}
.related h2{font-size:18px;margin:8px 0 12px}
.related a{display:block;text-decoration:none;border:1.5px solid var(--line);border-radius:8px;padding:13px 15px;margin-bottom:9px;background:var(--surface)}
.related a:hover{background:var(--chip)}
.related .rt{font-weight:800;font-size:15.5px}
.related .rd{color:var(--muted);font-size:13px;margin-top:3px}
footer{margin-top:56px;border-top:1px solid var(--line);padding-top:18px;color:var(--faint);font-size:13px;line-height:1.9}
footer a{color:var(--muted);text-decoration:none;margin-right:16px;border-bottom:1px solid var(--line)}
footer a:hover{color:var(--accent)}
.hubgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;margin-top:20px}
.hubsec{font-family:Archivo;font-weight:900;font-size:20px;text-transform:uppercase;letter-spacing:.03em;margin:34px 0 0}
.hubsec span{font-size:13px;color:var(--faint);font-weight:700;margin-left:6px}
.hubjump{font-size:14px;font-weight:700;margin:6px 0 0}
.hubjump a{color:var(--ink)}
.hubcard{display:block;text-decoration:none;border:1.5px solid var(--line);border-radius:10px;padding:18px;background:var(--surface)}
.hubcard:hover{background:var(--chip)}
.hubcard .ht{font-family:Archivo;font-weight:800;font-size:18px;line-height:1.25}
.hubcard .hd{color:var(--muted);font-size:14px;margin-top:7px}
.hubcard .hl{font-size:10px;font-weight:800;letter-spacing:.06em;background:var(--chip);color:var(--muted);border-radius:999px;padding:3px 8px;display:inline-block;margin-top:10px}
h1.hubh{font-family:Archivo;font-weight:900;font-size:clamp(26px,5vw,38px);margin:26px 0 6px}
.hublead{color:var(--muted);font-size:16px;max-width:60ch}
"""

def esc(s): return htmlmod.escape(s, quote=True)

def top_bar(lang):
    jobs = "Jobs" if lang=="en" else "Jobs"
    return ('<div id="top"><div class="bar">'
            '<a class="wordmark" href="/"><span class="a">Berlin</span><span class="b">App Jobs</span></a>'
            '<div class="spacer"></div>'
            '<a class="nav" href="/guides/">Guides</a>'
            f'<a class="nav" href="/" style="margin-left:14px">{jobs} &rarr;</a>'
            '</div></div>')

def related_block(a):
    lang=a["lang"]
    others=[x for x in ALL if x["slug"]!=a["slug"]]
    same=[x for x in others if x["lang"]==lang]
    pref=[by_slug[s_] for s_ in a.get("related",[]) if s_ in by_slug and s_!=a["slug"]]
    seen_=set(); pick=[]
    for x in pref+same+others:
        if x["slug"] not in seen_: seen_.add(x["slug"]); pick.append(x)
    pick=pick[:4]
    head = "Related guides" if lang=="en" else "Weitere Guides"
    cards=""
    for x in pick:
        cards+=(f'<a href="/guides/{x["slug"]}/"><div class="rt">{esc(x["title"])}</div>'
                f'<div class="rd">{esc(x["desc"][:110])}</div></a>')
    return f'<div class="related"><h2>{head}</h2>{cards}</div>'

def footer_block(lang):
    label = "More guides" if lang=="en" else "Mehr Guides"
    links=""
    for x in ALL[:8]:
        links+=f'<a href="/guides/{x["slug"]}/">{esc(x["title"])}</a>'
    board = "Job board" if lang=="en" else "Jobboard"
    return (f'<footer><div style="margin-bottom:10px"><a href="/">{board}</a>'
            f'<a href="/guides/">{label}</a></div>{links}'
            '<div style="margin-top:14px">Berlin App Jobs, jobs at the companies behind Germany\'s top apps.</div></footer>')

def article_jsonld(a, url):
    g=[{
        "@context":"https://schema.org","@type":"Article",
        "headline":a["title"],"description":a["desc"],
        "datePublished":a.get("date",TODAY),"dateModified":TODAY,"inLanguage":a["lang"],
        "author":{"@type":"Organization","name":"Berlin App Jobs"},
        "publisher":{"@type":"Organization","name":"Berlin App Jobs"},
        "mainEntityOfPage":{"@type":"WebPage","@id":url}
    },{
        "@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
            {"@type":"ListItem","position":2,"name":"Guides","item":SITE+"/guides/"},
            {"@type":"ListItem","position":3,"name":a["title"],"item":url}
        ]
    }]
    if a.get("faq"):
        g.append({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
            {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":ans}}
            for q,ans in a["faq"]]})
    return '\n'.join('<script type="application/ld+json">'+json.dumps(x,ensure_ascii=False)+'</script>' for x in g)

def hreflang_tags(a, url):
    tags=[f'<link rel="alternate" hreflang="{a["lang"]}" href="{url}">']
    pair=a.get("hreflang")
    if pair and pair in by_slug:
        p=by_slug[pair]
        purl=f'{SITE}/guides/{p["slug"]}/'
        tags.append(f'<link rel="alternate" hreflang="{p["lang"]}" href="{purl}">')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{url}">')
    return '\n'.join(tags)

def render_article(a):
    url=f'{SITE}/guides/{a["slug"]}/'
    updated = ("Updated " if a["lang"]=="en" else "Aktualisiert ")+TODAY
    crumbhome = "Home" if a["lang"]=="en" else "Start"
    faq_html=""
    if a.get("faq"):
        head = "Frequently asked questions" if a["lang"]=="en" else "Häufige Fragen"
        items=""
        for q,ans in a["faq"]:
            items+=f'<details><summary>{esc(q)}</summary><div class="a">{esc(ans)}</div></details>'
        faq_html=f'<div class="faq"><h2>{head}</h2>{items}</div>'
    cta=(f'<a class="cta" href="{esc(a["ctaHref"])}">{esc(a["ctaLabel"])} <span class="ar">&rarr;</span></a>')
    doc=f"""<!doctype html>
<html lang="{a['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(a['metaTitle'])}</title>
<meta name="description" content="{esc(a['desc'])}">
<link rel="canonical" href="{url}">
{hreflang_tags(a,url)}
<meta property="og:type" content="article">
<meta property="og:site_name" content="Berlin App Jobs">
<meta property="og:title" content="{esc(a['title'])}">
<meta property="og:description" content="{esc(a['desc'])}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{FAV}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;800;900&display=swap">
<style>{CSS}</style>
{article_jsonld(a,url)}
</head>
<body>
{top_bar(a['lang'])}
<div class="wrap">
<nav class="crumb"><a href="/">{crumbhome}</a> / <a href="/guides/">Guides</a> / {esc(a['title'])}</nav>
<article>
<h1>{esc(a['title'])}</h1>
<div class="meta"><span class="langbadge">{a['lang'].upper()}</span><span>{updated}</span></div>
{a['html'].strip()}
{cta}
{faq_html}
</article>
{related_block(a)}
{footer_block(a['lang'])}
</div>
</body>
</html>"""
    return doc

# ---- write article pages ----
for a in ALL:
    d=os.path.join(GUIDES_DIR, a["slug"])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding='utf-8').write(render_article(a))

# ---- guides hub ----
def hub():
    cards=""
    for lang,head in (("en","English"),("de","Deutsch")):
        group=[a for a in ALL if a["lang"]==lang]
        cards+=f'<h2 class="hubsec" id="{lang}">{head} <span>{len(group)}</span></h2><div class="hubgrid">'
        for a in group:
            cards+=(f'<a class="hubcard" href="/guides/{a["slug"]}/" hreflang="{a["lang"]}">'
                    f'<div class="ht">{esc(a["title"])}</div>'
                    f'<div class="hd">{esc(a["desc"][:130])}</div>'
                    f'<span class="hl">{a["lang"].upper()}</span></a>')
        cards+='</div>\n' 
    url=f'{SITE}/guides/'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Guides: App Jobs in Germany | Berlin App Jobs</title>
<meta name="description" content="Practical guides to finding a job at the companies behind Germany's top apps: salaries, roles, cities, and how to get in. English and German.">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Berlin App Jobs">
<meta property="og:title" content="Guides: App Jobs in Germany"><meta property="og:url" content="{url}">
<link rel="icon" href="{FAV}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;700;800;900&display=swap">
<style>{CSS}</style>
</head>
<body>
{top_bar('en')}
<div class="wrap">
<nav class="crumb"><a href="/">Home</a> / Guides</nav>
<h1 class="hubh">Guides</h1>
<p class="hublead">Practical guides to working at the companies behind Germany's top apps: what roles pay, who is hiring, which cities, and how to get in. New guides added regularly.</p>
<p class="hubjump"><a href="#en">English</a> &middot; <a href="#de">Deutsch</a></p>
{cards}
{footer_block('en')}
</div>
</body>
</html>"""
open(os.path.join(GUIDES_DIR,"index.html"),"w",encoding='utf-8').write(hub())

# ---- sitemap.xml ----
urls=[(SITE+"/","1.0"),(SITE+"/guides/","0.8")]
for a in ALL: urls.append((f'{SITE}/guides/{a["slug"]}/',"0.7"))
sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u,p in urls:
    sm+=f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{p}</priority></url>\n'
sm+='</urlset>\n'
open(os.path.join(OUT,"sitemap.xml"),"w",encoding='utf-8').write(sm)

# ---- robots.txt ----
open(os.path.join(OUT,"robots.txt"),"w",encoding='utf-8').write(
    "User-agent: *\nAllow: /\nDisallow: /_build/\n\nSitemap: %s/sitemap.xml\nSitemap: %s/sitemap-jobs.xml\n" % (SITE, SITE))

# ---- regenerate guides_data.js (in-app tab): all 12, html + appended FAQ ----
def inapp_html(a):
    h=a["html"].strip()
    if a.get("faq"):
        head = "Häufige Fragen" if a["lang"]=="de" else "FAQ"
        h+=f'\n<h2>{head}</h2>\n'
        for q,ans in a["faq"]:
            h+=f'<p class="faq-q">{esc(q)}</p><p>{esc(ans)}</p>\n'
    return h
guides_out=[{"slug":a["slug"],"lang":a["lang"],"title":a["title"],"desc":a["desc"],"pair":a.get("hreflang"),"html":inapp_html(a)} for a in ALL]
open(os.path.join(DATA,'guides_data.js'),'w',encoding='utf-8').write(
    "const GUIDES = "+json.dumps(guides_out,ensure_ascii=False)+";\n")

print("articles total:",len(ALL)); print("missing company links:",sorted(set(_missing)))
print("guide pages written to",GUIDES_DIR)
print("sitemap urls:",len(urls))
print("guides_data.js entries:",len(guides_out))
