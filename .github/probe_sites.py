"""One-off network probe, run from a GitHub runner (the same network the daily refresh uses).

1. Zalando: how does jobs.zalando.com serve its job list? Looks for JSON-LD on job pages, embedded
   Next.js data, the pager's query parameter, and API paths named in the site's JS bundles, then
   tries the most likely API URLs.
2. "Dead link" false positives: Lotum and Stillfront (bytro.teamtailor.com) answer 404 to the refresh's
   page_check every day, but load fine elsewhere. Request them with the refresh's exact headers, without
   Accept-Language, without our User-Agent, and with no headers, to see which one causes the 404.

Writes probe_report.md. Read-only: it only sends GET/HEAD requests, about 60 in total.
"""
import json, re, urllib.request, urllib.error, urllib.parse

UA = 'Mozilla/5.0 (compatible; BerlinAppJobsBot/1.0; +https://berlinappjobs.com)'   # refresh_jobs.py
HTML_H = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'}                                 # ats_more.py
out = []
def say(s=''): out.append(s); print(s)

def fetch(url, headers=None, method='GET', limit=2_000_000):
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, dict(r.headers), r.read(limit).decode('utf-8', 'replace'), r.geturl()
    except urllib.error.HTTPError as e:
        body = ''
        try: body = e.read(4000).decode('utf-8', 'replace')
        except Exception: pass
        return e.code, dict(e.headers or {}), body, url
    except Exception as e:
        return None, {}, f'{type(e).__name__}: {e}', url

def snip(s, n=400): return re.sub(r'\s+', ' ', s or '')[:n]

# ------------------------------------------------------------------ 1. Zalando
say('## 1. Zalando (jobs.zalando.com)\n')
REF = {'User-Agent': UA, **HTML_H}
LIST = 'https://jobs.zalando.com/en/jobs/'
st, hd, html, final = fetch(LIST, REF)
say(f'- Listing `{LIST}`: HTTP {st}, {len(html):,} chars, final URL `{final}`, server `{hd.get("Server", "")}`')
job_links = sorted(set(re.findall(r'href="(/(?:en|de)/jobs/\d{6,}[^"]*)"', html)))
say(f'- Job links in the HTML: {len(job_links)} (e.g. `{job_links[0] if job_links else "-"}`)')
pager = sorted(set(re.findall(r'href="([^"]*[?&][^"]*page[^"]*)"', html, re.I)))[:8]
say(f'- Pager links: {pager or "none found"}')
nd = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
if nd:
    try:
        d = json.loads(nd.group(1))
        say(f'- `__NEXT_DATA__`: yes, page `{d.get("page")}`, buildId `{d.get("buildId")}`, pageProps keys {list((d.get("props", {}).get("pageProps") or {}).keys())[:15]}')
        say(f'  - first 600 chars of pageProps: `{snip(json.dumps(d.get("props", {}).get("pageProps"))[:600], 600)}`')
    except Exception as e:
        say(f'- `__NEXT_DATA__`: present but not JSON ({e})')
else:
    say('- `__NEXT_DATA__`: none (App Router / RSC, or not Next.js)')
say(f'- `self.__next_f` (React server components payload): {"yes" if "self.__next_f" in html else "no"}')
ld = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S)
say(f'- JSON-LD blocks on the listing: {len(ld)}')
api_inline = sorted(set(re.findall(r'["\'](/api/[\w/.-]{2,80}|https?://[\w.-]*zalando[\w.-]*/api/[\w/.-]{2,80})', html)))
say(f'- `/api/` strings in the HTML: {api_inline[:20] or "none"}')

# job page: JSON-LD?
if job_links:
    ju = urllib.parse.urljoin(LIST, job_links[0])
    st2, _, jhtml, _ = fetch(ju, REF)
    lds = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', jhtml, re.S)
    types = []
    for b in lds:
        try:
            o = json.loads(b); types += [x.get('@type') for x in (o if isinstance(o, list) else [o]) if isinstance(x, dict)]
        except Exception: types.append('unparseable')
    say(f'- Job page `{ju}`: HTTP {st2}, JSON-LD types {types or "none"}, microdata JobPosting: {"yes" if "schema.org/JobPosting" in jhtml else "no"}')
    if 'JobPosting' in types:
        for b in lds:
            if 'JobPosting' in b: say(f'  - JobPosting (first 700 chars): `{snip(b, 700)}`')

# JS bundles: which API paths does the front end call?
scripts = sorted(set(re.findall(r'<script[^>]+src="([^"]+\.js[^"]*)"', html)))
say(f'- Script bundles: {len(scripts)}')
found = {}
for s in scripts[:40]:
    su = urllib.parse.urljoin(LIST, s)
    stj, _, js, _ = fetch(su, {'User-Agent': UA}, limit=4_000_000)
    if stj != 200: continue
    for m in re.findall(r'["\'`]((?:https?://[\w.-]+)?/api/[\w/${}.:-]{2,100})', js):
        found.setdefault(m, s.rsplit('/', 1)[-1])
    for m in re.findall(r'["\'`](https?://[\w.-]*(?:algolia|workday|greenhouse|smartrecruiters|successfactors|personio|lever|ashby|graphql)[\w./-]*)', js, re.I):
        found.setdefault(m, s.rsplit('/', 1)[-1])
say(f'- API paths / ATS hosts named in the JS ({len(found)}):')
for k, v in sorted(found.items())[:40]: say(f'  - `{k}` (in `{v}`)')

# try the likely endpoints
say('- Endpoint attempts (JSON Accept header):')
JH = {'User-Agent': UA, 'Accept': 'application/json', 'Accept-Language': 'en'}
tries = ['https://jobs.zalando.com/api/jobs/', 'https://jobs.zalando.com/api/jobs',
         'https://jobs.zalando.com/api/jobs/?limit=10&offset=0', 'https://jobs.zalando.com/api/jobs/?page=1&limit=10',
         'https://jobs.zalando.com/api/jobs/?locale=en', 'https://jobs.zalando.com/api/jobs/?lang=en&page=1',
         'https://jobs.zalando.com/en/jobs/?page=2', 'https://jobs.zalando.com/en/jobs?page=2', 'https://jobs.zalando.com/en/jobs/?p=2',
         'https://jobs.zalando.com/sitemap.xml', 'https://jobs.zalando.com/robots.txt']
tries += [urllib.parse.urljoin(LIST, k) for k in sorted(found) if k.startswith('/api/') and '$' not in k and '{' not in k][:10]
for u in dict.fromkeys(tries):
    st3, h3, b3, _ = fetch(u, JH)
    extra = ''
    if 'page' in u and '/en/jobs' in u:
        ids = re.findall(r'/(?:en|de)/jobs/(\d{6,})', b3)
        extra = f' | first job ids {ids[:3]}'
    say(f'  - `{u}` → {st3}, {h3.get("Content-Type", "")}, {len(b3):,} chars{extra} | `{snip(b3, 250)}`')

# ------------------------------------------------------------------ 2. dead-link false positives
say('\n## 2. "Dead link" false positives (page_check in refresh_jobs.py)\n')
variants = [
    ('refresh headers (UA + Accept + Accept-Language de)', {'User-Agent': UA, **HTML_H}),
    ('our UA, no Accept-Language', {'User-Agent': UA, 'Accept': HTML_H['Accept']}),
    ('browser-like UA, same Accept headers (diagnostic only)', {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', **HTML_H}),
    ('no headers at all (Python default UA)', {}),
]
urls = ['https://www.lotum.com', 'https://www.lotum.com/', 'https://bytro.teamtailor.com/jobs',
        'https://bytro.teamtailor.com/jobs/6274405-senior-crm-manager',
        'https://www.hanseaticbank.de/karriere/jobs/03573487',   # control: really 404 elsewhere
        'https://berlinappjobs.com/']                          # control: should be 200
say('| URL | ' + ' | '.join(v[0] for v in variants) + ' |')
say('|---|' + '---|' * len(variants))
for u in urls:
    cells = []
    for _, h in variants:
        st4, h4, b4, fin = fetch(u, h)
        note = (f'{st4}' if st4 else f'error: {snip(b4, 60)}') + (f' → {fin}' if fin != u else '') + (f' ({h4.get("Server", "")})' if st4 and st4 >= 400 else '')
        cells.append(note)
    say(f'| `{u}` | ' + ' | '.join(cells) + ' |')
st5, _, b5, _ = fetch('https://api.ipify.org?format=json', {})
say(f'\nRunner IP: {snip(b5, 60)} (GitHub-hosted Azure range)')

open('probe_report.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
