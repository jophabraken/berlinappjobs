# -*- coding: utf-8 -*-
"""Which apps get a "Who makes this app?" page (/apps/<slug>/ and /en/apps/<slug>/), and their slugs.

Shared by build_programmatic.py (company pages link to app pages), build_jobpages.py (job pages link to the app page)
and build_apps.py (writes the pages). Pure function of board_data.js + data/apps_curated.json, so every step agrees.

An app gets a page when:
  - it has 1M+ installs on Google Play (a proxy for people searching its name), and
  - its name differs from its company's name ("Forge of Empires" by InnoGames). When the names match
    ("Trade Republic" by Trade Republic Bank), the company page already answers the search, and a second page would
    compete with it. apps_curated.json can force an app in ("include") or out ("exclude", e.g. individual developers).
"""
import html, json, os, re, unicodedata

MIN_INSTALLS = 1_000_000
_INST = {'1B+': 1e9, '500M+': 5e8, '100M+': 1e8, '50M+': 5e7, '10M+': 1e7, '5M+': 5e6, '1M+': 1e6, '500K+': 5e5,
         '100K+': 1e5, '50K+': 5e4, '10K+': 1e4, '5K+': 5e3, '1K+': 1e3}
RESERVED = {'spiele', 'games'}   # hub slugs under /apps/

def installs(a): return _INST.get(a.get('i') or '', 0)

def curated(data_dir):
    try: return json.load(open(os.path.join(data_dir, 'apps_curated.json'), encoding='utf-8'))
    except FileNotFoundError: return {'owners': {}, 'game_companies': [], 'include': [], 'exclude': []}

def _ascii(x):
    x = (x.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
          .replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue'))
    return unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode('ascii')

def short_title(t):
    """'Idle Miner Tycoon: Gold Games' -> 'Idle Miner Tycoon'; 'Kleinanzeigen - Marketplace' -> 'Kleinanzeigen'."""
    t = html.unescape(t or '').strip()
    core = re.split(r'\s+[-–—|:]\s+|:\s+|\s+[|]\s*|\s+–', t)[0].strip()
    core = core.rstrip(' :-–|')
    return core if len(core) >= 2 else t

_STOP = {'gmbh', 'ag', 'se', 'mbh', 'co', 'kg', 'kgaa', 'inc', 'ltd', 'llc', 'group', 'holding', 'deutschland', 'verlag',
         'the', 'app', 'apps', 'game', 'games', 'studio', 'studios', 'digital', 'media', 'mobile', 'technologies',
         'software', 'bank', 'und', 'and', 'der', 'die', 'das', 'online', 'germany', 'service', 'services', 'interactive',
         'entertainment', 'stiftung', 'ohg', 'gesellschaft', 'company', 'labs', 'lab', 'the', 'shop', 'news', 'mein', 'meine'}

def _tokens(x):
    return {w for w in re.findall(r'[a-z0-9]+', _ascii(html.unescape(x or '')).lower()) if len(w) >= 4 and w not in _STOP}

def name_differs(app_title, company):
    """True when the app's name says nothing about the company (Forge of Empires / InnoGames)."""
    core = _ascii(short_title(app_title)).lower()
    core_join = re.sub(r'[^a-z0-9]', '', core)
    cn = re.sub(r'[^a-z0-9]', '', _ascii(html.unescape(company.get('n', ''))).lower())
    if core_join and core_join in cn: return False          # "mobile.de" by mobile.de GmbH
    for w in _tokens(company.get('n', '')) | _tokens(company.get('legal', '')):
        if w in core_join: return False                     # "Lounge by Zalando" by Zalando SE
    # short names and acronyms: the app's first word is a word of the company's name ("RTL+" by RTL interactive, "SAP Concur" by SAP SE)
    first = re.findall(r'[a-z0-9]+', core)[:1]
    cwords = set(re.findall(r'[a-z0-9]+', _ascii(html.unescape(company.get('n', '') + ' ' + company.get('legal', ''))).lower()))
    if first and len(first[0]) >= 2 and first[0] in cwords - {'gmbh', 'ag', 'se', 'kg', 'co', 'mein', 'meine', 'my', 'the', 'die', 'der', 'das'}: return False
    return True

def slugify(x):
    x = _ascii(html.unescape(x)).replace('&', ' and ')
    x = re.sub(r'[^a-zA-Z0-9]+', '-', x).strip('-').lower()
    return re.sub(r'-+', '-', x) or 'app'

def app_pages(companies, data_dir):
    """[(company, app, slug)] for every app that gets a page, biggest first. Deterministic."""
    cur = curated(data_dir)
    inc, exc = set(cur.get('include') or []), set(cur.get('exclude') or [])
    rows = []
    for c in companies:
        for a in c.get('apps') or []:
            if not a.get('id') or not a.get('t') or a['id'] in exc: continue
            if a['id'] in inc or (installs(a) >= MIN_INSTALLS and name_differs(a['t'], c)):
                rows.append((c, a))
    rows.sort(key=lambda r: (-installs(r[1]), short_title(r[1]['t']).lower(), r[1]['id']))
    used, out = set(RESERVED), []
    for c, a in rows:
        s = slugify(short_title(a['t']))
        if s in used: s = f"{s}-{slugify(c.get('n', ''))[:24].strip('-')}"   # "rummy" by LITE Games, "rummy-gameduell"
        base, k = s, 2
        while s in used: s = f'{base}-{k}'; k += 1
        used.add(s); out.append((c, a, s))
    return out

def slug_map(companies, data_dir):
    """Play app id -> slug, for links from company and job pages."""
    return {a['id']: s for c, a, s in app_pages(companies, data_dir)}
