# -*- coding: utf-8 -*-
"""Tell Google about new and removed job pages via the Indexing API (Google's recommended route for JobPosting
URLs: "the Indexing API prompts Googlebot to crawl your page sooner").
Usage (in CI, after the new pages are committed and published): python3 _build/google_indexing.py HEAD~1 HEAD
Compares the /job/ URLs in sitemap-jobs.xml between the two commits: new pages -> URL_UPDATED, removed pages
(which now return 404) -> URL_DELETED. Stays under the default quota of 200 requests a day, new jobs first.
Needs the secret GOOGLE_INDEXING_KEY (a service account JSON key whose e-mail is an Owner of the site in Search
Console, with the Indexing API enabled). Without it, it does nothing. Never fails the build."""
import json, os, re, subprocess, sys

QUOTA = 190   # default quota is 200 publish requests per day; keep a margin for manual use

def job_urls(rev):
    try:
        xml = subprocess.run(['git', 'show', f'{rev}:sitemap-jobs.xml'], capture_output=True, text=True, check=True).stdout
    except Exception:
        return set()
    return set(re.findall(r'<loc>([^<]+/job/[^<]+)</loc>', xml))

def main():
    key = os.environ.get('GOOGLE_INDEXING_KEY', '').strip()
    if not key:
        print('Indexing API: no GOOGLE_INDEXING_KEY secret set, skipping'); return
    old, new = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ('HEAD~1', 'HEAD')
    before, after = job_urls(old), job_urls(new)
    added, removed = sorted(after - before), sorted(before - after)
    todo = [(u, 'URL_UPDATED') for u in added] + [(u, 'URL_DELETED') for u in removed]
    print(f'Indexing API: {len(added)} new, {len(removed)} removed job pages; sending {min(len(todo), QUOTA)}')
    if not todo: return
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(json.loads(key), scopes=['https://www.googleapis.com/auth/indexing'])
    s = AuthorizedSession(creds)
    ok = fail = 0
    for u, t in todo[:QUOTA]:
        r = s.post('https://indexing.googleapis.com/v3/urlNotifications:publish', json={'url': u, 'type': t}, timeout=30)
        if r.status_code == 200: ok += 1
        else:
            fail += 1
            if fail <= 3: print('  failed', r.status_code, u, r.text[:200])
            if r.status_code in (401, 403, 429): break   # bad key, not an owner, or quota used up: stop
    print(f'Indexing API: {ok} sent, {fail} failed, {max(0, len(todo) - QUOTA)} left for a later run')

if __name__ == '__main__':
    try: main()
    except Exception as e: print('Indexing API: skipped after error:', e)
