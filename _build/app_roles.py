# -*- coding: utf-8 -*-
"""Which jobs belong on the board (Jop, 12 Oct 2026): only jobs we are confident have an impact on the app.

  * App-first companies (APP_FIRST: the app, website or software is the product): every office role counts, because the
    whole company works on the product. Store, restaurant, warehouse, driving, field and clinical roles do not.
  * Every other company (retail chains, banks, insurers, gyms, utilities, transport, publishers, manufacturers): only
    digital roles count: software, data, product, UX/UI design, QA, app/online marketing, e-commerce, CRM.
    "If someone at McFIT works on the app, it should be listed"; a McFIT trainer should not.
  * App-first companies get a higher cap (CAP_APP_FIRST) than the rest (CAP).

Used by refresh_jobs.py (new ads before the cap, and the jobs already on the board) and by the readers in ats_more.py
(titles are checked before the ad pages are opened, so store ads don't use up the reading budget).
A company that is not in APP_FIRST is treated strictly; add a company here only when its main product is digital.
"""
import re

CAP = 60              # jobs per company
CAP_APP_FIRST = 200   # jobs per app-first company (Jop, 12 Oct 2026: "app and tech companies should have a higher cap")

# Exact company names from board_data.js ("n"). Checked by hand on 12 Oct 2026 against each company's app and jobs.
APP_FIRST = {
    # apps, games and consumer platforms
    'Algoriddim', 'Atolls', 'Audials Radio Software', 'Bling Services GmbH', 'Bloomwell GmbH', 'bonify', 'Carly Solutions GmbH & Co KG',
    'celebrate apps', 'Changers.com / Blacksquared GmbH', 'Clue Period Tracker by BioWink', 'Conntac GmbH', 'DeepL', 'Dermanostic GmbH',
    'Dogorama GmbH', 'dwins GmbH', 'Dyn Media GmbH', 'EatSmarter', 'Edkon Games GmbH', 'Edurino GmbH', 'EGYM', 'falkemedia digital GmbH',
    'felmo GmbH', 'fillibri GmbH & Co. KG', 'Finanztip Verbraucherinformation GmbH', 'Finflow GmbH', 'Flink SE', 'Flix SE',
    'FLOYT Mobility GmbH', 'foodora (Delivery Hero)', 'Freecash', 'freenet.de GmbH', 'Fryd GmbH', 'GamerProfiles', 'gesund.de GmbH & Co. KG.',
    'GetYourGuide', 'Good Hood GmbH', 'GOREHA GmbH', 'Grover Group GmbH', 'Gryphon Games', 'Gymondo GmbH', 'H2 Technologies GmbH',
    'Helpling group', 'Holidu GmbH', 'HomeToGo', 'Horizon Alpha GmbH & Co KG', 'IhreApotheken GmbH & Co. KGaA', 'InStaff & Jobs GmbH',
    'InstiKom GmbH', 'Intelligent Apps GmbH', 'interaid GmbH', 'Iteration One GmbH', 'justDice GmbH', 'JustPlay GmbH', 'JustWatch GmbH',
    'kaufDA (Bonial)', 'KELEYA: Pregnancy & Mama Apps', 'Kickbase GmbH', 'Kindaling', 'Klarna', 'Knowunity',
    'Knuddels - Chat und Spiele Community', 'Kolibri Games', 'komoot GmbH', 'kv.digital GmbH', 'LOTTO24', 'Lotum one GmbH', 'Lotum two GmbH',
    'Lufthansa Innovation Hub', 'Meet5 GmbH', 'meinestadt.de GmbH', 'Mellowdrop Studio', 'MetaFlow', 'MILES Mobility GmbH', 'MOQO',
    'Mobile-Team der DAK-Gesundheit', 'MyPostcard Photo Postcards and Greeting Cards App', 'MyTherapy', 'N26 AG', 'NeoTaste', 'NeuroNation',
    'nextbike', 'Onefootball GmbH', 'ONLOGIST GmbH', 'onvista media GmbH', 'Ostrom GmbH', 'Outdooractive AG', 'PAYBACK', 'petaFuel GmbH',
    'Pflegecampus', 'PL Gutscheinsysteme GmbH', 'Pohl-Boskamp Digital Health GmbH', 'PowerUs', 'Preventicus GmbH', 'QUIN Technologies GmbH',
    'Raisin SE', 'Rausgegangen GmbH', 'Relevo', 'ryd GmbH', 'Sandbox Interactive GmbH', 'Scalable AG', 'Sdui', 'smava', 'sofatutor.com',
    'SOFTGAMES Mobile Entertainment Services', 'Spiele-Palast GmbH', 'stashcat GmbH', 'Stay Informed', 'Stepstone', 'Stillfront Supremacy GmbH',
    'Studyflix GmbH', 'SumUp', 'Supershift GmbH', 'SWIFT GAMES', 'Tap Nine', 'Taxfix SE', 'TeleClinic GmbH', 'TikTok', 'Too Good To Go',
    'TorAlarm GmbH', 'Trade Republic Bank GmbH', 'Travian Games GmbH', 'Tripod Technology GmbH', 'trivago N.V.', 'Tutao GmbH',
    'Urban Sports GmbH', 'Vaia', 'Verivox GmbH', 'Vinted', 'Vivid Money GmbH', 'Vivira Health Lab GmbH', 'WebID Solutions GmbH',
    'Whow Games GmbH', 'Wolt', 'Wooga', 'XYRALITY GmbH', 'Yazio', 'Nufin GmbH', 'IDnow', 'CHECK24 GmbH', 'idealo internet GmbH',
    'Immobilien Scout GmbH', 'AMBOSS', 'aestimium GmbH',
    # online shops and marketplaces (the shop is the product)
    'ABOUT YOU SE & Co. KG', 'Zalando SE', 'bitiba GmbH', 'Flaconi', 'home24 SE', 'kfzteile24 GmbH', 'momox SE', 'rebuy recommerce GmbH',
    'ZOXS', 'moebel.de Einrichten & Wohnen GmbH', 'Limango GmbH', 'mycare.de Apotheke', 'ATP Autoteile GmbH', 'Pixum', 'Saal Digital Fotoservice GmbH',
    'Plantura', 'HelloFresh SE',
    # software companies (the software, of which the app is part, is the product)
    'Buhl Data Service GmbH', 'DATEV eG', 'datronicsoft IT Systems GmbH & Co KG', 'eurodata AG', 'G Data CyberDefense AG', 'Governikus Service GmbH',
    'ifap Service-Institut für Ärzte und Apotheker GmbH', 'INFOSOFT GmbH', 'IServ GmbH', 'mbits imaging GmbH', 'METRO Digital GmbH', 'Nextcloud',
    'Personio SE & Co KG', 'Rexx Systems', 'SAP SE', 'Schulmanager Online GmbH', 'smartlab Innovationsgesellschaft mbH', 'snapAddy GmbH',
    'SoftMaker Software GmbH', 'Star Finanz GmbH', 'TeamViewer', 'Vogel-System', 'Wolters Kluwer Tax & Accounting Deutschland GmbH',
    'zollsoft GmbH', 'clockin GmbH', 'sipgate', 'Palette CAD AG',
    # added 20 Oct 2026 (Jop): the app, online shop or smart-home app is the product
    'tado', 'AUTOHERO', 'Lautsprecher Teufel GmbH',
}

# Roles that don't work on the product even at an app-first company.
# Whole words first, then word parts that also appear inside German compounds ("Industriemechatroniker", "Fachlagerist").
NON_OFFICE = re.compile(
    r'\b(?:store|filial\w*|shop ?manager|hub manager|shift lead|markt ?leit\w*|einzelhandel\w*|verkäufer\w*|verkaufsberater\w*|'
    r'kassier\w*|kasse|koch|köchin|barista|kellner\w*|servicekraft|warehouse|picker|packer|driver|courier|rider|'
    r'restaurant ?manager|cleaner|hausmeister|arzt|ärztin|tierarzt|tierärzt\w*|chirurg\w*|dermatolog\w*|apotheker\w*|pta|mfa|hebamme|'
    r'production|kitchen|sanitation|fsqa|asset protection|culinary operations|food safety)\b|'
    r'gastronomie|küche|lagerist|lagermitarbeit|lagerlogist|kommissionier|fulfil+ment ?(?:associate|mitarbeit|center)|fahrer|kurier|'
    r'auslieferung|restaurantleit|restaurantfach|reinigung|monteur|mechaniker|mechatroniker|elektriker|elektroniker|schlosser|'
    r'servicetechniker|gebäudetechni|instandhalt|installateur|pflegefach|pflegekraft|physiotherap|fitnesstrainer|kursleiter|studioleit|'
    r'produktion|fertigung|schichtleit|lebensmitteltechn|arbeitssicherheit|qualitätssicherung', re.I)

# Digital roles: for companies that are not app-first, a job is listed only if its title says one of these.
DIGITAL = re.compile(
    r'\b(?:app|apps|ios|android|mobile|flutter|react|kotlin|swift)\b|software|frontend|front-end|backend|back-end|full[ -]?stack|'
    r'devops|\bsre\b|site reliability|cloud|platform engineer|developer|programmier|anwendungsentwickl|softwareentwickl|webentwickl|'
    r'app-?entwickl|(?:java|python|php|\.net|web|frontend|backend|ios|android|mobile)[ -]?entwickl|'
    r'data (?:scien|engineer|analy)|künstliche intelligenz|(?:wirtschafts)?informatik|daten(?:analy|engineer|wissenschaft)|analytics|machine learning|\bml\b|\bki\b|\bai\b|\bllm|'
    r'\bux\b|\bui\b|user experience|user interface|user research|ux/ui|ui/ux|interaction design|product design|digital design|'
    r'product owner|digital product|'
    r'\bqa\b|quality assurance engineer|test ?automati|software ?test|testmanag\w* (?:it|software)|'
    r'e-?commerce|e-?shop|onlineshop|online-shop|webshop|online[ -]?marketing|digital[ -]?marketing|performance[ -]?marketing|'
    r'\bcrm\b|\bseo\b|\bsea\b|growth marketing|lifecycle|user acquisition|\baso\b|marketing automation|conversion|web ?analy|'
    r'scrum master|agile coach|tech(?:nical)? consultant|tech lead|engineering manager|\bcto\b|head of (?:engineering|data|digital)|'
    r'digital(?:isierung)? (?:channel|kanäle|vertrieb|sales)|omnichannel|online ?redakt|'
    r'web ?design|anwendungsbetreu|\bsiem\b|security operations|security engineer', re.I)   # last line added 20 Oct 2026 (Jop)
# A product manager counts only for a digital product: the title also has to name one of these.
PRODUCT_MANAGER = re.compile(r'product manag|produktmanag', re.I)
PM_DIGITAL = re.compile(r'\b(?:digital|app|apps|mobile|online|web|platform|plattform|technical|tech|data|ai|ki|genai|growth|'
                        r'e-?commerce|subscription|abo|payments?|search|api|saas|software|ux)\b', re.I)
# ... but not these, which share a word with the list above.
NOT_DIGITAL = re.compile(r'personalentwickl|organisationsentwickl|business develop|geschäftsentwickl|immobilien|bauingenieur|\bsap\b|'
                         r'it[- ]?support|service ?desk|help ?desk|systemadministr|systemintegration|systemelektron|netzwerk|network admin|'
                         r'purchasing|einkauf|\bhr\b|personal|controlling|sales manager|fahrzeug|\be/e\b|embedded|firmware|antrieb|softlines|accessories|trading|product lifecycle|\bplm\b', re.I)

def app_first(company):
    return company in APP_FIRST

def cap_for(company):
    return CAP_APP_FIRST if app_first(company) else CAP

def app_job(title, company):
    """True if the job belongs on the board under the rule above (title-only, so readers can use it before opening an ad)."""
    t = title or ''
    digital = bool(DIGITAL.search(t) or (PRODUCT_MANAGER.search(t) and PM_DIGITAL.search(t)))
    if app_first(company):
        return digital or not NON_OFFICE.search(t)
    return digital and not NOT_DIGITAL.search(t)
