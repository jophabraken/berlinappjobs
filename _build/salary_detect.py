# -*- coding: utf-8 -*-
"""Does a job ad state the pay? Used by the salary transparency index (build_salary.py) and the company pages.

An ad counts when it names a concrete amount in euros tied to pay: an annual, monthly or hourly figure, a range or a
minimum ("ab 2.700 € brutto"), or when the hiring system has a salary field (board_data.js "sal").
Not counted: benefits, budgets, funding rounds, bonuses, discounts, and references to a collective agreement
without an amount (those are counted separately as `tarif`). Checked by hand on ~85 matched/unmatched ads (Oct 2026).

salary_map(COS, DATA) -> {job url: {'sal': bool, 'checked': bool, 'tarif': bool, 'ask': bool, 'kind': 'y'|'m'|'h'|None,
                                   'vals': [floats], 'rt': 'pro'|'student'|'ausbildung'}}
'checked' means we have the full ad text (or a salary field), so the ad can be judged at all."""
import gzip, html, json, os, re

PAYWORD = re.compile(r'(gehalt|gehälter|vergütung|verguetung|salary|salaries|compensation|base pay|pay range|pay band|brutto|gross|jahres|monats|'
                     r'stundenlohn|stundensatz|hourly|per hour|pro stunde|einstieg|entgelt|lohn|verdienst|ote\b|on-target|p\.\s?a\.|pro jahr|per year|'
                     r'per annum|annually|jährlich|monatlich|per month|pro monat|/\s?(monat|month|std|h|jahr|year)\b|vollzeit|full-time|fte)', re.I)
NUM = r'(\d{1,3}(?:[.,\s]\d{3})+(?:,\d{2}|\.\d{2}(?!\d))?|\d{2,3}\s?[kK]|\d{2,6}(?:[.,]\d{1,2})?)'
CUR = r'(€|eur\b|euro\b|eur\.)'
AMOUNT = re.compile(r'(?:' + CUR + r'\s?' + NUM + r'|' + NUM + r'\s?(?:-|–|bis|to)?\s?(?:' + NUM + r')?\s?' + CUR + r')', re.I)
NOT_PAY = re.compile(r'(zuschuss|subsid|budget|rabatt|discount|gutschein|voucher|ticket|jobrad|bike|fahrrad|sachbezug|benefit|essens|lunch|meal|urlaub|'
                     r'vacation|weiterbildung|learning|training|education|umsatz|revenue|funding|raised|finanzierung|investment|investor|kapital|capital|'
                     r'mrd|milliard|billion|mio|million|bonus von|prämie|referral|empfehlung|sport|gym|urban sports|wellpass|egym|kita|pension contribution|'
                     r'altersvorsorge|bav|vwl|vermögenswirksam|home ?office|equipment|ausstattung|hardware|laptop|nettolohnoptimierung|kunden|customers|'
                     r'transaktion|volumen|aum|assets|kredit|loan|darlehen|preis|price|kosten|cost|gebühr|fee|spende|donat)', re.I)
TARIF = re.compile(r'(tarifvertrag|tarifgebunden|tariflich|nach tarif|tvöd|tv-l|tv-?v\b|entgeltgruppe|eg \d|tarif-?gruppe|collective (bargaining|agreement)|haustarif)', re.I)
ASK = re.compile(r'(gehaltsvorstellung|gehaltswunsch|gewünschte[ns]? gehalt|salary expectation|expected salary|desired salary|salary requirement|'
                 r'einkommensvorstellung|vergütungsvorstellung)', re.I)

def text_of(h):
    h = re.sub(r'<(br|/p|/li|/h\d|/div)[^>]*>', '\n', h or '', flags=re.I)
    h = html.unescape(re.sub(r'<[^>]+>', ' ', h))
    h = re.sub(r'[ \t ]+', ' ', h)
    return re.sub(r'(\d),\s(\d{2})\s?(€|eur)', r'\1,\2 \3', h, flags=re.I)   # "16, 89 €" -> "16,89 €"

def _eur(n):
    n = n.strip().replace(' ', '')
    if n[-1:] in 'kK': return float(n[:-1]) * 1000
    n = re.sub(r'^(\d{1,3}(?:[.,]\d{3})+)[.,]\d{2}$', r'\1', n)          # "45.000,00" -> "45.000"
    if re.match(r'^\d{1,3}([.,]\d{3})+$', n): return float(re.sub(r'[.,]', '', n))
    return float(n.replace(',', '.'))

def _kind(v, ctx, near):
    c = ctx.lower()
    c = re.sub(r'(\d+\s*)?(wochenstunden|stunden(-|\s)?(pro|/|die|in der|je)\s?woche|hours? (per|a|/) ?week|stunden-woche)', ' ', c)   # "40 Stunden pro Woche" is not an hourly rate
    if re.search(r'(stunde|std|hour|/h\b|hourly|stundenlohn)', c) and 12 <= v <= 150: return 'h'
    if re.search(r'(monat|month|/m\b|monthly|mtl)', c) and 1200 <= v <= 25000: return 'm'
    if 18000 <= v <= 350000: return 'y'
    if 450 <= v <= 12000 and re.search(r'(vergütung|verguetung|gehalt|salary|lohn|brutto|gross|einstieg|ausbildungsjahr|lehrjahr|monat|month)', near, re.I): return 'm'
    return None

def detect(t):
    """(kind, [values], snippet) for the first pay statement in the ad text, else None."""
    if not t: return None
    for m in AMOUNT.finditer(t):
        nums = [x for x in m.groups() if x and re.match(r'^\d', x)]
        try: vals = [_eur(x) for x in nums]
        except ValueError: continue
        if not vals: continue
        near = t[max(0, m.start() - 160):m.end() + 50]
        if not PAYWORD.search(near): continue
        if NOT_PAY.search(t[max(0, m.start() - 40):m.end() + 25]): continue
        k = _kind(max(vals), t[max(0, m.start() - 110):m.end() + 70], near)
        if k: return k, vals, t[max(0, m.start() - 110):m.end() + 70]
    return None

def role_type(title, seniority=''):
    tl = (title or '').lower()
    if re.search(r'werkstudent|working student', tl): return 'student'
    if re.search(r'ausbildung|azubi|apprentice|duales? studium|dual(e|er)? student|trainee', tl): return 'ausbildung'
    if seniority == 'intern' or re.search(r'werkstudent|working student|praktik|intern\b|internship|studentische|student assistant|minijob|aushilfe|thesis|'
                                          r'abschlussarbeit|bachelorand|masterand', tl): return 'student'
    return 'pro'

def _field_vals(s):
    s = re.sub(r'(?<=\d)[.,](?=\d{3}\b)', '', s or '')                # "€5.000" / "EUR 55,200" -> 5000 / 55200
    nums = re.findall(r'(\d+(?:[.,]\d+)?)\s?([kK])?', s or '')
    v = [float(a.replace(',', '.')) * (1000 if k else 1) for a, k in nums]
    per = 'h' if '/h' in s else ('m' if ('Monat' in s or '/mo' in s) else 'y')
    return per, v

def salary_map(COS, DATA):
    try: D = json.load(gzip.open(os.path.join(DATA, 'descriptions.json.gz'), 'rt', encoding='utf-8'))
    except FileNotFoundError: D = {'jobs': []}
    norm = lambda u: (u or '').split('#')[0].rstrip('/')
    by, by2 = {}, {}
    for x in D.get('jobs') or []:
        u = norm(x.get('url')); by[u] = x; by2[u.split('?')[0]] = x
    out = {}
    for c in COS:
        for jb in c.get('jobs') or []:
            u = norm(jb.get('u')); d = by.get(u) or by2.get(u.split('?')[0])
            t = text_of(d['desc']) if d and d.get('desc') else ''
            full = len(t) >= 400
            h = detect(t) if full else None
            if jb.get('sal'): kind, vals = _field_vals(jb['sal'])
            elif h: kind, vals = h[0], h[1]
            else: kind, vals = None, []
            if kind == 'y' and max(vals or [0]) < 1000: kind, vals = None, []   # e.g. "€40 pauschal pro Einsatz" is no annual pay
            out[jb.get('u')] = dict(sal=bool(jb.get('sal')) or bool(h), checked=full or bool(jb.get('sal')), full=full,
                                     tarif=bool(full and TARIF.search(t)), ask=bool(full and ASK.search(t)), kind=kind, vals=vals,
                                     rt=role_type(jb.get('t'), jb.get('s') or ''))
    return out

def pay_label(info, lang='de', field=None):
    """Short pay text for a job list, e.g. '47.000–65.000 € / Jahr' or '€14–16 / hour'."""
    if field: return field
    v = [x for x in info.get('vals') or [] if x > 0]
    if not v: return ''
    lo, hi = min(v), max(v)
    de = lang == 'de'
    def f(x):
        if x >= 100: s = f"{x:,.0f}"; return s.replace(',', '.') if de else s
        s = f"{x:.2f}".rstrip('0').rstrip('.')
        return s.replace('.', ',') if de else s
    per = {'y': ('Jahr', 'year'), 'm': ('Monat', 'month'), 'h': ('Stunde', 'hour')}.get(info.get('kind'), ('', ''))[0 if de else 1]
    amt = f(lo) if lo == hi else f"{f(lo)}–{f(hi)}"
    return (f"{amt} €" if de else f"€{amt}") + (f" / {per}" if per else '')
