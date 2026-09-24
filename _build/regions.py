# German state (Bundesland) for each company city on the board, for JobPosting addressRegion.
# Ambiguous town names were resolved via the company's postcode (e.g. Neunkirchen 57290 = NRW, Friedberg 86316 = Bayern).
_BY = 'Bayern'; _BW = 'Baden-Württemberg'; _NW = 'Nordrhein-Westfalen'; _NI = 'Niedersachsen'; _HE = 'Hessen'
_RP = 'Rheinland-Pfalz'; _SH = 'Schleswig-Holstein'; _SL = 'Saarland'; _TH = 'Thüringen'; _SN = 'Sachsen'
_ST = 'Sachsen-Anhalt'; _BB = 'Brandenburg'
REGION = {
 'Berlin': 'Berlin', 'Hamburg': 'Hamburg', 'Bremen': 'Bremen', 'Bremerhaven': 'Bremen',
 'Aachen': _NW, 'Arnsberg': _NW, 'Bergkamen': _NW, 'Bochum': _NW, 'Bonn': _NW, 'Düsseldorf': _NW, 'Essen': _NW,
 'Gelsenkirchen': _NW, 'Hüllhorst': _NW, 'Köln': _NW, 'Krefeld': _NW, 'Meckenheim': _NW, 'Mülheim an der Ruhr': _NW,
 'Münster': _NW, 'Neunkirchen': _NW, 'Siegen': _NW, 'Solingen': _NW, 'Steinhagen': _NW, 'Troisdorf': _NW, 'Windeck': _NW,
 'Augsburg': _BY, 'Bad Steben': _BY, 'Baierbrunn': _BY, 'Freising': _BY, 'Friedberg': _BY, 'Gaimersheim': _BY,
 'Grünwald': _BY, 'Herzogenaurach': _BY, 'Immenstadt i. Allgäu': _BY, 'Ingolstadt': _BY, 'Ismaning': _BY,
 'Maxhütte-Haidhof': _BY, 'München': _BY, 'Nürnberg': _BY, 'Oberhaching': _BY, 'Planegg': _BY, 'Pressath': _BY,
 'Pullach i. Isartal': _BY, 'Rottendorf': _BY, 'Schlüsselfeld': _BY, 'Starnberg': _BY, 'Wendelstein': _BY, 'Würzburg': _BY,
 'Bad Friedrichshall': _BW, 'Freiburg im Breisgau': _BW, 'Heidelberg': _BW, 'Heidenheim an der Brenz': _BW,
 'Heilbronn': _BW, 'Karlsruhe': _BW, 'Mannheim': _BW, 'Metzingen': _BW, 'Offenburg': _BW, 'Rust': _BW,
 'Schwäbisch Hall': _BW, 'Stuttgart': _BW, 'Ulm': _BW, 'Walldorf': _BW,
 'Bad Nauheim': _HE, 'Frankfurt am Main': _HE, 'Fulda': _HE, 'Kassel': _HE, 'Obertshausen': _HE,
 'Braunschweig': _NI, 'Burgwedel': _NI, 'Emmerthal': _NI, 'Hannover': _NI, 'Oldenburg': _NI, 'Soltau': _NI, 'Wolfsburg': _NI,
 'Höhr-Grenzhausen': _RP, 'Koblenz': _RP, 'Trier': _RP,
 'Büdelsdorf': _SH, 'Kiel': _SH, 'Schönkirchen': _SH,
 'Völklingen': _SL, 'Erfurt': _TH, 'Jena': _TH, 'Leipzig': _SN, 'Magdeburg': _ST, 'Schönefeld': _BB,
}
