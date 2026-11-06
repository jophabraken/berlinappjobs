# -*- coding: utf-8 -*-
"""Facts that only this board has, for company and job pages (growth plan, 6 Nov 2026: every indexed page has to say
something the employer's own careers page doesn't). All numbers come from our own data:

  * hiring trend per company: open app roles per day (hiring_history.py)
  * pay transparency: share of a company's ads that state the pay vs. all app companies (salary_detect.py)
  * pay in comparable ads: what ads for the same team state, only when >= PAY_MIN ads give a yearly figure
  * companies hiring for similar teams, and similar jobs at other app companies

Nothing here is an estimate: every figure is counted from ads on the board, and the text says how many."""
import collections, datetime, hashlib, json, math, os, statistics

PAY_MIN = 8          # yearly pay figures needed before we show a team's pay range
TREND_DAYS = 28      # compare with about four weeks ago
TREND_MIN_DAYS = 14  # a trend needs at least two weeks of history
RANK_MIN = 5         # ads we could judge before a company enters the pay-transparency ranking

MDE = ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sept.', 'Okt.', 'Nov.', 'Dez.']
MEN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']
def day_label(iso, de):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day}. {MDE[d.month-1]}" if de else f"{d.day} {MEN[d.month-1]}"
def euro(v, de):
    v = int(round(v / 500.0) * 500)
    return (f"{v:,}".replace(',', '.') + ' €') if de else f"€{v:,}"

def load_history(DATA):
    try: return json.load(open(os.path.join(DATA, 'hiring_history.json'), encoding='utf-8'))
    except Exception: return {}

class Facts:
    def __init__(self, COS, SAL, DATA):
        self.H = load_history(DATA)
        self.days = sorted(self.H)
        self.COS = [c for c in COS if c.get('jobs')]
        # pay transparency per company and on the whole board (ads we could judge only)
        self.pay = {}
        tot_chk = tot_sal = 0
        for c in self.COS:
            chk = [SAL[j['u']] for j in c['jobs'] if j.get('u') in SAL and SAL[j['u']]['checked']]
            s = sum(1 for x in chk if x['sal'])
            self.pay[c['n']] = (s, len(chk)); tot_chk += len(chk); tot_sal += s
        self.board_share = (tot_sal / tot_chk) if tot_chk else None
        ranked = sorted(((s / n, nm) for nm, (s, n) in self.pay.items() if n >= RANK_MIN), reverse=True)
        self.rank = {}; prev = None; place = 0
        for i, (share, nm) in enumerate(ranked):   # equal shares share a place
            if share != prev: place = i + 1; prev = share
            self.rank[nm] = place
        self.ranked_n = len(ranked)
        # yearly pay stated in ads, per team (professional roles only: no internships, working students, apprenticeships)
        self.team_pay = collections.defaultdict(list)
        for c in self.COS:
            for j in c['jobs']:
                x = SAL.get(j.get('u'))
                if x and x['kind'] == 'y' and x['vals'] and x['rt'] == 'pro':
                    self.team_pay[j.get('d')].append(sum(x['vals']) / len(x['vals']))
        # team mix per company, for "companies hiring for similar teams"
        self.mix = {c['n']: collections.Counter(j.get('d') for j in c['jobs'] if j.get('d') and j.get('d') != 'other') for c in self.COS}
        self.zero_pay = sum(1 for s, n in self.pay.values() if n >= RANK_MIN and not s)

    # ---- hiring trend ----
    def series(self, name):
        """[(day, open app roles)] from the first day we tracked the company."""
        out = [(d, self.H[d][name][0]) for d in self.days if name in self.H[d]]
        return out

    def trend(self, name):
        """dict(now, then, then_day, since, series) or None when there isn't two weeks of history."""
        s = self.series(name)
        if len(s) < 2: return None
        last = datetime.date.fromisoformat(s[-1][0]); first = datetime.date.fromisoformat(s[0][0])
        if (last - first).days < TREND_MIN_DAYS: return None
        target = (last - datetime.timedelta(days=TREND_DAYS)).isoformat()
        older = [x for x in s if x[0] <= target]
        then_day, then = (older[-1] if older else s[0])
        return dict(now=s[-1][1], then=then, then_day=then_day, since=s[0][0], series=s)

    @staticmethod
    def direction(t):
        diff = t['now'] - t['then']
        if diff >= 3 and diff >= 0.15 * max(t['then'], 1): return 'up'
        if diff <= -3 and -diff >= 0.15 * max(t['then'], 1): return 'down'
        return 'flat'

    def sparkline(self, name, w=240, h=44):
        t = self.trend(name)
        if not t: return ''
        pts = t['series']; vals = [v for _, v in pts]; hi = max(vals) or 1; lo = min(vals)
        span = max(hi - lo, 1); n = len(pts)
        xy = [(round(4 + (w - 8) * i / max(n - 1, 1), 1), round(h - 6 - (h - 12) * (v - lo) / span, 1)) for i, v in enumerate(vals)]
        path = 'M' + ' L'.join(f'{x} {y}' for x, y in xy)
        return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{vals[0]} → {vals[-1]}">'
                f'<path d="{path}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
                f'<circle cx="{xy[-1][0]}" cy="{xy[-1][1]}" r="4" fill="#FFD400" stroke="currentColor" stroke-width="2"/></svg>')

    def trend_sentence(self, name, short, de):
        t = self.trend(name)
        if not t: return ''
        d = self.direction(t); now, then = t['now'], t['then']; when = day_label(t['then_day'], de)
        if de:
            base = f"{short} hat gerade {now} offene {'App-Rolle' if now == 1 else 'App-Rollen'}"
            return base + {'up': f", {now - then} mehr als am {when} ({then}).", 'down': f", {then - now} weniger als am {when} ({then}).",
                           'flat': f", etwa so viele wie am {when} ({then})."}[d]
        base = f"{short} has {now} open app {'role' if now == 1 else 'roles'} right now"
        return base + {'up': f", {now - then} more than on {when} ({then}).", 'down': f", {then - now} fewer than on {when} ({then}).",
                       'flat': f", about as many as on {when} ({then})."}[d]

    # ---- pay transparency ----
    def pay_sentence(self, name, short, de):
        """Pay transparency against all app companies (the overview above already says how many of its ads state pay)."""
        s, n = self.pay.get(name, (0, 0))
        if not n or self.board_share is None: return ''
        q = round(100 * self.board_share); p = round(100 * s / n)
        rk = self.rank.get(name)
        if de:
            out = f"Über alle App-Firmen auf dem Board nennen {q} % der Anzeigen ein Gehalt, bei {short} sind es {p} %."
            if rk and not s: out += f" Wie {short} nennen {self.zero_pay - 1} der {self.ranked_n} Firmen mit mindestens {RANK_MIN} Anzeigen in keiner Anzeige eins."
            elif rk: out += f" Damit liegt {short} auf Platz {rk} von {self.ranked_n} Firmen mit mindestens {RANK_MIN} Anzeigen."
            return out
        out = f"Across all app companies on the board, {q}% of ads state the pay; at {short} it's {p}%."
        if rk and not s: out += f" Like {short}, {self.zero_pay - 1} of the {self.ranked_n} companies with at least {RANK_MIN} ads state it in none of them."
        elif rk: out += f" That puts {short} at #{rk} of {self.ranked_n} companies with at least {RANK_MIN} ads."
        return out

    def team_pay_range(self, d):
        v = sorted(self.team_pay.get(d) or [])
        if len(v) < PAY_MIN: return None
        q = statistics.quantiles(v, n=4)
        return dict(lo=q[0], hi=q[2], med=statistics.median(v), n=len(v))

    # ---- similar companies ----
    def similar_companies(self, c, k=6):
        me = self.mix.get(c['n'])
        if not me: return []
        if not any(me.values()): return []
        def cos(a, b):
            dot = sum(a[x] * b.get(x, 0) for x in a)
            return dot / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())) or 1)
        city = c.get('city') or ''
        scored = []
        for o in self.COS:
            if o is c or not o.get('_slug'): continue
            if not self.mix[o['n']]: continue
            sc = cos(me, self.mix[o['n']]) + (0.15 if city and o.get('city') == city else 0)
            scored.append((-round(sc, 3), -len(o['jobs']), o['n'], o))
        scored.sort(key=lambda x: x[:3])
        return [x[3] for x in scored[:k]]

def similar_jobs(rec, by_team, k=5):
    """Job pages for the same team at other companies: same level and city first, then a stable per-page shuffle,
    so the links spread over many pages instead of every page pointing at the same five."""
    jb, c = rec['jb'], rec['c']
    d = jb.get('d')
    if not d or d == 'other': return []
    city = c.get('city'); lvl = jb.get('s')
    pool = [r for r in by_team.get(d, []) if r['c']['n'] != c['n']]
    def key(r):
        h = hashlib.md5((rec['slug'] + r['slug']).encode()).hexdigest()
        return (r['jb'].get('s') != lvl or r['c'].get('city') != city, r['jb'].get('s') != lvl, r['c'].get('city') != city, h)
    out, seen = [], set()
    for r in sorted(pool, key=key):
        if r['c']['n'] in seen: continue   # one job per company, more variety
        seen.add(r['c']['n']); out.append(r)
        if len(out) == k: break
    return out
