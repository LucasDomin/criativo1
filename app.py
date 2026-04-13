#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio4 — Flask App
Rotas: preview, random-batch, generate (document+model), translate, upload-image.
Cache de preview em memória (LRU 256 entradas).
Workers assíncronos via threads para geração em lote.
"""
import os, sys, json, uuid, zipfile, threading, subprocess, base64, hashlib
from pathlib import Path
from functools import lru_cache
from collections import OrderedDict
from flask import Flask, request, jsonify, send_file

sys.path.insert(0, os.path.dirname(__file__))

from engine.renderer   import render_document, doc_fingerprint, BLOCK_TYPES, BASE_SIZES
from engine.random_model import generate_random_doc, generate_batch, LAYOUTS, PALETTES
from engine.translator  import translate_blocks, LANG_MAP, CTA_DEFAULTS, get_cta_for_country
from engine.countries   import COUNTRIES, get_palette
from engine.core        import FONTS, FONT_LABELS
from engine.models      import MODEL_MAP, MODEL_FONTS, generate_svg

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / 'uploads';          UPLOAD_DIR.mkdir(exist_ok=True)
OUT_SVG    = BASE_DIR / 'outputs' / 'svg';  OUT_SVG.mkdir(parents=True, exist_ok=True)
OUT_PNG    = BASE_DIR / 'outputs' / 'png';  OUT_PNG.mkdir(parents=True, exist_ok=True)
OUT_ZIP    = BASE_DIR / 'outputs' / 'zip';  OUT_ZIP.mkdir(parents=True, exist_ok=True)

JOBS: dict = {}         # job_id → state dict

# ── Cache de preview (LRU, 256 entradas, ~10 MB) ─────────────────
class LRUCache:
    def __init__(self, maxsize=256):
        self._cache = OrderedDict()
        self._max   = maxsize
        self._lock  = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def set(self, key, value):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self._max:
                self._cache.popitem(last=False)

PREVIEW_CACHE = LRUCache(256)


# ── PNG Render ────────────────────────────────────────────────────
def svg_to_png(svg_path: Path, png_path: Path) -> bool:
    raw = str(png_path).replace('.png', '_raw.png')
    try:
        r1 = subprocess.run(
            ['wkhtmltoimage', '--format', 'png', '--quiet', '--width', '1080',
             str(svg_path), raw], timeout=60, capture_output=True)
        if r1.returncode == 0 and Path(raw).exists():
            r2 = subprocess.run(
                ['convert', raw, '-flatten', '-quality', '92',
                 '-define', 'png:compression-level=9', str(png_path)],
                timeout=30, capture_output=True)
            if Path(raw).exists(): os.remove(raw)
            return r2.returncode == 0 and png_path.exists() and png_path.stat().st_size > 5000
    except Exception as e:
        print(f'[PNG] {e}')
    return False


# ── Job runners ───────────────────────────────────────────────────
def run_job(job_id: str, payload: dict):
    j = JOBS[job_id]
    try:
        mode = payload.get('mode', 'document')
        if   mode == 'document': _job_document(j, payload)
        elif mode == 'random':   _job_random(j, payload)
        else:                    _job_model(j, payload)
    except Exception as e:
        import traceback; traceback.print_exc()
        j.update({'status': 'error', 'error': str(e)})


def _job_document(j, payload):
    """Exporta documentos (primário + clones) nos formatos escolhidos."""
    primary   = payload['document']
    clones    = payload.get('clones', [])
    formats   = payload.get('formats', ['45', '916'])
    do_png    = payload.get('generate_png', True)

    docs = [(primary, primary.get('country', 'BR'))]
    for cl in clones:
        docs.append((cl, cl.get('country', 'US')))

    total = len(docs) * len(formats)
    j.update({'status': 'generating', 'total': total, 'progress': 0, 'files': []})
    files = []; done = 0

    for doc, country in docs:
        for fmt in formats:
            fname = f"{country}_doc_{fmt}"
            try:
                svg = render_document(doc, fmt=fmt)
                sp  = OUT_SVG / f'{fname}.svg'
                sp.write_text(svg, encoding='utf-8')
                files.append({'type':'svg','path':str(sp),'name':f'{fname}.svg',
                              'country':country,'fmt':fmt})
                if do_png:
                    pp = OUT_PNG / f'{fname}.png'
                    if svg_to_png(sp, pp):
                        files.append({'type':'png','path':str(pp),'name':f'{fname}.png',
                                      'country':country,'fmt':fmt})
            except Exception as e:
                print(f'[DOC] {fname}: {e}')
            done += 1; j['progress'] = done; j['files'] = files

    _finish(j, files)


def _job_random(j, payload):
    """Exporta documentos gerados aleatoriamente (múltiplos modelos × países × formatos)."""
    docs    = payload.get('docs', [])     # lista de DocumentState com bg_svg
    formats = payload.get('formats', ['45', '916'])
    do_png  = payload.get('generate_png', True)

    total = len(docs) * len(formats)
    j.update({'status': 'generating', 'total': total, 'progress': 0, 'files': []})
    files = []; done = 0

    for i, doc in enumerate(docs):
        country = doc.get('country', 'BR')
        layout  = doc.get('_layout', f'v{i}')
        for fmt in formats:
            fname = f"{country}_rnd_{layout}_{fmt}"
            try:
                svg = render_document(doc, fmt=fmt)
                sp  = OUT_SVG / f'{fname}.svg'
                sp.write_text(svg, encoding='utf-8')
                files.append({'type':'svg','path':str(sp),'name':f'{fname}.svg',
                              'country':country,'fmt':fmt,'layout':layout})
                if do_png:
                    pp = OUT_PNG / f'{fname}.png'
                    if svg_to_png(sp, pp):
                        files.append({'type':'png','path':str(pp),'name':f'{fname}.png',
                                      'country':country,'fmt':fmt})
            except Exception as e:
                print(f'[RND] {fname}: {e}')
            done += 1; j['progress'] = done; j['files'] = files

    _finish(j, files)


def _job_model(j, payload):
    """Exporta usando modelos clássicos A–N."""
    countries = payload['countries']
    models    = payload['models']
    formats   = payload['formats']
    do_png    = payload.get('generate_png', True)
    copies    = payload['copies']
    opts      = payload.get('opts', {})

    total = len(countries) * len(models) * len(formats)
    j.update({'status': 'generating', 'total': total, 'progress': 0, 'files': []})
    files = []; done = 0

    for country in countries:
        copy = copies.get(country, copies.get('_base', {}))
        pal  = get_palette(country)
        copy.setdefault('cta',  pal['cta'])
        copy.setdefault('lang', pal['lang'])
        for model in models:
            for fmt in formats:
                fname = f'{country}_M{model}_{fmt}'
                try:
                    svg = generate_svg(country, copy, model, fmt, opts=opts or None)
                    sp  = OUT_SVG / f'{fname}.svg'
                    sp.write_text(svg, encoding='utf-8')
                    files.append({'type':'svg','path':str(sp),'name':f'{fname}.svg',
                                  'country':country,'model':model,'fmt':fmt})
                    if do_png:
                        pp = OUT_PNG / f'{fname}.png'
                        if svg_to_png(sp, pp):
                            files.append({'type':'png','path':str(pp),'name':f'{fname}.png',
                                          'country':country,'model':model,'fmt':fmt})
                except Exception as e:
                    print(f'[MODEL] {fname}: {e}')
                done += 1; j['progress'] = done; j['files'] = files

    _finish(j, files)


def _finish(j, files):
    zip_path = OUT_ZIP / f'studio4_{uuid.uuid4().hex[:8]}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f['path'], f['name'])
    j.update({'status': 'done', 'zip': str(zip_path), 'files': files})


# ════════════════════════════════════════════════════════════════
# ROTAS
# ════════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return (BASE_DIR / 'templates' / 'index.html').read_text(encoding='utf-8')


@app.route('/api/meta')
def api_meta():
    return jsonify({
        'models':       MODEL_MAP,
        'model_fonts':  MODEL_FONTS,
        'countries':    {k: {'name': v['name'], 'lang': v['lang']}
                         for k, v in COUNTRIES.items()},
        'fonts':        FONT_LABELS,
        'block_types':  BLOCK_TYPES,
        'base_sizes':   BASE_SIZES,
        'layouts':      LAYOUTS,
        'palettes':     list(PALETTES.keys()),
    })


@app.route('/api/preview', methods=['POST'])
def api_preview():
    """Preview rápido — com cache LRU."""
    data = request.json or {}
    doc  = data.get('document', {})
    fmt  = data.get('fmt', '45')

    # Ignorar imagem no fingerprint (muito grande)
    fkey = doc_fingerprint(doc, fmt)
    cached = PREVIEW_CACHE.get(fkey)
    if cached:
        return jsonify({'svg': cached, 'ok': True, 'cached': True})

    try:
        svg = render_document(doc, fmt=fmt)
        PREVIEW_CACHE.set(fkey, svg)
        return jsonify({'svg': svg, 'ok': True, 'cached': False})
    except Exception as e:
        return jsonify({'error': str(e), 'ok': False}), 500


@app.route('/api/random-batch', methods=['POST'])
def api_random_batch():
    """
    Gera N documentos aleatórios e retorna SVGs para preview.
    Aceita copy, count, palette_mode, country, fmt.
    Geração paralela com ThreadPoolExecutor.
    """
    data          = request.json or {}
    copy_data     = data.get('copy', {})
    count         = max(1, int(data.get('count', 6)))       # sem limite — gera exatamente N
    palette_mode  = data.get('palette_mode', 'auto')         # 'vibrante'|'minimalista'|'neutro'|'auto'
    country       = data.get('country', 'BR')
    fmt           = data.get('fmt', '45')
    seed_prefix   = data.get('seed', uuid.uuid4().hex[:8])

    if not copy_data.get('head'):
        return jsonify({'error': 'copy.head required'}), 400

    # Geração em paralelo (threads)
    from concurrent.futures import ThreadPoolExecutor
    docs = [None] * count

    def gen_one(i):
        # Layout: rotaciona + dentro de cada ciclo varia paleta e fontes via seed única
        layout = LAYOUTS[i % len(LAYOUTS)]
        # Paleta: alterna os 3 modos ciclicamente, auto usa todos
        pm = palette_mode if palette_mode != 'auto' else ['vibrante','minimalista','neutro'][i % 3]
        # Seed única por (prefix, índice, layout, modo) — garante variedade mesmo para i>14
        unique_seed = f'{seed_prefix}_{i}_{layout}_{pm}'
        return generate_random_doc(
            copy_data=copy_data,
            palette_mode=pm,
            layout_hint=layout,
            seed=unique_seed,
            country=country,
            fmt=fmt,
            variation_index=i,
        )

    with ThreadPoolExecutor(max_workers=min(count, 8)) as ex:
        futures = {ex.submit(gen_one, i): i for i in range(count)}
        from concurrent.futures import as_completed
        for future in as_completed(futures):
            i = futures[future]
            try:
                docs[i] = future.result()
            except Exception as e:
                print(f'[RAND BATCH] i={i}: {e}')

    # Renderizar SVGs (também em paralelo)
    results = [None] * count

    def render_one(i):
        doc = docs[i]
        if doc is None: return None
        fkey = doc_fingerprint(doc, fmt)
        cached = PREVIEW_CACHE.get(fkey)
        if cached:
            return {'svg': cached, 'doc': doc, 'cached': True}
        svg = render_document(doc, fmt=fmt)
        PREVIEW_CACHE.set(fkey, svg)
        return {'svg': svg, 'doc': doc, 'cached': False}

    with ThreadPoolExecutor(max_workers=min(count, 8)) as ex:
        futures = {ex.submit(render_one, i): i for i in range(count)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                results[i] = future.result()
            except Exception as e:
                print(f'[RAND RENDER] i={i}: {e}')
                results[i] = None

    # Filtrar Nones e serializar (remover bg_image para não explodir o JSON)
    clean = []
    for r in results:
        if r is None: continue
        doc_clean = {k: v for k, v in r['doc'].items() if k not in ('bg_image','bg_image_b64')}
        clean.append({
            'svg':     r['svg'],
            'doc':     doc_clean,
            'layout':  r['doc'].get('_layout',''),
            'palette': r['doc'].get('_palette',{}),
            'palette_mode': r['doc'].get('_palette_mode',''),
            'font_h':  r['doc'].get('_font_h',''),
            'font_b':  r['doc'].get('_font_b',''),
            'cached':  r['cached'],
        })

    return jsonify({'results': clean, 'count': len(clean), 'seed': seed_prefix})


@app.route('/api/random-preview-country', methods=['POST'])
def api_random_preview_country():
    """
    Recebe um DocumentState (doc) + país alvo + idioma e devolve
    o SVG do doc adaptado para esse país (paleta + tradução).
    Usado no preview de clones no painel de modelos aleatórios.
    """
    data    = request.json or {}
    doc     = data.get('doc', {})
    country = data.get('country', 'BR')
    fmt     = data.get('fmt', '45')
    src_lang= data.get('source_lang', 'pt-BR')

    # 1. Traduzir blocos
    blocks = doc.get('blocks', [])
    try:
        translated_blocks = translate_blocks(blocks, country, source_lang=src_lang)
    except Exception:
        translated_blocks = blocks

    # 2. Aplicar paleta do país
    pal = get_palette(country)
    doc_adapted = {
        **doc,
        'country':    country,
        'lang':       LANG_MAP.get(country, 'en-US'),
        'cta_text':   pal['cta'],
        'cta_color':  pal['a1'] if pal else doc.get('cta_color','#FFFFFF'),
        'ac_color':   pal['a1'] if pal else doc.get('ac_color','#FFDF00'),
        'blocks':     translated_blocks,
    }

    try:
        svg = render_document(doc_adapted, fmt=fmt)
        return jsonify({'svg': svg, 'ok': True})
    except Exception as e:
        return jsonify({'error': str(e), 'ok': False}), 500


@app.route('/api/translate', methods=['POST'])
def api_translate():
    """Traduz blocos para múltiplos países de uma vez."""
    data     = request.json or {}
    blocks   = data.get('blocks', [])
    targets  = data.get('countries', [])
    src_lang = data.get('source_lang', 'pt-BR')

    if not blocks or not targets:
        return jsonify({'error': 'blocks and countries required'}), 400

    result = {}
    for country in targets:
        try:
            result[country] = translate_blocks(blocks, country, source_lang=src_lang)
        except Exception as e:
            result[country] = blocks
            print(f'[TRANSLATE] {country}: {e}')

    return jsonify({'translations': result})


@app.route('/api/generate', methods=['POST'])
def api_generate():
    payload = request.json or {}
    job_id  = str(uuid.uuid4())
    JOBS[job_id] = {
        'id': job_id, 'status': 'queued',
        'progress': 0, 'total': 0,
        'files': [], 'zip': None, 'error': None,
    }
    threading.Thread(target=run_job, args=(job_id, payload), daemon=True).start()
    return jsonify({'job_id': job_id})


@app.route('/api/status/<job_id>')
def api_status(job_id):
    j = JOBS.get(job_id)
    if not j: return jsonify({'error': 'Not found'}), 404
    return jsonify({k: v for k, v in j.items() if k != 'files'} | {'file_count': len(j.get('files', []))})


@app.route('/api/previews/<job_id>')
def api_previews(job_id):
    j = JOBS.get(job_id)
    if not j: return jsonify({'error': 'Not found'}), 404
    svgs = []
    for f in j.get('files', []):
        if f['type'] == 'svg':
            try:
                svgs.append({
                    'name':    f['name'],
                    'content': Path(f['path']).read_text('utf-8'),
                    'country': f.get('country', ''),
                    'fmt':     f.get('fmt', '45'),
                    'layout':  f.get('layout', ''),
                })
            except: pass
    return jsonify({'files': svgs, 'status': j['status'],
                    'progress': j['progress'], 'total': j['total']})


@app.route('/api/download/<job_id>')
def api_download(job_id):
    j = JOBS.get(job_id)
    if not j or j['status'] != 'done': return jsonify({'error': 'Not ready'}), 404
    return send_file(j['zip'], as_attachment=True,
                     download_name=Path(j['zip']).name, mimetype='application/zip')


@app.route('/api/upload-image', methods=['POST'])
def api_upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    f    = request.files['file']
    data = f.read()
    b64  = base64.b64encode(data).decode('utf-8')
    return jsonify({'b64': b64, 'size': len(data)})


@app.route('/api/country-palette/<code>')
def api_country_palette(code):
    return jsonify(get_palette(code.upper()))


@app.route('/api/set-translate-key', methods=['POST'])
def api_set_translate_key():
    data = request.get_json(force=True) or {}
    key  = data.get('key', '').strip()
    url  = data.get('url', '').strip()
    if key:
        os.environ['LIBRETRANSLATE_API_KEY'] = key
        import engine.translator as tr; tr.LIBRE_KEY = key
    if url:
        os.environ['LIBRETRANSLATE_URL'] = url
        import engine.translator as tr; tr.LIBRE_URL = url
    return jsonify({'ok': bool(key)})

@app.route('/api/test-translate')
def api_test_translate():
    from engine.translator import test_connection
    return jsonify(test_connection())

@app.route('/api/set-apikey', methods=['POST'])
def api_set_apikey():
    data = request.get_json(force=True) or {}
    key  = data.get('key', '').strip()
    url  = data.get('url', '').strip()
    if key:
        os.environ['LIBRETRANSLATE_API_KEY'] = key
        import engine.translator as tr; tr.LIBRE_KEY = key
    if url:
        os.environ['LIBRETRANSLATE_URL'] = url
        import engine.translator as tr; tr.LIBRE_URL = url
    return jsonify({'ok': bool(key)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n  Studio4 → http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

