# -*- coding: utf-8 -*-
"""Live numbers for guide texts. A guide writes {{token}} instead of a hard-coded count; build_seo.py replaces it with the
value from the current job data on every build, so a guide can't drift away from the board, the hub pages or
/gehaltstransparenz/ again (it did: "nur rund drei Prozent nennen ein Gehalt" while the index said 8 %).

Only in the body (html) and the FAQ answers, never in title, metaTitle or desc: those may change at most once per
28 days, and a weekly number in them would break that rule. An unknown token stops the build, so a typo can't go live.

Tokens (German guides get 1.234 / 8,4; English guides 1,234 / 8.4):
  {{jobs}} open roles on the board        {{cos}} companies with at least one open role    {{tracked}} companies tracked
  {{remote}} roles marked remote          {{design}}, {{eng}} ... roles per discipline (board codes, see DISC)
  {{city:Berlin}} roles at companies based in that city      {{state:Bayern}} the same per German state
  {{co:N26 AG}} roles of one company (exact board name)
  {{pct:remote}} {{pct:eng}} {{pct:city:Berlin}} share of all roles in %, whole number
  {{en:Berlin}} share of a city's roles advertised in English, whole number
  {{sal}} share of ads that name a salary, one decimal, same sample and rule as /gehaltstransparenz/
  {{month}} month of the job data, e.g. "November 2026"
  {{list:cities:9}} {{list:cos:10}} {{list:remote:10}} {{list:disc}} ready-made <li> rows (company rows as [[Name|Label]] links,
      which build_seo.py turns into company links in articles_src2/3 only: use list tokens there)
"""
import collections, datetime, json, os, re
from paths import DATA, TODAY
import regions, salary_detect
from footer import short_name

_S = {}
_MDE = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
_MEN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
_DISC = {'eng': ('Engineering', 'Engineering'), 'support': ('Ops &amp; Support', 'Ops &amp; support'), 'marketing': ('Marketing', 'Marketing'),
         'people': ('People &amp; Finance', 'People &amp; finance'), 'sales': ('Sales', 'Sales'), 'data': ('Data', 'Data'),
         'product': ('Product', 'Product'), 'design': ('Design', 'Design'), 'health': ('Health', 'Health'), 'other': ('Sonstige', 'Other')}


def _stats():
    if _S: return _S
    s = open(os.path.join(DATA, 'board_data.js'), encoding='utf-8').read()
    i = s.find('const BOARD = '); j = s.find('\nconst ', i + 5)
    cos = json.loads(s[i + len('const BOARD = '):j].rstrip().rstrip(';'))['companies']
    jobs = [(c, jb) for c in cos for jb in (c.get('jobs') or [])]
    sal = salary_detect.salary_map(cos, DATA)
    full = [sal[jb['u']] for c, jb in jobs if jb.get('u') in sal and sal[jb['u']]['full']]
    _S.update(jobs=jobs, n=len(jobs), cos=cos,
              city=collections.Counter(c.get('city') for c, jb in jobs),
              state=collections.Counter(regions.REGION.get(c.get('city')) for c, jb in jobs),
              disc=collections.Counter(jb.get('d') or 'other' for c, jb in jobs),
              co=collections.Counter(c['n'] for c, jb in jobs),
              sal=100 * sum(1 for m in full if m['sal']) / len(full) if full else 0.0)
    return _S


def _num(v, lang):
    return f'{v:,}'.replace(',', '.' if lang == 'de' else ',')


def _pct(v, lang, dec=0):
    t = f'{v:.{dec}f}'
    return t.replace('.', ',') if lang == 'de' else t


def value(tok, lang='de'):
    S = _stats(); n = S['n']
    k, _, arg = tok.partition(':')
    if k == 'jobs': return _num(n, lang)
    if k == 'cos': return _num(sum(1 for c in S['cos'] if c.get('jobs')), lang)
    if k == 'tracked': return _num(len(S['cos']), lang)
    if k == 'remote': return _num(sum(1 for c, jb in S['jobs'] if jb.get('rem')), lang)
    if k in _DISC and not arg: return _num(S['disc'][k], lang)
    if k == 'city': return _num(S['city'][arg], lang)
    if k == 'state': return _num(S['state'][arg], lang)
    if k == 'co':
        if not S['co'][arg]: print(f'live_numbers: WARNING {{{{co:{arg}}}}} is 0 (company gone or not hiring): edit the guide')
        return _num(S['co'][arg], lang)   # never fail here: a weekly refresh must not break the build
    if k == 'pct':
        part = int(value(arg, 'en').replace(',', ''))
        return _pct(100 * part / n if n else 0, lang)
    if k == 'en':
        js = [jb for c, jb in S['jobs'] if c.get('city') == arg]
        return _pct(100 * sum(1 for jb in js if jb.get('lang') == 'en') / len(js) if js else 0, lang)
    if k == 'sal': return _pct(S['sal'], lang, 1)
    if k == 'month':
        d = datetime.date.fromisoformat(TODAY)
        return f"{(_MDE if lang == 'de' else _MEN)[d.month - 1]} {d.year}"
    if k == 'list':
        what, _, top = arg.partition(':'); top = int(top or 10)
        if what == 'cities':
            rows = [(cy, v) for cy, v in S['city'].most_common() if cy][:top]
            return ''.join(f'<li>{cy}: {_num(v, lang)}</li>' for cy, v in rows)
        if what == 'cos':
            city = {c['n']: c.get('city') or '' for c in S['cos']}
            return ''.join(f'<li>[[{nm}|{short_name(nm)}]] ({city[nm]}): {_num(v, lang)}</li>' for nm, v in S['co'].most_common(top))
        if what == 'remote':
            city = {c['n']: c.get('city') or '' for c in S['cos']}
            rem = collections.Counter(c['n'] for c, jb in S['jobs'] if jb.get('rem'))
            word = ('von', 'Stellen remote') if lang == 'de' else ('of', 'roles remote')
            return ''.join(f'<li>[[{nm}|{short_name(nm)}]] ({city[nm]}): {_num(v, lang)} {word[0]} {_num(S["co"][nm], lang)} {word[1]}</li>'
                           for nm, v in rem.most_common(top))
        if what == 'disc':
            return ''.join(f'<li>{_DISC[d][0 if lang == "de" else 1]}: {_num(v, lang)}</li>'
                           for d, v in sorted(S['disc'].items(), key=lambda x: (x[0] == 'other', -x[1])))
    raise KeyError(f'live_numbers: unknown token {{{{{tok}}}}}')


_TOK = re.compile(r'\{\{([^{}]+)\}\}')


def expand(a):
    """Replace {{tokens}} in a guide's html and FAQ answers. Title, metaTitle and desc must not contain any."""
    lang = a.get('lang', 'de')
    for k in ('title', 'metaTitle', 'desc'):
        if _TOK.search(a.get(k) or ''): raise ValueError(f"live_numbers: {{{{...}}}} in {a['slug']} {k}: not allowed (28-day rule)")
    a['html'] = _TOK.sub(lambda m: value(m.group(1).strip(), lang), a['html'])
    if a.get('faq'):
        a['faq'] = [[q, _TOK.sub(lambda m: value(m.group(1).strip(), lang), x)] for q, x in a['faq']]
    return a
