# -*- coding: utf-8 -*-
"""Tell IndexNow (Bing, Yandex, Seznam, Naver) which pages changed in the last commit."""
import json, subprocess, sys, urllib.request
KEY = '07a7c54ce0fd5631ba35decb8878f8cf'
SITE = 'https://berlinappjobs.com'
files = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], capture_output=True, text=True).stdout.split()
urls = sorted({SITE + '/' + f[:-len('index.html')] for f in files if f.endswith('index.html') and not f.startswith('_build/')})
if not urls:
    print('IndexNow: no changed pages'); sys.exit(0)
body = json.dumps({'host': 'berlinappjobs.com', 'key': KEY, 'keyLocation': f'{SITE}/{KEY}.txt', 'urlList': urls[:10000]}).encode()
req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
try:
    print('IndexNow:', urllib.request.urlopen(req, timeout=30).status, f'{len(urls)} URLs')
except Exception as e:  # never fail the build over a ping
    print('IndexNow failed:', e)
