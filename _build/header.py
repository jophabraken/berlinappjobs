# -*- coding: utf-8 -*-
"""The site header for every static page (job, company, city, role, guide, about, 404 pages).

It is the same header as the job board (templates/board.html): wordmark, live counts, the Jobs / Charts /
Companies / Map / Guides tabs, "Promote your company" and the language flags; on phones the dark bottom bar
with Jobs / Charts / Map / More. On the board those are buttons that switch views; here they are links to
the same views (/#charts, /#studios, /#maptab, /#guides, /#promote), so moving between the board and a job
page never changes the header. Keep the look in sync with the #top / #bottomNav / #moreSheet CSS in board.html.

The flags link to this page's other-language version when there is one, otherwise to the board in that language.
"""
import html as htmlmod

ON, ONC = ' class="on"', ' class="on" aria-current="true"'
def _esc(s): return htmlmod.escape(str(s), quote=True)

LABELS = {
    'en': dict(roles='roles', cos='companies hiring', jobs='Jobs', charts='Charts', companies='Companies', map='Map', guides='Guides',
               promo='Promote your company', more='More'),
    'de': dict(roles='Stellen', cos='Firmen stellen ein', jobs='Jobs', charts='Charts', companies='Unternehmen', map='Karte', guides='Ratgeber',
               promo='Werbung schalten', more='Mehr'),
}
FLAG_EN = ('<svg viewBox="0 0 60 30" width="22" height="15" aria-hidden="true"><rect width="60" height="30" fill="#012169"/>'
           '<path d="M0,0 60,30 M60,0 0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 60,30 M60,0 0,30" stroke="#C8102E" stroke-width="3.5"/>'
           '<path d="M30,0 V30 M0,15 H60" stroke="#fff" stroke-width="10"/><path d="M30,0 V30 M0,15 H60" stroke="#C8102E" stroke-width="6"/></svg>')
FLAG_DE = ('<svg viewBox="0 0 5 3" width="22" height="15" aria-hidden="true"><rect width="5" height="3" fill="#111"/>'
           '<rect y="1" width="5" height="1" fill="#D00"/><rect y="2" width="5" height="1" fill="#FFCE00"/></svg>')
ICONS = {
    'jobs': '<path d="M3 8h18v11H3z"/><path d="M8 8V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    'charts': '<path d="M5 20V11M12 20V4M19 20v-6"/>',
    'map': '<path d="M12 21s7-6.6 7-12a7 7 0 1 0-14 0c0 5.4 7 12 7 12z"/><circle cx="12" cy="9" r="2.4"/>',
    'more': '<path d="M4 7h16M4 12h16M4 17h16"/>',
}

CSS = """
#top{position:sticky;top:env(safe-area-inset-top,0px);z-index:30;background:#131310}
#top .bar{max-width:1140px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;gap:14px;flex-wrap:nowrap}
#top .bar>*{flex-shrink:0}
#top .wordmark{text-decoration:none;display:flex;align-items:stretch;font:900 13px/1 Archivo,sans-serif;letter-spacing:.04em;text-transform:uppercase;white-space:nowrap}
#top .wordmark .wm1{background:#FFD400;color:#131310;padding:7px 9px}
#top .wordmark .wm2{background:#fff;color:#131310;padding:7px 9px;border-left:2.5px solid #131310}
#top .topstats{color:#8A887B;font-size:12.5px;font-variant-numeric:tabular-nums;line-height:1.5}
#top .topstats b{color:#FFD400;font-weight:600}
#top nav.tabs{display:flex;gap:4px;background:#26261F;border-radius:4px;padding:3px}
#top nav.tabs a{color:#B8B5A3;font:600 12.5px/normal Archivo,sans-serif;padding:6px 11px;display:block;border-radius:3px;text-decoration:none}
#top nav.tabs a:hover{color:#F4F1E0}
#top nav.tabs a.on{background:#FFD400;color:#131310}
#top .promo{margin-left:auto;background:#FFD400;color:#131310;border-radius:3px;padding:8px 14px;font:700 12.5px/normal Archivo,sans-serif;white-space:nowrap;text-decoration:none;display:block}
#top .promo:hover{filter:brightness(1.06)}
#top .langtog{display:flex;gap:6px;margin-left:4px}
#top .langtog a{border:1.5px solid #3a3a34;padding:3px;border-radius:4px;line-height:0;opacity:.5;display:block}
#top .langtog a svg{display:block;border-radius:2px}
#top .langtog a.on{opacity:1;border-color:#FFD400}
#top .langtog a:hover{opacity:.85}
#bottomNav,#moreSheet,#moreShade{display:none}
@media (max-width:1080px){#top .topstats{display:none}}
@media (max-width:880px){
  #top .bar{padding:10px 16px}
  #top nav.tabs,#top .promo{display:none}
  #top .langtog{margin-left:auto}
  #top .wordmark{font-size:12px}
  body{padding-bottom:calc(58px + env(safe-area-inset-bottom,0px))}
  #bottomNav{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:44;background:#131310;border-top:1px solid #2c2c24;padding-bottom:env(safe-area-inset-bottom,0px)}
  #bottomNav a,#bottomNav button{flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;background:none;border:0;color:#8A887B;font:700 10px Archivo,sans-serif;padding:8px 2px 7px;cursor:pointer;min-height:52px;text-decoration:none}
  #bottomNav svg{width:23px;height:23px}
  #bottomNav .on{color:#FFD400}
  #moreShade{display:block;position:fixed;inset:0;z-index:46;background:rgba(8,10,22,.5);opacity:0;pointer-events:none;transition:opacity .2s}
  #moreShade.open{opacity:1;pointer-events:auto}
  #moreSheet{display:flex;flex-direction:column;position:fixed;left:0;right:0;bottom:0;z-index:47;background:var(--surface,#fff);border-top:2.5px solid var(--ink,#131310);border-radius:16px 16px 0 0;transform:translateY(101%);transition:transform .26s cubic-bezier(.3,1,.4,1);padding:8px 12px calc(12px + env(safe-area-inset-bottom,0px));box-shadow:0 -12px 40px rgba(0,0,0,.28)}
  #moreSheet.open{transform:none}
  #moreSheet a{display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--line,#131310);color:var(--ink,#131310);font:700 16px Archivo,sans-serif;padding:16px 6px;text-decoration:none}
  #moreSheet a:last-child{border-bottom:0}
  #moreSheet a::after{content:"\\2192";margin-left:auto;color:var(--faint,#75756B)}
}
"""

MORE_JS = ("<script>(function(){var b=document.getElementById('bnMoreBtn'),s=document.getElementById('moreSheet'),h=document.getElementById('moreShade');"
           "if(!b||!s||!h)return;function t(o){s.classList.toggle('open',o);h.classList.toggle('open',o);}"
           "b.addEventListener('click',function(){t(!s.classList.contains('open'));});h.addEventListener('click',function(){t(false);});})();</script>")

def site_header(lang='en', active='jobs', alt=None, n_jobs=0, n_cos=0):
    """Header HTML (goes right after <body>). active: jobs | charts | companies | map | guides | ''.
    alt: {'de': url, 'en': url} for pages that exist in both languages."""
    L = LABELS['de' if lang == 'de' else 'en']
    alt = alt or {}
    tabs = [('jobs', '/#jobs', L['jobs']), ('charts', '/#charts', L['charts']), ('companies', '/#studios', L['companies']),
            ('map', '/#maptab', L['map']), ('guides', '/#guides', L['guides'])]
    tab_html = ''.join(f'<a href="{h}"{ON if k == active else ""}>{_esc(t)}</a>' for k, h, t in tabs)
    def flag(code, svg, name):
        on = code == lang
        href = alt.get(code) or ('#' if on else f'/?lang={code}')
        return f'<a href="{_esc(href)}" hreflang="{code}" aria-label="{name}"{ONC if on else ""}>{svg}</a>'
    top = (f'<div id="top"><div class="bar">'
           f'<a class="wordmark" href="/" aria-label="Berlin App Jobs: all jobs"><span class="wm1">Berlin</span><span class="wm2">App Jobs</span></a>'
           f'<div class="topstats"><b>{n_jobs}</b> {_esc(L["roles"])} &middot; <b>{n_cos}</b> {_esc(L["cos"])}</div>'
           f'<nav class="tabs" aria-label="Berlin App Jobs">{tab_html}</nav>'
           f'<a class="promo" href="/#promote">{_esc(L["promo"])}</a>'
           f'<nav class="langtog" title="Sprache / Language">{flag("en", FLAG_EN, "English")}{flag("de", FLAG_DE, "Deutsch")}</nav>'
           f'</div></div>')
    def bn(k, href, label):
        return (f'<a href="{href}"{ON if k == active else ""}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
                f'stroke-linecap="round" stroke-linejoin="round">{ICONS[k]}</svg><span>{_esc(label)}</span></a>')
    bottom = ('<nav id="bottomNav" aria-label="Primary">' + bn('jobs', '/#jobs', L['jobs']) + bn('charts', '/#charts', L['charts']) + bn('map', '/#maptab', L['map'])
              + f'<button type="button" id="bnMoreBtn"{ON if active in ("companies", "guides") else ""}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              f'stroke-width="1.9" stroke-linecap="round">{ICONS["more"]}</svg><span>{_esc(L["more"])}</span></button></nav>'
              f'<div id="moreShade"></div><nav id="moreSheet" aria-label="{_esc(L["more"])}"><a href="/#studios">{_esc(L["companies"])}</a>'
              f'<a href="/#guides">{_esc(L["guides"])}</a><a href="/#promote">{_esc(L["promo"])}</a></nav>' + MORE_JS)
    return top, bottom
