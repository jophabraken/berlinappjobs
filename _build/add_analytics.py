# -*- coding: utf-8 -*-
"""Adds the Umami Cloud loader (site_config.UMAMI_ID; empty = off) to every generated page. Runs last in build_all.py and is
idempotent: a page that already has a loader (the current one, or the older GoatCounter one) gets it replaced by the
current one, so a changed loader reaches pages that weren't rebuilt.
Umami is cookieless. The loader waits for the page's load event plus an idle moment, so it never competes with first paint.
It also sends events, all read from clicks the page already has, with the company's site as data:
  apply      click on an Apply button or link to a company's own application page
  sponsored  same, for a sponsored placement
  careers    click on "All roles on their careers page"
Free-text search and filter choices are never sent."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT
import site_config

OPEN = '<script id="baj-stats">'
CURRENT = re.compile(r'<script id="baj-stats">.*?</script>', re.S)
LEGACY = re.compile(r"<script>\(function\(\)\{var U='https://[a-z0-9.-]*goatcounter\.com/count'.*?\}\)\(\)</script>", re.S)
LOADER = OPEN + r"""(function(){var M=__M__,W=__W__,D=__D__,on=0;
function go(){if(on)return;on=1;var s=document.createElement('script');s.async=true;s.src=M;s.setAttribute('data-website-id',W);if(D)s.setAttribute('data-domains',D);document.body.appendChild(s)}
function ev(k,h){try{if(window.umami&&umami.track)umami.track(k,{site:h})}catch(e){}}
function later(){var f=window.requestIdleCallback;if(f)f(go,{timeout:3000});else setTimeout(go,1500)}
if(document.readyState==='complete')later();else addEventListener('load',later);
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var u;try{u=new URL(a.href,location.href)}catch(x){return}
if(u.protocol.indexOf('http')||u.host===location.host)return;var h=u.hostname.replace(/^www\./,'');
if(a.id==='cp-careers')ev('careers',h);else if(a.hasAttribute('data-spc')&&a.classList.contains('apply'))ev('sponsored',h);
else if(a.matches('.apply,.applybtn,.cpapply,.cp-job a[target]'))ev('apply',h)},true);
})()</script>"""

def build():
    uid = getattr(site_config, 'UMAMI_ID', '')
    if not uid: return ''
    rep = {'__M__': json.dumps(getattr(site_config, 'UMAMI_SCRIPT', 'https://cloud.umami.is/script.js')),
           '__W__': json.dumps(uid), '__D__': json.dumps(getattr(site_config, 'UMAMI_DOMAINS', ''))}
    tag = LOADER
    for k, v in rep.items(): tag = tag.replace(k, v)
    return tag

def main():
    tag = build()
    if not tag:
        print('analytics: UMAMI_ID not set, nothing added'); return
    added = replaced = 0
    for root, dirs, names in os.walk(OUT):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_')) and d != 'node_modules']
        for nm in names:
            if not nm.endswith('.html'): continue
            p = os.path.join(root, nm); h = open(p, encoding='utf-8').read()
            if '</body>' not in h: continue
            old = CURRENT.search(h) or LEGACY.search(h)
            if old:
                if old.group(0) == tag: continue
                new = h[:old.start()] + tag + h[old.end():]; replaced += 1
            else:
                new = h.replace('</body>', tag + '</body>', 1); added += 1
            open(p, 'w', encoding='utf-8').write(new)
    print('analytics loader added to', added, 'pages, replaced on', replaced)

if __name__ == '__main__': main()
