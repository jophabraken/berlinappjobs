# -*- coding: utf-8 -*-
"""Self-hosted Archivo (the site font) instead of Google Fonts.

Google's stylesheet blocked the first paint (an extra connection to two hosts before anything shows) and
loaded six separate weights. Archivo is a variable font: one small file per character set covers every
weight from 100 to 900. Files live in _build/fonts/ (SIL Open Font License, see OFL.txt) and are copied to
/assets/fonts/ on every build. HEAD goes into each page's <head> in place of the Google Fonts links:
it preloads the Latin file (all English/German text) and declares both @font-face rules.
"""
import hashlib, os, shutil
from paths import OUT, BUILD

SRC = os.path.join(BUILD, 'fonts')
FILES = {'latin': 'archivo-latin-wght-normal.woff2', 'latin-ext': 'archivo-latin-ext-wght-normal.woff2'}
RANGES = {   # unicode-range values from Fontsource / Google Fonts
    'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
    'latin-ext': 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF',
}

def _publish():
    dst = os.path.join(OUT, 'assets', 'fonts'); os.makedirs(dst, exist_ok=True)
    urls = {}
    for key, name in FILES.items():
        src = os.path.join(SRC, name); data = open(src, 'rb').read()
        out = os.path.join(dst, name)
        if not os.path.exists(out) or open(out, 'rb').read() != data:
            shutil.copyfile(src, out)
        urls[key] = f'/assets/fonts/{name}?v={hashlib.sha1(data).hexdigest()[:10]}'
    return urls

URLS = _publish()
FACES = ''.join(f"@font-face{{font-family:'Archivo';font-style:normal;font-weight:100 900;font-display:swap;"
                f"src:url({URLS[k]}) format('woff2');unicode-range:{RANGES[k]}}}" for k in ('latin-ext', 'latin'))
HEAD = (f'<link rel="preload" href="{URLS["latin"]}" as="font" type="font/woff2" crossorigin>'
        f'<style>{FACES}</style>')
