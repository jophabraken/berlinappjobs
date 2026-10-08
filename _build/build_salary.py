# -*- coding: utf-8 -*-
"""Salary transparency index (/gehaltstransparenz/, /en/salary-transparency/) and the list of jobs that state the pay
(/jobs/mit-gehalt/, /en/jobs/with-salary/).

Called from build_programmatic.py (build(globals()) right before the sitemap), like build_apps.py. All numbers are
recomputed from the current job data on every build; the index names no companies (only totals), on purpose.
Detection rules: salary_detect.py. Sample: ads with full text (>= 400 characters)."""
import collections, json, statistics
import salary_detect

CSS = """<style>
.lead{font-size:17px;line-height:1.55;max-width:66ch;margin:4px 0 12px}
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;background:#131310;color:#F7F6EF;border-radius:10px;margin:18px 0 6px;overflow:hidden}
.tiles div{padding:18px 16px;border-left:1px solid #2E2E29;display:grid;gap:6px;align-content:start}.tiles div:first-child{border-left:0}
.tiles b{font:900 clamp(30px,4.4vw,44px)/1 Archivo,sans-serif;color:#FFD400;font-variant-numeric:tabular-nums}
.tiles span{font-size:13.5px;line-height:1.35}.tiles small{font-size:11.5px;color:#B9B6A6}
@media (max-width:700px){.tiles{grid-template-columns:repeat(2,minmax(0,1fr))}.tiles div{border-left:0;border-top:1px solid #2E2E29}.tiles div:nth-child(-n+2){border-top:0}}
.bars{display:grid;gap:7px;margin:10px 0 4px}
.bar{display:grid;grid-template-columns:minmax(110px,200px) minmax(0,1fr) 112px;gap:12px;align-items:center;font-size:14.5px}
.bar .l{font-weight:600;min-width:0}
.bar .tr{position:relative;height:20px;background:#EEECDF;border-radius:0 4px 4px 0}
.bar .fl{position:absolute;inset:0 auto 0 0;background:#131310;border-radius:0 4px 4px 0;min-width:2px}
.bar.hi .fl{background:#FFD400;box-shadow:inset 0 0 0 1.5px #131310}.bar.ext .fl{background:#9A988C}
.bar .v{font-weight:700;font-size:13.5px;text-align:right;font-variant-numeric:tabular-nums}.bar .v small{display:block;font-weight:400;font-size:11.5px;color:var(--faint)}
.avg{position:absolute;top:-4px;bottom:-4px;border-left:2px dashed #B8261B}
@media (max-width:600px){.bar{grid-template-columns:minmax(0,1fr) 92px}.bar .l{grid-column:1/-1}}
.key{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted)}.key span{display:inline-flex;gap:7px;align-items:center}
.sw{width:14px;height:10px;border-radius:2px;background:#131310;display:inline-block}.sw.hi{background:#FFD400;box-shadow:inset 0 0 0 1.5px #131310}.sw.ext{background:#9A988C}.sw.avg{height:0;border-top:2px dashed #B8261B;background:none;width:16px}
.cells{display:grid;grid-template-columns:repeat(auto-fill,minmax(13px,1fr));gap:3px;max-width:640px;margin:10px 0}
.cells i{aspect-ratio:1;border:1.5px solid #131310;border-radius:2px;display:block}.cells i.on{background:#FFD400}
.tl{list-style:none;margin:10px 0 0 6px;padding:0;border-left:3px solid #131310}
.tl li{position:relative;padding:0 0 16px 20px}.tl li:before{content:"";position:absolute;left:-9px;top:4px;width:15px;height:15px;border-radius:50%;background:var(--bg);border:3px solid #131310}
.tl li.now:before{background:#FFD400}.tl .w{display:block;font-size:12px;font-weight:700;color:var(--faint);text-transform:uppercase;letter-spacing:.05em}
table.st{border-collapse:collapse;width:100%;font-size:14px;margin-top:8px}.st th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--faint);border-bottom:2px solid #131310;padding:6px 8px}
.st td{border-bottom:1px solid #DEDBCB;padding:8px;font-variant-numeric:tabular-nums}.st .r{text-align:right}
.faq h3{font-size:16px;margin:18px 0 4px}.faq p{margin:0 0 6px;max-width:68ch}
.pay{flex:none;font-weight:800;font-size:13px;white-space:nowrap;background:#FFD400;border:1.5px solid #131310;border-radius:6px;padding:5px 9px;font-variant-numeric:tabular-nums}
@media (max-width:560px){.row{flex-wrap:wrap}.pay{order:3}}
</style>"""

INDEED = [('United Kingdom', 'Großbritannien', 56.0), ('Netherlands', 'Niederlande', 48.0), ('France', 'Frankreich', 43.0),
          ('Ireland', 'Irland', 39.0), ('Italy', 'Italien', 36.0), ('Germany, all sectors', 'Deutschland, alle Branchen', 12.5),
          ('Germany, IT', 'Deutschland, IT', 5.0)]   # Indeed Deutschland press release, 19 May 2026


def build(G):
    SITE, TODAY, esc, head, jsonld, breadcrumb = G['SITE'], G['TODAY'], G['esc'], G['head'], G['jsonld'], G['breadcrumb']
    FOOT, FOOT_EN, JOBPAGE, DISC, ROLE_EN, COS = G['FOOT'], G['FOOT_EN'], G['JOBPAGE'], G['DISC'], G['ROLE_EN'], G['COS']
    MONTH_DE, MONTH_EN, short_name, OUT = G['MONTH_DE'], G['MONTH_EN'], G['short_name'], G['OUT']
    import os
    SAL = G['SAL']
    rows = []
    for c in COS:
        for jb in c.get('jobs') or []:
            m = SAL.get(jb.get('u'))
            if m and m['full']: rows.append(dict(m, c=c, jb=jb, d=jb.get('d') or 'other', s=jb.get('s') or '', lang=jb.get('lang') or '', city=c.get('city') or ''))
    if len(rows) < 200: print('salary index: too few ads with text, skipped'); return []
    def cnt(rs): return len(rs), sum(r['sal'] for r in rs)
    def share(rs): n, s = cnt(rs); return 100 * s / n if n else 0
    pro = [r for r in rows if r['rt'] == 'pro']
    by = lambda rs, k: {key: [r for r in rs if r[k] == key] for key in {r[k] for r in rs}}
    disc = {k: v for k, v in by(pro, 'd').items() if len(v) >= 30}
    sen = {k: v for k, v in by(pro, 's').items() if len(v) >= 30 and k in ('junior', 'mid', 'senior', 'lead')}
    lng = {k: v for k, v in by(pro, 'lang').items() if k in ('de', 'en') and len(v) >= 30}
    cities = {k: v for k, v in by(rows, 'city').items() if k in ('Berlin', 'München', 'Hamburg', 'Köln', 'Düsseldorf', 'Frankfurt am Main', 'Stuttgart') and len(v) >= 60}
    rtypes = by(rows, 'rt')
    ask = [r for r in rows if r['ask']]; ask_sal = sum(r['sal'] for r in ask)
    tarif = sum(1 for r in rows if r['tarif'] and not r['sal'])
    co = collections.defaultdict(list)
    for r in rows: co[id(r['c'])].append(r)
    c5 = [v for v in co.values() if len(v) >= 5]
    c5_none, c5_all = sum(1 for v in c5 if not any(r['sal'] for r in v)), sum(1 for v in c5 if all(r['sal'] for r in v))
    lv = collections.defaultdict(list)
    for r in pro:
        if r['sal'] and r['kind'] == 'y':
            v = [x for x in r['vals'] if 15000 <= x <= 400000]
            if v: lv[r['d']].append((min(v), max(v))); lv['all'].append((min(v), max(v)))
    levels = {k: dict(n=len(v), lo=statistics.median(a for a, b in v), hi=statistics.median(b for a, b in v)) for k, v in lv.items() if len(v) >= 8}
    ranged = sum(1 for a, b in lv['all'] if b > a)
    N, S = cnt(rows); P_all, P_pro = share(rows), share(pro)
    eng = disc.get('eng', [])
    out_urls = []

    def pf(x, de): s = f"{x:.1f}"; return (s.replace('.', ',') + ' %') if de else s + '%'
    def nf(x, de): return f"{x:,}".replace(',', '.') if de else f"{x:,}"
    def eur(x, de): x = round(x / 500) * 500; return (f"{x:,.0f}".replace(',', '.') + ' €') if de else f"€{x:,.0f}"
    def bars(items, mx, de, avg=None):
        h = '<div class="bars">'
        for it in items:
            lab, rs, cls = it[:3]
            if isinstance(rs, (int, float)): p, sub = rs, (it[3] if len(it) > 3 else ('Indeed, Mai 2026' if de else 'Indeed, May 2026'))
            else: n, s = cnt(rs); p, sub = 100 * s / n, f"{nf(s, de)} / {nf(n, de)}"
            h += (f'<div class="bar {cls}"><span class="l">{esc(lab)}</span><span class="tr"><span class="fl" style="width:{max(0.4, 100 * p / mx):.1f}%"></span>'
                  + (f'<span class="avg" style="left:{100 * avg / mx:.1f}%"></span>' if avg is not None else '') + f'</span><span class="v">{pf(p, de)}<small>{sub}</small></span></div>')
        return h + '</div>'
    ROLE_DE = {k: v[1] for k, v in DISC.items()}; ROLE_DE['other'] = 'Sonstige'
    def rname(k, de): return (ROLE_DE.get(k, k) if de else {**ROLE_EN, 'other': 'Other roles'}.get(k, k))

    # ================= the index =================
    def index(lang):
        de = lang == 'de'; T = lambda a, b: a if de else b
        url = SITE + T('/gehaltstransparenz/', '/en/salary-transparency/')
        alt = {'de': SITE + '/gehaltstransparenz/', 'en': SITE + '/en/salary-transparency/'}
        jobs_url = T('/jobs/mit-gehalt/', '/en/jobs/with-salary/')
        title = T(f"Gehaltstransparenz-Index: {pf(P_all, de)} der Stellenanzeigen nennen ein Gehalt",
                  f"Salary Transparency Index: {pf(P_all, de)} of App Job Ads Show Pay")
        if len(title) > 70: title = T("Gehaltstransparenz in Stellenanzeigen: der Index für App-Firmen", "Salary Transparency in Job Ads: App Companies Index")
        desc = T(f"Nur {pf(P_all, de)} von {nf(N, de)} Stellenanzeigen bei {len(co)} deutschen App-Firmen nennen ein Gehalt, in der Entwicklung {pf(share(eng), de)}. Auswertung nach Bereich, Stadt und Seniorität, Stand {TODAY}.",
                 f"Only {pf(P_all, de)} of {nf(N, de)} job ads at {len(co)} German app companies state the pay, {pf(share(eng), de)} in engineering. Broken down by role, city and seniority, as of {TODAY}.")
        low = sorted(disc.items(), key=lambda kv: share(kv[1]))[:2]
        hi_ = sorted(disc.items(), key=lambda kv: -share(kv[1]))[:2]
        ab = rtypes.get('ausbildung', []); ratio = share(ab) / P_pro if P_pro and ab else 0
        b = f'<nav class="crumb"><a href="/">Home</a> / {T("Gehaltstransparenz", "Salary transparency")}</nav>'
        b += f'<p class="eyebrow" style="font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin:14px 0 0">{T("Gehaltstransparenz-Index App-Jobs", "App Jobs Salary Transparency Index")} · {T("Stand", "As of")} {TODAY}</p>'
        b += f'<h1>{T(f"Nur {pf(P_all, de)} der Stellenanzeigen bei App-Firmen nennen ein Gehalt", f"Only {pf(P_all, de)} of job ads at app companies say what the job pays")}</h1>'
        b += ('<p class="lead">' + T(f"Wir haben {nf(N, de)} aktuelle Stellenanzeigen von {len(co)} Unternehmen hinter Deutschlands meistgeladenen Apps ausgewertet, direkt aus deren Bewerbungssystemen. {nf(S, de)} davon nennen ein Gehalt, eine Gehaltsspanne oder einen Stundenlohn.",
                                     f"We read {nf(N, de)} live job ads from {len(co)} companies behind Germany's most-downloaded apps, straight from their own hiring systems. {nf(S, de)} of them name a salary, a pay range or an hourly rate.") + '</p>')
        n_eng, s_eng = cnt(eng); n_pro, s_pro = cnt(pro)
        b += ('<div class="tiles">'
              + f'<div><b>{pf(P_all, de)}</b><span>{T("aller Anzeigen nennen ein Gehalt", "of all ads state the pay")}</span><small>{nf(S, de)} / {nf(N, de)}</small></div>'
              + f'<div><b>{pf(P_pro, de)}</b><span>{T("bei Fach- und Führungskräften", "for professional roles")}</span><small>{T("ohne Ausbildung und Studentenjobs", "without apprenticeships and student jobs")}</small></div>'
              + (f'<div><b>{pf(share(eng), de)}</b><span>{T("in der Software-Entwicklung", "in engineering")}</span><small>{s_eng} / {n_eng}</small></div>' if eng else '')
              + (f'<div><b>{round(100 * (len(ask) - ask_sal) / len(ask))}{T(" %", "%")}</b><span>{T("der Anzeigen, die nach Ihrer Gehaltsvorstellung fragen, nennen selbst keine Zahl", "of ads asking for your salary expectation give no number themselves")}</span><small>{len(ask) - ask_sal} / {len(ask)}</small></div>' if ask else '')
              + '</div>')
        # by role
        b += f'<h2>{T(f"Am seltensten in {rname(low[0][0], de)} und {rname(low[1][0], de)}", f"Least often in {rname(low[0][0], de).lower()} and {rname(low[1][0], de).lower()}")}</h2>'
        b += ('<p>' + T(f"Unter den Fach- und Führungsrollen nennen {rname(hi_[0][0], de)} ({pf(share(hi_[0][1]), de)}) und {rname(hi_[1][0], de)} ({pf(share(hi_[1][1]), de)}) am häufigsten ein Gehalt. Am seltensten {rname(low[0][0], de)} mit {pf(share(low[0][1]), de)}.",
                                f"Among professional roles, {rname(hi_[0][0], de).lower()} ({pf(share(hi_[0][1]), de)}) and {rname(hi_[1][0], de).lower()} ({pf(share(hi_[1][1]), de)}) state the pay most often. {rname(low[0][0], de)} ads least often, at {pf(share(low[0][1]), de)}.") + '</p>')
        b += f'<div class="key"><span><i class="sw"></i>{T("Anteil mit Gehaltsangabe", "Share that state the pay")}</span><span><i class="sw avg"></i>{T("Durchschnitt Fach- und Führungsrollen", "Average for professional roles")}</span></div>'
        mx = max(25, round(max(share(v) for v in disc.values()) / 5 + 1) * 5)
        b += bars([(rname(k, de), v, 'hi' if k in ('eng', 'product', 'design') else '') for k, v in sorted(disc.items(), key=lambda kv: -share(kv[1]))], mx, de, avg=P_pro)
        b += f'<p class="secnote">{T(f"Fach- und Führungsrollen (n = {nf(n_pro, de)}), Bereich aus dem Jobtitel. Bereiche mit weniger als 30 Anzeigen sind ausgeblendet.", f"Professional roles (n = {nf(n_pro, de)}), role from the job title. Groups under 30 ads are left out.")}</p>'
        # apprenticeships
        if ab:
            b += f'<h2>{T(f"Azubis sehen ihr Gehalt {ratio:.0f}-mal so oft wie Berufserfahrene", f"Apprentices see their pay {ratio:.0f} times as often as professionals")}</h2>'
            b += '<p>' + T("Ausbildungsvergütungen sind oft tariflich geregelt und stehen Jahr für Jahr in der Anzeige („1. Ausbildungsjahr: 1.139 €“). Sobald ein Job Studium oder Erfahrung verlangt, verschwindet die Zahl.",
                           "Training pay is often set by collective agreements and printed year by year (\"1st year: €1,139\"). Once a job needs a degree or experience, the number disappears.") + '</p>'
            RT = {'ausbildung': T('Ausbildung und duales Studium', 'Apprenticeships and dual study'), 'student': T('Werkstudenten und Praktika', 'Working students and interns'), 'pro': T('Fach- und Führungsrollen', 'Professional roles')}
            b += bars([(RT[k], rtypes[k], 'hi' if k == 'ausbildung' else '') for k in ('ausbildung', 'student', 'pro') if k in rtypes], 50, de)
        # ask vs tell
        if ask:
            b += f'<h2>{T("Sie wollen Ihre Zahl. Ihre eigene nennen sie nicht.", "They want your number. They keep theirs.")}</h2>'
            b += '<p>' + T(f"{len(ask)} Anzeigen bitten um Ihre Gehaltsvorstellung. Nur {ask_sal} davon nennen selbst ein Gehalt. Jedes Kästchen ist eine dieser Anzeigen, gelb heißt: mit Gehaltsangabe.",
                           f"{len(ask)} ads ask applicants for their salary expectation. Only {ask_sal} of them state a salary themselves. Each square is one of those ads; yellow means it states the pay.") + '</p>'
            b += f'<div class="cells" role="img" aria-label="{len(ask)} / {ask_sal}">' + ''.join(f'<i class="{"on" if i < ask_sal else ""}"></i>' for i in range(len(ask))) + '</div>'
        # companies, totals only
        b += f'<h2>{T(f"{c5_none} von {len(c5)} Unternehmen nennen in keiner Anzeige ein Gehalt", f"{c5_none} of {len(c5)} companies state the pay in none of their ads")}</h2>'
        b += '<p>' + T(f"Gezählt sind Unternehmen mit mindestens fünf ausgewerteten Anzeigen. Nur {c5_all} nennen in jeder Anzeige ein Gehalt, {len(c5) - c5_none - c5_all} in einem Teil davon. Ob ein bestimmtes Unternehmen Gehälter nennt, steht auf seiner Unternehmensseite.",
                       f"Companies with at least five ads in the sample. Only {c5_all} state the pay in every ad, {len(c5) - c5_none - c5_all} in some of them. Each company page shows how often that company states the pay.") + f' <a href="{T("/companies/", "/en/companies/")}">{T("Alle Unternehmen", "All companies")} &rarr;</a></p>'
        cs = lambda k: T(f"{k} von {len(c5)} Firmen", f"{k} of {len(c5)} companies")
        b += bars([(T('In keiner Anzeige', 'In no ad'), 100 * c5_none / len(c5), '', cs(c5_none)), (T('In einem Teil', 'In some ads'), 100 * (len(c5) - c5_none - c5_all) / len(c5), '', cs(len(c5) - c5_none - c5_all)), (T('In jeder Anzeige', 'In every ad'), 100 * c5_all / len(c5), 'hi', cs(c5_all))], 100, de)
        # europe
        b += f'<h2>{T("Deutschland ist Europas Schlusslicht, App-Firmen liegen noch darunter", "Germany trails Europe, and app companies sit below even that")}</h2>'
        b += '<p>' + T("Laut Indeed nannten im Mai 2026 nur 12,5 % der Stellenanzeigen in Deutschland ein Gehalt, in der IT 5 %. In Großbritannien sind es 56 %.",
                       "According to Indeed, only 12.5% of job ads in Germany stated a salary in May 2026, and 5% in IT. In the UK it is 56%.") + '</p>'
        b += f'<div class="key"><span><i class="sw ext"></i>Indeed Hiring Lab, {T("alle Anzeigen", "all job ads")}</span><span><i class="sw hi"></i>{T("Dieser Index (App-Firmen)", "This index (app companies)")}</span></div>'
        b += bars([(e if not de else d, v, 'ext') for e, d, v in INDEED] + [(T('App-Firmen, alle Anzeigen', 'App companies, all ads'), rows, 'hi'), (T('App-Firmen, Fach- und Führungsrollen', 'App companies, professional roles'), pro, 'hi')], 60, de)
        b += f'<p class="secnote">{T("Indeed zählt Anzeigen auf seiner Plattform, wir die Anzeigen in den Bewerbungssystemen der Unternehmen. Index Research misst mit breiterer Definition rund 22 %. Der Vergleich ist daher eine Größenordnung, kein exakter Abstand.", "Indeed counts ads on its platform; we count ads in the companies’ own hiring systems. Index Research measures about 22% with a broader definition, so read the comparison as an order of magnitude, not an exact gap.")}</p>'
        # seniority, language, city
        SEN = {'junior': 'Junior', 'mid': T('Mid-Level', 'Mid-level'), 'senior': 'Senior', 'lead': T('Lead und Head of', 'Lead and head of')}
        b += f'<h2>{T("Seniorität, Sprache, Stadt", "Seniority, language, city")}</h2>'
        b += bars([(SEN[k], sen[k], '') for k in ('junior', 'mid', 'senior', 'lead') if k in sen], 15, de)
        if len(lng) == 2:
            pe, pd = share(lng['en']), share(lng['de'])
            b += '<p>' + T(f"Englischsprachige Anzeigen nennen {'genauso oft' if abs(pe - pd) < 1 else ('öfter' if pe > pd else 'seltener')} ein Gehalt {'wie' if abs(pe - pd) < 1 else 'als'} deutsche ({pf(pe, de)} gegenüber {pf(pd, de)}, Fach- und Führungsrollen).",
                           f"English-language ads state the pay {'as often as' if abs(pe - pd) < 1 else ('more often than' if pe > pd else 'less often than')} German ones ({pf(pe, de)} vs {pf(pd, de)}, professional roles).") + '</p>'
        CITY_EN = {'München': 'Munich', 'Köln': 'Cologne', 'Frankfurt am Main': 'Frankfurt'}
        if cities:
            b += bars([(k if de else CITY_EN.get(k, k), v, 'hi' if k == 'Berlin' else '') for k, v in sorted(cities.items(), key=lambda kv: -share(kv[1]))], 25, de)
            b += f'<p class="secnote">{T("Alle Anzeigen, nach Sitz des Unternehmens. Städte mit mindestens 60 Anzeigen. Ein großer Arbeitgeber kann den Wert einer Stadt stark bewegen.", "All ads, by the company’s headquarters city. Cities with 60+ ads. One large employer can move a city’s number a lot.")}</p>'
        # published ranges
        if 'all' in levels:
            L = levels['all']
            lo_s, hi_s = eur(L['lo'], de), eur(L['hi'], de)
            b += f'<h2>{T(f"Die typische veröffentlichte Spanne: {lo_s} bis {hi_s}", f"The typical published range: {lo_s} to {hi_s}")}</h2>'
            b += '<p>' + T(f"Median über {L['n']} Anzeigen für Fach- und Führungsrollen mit Jahresgehalt. {round(100 * ranged / L['n'])} % geben eine Spanne statt einer einzelnen Zahl an.",
                           f"Median across {L['n']} professional ads with an annual figure. {round(100 * ranged / L['n'])}% give a range rather than a single number.") + '</p>'
            b += (f'<div style="overflow-x:auto"><table class="st"><thead><tr><th>{T("Bereich", "Role")}</th><th class="r">{T("Anzeigen", "Ads")}</th><th class="r">{T("Median von", "Median low")}</th><th class="r">{T("Median bis", "Median high")}</th></tr></thead><tbody>'
                  + ''.join(f'<tr><td>{"<b>" + T("Alle Fach- und Führungsrollen", "All professional roles") + "</b>" if k == "all" else esc(rname(k, de))}</td><td class="r">{v["n"]}</td><td class="r">{eur(v["lo"], de)}</td><td class="r">{eur(v["hi"], de)}</td></tr>'
                            for k, v in sorted(levels.items(), key=lambda kv: (kv[0] != 'all', -kv[1]['n'])) if v['hi'] > v['lo'] or k == 'all')
                  + '</tbody></table></div>')
            b += f'<p class="secnote">{T("Kleine Stichproben. Das zeigt, was Unternehmen veröffentlichen, nicht was der Markt zahlt.", "Small samples. This shows what companies publish, not what the market pays.")}</p>'
        # the law
        b += f'<h2>{T("Ein Gesetz kommt. Ins Inserat muss das Gehalt wohl trotzdem nicht.", "A law is coming. It probably won’t force the number into the ad.")}</h2>'
        b += '<p>' + T("Nach der EU-Entgelttransparenzrichtlinie (2023/970) haben Bewerber Anspruch auf Informationen zum Einstiegsgehalt oder zur Gehaltsspanne: in der Stellenanzeige, vor dem Vorstellungsgespräch oder auf anderem Weg. Nach dem bisherigen Gehalt dürfen Arbeitgeber nicht mehr fragen.",
                       "Under the EU Pay Transparency Directive (2023/970), applicants have a right to the starting pay or its range: in the job ad, before the interview or in another way. Employers may no longer ask about your current salary.") + '</p>'
        b += ('<ol class="tl">'
              + f'<li><span class="w">{T("Juni 2023", "Jun 2023")}</span><b>{T("Richtlinie (EU) 2023/970 tritt in Kraft", "Directive (EU) 2023/970 enters into force")}</b></li>'
              + f'<li><span class="w">{T("7. Juni 2026", "7 Jun 2026")}</span><b>{T("Umsetzungsfrist. Deutschland verpasst sie.", "Deadline for national law. Germany misses it.")}</b></li>'
              + f'<li class="now"><span class="w">{T("Herbst 2026", "Autumn 2026")}</span><b>{T("Noch kein deutscher Gesetzentwurf veröffentlicht", "No German draft law published yet")}</b></li>'
              + f'<li><span class="w">{T("Erwartet 2027", "Expected 2027")}</span><b>{T("Deutsches Gesetz in Kraft, Datum offen", "German law in force, date not confirmed")}</b></li></ol>')
        if de: b += '<p>Was das für Ihre Bewerbung heißt und wie Sie nach dem Gehaltsband fragen: <a href="/guides/gehaltstransparenz-app-jobs-2026/">Gehalt in der Stellenanzeige: Rechtslage und Tipps</a>.</p>'
        b += f'<p class="secnote">{T("Keine Rechtsberatung. Quellen: EUR-Lex; hib Bundestag, 16.7.2026; Personalwirtschaft, 19.6.2026.", "Not legal advice. Sources: EUR-Lex; Bundestag hib, 16 Jul 2026; Personalwirtschaft, 19 Jun 2026.")}</p>'
        # method
        b += f'<h2>{T("Methodik", "Method")}</h2>'
        b += '<p>' + T(f"Alle aktuellen Stellenanzeigen der Unternehmen hinter Deutschlands meistgeladenen Apps, direkt aus ihren Bewerbungssystemen (Greenhouse, Personio, Ashby, SmartRecruiters, Workday und Karriereseiten), Stand {TODAY}. Ausgewertet sind {nf(N, de)} Anzeigen mit vollständigem Text, höchstens 60 pro Unternehmen. Als Gehaltsangabe zählt ein konkreter Euro-Betrag zum Gehalt: Jahres-, Monats- oder Stundenwert, Spanne oder Mindestbetrag („ab 2.700 € brutto“), oder ein Gehaltsfeld im Bewerbungssystem. Benefits, Budgets und Boni zählen nicht, ein Verweis auf einen Tarifvertrag ohne Betrag auch nicht (weitere {tarif} Anzeigen). Die Erkennung ist automatisch und wurde an Stichproben von Hand geprüft. Anzeigen ohne vollständigen Text sind nicht enthalten.",
                       f"All live job ads at the companies behind Germany's most-downloaded apps, read from their hiring systems (Greenhouse, Personio, Ashby, SmartRecruiters, Workday and career pages), as of {TODAY}. We analysed {nf(N, de)} ads with full text, at most 60 per company. An ad counts when it names a concrete euro amount for pay: annual, monthly or hourly, a range or a minimum (\"ab 2.700 € brutto\"), or a salary field in the hiring system. Benefits, budgets and bonuses don't count, and neither does a reference to a collective agreement without an amount (another {tarif} ads). Detection is automatic and was checked by hand on samples. Ads without full text are not included.") + '</p>'
        # FAQ
        faq = [(T("Wie viele Stellenanzeigen nennen ein Gehalt?", "How many job ads state a salary?"),
                T(f"Bei deutschen App-Firmen nennen {pf(P_all, de)} der Stellenanzeigen ein Gehalt, bei Fach- und Führungsrollen {pf(P_pro, de)} (Stand {TODAY}). Laut Indeed sind es in ganz Deutschland 12,5 % (Mai 2026).",
                  f"At German app companies {pf(P_all, de)} of job ads state a salary, {pf(P_pro, de)} for professional roles (as of {TODAY}). Indeed puts all of Germany at 12.5% (May 2026).")),
               (T("Muss das Gehalt in der Stellenanzeige stehen?", "Does the salary have to be in the job ad?"),
                T("In Deutschland bisher nicht. Die EU-Entgelttransparenzrichtlinie verlangt, dass Bewerber das Einstiegsgehalt oder die Spanne erfahren, erlaubt dafür aber auch den Weg vor dem Vorstellungsgespräch. In Österreich ist eine Gehaltsangabe in Inseraten seit 2011 Pflicht.",
                  "Not in Germany so far. The EU Pay Transparency Directive requires that applicants learn the starting pay or range, but also allows sharing it before the interview. In Austria a salary in job ads has been mandatory since 2011.")),
               (T("Wann gilt die Entgelttransparenzrichtlinie in Deutschland?", "When does the pay transparency directive apply in Germany?"),
                T("Die Frist zur Umsetzung lief am 7. Juni 2026 ab. Deutschland hat sie verpasst, ein Gesetz wird für 2027 erwartet. Ein genaues Datum steht noch nicht fest.",
                  "The deadline was 7 June 2026. Germany missed it, and a law is expected in 2027. No exact date has been set.")),
               (T("Wo finde ich App-Jobs mit Gehaltsangabe?", "Where can I find app jobs that show the salary?"),
                T(f"Alle {nf(len(paid), de)} Anzeigen mit Gehaltsangabe stehen auf berlinappjobs.com{jobs_url}.", f"All {nf(len(paid), de)} ads that state the pay are listed at berlinappjobs.com{jobs_url}."))]
        b += '<section class="faq"><h2>FAQ</h2>' + ''.join(f'<h3>{esc(q)}</h3><p>{esc(a)}</p>' for q, a in faq) + '</section>'
        b += f'<div style="margin-top:18px"><a class="cta" href="{jobs_url}">{T(f"Alle {nf(len(paid), de)} Jobs mit Gehaltsangabe", f"All {nf(len(paid), de)} jobs that show pay")} &rarr;</a></div>'
        ld = [breadcrumb([("Home", SITE + "/"), (T("Gehaltstransparenz", "Salary transparency"), url)]),
              {"@context": "https://schema.org", "@type": "Article", "headline": title[:110], "description": desc, "inLanguage": lang,
               "datePublished": "2026-10-07", "dateModified": max(TODAY, "2026-10-07"), "mainEntityOfPage": url,
               "author": {"@type": "Organization", "name": "Berlin App Jobs", "url": SITE + "/"}, "publisher": {"@type": "Organization", "name": "Berlin App Jobs", "url": SITE + "/"}},
              {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}]
        doc = head(title, desc, url, extra='\n' + CSS + '\n' + jsonld(ld), lang=lang, alt=alt, active='')
        doc += b + '</div>' + (FOOT if de else FOOT_EN) + '</body></html>'
        d = os.path.join(OUT, *T('gehaltstransparenz', 'en/salary-transparency').split('/')); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(doc)
        out_urls.append(url)

    # ================= jobs that state the pay =================
    paid = []
    for c in COS:
        for jb in c.get('jobs') or []:
            m = SAL.get(jb.get('u'))
            if m and m['sal']: paid.append((c, jb, m))
    paid.sort(key=lambda x: (x[1].get('p') or '0000'), reverse=True)
    def jobs_page(lang):
        de = lang == 'de'; T = lambda a, b: a if de else b
        url = SITE + T('/jobs/mit-gehalt/', '/en/jobs/with-salary/')
        alt = {'de': SITE + '/jobs/mit-gehalt/', 'en': SITE + '/en/jobs/with-salary/'}
        n = len(paid)
        title = T(f"Jobs mit Gehaltsangabe: {n} App-Jobs mit Gehalt ({MONTH_DE})", f"Jobs With Salary: {n} App Jobs That Show Pay ({MONTH_EN})")
        desc = T(f"{n} offene Stellen bei deutschen App-Firmen, die ihr Gehalt nennen: Spanne, Monats- oder Stundenlohn direkt aus der Anzeige. Aktualisiert {TODAY}.",
                 f"{n} open roles at German app companies that state the pay: range, monthly or hourly rate straight from the ad. Updated {TODAY}.")
        b = f'<nav class="crumb"><a href="/">Home</a> / <a href="{T("/jobs/", "/en/jobs/")}">Jobs</a> / {T("Mit Gehaltsangabe", "With salary")}</nav>'
        b += f'<h1>{T(f"{n} App-Jobs mit Gehaltsangabe", f"{n} app jobs that show the salary")}</h1>'
        b += ('<p class="sub">' + T(f"Nur {pf(P_all, de)} der Stellenanzeigen bei deutschen App-Firmen nennen ein Gehalt. Hier sind alle, die es tun, mit der Angabe aus der Anzeige.",
                                    f"Only {pf(P_all, de)} of job ads at German app companies state the pay. Here are all the ones that do, with the figure from the ad.")
              + f' <a href="{T("/gehaltstransparenz/", "/en/salary-transparency/")}">{T("Zum Gehaltstransparenz-Index", "See the salary transparency index")} &rarr;</a></p>')
        b += f'<div class="meta"><span class="pill">{n} {T("Stellen", "roles")}</span><span>{T("Aktualisiert", "Updated")} {TODAY}</span></div>'
        RT = {'ausbildung': T('Ausbildung', 'Apprenticeship'), 'student': T('Werkstudent/Praktikum', 'Student/intern'), 'pro': ''}
        for c, jb, m in paid:
            jpu = JOBPAGE.get(jb.get('u', ''))
            pay = salary_detect.pay_label(m, lang)
            sub = esc(short_name(c['n'])) + ' &middot; ' + esc(jb.get('loc') or c.get('city') or '') + (' &middot; ' + RT[m['rt']] if RT.get(m['rt']) else '')
            b += ((f'<a class="row" href="{jpu}">' if jpu else f'<a class="row" href="{esc(jb.get("u", "#"))}" target="_blank" rel="noopener nofollow">')
                  + f'<div class="m"><div class="t">{esc(jb["t"])}</div><div class="d">{sub}</div></div>'
                  + (f'<span class="pay">{esc(pay)}</span>' if pay else '') + '</a>')
        b += f'<p class="secnote" style="margin-top:14px">{T("Betrag wie in der Anzeige angegeben, automatisch erkannt. Maßgeblich ist die Anzeige des Unternehmens.", "Amount as stated in the ad, detected automatically. The company’s ad is what counts.")}</p>'
        b += f'<a class="cta" href="/?sal=1">{T("Im Jobboard filtern", "Filter on the job board")} &rarr;</a>'
        ld = [breadcrumb([("Home", SITE + "/"), ("Jobs", SITE + T('/jobs/', '/en/jobs/')), (T("Mit Gehaltsangabe", "With salary"), url)]),
              {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": k + 1, "name": jb['t'], "url": SITE + JOBPAGE[jb['u']] if jb.get('u') in JOBPAGE else jb.get('u')} for k, (c, jb, m) in enumerate(paid[:100])]}]
        doc = head(title, desc, url, extra='\n' + CSS + '\n' + jsonld(ld), lang=lang, alt=alt, active='jobs')
        doc += b + '</div>' + (FOOT if de else FOOT_EN) + '</body></html>'
        d = os.path.join(OUT, *T('jobs/mit-gehalt', 'en/jobs/with-salary').split('/')); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(doc)
        out_urls.append(url)

    for lg in ('de', 'en'):
        index(lg)
        if paid: jobs_page(lg)
    print(f"salary index: {S}/{N} ads state pay ({P_all:.1f}%), pro {P_pro:.1f}%, jobs-with-salary page {len(paid)} rows")
    return out_urls
