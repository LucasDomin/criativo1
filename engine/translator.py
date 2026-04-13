#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio4 — Translator v2 (LibreTranslate)

Hierarquia:
  1. LibreTranslate API  (se LIBRETRANSLATE_API_KEY configurada)
  2. Fallback local      (CTA localizado + valor monetário por país)

Variáveis de ambiente:
  LIBRETRANSLATE_API_KEY  — chave da API
  LIBRETRANSLATE_URL      — URL da instância (padrão: https://libretranslate.com)

Como obter chave gratuita:
  https://portal.libretranslate.com/register
  Limite gratuito: 80 requests/hora
"""
import os, re, time
import requests as _req

# ── Configuração ──────────────────────────────────────────────────
LIBRE_KEY = os.environ.get('LIBRETRANSLATE_API_KEY', '')
LIBRE_URL = os.environ.get('LIBRETRANSLATE_URL', 'https://libretranslate.com')

# ── Mapas de idioma ───────────────────────────────────────────────
LANG_MAP = {
    'BR':'pt-BR','AR':'es-AR','MX':'es-MX','US':'en-US','JP':'ja-JP',
    'TR':'tr-TR','PH':'en-PH','BE':'fr-BE','CO':'es-CO','NL':'nl-NL',
    'FR':'fr-FR','UK':'en-GB','KR':'ko-KR','DE':'de-DE','CZ':'cs-CZ',
    'AU':'en-AU','PT':'pt-PT','IT':'it-IT','ES':'es-ES','CA':'en-CA',
    'PE':'es-PE','GR':'el-GR','TH':'th-TH','ID':'id-ID','PL':'pl-PL',
}

_LIBRE_LANG = {
    'pt-BR':'pt','pt-PT':'pt',
    'es-AR':'es','es-MX':'es','es-CO':'es','es-ES':'es','es-PE':'es',
    'en-US':'en','en-GB':'en','en-PH':'en','en-AU':'en','en-CA':'en',
    'fr-FR':'fr','fr-BE':'fr','de-DE':'de','nl-NL':'nl','it-IT':'it',
    'pl-PL':'pl','cs-CZ':'cs','ja-JP':'ja','ko-KR':'ko','tr-TR':'tr',
    'el-GR':'el','th-TH':'th','id-ID':'id',
}

LANG_NAMES = {
    'pt-BR':'Português (Brasil)','es-AR':'Español (Argentina)',
    'es-MX':'Español (México)','en-US':'English (US)','ja-JP':'Japonês',
    'tr-TR':'Turco','en-PH':'English (Filipinas)','fr-BE':'Français (Bélgica)',
    'es-CO':'Español (Colômbia)','nl-NL':'Holandês','fr-FR':'Français',
    'en-GB':'English (UK)','ko-KR':'Coreano','de-DE':'Alemão',
    'cs-CZ':'Tcheco','en-AU':'English (Austrália)','pt-PT':'Português (Portugal)',
    'it-IT':'Italiano','es-ES':'Español (Espanha)','en-CA':'English (Canadá)',
    'es-PE':'Español (Peru)','el-GR':'Grego','th-TH':'Tailandês',
    'id-ID':'Indonésio','pl-PL':'Polonês',
}

CTA_DEFAULTS = {
    'pt-BR':'SIMULAR AGORA',     'pt-PT':'SIMULAR AGORA',
    'es-AR':'SIMULAR AHORA',     'es-MX':'SIMULAR AHORA',
    'es-CO':'SIMULAR AHORA',     'es-ES':'SIMULAR AHORA',
    'es-PE':'SIMULAR AHORA',     'en-US':'SIMULATE NOW',
    'en-GB':'SIMULATE NOW',      'en-PH':'SIMULATE NOW',
    'en-AU':'SIMULATE NOW',      'en-CA':'SIMULATE NOW',
    'fr-FR':'SIMULER MAINTENANT','fr-BE':'SIMULER MAINTENANT',
    'de-DE':'JETZT SIMULIEREN',  'it-IT':'SIMULA ORA',
    'nl-NL':'NU SIMULEREN',      'pl-PL':'SYMULUJ TERAZ',
    'cs-CZ':'SIMULOVAT NYNÍ',    'ja-JP':'今すぐシミュレーション',
    'ko-KR':'지금 시뮬레이션',     'tr-TR':'HEMEN SİMÜLE ET',
    'el-GR':'ΠΡΟΣΟΜΟΊΩΣΗ ΤΏΡΑ',  'th-TH':'จำลองตอนนี้',
    'id-ID':'SIMULASIKAN SEKARANG',
}

COUNTRY_VALUE_TEMPLATES = {
    'BR':'R$ {low} a R$ {high}',   'AR':'AR$ {low} a AR$ {high}',
    'MX':'MX$ {low} a MX$ {high}', 'CO':'COP {low} a COP {high}',
    'PE':'S/ {low} a S/ {high}',   'US':'${low} to ${high}',
    'CA':'CA${low} to CA${high}',  'AU':'A${low} to A${high}',
    'UK':'£{low} to £{high}',      'FR':'{low}€ à {high}€',
    'DE':'{low}€ bis {high}€',     'NL':'{low}€ tot {high}€',
    'BE':'{low}€ à {high}€',       'IT':'{low}€ a {high}€',
    'ES':'{low}€ a {high}€',       'PT':'{low}€ a {high}€',
    'CZ':'Kč {low} až Kč {high}',  'PL':'{low} zł do {high} zł',
    'GR':'{low}€ έως {high}€',     'JP':'¥{low} 〜 ¥{high}',
    'KR':'₩{low} ~ ₩{high}',       'TH':'฿{low} ถึง ฿{high}',
    'ID':'Rp{low} - Rp{high}',     'PH':'₱{low} to ₱{high}',
    'TR':'₺{low} - ₺{high}',
}

CURRENCY_MULTIPLIER = {
    'BR':1.0,  'AR':5.0,   'MX':3.5,   'CO':120.0, 'PE':0.6,
    'US':0.2,  'CA':0.27,  'AU':0.3,   'UK':0.16,  'FR':0.18,
    'DE':0.18, 'NL':0.18,  'BE':0.18,  'IT':0.18,  'ES':0.18,
    'PT':0.18, 'CZ':4.5,   'PL':0.8,   'GR':0.18,  'JP':30.0,
    'KR':260.0,'TH':7.0,   'ID':3200.0,'PH':11.0,  'TR':6.0,
}

# ── Helpers ───────────────────────────────────────────────────────
def _adapt_valor(valor_text, country):
    nums = re.findall(r'[\d.,]+', valor_text.replace('.','').replace(',','.'))
    if not nums: return valor_text
    try:
        vals = [float(n.replace(',','')) for n in nums[:2]]
        mult = CURRENCY_MULTIPLIER.get(country, 1.0)
        tmpl = COUNTRY_VALUE_TEMPLATES.get(country, COUNTRY_VALUE_TEMPLATES['US'])
        low  = _fmt(vals[0]*mult)
        high = _fmt(vals[1]*mult) if len(vals)>1 else _fmt(vals[0]*mult*8)
        return tmpl.format(low=low, high=high)
    except Exception:
        return valor_text

def _fmt(n):
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'.rstrip('0').rstrip('.')
    if n >= 1_000:     return f'{round(n/1000)*1000:,.0f}'.replace(',','.')
    return str(int(round(n)))

def _libre_code(bcp47):
    return _LIBRE_LANG.get(bcp47, bcp47.split('-')[0].lower())

# ── LibreTranslate ────────────────────────────────────────────────
def _translate_one(text, src, tgt, key, url):
    if not text or not text.strip(): return ''
    try:
        r = _req.post(
            f'{url.rstrip("/")}/translate',
            json={'q':text,'source':src,'target':tgt,'format':'text','api_key':key},
            timeout=15,
            headers={'Content-Type':'application/json'},
        )
        if r.status_code == 200:
            return r.json().get('translatedText','').strip()
        elif r.status_code == 429:
            print('[LibreTranslate] Rate limit — chave gratuita: 80 req/hora.')
        elif r.status_code == 403:
            print('[LibreTranslate] Chave inválida. Verifique LIBRETRANSLATE_API_KEY.')
        else:
            print(f'[LibreTranslate] Erro {r.status_code}: {r.text[:80]}')
    except _req.exceptions.Timeout:
        print('[LibreTranslate] Timeout.')
    except Exception as e:
        print(f'[LibreTranslate] {e}')
    return ''

def _translate_batch(texts_dict, source_lang, target_lang):
    """
    Traduz múltiplos textos em batch.
    texts_dict = {id: texto}
    Usa separador ||| para agrupar tudo em 1 request (economiza rate limit).
    """
    global LIBRE_KEY, LIBRE_URL
    LIBRE_KEY = os.environ.get('LIBRETRANSLATE_API_KEY', LIBRE_KEY)
    LIBRE_URL = os.environ.get('LIBRETRANSLATE_URL', LIBRE_URL)

    if not LIBRE_KEY or not texts_dict: return {}

    src = _libre_code(source_lang)
    tgt = _libre_code(target_lang)
    if src == tgt: return {}

    SEP  = '\n|||SPLIT|||\n'
    ids  = list(texts_dict.keys())
    txts = [texts_dict[i] for i in ids]

    # Tentativa 1: batch único
    translated = _translate_one(SEP.join(txts), src, tgt, LIBRE_KEY, LIBRE_URL)
    if translated:
        parts = [p.strip() for p in translated.split('|||SPLIT|||')]
        if len(parts) == len(ids):
            return dict(zip(ids, parts))
        print(f'[LibreTranslate] Batch retornou {len(parts)} partes, esperava {len(ids)}. Tentando individual.')

    # Tentativa 2: individual
    result = {}
    for i, (bid, txt) in enumerate(zip(ids, txts)):
        if i > 0: time.sleep(0.4)
        t = _translate_one(txt, src, tgt, LIBRE_KEY, LIBRE_URL)
        if t: result[bid] = t
    return result

# ── Função principal ──────────────────────────────────────────────
def translate_blocks(blocks, target_country, source_lang='pt-BR'):
    """
    Traduz lista de blocos para o idioma do país alvo.

    Por tipo:
      cta        → CTA_DEFAULTS (sempre local — garante tom correto)
      value      → conversão monetária local (sempre)
      headline   → LibreTranslate se disponível, senão mantém original
      subhead    → LibreTranslate se disponível, senão mantém original
      disclaimer → LibreTranslate se disponível, senão mantém original

    Nunca altera campos de estilo (font, color, size, etc.).
    """
    global LIBRE_KEY, LIBRE_URL
    LIBRE_KEY = os.environ.get('LIBRETRANSLATE_API_KEY', LIBRE_KEY)
    LIBRE_URL = os.environ.get('LIBRETRANSLATE_URL', LIBRE_URL)

    country     = target_country.upper()
    target_lang = LANG_MAP.get(country, 'en-US')

    # Passo 1: ajustes locais (sempre, independente de API)
    result = []
    for b in blocks:
        nb    = dict(b)
        btype = b.get('type','')
        text  = b.get('text','')
        if btype == 'cta':
            nb['text'] = CTA_DEFAULTS.get(target_lang, text or 'SIMULATE NOW')
        elif btype == 'value':
            nb['text'] = _adapt_valor(text, country)
        result.append(nb)

    # Passo 2: tradução via LibreTranslate se disponível
    src_code = _libre_code(source_lang)
    tgt_code = _libre_code(target_lang)
    if not LIBRE_KEY or src_code == tgt_code:
        return result

    to_translate = {b['id']: b['text']
                    for b in result
                    if b.get('type') in ('headline','subhead','disclaimer')
                    and b.get('text','').strip()}

    if not to_translate:
        return result

    translated = _translate_batch(to_translate, source_lang, target_lang)

    for b in result:
        bid = b.get('id','')
        if bid in translated and translated[bid]:
            b['text'] = translated[bid]

    return result


def get_cta_for_country(country):
    lang = LANG_MAP.get(country.upper(), 'en-US')
    return CTA_DEFAULTS.get(lang, 'SIMULATE NOW')


def test_connection():
    """Testa a conexão com LibreTranslate. Retorna dict com status."""
    global LIBRE_KEY, LIBRE_URL
    LIBRE_KEY = os.environ.get('LIBRETRANSLATE_API_KEY', LIBRE_KEY)
    LIBRE_URL = os.environ.get('LIBRETRANSLATE_URL', LIBRE_URL)

    if not LIBRE_KEY:
        return {'ok': False, 'message': 'LIBRETRANSLATE_API_KEY não configurada.', 'languages': []}
    try:
        r = _req.get(f'{LIBRE_URL.rstrip("/")}/languages',
                     params={'api_key': LIBRE_KEY}, timeout=10)
        if r.status_code != 200:
            return {'ok': False, 'message': f'Erro {r.status_code}: {r.text[:100]}', 'languages': []}
        langs = [l['code'] for l in r.json()]
        test  = _translate_one('Olá mundo', 'pt', 'en', LIBRE_KEY, LIBRE_URL)
        if test:
            return {'ok': True,
                    'message': f'Conectado. Teste: "Olá mundo" → "{test}"',
                    'languages': langs}
        return {'ok': False, 'message': 'Conexão OK mas tradução falhou.', 'languages': langs}
    except Exception as e:
        return {'ok': False, 'message': str(e), 'languages': []}
