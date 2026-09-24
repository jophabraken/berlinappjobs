"""Shared paths and build date for the site generators.
All paths are relative to the repo, so the build runs anywhere (laptop, CI, an agent session)."""
import os, datetime
BUILD = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BUILD)          # the site is served from the repo root (GitHub Pages)
DATA = os.path.join(BUILD, 'data')
TPL = os.path.join(BUILD, 'templates')
OUT = os.environ.get('BAJ_OUT', ROOT)  # override to build into a scratch folder
def _data_date():
    """Date of the last job-data refresh (BOARD.checked, e.g. "22 Sept 2026"), so a rebuild without new data
    doesn't claim pages were updated today."""
    import re
    try:
        head = open(os.path.join(DATA, 'board_data.js'), encoding='utf-8').read(400000)
        m = re.search(r'"checked":\s*"(\d{1,2}) (\w+) (\d{4})"', head)
        mon = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}[m.group(2)[:3].lower()]
        return datetime.date(int(m.group(3)), mon, int(m.group(1))).isoformat()
    except Exception:
        return datetime.date.today().isoformat()
TODAY = os.environ.get('BAJ_DATE') or _data_date()
