"""One-off network probe #2 (Zalando only), run from a GitHub runner by .github/workflows/probe-sites.yml.

Probe #1 showed: jobs.zalando.com has no JSON API and no JSON-LD; the list is server-rendered (Next.js App
Router), 15 jobs per page, ?page=N works, sitemap.xml loads. This run saves what a Zalando reader needs:
  1. the sitemap's job URLs (count, URL shape, lastmod);
  2. how many pages the list has, and the HTML of one job card;
  3. job data inside the React server-components payload (self.__next_f), if any;
  4. on one job page: title, location, date and description markup.

Writes probe_report.md. Read-only: about 20 GET requests.
"""
import html as H, json, re, urllib.request, urllib.error, urllib.parse

UA = 'Mozilla/5.0 (compatible; BerlinAppJobsBot/1.0; +https://berlinappjobs.com)'   # refresh_jobs.py
HDR = {'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Language': 'en;q=0.9,de;q=0.8'}
BASE = 'https://jobs.zalando.com'
out = []
def say(s=''): out.append(s); print(s)

def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=25) as r:
            return r.status, r.read(3_000_000).decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'

def tidy(s):
    """Shorten HTML for reading: drop svg/style/script bodies and long class lists, collapse spaces."""
    s = re.sub(r'<svg\b.*?</svg>', '<svg/>', s, flags=re.S)
    s = re.sub(r'<(style|script)\b.*?</\1>', '', s, flags=re.S)
    s = re.sub(r'class="([^"]{60})[^"]*"', r'class="\1…"', s)
    return re.sub(r'\s+', ' ', s).strip()

def block(title, text, n):
    say(f'**{title}**\n```\n{text[:n]}\n```')

def rsc(page):
    """Join the self.__next_f.push([1,"..."]) chunks into one decoded string."""
    parts = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', page)
    txt = ''
    for p in parts:
        try: txt += json.loads('"' + p + '"')
        except Exception: pass
    return txt

# ------------------------------------------------------------------ 1. sitemap
say('## Zalando probe #2\n')
st, sm = get(BASE + '/sitemap.xml')
locs = re.findall(r'<loc>([^<]+)</loc>', sm)
jobs = [u for u in locs if re.search(r'/jobs/\d{6,}', u)]
say(f'### 1. sitemap.xml: HTTP {st}, {len(locs)} URLs, {len(jobs)} job URLs')
say(f'- languages: {sorted({(re.search(r"\.com/(\w\w)/", u) or [None, "-"])[1] for u in jobs})}')
for u in jobs[:5]: say(f'  - `{u}`')
m = re.search(r'<url>\s*<loc>[^<]*/jobs/\d{6,}[^<]*</loc>.*?</url>', sm, re.S)
if m: block('one job entry in the sitemap', tidy(m.group(0)), 600)
en_ids = {re.search(r'/jobs/(\d+)', u).group(1) for u in jobs if '/en/' in u}
say(f'- distinct job ids (en): {len(en_ids)}')

# ------------------------------------------------------------------ 2. list pages
say('\n### 2. List pages')
st1, p1 = get(BASE + '/en/jobs')
counts, seen, last = [], set(), 0
for n in range(1, 21):
    stn, pn = (st1, p1) if n == 1 else get(f'{BASE}/en/jobs?page={n}')
    ids = list(dict.fromkeys(re.findall(r'href="/en/jobs/(\d{6,})', pn)))
    new = [i for i in ids if i not in seen]; seen.update(ids)
    counts.append(f'p{n}: {stn}/{len(ids)} ids/{len(new)} new')
    if not new: last = n; break
say(f'- {"; ".join(counts)}')
say(f'- distinct job ids across pages: {len(seen)} (sitemap en: {len(en_ids)}, overlap {len(seen & en_ids)})')
say(f'- page 1 title tag: `{H.unescape((re.search(r"<title>(.*?)</title>", p1, re.S) or [None, ""])[1])}`')
filters = sorted(set(re.findall(r'href="(/en/jobs\?[^"]+)"', p1)))[:15]
say(f'- filter/pager hrefs on page 1: {filters or "none"}')
# one job card: the smallest element around the first job link
first = re.search(r'href="/en/jobs/\d{6,}[^"]*"', p1)
if first:
    i = first.start()
    start = max(p1.rfind('<li', 0, i), p1.rfind('<article', 0, i), p1.rfind('<div', max(0, i - 1500), i))
    a_end = p1.find('</a>', i)
    block('HTML of the first job card (tidied)', tidy(p1[max(0, i - 1200):a_end + 1500]), 3500)

# ------------------------------------------------------------------ 3. RSC payload
say('\n### 3. React server-components payload on page 1')
r1 = rsc(p1)
say(f'- decoded payload: {len(r1):,} chars')
fid = re.search(r'/en/jobs/(\d{6,})', p1)
if r1 and fid:
    k = r1.find(fid.group(1))
    say(f'- first job id `{fid.group(1)}` found in payload at {k}')
    if k >= 0: block('payload around the first job id', r1[max(0, k - 1500):k + 2500], 4000)
keys = sorted(set(re.findall(r'"(title|jobTitle|name|location|locations|city|country|department|team|category|'
                             r'employmentType|contractType|seniority|experienceLevel|workplaceType|remote|'
                             r'publishedAt|createdAt|updatedAt|datePosted|postedAt|startDate|language|slug|id|'
                             r'description|content|body|requisitionId|externalId|applyUrl|applicationUrl)"\s*:', r1)))
say(f'- interesting keys in payload: {keys or "none"}')

# ------------------------------------------------------------------ 4. one job page
say('\n### 4. One job page')
ju = BASE + '/en/jobs/' + (fid.group(1) if fid else '2724676')
stj, pj = get(ju)
say(f'- `{ju}`: HTTP {stj}, {len(pj):,} chars')
for name, rx in [('title tag', r'<title>(.*?)</title>'), ('h1', r'<h1[^>]*>(.*?)</h1>'),
                 ('og:title', r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"'),
                 ('og:description', r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"'),
                 ('meta description', r'<meta[^>]+name="description"[^>]+content="([^"]*)"'),
                 ('canonical', r'<link[^>]+rel="canonical"[^>]+href="([^"]*)"')]:
    mm = re.search(rx, pj, re.S)
    say(f'- {name}: `{tidy(H.unescape(re.sub(r"<[^>]+>", "", mm.group(1))))[:200] if mm else "-"}`')
h1 = re.search(r'<h1\b', pj)
if h1: block('HTML after the h1 (tidied): location / date / tags', tidy(pj[h1.start():h1.start() + 6000]), 3000)
main = re.search(r'<main\b.*?</main>', pj, re.S)
body = main.group(0) if main else pj
text = re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<(style|script)\b.*?</\1>', '', body, flags=re.S))))
say(f'- visible text in <main>: {len(text):,} chars (main element: {"yes" if main else "no"})')
heads = re.findall(r'<h[2-4][^>]*>(.*?)</h[2-4]>', body, re.S)
say(f'- h2-h4 headings: {[tidy(re.sub(r"<[^>]+>", "", x))[:60] for x in heads][:15]}')
dates = sorted(set(re.findall(r'\b20\d\d-\d\d-\d\d(?:T[\d:.]+Z?)?', pj)))[:10]
say(f'- ISO dates on the page: {dates or "none"}')
rj = rsc(pj)
say(f'- job page RSC payload: {len(rj):,} chars; keys: '
    f'{sorted(set(re.findall(r"\"(title|location|locations|city|publishedAt|createdAt|updatedAt|datePosted|description|content|employmentType|applyUrl|language|team|department)\"\s*:", rj))) or "none"}')
if rj:
    k = max(rj.find('"description"'), rj.find('"content"'))
    if k >= 0: block('job page payload around "description"/"content"', rj[max(0, k - 800):k + 1500], 2300)
apply = sorted(set(re.findall(r'href="([^"]*(?:apply|bewerb)[^"]*)"', pj, re.I)))[:5]
say(f'- apply links: {apply or "none"}')

open('probe_report.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
