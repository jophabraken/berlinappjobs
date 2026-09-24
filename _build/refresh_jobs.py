# -*- coding: utf-8 -*-
"""Weekly job refresh. Re-fetches every company whose hiring system has a public API and
updates _build/data/board_data.js (the board) and _build/data/descriptions.json.gz (job pages).

What it does
  * Greenhouse, Lever, Ashby, Personio (XML), SmartRecruiters, Recruitee, softgarden: fetch live jobs,
    keep German locations (plus remote), drop placeholder ads, cap 60 per company.
  * Jobs we already had keep their labels (discipline, seniority, language); new jobs get labels
    from classify.py. Closed jobs disappear.
  * Companies without an API (custom career pages): their jobs stay, but links that now return
    404/410 are removed.
  * Published salaries from the APIs (Ashby, Lever, Recruitee, Personio) are added.

Safety rails (nothing is written if a hard check fails, exit code 1)
  * More than 30% of API companies fail to fetch -> abort.
  * Total job count drops by more than 30% -> abort.
  * A company that fetched fine but suddenly has 0 German jobs (had >= 5) keeps its old jobs.
  * Ashby boards never shrink by more than half in one run.
  * A company whose fetch fails keeps its old jobs and descriptions.

Usage: python3 _build/refresh_jobs.py [--dry-run]
Writes a summary to _build/refresh_report.md either way.
"""
import concurrent.futures as cf, datetime, gzip, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA, BUILD
from classify import discipline, seniority, language
from regions import REGION

DRY = '--dry-run' in sys.argv
UA = 'Mozilla/5.0 (compatible; BerlinAppJobsBot/1.0; +https://berlinappjobs.com)'
CAP = 60
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = NOW.date()

# ---------------------------------------------------------------- http
TRIES = int(os.environ.get('BAJ_TRIES', '3'))
def fetch(url, data=None, headers=None, timeout=40, tries=None):
    tries = tries or TRIES
    h = {'User-Agent': UA, 'Accept': 'application/json, text/xml, */*'}
    h.update(headers or {})
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404, 410): raise
            last = e
        except Exception as e:
            last = e
        time.sleep(2 * (k + 1))
    raise last
def jfetch(url, **kw): return json.loads(fetch(url, **kw).decode('utf-8'))

# ---------------------------------------------------------------- helpers
def txt(h): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(h or ''))).strip()
def iso_date(s):
    if not s: return ''
    if isinstance(s, (int, float)): return datetime.datetime.fromtimestamp(s / 1000, datetime.timezone.utc).date().isoformat()
    m = re.match(r'(\d{4}-\d{2}-\d{2})', str(s)); return m.group(1) if m else ''
def kfmt(v): return f'€{round(v / 1000)}K'
def sal_str(lo, hi, period='year', cur='EUR'):
    try: lo = float(lo or 0); hi = float(hi or 0)
    except Exception: return ''
    if cur not in ('EUR', '€') or not (lo or hi): return ''
    p = (period or 'year').lower()
    if p.startswith(('year', 'annual', '1 year')) or p in ('yearly', 'per-year-salary'):
        if max(lo, hi) < 15000: return ''
        return f'{kfmt(lo)} – {kfmt(hi)}' if lo and hi and lo != hi else kfmt(lo or hi)
    if p.startswith('month'):
        return f'€{lo:,.0f} – €{hi:,.0f} /Monat'.replace(',', '.') if lo and hi and lo != hi else f'€{(lo or hi):,.0f} /Monat'.replace(',', '.')
    if p.startswith('hour'):
        return f'€{lo:g} – €{hi:g} /h' if lo and hi and lo != hi else f'€{(lo or hi):g} /h'
    return ''

PLACEHOLDER = re.compile(r'initiativbewerbung|initiative application|open application|unsolicited|talent ?pool|talentpool|general application|spontan|blindbewerbung|kein job, der zu dir passt|dein job ist nicht dabei|nicht das passende dabei|future opportunities|speculative', re.I)
EN_CITY = {'munich': 'München', 'cologne': 'Köln', 'nuremberg': 'Nürnberg', 'frankfurt': 'Frankfurt am Main', 'hanover': 'Hannover',
           'dusseldorf': 'Düsseldorf', 'duesseldorf': 'Düsseldorf', 'muenster': 'Münster', 'wurzburg': 'Würzburg', 'brunswick': 'Braunschweig'}
FOREIGN = re.compile(r'\b(united states|usa|us|americas|apac|latam|u\.s\.|uk\b|united kingdom|london|dublin|ireland|paris|france|madrid|barcelona|spain|lisbon|portugal|milan|milano|rome|italy|amsterdam|netherlands|rotterdam|brussels|belgium|vienna|wien|austria|zurich|zürich|switzerland|warsaw|poland|krakow|prague|czech|budapest|stockholm|sweden|copenhagen|denmark|oslo|norway|helsinki|finland|tallinn|estonia|riga|vilnius|lithuania|bratislava|slovakia|sofia|bucharest|romania|athens|greece|istanbul|turkey|tel aviv|israel|dubai|singapore|tokyo|japan|seoul|korea|beijing|shanghai|china|india|bangalore|toronto|canada|new york|san francisco|austin|texas|california|sydney|australia|mexico|brazil|são paulo|sao paulo|cairo|lagos|nairobi|luxembourg|vietnam|manila)\b', re.I)

def load_board():
    s = open(os.path.join(DATA, 'board_data.js'), encoding='utf-8').read()
    i = s.find('const BOARD = '); j = s.find('const CHARTS', i)
    return s, i, j, json.loads(s[i + len('const BOARD = '):j].rstrip().rstrip(';').rstrip())

SRC, I0, J0, B = load_board()
GERMAN = set(REGION) | {'Dresden', 'Potsdam', 'Darmstadt', 'Wiesbaden', 'Mainz', 'Dortmund', 'Duisburg', 'Wuppertal', 'Bielefeld', 'Rostock', 'Lübeck',
                        'Regensburg', 'Göttingen', 'Paderborn', 'Osnabrück', 'Kaiserslautern', 'Saarbrücken', 'Chemnitz', 'Halle', 'Erlangen', 'Fürth',
                        'Konstanz', 'Tübingen', 'Esslingen', 'Ludwigsburg', 'Böblingen', 'Sindelfingen', 'Pforzheim', 'Reutlingen', 'Gütersloh', 'Hamm',
                        'Leverkusen', 'Neuss', 'Mönchengladbach', 'Oberhausen', 'Herne', 'Hagen', 'Bottrop', 'Recklinghausen', 'Ratingen', 'Eschborn',
                        'Offenbach', 'Hanau', 'Bad Homburg', 'Neu-Isenburg', 'Unterföhring', 'Garching', 'Eching', 'Hallbergmoos', 'Frankfurt'}
for c in B['companies']:
    for jb in c.get('jobs') or []:
        if jb.get('loc') and len(jb['loc']) < 30 and not re.search(r'remote|/|\(|,', jb['loc'], re.I): GERMAN.add(jb['loc'])
GERMAN_RX = re.compile(r'\b(' + '|'.join(sorted((re.escape(g) for g in GERMAN), key=len, reverse=True)) + r')\b', re.I)

def german_loc(locs, country='', remote=False):
    """Return (normalized location, remote flag) if the job is in Germany (or remote for Germany/Europe), else None."""
    locs = [l for l in locs if l]
    joined = ' | '.join(locs)
    low = joined.lower()
    for en, de in EN_CITY.items():
        low = re.sub(r'\b' + en + r'\b', de.lower(), low)
    m = GERMAN_RX.search(low)
    is_rem = remote or bool(re.search(r'remote|home.?office|homeoffice|bundesweit|deutschlandweit|mobiles arbeiten', low))
    de_country = (country or '').lower() in ('de', 'deu', 'germany', 'deutschland') or bool(re.search(r'germany|deutschland|,\s*de\b|\(de\)|\bdach\b', low))
    if m:
        name = next((g for g in GERMAN if g.lower() == m.group(1).lower()), m.group(1))
        return name, is_rem
    if de_country:
        return ('Remote' if is_rem else 'Deutschland'), is_rem
    if is_rem and not FOREIGN.search(low) and (not low.strip() or re.search(r'remote|europe|emea|cet', low)):
        return 'Remote', True
    return None

# ---------------------------------------------------------------- fetchers -> list of raw jobs
# raw job: dict(id, url, t, locs[list], country, remote, desc(html), pub, et, sal, dept, sen_hint)
def f_greenhouse(feed):
    base = feed.split('?')[0]
    d = jfetch(base + '?content=true')
    out = []
    for x in d.get('jobs', []):
        locs = [(x.get('location') or {}).get('name', '')] + [o.get('name', '') for o in x.get('offices') or []]
        out.append(dict(id=str(x['id']), url=x.get('absolute_url'), t=x.get('title', ''), locs=locs, desc=html.unescape(x.get('content') or ''),
                        pub=x.get('first_published') or x.get('updated_at'), et='', sal='', dept=' '.join(dd.get('name', '') for dd in x.get('departments') or [])))
    return out

def f_lever(feed):
    d = jfetch(feed if 'mode=json' in feed else feed.rstrip('/') + '?mode=json')
    out = []
    for x in d:
        cat = x.get('categories') or {}
        locs = [cat.get('location', '')] + list(cat.get('allLocations') or [])
        desc = (x.get('description') or '') + ''.join(f"<h3>{l.get('text', '')}</h3><ul>{l.get('content', '')}</ul>" for l in x.get('lists') or []) + (x.get('additional') or '')
        sr = x.get('salaryRange') or {}
        out.append(dict(id=x['id'], url=x.get('hostedUrl'), t=x.get('text', ''), locs=locs, country=x.get('country', ''), remote=(x.get('workplaceType') == 'remote'),
                        desc=desc, pub=x.get('createdAt'), et=cat.get('commitment', ''), sal=sal_str(sr.get('min'), sr.get('max'), sr.get('interval', 'year'), sr.get('currency', '')),
                        dept=cat.get('team', '') + ' ' + cat.get('department', '')))
    return out

def f_ashby(feed):
    board = feed.rstrip('/').split('/')[-1] if '/' in feed else feed
    d = jfetch(f'https://api.ashbyhq.com/posting-api/job-board/{board}?includeCompensation=true')
    out = []
    for x in d.get('jobs', []):
        if x.get('isListed') is False: continue
        locs = [x.get('location', '')] + [s.get('location', '') for s in x.get('secondaryLocations') or []]
        sal = ''
        comp = x.get('compensation') or {}
        tiers = comp.get('compensationTiers') or []
        pick = [t for t in tiers if re.search(r'german|deutschland|dach|western|northern|europe|berlin', (t.get('title') or ''), re.I)] or (tiers if len(tiers) == 1 else [])
        comps = [k for t in pick for k in t.get('components') or []] or (comp.get('summaryComponents') or [] if not tiers else [])
        for k in comps:
            if k.get('compensationType') == 'Salary' and k.get('currencyCode') == 'EUR':
                sal = sal_str(k.get('minValue'), k.get('maxValue'), 'year' if '1 YEAR' in (k.get('interval') or '') else (k.get('interval') or '')); break
        out.append(dict(id=x['id'], url=x.get('jobUrl'), t=x.get('title', ''), locs=locs, remote=bool(x.get('isRemote')) or x.get('workplaceType') == 'Remote',
                        desc=x.get('descriptionHtml') or '', pub=x.get('publishedAt'), et=x.get('employmentType', ''), sal=sal, dept=x.get('department', '') + ' ' + x.get('team', '')))
    return out

def f_personio(feed):
    base = re.sub(r'/(search\.json|xml.*)$', '', feed.rstrip('/'))
    bases = [base] + ([base.replace('.personio.com', '.personio.de')] if '.personio.com' in base else [])
    last = None
    for b in bases:
        try:
            root = ET.fromstring(fetch(b + '/xml?language=de'))
            break
        except Exception as e:
            last = e
    else:
        raise last
    out = []
    for p in root.findall('position'):
        g = lambda k: (p.findtext(k) or '').strip()
        offices = [g('office')] + [o.text or '' for o in p.findall('additionalOffices/office')]
        desc = ''.join(f"<h3>{html.escape((jd.findtext('name') or '').strip())}</h3>{(jd.findtext('value') or '').strip()}" for jd in p.findall('jobDescriptions/jobDescription'))
        si = p.find('salaryInformation'); sal = ''
        if si is not None:
            sal = sal_str(si.findtext('min'), si.findtext('max'), {'yearly': 'year', 'monthly': 'month', 'hourly': 'hour'}.get((si.findtext('type') or '').strip(), ''), (si.findtext('currencyCode') or '').strip())
        out.append(dict(id=g('id'), url=f"{b}/job/{g('id')}", t=g('name'), locs=offices, desc=desc, pub=g('createdAt'), et=g('employmentType'),
                        sal=sal, dept=g('department'), sen_hint=g('seniority'), country='de' if any(o in GERMAN for o in offices) else ''))
    return out

def f_smartrecruiters(feed):
    m = re.search(r'companies/([^/]+)/postings', feed) or re.search(r'smartrecruiters\.com/([^/?]+)', feed)
    co = m.group(1)
    items, off = [], 0
    while True:
        d = jfetch(f'https://api.smartrecruiters.com/v1/companies/{co}/postings?limit=100&offset={off}')
        items += d.get('content', [])
        off += 100
        if off >= d.get('totalFound', 0) or off > 1500: break
    out = []
    de_items = [x for x in items if (x.get('location') or {}).get('country', '').lower() == 'de']
    de_items.sort(key=lambda x: x.get('releasedDate') or '', reverse=True)
    def detail(x):
        try:
            dd = jfetch(f"https://api.smartrecruiters.com/v1/companies/{co}/postings/{x['id']}")
            secs = (dd.get('jobAd') or {}).get('sections') or {}
            desc = ''.join(f"<h3>{s.get('title', '')}</h3>{s.get('text', '')}" for s in secs.values() if isinstance(s, dict))
            url = dd.get('postingUrl')
        except Exception:
            desc, url = '', f"https://jobs.smartrecruiters.com/{co}/{x['id']}"
        loc = x.get('location') or {}
        return dict(id=str(x['id']), url=url, t=x.get('name', ''), locs=[loc.get('city', ''), loc.get('fullLocation', '')], country=loc.get('country', ''),
                    remote=bool(loc.get('remote')), desc=desc, pub=x.get('releasedDate'), et=(x.get('typeOfEmployment') or {}).get('label', ''), sal='',
                    dept=(x.get('department') or {}).get('label', '') + ' ' + (x.get('function') or {}).get('label', ''), sen_hint=(x.get('experienceLevel') or {}).get('id', ''))
    with cf.ThreadPoolExecutor(8) as ex:
        out = list(ex.map(detail, de_items[:CAP * 2]))
    return out

def f_recruitee(feed):
    d = jfetch(feed)
    out = []
    for x in d.get('offers', []):
        s = x.get('salary') or {}
        out.append(dict(id=str(x['id']), url=x.get('careers_url'), t=x.get('title', ''), locs=[x.get('location', ''), x.get('city', '')], country=x.get('country_code', ''),
                        remote=bool(x.get('remote')), desc=(x.get('description') or '') + (x.get('requirements') or ''), pub=x.get('published_at') or x.get('created_at'),
                        et=x.get('employment_type_code', ''), sal=sal_str(s.get('min'), s.get('max'), s.get('period', ''), s.get('currency', '')),
                        dept=x.get('department', '') or '', sen_hint=x.get('experience_code', '')))
    return out

def f_softgarden(feed):
    url = feed if feed.endswith('.json') else feed.rstrip('/') + '/jobs.feed.json'
    d = jfetch(url)
    out = []
    for e in d.get('dataFeedElement', []):
        x = e.get('item') or e
        a = ((x.get('jobLocation') or {}).get('address') or {})
        out.append(dict(id=str((x.get('identifier') or {}).get('value', '')), url=x.get('url'), t=x.get('title', ''), locs=[a.get('addressLocality', '')],
                        country=a.get('addressCountry', ''), desc=x.get('description', ''), pub=x.get('datePosted'), et=x.get('employmentType', ''), sal=''))
    return out

FETCHERS = {'greenhouse': f_greenhouse, 'lever': f_lever, 'ashby': f_ashby, 'personio': f_personio, 'smartrecruiters': f_smartrecruiters,
            'recruitee': f_recruitee, 'softgarden': f_softgarden}

def ats_of(c):
    a = (c.get('ats') or '').lower().split()[0] if c.get('ats') else ''
    return a if a in FETCHERS and c.get('feed') and c['feed'].startswith(('http', 'yazio')) else ''

# ---------------------------------------------------------------- run
D = json.load(gzip.open(os.path.join(DATA, 'descriptions.json.gz'), 'rt', encoding='utf-8'))
DESC_BY_URL = {x['url'].split('?')[0].rstrip('/'): x for x in D['jobs'] if x.get('url')}
def key_ids(u):
    u = u or ''
    return {u.split('?')[0].rstrip('/')} | set(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\d{6,}', u))

feeds = {}
for c in B['companies']:
    if c.get('tier') == 1 and ats_of(c):
        feeds.setdefault((ats_of(c), c['feed'] if c['feed'] != 'yazio' else 'yazio'), []).append(c)

results, errors = {}, {}
def run(key):
    ats, feed = key
    return key, FETCHERS[ats](feed)
with cf.ThreadPoolExecutor(10) as ex:
    futs = {ex.submit(run, k): k for k in feeds}
    for f in cf.as_completed(futs):
        try:
            k, jobs = f.result(); results[k] = jobs
        except Exception as e:
            errors[futs[f]] = f'{type(e).__name__}: {str(e)[:120]}'

report = []
before_total = sum(len(c.get('jobs') or []) for c in B['companies'])
new_desc, stats = [], dict(kept_failed=0, new=0, closed=0, updated=0, suspicious=0, salaries_added=0)
for (ats, feed), cos in feeds.items():
    raw = results.get((ats, feed))
    for c in cos:
        old = c.get('jobs') or []
        if raw is None:
            stats['kept_failed'] += 1
            report.append(f'- {c["n"]} ({ats}): fetch failed, kept {len(old)} jobs. {errors.get((ats, feed), "")}')
            continue
        old_by = {}
        for jb in old:
            for k in key_ids(jb['u']): old_by[k] = jb
        fresh, seen = [], set()
        for x in raw:
            if not x.get('url') or not x.get('t') or PLACEHOLDER.search(x['t']): continue
            gl = german_loc(x.get('locs') or [], x.get('country', ''), x.get('remote', False))
            if not gl: continue
            loc, rem = gl
            prev = next((old_by[k] for k in key_ids(x['url']) | {x['id']} if k in old_by), None)
            text = txt(x.get('desc'))
            if prev:
                jb = dict(prev)
                jb['t'] = x['t'] or prev['t']
                if x.get('sal') and not prev.get('sal'): jb['sal'] = x['sal']; stats['salaries_added'] += 1
                if not jb.get('p'): jb['p'] = iso_date(x.get('pub'))
                stats['updated'] += 1
            else:
                jb = {'t': x['t'], 'loc': loc, 'rem': rem, 'd': discipline(x['t'], x.get('dept', ''), text), 's': seniority(x['t'], x.get('sen_hint', '')),
                      'lang': language(x['t'], text), 'u': x['url'], 'p': iso_date(x.get('pub')), 'sal': x.get('sal', '')}
                if jb['sal']: stats['salaries_added'] += 1
                stats['new'] += 1
            if jb['u'] in seen: continue
            seen.add(jb['u']); fresh.append(jb)
            if len(text) >= 300:
                new_desc.append({'src': f'{ats}:{feed}', 'id': x['id'], 'url': jb['u'], 't': x['t'], 'loc': loc, 'desc': x.get('desc', ''), 'et': x.get('et', ''),
                                 'pub': str(x.get('pub') or ''), 'rem': str(rem)})
        fresh.sort(key=lambda j: j.get('p') or '', reverse=True)
        fresh = fresh[:CAP]
        if not fresh and len(old) >= 5:
            stats['suspicious'] += 1; report.append(f'- {c["n"]} ({ats}): feed returned 0 German jobs (had {len(old)}), kept old jobs'); continue
        if ats == 'ashby' and len(fresh) < len(old) / 2 and len(old) >= 4:
            stats['suspicious'] += 1; report.append(f'- {c["n"]} (ashby): would shrink {len(old)} → {len(fresh)}, kept old jobs'); continue
        closed = len({j['u'] for j in old} - {j['u'] for j in fresh})
        stats['closed'] += closed
        if len(fresh) != len(old) or closed:
            report.append(f'- {c["n"]} ({ats}): {len(old)} → {len(fresh)} jobs ({closed} closed)')
        c['jobs'] = fresh; c['total'] = len(fresh)

# ---- custom career pages: drop only jobs whose link is gone (404/410)
def alive(u):
    try:
        req = urllib.request.Request(u, headers={'User-Agent': UA}, method='GET')
        with urllib.request.urlopen(req, timeout=int(os.environ.get('BAJ_LINK_TIMEOUT', '20'))) as r: return True
    except urllib.error.HTTPError as e:
        return e.code not in (404, 410)
    except Exception:
        return True   # network trouble is not proof the job is gone
custom = [c for c in B['companies'] if c.get('jobs') and not ats_of(c)]
urls = sorted({jb['u'] for c in custom for jb in c['jobs'] if jb.get('u', '').startswith('http')})
with cf.ThreadPoolExecutor(16) as ex:
    status = dict(zip(urls, ex.map(alive, urls)))
dead_total = 0
for c in custom:
    dead = [jb for jb in c['jobs'] if status.get(jb['u']) is False]
    if not dead: continue
    if len(dead) > len(c['jobs']) / 2 and len(c['jobs']) >= 4:
        report.append(f'- {c["n"]} (custom): {len(dead)}/{len(c["jobs"])} links 404, looks like a site change, kept all'); continue
    c['jobs'] = [jb for jb in c['jobs'] if status.get(jb['u']) is not False]; c['total'] = len(c['jobs']); dead_total += len(dead)
    report.append(f'- {c["n"]} (custom): removed {len(dead)} dead links')

after_total = sum(len(c.get('jobs') or []) for c in B['companies'])
fail_share = len(errors) / max(1, len(feeds))
hard = []
if fail_share > 0.30: hard.append(f'{len(errors)}/{len(feeds)} feeds failed ({fail_share:.0%} > 30%)')
if after_total < before_total * 0.70: hard.append(f'total jobs would drop {before_total} → {after_total} (> 30%)')

B['checked'] = f'{TODAY.day} {["Jan", "Feb", "March", "April", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"][TODAY.month - 1]} {TODAY.year}'
head = [f'# Job refresh {TODAY.isoformat()}' + (' (dry run)' if DRY else ''), '',
        f'- API feeds: {len(feeds)}, failed: {len(errors)}; custom career pages link-checked: {len(urls)} links, {dead_total} removed',
        f'- Jobs: {before_total} → {after_total} (new {stats["new"]}, closed {stats["closed"]}, still open {stats["updated"]})',
        f'- Published salaries added: {stats["salaries_added"]}; companies kept as-is because of a suspicious result: {stats["suspicious"]}',
        f'- Result: ' + ('ABORTED, nothing written: ' + '; '.join(hard) if hard else ('not written (dry run)' if DRY else 'written')), '', '## Changes by company', '']
open(os.path.join(BUILD, 'refresh_report.md'), 'w', encoding='utf-8').write('\n'.join(head + sorted(report)) + '\n')
print('\n'.join(head))
if hard: sys.exit(1)
if DRY: sys.exit(0)

# ---- write board + descriptions
out = SRC[:I0] + 'const BOARD = ' + json.dumps(B, ensure_ascii=False, separators=(',', ':')) + ';\n' + SRC[J0:]
open(os.path.join(DATA, 'board_data.js'), 'w', encoding='utf-8').write(out)
refetched = {f'{a}:{f}' for (a, f) in results}
live = {jb['u'].split('?')[0].rstrip('/') for c in B['companies'] for jb in c.get('jobs') or []}
fresh_urls = {x['url'].split('?')[0].rstrip('/') for x in new_desc}
kept = [x for x in D['jobs'] if (x.get('url') or '').split('?')[0].rstrip('/') in live - fresh_urls]   # e.g. companies whose fetch failed this week
D = {'fetched': NOW.isoformat(), 'log': {k: len([x for x in new_desc if x['src'] == k]) for k in refetched}, 'jobs': new_desc + kept}
with gzip.open(os.path.join(DATA, 'descriptions.json.gz'), 'wt', encoding='utf-8', compresslevel=9) as f:
    json.dump(D, f, ensure_ascii=False)
print('written board_data.js and descriptions.json.gz')
