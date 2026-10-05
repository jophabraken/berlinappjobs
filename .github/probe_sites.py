"""One-off probe #5: coverage audit. Are we listing all the jobs we could?

Runs from a GitHub runner (the network the daily refresh uses), on the current main data. Read-only: nothing is
written to the repo; it only sends GET requests to public careers pages and hiring-system APIs.
  A. Companies marked "not hiring" (tier 2/3) that have a readable hiring-system feed: how many German jobs do
     they have today? (The refresh only re-reads tier 1, so a company once marked tier 3 is never re-checked.)
  B. Hiring-system detection (ats_more.detect) on big companies without a readable feed: tier 1/2 "custom" first,
     then tier 3 by installs, within a time budget.
  C. Candidate feeds for big brands (guessed hiring-system slugs), to find the ones that exist.
Writes probe_report.md, posted as a PR comment by the workflow.
"""
import collections, concurrent.futures as cf, json, os, re, sys, time

os.environ.setdefault('BAJ_TRIES', '1')   # one try per request: a dead guess should cost one request, not three
out = []
def say(s=''): out.append(s); print(s)
sys.path.insert(0, '_build')
src = open('_build/refresh_jobs.py', encoding='utf-8').read().split('# ---------------------------------------------------------------- run')[0]
g = {'__name__': 'refresh_top', '__file__': os.path.abspath('_build/refresh_jobs.py')}
exec(compile(src, '_build/refresh_jobs.py', 'exec'), g)
A, B, F = g['ats_more'], g['B'], g['FETCHERS']
german_loc, PLACEHOLDER, is_manual = g['german_loc'], g['PLACEHOLDER'], g['is_manual']
T0 = time.time()
BUDGET = 420   # seconds for the whole run (the workflow stops at 10 minutes)

def ats(c): return (c.get('ats') or '').lower().split()[0] if c.get('ats') else ''
def german(raw):
    de, locs = [], collections.Counter()
    for x in raw or []:
        if x.get('keep') or not x.get('t') or not x.get('url') or PLACEHOLDER.search(x['t']) or is_manual(x['t']): continue
        gl = german_loc(x.get('locs') or [], x.get('country', ''), x.get('remote', False))
        if gl: de.append(x); locs[gl[0]] += 1
    return de, locs
def run(fn, *a):
    t = time.time()
    try: return fn(*a), None, time.time() - t
    except Exception as e: return None, f'{type(e).__name__}: {str(e)[:90]}', time.time() - t

# ------------------------------------------------------------------ A
say('## Probe #5: coverage audit\n')
say(f'Board: {len(B["companies"])} companies, {sum(len(c.get("jobs") or []) for c in B["companies"])} jobs; tiers {dict(collections.Counter(c.get("tier") for c in B["companies"]))}\n')
say('### A. "Not hiring" companies (tier 2/3) that have a readable feed\n')
cand = [c for c in B['companies'] if c.get('tier') in (2, 3) and ats(c) in F and ats(c) not in A.CRAWL_ATS and (c.get('feed') or '').startswith('http')]
say(f'{len(cand)} companies. German jobs today after the refresh filters (placeholder, manual roles, German location):\n')
say('| company | tier | system | feed jobs | German jobs | top cities | note |\n|---|---|---|---|---|---|---|')
rows = []
with cf.ThreadPoolExecutor(10) as ex:
    futs = {ex.submit(run, F[ats(c)], c['feed']): c for c in cand}
    for f in cf.as_completed(futs):
        c = futs[f]; raw, err, _ = f.result()
        de, locs = german(raw)
        rows.append((len(de), c, len(raw or []), locs, err))
for n, c, nraw, locs, err in sorted(rows, key=lambda r: -r[0]):
    say(f'| {c["n"][:40]} | {c.get("tier")} | {ats(c)} | {nraw} | **{n}** | {", ".join(f"{k} {v}" for k, v in locs.most_common(3))} | {err or ""} |')
say(f'\nTotal German jobs we are not showing from these: **{sum(r[0] for r in rows)}** (cap 60 per company: {sum(min(r[0], 60) for r in rows)})')

# ------------------------------------------------------------------ C (fast, before the slow detection)
say('\n### C. Guessed hiring-system feeds for big brands\n')
GUESS = {
    'greenhouse': ['babbel', 'soundcloud', 'deliveryhero', 'toogoodtogo', 'toogoodtogoapsdk', 'tiermobility', 'flink', 'raisin', 'pitch', 'miro',
                   'contentful', 'personio', 'blinkist', 'gorillas', 'grover', 'taxfix', 'getir', 'kry', 'doctolib', 'ottonova', 'zeitgold',
                   'thermondo', 'enpal', 'solarisbank', 'solaris', 'bitpanda', 'n26', 'mobilede', 'kleinanzeigen', 'adevinta', 'autoscout24',
                   'scout24', 'ecosia', 'wooga', 'king', 'innogames', 'goodgamestudios', 'bigpoint', 'travian', 'yager', 'ada', 'adahealth',
                   'mytheresa', 'idnow', 'freenow', 'lyft', 'bolt', 'uber', 'spotify', 'klarna', 'revolut', 'wise', 'vinted', 'tiktok', 'bending-spoons',
                   'onefootball', 'clue', 'helloclue', 'komoot', 'kaiaHealth', 'kaiahealth', 'selfapy', 'heyjobs', 'joblift', 'smava', 'check24',
                   'trivago', 'immoscout24', 'immobilienscout24', 'zalando', 'aboutyou', 'mediamarktsaturn', 'payback', 'celonis', 'deepl'],
    'lever': ['babbel', 'soundcloud', 'wooga', 'deliveryhero', 'blinkist', 'gorillas', 'miro', 'pitch', 'kry', 'taxfix', 'tier', 'bolt', 'onefootball',
              'clue', 'komoot', 'vinted', 'freenow', 'grover', 'raisin', 'getir', 'scalable', 'trade-republic', 'traderepublic', 'kolibri', 'kolibrigames'],
    'ashby': ['babbel', 'soundcloud', 'deliveryhero', 'blinkist', 'pitch', 'taxfix', 'raisin', 'grover', 'onefootball', 'clue', 'komoot', 'vinted',
              'tier', 'dott', 'flink', 'kry', 'doctolib', 'ecosia', 'deepl', 'n8n', 'langdock', 'parloa', 'tacto', 'mistral', 'black-forest-labs'],
    'smartrecruiters': ['DeliveryHero', 'Babbel', 'SoundCloud', 'Vinted', 'BoschGroup', 'Visa', 'Lidl', 'LidlDeutschland', 'Kaufland', 'adidas',
                        'Telekom', 'DeutscheTelekom', 'METRO', 'MetroAG', 'Flink3', 'IKEA', 'Allianz', 'Siemens', 'ProSiebenSat1', 'RTL', 'Sixt'],
    'personio': ['babbel', 'wooga', 'komoot', 'clue', 'onefootball', 'kleinanzeigen', 'sdui', 'anton', 'simpleclub', 'knowunity', 'fastic', 'yazio'],
    'recruitee': ['babbel', 'soundcloud', 'wooga', 'komoot', 'clue', 'kleinanzeigen', 'mobilede', 'autodoc', 'lotum', 'idealo', 'kaufda'],
}
URL = {'greenhouse': 'https://boards-api.greenhouse.io/v1/boards/{}/jobs', 'lever': 'https://api.lever.co/v0/postings/{}?mode=json',
       'ashby': 'https://api.ashbyhq.com/posting-api/job-board/{}', 'smartrecruiters': 'https://api.smartrecruiters.com/v1/companies/{}/postings',
       'personio': 'https://{}.jobs.personio.de', 'recruitee': 'https://{}.recruitee.com/api/offers/'}
known_feeds = {(c.get('feed') or '').lower() for c in B['companies']}
tests = [(a, s, URL[a].format(s)) for a, ss in GUESS.items() for s in dict.fromkeys(ss)]
found = []
def sr_list(u):   # SmartRecruiters: the list only (the reader also opens every ad, too slow for 20 guesses)
    items, off = [], 0
    while off <= 1500:
        d = g['jfetch'](f'{u}?limit=100&offset={off}')
        items += [dict(id=x['id'], url='https://jobs.smartrecruiters.com/x/' + str(x['id']), t=x.get('name', ''),
                       locs=[(x.get('location') or {}).get('city', '')], country=(x.get('location') or {}).get('country', '')) for x in d.get('content', [])]
        off += 100
        if off >= d.get('totalFound', 0): break
    return items
def guess(t):
    a, s, u = t
    if u.lower() in known_feeds: return None
    raw, err, _ = run(sr_list if a == 'smartrecruiters' else F[a], u)
    if not raw: return None
    de, locs = german(raw)
    return (a, s, u, len(raw), len(de), locs)
with cf.ThreadPoolExecutor(12) as ex:
    for r in ex.map(guess, tests):
        if r: found.append(r)
say(f'{len(tests)} guesses tried; {len(found)} feeds exist and are not on the board yet:\n')
say('| system | slug | feed jobs | German jobs | top cities |\n|---|---|---|---|---|')
for a, s, u, n, nde, locs in sorted(found, key=lambda r: -r[4]):
    say(f'| {a} | `{s}` | {n} | **{nde}** | {", ".join(f"{k} {v}" for k, v in locs.most_common(3))} |')

# ------------------------------------------------------------------ B
say('\n### B. Hiring-system detection on big companies without a readable feed\n')
samples = {}
_eval = A.evaluate
def evaluate(raw, company, placeholder, manual):
    r = _eval(raw, company, placeholder, manual)
    if raw and r[0] == 0:
        samples.setdefault(company['n'], [x.get('locs') for x in raw[:4]])
    return r
A.evaluate = evaluate
pool = [c for c in B['companies'] if not (ats(c) in F and (c.get('feed') or '').startswith('http')) and 'zalando' not in (c.get('feed') or '')
        and (c.get('careers') or c.get('feed') or '').startswith('http')]
pool.sort(key=lambda c: (c.get('tier') == 3, -(c.get('v') or 0)))
say(f'{len(pool)} candidates (tier 1/2 first, then tier 3, biggest apps first); time budget {BUDGET}s for the whole probe.\n')
res, done = [], 0
def det(c):
    if time.time() - T0 > BUDGET: return c, 'skipped', []
    log = []
    try: r = A.detect(c, F, PLACEHOLDER, is_manual, log)
    except Exception as e: r = None; log.append(f'error {type(e).__name__}')
    return c, r, log
with cf.ThreadPoolExecutor(16) as ex:
    for c, r, log in ex.map(det, pool):
        if r == 'skipped': continue
        done += 1
        if r:
            a, feed, cfg, raw = r
            de, locs = german(raw)
            res.append((len(de), c, a, feed, locs))
        elif c['n'] in samples:
            res.append((0, c, 'found jobs, none placed in Germany', '; '.join(log[-2:])[:150], samples[c['n']]))
say(f'Checked {done} of {len(pool)}. Readable systems found:\n')
say('| company | tier | jobs now | system → feed | German jobs | top cities |\n|---|---|---|---|---|---|')
for n, c, a, feed, locs in sorted(res, key=lambda r: -r[0]):
    loc_s = ', '.join(f'{k} {v}' for k, v in locs.most_common(3)) if isinstance(locs, collections.Counter) else f'sample locs: {str(locs)[:120]}'
    say(f'| {c["n"][:36]} | {c.get("tier")} | {len(c.get("jobs") or [])} | {a} `{str(feed)[:70]}` | **{n}** | {loc_s} |')
say(f'\nRun time {time.time() - T0:.0f}s.')
open('probe_report.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
