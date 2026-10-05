"""One-off probe #3: test the new Zalando reader (PR to come, branch seo-lead/2026-10-05) on the real site.

Applies the reader's diff (below) to this checkout, loads refresh_jobs.py up to the point where the refresh starts
(no feeds are fetched, nothing is written), then runs the Zalando reader and the refresh's own filters on its output:
placeholder, manual-role and German-location checks. Read-only: about 25 GET requests to jobs.zalando.com.
"""
import collections, json, os, re, subprocess, sys, time

PATCH = r'''diff --git a/_build/ats_more.py b/_build/ats_more.py
index 5fa488f0a..46f45b43d 100644
--- a/_build/ats_more.py
+++ b/_build/ats_more.py
@@ -347,7 +347,87 @@ def f_bamboohr(feed):
     with cf.ThreadPoolExecutor(6) as ex:
         return list(ex.map(detail, lst[:CAP * 2]))
 
-FETCHERS = {'workday': f_workday, 'workable': f_workable, 'bamboohr': f_bamboohr, 'crawl': f_crawl, 'join': f_join, 'teamtailor': f_teamtailor}
+# ---------------------------------------------------------------- Zalando (jobs.zalando.com)
+# Zalando's own careers site: no API, no JobPosting data. Each list page (/en/jobs?page=N, 15 jobs) carries its jobs as
+# JSON in the Next.js payload (self.__next_f): {"data":[{"title","id","entity","job_categories","offices","experience_level",
+# "updated_at"}]}, plus the office filter that maps each city to its country. The ad itself is on /en/jobs/{id}: a <dl> with
+# Location and Contract, then the description. Applications go through a form on that page, so it is also the apply link.
+ZAL = 'https://jobs.zalando.com'
+ZAL_CITY = {'Cologne': 'Köln', 'Hanover': 'Hannover', 'Dusseldorf': 'Düsseldorf', 'Munster': 'Münster', 'Munich': 'München',
+            'Moenchengladbach': 'Mönchengladbach', 'Constance': 'Konstanz', 'Giessen': 'Gießen', 'Nuremberg': 'Nürnberg', 'Frankfurt': 'Frankfurt am Main'}
+# Office roles only (Jop, 5 Oct 2026): warehouse, logistics and store jobs are left out, like MANUAL in refresh_jobs.py.
+ZAL_SKIP = re.compile(r'logistic|supply chain|warehouse|retail|outlet|store', re.I)
+
+def _rsc(page):
+    """The Next.js server-components payload of a page, decoded into one string."""
+    txt = ''
+    for p in re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', page):
+        try: txt += json.loads('"' + p + '"')
+        except Exception: pass
+    return txt
+
+def _rsc_values(txt, key):
+    """Every JSON value that follows "key": in the payload."""
+    out, dec = [], json.JSONDecoder()
+    for m in re.finditer(r'"%s":(?=[\[{"])' % re.escape(key), txt):
+        try: out.append(dec.raw_decode(txt, m.end())[0])
+        except Exception: pass
+    return out
+
+def _zal_ad(page):
+    """(location, contract, description html) from a Zalando job page."""
+    info = {}
+    for dt, dd in re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', page, re.S):
+        info.setdefault(html.unescape(re.sub(r'<[^>]+>', '', dt)).strip().lower(), html.unescape(re.sub(r'<[^>]+>', ' ', dd)).strip())
+    m = re.search(r'<(main)\b[^>]*>', page, re.I)
+    body = _inner(page, m) if m else ''
+    for rx in (r'<(div)\b[^>]*\bid="apply"[^>]*>', r'<(header)\b[^>]*>', r'<(form)\b[^>]*>'):   # the header and the application form
+        while True:
+            mm = re.search(rx, body, re.I)
+            if not mm: break
+            end = mm.end() + len(_inner(body, mm))
+            close = re.match(r'</%s\s*>' % mm.group(1), body[end:], re.I)
+            body = body[:mm.start()] + body[end + (close.end() if close else 0):]
+    body = re.sub(r'<(script|style|template|button|svg|select)\b.*?</\1\s*>', '', body, flags=re.S | re.I)
+    body = re.sub(r'<(?:img|input)\b[^>]*>', ' ', body, flags=re.I)
+    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
+    return info.get('location', ''), info.get('contract', ''), body.strip()
+
+def f_zalando(feed):
+    jobs, country, n = [], {}, 1
+    while n <= 30:
+        page = get(f'{ZAL}/en/jobs?page={n}')
+        txt = _rsc(page)
+        if n == 1:
+            for offices in _rsc_values(txt, 'offices'):
+                if isinstance(offices, list):
+                    for o in offices:
+                        if isinstance(o, dict) and o.get('main'): country[o['main']] = o.get('parent') or ''
+        batch = next((d for d in _rsc_values(txt, 'data') if isinstance(d, list) and d and isinstance(d[0], dict) and 'id' in d[0] and 'title' in d[0]), [])
+        if not batch: break
+        jobs += batch; n += 1
+    if not jobs: raise ValueError('no jobs found on jobs.zalando.com (site changed?)')
+    if not country: raise ValueError('no office list on jobs.zalando.com (site changed?)')
+    seen, keep = set(), []
+    for x in jobs:
+        de = [ZAL_CITY.get(o, o) for o in x.get('offices') or [] if country.get(o) == 'Germany']
+        de.sort(key=lambda c: c != 'Berlin')   # a Berlin job that is also in Dortmund shows as Berlin
+        if not de or str(x['id']) in seen or ZAL_SKIP.search(' '.join(x.get('job_categories') or [])): continue
+        seen.add(str(x['id'])); keep.append((x, de))
+    def detail(item):
+        x, de = item
+        url = f'{ZAL}/en/jobs/{x["id"]}'
+        try: loc, et, desc = _zal_ad(get(url))
+        except Exception: loc, et, desc = '', '', ''
+        return dict(id=str(x['id']), url=url, t=html.unescape(x.get('title') or ''), locs=de, country='Germany', remote=False, desc=desc,
+                    pub=x.get('updated_at') or '', et=et, sal='', dept=', '.join(x.get('job_categories') or []), sen_hint=x.get('experience_level') or '')
+    with cf.ThreadPoolExecutor(6) as ex:
+        return list(ex.map(detail, keep[:CAP * 2]))
+
+FETCHERS = {'workday': f_workday, 'workable': f_workable, 'bamboohr': f_bamboohr, 'crawl': f_crawl, 'join': f_join, 'teamtailor': f_teamtailor,
+            'zalando': f_zalando}
+# Careers sites with a reader of their own that companies on the board link as "custom": the host picks the reader.
+HOST_READERS = {'jobs.zalando.com': 'zalando'}
 CRAWL_ATS = {'crawl', 'join', 'teamtailor'}
 
 # ---------------------------------------------------------------- detection
diff --git a/_build/refresh_jobs.py b/_build/refresh_jobs.py
index 5af0fc1b0..442deed0c 100644
--- a/_build/refresh_jobs.py
+++ b/_build/refresh_jobs.py
@@ -269,7 +269,9 @@ FETCHERS.update(ats_more.FETCHERS)
 
 def ats_of(c):
     a = (c.get('ats') or '').lower().split()[0] if c.get('ats') else ''
-    return a if a in FETCHERS and c.get('feed') and c['feed'].startswith(('http', 'yazio')) else ''
+    if a in FETCHERS and c.get('feed') and c['feed'].startswith(('http', 'yazio')): return a
+    # a careers site with a reader of its own (ats_more.HOST_READERS, e.g. jobs.zalando.com), listed as "custom" on the board
+    return ats_more.HOST_READERS.get(urllib.parse.urlsplit(c.get('feed') or '').netloc.lower(), '')
 
 # ---------------------------------------------------------------- run
 D = json.load(gzip.open(os.path.join(DATA, 'descriptions.json.gz'), 'rt', encoding='utf-8'))
'''
open('/tmp/zal.patch', 'w', encoding='utf-8').write(PATCH)
subprocess.run(['git', 'apply', '/tmp/zal.patch'], check=True)
out = []
def say(s=''): out.append(s); print(s)

sys.path.insert(0, '_build')
src = open('_build/refresh_jobs.py', encoding='utf-8').read().split('# ---------------------------------------------------------------- run')[0]
g = {'__name__': 'refresh_top', '__file__': os.path.abspath('_build/refresh_jobs.py')}
exec(compile(src, '_build/refresh_jobs.py', 'exec'), g)
A = g['ats_more']
cache = {}
_get = A.get
def get(url, **kw):
    if url not in cache: cache[url] = _get(url, **kw)
    return cache[url]
A.get = get

say('## Probe #3: the Zalando reader on the real site\n')
c = next(c for c in g['B']['companies'] if c['n'] == 'Zalando SE')
say(f'- board entry: ats `{c.get("ats")}`, feed `{c.get("feed")}`, {len(c.get("jobs") or [])} jobs now → `ats_of()` = `{g["ats_of"](c)}`')
t0 = time.time()
try:
    raw = g['FETCHERS'][g['ats_of'](c)](c['feed'])
except Exception as e:
    say(f'- **reader failed:** {type(e).__name__}: {e}'); raw = []
say(f'- reader returned {len(raw)} jobs in {time.time() - t0:.0f}s ({len(cache)} pages fetched)')

# everything on the list, to check the category filter
allj, n = [], 1
while f'{A.ZAL}/en/jobs?page={n}' in cache:
    txt = A._rsc(cache[f'{A.ZAL}/en/jobs?page={n}'])
    allj += next((d for d in A._rsc_values(txt, 'data') if isinstance(d, list) and d and isinstance(d[0], dict) and 'id' in d[0]), [])
    n += 1
country = {}
for offices in A._rsc_values(A._rsc(cache.get(f'{A.ZAL}/en/jobs?page=1', '')), 'offices'):
    if isinstance(offices, list):
        for o in offices:
            if isinstance(o, dict) and o.get('main'): country[o['main']] = o.get('parent') or ''
de_all = [x for x in allj if any(country.get(o) == 'Germany' for o in x.get('offices') or [])]
say(f'- on the site: {len(allj)} jobs, {len(de_all)} with a German office; offices map: {len(country)} cities')
cats = collections.Counter(cat for x in de_all for cat in x.get('job_categories') or [])
skipped = collections.Counter(cat for x in de_all for cat in x.get('job_categories') or [] if A.ZAL_SKIP.search(' '.join(x.get('job_categories') or [])))
say(f'- German jobs by category: {dict(cats.most_common())}')
say(f'- skipped by ZAL_SKIP: {dict(skipped)}')
say(f'- German offices: {dict(collections.Counter(o for x in de_all for o in x.get("offices") or [] if country.get(o) == "Germany").most_common())}')

# the refresh's own filters, as in the main loop
kept, why = [], collections.Counter()
for x in raw:
    if g['PLACEHOLDER'].search(x['t']): why['placeholder'] += 1; continue
    if g['is_manual'](x['t']): why['manual role'] += 1; continue
    gl = g['german_loc'](x.get('locs') or [], x.get('country', ''), x.get('remote', False))
    if not gl: why['not German'] += 1; continue
    x['_loc'] = gl[0]; kept.append(x)
say(f'- after the refresh filters: {len(kept)} jobs (dropped: {dict(why)}); cap {g["CAP"]} → {min(len(kept), g["CAP"])} on the board')
say(f'- board locations: {dict(collections.Counter(x["_loc"] for x in kept).most_common())}')
dl = [len(g['txt'](x['desc'])) for x in kept]
say(f'- description text length: min {min(dl) if dl else 0}, median {sorted(dl)[len(dl)//2] if dl else 0}, max {max(dl) if dl else 0}; under 300 chars: {sum(1 for d in dl if d < 300)}')
say(f'- contract values: {dict(collections.Counter(x["et"] for x in kept))}')
say(f'- discipline / seniority / language of the first 60: '
    f'{dict(collections.Counter(g["discipline"](x["t"], x["dept"], g["txt"](x["desc"])) for x in kept[:60]))} / '
    f'{dict(collections.Counter(g["seniority"](x["t"], x.get("sen_hint", "")) for x in kept[:60]))} / '
    f'{dict(collections.Counter(g["language"](x["t"], g["txt"](x["desc"])) for x in kept[:60]))}')
old_ids = {i for jb in c.get('jobs') or [] for i in re.findall(r'/jobs/(\d{6,})', jb['u'])}
say(f'- the 3 jobs on the board now: {sorted(old_ids)}; still open: {sorted(old_ids & {x["id"] for x in raw})}')
say('\n| id | title | locs → board loc | contract | dept | desc chars |\n|---|---|---|---|---|---|')
for x in kept[:12]:
    say(f'| {x["id"]} | {x["t"][:60]} | {", ".join(x["locs"])} → {x["_loc"]} | {x["et"]} | {x["dept"][:30]} | {len(g["txt"](x["desc"]))} |')
for x in kept[:2]:
    say(f'\n**Description of {x["id"]}: first 1,200 and last 400 characters of the HTML**\n```\n{x["desc"][:1200]}\n…\n{x["desc"][-400:]}\n```')
open('probe_report.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
