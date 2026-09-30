# -*- coding: utf-8 -*-
"""Adds the GoatCounter loader to every generated page (site_config.GOATCOUNTER; empty = off). Runs last in build_all.py
and is idempotent: a page that already has the loader is left alone.
GoatCounter is cookieless and stores no personal data. The loader waits for the page's load event plus an idle moment, so
it never competes with first paint. It also sends events, all read from clicks the page already has:
  apply/<company site>     click on an Apply button or link to a company's own application page
  sponsored/<company site> same, for a sponsored placement
  careers/<company site>   click on "All roles on their careers page"
  filter/<id>=<value>      a board filter (city, seniority, type, workplace, language, date, sort) was changed
Free-text search is never sent."""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import OUT
import site_config

MARK = 'data-goatcounter'
LOADER = """<script>(function(){var U=%s,on=0;
function go(){if(on)return;on=1;var s=document.createElement('script');s.async=true;s.src='https://gc.zgo.at/count.js';s.setAttribute('data-goatcounter',U);document.body.appendChild(s)}
function ev(n){try{if(window.goatcounter&&goatcounter.count)goatcounter.count({path:n,event:true})}catch(e){}}
function later(){var f=window.requestIdleCallback;if(f)f(go,{timeout:3000});else setTimeout(go,1500)}
if(document.readyState==='complete')later();else addEventListener('load',later);
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(!a)return;var u;try{u=new URL(a.href,location.href)}catch(x){return}
if(u.protocol.indexOf('http')||u.host===location.host)return;var h=u.hostname.replace(/^www\\./,'');
if(a.id==='cp-careers')ev('careers/'+h);else if(a.hasAttribute('data-spc')&&a.classList.contains('apply'))ev('sponsored/'+h);
else if(a.matches('.apply,.applybtn,.cpapply,.cp-job a[target]'))ev('apply/'+h)},true);
document.addEventListener('change',function(e){var t=e.target;if(t&&t.tagName==='SELECT'&&t.id)ev('filter/'+t.id+'='+String(t.value).slice(0,40))},true);
})()</script>"""

def main():
    url = getattr(site_config, 'GOATCOUNTER', '')
    if not url:
        print('analytics: GOATCOUNTER not set, nothing added'); return
    tag = LOADER % ("'" + url + "'")
    n = 0
    for root, dirs, names in os.walk(OUT):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_')) and d != 'node_modules']
        for nm in names:
            if not nm.endswith('.html'): continue
            p = os.path.join(root, nm); h = open(p, encoding='utf-8').read()
            if MARK in h or '</body>' not in h: continue
            open(p, 'w', encoding='utf-8').write(h.replace('</body>', tag + '</body>', 1)); n += 1
    print('analytics loader added to', n, 'pages')

if __name__ == '__main__': main()
