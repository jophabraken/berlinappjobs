# -*- coding: utf-8 -*-
# One page per job with valid JobPosting markup (Google for Jobs).
# Only jobs whose full description we have from the hiring system's feed (descriptions.json)
# and that are still live in that feed. Writes /job/<slug>/ pages, sitemap-jobs.xml and
# /tmp/berlin/jobpages_map.json (ATS url -> our job page URL) for internal links.
import json, os, re, hashlib, datetime, shutil, html
import bleach

SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'build_programmatic.py'), encoding='utf-8').read()
exec(SRC[:SRC.index('def jsonld(objs):')])   # CSS, head(), FOOT, esc(), slugify(), B, COS, SITE, OUT, FAV
exec(SRC[SRC.index('def jsonld(objs):'):SRC.index('def jobposting_list')])  # jsonld(), breadcrumb()

D = json.load(__import__('gzip').open(os.path.join(DATA,'descriptions.json.gz'), 'rt', encoding='utf-8'))
FETCHED = D['fetched'][:10]
VALID_THROUGH = (datetime.date.fromisoformat(FETCHED) + datetime.timedelta(days=30)).isoformat()
idx = {}
for j in D['jobs']:
    for k in filter(None, [j.get('url'), str(j.get('id') or '')]):
        idx.setdefault(k.split('?')[0].rstrip('/'), j)

def match(u):
    m = idx.get(u.split('?')[0].rstrip('/'))
    if m: return m
    for i in reversed(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\d{6,}', u)):
        if i in idx: return idx[i]
    return None

TAGS = ['p', 'br', 'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'h2', 'h3', 'h4', 'a', 'blockquote']
def sanitize(h):
    h = re.sub(r'<h1[^>]*>', '<h3>', h, flags=re.I).replace('</h1>', '</h3>')
    h = re.sub(r'<(div|section|span|font)[^>]*>|</(div|section|span|font)>', lambda m: '' if m.group(0).lower().startswith(('<span', '</span', '<font', '</font')) else ('<p>' if not m.group(0).startswith('</') else '</p>'), h, flags=re.I)
    h = bleach.clean(h, tags=TAGS, attributes={'a': ['href']}, strip=True)
    h = re.sub(r'<a href=', '<a rel="nofollow noopener" target="_blank" href=', h)
    h = re.sub(r'(<p>\s*(&nbsp;|\s)*</p>\s*)+', '', h)
    h = re.sub(r'(<br\s*/?>\s*){3,}', '<br><br>', h)
    return h.strip()

def text_len(h): return len(re.sub(r'<[^>]+>', '', h))

def emp_type(j, jb):
    s = ' '.join(str(x or '') for x in (j.get('et'), j.get('sched'), jb.get('t'))).lower()
    out = []
    if re.search(r'werkstud|working student', s): out = ['PART_TIME', 'INTERN']
    elif re.search(r'intern|praktik|trainee|internship', s): out = ['INTERN']
    elif re.search(r'part.?time|teilzeit|parttime|minijob', s): out = ['PART_TIME']
    elif re.search(r'freelanc|freiberuf|contractor', s): out = ['CONTRACTOR']
    elif re.search(r'temporary|befristet|fixed.?term|temp', s): out = ['TEMPORARY']
    else: out = ['FULL_TIME']
    return out

def salary(sal):
    if not sal or not re.search(r'\d', sal): return None
    unit = 'HOUR' if '/h' in sal else 'MONTH' if 'Monat' in sal or '/month' in sal.lower() else 'YEAR'
    nums = []
    for m in re.finditer(r'(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*([kK])?', sal.split('•')[0]):
        t = m.group(1)
        v = float(re.sub(r'[.,]', '', t)) if re.fullmatch(r'\d{1,3}(?:[.,]\d{3})+', t) else float(t.replace(',', '.'))
        if m.group(2): v *= 1000
        nums.append(v)
    nums = [n for n in nums if n > 0]
    if not nums: return None
    val = {"@type": "QuantitativeValue", "unitText": unit}
    if len(nums) >= 2 and max(nums) != min(nums): val.update(minValue=min(nums), maxValue=max(nums))
    else: val.update(value=nums[0])
    return {"@type": "MonetaryAmount", "currency": "EUR", "value": val}

def is_de(h):
    t = ' ' + re.sub(r'<[^>]+>', ' ', h).lower() + ' '
    return sum(t.count(w) for w in (' und ', ' die ', ' der ', ' wir ', ' mit ', ' für ')) > sum(t.count(w) for w in (' and ', ' the ', ' we ', ' with ', ' for ', ' you '))

def iso(d):
    if not d: return None
    d = str(d)
    return d[:10] if re.match(r'\d{4}-\d{2}-\d{2}', d) else None

def co_slug(name):
    sl = slugify(name)
    return sl if os.path.isdir(os.path.join(OUT, 'companies', sl)) else None

JOB_DIR = os.path.join(OUT, 'job')
shutil.rmtree(JOB_DIR, ignore_errors=True)   # local build dir only; the repo copy is handled at deploy time
os.makedirs(JOB_DIR, exist_ok=True)

EXPIRE_JS = ("<script>(function(){var v='" + VALID_THROUGH + "';if(new Date()>new Date(v+'T23:59:59')){var b=document.getElementById('expired');if(b)b.hidden=false;var a=document.querySelectorAll('.applybtn');for(var i=0;i<a.length;i++)a[i].style.display='none';}})();</script>")
EXTRA_CSS = """<style>
.jd{background:var(--surface);border:1.5px solid var(--line);border-radius:10px;padding:18px 20px;margin-top:14px;font-size:15.5px;line-height:1.65;overflow-wrap:anywhere}
.jd h2,.jd h3,.jd h4{font-family:Archivo;font-weight:800;font-size:17px;margin:20px 0 6px}
.jd ul{padding-left:20px}.jd p{margin:0 0 12px}
.expired{background:#FFE9E3;color:#7A1F0C;border:1.5px solid #7A1F0C;border-radius:8px;padding:12px 14px;margin:10px 0;font-weight:700}
.note{color:var(--faint);font-size:12.5px;margin-top:10px}
</style>"""

pages = []; mapping = {}; per_co = {}
seen_slugs = set()
for c in COS:
    for jb in c.get('jobs') or []:
        m = match(jb['u'])
        if not m or not m.get('desc'): continue
        desc = sanitize(m['desc'])
        if text_len(desc) < 300: continue
        cs = slugify(c['n'])
        h = hashlib.md5(jb['u'].encode()).hexdigest()[:6]
        slug = f"{cs}-{slugify(jb['t'])[:60].strip('-')}-{h}"
        if slug in seen_slugs: continue
        seen_slugs.add(slug)
        rec = dict(c=c, jb=jb, m=m, desc=desc, slug=slug)
        pages.append(rec); per_co.setdefault(c['n'], []).append(rec)
        mapping[jb['u']] = f"/job/{slug}/"

import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGION
# Feed values can be strings: descriptions.json stores rem as "True"/"False", and bool("False") is True.
def truthy(v): return v is True or str(v).strip().lower() in ('true', '1', 'yes')
CITY_ALIAS = {'munich': 'München', 'muenchen': 'München', 'cologne': 'Köln', 'koeln': 'Köln', 'nuremberg': 'Nürnberg',
              'frankfurt': 'Frankfurt am Main', 'hanover': 'Hannover', 'duesseldorf': 'Düsseldorf', 'esslingen': 'Esslingen am Neckar',
              'immenstadt': 'Immenstadt i. Allgäu', 'freiburg': 'Freiburg im Breisgau'}
_KNOWN = sorted(REGION, key=len, reverse=True)
def job_cities(loc, fallback):
    """The job's own city/cities from the feed location ('Berlin / Hamburg', 'Office Frankfurt/Hybrid', 'Munich').
    Only known German cities (regions.py) are used, never a guess; otherwise the company city, as before."""
    out = []
    for p in re.split(r'[/,|]', loc or ''):
        p = re.sub(r'\(.*?\)|\b(office|hybrid|remote|home.?office)\b', ' ', p, flags=re.I)
        p = re.sub(r'\s+', ' ', p).strip(' -')
        p = CITY_ALIAS.get(p.lower(), p)
        if p in REGION and p not in out: out.append(p)
    if not out:   # city only in brackets, e.g. 'Green Campus (Kiel)'
        out = [k for k in _KNOWN if re.search(r'\(' + re.escape(k) + r'\)', loc or '')][:1]
    return out or [fallback]
def postal_address(c, city):
    """PostalAddress for the company's office in `city`. Street and postcode only when the company's
    registered address is in that same city (never guessed); state from the city."""
    a = {"@type": "PostalAddress", "addressLocality": city}
    addr = c.get('addr') or ''
    if addr and city in addr:
        street = re.split(r',|\s\d{5}\s', addr)[0].strip()
        if street and street != city: a["streetAddress"] = street
        m = re.search(r'\b(\d{5})\b', addr)
        if m: a["postalCode"] = m.group(1)
    if city in REGION: a["addressRegion"] = REGION[city]
    a["addressCountry"] = "DE"
    return a

# Title and meta description: short and made of the job's facts. Gender tags like "(m/w/d)" are dropped from the
# <title> only (the page H1 and JobPosting keep the full title), and legal suffixes from the company name.
GENDER = re.compile(r'\s*[(\[]\s*(?:(?:[mwfdxi]|div|gn\*?|all\s+genders?|alle\s+geschlechter)\s*[/|,*.]?\s*)+[)\]]', re.I)
LEGAL = re.compile(r'\s+(?:GmbH\s*&\s*Co\.?\s*KG(?:aA)?|GmbH|AG|SE|KG|KGaA|UG|mbH|e\.\s?V\.|Ltd\.?|Inc\.?|B\.V\.|S\.A\.)(?=\s|$|,).*$')
def short_title(t):
    t = re.sub(r'\s+', ' ', GENDER.sub('', t or '')).strip(' -–|,')
    return t or re.sub(r'\s+', ' ', t).strip()
def short_co(n):
    return LEGAL.sub('', n).strip() or n
ET_LABEL = {"FULL_TIME": ("Vollzeit", "Full-time"), "PART_TIME": ("Teilzeit", "Part-time"), "INTERN": ("Praktikum", "Internship"),
            "CONTRACTOR": ("Freelance", "Freelance"), "TEMPORARY": ("Befristet", "Temporary")}
def contract_label(et, jt, k):
    if re.search(r'ausbildung|azubi|apprentice', jt, re.I): return ("Ausbildung", "Apprenticeship")[k]
    if 'PART_TIME' in et and 'INTERN' in et: return ("Werkstudent", "Working student")[k]
    return ET_LABEL[et[-1]][k]
def job_desc(jt, co, where, de, et, remote, sal, desc_html):
    """~155 chars, unique per job: company, place, role, contract, remote, salary, then the ad's own opening words."""
    k = 0 if de else 1
    facts = [contract_label(et, jt, k)]
    if remote: facts.append("remote/hybrid möglich" if de else "remote/hybrid possible")
    if sal: facts.append(("Gehalt " if de else "salary ") + sal.split('•')[0].strip())
    s = f"{co}, {where}: {jt}. ".replace(', Remote:', ' (Remote):') + ', '.join(facts) + '. '
    body = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', desc_html)).replace('\xa0', ' ')).strip()
    s += body
    if len(s) > 158:
        s = s[:158].rsplit(' ', 1)[0].rstrip(' ,.;:-–(') + '…'
    return s

for rec in pages:
    c, jb, m, desc, slug = rec['c'], rec['jb'], rec['m'], rec['desc'], rec['slug']
    url = f"{SITE}/job/{slug}/"
    city = c.get('city') or 'Berlin'
    loc = jb.get('loc') or m.get('loc') or city
    cities = job_cities(loc, city)
    remote = truthy(jb.get('rem')) or truthy(m.get('rem')) or bool(re.search(r'remote|home.?office', f"{jb['t']} {loc}", re.I))
    de = is_de(desc)
    posted = iso(m.get('pub')) or iso(m.get('upd')) or iso(jb.get('p')) or FETCHED
    et = emp_type(m, jb)
    cname = c['n'].split('|')[0].strip()
    cslug = co_slug(c['n'])
    jp = {
        "@context": "https://schema.org", "@type": "JobPosting",
        "title": jb['t'], "description": desc,
        "datePosted": posted, "validThrough": VALID_THROUGH + "T23:59:59+02:00",
        "employmentType": et if len(et) > 1 else et[0],
        "hiringOrganization": {"@type": "Organization", "name": cname, **({"sameAs": c['careers']} if c.get('careers') else {})},
        "jobLocation": [{"@type": "Place", "address": postal_address(c, x)} for x in cities] if len(cities) > 1 else {"@type": "Place", "address": postal_address(c, cities[0])},
        "directApply": False,
        "identifier": {"@type": "PropertyValue", "name": cname, "value": str(m.get('id') or slug)},
        "url": url,
    }
    if remote:
        jp["jobLocationType"] = "TELECOMMUTE"
        jp["applicantLocationRequirements"] = {"@type": "Country", "name": "DE"}
    sal = salary(jb.get('sal'))
    if sal: jp["baseSalary"] = sal
    L = (lambda de_, en_: de_ if de else en_)
    others = [r for r in per_co.get(c['n'], []) if r is not rec][:6]
    other_html = ''
    if others:
        other_html = f"<h2>{L('Weitere Stellen bei', 'More jobs at')} {esc(cname)}</h2>" + ''.join(
            f'<a class="row" href="/job/{r["slug"]}/"><div class="m"><div class="t">{esc(r["jb"]["t"])}</div>'
            f'<div class="d">{esc(r["jb"].get("loc") or city)}</div></div><span class="apply">{L("Ansehen", "View")}</span></a>' for r in others)
    where = loc.strip() if (loc or '').strip().lower() in ('remote', 'deutschland') else ' / '.join(cities)
    jt = short_title(jb['t'])
    co = short_co(cname)
    at = '' if co.lower() in jt.lower() else (f" bei {co}" if de else f" at {co}")   # "... beim 1. FC Köln" already names it
    title_tag = f"{jt}{at} in {where}".replace(' in Remote', ' (Remote)')
    full_title = title_tag + " | Berlin App Jobs" if len(title_tag) <= 62 else title_tag   # Google cuts titles at ~60 chars
    meta_desc = job_desc(jt, co, where, de, et, remote, jb.get('sal'), desc)
    crumbs = breadcrumb([("Start" if de else "Home", SITE + "/"), (cname, f"{SITE}/companies/{cslug}/" if cslug else SITE + "/"), (jb['t'], url)])
    pills = [esc(loc)] + (["Remote"] if remote else []) + [{"FULL_TIME": L("Vollzeit", "Full-time"), "PART_TIME": L("Teilzeit", "Part-time"), "INTERN": L("Praktikum", "Internship"), "CONTRACTOR": "Freelance", "TEMPORARY": L("Befristet", "Temporary")}[et[-1]]]
    if jb.get('sal'): pills.append(esc(jb['sal'].split('•')[0].strip()))
    body = (head(full_title, meta_desc, url, EXTRA_CSS + "\n" + jsonld([jp, crumbs])).replace('<html lang="de">', f'<html lang="{"de" if de else "en"}">')
      + f'<nav class="crumb"><a href="/">{L("Start", "Home")}</a> / '
      + (f'<a href="/companies/{cslug}/">{esc(cname)}</a>' if cslug else esc(cname)) + f' / {esc(jb["t"])}</nav>'
      + f'<h1>{esc(jb["t"])}</h1>'
      + f'<div class="meta"><b>{esc(cname)}</b>' + ''.join(f'<span class="pill">{p}</span>' for p in pills) + f'<span>{L("Veröffentlicht", "Posted")} {posted}</span></div>'
      + f'<div id="expired" class="expired" hidden>{L("Diese Anzeige ist möglicherweise nicht mehr aktuell. Prüfe die Stelle auf der Karriereseite des Unternehmens.", "This posting may no longer be open. Check the role on the company careers page.")}</div>'
      + f'<a class="cta applybtn" href="{esc(jb["u"])}" target="_blank" rel="noopener nofollow">{L("Jetzt beim Unternehmen bewerben", "Apply on the company site")} &#8599;</a>'
      + f'<div class="jd">{desc}</div>'
      + f'<a class="cta applybtn" href="{esc(jb["u"])}" target="_blank" rel="noopener nofollow" style="margin-top:16px">{L("Jetzt beim Unternehmen bewerben", "Apply on the company site")} &#8599;</a>'
      + f'<p class="note">{L("Quelle: Bewerbungssystem von", "Source: hiring system of")} {esc(cname)}, {L("zuletzt geprüft am", "last checked")} {FETCHED}. {L("Du bewirbst dich direkt beim Unternehmen.", "You apply directly with the company.")}</p>'
      + other_html
      + (f'<p style="margin-top:22px"><a href="/companies/{cslug}/">{L("Alle Infos und Apps von", "All info and apps from")} {esc(cname)} &rarr;</a> &middot; ' if cslug else '<p style="margin-top:22px">')
      + f'<a href="/">{L("Alle Stellen auf dem Board", "All jobs on the board")} &rarr;</a></p>'
      + '</div>' + (FOOT if de else FOOT_EN) + EXPIRE_JS + '</body></html>')
    d = os.path.join(JOB_DIR, slug); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(body)

json.dump(mapping, open(os.path.join(DATA,'jobpages_map.json'), 'w'), ensure_ascii=False)
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for rec in pages:
    sm += f'  <url><loc>{SITE}/job/{rec["slug"]}/</loc><lastmod>{FETCHED}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>\n'
sm += '</urlset>\n'
open(os.path.join(OUT, 'sitemap-jobs.xml'), 'w', encoding='utf-8').write(sm)
print('job pages:', len(pages), 'companies:', len(per_co), 'validThrough', VALID_THROUGH)
