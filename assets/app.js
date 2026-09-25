(function () {
  const $ = id => document.getElementById(id);
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const COS = BOARD.companies;
  const DISCS = ['', 'eng', 'data', 'product', 'design', 'marketing', 'sales', 'support', 'people', 'health', 'other'];
  const DLINE = { eng: '#3F8F3D', data: '#E8850C', product: '#DA421E', design: '#1B5FA6', marketing: '#8B2E8B', sales: '#0F8F8F', support: '#66655C', people: '#A0561B', health: '#D6003C', other: '#52524A' };
  const DSHORT = { eng: 'ENG', data: 'DATA', product: 'PROD', design: 'DSGN', marketing: 'MKT', sales: 'SALES', support: 'OPS', people: 'PPL', health: 'MED', other: 'MISC' };
  const INST = v => v >= 1e9 ? '1B+' : v >= 5e8 ? '500M+' : v >= 1e8 ? '100M+' : v >= 5e7 ? '50M+' : v >= 1e7 ? '10M+' : v >= 5e6 ? '5M+' : v >= 1e6 ? '1M+' : v >= 5e5 ? '500K+' : v >= 1e5 ? '100K+' : v >= 5e4 ? '50K+' : v >= 1e4 ? '10K+' : v > 0 ? '<10K' : '';
  const fmtN = n => n >= 1e6 ? (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + 'M' : n >= 1e3 ? (n / 1e3).toFixed(n >= 1e4 ? 0 : 1) + 'K' : String(n);
  const LS = { get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
  const salShort = s => { if (!s) return ''; let x = String(s).split('•')[0].split('·')[0].split('|')[0].trim(); return x.replace(/\s*[-–]\s*/g, '–'); };
  const salNum = s => { if (!s) return 0; const m = String(s).replace(/[.,](?=\d{3}\b)/g, '').match(/\d{2,}/g); if (!m) return 0; let n = Math.max(...m.map(Number)); if (/k/i.test(s) && n < 1000) n *= 1000; return n; };

  // ---------- i18n ----------
  const T = {
    en: {
      roles: 'roles', cosHiring: 'companies hiring', tJobs: 'Jobs', tCharts: 'Charts', tCos: 'Companies', tMap: 'Map', promo: 'Promote your company',
      wp: { office: 'Office', remote: 'Remote', hybrid: 'Hybrid' }, hType: 'Job type', hDate: 'Date posted', salOnly: 'Salary shown only', filtersBtn: 'Filters', showN: n => 'Show ' + n + ' job' + (n === 1 ? '' : 's'), clearAll: 'Clear all', filterHead: 'Filters', tGuides: 'Guides', moreNav: 'More', guidesH2: 'Guides', guidesSub: 'Practical guides to finding a job at a German app company. New ones added weekly.', readGuide: 'Read guide', backGuides: 'All guides', introGuide: 'Read the guides →', moreGuides: n => n + ' more guide' + (n === 1 ? '' : 's') + ' in German', fewerGuides: 'Hide German guides', otherLangH: 'In German', introCompanies: 'Browse companies →', footGuidesT: 'Guides', ctaJobs: 'Browse open roles ↗',
      introH1: 'Berlin App Jobs: work on an app <em>people actually use.</em>',
      introSub: "Live roles from the hiring systems of Germany's app companies. Direct apply, no middleman.",
      stamp: d => 'Feeds checked ' + d, search: 'Search roles, apps, companies…',
      hCity: 'City', hDisc: 'Discipline', hDet: 'Details', saved: 'Saved', reset: 'Reset filters', allCities: 'All of Germany',
      selSen: [['', 'Any seniority'], ['intern', 'Intern / Working student'], ['junior', 'Junior'], ['mid', 'Mid'], ['senior', 'Senior'], ['lead', 'Lead / Manager']],
      selType: [['', 'Any job type'], ['fulltime', 'Full-time'], ['parttime', 'Part-time'], ['werkstudent', 'Working student'], ['intern', 'Internship'], ['contract', 'Contract'], ['freelance', 'Freelance']],
      selDate: [['', 'Any time'], ['1', 'Last 24 hours'], ['7', 'Last 7 days'], ['14', 'Last 14 days'], ['30', 'Last 30 days']],
      selWp: [['', 'Any workplace'], ['office', 'Office'], ['remote', 'Remote'], ['hybrid', 'Hybrid']],
      selLg: [['', 'English / German'], ['en', 'English'], ['de', 'German']],
      selSort: [['app', 'Most relevant'], ['new', 'Newest'], ['sal', 'Highest salary'], ['az', 'Company A-Z']],
      disc: { '': 'All roles', eng: 'Engineering', data: 'Data', product: 'Product', design: 'Design', marketing: 'Marketing', sales: 'Sales', support: 'Ops & Support', people: 'People & Finance', health: 'Health', other: 'Other' },
      sen: { intern: 'Intern/WS', junior: 'Junior', senior: 'Senior', lead: 'Lead+' },
      nRoles: (n, s) => n + ' role' + (n === 1 ? '' : 's') + (s ? ' saved' : ''), remoteOk: 'remote-ok', remote: 'Remote', sponsored: 'Sponsored', clicks: 'clicks', apply: 'Apply ↗', today: 'today', dAgo: d => d + 'd ago', moAgo: m => m + 'mo ago', androidP: ' Android',
      emptyT: 'No roles match', emptyB: "Clear a filter or two, or check the Companies tab for boards we couldn't parse.",
      linkT: "Also hiring, on boards we can't parse", linkB: 'Live openings, but no readable feed. Worth a direct look.', careers: 'Careers ↗', more: 'Show more roles', nOpen: n => '~' + n + ' roles',
      cosH2: 'Hiring companies', cosSub: 'Every German app company with open roles, most roles first. Click one for its jobs and apps.', openRoles: n => n + ' open role' + (n > 1 ? 's' : ''), hiringLink: 'hiring · careers page', dorm: n => 'Not hiring right now (' + n + ' companies)',
      lbH2: 'The app leaderboard', lbSubPlay: n => 'The ' + n + ' German app companies currently hiring, from the DE Play Store top charts, ranked by lifetime Android installs (review count breaks ties).', lbSubIos: n => n + ' currently-hiring apps matched on the German App Store, ranked by lifetime rating count. Apple publishes no download numbers.', lbFind: 'Find an app…', all: 'All', hiring: 'hiring', instSub: 'Android installs', revSub: ' reviews', rateSub: 'DE ratings · ★ ', lbMore: 'Show the full ranking', lbEmptyT: 'Nothing matches', lbEmptyB: 'Try another category or store.',
      mapH2: 'Where the jobs are: Germany', cityTip: (n, r) => n + (n === 1 ? ' company' : ' companies') + ' hiring · ' + r + ' open roles', zoomIn: 'Click to zoom in', mapSub: 'Opens on Berlin. Zoom out (or hit DE) for all of Germany: yellow bubbles are cities, sized by open roles. Tap a city to fly in, tap a logo for that company\'s roles. Small dots are companies not hiring right now.', legend: '<b>Size = open roles</b> · yellow ring = hiring · thick ring = sponsor · dots = not hiring', notHiring: 'not hiring right now', openN: n => n + ' open roles', sponsor: 'sponsor',
      cpH1: 'Open roles', cpH2: 'Their apps', cpCta: 'All roles on their careers page ↗', regAs: 'Registered as ', ext: 'German office, HQ elsewhere', instA: ' installs (Android)', ratI: ' DE ratings (iOS)', seeCareers: 'View open roles', noRoles: 'No open roles right now', rolesOn: n => 'View ' + n + '+ open roles', extrolesSub: "These roles are listed on the company's own careers page, and open in a new tab.",
      pmTitle: 'Promote your company', booked: 'booked until 31 Dec 2069', soldOut: 'Sold out', pmActs: [['Freecash', 'extended all 3 top spots until 2069', 'today'], ['Freecash', 'politely declined a very generous offer to share', 'last week'], ['Freecash', 'booked the featured slot', '19 Sept']], pmSub: 'sold out · waitlist open', pmSoonT: 'Sold out until 2069', pmSoonD: 'Freecash has booked every top spot and every featured slot on this board until 31 December 2069. We tried to negotiate. They paid us in coins. If anything frees up before then (unlikely, but we are optimists), companies on the waitlist hear first.', pmEmail: 'Join the waitlist', pmH1: 'Top spots', pmP1: 'Three pinned slots above every job list. Yours until someone outbids you. Views and clicks are counted and shown publicly on your rows.', pmH2: 'Featured company: flat rate', pmPkgT: 'Featured for a week', pmPkg: ['All your roles highlighted and boosted to the top of their discipline', 'Bigger glowing marker on the map', 'Featured badge on Companies and Charts', 'Public view & click counter on your rows'], featBtn: 'Email to feature my company', claimBtn: 'Claim top spot', pmH3: 'Recent sponsor activity', pmFine: 'Serious about hiring? Email jophabraken@gmail.com and we will talk. The 2069 part is a joke. Mostly.', vacant: 'Vacant', fromE: 'from €', since: 'since', outbid: 'Outbid €', claim: 'Claim €', choose: 'Choose your company…', noAct: 'No sponsor activity yet. Be first.',
      seoH2: 'App jobs in Germany: how this works',
      seoBody: `<p>Berlin App Jobs lists live roles at the companies behind Germany's most-used apps: Android and iOS developer jobs, product, design, data, marketing and operations roles in Berlin, Munich, Hamburg and remote across Germany. Every listing is pulled directly from the company's own hiring system and links straight to their application page: no recruiters, no stale posts, with salary ranges wherever companies publish them.</p>`,
      faq: [
        ['How current are the listings?', 'Job feeds are re-checked weekly, straight from each company\'s applicant tracking system (Greenhouse, Personio, Ashby, Lever and others). The "feeds checked" date shows the last run.'],
        ['Which companies are on Berlin App Jobs?', 'Every developer registered in Germany behind the Google Play top charts, plus verified German offices of international app companies like SumUp, Wolt and TikTok. Companies are shown with their apps, Android install counts and iOS ratings.'],
        ['Do I need German for these jobs?', 'Often not. Listings are tagged EN or DE by language, and Berlin app companies in particular hire in English; use the listing-language filter.'],
        ['Are salaries shown?', 'Where the company publishes them, yes: salary ranges appear directly on the job cards.']
      ],
      foot: `<b>How this board works.</b> Companies come from the Google Play top charts (all categories, German storefront): every developer registered in Germany per its EU trader address, plus verified German offices of companies headquartered elsewhere. Jobs are pulled from each company's own hiring system. Install figures are <b>Google Play (Android) lifetime brackets</b>; iOS popularity is shown as German App Store rating counts, since Apple publishes no download numbers. Sponsored placements are labeled; exposure counters count views and clicks in your browser (demo). Always confirm roles on the company's page.`
    },
    de: {
      roles: 'Stellen', cosHiring: 'Firmen stellen ein', tJobs: 'Jobs', tCharts: 'Charts', tCos: 'Unternehmen', tMap: 'Karte', promo: 'Werbung schalten',
      wp: { office: 'Vor Ort', remote: 'Remote', hybrid: 'Hybrid' }, hType: 'Anstellungsart', hDate: 'Veröffentlicht', salOnly: 'Nur mit Gehalt', filtersBtn: 'Filter', showN: n => n + ' Stelle' + (n === 1 ? '' : 'n') + ' anzeigen', clearAll: 'Zurücksetzen', filterHead: 'Filter', tGuides: 'Ratgeber', moreNav: 'Mehr', guidesH2: 'Ratgeber', guidesSub: 'Praktische Ratgeber für die Jobsuche bei deutschen App-Unternehmen. Wöchentlich neue Beiträge.', readGuide: 'Lesen', backGuides: 'Alle Ratgeber', introGuide: 'Zu den Ratgebern →', moreGuides: n => n + ' weitere Ratgeber auf Englisch', fewerGuides: 'Englische Ratgeber ausblenden', otherLangH: 'Auf Englisch', introCompanies: 'Alle Unternehmen →', footGuidesT: 'Ratgeber', ctaJobs: 'Offene Stellen ansehen ↗',
      introH1: 'Berlin App Jobs: Arbeite an einer App, <em>die Menschen wirklich nutzen.</em>',
      introSub: 'Live-Stellen direkt aus den Bewerbungssystemen deutscher App-Unternehmen. Direkt bewerben, ohne Umwege.',
      stamp: d => 'Feeds geprüft am ' + d, search: 'Jobs, Apps, Unternehmen suchen…',
      hCity: 'Stadt', hDisc: 'Bereich', hDet: 'Details', saved: 'Gemerkt', reset: 'Filter zurücksetzen', allCities: 'Ganz Deutschland',
      selSen: [['', 'Alle Level'], ['intern', 'Praktikum / Werkstudent'], ['junior', 'Junior'], ['mid', 'Mid-Level'], ['senior', 'Senior'], ['lead', 'Lead / Manager']],
      selType: [['', 'Alle Anstellungsarten'], ['fulltime', 'Vollzeit'], ['parttime', 'Teilzeit'], ['werkstudent', 'Werkstudent'], ['intern', 'Praktikum'], ['contract', 'Vertrag'], ['freelance', 'Freelance']],
      selDate: [['', 'Jederzeit'], ['1', 'Letzte 24 Std.'], ['7', 'Letzte 7 Tage'], ['14', 'Letzte 14 Tage'], ['30', 'Letzte 30 Tage']],
      selWp: [['', 'Alle Arbeitsorte'], ['office', 'Vor Ort'], ['remote', 'Remote'], ['hybrid', 'Hybrid']],
      selLg: [['', 'Englisch / Deutsch'], ['en', 'Englisch'], ['de', 'Deutsch']],
      selSort: [['app', 'Relevanteste'], ['new', 'Neueste'], ['sal', 'Höchstes Gehalt'], ['az', 'Unternehmen A-Z']],
      disc: { '': 'Alle Stellen', eng: 'Engineering', data: 'Data', product: 'Produkt', design: 'Design', marketing: 'Marketing', sales: 'Sales', support: 'Ops & Support', people: 'People & Finance', health: 'Gesundheit', other: 'Sonstige' },
      sen: { intern: 'Praktikum/WS', junior: 'Junior', senior: 'Senior', lead: 'Lead+' },
      nRoles: (n, s) => n + (n === 1 ? ' Stelle' : ' Stellen') + (s ? ' gemerkt' : ''), remoteOk: 'remote möglich', remote: 'Remote', sponsored: 'Gesponsert', clicks: 'Klicks', apply: 'Bewerben ↗', today: 'heute', dAgo: d => 'vor ' + d + ' Tg.', moAgo: m => 'vor ' + m + ' Mon.', androidP: ' Android',
      emptyT: 'Keine passenden Stellen', emptyB: 'Entferne einen Filter oder schau im Unternehmen-Tab nach Karriereseiten ohne lesbaren Feed.',
      linkT: 'Stellen auch offen: Feeds nicht lesbar', linkB: 'Offene Stellen vorhanden, aber kein lesbarer Feed. Ein direkter Blick lohnt sich.', careers: 'Karriere ↗', more: 'Mehr Stellen anzeigen', nOpen: n => '~' + n + ' Stellen',
      cosH2: 'Unternehmen, die einstellen', cosSub: 'Alle deutschen App-Unternehmen mit offenen Stellen, sortiert nach Anzahl. Klick für Jobs und Apps.', openRoles: n => n + (n > 1 ? ' offene Stellen' : ' offene Stelle'), hiringLink: 'stellt ein · Karriereseite', dorm: n => 'Aktuell keine offenen Stellen (' + n + ' Unternehmen)',
      lbH2: 'Das App-Ranking', lbSubPlay: n => 'Die ' + n + ' deutschen App-Unternehmen mit offenen Stellen, aus den DE Play-Store-Charts, sortiert nach Android-Installationen (Bewertungszahl entscheidet bei Gleichstand).', lbSubIos: n => n + ' davon mit offenen Stellen im deutschen App Store, sortiert nach Bewertungsanzahl. Apple veröffentlicht keine Download-Zahlen.', lbFind: 'App finden…', all: 'Alle', hiring: 'stellt ein', instSub: 'Android-Installationen', revSub: ' Bewertungen', rateSub: 'DE-Bewertungen · ★ ', lbMore: 'Komplettes Ranking anzeigen', lbEmptyT: 'Nichts gefunden', lbEmptyB: 'Andere Kategorie oder anderen Store probieren.',
      mapH2: 'Wo die Jobs sind: Deutschland', cityTip: (n, r) => n + (n === 1 ? ' Firma stellt' : ' Firmen stellen') + ' ein · ' + r + ' offene Stellen', zoomIn: 'Klicken zum Hineinzoomen', mapSub: 'Startet mit Berlin. Herauszoomen (oder DE tippen) zeigt ganz Deutschland: gelbe Blasen sind Städte, Größe nach offenen Stellen. Stadt antippen zum Hineinfliegen, Logo antippen für die Stellen. Kleine Punkte: Unternehmen ohne offene Stellen.', legend: '<b>Größe = offene Stellen</b> · gelber Ring = stellt ein · dicker Ring = Sponsor · Punkte = keine Stellen', notHiring: 'aktuell keine offenen Stellen', openN: n => n + ' offene Stellen', sponsor: 'Sponsor',
      cpH1: 'Offene Stellen', cpH2: 'Ihre Apps', cpCta: 'Alle Stellen auf der Karriereseite ↗', regAs: 'Eingetragen als ', ext: 'Deutsches Büro, HQ im Ausland', instA: ' Installationen (Android)', ratI: ' DE-Bewertungen (iOS)', seeCareers: 'Offene Stellen ansehen', noRoles: 'Aktuell keine offenen Stellen', rolesOn: n => 'Alle ' + n + '+ offenen Stellen ansehen', extrolesSub: 'Diese Stellen stehen auf der Karriereseite des Unternehmens und öffnen in neuem Tab.',
      pmTitle: 'Werbung schalten', booked: 'gebucht bis 31.12.2069', soldOut: 'Ausgebucht', pmActs: [['Freecash', 'hat alle 3 Top-Plätze bis 2069 verlängert', 'heute'], ['Freecash', 'hat ein sehr großzügiges Angebot zum Teilen höflich abgelehnt', 'letzte Woche'], ['Freecash', 'hat den Featured-Platz gebucht', '19. Sept.']], pmSub: 'ausgebucht · Warteliste offen', pmSoonT: 'Ausgebucht bis 2069', pmSoonD: 'Freecash hat jeden Top-Platz und jede Featured-Fläche auf diesem Board bis zum 31. Dezember 2069 gebucht. Wir haben verhandelt. Bezahlt wurde in Coins. Wird vorher etwas frei (unwahrscheinlich, aber wir sind Optimisten), erfahren es Firmen auf der Warteliste zuerst.', pmEmail: 'Auf die Warteliste', pmH1: 'Top-Plätze', pmP1: 'Drei fixe Plätze über jeder Jobliste. Deiner, bis dich jemand überbietet. Views und Klicks werden gezählt und öffentlich angezeigt.', pmH2: 'Featured: Festpreis', pmPkgT: 'Eine Woche featured', pmPkg: ['Alle deine Stellen hervorgehoben und oben im jeweiligen Bereich', 'Größerer, leuchtender Marker auf der Karte', 'Featured-Badge bei Unternehmen und Charts', 'Öffentlicher View- & Klick-Zähler auf deinen Stellen'], featBtn: 'Per E-Mail featuren', claimBtn: 'Top-Platz sichern', pmH3: 'Letzte Sponsor-Aktivität', pmFine: 'Ernsthaft am Einstellen? Schreib an jophabraken@gmail.com, dann reden wir. Das mit 2069 ist ein Witz. Größtenteils.', vacant: 'Frei', fromE: 'ab €', since: 'seit', outbid: 'Überbieten €', claim: 'Sichern €', choose: 'Unternehmen wählen…', noAct: 'Noch keine Sponsor-Aktivität. Sei der Erste.',
      seoH2: 'App Jobs in Deutschland: so funktioniert es',
      seoBody: `<p>Berlin App Jobs listet offene Stellen bei den Unternehmen hinter Deutschlands meistgenutzten Apps: App-Entwickler-Jobs (Android & iOS), Produkt, Design, Data, Marketing und Operations, in Berlin, München, Hamburg und remote in ganz Deutschland. Jede Anzeige kommt direkt aus dem Bewerbungssystem des Unternehmens und verlinkt auf die Original-Bewerbungsseite: ohne Recruiter, ohne veraltete Anzeigen, mit Gehaltsspannen, wo Unternehmen sie veröffentlichen.</p>`,
      faq: [
        ['Wie aktuell sind die Stellen?', 'Die Feeds werden wöchentlich direkt aus den Bewerbungssystemen der Unternehmen (Greenhouse, Personio, Ashby, Lever u.a.) neu geladen. Das Datum "Feeds geprüft" zeigt den letzten Lauf.'],
        ['Welche Unternehmen sind auf Berlin App Jobs?', 'Jeder in Deutschland registrierte Entwickler hinter den Google-Play-Top-Charts, plus verifizierte deutsche Büros internationaler App-Firmen wie SumUp, Wolt und TikTok, mit ihren Apps, Android-Installationszahlen und iOS-Bewertungen.'],
        ['Brauche ich Deutsch für diese Jobs?', 'Oft nicht. Anzeigen sind nach Sprache (EN/DE) gefiltert; gerade Berliner App-Unternehmen stellen auf Englisch ein.'],
        ['Werden Gehälter angezeigt?', 'Wo Unternehmen sie veröffentlichen, ja: Gehaltsspannen stehen direkt auf den Job-Karten.']
      ],
      foot: `<b>So funktioniert das Board.</b> Die Unternehmen stammen aus den Google-Play-Top-Charts (alle Kategorien, deutscher Store): jeder Entwickler mit deutscher EU-Händleradresse, plus verifizierte deutsche Büros internationaler Firmen. Stellen kommen direkt aus dem jeweiligen Bewerbungssystem. Installationszahlen sind <b>Google-Play-Brackets (Android, gesamt)</b>; iOS-Beliebtheit als Anzahl deutscher App-Store-Bewertungen, da Apple keine Downloads veröffentlicht. Gesponserte Platzierungen sind gekennzeichnet; Zähler erfassen Views und Klicks in deinem Browser (Demo). Stellen immer auf der Unternehmensseite prüfen.`
    }
  };
  let L = LS.get('ak_lang', (navigator.language || '').startsWith('de') ? 'de' : 'en');
  const t = k => T[L][k];

  let JOBS = [];
  COS.forEach((c, ci) => { c.ci = ci; c.city = c.city || 'Berlin'; (c.jobs || []).forEach(j => JOBS.push({ ...j, c })); });
  JOBS.forEach(j => {
    const hay = (j.t + ' ' + (j.loc || '')).toLowerCase();
    j.wp = /hybrid/.test(hay) ? 'hybrid' : (j.rem ? 'remote' : 'office');
    j.typ = /werkstud|working student/.test(hay) ? 'werkstudent'
      : (j.s === 'intern' || /praktik|internship|\bintern\b|trainee/.test(hay)) ? 'intern'
      : /freelanc|freiberuf/.test(hay) ? 'freelance'
      : /part.?time|teilzeit|minijob/.test(hay) ? 'parttime'
      : /contract|befristet|fixed.?term|interim|\bftc\b/.test(hay) ? 'contract'
      : 'fulltime';
  });
  const hiringCos = COS.filter(c => c.tier <= 2);
  $('st-jobs').textContent = JOBS.length;
  $('st-cos').textContent = hiringCos.length;
  const CITY_COUNTS = {};
  JOBS.forEach(j => { CITY_COUNTS[j.c.city] = (CITY_COUNTS[j.c.city] || 0) + 1; });
  const CITIES = Object.entries(CITY_COUNTS).sort((a, b) => b[1] - a[1]).map(x => x[0]);

  // ---------- sponsors (demo backend: seeded + this browser) ----------
  const sponsors = { slots: SPONSOR_SEED.slots.slice(), featured: SPONSOR_SEED.featured.slice(), acts: SPONSOR_SEED.acts.slice() };
  const metrics = LS.get('baj_mx', {});
  function saveSp() { LS.set('baj_sp2', sponsors); }
  // fair counting: each role counts at most one view and one click per page load (re-renders, saves, filter changes don't re-count)
  const countedOnce = new Set();
  function bump(dev, kind, key) {
    if (key) { const k = kind + '|' + key; if (countedOnce.has(k)) return; countedOnce.add(k); }
    const m = metrics[dev] = metrics[dev] || { i: 0, c: 0 }; m[kind]++; LS.set('baj_mx', metrics);
  }
  const sponDevs = () => new Set([...sponsors.slots.filter(s => s.dev).map(s => s.dev), ...sponsors.featured.map(f => f.dev)]);
  const io = 'IntersectionObserver' in window ? new IntersectionObserver(es => {
    es.forEach(e => { if (e.isIntersecting && e.target.dataset.spdev) { bump(e.target.dataset.spdev, 'i', e.target.dataset.ju); io.unobserve(e.target); } });
  }, { threshold: 0.6 }) : null;

  // ---------- tabs ----------
  const tabs = ['jobs', 'charts', 'studios', 'maptab', 'guides'];
  let mapBuilt = false;
  function setTab(t, init) {
    tabs.forEach(x => { $(x).hidden = x !== t; });
    hideTip();
    document.querySelectorAll('#tabs button, #bottomNav button').forEach(b => b.classList.toggle('on', b.dataset.tab === t));
    const moreBtn = document.querySelector('#bottomNav button[data-act="more"]'); if (moreBtn) moreBtn.classList.toggle('on', t === 'studios' || t === 'guides');
    if (t === 'maptab' && !mapBuilt) { buildMap(); mapBuilt = true; }
    if (t === 'guides') renderGuides();
    if (!init) try { history.replaceState(null, '', '#' + t); } catch (e) {}
  }
  $('tabs').addEventListener('click', e => { const b = e.target.closest('button'); if (b) setTab(b.dataset.tab); });
  $('wordmark').addEventListener('click', e => { e.preventDefault(); setTab('jobs'); if (typeof closeAll === 'function') closeAll(); window.scrollTo({ top: 0, behavior: 'smooth' }); });
  function openMore() { $('moreSheet').classList.add('open'); $('shade').classList.add('on'); }
  function closeMore() { $('moreSheet').classList.remove('open'); $('shade').classList.remove('on'); }
  document.getElementById('bottomNav').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.act === 'more') { openMore(); return; } setTab(b.dataset.tab); window.scrollTo({ top: 0, behavior: 'smooth' }); });
  $('moreSheet').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; closeMore(); const a = b.dataset.more; if (a === 'promo') { renderPm(); $('shade').classList.add('on'); $('pm').classList.add('on'); } else { setTab(a); window.scrollTo({ top: 0, behavior: 'smooth' }); } });
  setTab(['#studios', '#maptab', '#charts'].includes(location.hash) ? location.hash.slice(1) : 'jobs', true);

  // ---------- filters state ----------
  const state = Object.assign({ q: '', d: '', city: '', sen: '', typ: '', wp: '', lg: '', date: '', sort: 'app', salOnly: false, saved: false, shown: 50 }, LS.get('baj', {}), { shown: 50, saved: false });
  if (!['', 'office', 'remote', 'hybrid'].includes(state.wp)) state.wp = '';
  // deep-link filters from URL (?q=&city=&disc=&lg=), e.g. from guide pages
  try {
    const sp = new URLSearchParams(location.search);
    // a deep link (from a guide or programmatic page) should show exactly that view, not mixed with filters saved from an earlier visit
    if (['q', 'city', 'disc', 'lg', 'wp', 'sen', 'sal'].some(k => sp.get(k))) Object.assign(state, { q: '', d: '', city: '', sen: '', typ: '', wp: '', lg: '', date: '', salOnly: false });
    if (sp.has('q')) state.q = (sp.get('q') || '').toLowerCase();
    if (sp.has('city')) state.city = sp.get('city') || '';
    if (sp.has('disc')) state.d = sp.get('disc') || '';
    if (sp.has('lg')) state.lg = sp.get('lg') || '';
    if (['office', 'remote', 'hybrid'].includes(sp.get('wp'))) state.wp = sp.get('wp');
    if (['intern', 'junior', 'mid', 'senior', 'lead'].includes(sp.get('sen'))) state.sen = sp.get('sen');
    if (sp.get('sal') === '1') state.salOnly = true;
    if (sp.get('q') || sp.get('city') || sp.get('disc') || sp.get('lg') || sp.get('wp') || sp.get('sen') || sp.get('sal')) window.__deepFilter = true;
  } catch (e) {}
  const seen = new Set(LS.get('baj_seen', []));
  const firstVisit = seen.size === 0;
  const savedSet = new Set(LS.get('baj_sav', []));
  const relTime = p => {
    if (!p) return '';
    const d = Math.round((Date.now() - new Date(p).getTime()) / 864e5);
    return d <= 0 ? t('today') : d < 30 ? t('dAgo')(d) : t('moAgo')(Math.round(d / 30));
  };

  function applyFilters(skipDisc) {
    return JOBS.filter(j => {
      if (state.saved && !savedSet.has(j.u)) return false;
      if (state.city && j.c.city !== state.city) return false;
      if (!skipDisc && state.d && j.d !== state.d) return false;
      if (state.sen && j.s !== state.sen) return false;
      if (state.wp && j.wp !== state.wp) return false;
      if (state.typ && j.typ !== state.typ) return false;
      if (state.lg && j.lang !== state.lg) return false;
      if (state.salOnly && !j.sal) return false;
      if (state.date) { const dd = j.p ? (Date.now() - new Date(j.p).getTime()) / 864e5 : 9999; if (dd > +state.date) return false; }
      if (state.q) { const hay = (j.t + ' ' + j.c.n + ' ' + j.c.apps.map(a => a.t).join(' ')).toLowerCase(); if (!hay.includes(state.q)) return false; }
      return true;
    });
  }
  // seniority level for picking sponsored roles: title signals first, then parsed seniority
  const SEN_RANK = { intern: 0, junior: 1, mid: 2, senior: 3, lead: 4 };
  function lvl(j) {
    const t = (j.t || '').toLowerCase();
    if (/\b(chief|cto|cpo|cfo|coo|vp|vice president|svp|evp|director|head of|geschäftsführ)/.test(t)) return 7;
    if (/\b(principal|staff|distinguished)\b/.test(t)) return 6;
    if (/\b(lead|manager|leiter|leitung)\b/.test(t) && j.s !== 'intern' && j.s !== 'junior') return 5;
    return SEN_RANK[j.s] ?? 2;
  }
  function sortJobs(list) {
    const featRank = j => 0; // sponsors no longer bulk-boosted; see sponsoredPicks()
    if (state.sort === 'az') list.sort((a, b) => featRank(a) - featRank(b) || a.c.n.localeCompare(b.c.n) || a.t.localeCompare(b.t));
    else if (state.sort === 'new') list.sort((a, b) => featRank(a) - featRank(b) || (b.p || '').localeCompare(a.p || '') || b.c.v - a.c.v);
    else if (state.sort === 'sal') list.sort((a, b) => featRank(a) - featRank(b) || salNum(b.sal) - salNum(a.sal) || b.c.v - a.c.v);
    else list.sort((a, b) => featRank(a) - featRank(b) || b.c.v - a.c.v || a.c.n.localeCompare(b.c.n));
    return list;
  }
  function icoHtml(c) {
    if (c.icon) return `<img src="${c.icon}" alt="" loading="lazy">`;
    return `<span class="co-ic">${esc(c.n.split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase())}</span>`;
  }

  function discCounts(list) { const m = {}; list.forEach(j => m[j.d] = (m[j.d] || 0) + 1); return m; }
  function renderSide() {
    const counts = discCounts(applyFilters(true));
    const all = Object.values(counts).reduce((a, b) => a + b, 0);
    $('discList').innerHTML = DISCS.map(k => {
      const n = k === '' ? all : (counts[k] || 0);
      return `<button class="${state.d === k && !state.saved ? 'on' : ''}" data-d="${k}"><span class="dl">${k ? `<i class="ddot" style="background:${DLINE[k]}"></i>` : ''}${t('disc')[k]}</span><small>${n}</small></button>`;
    }).join('');
    $('savedN').textContent = savedSet.size;
    $('savedBtn').classList.toggle('on', state.saved);
  }
  function fillSelects() {
    const fill = (id, pairs, val) => { $(id).innerHTML = pairs.map(([v, l]) => `<option value="${v}">${l}</option>`).join(''); $(id).value = val; };
    fill('sen', t('selSen'), state.sen); fill('typ', t('selType'), state.typ); fill('wp', t('selWp'), state.wp); fill('lg', t('selLg'), state.lg); fill('date', t('selDate'), state.date); fill('sort', t('selSort'), state.sort);
    fill('city', [['', t('allCities')]].concat(CITIES.map(c => [c, c + ' (' + CITY_COUNTS[c] + ')'])), state.city);
  }
  $('discList').addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; state.d = b.dataset.d; state.saved = false; state.shown = 50; render(); });
  $('savedBtn').addEventListener('click', () => { state.saved = !state.saved; state.shown = 50; render(); });
  $('q').value = state.q;
  $('salOnly').checked = !!state.salOnly;
  let deb;
  $('q').addEventListener('input', e => { clearTimeout(deb); deb = setTimeout(() => { state.q = e.target.value.trim().toLowerCase(); state.shown = 50; render(); }, 120); });
  ['sen', 'typ', 'wp', 'lg', 'date', 'sort', 'city'].forEach(id => $(id).addEventListener('change', e => { state[id] = e.target.value; state.shown = 50; render(); }));
  $('salOnly').addEventListener('change', e => { state.salOnly = e.target.checked; state.shown = 50; render(); });
  $('reset').addEventListener('click', () => { state.q = ''; state.d = ''; state.city = ''; state.sen = ''; state.typ = ''; state.wp = ''; state.lg = ''; state.date = ''; state.salOnly = false; state.saved = false; state.shown = 50; $('q').value = ''; if ($('mq')) $('mq').value = ''; $('salOnly').checked = false; fillSelects(); render(); });

  function jobRow(j, spon) {
    const app = j.c.apps[0];
    const inst = INST(j.c.v);
    const isNew = !firstVisit && j.p && !seen.has(j.u) ? '<span class="newb">NEW</span>' : '';
    const m = metrics[j.c.n];
    const loc = esc(j.loc === 'Berlin' || j.loc === 'Remote' ? j.c.city : j.loc);
    return `<div class="job${spon ? ' spon' : ''}" data-ci="${j.c.ci}" data-ju="${esc(j.u)}" ${spon ? `data-spdev="${esc(j.c.n)}"` : ''}>
      ${icoHtml(j.c)}
      <div class="jbody">
        <div class="jtop">
          ${j.d && j.d !== 'other' ? `<span class="dln" style="background:${DLINE[j.d] || '#52524A'}">${DSHORT[j.d] || ''}</span>` : ''}
          <span class="jco">${esc(j.c.n)}</span>${isNew}${spon ? `<span class="sponb">${t('sponsored')}</span>` : ''}
          <span class="ago">${relTime(j.p)}</span>
        </div>
        <div class="jt"><span class="tt">${esc(j.t)}</span></div>
        <div class="jmeta">
          <span>${loc}</span>
          <span>${t('wp')[j.wp]}</span>
          ${j.sal ? `<span class="sal" title="${esc(j.sal)}">${esc(salShort(j.sal))}</span>` : ''}
          ${j.s !== 'mid' ? `<span>${t('sen')[j.s] || ''}</span>` : ''}
          <span class="dx">${esc(app.t)}${inst ? ' · ' + inst + t('androidP') : ''}${j.lang === 'de' ? ' · DE' : ''}</span>
          ${spon && m ? `<span class="eye">👁 ${fmtN(m.i)} · ${fmtN(m.c)}</span>` : ''}
        </div>
      </div>
      <button class="sav${savedSet.has(j.u) ? ' on' : ''}" data-u="${esc(j.u)}" aria-label="Save">${savedSet.has(j.u) ? '★' : '☆'}</button>
      <a class="apply" href="${esc(j.u)}" target="_blank" rel="noopener" ${spon ? `data-spc="${esc(j.c.n)}"` : ''}>${t('apply')}</a>
    </div>`;
  }

  function activeFilters() {
    const out = [];
    if (state.d) out.push(['d', t('disc')[state.d]]);
    if (state.city) out.push(['city', state.city]);
    if (state.sen) out.push(['sen', dict('selSen', state.sen)]);
    if (state.typ) out.push(['typ', dict('selType', state.typ)]);
    if (state.wp) out.push(['wp', t('wp')[state.wp]]);
    if (state.lg) out.push(['lg', dict('selLg', state.lg)]);
    if (state.date) out.push(['date', dict('selDate', state.date)]);
    if (state.salOnly) out.push(['salOnly', t('salOnly')]);
    if (state.saved) out.push(['saved', t('saved')]);
    return out;
  }
  function dict(sel, val) { const p = t(sel).find(x => x[0] === val); return p ? p[1] : val; }
  function clearFilter(k) {
    if (k === 'salOnly') { state.salOnly = false; $('salOnly').checked = false; }
    else if (k === 'saved') state.saved = false;
    else { state[k] = ''; }
    state.shown = 50; fillSelects(); render();
  }
  function renderActiveChips() {
    const af = activeFilters();
    const n = af.length;
    const badge = $('mFilterN');
    if (badge) { badge.hidden = n === 0; badge.textContent = n; }
    const box = $('activeChips');
    if (!box) return;
    if (!n) { box.innerHTML = ''; return; }
    box.innerHTML = af.map(([k, lbl]) => `<button class="achip" data-fk="${k}">${esc(lbl)} <span class="x">✕</span></button>`).join('')
      + `<button class="achip clear" data-fk="__all">${t('clearAll')}</button>`;
  }
  document.getElementById('activeChips').addEventListener('click', e => {
    const b = e.target.closest('.achip'); if (!b) return;
    if (b.dataset.fk === '__all') $('reset').click(); else clearFilter(b.dataset.fk);
  });
  // mobile sheet + search mirror
  function openSheet() { $('side').classList.add('open'); $('shade').classList.add('on'); }
  function closeSheet() { $('side').classList.remove('open'); $('shade').classList.remove('on'); }
  $('mFilters').addEventListener('click', openSheet);
  $('sheetClose').addEventListener('click', closeSheet);
  $('applyBtn').addEventListener('click', closeSheet);
  $('shade').addEventListener('click', closeSheet);
  $('shade').addEventListener('click', closeMore);
  (function () { let d; $('mq').addEventListener('input', e => { clearTimeout(d); d = setTimeout(() => { state.q = e.target.value.trim().toLowerCase(); state.shown = 50; $('q').value = e.target.value; render(); }, 120); }); })();

  function render() {
    LS.set('baj', { q: state.q, d: state.d, sen: state.sen, typ: state.typ, wp: state.wp, lg: state.lg, date: state.date, sort: state.sort, salOnly: state.salOnly });
    renderSide();
    let list = sortJobs(applyFilters(false));
    // sponsored block: at most 3 roles, the most senior / best-paid roles of sponsoring companies that match the current filters
    let pinned = [];
    if (!state.saved) {
      const sd = sponDevs();
      pinned = list.filter(j => sd.has(j.c.n)).sort((a, b) => lvl(b) - lvl(a) || salNum(b.sal) - salNum(a.sal) || (b.p || '').localeCompare(a.p || '')).slice(0, 3);
      const pu = new Set(pinned.map(j => j.u));
      list = list.filter(j => !pu.has(j.u));
    }
    const total = list.length + pinned.length;
    $('count').textContent = t('nRoles')(total, state.saved);
    $('empty').hidden = total > 0;
    $('applyBtn').textContent = t('showN')(total);
    renderActiveChips();
    $('list').innerHTML = pinned.map(j => jobRow(j, true)).join('') +
      list.slice(0, state.shown).map(j => jobRow(j, false)).join('');
    $('morebar').hidden = list.length <= state.shown;
    if (io) $('list').querySelectorAll('.job[data-spdev]').forEach(el => io.observe(el));
  }
  $('more').addEventListener('click', () => { state.shown += 80; render(); });
  $('list').addEventListener('click', e => {
    const sv = e.target.closest('.sav');
    if (sv) { e.stopPropagation(); const u = sv.dataset.u; savedSet.has(u) ? savedSet.delete(u) : savedSet.add(u); LS.set('baj_sav', [...savedSet]); render(); return; }
    const ap = e.target.closest('.apply');
    if (ap) { e.stopPropagation(); if (ap.dataset.spc) bump(ap.dataset.spc, 'c', ap.getAttribute('href')); return; }
    const row = e.target.closest('.job'); if (row) openCo(+row.dataset.ci, row.dataset.ju);
  });
  setTimeout(() => { JOBS.forEach(j => seen.add(j.u)); LS.set('baj_seen', [...seen].slice(-3000)); }, 5000);

  const linkCos = COS.filter(c => c.tier === 2 && !(c.jobs || []).length);
  function renderLinkonly() {
    if (!linkCos.length) return;
    $('linkonly').innerHTML = `<h2 class="sec">${t('linkT')}</h2><p class="secsub">${t('linkB')}</p>` +
      linkCos.sort((a, b) => b.v - a.v).map(c => `<div class="job" data-ci="${c.ci}">${icoHtml(c)}
        <div class="jbody"><div class="jtop"><span class="jco">${esc(c.city)}</span></div>
        <div class="jt"><span class="tt">${esc(c.n)}</span></div>
        <div class="jmeta"><span>${esc(c.apps[0].t)}</span>${c.total ? `<span>${t('nOpen')(c.total)}</span>` : ''}<span class="dx">${INST(c.v) ? INST(c.v) + t('androidP') : ''}</span></div></div>
        <a class="apply" href="${esc(c.careers || '#')}" target="_blank" rel="noopener">${t('careers')}</a></div>`).join('');
  }
  $('linkonly').addEventListener('click', e => { const row = e.target.closest('.job'); if (row) openCo(+row.dataset.ci); });

  // ---------- leaderboard ----------
  (function () {
    const byDev = {}; COS.forEach(c => byDev[c.n] = c);
    const lbState = { store: 'play', cat: '', q: '', shown: 100 };
    const isHiring = e => { const co = byDev[e.dev]; return !!(co && co.tier <= 2); };
    const played = CHARTS.play.filter(isHiring), iosed = CHARTS.ios.filter(isHiring);
    const catCount = {}; played.forEach(e => catCount[e.g] = (catCount[e.g] || 0) + 1);
    const topCats = Object.entries(catCount).sort((a, b) => b[1] - a[1]).slice(0, 8).map(x => x[0]);
    function renderLbCats() {
      $('lbcats').innerHTML = ['<button class="chip' + (lbState.cat === '' ? ' on' : '') + '" data-c="">' + t('all') + '</button>']
        .concat(topCats.map(c => `<button class="chip${lbState.cat === c ? ' on' : ''}" data-c="${esc(c)}">${esc(c)}</button>`)).join('');
    }
    $('lbcats').addEventListener('click', e => { const b = e.target.closest('.chip'); if (!b) return; lbState.cat = b.dataset.c; lbState.shown = 100; renderLb(); });
    let lbdeb;
    $('lbq').addEventListener('input', e => { clearTimeout(lbdeb); lbdeb = setTimeout(() => { lbState.q = e.target.value.trim().toLowerCase(); lbState.shown = 100; renderLb(); }, 120); });
    $('storetoggle').addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      lbState.store = b.dataset.store; lbState.shown = 100;
      document.querySelectorAll('#storetoggle button').forEach(x => x.classList.toggle('on', x === b));
      renderLb();
    });
    function renderLb() {
      renderLbCats();
      const src = lbState.store === 'play' ? played : iosed;
      document.querySelector('#charts h2').textContent = t('lbH2');
      $('lbq').placeholder = t('lbFind');
      $('lbsub').textContent = lbState.store === 'play' ? t('lbSubPlay')(played.length) : t('lbSubIos')(iosed.length);
      let list = src.filter(e => (!lbState.cat || e.g === lbState.cat) && (!lbState.q || (e.t + ' ' + e.dev).toLowerCase().includes(lbState.q)));
      $('lblist').innerHTML = list.slice(0, lbState.shown).map((e, i) => {
        const co = byDev[e.dev]; const hire = co && co.tier <= 2;
        const icon = ICONS[e.id] ? `<img src="${ICONS[e.id]}" alt="" loading="lazy">` : (co && co.icon ? `<img src="${co.icon}" alt="" loading="lazy">` : `<span class="co-ic">${esc(e.t[0])}</span>`);
        const rank = i + 1;
        const right = lbState.store === 'play'
          ? `<div class="big">${esc(e.inst)}</div><div class="sub">${t('instSub')}${e.rev ? ' · ' + fmtN(e.rev) + t('revSub') : ''}</div>`
          : `<div class="big">${fmtN(e.rc)}</div><div class="sub">${t('rateSub')}${e.avg ?? '–'}</div>`;
        const badge = lbState.store === 'play' ? `<span class="cbadge">#${e.crank} · <span class="cb-coll">${esc(e.ccoll)} · </span>${esc(e.g)}</span>` : `<span class="cbadge">${esc(e.g)}</span>`;
        return `<div class="lb${rank <= 3 ? ' m' + rank : ''}" data-dev="${esc(e.dev)}">
          <div class="rk">${rank <= 3 ? ['🥇','🥈','🥉'][rank - 1] : '#' + rank}</div>${icon}
          <div class="mid"><div class="t">${esc(e.t)}</div>
          <div class="s">${hire ? `<span><span class="hiredot"></span>${t('hiring')}</span><span class="sep">·</span>` : ''}<span>${esc(e.dev)}</span> ${badge}</div></div>
          <div class="right">${right}</div></div>`;
      }).join('') || `<div class="empty"><b>${t('lbEmptyT')}</b>${t('lbEmptyB')}</div>`;
      $('lbmorebar').hidden = list.length <= lbState.shown;
    }
    $('lbmore').addEventListener('click', () => { lbState.shown = 9999; renderLb(); });
    $('lblist').addEventListener('click', e => { const row = e.target.closest('.lb'); if (!row) return; const co = byDev[row.dataset.dev]; if (co) openCo(co.ci); });
    window.__renderLb = renderLb;
  })();

  // ---------- guides ----------
  const GUIDES_LIST = (typeof GUIDES !== 'undefined' ? GUIDES : []);
  // guides follow the selected language; the other language stays one click away. A guide with a translation only shows in the viewer's language.
  let guidesShowOther = false;
  function guideSets() {
    const idx = GUIDES_LIST.map((g, i) => ({ g, i }));
    const mine = idx.filter(x => x.g.lang === L);
    const mineSlugs = new Set(mine.map(x => x.g.slug));
    const other = idx.filter(x => x.g.lang !== L && !(x.g.pair && mineSlugs.has(x.g.pair)));
    return { mine, other };
  }
  // Each guide is a real page at /guides/<slug>/ (its own URL to share, rank and track), so cards are plain links.
  const gurl = g => '/guides/' + encodeURIComponent(g.slug) + '/';
  const gcard = ({ g }) => `<a class="gcard" href="${gurl(g)}" hreflang="${g.lang}">
      <div class="gt">${esc(g.title)}</div>
      <div class="gd">${esc(g.desc)}</div>
      <div class="gmeta"><span class="glang">${g.lang.toUpperCase()}</span><span class="gread">${t('readGuide')} →</span></div>
    </a>`;
  function renderGuides() {
    const { mine, other } = guideSets();
    $('guideList').innerHTML = mine.map(gcard).join('') +
      (other.length ? `<div class="gother"><button class="gmore" id="gmore">${guidesShowOther ? t('fewerGuides') : t('moreGuides')(other.length)}</button></div>` +
        (guidesShowOther ? `<h3 class="gotherh">${t('otherLangH')}</h3>` + other.map(gcard).join('') : '') : '');
  }
  $('guideList').addEventListener('click', e => { if (e.target.closest('#gmore')) { guidesShowOther = !guidesShowOther; renderGuides(); } });
  if (location.hash === '#guides') setTab('guides', true);   // deep link to the Guides tab (after the guide code above is defined)

  // ---------- companies ----------
  function renderCos() {
    const hg = hiringCos.slice().sort((a, b) => (b.jobs.length - a.jobs.length) || (b.v - a.v));
    $('sgrid').innerHTML = hg.map(c => `<div class="sc" data-ci="${c.ci}">${icoHtml(c)}
        <div class="m"><div class="n">${esc(c.n)}${sponDevs().has(c.n) ? ' <span class="sponb">★</span>' : ''}</div>
        <div class="s">${esc(c.apps[0].t)} · ${esc(c.city)}${INST(c.v) ? ' · ' + INST(c.v) + t('androidP') : ''}</div>
        <div class="s">${c.jobs.length ? `<b style="color:var(--good)">${t('openRoles')(c.jobs.length)}</b>` : `<b style="color:var(--accent)">${c.total ? t('rolesOn')(c.total) : t('hiringLink')} ↗</b>`}</div></div></div>`).join('');
    const dorm = COS.filter(c => c.tier === 3).sort((a, b) => b.v - a.v);
    $('dormsum').textContent = t('dorm')(dorm.length);
    $('dgrid').innerHTML = dorm.map(c => `<div class="sc" style="opacity:.6" data-ci="${c.ci}">${icoHtml(c)}
        <div class="m"><div class="n">${esc(c.n)}</div><div class="s">${esc(c.apps[0].t)} · ${esc(c.city)}${INST(c.v) ? ' · ' + INST(c.v) + t('androidP') : ''}</div></div></div>`).join('');
  }
  $('studios').addEventListener('click', e => { const el = e.target.closest('.sc'); if (el) openCo(+el.dataset.ci); });

  // ---------- company panel ----------
  function cpJobRow(j, c, focus) {
    const wp = /hybrid/.test((j.t + ' ' + (j.loc || '')).toLowerCase()) ? 'hybrid' : (j.rem ? 'remote' : 'office');
    return `<div class="cp-job${focus ? ' focus' : ''}"><div><div class="t">${esc(j.t)}</div><div class="m">${esc(j.loc === 'Berlin' ? c.city : j.loc)} · ${t('wp')[wp]}${j.sal ? ' · <b>' + esc(salShort(j.sal)) + '</b>' : ''}${j.p ? ' · ' + relTime(j.p) : ''}</div></div><a class="${focus ? 'cpapply' : ''}" href="${esc(j.u)}" target="_blank" rel="noopener" data-spc="${esc(c.n)}">${t('apply')}</a></div>`;
  }
  function openCo(ci, focusU) {
    const c = COS[ci]; hideTip();
    $('cp-ic').innerHTML = icoHtml(c);
    $('cp-name').textContent = c.n;
    $('cp-addr').textContent = c.addr;
    $('cp-legal').textContent = c.legal && c.legal !== c.n ? t('regAs') + c.legal : '';
    $('cp-ext').hidden = !c.ext;
    const jobs = (c.jobs || []).slice();
    if (focusU) jobs.sort((a, b) => (a.u === focusU ? -1 : 0) - (b.u === focusU ? -1 : 0));
    $('cp-jobs').innerHTML = jobs.length
      ? jobs.map(j => cpJobRow(j, c, focusU && j.u === focusU)).join('')
      : (c.tier === 2
          ? `<a class="cp-extroles" href="${esc(c.careers || '#')}" target="_blank" rel="noopener"><div><div class="ttl">${c.total ? t('rolesOn')(c.total) : t('seeCareers')}</div><div class="sub">${t('extrolesSub')}</div></div><span class="arr">↗</span></a>`
          : `<div class="cp-job"><div class="t" style="color:var(--muted)">${t('noRoles')}</div></div>`);
    const ca = $('cp-careers');
    ca.textContent = t('cpCta');
    if (c.careers) { ca.href = c.careers; ca.hidden = false; } else ca.hidden = true;
    $('cp-apps').innerHTML = c.apps.map(a => {
      const ios = IOS[a.id];
      return `<div class="cp-app"><div style="min-width:0"><div class="an">${esc(a.t)}</div>
        <div class="meta">${a.i ? esc(a.i) + t('instA') : ''}${ios ? (a.i ? ' · ' : '') + fmtN(ios.rc) + t('ratI') : ''}</div></div>
        <div class="stores"><a href="https://play.google.com/store/apps/details?id=${encodeURIComponent(a.id)}" target="_blank" rel="noopener">Play</a>${ios ? `<a href="${esc(ios.url)}" target="_blank" rel="noopener">iOS</a>` : ''}</div></div>`;
    }).join('');
    $('shade').classList.add('on'); $('cp').classList.add('on');
  }
  function closeAll() { $('shade').classList.remove('on'); $('cp').classList.remove('on'); $('pm').classList.remove('on'); }
  $('cp-jobs').addEventListener('click', e => { const a = e.target.closest('a[data-spc]'); if (a && sponDevs().has(a.dataset.spc)) bump(a.dataset.spc, 'c', a.getAttribute('href')); });
  $('cp-x').addEventListener('click', closeAll);
  $('shade').addEventListener('click', closeAll);
  addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });

  // ---------- promote modal ----------
  function renderPm() {
    const fc = COS.find(c => c.n === 'Freecash');
    $('slots').innerHTML = [1, 2, 3].map(i => `<div class="slot held">
        <div class="rk2">#${i}</div>
        ${fc ? icoHtml(fc) : '<span class="co-ic">F</span>'}
        <div class="m"><div class="n">Freecash</div><div class="s">${t('booked')}</div></div>
        <span class="claim sold">${t('soldOut')}</span>
      </div>`).join('');
    $('actFeed').innerHTML = t('pmActs').map(([d, w, when]) => `<div class="act"><span><b>${esc(d)}</b> ${esc(w)}</span><span>${esc(when)}</span></div>`).join('');
  }

  $('promoBtn').addEventListener('click', () => { renderPm(); $('shade').classList.add('on'); $('pm').classList.add('on'); });
  $('pm-x').addEventListener('click', closeAll);

  // ---------- map (Germany, opens zoomed on Berlin) ----------
  function hideTip() { const tp = $('mtip'); if (tp) tp.style.display = 'none'; }
  addEventListener('scroll', hideTip, { passive: true });
  function buildMap() {
    const svg = $('bmap'), NS = 'http://www.w3.org/2000/svg';
    const el = (n, at, p) => { const e = document.createElementNS(NS, n); for (const k in at) e.setAttribute(k, at[k]); (p || svg).appendChild(e); return e; };
    const [BX0, BFX, BY0, BFY] = GEO.bx;
    const world = el('g', {});
    const defs = el('defs', {}, world);
    const gS = el('g', {}, world);
    for (const st of GEO.states) el('path', { class: 'state', d: st.d }, gS);
    const gB = el('g', { transform: `translate(${BX0},${BY0}) scale(${BFX},${BFY})` }, world);
    const gD = el('g', {}, gB), gL = el('g', {}, gB);
    for (const d of BOARD.districts) {
      el('path', { class: 'district', d: d.d }, gD);
      const tl = el('text', { class: 'dlabel', x: d.cx, y: d.cy, 'font-size': 15 }, gL);
      tl.textContent = d.name;
    }
    const gQ = el('g', {}, world), gM = el('g', {}, world), gC = el('g', {}, world);
    const sd = sponDevs();
    const nJobs = c => (c.jobs || []).length || (c.tier === 2 ? Math.min(c.total || 1, 40) : 0);
    const R = c => { const n = nJobs(c); return n > 0 ? Math.min(30, 9 + 4.2 * Math.sqrt(n)) : 0; };

    let vw = svg.clientWidth || 900, vh = svg.clientHeight || 600;
    svg.setAttribute('viewBox', `0 0 ${vw} ${vh}`);
    const fitB = Math.min(vw / (BOARD.W * BFX), vh / (BOARD.H * BFY));
    const kDef = fitB * 1.5;
    const fitG = Math.min(vw / GEO.W, vh / GEO.H) * 0.96;
    const kSwitch = kDef * 0.3;
    let berlinC = [BX0 + BFX * BOARD.W * 0.52, BY0 + BFY * BOARD.H * 0.42];

    // positions: Berlin companies at their street address; elsewhere a sunflower spiral around the city centre
    const byCity = {};
    COS.forEach(c => {
      if (c.x != null && c.city === 'Berlin') { c.X = BX0 + BFX * c.x; c.Y = BY0 + BFY * c.y; }
      else if (GEO.cities[c.city]) (byCity[c.city] = byCity[c.city] || []).push(c);
    });
    const sp = 24 / kDef;
    for (const [city, list] of Object.entries(byCity)) {
      const [cx, cy] = GEO.cities[city];
      list.sort((a, b) => nJobs(b) - nJobs(a) || b.v - a.v);
      list.forEach((c, i) => { const r = sp * Math.sqrt(i) * 1.15, a = i * 2.39996; c.X = cx + r * Math.cos(a); c.Y = cy + r * Math.sin(a); });
    }
    const marks = COS.filter(c => c.X != null);
    { const bh = COS.filter(c => c.city === 'Berlin' && c.x != null && nJobs(c) > 0); if (bh.length) { const xs = bh.map(c => c.X).sort((a, b) => a - b), ys = bh.map(c => c.Y).sort((a, b) => a - b); berlinC = [xs[xs.length >> 1], ys[ys.length >> 1]]; } }
    const gCN = el('g', {}, world), cityLabels = [];
    for (const [city, list] of Object.entries(byCity)) {
      if (city === 'Berlin') continue;
      const [cx, cy] = GEO.cities[city], rad = sp * Math.sqrt(Math.max(0, list.length - 1)) * 1.15;
      const tl = el('text', { class: 'dlabel cname', x: cx, y: cy - rad - 34 / kDef }, gCN); tl.textContent = city;
      cityLabels.push(tl);
    }

    // company markers
    const radii = new Set();
    marks.forEach(c => { const r = Math.round(R(c)); if (r) radii.add(r); });
    for (const r of radii) { const cp = el('clipPath', { id: 'bcp' + r, clipPathUnits: 'userSpaceOnUse' }, defs); el('circle', { cx: 0, cy: 0, r: r - 1 }, cp); }
    const nodes = [];
    marks.sort((a, b) => nJobs(a) - nJobs(b));
    for (const c of marks) {
      const n = nJobs(c);
      if (!n) { el('circle', { class: 'quietdot', cx: c.X, cy: c.Y, r: 0.05 }, gQ); continue; }
      const r = Math.round(R(c));
      const g = el('g', { class: 'bmk hire' + (sd.has(c.n) ? ' sponm' : ''), 'data-ci': c.ci }, gM);
      el('circle', { class: 'ring', r: r + 1.2 }, g);
      if (c.icon) el('image', { href: c.icon, x: -r, y: -r, width: 2 * r, height: 2 * r, 'clip-path': 'url(#bcp' + r + ')', preserveAspectRatio: 'xMidYMid slice' }, g);
      else { el('circle', { r: r - 1, fill: '#1A2138' }, g); const tt = el('text', { fill: '#B8B5A3', 'text-anchor': 'middle', dy: 4, 'font-size': r * 0.8, 'font-weight': 700 }, g); tt.textContent = c.n[0]; }
      el('circle', { class: 'cntbg', cx: r * 0.78, cy: -r * 0.78, r: 8.5 }, g);
      const tt = el('text', { class: 'cnt', x: r * 0.78, y: -r * 0.78, dy: 3.5 }, g);
      tt.textContent = n > 99 ? '99' : n;
      c._g = g; nodes.push(c);
    }

    // city bubbles (shown when zoomed out)
    const CITYAGG = {};
    COS.forEach(c => {
      const n = nJobs(c); if (!n) return;
      const ll = GEO.cities[c.city]; if (!ll) return;
      const a = CITYAGG[c.city] = CITYAGG[c.city] || { n: c.city, X: ll[0], Y: ll[1], cos: 0, roles: 0 };
      a.cos++; a.roles += n;
    });
    const cities = Object.values(CITYAGG).sort((a, b) => a.roles - b.roles);
    for (const a of cities) {
      const r = Math.min(30, 5 + 1.5 * Math.sqrt(a.roles));
      a.r = r;
      a._g = el('g', { class: 'cbub', 'data-city': a.n }, gC);
      el('circle', { class: 'b', r }, a._g);
      if (r >= 10) { const tc = el('text', { class: 'c', dy: 4 }, a._g); tc.textContent = a.roles > 999 ? fmtN(a.roles) : a.roles; }
      a._l = el('text', { class: 'l', x: r + 5, dy: 4 }, a._g); a._l.textContent = a.n;
    }
    const citiesByRoles = cities.slice().sort((a, b) => b.roles - a.roles);

    let k = kDef, tx = vw / 2 - berlinC[0] * k, ty = vh / 2 - berlinC[1] * k;
    let lastLow = null;
    function apply() {
      world.setAttribute('transform', `translate(${tx},${ty}) scale(${k})`);
      const low = k < kSwitch;
      if (low !== lastLow) { gM.style.display = gQ.style.display = gL.style.display = gCN.style.display = low ? 'none' : ''; gC.style.display = low ? '' : 'none'; lastLow = low; hideTip(); }
      if (!low) {
        const s = (0.92 / k) * Math.pow(k / kDef, 0.38);
        for (const c of nodes) c._g.setAttribute('transform', `translate(${c.X},${c.Y}) scale(${s})`);
        const qs = (2.6 / k) * Math.pow(k / kDef, 0.38);
        for (const d of gQ.children) d.setAttribute('r', qs);
        const lf = (12.5 / (k * BFX)) * Math.pow(k / kDef, 0.22);
        for (const tl of gL.children) tl.setAttribute('font-size', lf);
        gL.style.opacity = k < kDef * 0.6 ? 0 : 1;
        const cf = 13 / k; for (const tl of cityLabels) tl.setAttribute('font-size', cf);
      } else {
        const inv = 1 / k;
        for (const a of cities) a._g.setAttribute('transform', `translate(${a.X},${a.Y}) scale(${inv})`);
        const placed = citiesByRoles.filter(a => a.r >= 12).map(a => [a.X * k - a.r, a.Y * k - a.r, a.X * k + a.r, a.Y * k + a.r, a]);
        const minRoles = k > fitG * 2.2 ? 1 : k > fitG * 1.4 ? 5 : 12;
        citiesByRoles.forEach((a, rank) => {
          let show = false;
          if (a.roles >= minRoles) {
            const w = a.n.length * 6.6 + 4, h = 14, cx = a.X * k, cy = a.Y * k - 7;
            for (const side of [1, -1]) {
              const x0 = side > 0 ? cx + a.r + 4 : cx - a.r - 4 - w;
              const bx = [x0, cy, x0 + w, cy + h];
              if (!placed.some(p => p[4] !== a && (rank >= 8 || !p[4]) && bx[0] < p[2] && bx[2] > p[0] && bx[1] < p[3] && bx[3] > p[1])) {
                a._l.setAttribute('x', side > 0 ? a.r + 5 : -a.r - 5); a._l.setAttribute('text-anchor', side > 0 ? 'start' : 'end');
                placed.push(bx); show = true; break;
              }
            }
          }
          a._l.style.display = show ? '' : 'none';
        });
      }
    }
    apply();
    const clampK = nk => Math.min(kDef * 16, Math.max(fitG * 0.85, nk));
    function zoomAt(nk, px, py) { nk = clampK(nk); tx = px - (px - tx) * (nk / k); ty = py - (py - ty) * (nk / k); k = nk; requestAnimationFrame(apply); }
    let anim = 0;
    function flyTo(X, Y, nk) {
      nk = clampK(nk); cancelAnimationFrame(anim); hideTip();
      const k0 = k, cx0 = (vw / 2 - tx) / k, cy0 = (vh / 2 - ty) / k, t0 = performance.now(), D = 520;
      const step = now => {
        const p = Math.min(1, (now - t0) / D), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
        k = Math.exp(Math.log(k0) + (Math.log(nk) - Math.log(k0)) * e);
        const cx = cx0 + (X - cx0) * e, cy = cy0 + (Y - cy0) * e;
        tx = vw / 2 - cx * k; ty = vh / 2 - cy * k; apply();
        if (p < 1) anim = requestAnimationFrame(step);
      };
      anim = requestAnimationFrame(step);
    }
    const resetView = () => flyTo(berlinC[0], berlinC[1], kDef);
    const germanyView = () => flyTo(GEO.W / 2, GEO.H / 2, fitG);
    const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
    svg.addEventListener('wheel', e => { e.preventDefault(); hideTip(); cancelAnimationFrame(anim); const rc = svg.getBoundingClientRect(); zoomAt(k * Math.exp(-e.deltaY * 0.0016), e.clientX - rc.left, e.clientY - rc.top); }, { passive: false });

    // pointer handling: taps open things, drags pan; capture only once a real drag starts (capturing on pointerdown swallowed clicks and stranded the tooltip)
    const pts = new Map(); let pinch = null, down = null, moved = false;
    svg.addEventListener('pointerdown', e => {
      pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pts.size === 1) { down = { x: e.clientX, y: e.clientY }; moved = false; }
      if (pts.size === 2) { moved = true; hideTip(); cancelAnimationFrame(anim); const a = [...pts.values()]; pinch = { d: dist(a[0], a[1]), k }; try { svg.setPointerCapture(e.pointerId); } catch (_) {} }
    });
    svg.addEventListener('pointermove', e => {
      if (!pts.has(e.pointerId)) { if (e.pointerType === 'mouse' && $('mtip').style.display === 'block') mtipMove(e); return; }
      const prev = pts.get(e.pointerId); pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (!moved) {
        if (Math.hypot(e.clientX - down.x, e.clientY - down.y) < 5) return;
        moved = true; hideTip(); cancelAnimationFrame(anim); svg.classList.add('dragging');
        try { svg.setPointerCapture(e.pointerId); } catch (_) {}
      }
      const rc = svg.getBoundingClientRect();
      if (pts.size === 2 && pinch) { const a = [...pts.values()]; const nd = dist(a[0], a[1]); zoomAt(pinch.k * (nd / pinch.d), (a[0].x + a[1].x) / 2 - rc.left, (a[0].y + a[1].y) / 2 - rc.top); }
      else if (pts.size === 1) { tx += e.clientX - prev.x; ty += e.clientY - prev.y; requestAnimationFrame(apply); }
    });
    const endp = e => {
      pts.delete(e.pointerId); if (pts.size < 2) pinch = null;
      if (pts.size === 0) svg.classList.remove('dragging');
    };
    // open on click (not pointerup): on touch, opening during pointerup let the follow-up click land on the new overlay and close it again
    svg.addEventListener('click', e => {
      if (moved) return;
      const g = e.target.closest ? e.target.closest('.bmk, .cbub') : null;
      hideTip();
      if (!g) return;
      if (g.classList.contains('bmk')) openCo(+g.dataset.ci);
      else { const a = CITYAGG[g.dataset.city]; if (a) flyTo(a.X, a.Y, a.n === 'Berlin' ? kDef : kDef * 0.9); }
    });
    svg.addEventListener('pointerup', endp); svg.addEventListener('pointercancel', endp);
    // hover tooltip (mouse only), delegated so re-renders can't strand it
    svg.addEventListener('pointerover', e => {
      if (e.pointerType !== 'mouse' || pts.size) return;
      const g = e.target.closest && e.target.closest('.bmk, .cbub'); if (!g) return;
      if (g.classList.contains('bmk')) mtipShow(COS[+g.dataset.ci], e);
      else { const a = CITYAGG[g.dataset.city]; if (a) { $('mtip').innerHTML = `<div class="a">${esc(a.n)}</div><div class="b">${t('cityTip')(a.cos, a.roles)}</div><div class="b" style="color:#FFD400">${t('zoomIn')}</div>`; $('mtip').style.display = 'block'; mtipMove(e); } }
    });
    svg.addEventListener('pointerout', e => { const g = e.target.closest && e.target.closest('.bmk, .cbub'); if (g && !(e.relatedTarget && g.contains(e.relatedTarget))) hideTip(); });
    svg.addEventListener('pointerleave', hideTip);
    const ctl = svg.parentElement.querySelector('.mapctl');
    if (ctl) ctl.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; hideTip(); if (b.dataset.z === 'in') zoomAt(k * 1.6, vw / 2, vh / 2); else if (b.dataset.z === 'out') zoomAt(k / 1.6, vw / 2, vh / 2); else if (b.dataset.z === 'de') germanyView(); else resetView(); });
    addEventListener('resize', () => { const cx = (vw / 2 - tx) / k, cy = (vh / 2 - ty) / k; vw = svg.clientWidth; vh = svg.clientHeight; svg.setAttribute('viewBox', `0 0 ${vw} ${vh}`); tx = vw / 2 - cx * k; ty = vh / 2 - cy * k; apply(); });
    function mtipShow(c, ev) {
      const n = nJobs(c);
      $('mtip').innerHTML = `<div class="a">${esc(c.n)}${sd.has(c.n) ? ` · <span style="color:#FFD400">${t('sponsor')}</span>` : ''}</div><div class="b">${esc(c.apps[0].t)} · ${esc(c.city)}${INST(c.v) ? ' · ' + INST(c.v) + t('androidP') : ''}</div><div class="b">${n ? t('openN')(n) : t('notHiring')}</div>`;
      $('mtip').style.display = 'block'; mtipMove(ev);
    }
    function mtipMove(ev) {
      const tip = $('mtip'), pad = 14;
      let x = ev.clientX + pad, y = ev.clientY + pad;
      if (x + tip.offsetWidth > innerWidth - 8) x = ev.clientX - tip.offsetWidth - pad;
      if (y + tip.offsetHeight > innerHeight - 8) y = ev.clientY - tip.offsetHeight - pad;
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
    }
  }

  // ---------- language ----------
  function applyLang() {
    try { document.documentElement.lang = L; } catch (e) {}
    document.querySelectorAll('#langtog button').forEach(b => b.classList.toggle('on', b.dataset.lang === L));
    $('st-l1').textContent = t('roles'); $('st-l2').textContent = t('cosHiring');
    $('tb-jobs').textContent = t('tJobs'); $('tb-charts').textContent = t('tCharts'); $('tb-cos').textContent = t('tCos'); $('tb-map').textContent = t('tMap');
    $('promoBtn').textContent = t('promo');
    $('introH1').innerHTML = t('introH1'); $('introSub').textContent = t('introSub');
    $('q').placeholder = t('search'); if ($('mq')) $('mq').placeholder = t('search');
    $('salOnlyLbl').textContent = t('salOnly'); $('mFiltersT').textContent = t('filtersBtn'); $('sheetHeadT').textContent = t('filterHead');
    $('hCity').textContent = t('hCity'); $('hDisc').textContent = t('hDisc'); $('hDet').textContent = t('hDet');
    $('savedLbl').textContent = t('saved'); $('reset').textContent = t('reset');
    $('empty').innerHTML = `<b>${t('emptyT')}</b>${t('emptyB')}`;
    $('more').textContent = t('more'); $('lbmore').textContent = t('lbMore');
    $('cosH2').textContent = t('cosH2'); $('cosSub').textContent = t('cosSub');
    $('tb-guides').textContent = t('tGuides'); $('bnMore').textContent = t('moreNav'); $('ms-cos').textContent = t('tCos'); $('ms-guides').textContent = t('tGuides'); $('ms-promo').textContent = t('promo'); $('guidesH2').textContent = t('guidesH2'); $('guidesSub').textContent = t('guidesSub'); if (!$('guides').hidden) renderGuides();
    $('mapH2').textContent = t('mapH2'); $('mapSub').textContent = t('mapSub');
    document.querySelector('.maplegend').innerHTML = t('legend');
    $('cpH1').textContent = t('cpH1'); $('cpH2').textContent = t('cpH2');
    $('cp-ext').textContent = t('ext');
    $('pmTitle').textContent = t('pmTitle'); $('pmSub').textContent = t('pmSub');
    $('pmH1').textContent = t('pmH1');
    $('pmSoonT').textContent = t('pmSoonT'); $('pmSoonD').textContent = t('pmSoonD'); $('pmEmail').textContent = t('pmEmail');
    $('pmH3').textContent = t('pmH3'); $('pmFine').textContent = t('pmFine');
    $('seoH2').textContent = t('seoH2');
    $('seoBody').innerHTML = t('seoBody');
    $('seoFaq').innerHTML = t('faq').map(([q, a]) => `<details style="border-top:1px solid var(--line);padding:9px 0"><summary style="cursor:pointer;font-weight:600;font-size:13px">${q}</summary><p style="color:var(--muted);font-size:12.5px;margin:7px 0 0;max-width:70ch">${a}</p></details>`).join('');
    $('foot').innerHTML = t('foot');
    fillSelects();
    renderSide();
    renderLinkonly();
    renderCos();
    render();
    if (window.__renderLb) window.__renderLb();
  }
  $('langtog').addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b || b.dataset.lang === L) return;
    L = b.dataset.lang; LS.set('ak_lang', L); applyLang();
  });

  applyLang();
})();
