#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio4 — api/index.py  (Vercel Serverless)

CORREÇÕES vs versão anterior:
  1. vercel.json usa "rewrites" (não builds+routes) — evita 404
  2. ROOT resolvido via __file__ antes de qualquer import do engine
  3. index.html servido diretamente (sem render_template)
  4. generate() síncrono + ZIP em /tmp
  5. PNG desabilitado (sem wkhtmltoimage no Vercel)
"""

import os, sys, uuid, zipfile, base64, io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict
import threading

# ── Resolver paths ANTES de qualquer import do engine ─────────────
# No Vercel: __file__ = /var/task/api/index.py
# ROOT      = /var/task
HERE = Path(__file__).resolve().parent   # .../api/
ROOT = HERE.parent                       # raiz do projeto
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Imports do engine ─────────────────────────────────────────────
from flask import Flask, request, jsonify, send_file
from engine.renderer     import render_document, doc_fingerprint
from engine.random_model import generate_random_doc, LAYOUTS, PALETTES
from engine.models       import generate_svg, MODEL_MAP, MODEL_FONTS
from engine.countries    import COUNTRIES, get_palette
from engine.translator   import translate_blocks, LANG_MAP
from engine.renderer     import BLOCK_TYPES, BASE_SIZES
from engine.core         import FONT_LABELS

# ── App Flask ─────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=str(ROOT / 'templates'),
)

# ── LRU Cache ─────────────────────────────────────────────────────
class LRUCache:
    def __init__(self, maxsize=256):
        self._d = OrderedDict()
        self._max = maxsize
        self._lock = threading.Lock()
    def get(self, k):
        with self._lock:
            if k in self._d:
                self._d.move_to_end(k); return self._d[k]
        return None
    def set(self, k, v):
        with self._lock:
            if k in self._d: self._d.move_to_end(k)
            self._d[k] = v
            if len(self._d) > self._max: self._d.popitem(last=False)

PREVIEW_CACHE = LRUCache(256)
_JOBS = {}

# ── Rota raiz ─────────────────────────────────────────────────────
@app.route('/')
def index():
    # Servir HTML diretamente — mais confiável que render_template no Vercel
    p = ROOT / 'templates' / 'index.html'
    return p.read_text('utf-8'), 200, {'Content-Type': 'text/html; charset=utf-8'}

# ── API ───────────────────────────────────────────────────────────
@app.route('/api/meta')
def api_meta():
    return jsonify({
        'models':      MODEL_MAP,
        'model_fonts': MODEL_FONTS,
        'countries':   {k: {'name': v['name'], 'lang': v['lang']} for k, v in COUNTRIES.items()},
        'fonts':       FONT_LABELS,
        'block_types': BLOCK_TYPES,
        'base_sizes':  BASE_SIZES,
        'layouts':     LAYOUTS,
        'palettes':    list(PALETTES.keys()),
    })

@app.route('/api/preview', methods=['POST'])
def api_preview():
    data = request.get_json(force=True) or {}
    doc  = data.get('document', {})
    fmt  = data.get('fmt', '45')
    key  = doc_fingerprint(doc, fmt)
    hit  = PREVIEW_CACHE.get(key)
    if hit:
        return jsonify({'svg': hit, 'ok': True, 'cached': True})
    try:
        svg = render_document(doc, fmt)
        PREVIEW_CACHE.set(key, svg)
        return jsonify({'svg': svg, 'ok': True, 'cached': False})
    except Exception as e:
        return jsonify({'error': str(e), 'ok': False}), 500

@app.route('/api/random-batch', methods=['POST'])
def api_random_batch():
    data         = request.get_json(force=True) or {}
    copy_data    = data.get('copy', {})
    count        = max(1, int(data.get('count', 6)))
    palette_mode = data.get('palette_mode', 'auto')
    country      = data.get('country', 'BR')
    fmt          = data.get('fmt', '45')
    seed_prefix  = data.get('seed', uuid.uuid4().hex[:8])
    if not copy_data.get('head'):
        return jsonify({'error': 'copy.head required'}), 400

    def gen_one(i):
        layout = LAYOUTS[i % len(LAYOUTS)]
        pm     = palette_mode if palette_mode != 'auto' else ['vibrante','minimalista','neutro'][i % 3]
        return generate_random_doc(
            copy_data=copy_data, palette_mode=pm, layout_hint=layout,
            seed=f'{seed_prefix}_{i}_{layout}_{pm}',
            country=country, fmt=fmt, variation_index=i)

    docs = [None] * count
    with ThreadPoolExecutor(max_workers=min(count, 8)) as ex:
        futs = {ex.submit(gen_one, i): i for i in range(count)}
        for f in as_completed(futs):
            i = futs[f]
            try: docs[i] = f.result()
            except Exception as e: print(f'[BATCH gen {i}] {e}')

    def render_one(i):
        doc = docs[i]
        if doc is None: return None
        key = doc_fingerprint(doc, fmt)
        hit = PREVIEW_CACHE.get(key)
        if hit: return {'svg': hit, 'doc': doc, 'cached': True}
        svg = render_document(doc, fmt)
        PREVIEW_CACHE.set(key, svg)
        return {'svg': svg, 'doc': doc, 'cached': False}

    results = [None] * count
    with ThreadPoolExecutor(max_workers=min(count, 8)) as ex:
        futs = {ex.submit(render_one, i): i for i in range(count)}
        for f in as_completed(futs):
            i = futs[f]
            try: results[i] = f.result()
            except Exception as e: print(f'[BATCH render {i}] {e}')

    clean = []
    for r in results:
        if r is None: continue
        dc = {k: v for k, v in r['doc'].items() if k not in ('bg_image','bg_image_b64')}
        clean.append({'svg': r['svg'], 'doc': dc,
            'layout': r['doc'].get('_layout',''), 'palette': r['doc'].get('_palette',{}),
            'palette_mode': r['doc'].get('_palette_mode',''),
            'font_h': r['doc'].get('_font_h',''), 'font_b': r['doc'].get('_font_b',''),
            'cached': r['cached']})
    return jsonify({'results': clean, 'count': len(clean), 'seed': seed_prefix})

@app.route('/api/random-preview-country', methods=['POST'])
def api_random_preview_country():
    data        = request.get_json(force=True) or {}
    doc         = dict(data.get('doc', {}))
    country     = data.get('country', 'US').upper()
    fmt         = data.get('fmt', '45')
    source_lang = data.get('source_lang', 'pt-BR')
    try:    tblocks = translate_blocks(doc.get('blocks', []), country, source_lang)
    except: tblocks = doc.get('blocks', [])
    pal = get_palette(country)
    doc.update({'country': country, 'lang': LANG_MAP.get(country, 'en-US'),
        'cta_text': pal.get('cta', doc.get('cta_text','')),
        'cta_color': pal.get('a1', doc.get('cta_color','#FFFFFF')),
        'ac_color':  pal.get('a1', doc.get('ac_color','#FFDF00')),
        'blocks': tblocks})
    try:
        svg = render_document(doc, fmt)
        return jsonify({'svg': svg, 'ok': True})
    except Exception as e:
        return jsonify({'error': str(e), 'ok': False}), 500

@app.route('/api/translate', methods=['POST'])
def api_translate():
    data     = request.get_json(force=True) or {}
    blocks   = data.get('blocks', [])
    targets  = data.get('countries', [])
    src_lang = data.get('source_lang', 'pt-BR')
    if not blocks or not targets:
        return jsonify({'error': 'blocks and countries required'}), 400
    result = {}
    for cc in targets:
        try: result[cc] = translate_blocks(blocks, cc, src_lang)
        except Exception as e: result[cc] = blocks; print(f'[TRANSLATE {cc}] {e}')
    return jsonify({'translations': result})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Síncrono — gera SVGs, empacota ZIP em /tmp, retorna job_id imediatamente."""
    data    = request.get_json(force=True) or {}
    mode    = data.get('mode', 'random')
    formats = data.get('formats', ['45', '916'])
    svgs    = []

    if mode == 'random':
        for i, doc in enumerate(data.get('docs', [])):
            cc  = doc.get('country', 'BR')
            lay = doc.get('_layout', f'doc{i}')[:20]
            for fmt in formats:
                try: svgs.append((f'{cc}_{lay}_{i:03d}_{fmt}.svg', render_document(doc, fmt)))
                except Exception as e: print(f'[GEN {i}/{fmt}] {e}')

    elif mode == 'document':
        for d in [data.get('document', {})] + data.get('clones', []):
            cc = d.get('country', 'BR'); lay = d.get('_layout','doc')[:20]
            for fmt in formats:
                try: svgs.append((f'{cc}_{lay}_{fmt}.svg', render_document(d, fmt)))
                except Exception as e: print(f'[GEN doc {cc}/{fmt}] {e}')

    elif mode == 'model':
        for cc in data.get('countries', ['BR']):
            copy = data.get('copies', {}).get(cc) or data.get('copies', {}).get('_base', {})
            for model in data.get('models', ['A']):
                for fmt in formats:
                    try: svgs.append((f'{cc}_{model}_{fmt}.svg', generate_svg(cc, copy, model, fmt, data.get('opts',{}))))
                    except Exception as e: print(f'[GEN model {cc}/{model}] {e}')

    job_id   = uuid.uuid4().hex[:10]
    tmp_path = f'/tmp/s4_{job_id}.zip'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in svgs:
            zf.writestr(name, content)
    buf.seek(0)
    Path(tmp_path).write_bytes(buf.getvalue())

    _JOBS[job_id] = {'status':'done','progress':len(svgs),'total':len(svgs),
                     'file_count':len(svgs),'zip':tmp_path,'error':None}
    return jsonify({'job_id': job_id})

@app.route('/api/status/<job_id>')
def api_status(job_id):
    j = _JOBS.get(job_id) or {'status':'done','progress':1,'total':1,'file_count':1,'error':None}
    return jsonify({k:v for k,v in j.items() if k!='zip'} | {'file_count': j.get('file_count',0)})

@app.route('/api/download/<job_id>')
def api_download(job_id):
    j        = _JOBS.get(job_id, {})
    tmp_path = j.get('zip', f'/tmp/s4_{job_id}.zip')
    if not Path(tmp_path).exists():
        return jsonify({'error': 'Arquivo expirou. Gere novamente.'}), 404
    return send_file(tmp_path, as_attachment=True,
                     download_name=f'studio4_{job_id}.zip',
                     mimetype='application/zip')

@app.route('/api/upload-image', methods=['POST'])
def api_upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    data = request.files['file'].read()
    return jsonify({'b64': base64.b64encode(data).decode(), 'size': len(data)})

@app.route('/api/country-palette/<code>')
def api_country_palette(code):
    return jsonify(get_palette(code.upper()) or {})

@app.route('/api/set-translate-key', methods=['POST'])
def api_set_translate_key():
    """Configura a chave LibreTranslate em runtime."""
    data = request.get_json(force=True) or {}
    key  = data.get('key', '').strip()
    url  = data.get('url', '').strip()
    if key: os.environ['LIBRETRANSLATE_API_KEY'] = key
    if url: os.environ['LIBRETRANSLATE_URL'] = url
    return jsonify({'ok': bool(key)})

@app.route('/api/test-translate')
def api_test_translate():
    """Testa a conexão com LibreTranslate e retorna o status."""
    from engine.translator import test_connection
    result = test_connection()
    return jsonify(result)

# Compatibilidade com set-apikey antigo
@app.route('/api/set-apikey', methods=['POST'])
def api_set_apikey():
    data = request.get_json(force=True) or {}
    key  = data.get('key', '').strip()
    url  = data.get('url', '').strip()
    if key: os.environ['LIBRETRANSLATE_API_KEY'] = key
    if url: os.environ['LIBRETRANSLATE_URL'] = url
    return jsonify({'ok': bool(key)})

# ── WSGI entrypoint ───────────────────────────────────────────────
# O Vercel procura a variável 'app' (WSGI callable).
# NÃO renomeie esta variável.

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'\n  Studio4 → http://localhost:{port}\n')
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
