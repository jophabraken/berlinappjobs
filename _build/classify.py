# -*- coding: utf-8 -*-
"""Rule-based labels for NEW jobs found by the weekly refresh (existing jobs keep their labels).
discipline d: eng, data, product, design, marketing, sales, support, people, health, other
seniority  s: intern, junior, mid, senior, lead
lang:         en / de (language of the ad)"""
import re

def _has(t, *pats):
    return any(re.search(p, t) for p in pats)

def discipline(title, dept='', desc=''):
    t = (title or '').lower()
    d = (dept or '').lower()
    s = t + ' | ' + d
    if _has(t, r'\b(mfa|zfa|mta|pta)\b', r'pflege', r'medizinische', r'zahnmedizin', r'arzt|ärzt', r'therapeut', r'apothek', r'physio', r'hebamme', r'nurse|nursing|physician|clinical'):
        return 'health'
    if _has(t, r'data scien', r'data engineer', r'data analy', r'analytics', r'\banalyst\b', r'machine learning', r'\bml\b', r'\bai (engineer|researcher|scientist)', r'business intelligence', r'\bbi\b', r'datenanaly', r'statisti'):
        return 'data'
    if _has(t, r'product (manager|owner|lead|director|management)', r'produktmanag', r'product ?owner', r'group product', r'head of product', r'\bcpo\b', r'produktverantwort'):
        return 'product'
    if _has(t, r'design', r'\bux\b', r'\bui\b', r'user research', r'illustrat', r'\bartist\b', r'animator', r'grafik', r'mediengestalt', r'creative director', r'art director', r'motion'):
        return 'design'
    if _has(t, r'engineer', r'developer', r'entwickler', r'programmier', r'software', r'devops', r'\bsre\b', r'\bios\b', r'android', r'backend', r'frontend', r'front-end', r'back-end', r'full.?stack', r'\bqa\b', r'quality assurance', r'tester\b', r'test automation', r'architect', r'architekt', r'\bcto\b', r'informatiker', r'it.?(security|sicherheit|admin|support|system)', r'systemadministr', r'cloud', r'platform', r'security', r'tech lead', r'game programmer', r'unity|unreal'):
        return 'eng'
    if _has(t, r'marketing', r'\bseo\b', r'\bsem\b', r'\bcrm\b', r'growth', r'user acquisition', r'\bua\b', r'brand', r'content', r'social media', r'community', r'redakt', r'editor', r'journalist', r'copywrit', r'\bpr\b', r'public relations', r'kommunikation', r'communications', r'influencer', r'creator', r'performance', r'campaign', r'kampagne', r'aso\b', r'lifecycle', r'partnership'):
        return 'marketing'
    if _has(t, r'sales', r'vertrieb', r'account executive', r'account manag', r'key account', r'business development', r'\bbdr\b', r'\bsdr\b', r'verkauf', r'außendienst', r'aussendienst', r'kundenberater', r'handelsvertret', r'partner manager', r'revenue', r'commercial'):
        return 'sales'
    if _has(t, r'support', r'customer (service|success|care|experience|operations)', r'kundenservice', r'kundendienst', r'kundenbetreu', r'service ?desk', r'help ?desk', r'call ?center', r'player support', r'client service', r'onboarding', r'operations', r'\bops\b', r'logistik', r'lager', r'warehouse', r'fahrer', r'driver', r'kurier', r'courier', r'rider'):
        return 'support'
    if _has(t, r'recruit', r'talent', r'\bhr\b', r'human resources', r'people', r'personal(referent|sachbearbeit|leit|wesen|entwickl)', r'payroll', r'lohn', r'finance', r'financ', r'finanz', r'accountant', r'accounting', r'buchhalt', r'controll', r'steuer', r'\btax\b', r'legal', r'jurist', r'rechts', r'counsel', r'compliance', r'office manag', r'assistenz', r'assistant', r'einkauf', r'procurement', r'founder.?s associate', r'chief of staff', r'\bcfo\b'):
        return 'people'
    if d:
        for key, lab in (('engineer', 'eng'), ('tech', 'eng'), ('develop', 'eng'), ('data', 'data'), ('product', 'product'), ('design', 'design'),
                         ('marketing', 'marketing'), ('sales', 'sales'), ('vertrieb', 'sales'), ('support', 'support'), ('customer', 'support'),
                         ('operations', 'support'), ('people', 'people'), ('hr', 'people'), ('finance', 'people')):
            if key in d: return lab
    return 'other'

def seniority(title, hint=''):
    t = (title or '').lower()
    h = (hint or '').lower()
    if _has(t, r'werkstud', r'working student', r'praktik', r'\bintern\b', r'internship', r'ausbildung', r'azubi', r'trainee', r'duales? stud', r'minijob', r'aushilfe', r'studentische', r'student assistant', r'abschlussarbeit', r'thesis', r'volontär', r'volontariat'):
        return 'intern'
    if _has(t, r'\b(head|director|vp|vice president|chief|cto|cpo|cfo|ceo|coo)\b', r'\blead\b', r'principal', r'\bstaff\b', r'leiter', r'leitung', r'teamlead', r'team lead', r'manager of', r'engineering manager', r'geschäftsführ'):
        return 'lead'
    if _has(t, r'\bsenior\b', r'\bsr\.?\b', r'\bexpert\b', r'erfahren'):
        return 'senior'
    if _has(t, r'\bjunior\b', r'\bjr\.?\b', r'graduate', r'entry', r'einsteiger', r'berufseinst', r'absolvent'):
        return 'junior'
    if h in ('entry_level', 'entry level', 'entry-level', 'student', 'internship') or 'entry' in h:
        return 'intern' if 'intern' in h or 'student' in h else 'junior'
    if 'senior' in h: return 'senior'
    return 'mid'

_DE = (' und ', ' die ', ' der ', ' wir ', ' mit ', ' für ', ' du ', ' dich ', ' deine ', ' sie ', ' ihre ', ' bei ', ' ist ')
_EN = (' and ', ' the ', ' we ', ' with ', ' for ', ' you ', ' your ', ' our ', ' will ', ' are ', ' is ')
def language(title, desc_text=''):
    x = ' ' + re.sub(r'\s+', ' ', (desc_text or '')).lower() + ' '
    if len(x) > 200:
        de = sum(x.count(w) for w in _DE); en = sum(x.count(w) for w in _EN)
        return 'de' if de > en else 'en'
    t = (title or '').lower()
    return 'de' if _has(t, r'mitarbeiter', r'werkstud', r'ausbildung', r'praktik', r'sachbearbeit', r'kauf(mann|frau)', r'fachkraft', r'referent', r'leiter', r'\(m/w/d\)', r'\bfür\b', r'\bim bereich\b') else 'en'
