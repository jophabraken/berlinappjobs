# -*- coding: utf-8 -*-
"""Hiring history: open app roles per company per data day, kept in _build/data/hiring_history.json.
Company pages show the trend from it ("hiring signal"), which no career page has (growth plan, 6 Nov 2026).

  python3 _build/hiring_history.py              # add/refresh the entry for the current data day (first step of build_all.py)
  python3 _build/hiring_history.py --backfill   # rebuild every past day from the git history of board_data.js

Counts use the app-impact rule (app_roles.app_job) on every day, also on days before that rule existed,
so the trend never shows a fake drop from a rule change. Per company and day we store
[open app roles, roles by team {d: n}, roles that state pay]. Days are the board's "checked" date."""
import datetime, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA, ROOT
import app_roles as AR

STORE = os.path.join(DATA, 'hiring_history.json')
MON = {m: i + 1 for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}

def parse_board(src):
    st = src.index('const BOARD = ') + len('const BOARD = '); nx = src.find('\nconst ', st)
    return json.loads(src[st:nx if nx > 0 else len(src)].strip().rstrip(';'))

def day_of(board):
    m = re.match(r'(\d{1,2}) (\w+) (\d{4})', board.get('checked', ''))
    return datetime.date(int(m.group(3)), MON[m.group(2)[:3].lower()], int(m.group(1))).isoformat() if m else None

def snapshot(board):
    out = {}
    for c in board.get('companies', []):
        jobs = [j for j in (c.get('jobs') or []) if AR.app_job(j.get('t'), c['n'])]
        if not jobs: continue
        teams = {}
        for j in jobs: teams[j.get('d') or 'other'] = teams.get(j.get('d') or 'other', 0) + 1
        out[c['n']] = [len(jobs), teams, sum(1 for j in jobs if (j.get('sal') or '').strip())]
    return out

def load():
    try: return json.load(open(STORE, encoding='utf-8'))
    except Exception: return {}

def save(h):
    h = dict(sorted(h.items()))
    for d in list(h)[:-1]:   # team mix only for the latest day, keeps the file small
        h[d] = {n: [v[0], {}, v[2]] for n, v in h[d].items()}
    json.dump(h, open(STORE, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    h = load()
    if '--backfill' in sys.argv:
        revs = subprocess.run(['git', 'log', '--format=%H', '--', '_build/data/board_data.js'], cwd=ROOT,
                              capture_output=True, text=True).stdout.split()
        for rev in reversed(revs):   # oldest first, so the last commit of a day wins
            src = subprocess.run(['git', 'show', f'{rev}:_build/data/board_data.js'], cwd=ROOT,
                                 capture_output=True, text=True).stdout
            try: b = parse_board(src)
            except Exception: continue
            d = day_of(b)
            if d: h[d] = snapshot(b)
    b = parse_board(open(os.path.join(DATA, 'board_data.js'), encoding='utf-8').read())
    d = day_of(b)
    if d: h[d] = snapshot(b)
    save(h)
    print(f'hiring history: {len(h)} days, latest {d} ({len(h.get(d, {}))} companies)')
