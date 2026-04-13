#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio4 — BlockRenderer v5
Mudanças vs v4:
- BUGFIX: linearGradient agora entra em <defs> corretamente
- NOVO: suporte a x_offset por bloco (posição X independente)
- NOVO: suporte a bg_crop {x,y,w,h} para recorte de imagem de fundo
- NOVO: bg_effect 'vignette' (escurecimento nas bordas)
- PERFORMANCE: patterns SVG em vez de loops de <line> (feito no random_model)
"""
import hashlib
from engine.core import (
    XL, XR, CX, CW, FONTS, FONT_LABELS,
    gf, gr, sw, ew, gap_ab, gap_s, first_y, bottom_of,
    fit, wrap, fw, atc, ctr, sac, mix, spv, tsc,
    T, R, L, Lv, Ci, Pg, Arc, DEFS,
    cap, desc
)

W_45,  H_45  = 1080, 1350  # 4:5 (substituiu 3:4 1080×1440)
W_916, H_916 = 1080, 1920

BLOCK_TYPES = ['headline','subhead','value','cta','disclaimer','divider','spacer','image']

BASE_SIZES = {
    'headline':88, 'subhead':30, 'value':96, 'cta':28,
    'disclaimer':13, 'divider':0, 'spacer':0, 'image':0,
}

DEFAULT_WEIGHTS = {
    'headline':'900', 'subhead':'300', 'value':'900',
    'cta':'900', 'disclaimer':'400',
}


def block_fs(block, country_scale=1.0):
    base = BASE_SIZES.get(block['type'], 30)
    return max(12, int(base * float(block.get('size', 100)) / 100.0 * country_scale))


def block_x(block):
    """Retorna (x, text-anchor). Respeita x_offset se definido."""
    align = block.get('align', 'left')
    xo    = int(block.get('x_offset', 0))
    if align == 'center': return CX + xo, 'middle'
    if align == 'right':  return XR + xo, 'end'
    return XL + xo, 'start'


def block_fw(block):
    w = block.get('weight', '')
    return w if w else DEFAULT_WEIGHTS.get(block.get('type', 'headline'), '400')


def default_block(btype, text='', **kw):
    return {
        'id':       kw.get('id', ''),
        'type':     btype,
        'text':     text,
        'font':     kw.get('font', 'poppins'),
        'size':     kw.get('size', 100),
        'color':    kw.get('color', '#FFFFFF'),
        'align':    kw.get('align', 'left'),
        'weight':   kw.get('weight', ''),
        'ls':       kw.get('ls', 0),
        'opacity':  kw.get('opacity', 1.0),
        'visible':  kw.get('visible', True),
        'y_offset': kw.get('y_offset', 0),
        'x_offset': kw.get('x_offset', 0),   # NOVO: deslocamento horizontal
        'flt':      kw.get('flt', ''),
    }


class BlockRenderer:
    """
    Renderiza DocumentState → SVG string.
    bg_svg_decor: decoração geométrica do random_model (patterns SVG leves).
    bg_crop: {'x':0,'y':0,'w':W,'h':H} — recorte da imagem de fundo.
    """

    def __init__(self, is9, bg_color='#000000', bg_image_b64=None,
                 bg_effect=None, bg_opacity=1.0, bg_svg_decor='',
                 bg_crop=None):
        self.is9    = is9
        self.W      = W_916 if is9 else W_45
        self.H      = H_916 if is9 else H_45
        self.bg     = bg_color
        self.bg_img = bg_image_b64
        self.bg_eff = bg_effect       # 'grayscale' | 'gradient' | 'vignette' | None
        self.bg_op  = float(bg_opacity)
        self.bg_svg_decor = bg_svg_decor
        self.bg_crop = bg_crop        # {'x','y','w','h'} — recorte em px originais
        self.top_m    = 280 if is9 else 84
        self.ct       = 1440 if is9 else 1110
        self.parts    = []
        self.y        = self.top_m
        self._cta_style = 'text+arrow'  # definido em render()

    # ── Background ──────────────────────────────────────────────
    def _build_bg_defs(self):
        """Retorna string de defs extras para efeitos de background."""
        defs = []
        if self.bg_eff == 'grayscale':
            defs.append('<filter id="bgbw" color-interpolation-filters="sRGB">'
                        '<feColorMatrix type="saturate" values="0"/></filter>')
        elif self.bg_eff == 'gradient':
            defs.append(
                f'<linearGradient id="bgg" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0%" stop-color="{self.bg}" stop-opacity="0.0"/>'
                f'<stop offset="60%" stop-color="{self.bg}" stop-opacity="0.45"/>'
                f'<stop offset="100%" stop-color="{self.bg}" stop-opacity="0.90"/>'
                f'</linearGradient>')
        elif self.bg_eff == 'vignette':
            defs.append(
                f'<radialGradient id="bgvig" cx="50%" cy="50%" r="70%">'
                f'<stop offset="0%" stop-color="transparent"/>'
                f'<stop offset="100%" stop-color="{self.bg}" stop-opacity="0.75"/>'
                f'</radialGradient>')
        return '\n'.join(defs)

    def _render_bg(self):
        W, H = self.W, self.H
        bg_defs = self._build_bg_defs()

        if self.bg_img:
            flt = ' filter="url(#bgbw)"' if self.bg_eff == 'grayscale' else ''
            op  = f' opacity="{self.bg_op}"' if self.bg_op < 1 else ''

            # Aplicar crop se definido: viewBox/preserveAspectRatio via clipPath
            if self.bg_crop:
                cx = float(self.bg_crop.get('x', 0))
                cy = float(self.bg_crop.get('y', 0))
                cw = float(self.bg_crop.get('w', W))
                ch = float(self.bg_crop.get('h', H))
                # Calcular escala para preencher o canvas
                sx = W / cw; sy = H / ch
                s  = max(sx, sy)
                iw = cw * s; ih = ch * s
                ix = -(cx * s); iy = -(cy * s)
                self.parts.append(
                    f'<image href="data:image/jpeg;base64,{self.bg_img}" '
                    f'x="{ix:.1f}" y="{iy:.1f}" width="{iw:.1f}" height="{ih:.1f}" '
                    f'preserveAspectRatio="none"{flt}{op}/>')
            else:
                self.parts.append(
                    f'<image href="data:image/jpeg;base64,{self.bg_img}" '
                    f'x="0" y="0" width="{W}" height="{H}" '
                    f'preserveAspectRatio="xMidYMid slice"{flt}{op}/>')

            # Overlay de efeito
            if self.bg_eff == 'gradient':
                self.parts.append(R(0, 0, W, H, '0', 'url(#bgg)', 1.0))
            elif self.bg_eff == 'vignette':
                self.parts.append(R(0, 0, W, H, '0', 'url(#bgvig)', 1.0))
            elif not self.bg_eff:
                # Overlay sutil de cor para garantir contraste do texto
                self.parts.append(R(0, 0, W, H, '0', self.bg, 0.20))
        else:
            self.parts.append(R(0, 0, W, H, '0', self.bg, 1.0))

    # ── Blocos ──────────────────────────────────────────────────
    def _render_block(self, block, lang, country, country_scale):
        bt = block['type']
        if not block.get('visible', True): return

        if bt == 'divider': self._blk_divider(block); return
        if bt == 'spacer':  self.y += max(10, int(float(block.get('size', 100)) * 0.3)); return
        if bt == 'image':   self._blk_image(block); return

        fk  = block.get('font', 'poppins')
        ff  = gf(fk, lang)
        fs  = block_fs(block, country_scale)
        col = block.get('color', '#FFFFFF')
        fw_ = block_fw(block)
        ls  = int(block.get('ls', 0))
        op  = float(block.get('opacity', 1.0))
        flt = block.get('flt', '')
        yo  = int(block.get('y_offset', 0))
        x, anc = block_x(block)  # já inclui x_offset
        safe_w = sw(XR - x - 10, fk, lang) if anc == 'start' else sw(CW, fk, lang)
        text = str(block.get('text', '')).strip()
        if not text: return

        if bt == 'disclaimer': self._blk_disc(text, fk, ff, lang, col, fs, op); return
        if bt == 'cta':        self._blk_cta(text, fk, ff, lang, col, fs, fw_, x, anc, ls, op,
                                             cta_style=self._cta_style); return
        if bt == 'value':      self._blk_val(text, fk, ff, lang, col, fs, fw_, x, anc, ls, op, yo, flt); return

        # headline / subhead
        lines = wrap(text, fs, safe_w)
        br    = 16 if bt == 'headline' else 12
        g     = gap_s(fk, fs, br)
        y     = first_y(self.y + yo, fk, fs)
        for i, ln in enumerate(lines):
            y_ln = y + i * g
            if y_ln < self.ct - 10:
                self.parts.append(T(x, y_ln, ln, fw_, fs, col, ff, anc, ls=ls, op=op, flt=flt))
        last = y + (len(lines) - 1) * g
        self.y = bottom_of(last, fk, fs) + br

    def _blk_val(self, text, fk, ff, lang, col, fs, fw_, x, anc, ls, op, yo, flt):
        p1, sep, p2 = spv(text)
        safe_w = sw(XR - x - 10, fk, lang) if anc == 'start' else sw(CW, fk, lang)
        vfs = min(fit(p1, safe_w, hi=fs, lo=20),
                  fit(p2 if sep else p1, safe_w, hi=fs, lo=20))
        y   = first_y(self.y + yo, fk, vfs)
        eff = flt or ('glow' if col.upper() != '#FFFFFF' else '')
        if sep:
            sf2 = max(20, int(vfs * 0.50) // 2 * 2)
            self.parts.append(T(x, y, p1, fw_, vfs, col, ff, anc, ls=-1, op=op * 0.70))
            y += gap_ab(fk, vfs, fk, sf2, 12)
            self.parts.append(T(x, y, sep, '300', sf2, col, ff, anc, op=op * 0.55))
            y += gap_ab(fk, sf2, fk, vfs, 16)
            self.parts.append(T(x, y, p2, fw_, vfs, col, ff, anc, ls=-2, flt=eff))
        else:
            self.parts.append(T(x, y, p1, fw_, vfs, col, ff, anc, ls=ls, op=op, flt=eff))
        self.y = bottom_of(y, fk, vfs) + 18

    def _blk_cta(self, text, fk, ff, lang, col, fs, fw_, x, anc, ls, op, cta_style='text+arrow'):
        # CTA no fluxo de blocos — usa mesmo sistema de estilos
        ratio = gr(fk, lang); y = first_y(self.y, fk, max(fs, 28))

        if cta_style in ('arrow-only','arrow-pulse','arrow-blink'):
            animate = {'arrow-pulse':'pulse','arrow-blink':'blink'}.get(cta_style)
            self._cta_arrow_only(y + 20, col, size=int(fs * 1.8), animate=animate)
            self.y = y + int(fs * 2.2)
        elif cta_style == 'double-arrow':
            self._cta_double_arrow(y, col, size=int(fs * 1.4))
            self.y = y + int(fs * 3.2)
        elif cta_style == 'tap-hint':
            self._cta_tap_hint(y + int(fs * 1.4), col, self.bg, size=int(fs * 2))
            self.y = y + int(fs * 3.0)
        else:
            # text+arrow e bar-arrow no fluxo
            arrow = '↓'; afs = 54
            aw    = int(ew(arrow, afs) * ratio) + 8
            cfs   = fit(text, sw(CW - aw - 28, fk, lang), hi=fs, lo=14)
            tw    = int(ew(text, cfs) * ratio)
            total = tw + 24 + aw
            tx    = max(XL, XR - total) if not self.is9 else max(XL, CX - total // 2)
            arx   = min(XR - aw, tx + tw + 24)
            self.parts += [
                T(tx, y, text, fw_, cfs, col, ff, ls=ls, op=op),
                T(arx, y, arrow, '900', afs, col, ff, flt='glowSm'),
                L(tx, y + 12, arx + aw, col, 2, 0.55),
            ]
            self.y = bottom_of(y, fk, cfs) + 16

    def _blk_disc(self, text, fk, ff, lang, col, fs, op):
        sf    = sw(CW, fk, lang)
        lines = wrap(text, fs, sf)
        g     = gap_s(fk, fs, 8)
        y     = first_y(self.y, fk, fs)
        for i, ln in enumerate(lines):
            y_ln = y + i * g
            if y_ln < self.H - 20:
                self.parts.append(T(CX, y_ln, ln, '400', fs, col, ff, 'middle', op=op))
        self.y = bottom_of(y + (len(lines) - 1) * g, fk, fs) + 8

    def _blk_divider(self, block):
        col = block.get('color', '#FFFFFF')
        op  = float(block.get('opacity', 0.30))
        w   = int(float(block.get('size', 60)) / 100 * CW)
        a   = block.get('align', 'left')
        xo  = int(block.get('x_offset', 0))
        if a == 'center':  x1 = CX - w // 2 + xo; x2 = CX + w // 2 + xo
        elif a == 'right': x1 = XR - w + xo;       x2 = XR + xo
        else:              x1 = XL + xo;             x2 = XL + w + xo
        self.y += 8
        self.parts.append(L(x1, self.y, x2, col, 2, op))
        self.y += 16

    def _blk_image(self, block):
        b64 = block.get('text', '')
        if not b64: return
        ih  = max(40, int(200 * float(block.get('size', 100)) / 100))
        iw  = min(CW, int(ih * 1.5))
        a   = block.get('align', 'left')
        xo  = int(block.get('x_offset', 0))
        if a == 'center':  ix = CX - iw // 2 + xo
        elif a == 'right': ix = XR - iw + xo
        else:              ix = XL + xo
        op  = float(block.get('opacity', 1.0))
        yo  = int(block.get('y_offset', 0))
        self.parts.append(
            f'<image href="data:image/jpeg;base64,{b64}" '
            f'x="{ix}" y="{self.y + yo}" width="{iw}" height="{ih}" '
            f'preserveAspectRatio="xMidYMid meet" opacity="{op}"/>')
        self.y += ih + 14

    # ── CTA e Disc fixos ────────────────────────────────────────
    # ── CTA helpers ─────────────────────────────────────────────

    def _cta_overlay(self, sy, ac_col):
        """Overlay de fundo + linha separadora — comum a todos os estilos."""
        self.parts += [
            R(0, sy, 1080, 1080, '0', self.bg, 0.96),
            L(XL, sy, XR, ac_col, 1.5, 0.35),
        ]

    def _cta_arrow_only(self, cy, ac_col, size=160, animate=None):
        """Só seta grande centralizada. animate: None | 'pulse' | 'blink'."""
        # Seta como path geométrico (chevron ↓) mais expressivo que texto
        afs = size
        cx  = CX
        # Grupo com seta + glow
        anim = ''
        if animate == 'pulse':
            # Bounce vertical: sobe 20px e volta
            anim = (f'<animateTransform attributeName="transform" type="translate" '
                    f'values="0,0;0,20;0,0" dur="1.2s" repeatCount="indefinite" '
                    f'calcMode="spline" keySplines="0.4 0 0.2 1;0.4 0 0.2 1"/>')
        elif animate == 'blink':
            anim = (f'<animate attributeName="opacity" '
                    f'values="1;0.15;1" dur="1.0s" repeatCount="indefinite"/>')

        if anim:
            self.parts.append(
                f'<g filter="url(#glowSm)">'
                f'<text x="{cx}" y="{cy}" font-size="{afs}" fill="{ac_col}" '
                f'text-anchor="middle" font-weight="900">{anim}↓</text></g>')
        else:
            self.parts.append(
                T(cx, cy, '↓', '900', afs, ac_col, 'sans-serif', 'middle', flt='glowSm'))

    def _cta_double_arrow(self, cy, ac_col, size=110):
        """Duas setas empilhadas com delay de fase na animação."""
        cx = CX; gap = int(size * 0.55)
        for i, yo in enumerate([0, gap]):
            delay = f'{i * 0.3:.1f}s'
            anim  = (f'<animate attributeName="opacity" '
                     f'values="0.4;1;0.4" dur="1.0s" begin="{delay}" repeatCount="indefinite"/>')
            self.parts.append(
                f'<text x="{cx}" y="{cy + yo}" font-size="{size}" fill="{ac_col}" '
                f'text-anchor="middle" font-weight="900" filter="url(#glowSm)">'
                f'{anim}↓</text>')

    def _cta_tap_hint(self, cy, ac_col, bg_col, size=120):
        """Círculo com seta dentro — estilo tap indicator do Instagram/TikTok."""
        cx = CX; r = int(size * 0.55)
        anim = (f'<animate attributeName="opacity" '
                f'values="1;0.55;1" dur="1.4s" repeatCount="indefinite"/>')
        anim2 = (f'<animate attributeName="r" '
                 f'values="{r};{r+8};{r}" dur="1.4s" repeatCount="indefinite"/>')
        # Círculo externo pulsante
        self.parts.append(
            f'<circle cx="{cx}" cy="{cy - int(size*0.3)}" r="{r}" '
            f'fill="{ac_col}" opacity="0.12">{anim2}</circle>')
        # Círculo sólido
        self.parts.append(
            f'<circle cx="{cx}" cy="{cy - int(size*0.3)}" r="{int(r*0.75)}" '
            f'fill="{ac_col}" opacity="0.90" filter="url(#glowSm)"/>')
        # Seta dentro
        inner_fs = int(size * 0.55)
        self.parts.append(
            f'<text x="{cx}" y="{cy - int(size*0.3) + int(inner_fs*0.38)}" '
            f'font-size="{inner_fs}" fill="{bg_col}" '
            f'text-anchor="middle" font-weight="900">{anim}↓</text>')

    def _cta_bar_arrow(self, sy, cy, ac_col, cta_col, text, fk, lang, cfs):
        """Faixa larga colorida com seta + texto. Call-to-action agressivo."""
        ff   = gf(fk, lang); bh = 90; bar_y = cy - 48
        # Faixa sólida
        self.parts.append(R(XL - 10, bar_y, CW + 20, bh, '6', ac_col, 0.95))
        # Texto na faixa
        self.parts.append(T(CX - 36, cy, text, '900', cfs, cta_col, ff, 'middle', ls=2))
        # Seta grande à direita
        self.parts.append(T(XR - 30, cy, '↓', '900', 72, cta_col, 'sans-serif', 'end'))

    def _fixed_cta(self, text, cta_col, ac_col, fk, lang, cta_style='text+arrow'):
        ff    = gf(fk, lang); ratio = gr(fk, lang)
        sy    = 1110 if not self.is9 else 1440
        cy    = 1185 if not self.is9 else 1540

        self._cta_overlay(sy, ac_col)

        if cta_style == 'arrow-only':
            self._cta_arrow_only(cy, ac_col, size=160)
        elif cta_style == 'arrow-pulse':
            self._cta_arrow_only(cy, ac_col, size=160, animate='pulse')
        elif cta_style == 'arrow-blink':
            self._cta_arrow_only(cy, ac_col, size=160, animate='blink')
        elif cta_style == 'double-arrow':
            self._cta_double_arrow(cy - 50, ac_col, size=110)
        elif cta_style == 'tap-hint':
            self._cta_tap_hint(cy + 20, ac_col, self.bg, size=130)
        elif cta_style == 'bar-arrow':
            arrow = '↓'; afs = 54
            cfs = fit(text, sw(CW - 80, fk, lang), hi=28, lo=14)
            self._cta_bar_arrow(sy, cy, ac_col, cta_col, text, fk, lang, cfs)
        else:
            # text+arrow (default)
            arrow = '↓'; afs = 54
            aw    = int(ew(arrow, afs) * ratio) + 8
            cfs   = fit(text, sw(CW - aw - 28, fk, lang), hi=28, lo=14)
            tw    = int(ew(text, cfs) * ratio)
            total = tw + 24 + aw
            tx    = max(XL, XR - total) if not self.is9 else max(XL, CX - total // 2)
            arx   = min(XR - aw, tx + tw + 24)
            self.parts += [
                T(tx,  cy, text,  '900', cfs, cta_col, ff, ls=1),
                T(arx, cy, arrow, '900', afs, ac_col,  ff, flt='glowSm'),
                L(tx,  cy + 12, arx + aw, ac_col, 2, 0.55),
            ]

    def _fixed_disc(self, text, disc_col, fk, lang):
        ff  = gf(fk, lang)
        dy  = 1228 if not self.is9 else 1830
        sf  = sw(CW, fk, lang)
        self.parts.append(L(XL, dy - 16, XR, disc_col, 0.5, 0.20))
        for wl in wrap(text, 13, sf):
            self.parts.append(T(CX, dy, wl, '400', 13, disc_col, ff, 'middle', op=0.72))
            dy += 18

    # ── Render principal ────────────────────────────────────────
    def render(self, blocks, lang='pt-BR', country='BR',
               cta_text='SIMULAR AGORA', cta_color='#FFFFFF', ac_color='#FFDF00',
               disc_text='', disc_color='#AAAAAA',
               fk_cta='poppins', fk_disc='poppins',
               cta_style='text+arrow'):
        W, H = self.W, self.H
        sc   = tsc(country)
        self._cta_style = cta_style  # usado por _fixed_cta e _blk_cta
        type_scales = {'headline': sc['h'], 'subhead': sc['s'], 'value': sc['v']}

        # Construir DEFS completo: glow filters + bg extras
        bg_defs_str = self._build_bg_defs()
        full_defs   = DEFS()
        if bg_defs_str:
            # Inserir bg_defs dentro do <defs> existente
            full_defs = full_defs.replace('</defs>', bg_defs_str + '\n</defs>')

        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            full_defs,
        ]

        # Fundo
        self._render_bg()
        out += self.parts; self.parts = []

        # Decoração geométrica (bg_svg_45 ou bg_svg_916)
        if self.bg_svg_decor:
            out.append(self.bg_svg_decor)

        # Blocos
        has_cta  = any(b['type'] == 'cta'         and b.get('visible', True) for b in blocks)
        has_disc = any(b['type'] == 'disclaimer'   and b.get('visible', True) for b in blocks)

        for block in blocks:
            if not block.get('visible', True): continue
            cscale = type_scales.get(block['type'], 1.0)
            self._render_block(block, lang=lang, country=country, country_scale=cscale)

        out += self.parts; self.parts = []

        if not has_cta and cta_text:
            self._fixed_cta(cta_text, cta_color, ac_color, fk_cta, lang,
                            cta_style=self._cta_style)
            out += self.parts; self.parts = []

        if not has_disc and disc_text:
            self._fixed_disc(disc_text, disc_color, fk_disc, lang)
            out += self.parts; self.parts = []

        out.append('</svg>')
        return '\n'.join(out)


# ── Ponto de entrada ─────────────────────────────────────────────
def render_document(doc, fmt='45'):
    """
    Renderiza DocumentState → SVG.
    Seleciona bg_svg_45 ou bg_svg_916 conforme fmt.
    Suporta bg_crop para recorte da imagem de fundo.
    """
    is9 = (fmt == '916')  # '45' é o formato 4:5 (não-9:16)
    if is9:
        bg_svg = doc.get('bg_svg_916') or doc.get('bg_svg', '') or doc.get('bg_svg_decor', '')
    else:
        bg_svg = doc.get('bg_svg_45')  or doc.get('bg_svg', '') or doc.get('bg_svg_decor', '')

    r = BlockRenderer(
        is9          = is9,
        bg_color     = doc.get('bg', '#000000'),
        bg_image_b64 = doc.get('bg_image') or doc.get('bg_image_b64'),
        bg_effect    = doc.get('bg_effect'),
        bg_opacity   = float(doc.get('bg_opacity', 1.0)),
        bg_svg_decor = bg_svg,
        bg_crop      = doc.get('bg_crop'),     # {'x','y','w','h'} ou None
    )
    return r.render(
        blocks     = doc.get('blocks', []),
        lang       = doc.get('lang', 'pt-BR'),
        country    = doc.get('country', 'BR'),
        cta_text   = doc.get('cta_text', 'SIMULAR AGORA'),
        cta_color  = doc.get('cta_color', '#FFFFFF'),
        ac_color   = doc.get('ac_color', '#FFDF00'),
        disc_text  = doc.get('disc_text', ''),
        disc_color = doc.get('disc_color', '#AAAAAA'),
        fk_cta     = doc.get('fk_cta', 'poppins'),
        fk_disc    = doc.get('fk_disc', 'poppins'),
        cta_style  = doc.get('cta_style', 'text+arrow'),
    )


def doc_fingerprint(doc, fmt):
    """Hash determinístico do doc para cache (exclui bg_image por tamanho)."""
    import json
    safe = {
        'b':  [(b.get('id'),b.get('type'),b.get('text'),b.get('font'),b.get('size'),
                b.get('color'),b.get('align'),b.get('weight'),b.get('ls'),
                b.get('opacity'),b.get('visible'),b.get('y_offset'),b.get('x_offset'),b.get('flt'))
               for b in doc.get('blocks', [])],
        'bg': doc.get('bg'), 'bge': doc.get('bg_effect'), 'bgo': doc.get('bg_opacity'),
        'bgc': doc.get('bg_crop'),
        'bs34': (doc.get('bg_svg_45') or '')[:60],
        'bs916': (doc.get('bg_svg_916') or '')[:60],
        'cc': doc.get('country'), 'la': doc.get('lang'),
        'ct': doc.get('cta_text'), 'co': doc.get('cta_color'), 'ac': doc.get('ac_color'), 'cs': doc.get('cta_style','text+arrow'),
        'dt': doc.get('disc_text'), 'fmt': fmt,
    }
    raw = json.dumps(safe, sort_keys=True, default=str)
    h = 0
    for c in raw: h = (31 * h + ord(c)) & 0xFFFFFFFF
    return f'{h:08x}{len(raw)}'
