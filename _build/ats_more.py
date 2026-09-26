# -*- coding: utf-8 -*-
"""More hiring-system readers for refresh_jobs.py, and detection of the hiring system behind a custom careers page.

Readers (same raw-job dicts as the ones in refresh_jobs.py):
  * workday     Workday career sites ({tenant}.wdN.myworkdayjobs.com/{site}), via the JSON API the site itself uses.
  * workable    apply.workable.com/{account}, via Workable's public widget API.
  * bamboohr    {sub}.bamboohr.com/careers, via the JSON the careers page loads.
  * crawl       Any careers site whose job pages carry schema.org JobPosting data (JSON-LD or microdata), which
                every site that wants to appear in Google for Jobs has: JOIN, Teamtailor, rexx, SAP SuccessFactors,
                d.vinci, many hand-built sites. It reads the listing page(s) and the sitemap for job links, opens
                each job page and reads title, location, date, description and salary from the JobPosting.
                Jobs we already have are re-opened too: a job counts as closed when its page is gone (404/410)
                or no longer carries a JobPosting (usually a redirect to the job list).
  * join, teamtailor: presets of crawl with the link pattern those systems use.

Detection (detect()): for a company without a readable feed, look for a hiring system's fingerprint in its
careers URL, feed, ATS note and job links, then in the careers page and one job page. Every candidate is
tried for real; it is only accepted when it returns German jobs that fit what the board already shows.
If no known system is found but the job pages carry JobPosting data, the company gets a crawl reader.
"""
import concurrent.futures as cf, gzip, html, json, os, re, urllib.error, urllib.parse

_fetch = _sal = _german = None
def init(fetch, sal_str, german_loc):
    """refresh_jobs.py hands over its HTTP helper, salary formatter and German-location test."""
    global _fetch, _sal, _german
    _fetch, _sal, _german = fetch, sal_str, german_loc

HTML_H = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'}
def get(url, tries=2, timeout=25):
    return _fetch(url, headers=HTML_H, tries=tries, timeout=timeout).decode('utf-8', 'replace')
def jget(url, **kw): return json.loads(_fetch(url, **kw).decode('utf-8'))

CAP = 60            # jobs per company (same as refresh_jobs.py)
NEW_PAGES = 45      # job pages not seen before that one crawl may open per run
AGGREGATORS = re.compile(r'stepstone|indeed\.|linkedin\.|xing\.com|games-career|glassdoor|monster\.|jobware|kununu|arbeitsagentur|'
                         r'google\.|facebook\.|instagram\.|twitter\.|youtube\.|goo\.gl|bit\.ly', re.I)
ASSET = re.compile(r'\.(?:js|css|png|jpe?g|gif|svg|webp|ico|woff2?|ttf|eot|pdf|mp4|zip|xml|json|rss)(?:\?|$)', re.I)

# ---------------------------------------------------------------- schema.org JobPosting
LD_RX = re.compile(r'<script[^>]+type\s*=\s*["\']?application/ld\+json["\']?[^>]*>(.*?)</script>', re.S | re.I)
def _walk(o):
    if isinstance(o, list):
        for x in o: yield from _walk(x)
    elif isinstance(o, dict):
        yield o
        for k in ('@graph', 'mainEntity', 'mainEntityOfPage', 'itemListElement', 'item'):
            if isinstance(o.get(k), (list, dict)): yield from _walk(o[k])
def _is_posting(o):
    t = o.get('@type')
    return t == 'JobPosting' or (isinstance(t, list) and 'JobPosting' in t)
def _s(v):
    if isinstance(v, dict): return _s(v.get('name') or v.get('@value') or v.get('value') or '')
    if isinstance(v, list): return ', '.join(x for x in (_s(y) for y in v) if x)
    return '' if v is None else str(v).strip()

def _inner(page, m):
    """Inner HTML of the element whose opening tag regex match is m (balanced on the same tag name)."""
    tag, pos, depth = m.group(1).lower(), m.end(), 1
    for t in re.finditer(r'<(/?)%s\b[^>]*>' % re.escape(tag), page[pos:pos + 300000], re.I):
        depth += -1 if t.group(1) else 1
        if depth == 0: return page[pos:pos + t.start()]
    return page[pos:pos + 30000]
def _microdata(page):
    """Minimal schema.org microdata reader (SAP SuccessFactors career sites use it instead of JSON-LD)."""
    if not re.search(r'itemtype\s*=\s*["\']https?://schema\.org/JobPosting', page, re.I): return None
    def prop(name, inner=False):
        m = (re.search(r'<meta[^>]+itemprop\s*=\s*["\']%s["\'][^>]*content\s*=\s*["\']([^"\']*)' % name, page, re.I)
             or re.search(r'<meta[^>]+content\s*=\s*["\']([^"\']*)["\'][^>]*itemprop\s*=\s*["\']%s["\']' % name, page, re.I))
        if m: return html.unescape(m.group(1)).strip()
        m = re.search(r'<(\w+)[^>]*\bitemprop\s*=\s*["\']%s["\'][^>]*>' % name, page, re.I)
        if not m: return ''
        v = _inner(page, m)
        return v if inner else html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', v))).strip()
    title = prop('title')
    if not title: return None
    return {'@type': 'JobPosting', 'title': title, 'description': prop('description', inner=True), 'datePosted': prop('datePosted'),
            'employmentType': prop('employmentType'), 'validThrough': prop('validThrough'),
            'jobLocation': {'address': {'addressLocality': prop('addressLocality'), 'addressRegion': prop('addressRegion'),
                                        'addressCountry': prop('addressCountry')}}}

def postings(page):
    """All JobPosting objects on a page (JSON-LD first, microdata as fallback)."""
    out = []
    for m in LD_RX.finditer(page):
        s = re.sub(r'^\s*(?:<!--|<!\[CDATA\[)|(?:-->|\]\]>)\s*$', '', m.group(1).strip())
        d = None
        for cand in (s, html.unescape(s), re.sub(r',\s*([}\]])', r'\1', s)):
            try: d = json.loads(cand, strict=False); break
            except Exception: pass
        if d is None: continue
        out += [o for o in _walk(d) if _is_posting(o)]
    if not out:
        md = _microdata(page)
        if md: out.append(md)
    return out

def posting_to_raw(o, url):
    locs, country = [], ''
    jl = o.get('jobLocation') or []
    for l in (jl if isinstance(jl, list) else [jl]):
        if not isinstance(l, dict): locs.append(_s(l)); continue
        a = l.get('address') or {}
        if isinstance(a, list): a = a[0] if a else {}
        if not isinstance(a, dict): locs.append(_s(a)); continue
        locs.append(', '.join(x for x in (_s(a.get('addressLocality')), _s(a.get('addressRegion'))) if x))
        country = country or _s(a.get('addressCountry'))
    remote = 'TELECOMMUTE' in json.dumps(o.get('jobLocationType') or '').upper()
    if remote:
        req = _s(o.get('applicantLocationRequirements'))
        if req: locs.append(req)
        if re.search(r'germany|deutschland|^de$', req, re.I): country = country or 'DE'
    desc = o.get('description') or ''
    if not isinstance(desc, str): desc = _s(desc)
    if '&lt;' in desc and '<' not in desc.replace('&lt;', ''): desc = html.unescape(desc)
    sal, bs = '', o.get('baseSalary')
    if isinstance(bs, dict):
        v = bs.get('value')
        if isinstance(v, dict): lo, hi, unit = v.get('minValue') or v.get('value'), v.get('maxValue'), v.get('unitText') or bs.get('unitText')
        else: lo, hi, unit = v, None, bs.get('unitText')
        per = {'YEAR': 'year', 'MONTH': 'month', 'HOUR': 'hour'}.get(str(unit or 'YEAR').upper(), '')
        try: sal = _sal(lo, hi, per, (bs.get('currency') or v.get('currency', '') if isinstance(v, dict) else bs.get('currency')) or '') if per else ''
        except Exception: sal = ''
    et = o.get('employmentType')
    et = ', '.join(map(str, et)) if isinstance(et, list) else _s(et)
    return dict(id=url, url=url, t=html.unescape(_s(o.get('title'))), locs=locs, country=country, remote=remote, desc=desc,
                pub=_s(o.get('datePosted')), et=et, sal=sal, dept=_s(o.get('occupationalCategory') or ''), valid=_s(o.get('validThrough')))

# ---------------------------------------------------------------- link discovery
def _norm(u, keep_query):
    p = urllib.parse.urlsplit(u)
    q = p.query if keep_query else ''
    return urllib.parse.urlunsplit((p.scheme or 'https', p.netloc.lower(), p.path or '/', q, ''))

def _depth(u): return len([x for x in urllib.parse.urlsplit(u).path.split('/') if x])
def _depth_ok(u, cfg): return not cfg.get('depths') or _depth(u) in cfg['depths']

def find_links(page, base, cfg):
    """Job-page links in a listing page: hrefs, plus absolute or root-relative URLs anywhere in the source
    (listings built with JavaScript often keep their job URLs in an embedded JSON blob)."""
    host, path_rx, keep_q = cfg['host'], cfg['path'], cfg.get('query', False)
    src = page.replace('\\/', '/').replace('\\u002F', '/').replace('&amp;', '&')
    rx = re.compile(r'(?:https?://' + re.escape(urllib.parse.urlsplit(host).netloc) + r'|(?<=["\'=(\s]))(' + path_rx + r')', re.I)
    out = []
    for m in rx.finditer(src):
        if m.group(1).startswith('//'): continue
        u = host + m.group(1)
        if ASSET.search(u) or not _depth_ok(u, cfg): continue
        out.append(_norm(u, keep_q))
    for h in re.findall(r'''href\s*=\s*["']([^"'#\s<>]+)''', src, re.I):   # relative links (no leading slash)
        if h.startswith(('http', '/', 'mailto:', 'tel:', 'javascript:', '#')): continue
        u = urllib.parse.urljoin(base, h)
        if u.startswith(host) and re.match(path_rx + '$', urllib.parse.urlsplit(u).path + (('?' + urllib.parse.urlsplit(u).query) if keep_q and urllib.parse.urlsplit(u).query else ''), re.I) and not ASSET.search(u) and _depth_ok(u, cfg):
            out.append(_norm(u, keep_q))
    return list(dict.fromkeys(out))

def sitemap_links(cfg, limit=6):
    host = cfg['host']
    try: sms = re.findall(r'(?im)^\s*sitemap:\s*(\S+)', get(host + '/robots.txt', tries=1, timeout=15))
    except Exception: sms = []
    queue, seen, out = (sms or [host + '/sitemap.xml'])[:6], set(), []
    rx = re.compile(r'^' + re.escape(host) + cfg['path'] + '$', re.I)
    while queue and len(seen) < limit:
        sm = queue.pop(0)
        if sm in seen: continue
        seen.add(sm)
        try:
            x = _fetch(sm, headers=HTML_H, tries=1, timeout=25)
            if x[:2] == b'\x1f\x8b': x = gzip.decompress(x)
            x = x.decode('utf-8', 'replace')
        except Exception:
            continue
        locs = [html.unescape(l) for l in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', x)]
        if '<sitemapindex' in x:
            queue += [l for l in locs if re.search(r'job|stelle|career|karriere|position|vacanc|offer', l, re.I)] or locs[:4]
        else:
            out += [_norm(l, cfg.get('query')) for l in locs if rx.match(l) and _depth_ok(l, cfg)]
    return list(dict.fromkeys(out))

# ---------------------------------------------------------------- crawl reader
CRAWL = {}   # feed (listing URL) -> cfg; refresh_jobs.py fills it from board_data before fetching

def learn_cfg(job_urls, listing):
    """Derive host + path pattern from the job links we already have. None if they are not individual pages."""
    urls = [u for u in job_urls if u and u.startswith('http') and not AGGREGATORS.search(u)]
    if not urls: return None
    hosts = {}
    for u in urls: hosts.setdefault(urllib.parse.urlsplit(u).netloc.lower(), []).append(u)
    netloc, us = max(hosts.items(), key=lambda kv: len(kv[1]))
    parts = [urllib.parse.urlsplit(u) for u in us]
    keep_q = all(p.query for p in parts) and len({p.path for p in parts}) < len({(p.path, p.query) for p in parts})
    paths = sorted({p.path + (('?' + p.query) if keep_q else '') for p in parts})
    lp = urllib.parse.urlsplit(listing or '')
    single_page = len(paths) < 2 and not keep_q
    if single_page and (lp.netloc.lower(), lp.path.rstrip('/')) == (netloc, paths[0].rstrip('/')):
        # the only link we have is the careers page itself: any page on the site that looks like a job ad
        path = r'/(?=[^"\'\s<>#?]*(?:job|stelle|karriere|career|position|vacanc|offer|angebot|\d{4}))[^"\'\s<>#?]{3,}'
    elif single_page:
        # one real job page: same first folder, same depth, digits if it has them
        segs = [x for x in paths[0].split('/') if x]
        base = '/' + segs[0] + '/' if len(segs) > 1 else '/'
        digits = bool(re.search(r'\d{2,}', paths[0][len(base):]))
        path = re.escape(base) + (r'(?=[^"\'\s<>#]*\d{2})' if digits else '') + r'[^"\'\s<>#?]*[^"\'\s<>#?/]/?'
    else:
        pre = os.path.commonprefix(paths)
        pre = pre[:pre.rfind('/') + 1] if '/' in pre else '/'
        digits = all(re.search(r'\d{2,}', p[len(pre):]) for p in paths)
        tail = r'[^"\'\s<>#]*' if keep_q else r'[^"\'\s<>#?]*'
        path = re.escape(pre) + (r'(?=[^"\'\s<>#]*\d{2})' if digits else '') + tail + r'[^"\'\s<>#?/]' + r'/?'
    scheme = parts[0].scheme or 'https'
    depths = [] if single_page and (lp.netloc.lower(), lp.path.rstrip('/')) == (netloc, paths[0].rstrip('/')) else sorted({_depth(u) for u in us})
    return {'host': f'{scheme}://{netloc}', 'path': path, 'query': keep_q, 'depths': depths,
            'lists': list(dict.fromkeys([x for x in [listing] if x and x.startswith('http')] + [f'{scheme}://{netloc}{os.path.commonprefix(paths)[:os.path.commonprefix(paths).rfind("/") + 1] or "/"}']))}

def preset(ats, feed):
    """Crawl settings for JOIN and Teamtailor from their usual URLs."""
    if ats == 'join':
        slug = re.search(r'join\.com/companies/([\w-]+)', feed).group(1)
        return {'host': 'https://join.com', 'path': rf'/companies/{slug}/\d+[\w%-]*', 'query': False, 'lists': [f'https://join.com/companies/{slug}']}
    if ats == 'teamtailor':
        p = urllib.parse.urlsplit(feed)
        return {'host': f'{p.scheme}://{p.netloc}', 'path': r'/(?:[a-z]{2}(?:-[a-zA-Z]{2})?/)?jobs/\d+[\w%-]*', 'query': False,
                'lists': list(dict.fromkeys([feed, f'{p.scheme}://{p.netloc}/jobs']))}
    return None

class SiteChanged(Exception): pass

def f_crawl(feed, cfg=None):
    cfg = cfg or CRAWL.get(feed) or {}
    if not cfg.get('host'): raise ValueError('no crawl settings for ' + feed)
    known = [u for u in cfg.get('known', []) if u.startswith(cfg['host'])]
    skip = set(cfg.get('skip', []))
    cands = []
    for lst in cfg.get('lists') or [feed]:
        try: cands += find_links(get(lst), lst, cfg)
        except Exception: pass
    if len(set(cands)) < 15:
        try: cands += sitemap_links(cfg)
        except Exception: pass
    known_n = {_norm(u, cfg.get('query')) for u in known}
    new = [u for u in dict.fromkeys(cands) if u not in known_n and u not in skip][:NEW_PAGES]
    todo = list(dict.fromkeys(list(known_n) + new))

    def one(u):
        try:
            page = get(u)
        except urllib.error.HTTPError as e:
            return u, ('gone' if e.code in (404, 410) else 'error'), None
        except Exception:
            return u, 'error', None
        ps = postings(page)
        # exactly one JobPosting = a job page; several = a list page (its jobs have their own pages)
        return u, ('ok' if len(ps) == 1 else 'multi' if ps else 'nojob'), ps
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(one, todo))
    raws, expired, nojob, fetched_ok = [], [], [], 0
    for u, st, ps in res:
        if st == 'error' or (st == 'multi' and u in known_n):
            if u in known_n: raws.append({'keep': True, 'url': u, 'id': u})
            continue
        fetched_ok += 1
        if st != 'ok':
            if u not in known_n: nojob.append(u)
            continue
        for o in ps[:1]:
            r = posting_to_raw(o, u)
            (expired if r['valid'] and r['valid'][:10] < _today() else raws).append(r)
    if not [r for r in raws if not r.get('keep')] and expired:
        raws += expired                                     # every validThrough in the past: the site sets it wrong, ignore it
    cfg['skip_new'] = nojob
    if fetched_ok and not [r for r in raws if not r.get('keep')] and known:
        raise SiteChanged(f'no job page with JobPosting data among {fetched_ok} pages (site changed?)')
    return raws

def _today():
    import datetime
    return datetime.date.today().isoformat()

def f_join(feed): return f_crawl(feed, CRAWL.get(feed) or preset('join', feed))
def f_teamtailor(feed): return f_crawl(feed, CRAWL.get(feed) or preset('teamtailor', feed))

# ---------------------------------------------------------------- API readers
WD_RX = re.compile(r'https?://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)')
def f_workday(feed):
    tenant, wd, site = WD_RX.match(feed).groups()
    host = f'https://{tenant}.{wd}.myworkdayjobs.com'
    api = f'{host}/wday/cxs/{tenant}/{site}'
    H = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    def post(body): return json.loads(_fetch(api + '/jobs', data=json.dumps(body).encode(), headers=H).decode('utf-8'))
    first = post({'appliedFacets': {}, 'limit': 20, 'offset': 0, 'searchText': ''})
    facets = {}
    def walk(fs, param=None):
        for f in fs or []:
            p = f.get('facetParameter') or param
            for v in f.get('values') or []:
                if v.get('values') is not None and v.get('facetParameter'): walk([v], p); continue
                if re.fullmatch(r'germany|deutschland', (v.get('descriptor') or '').strip(), re.I) and re.search(r'country', p or '', re.I) and v.get('id'):
                    facets.setdefault(p, []).append(v['id'])
    walk(first.get('facets'))
    body = {'appliedFacets': facets, 'limit': 20, 'offset': 0, 'searchText': ''}
    d = post(body) if facets else first
    total, items = d.get('total') or 0, []
    while True:
        items += d.get('jobPostings') or []
        body['offset'] += 20
        if body['offset'] >= total or body['offset'] >= (300 if facets else 1000): break
        d = post(body)
    if not facets:   # no country filter on this site: only open ads that could be in Germany
        items = [x for x in items if re.search(r'locations', x.get('locationsText') or '', re.I) or _german([x.get('locationsText') or ''])]
    def detail(x):
        try: i = json.loads(_fetch(api + x['externalPath'], headers={'Accept': 'application/json'}, tries=2).decode('utf-8')).get('jobPostingInfo') or {}
        except Exception: i = {}
        locs = [i.get('location') or x.get('locationsText') or ''] + list(i.get('additionalLocations') or [])
        rt = i.get('remoteType') or ''
        return dict(id=i.get('jobReqId') or x['externalPath'], url=i.get('externalUrl') or f'{host}/{site}{x["externalPath"]}', t=i.get('title') or x.get('title', ''),
                    locs=locs, country=(i.get('country') or {}).get('descriptor', ''), remote=bool(re.search(r'remote', rt, re.I) and not re.search(r'hybrid', rt, re.I)),
                    desc=i.get('jobDescription') or '', pub=i.get('startDate') or '', et=i.get('timeType') or '', sal='', dept='')
    with cf.ThreadPoolExecutor(6) as ex:
        return list(ex.map(detail, items[:CAP * 2]))

def f_workable(feed):
    acct = re.search(r'workable\.com/(?:api/v\d/widget/accounts/)?([\w-]+)', feed).group(1)
    d = jget(f'https://apply.workable.com/api/v1/widget/accounts/{acct}?details=true')
    out = []
    for x in d.get('jobs', []):
        locs = [', '.join(v for v in (x.get('city'), x.get('state')) if v)] + [l.get('city') or '' for l in x.get('locations') or [] if not l.get('hidden')]
        cc = x.get('country') or next((l.get('countryCode') or l.get('country') for l in x.get('locations') or []), '')
        out.append(dict(id=x.get('shortcode') or x.get('url'), url=x.get('url') or f"https://apply.workable.com/{acct}/j/{x.get('shortcode')}/", t=x.get('title', ''),
                        locs=locs, country=cc or '', remote=bool(x.get('telecommuting')), desc=x.get('description') or '', pub=x.get('published_on') or x.get('created_at'),
                        et=x.get('employment_type') or '', sal='', dept=x.get('department') or ''))
    return out

def f_bamboohr(feed):
    sub = re.search(r'([\w-]+)\.bamboohr\.com', feed).group(1)
    base = f'https://{sub}.bamboohr.com/careers'
    lst = jget(base + '/list').get('result') or []
    def detail(x):
        loc = x.get('atsLocation') or x.get('location') or {}
        try: jo = (jget(f"{base}/{x['id']}/detail").get('result') or {}).get('jobOpening') or {}
        except Exception: jo = {}
        l2 = jo.get('atsLocation') or jo.get('location') or loc
        return dict(id=str(x['id']), url=jo.get('jobOpeningShareUrl') or f"{base}/{x['id']}", t=jo.get('jobOpeningName') or x.get('jobOpeningName', ''),
                    locs=[', '.join(v for v in (l2.get('city'), l2.get('state')) if v)], country=l2.get('country') or '',
                    remote=bool(x.get('isRemote')) or str(x.get('locationType')) == '1', desc=jo.get('description') or '', pub=jo.get('datePosted') or '',
                    et=jo.get('employmentStatusLabel') or x.get('employmentStatusLabel') or '', sal='', dept=x.get('departmentLabel') or '')
    with cf.ThreadPoolExecutor(6) as ex:
        return list(ex.map(detail, lst[:CAP * 2]))

FETCHERS = {'workday': f_workday, 'workable': f_workable, 'bamboohr': f_bamboohr, 'crawl': f_crawl, 'join': f_join, 'teamtailor': f_teamtailor}
CRAWL_ATS = {'crawl', 'join', 'teamtailor'}

# ---------------------------------------------------------------- detection
BAD_SLUG = {'www', 'app', 'api', 'cdn', 'static', 'assets', 'embed', 'scripts', 'images', 'img', 'media', 'careers', 'career', 'jobs', 'job', 'v0', 'v1',
            'widget', 'js', 'css', 'tracking', 'oneclick-ui', 'support', 'help', 'blog', 'status', 'apply', 'boards', 'posting-api', 'companies', 'de', 'en'}
SIGS = [   # (ats, pattern, number of the group holding the account name or 0, feed builder)
    ('softgarden', r'(https?://[^\s"\'<>]+?/jobs\.feed\.json)', 0, lambda m: m[1]),
    ('greenhouse', r'boards-api(\.eu)?\.greenhouse\.io/v1/boards/([\w-]+)', 2, lambda m: f'https://boards-api{m[1] or ""}.greenhouse.io/v1/boards/{m[2]}/jobs'),
    ('greenhouse', r'(?:boards|job-boards)(\.eu)?\.greenhouse\.io/(?:embed/job_board(?:/js)?\?for=)?([\w-]+)', 2, lambda m: f'https://boards-api{m[1] or ""}.greenhouse.io/v1/boards/{m[2]}/jobs'),
    ('greenhouse', r'(?:boards|job-boards)(\.eu)?\.greenhouse\.io/(?:embed/job_board(?:/js)?\?for=)?([\w-]+)', 2, lambda m: f'https://boards-api.greenhouse.io/v1/boards/{m[2]}/jobs'),
    ('greenhouse', r"greenhouse board '([\w-]+)'", 1, lambda m: f'https://boards-api.greenhouse.io/v1/boards/{m[1]}/jobs'),
    ('lever', r'(?:jobs|api)(\.eu)?\.lever\.co/(?:v0/postings/)?([\w.-]+)', 2, lambda m: f'https://api{m[1] or ""}.lever.co/v0/postings/{m[2]}?mode=json'),
    ('ashby', r'(?:jobs\.ashbyhq\.com|api\.ashbyhq\.com/posting-api/job-board)/([\w.%-]+)', 1, lambda m: f'https://api.ashbyhq.com/posting-api/job-board/{m[1]}'),
    ('personio', r'([\w-]+)\.jobs\.personio\.(de|com)', 1, lambda m: f'https://{m[1]}.jobs.personio.{m[2]}'),
    ('smartrecruiters', r'(?:jobs|careers)\.smartrecruiters\.com/([\w-]+)', 1, lambda m: f'https://api.smartrecruiters.com/v1/companies/{m[1]}/postings'),
    ('smartrecruiters', r'api\.smartrecruiters\.com/v1/companies/([\w-]+)', 1, lambda m: f'https://api.smartrecruiters.com/v1/companies/{m[1]}/postings'),
    ('recruitee', r'([\w-]+)\.recruitee\.com', 1, lambda m: f'https://{m[1]}.recruitee.com/api/offers/'),
    ('softgarden', r'([\w-]+)\.softgarden\.io', 1, lambda m: f'https://{m[1]}.softgarden.io/jobs.feed.json'),
    ('softgarden', r'([\w-]+)\.career\.softgarden\.de', 1, lambda m: f'https://{m[1]}.career.softgarden.de/jobs.feed.json'),
    ('workday', r'([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([\w-]+)', 1, lambda m: f'https://{m[1]}.{m[2]}.myworkdayjobs.com/{m[3]}'),
    ('workable', r'apply\.workable\.com/(?:api/v\d/widget/accounts/)?([\w-]+)', 1, lambda m: f'https://apply.workable.com/{m[1]}'),
    ('bamboohr', r'([\w-]+)\.bamboohr\.com', 1, lambda m: f'https://{m[1]}.bamboohr.com/careers'),
    ('join', r'join\.com/companies/([\w-]+)', 1, lambda m: f'https://join.com/companies/{m[1]}'),
    ('teamtailor', r'([\w-]+)\.teamtailor\.com', 1, lambda m: f'https://{m[1]}.teamtailor.com/jobs'),
]
def fingerprints(text):
    """(ats, feed) candidates found in a blob of text or HTML, in order, without duplicates."""
    out = []
    t = (text or '').replace('\\/', '/')
    for ats, rx, g, mk in SIGS:
        for m in re.finditer(rx, t, re.I):
            if g and m.group(g).lower() in BAD_SLUG: continue
            if ats == 'workday' and m.group(3).lower() in BAD_SLUG | {'wday'}: continue
            out.append((ats, mk(m)))
    return list(dict.fromkeys(out))

def _key(t): return re.sub(r'\W+', ' ', (t or '').lower()).strip()

def evaluate(raw, company, placeholder, is_manual):
    """How well a candidate feed's jobs fit the company: (German jobs, title overlap with the board)."""
    de = [x for x in raw if x.get('t') and x.get('url') and not x.get('keep') and not placeholder.search(x['t']) and not is_manual(x['t'])
          and _german(x.get('locs') or [], x.get('country', ''), x.get('remote', False))]
    old = {_key(j['t']) for j in company.get('jobs') or []}
    return len(de), sum(1 for x in de if _key(x['t']) in old)

def accept(n_de, overlap, n_old, generic=False):
    if n_de == 0: return False
    if generic: return True                                  # JobPostings on the company's own job pages
    return overlap >= 1 or n_old <= 2 or n_de >= 0.3 * n_old

def detect(c, fetchers, placeholder, is_manual, log):
    """Find and verify a readable hiring system for company c. Returns (ats, feed, cfg, raw) or None."""
    jobs = c.get('jobs') or []
    urls = [j['u'] for j in jobs if j.get('u', '').startswith('http')]
    careers = c.get('careers') if (c.get('careers') or '').startswith('http') else ''
    feed0 = c.get('feed') if (c.get('feed') or '').startswith('http') else ''
    tried = set()

    def attempt(ats, feed, cfg=None, generic=False):
        if (ats, feed) in tried or ats not in fetchers: return None
        tried.add((ats, feed))
        try:
            if ats in CRAWL_ATS:
                cfg = cfg or preset(ats, feed)
                cfg = dict(cfg, known=urls if urls and urls[0].startswith(cfg['host']) else [])
                raw = f_crawl(feed, cfg)
            else:
                raw = fetchers[ats](feed)
        except Exception as e:
            log.append(f'{ats} {feed}: {type(e).__name__} {str(e)[:80]}'); return None
        n_de, ov = evaluate(raw, c, placeholder, is_manual)
        log.append(f'{ats} {feed}: {len(raw)} jobs, {n_de} in Germany, {ov} match the board')
        if accept(n_de, ov, len(jobs), generic): return ats, feed, cfg, raw
        return None

    # 1. fingerprints in what we already know (no page loads)
    for ats, feed in fingerprints(' '.join([c.get('ats') or '', feed0, careers] + urls)):
        r = attempt(ats, feed)
        if r: return r
    # 2. fingerprints in the careers page and in one job page
    pages = {}
    for u in dict.fromkeys(x for x in (careers, feed0) if x and not AGGREGATORS.search(x)):
        try: pages[u] = get(u)
        except Exception as e: log.append(f'load {u}: {type(e).__name__}')
    job_pages = [u for u in dict.fromkeys(urls) if u not in (careers, feed0) and not AGGREGATORS.search(u)]
    job_page = job_pages[0] if job_pages else ''
    for u in job_pages[:4]:   # up to 4 job pages, until one carries JobPosting data
        try: pages[u] = get(u)
        except Exception as e: log.append(f'load {u}: {type(e).__name__}'); continue
        if postings(pages[u]): break
    for u, p in pages.items():
        for ats, feed in fingerprints(p):
            r = attempt(ats, feed)
            if r: return r
        if re.search(r'softgarden', p, re.I):
            o = urllib.parse.urlsplit(u)
            r = attempt('softgarden', f'{o.scheme}://{o.netloc}/jobs.feed.json')
            if r: return r
        if re.search(r'teamtailor', p, re.I):
            o = urllib.parse.urlsplit(u)
            cfg = preset('teamtailor', f'{o.scheme}://{o.netloc}/jobs')
            cfg['lists'] = list(dict.fromkeys([u] + cfg['lists']))
            r = attempt('teamtailor', cfg['lists'][0], cfg)
            if r: return r
    # 3. schema.org JobPosting on the job pages: crawl the site
    if any(postings(p) for p in pages.values()) or (not job_page and careers):
        cfg = learn_cfg(urls or [careers], careers or feed0)
        if cfg:
            r = attempt('crawl', cfg['lists'][0], cfg, generic=True)
            if r: return r
        elif urls: log.append('job links too generic to crawl')
    return None

# ---------------------------------------------------------------- description from a job's own page
def _tokens(t): return set(re.findall(r'[a-zäöüß0-9]{3,}', (t or '').lower())) - {'m/w/d', 'mwd', 'all', 'genders', 'der', 'die', 'das', 'and', 'und', 'for', 'the'}
def same_title(a, b):
    ta, tb = _tokens(a), _tokens(b)
    return bool(ta and tb) and len(ta & tb) / min(len(ta), len(tb)) >= 0.6

def desc_from_page(page, url, title):
    """The JobPosting on a job's own page that belongs to this job (title must match), as a raw job, or None."""
    for o in postings(page or ''):
        r = posting_to_raw(o, url)
        if r['t'] and same_title(r['t'], title): return r
    return None
