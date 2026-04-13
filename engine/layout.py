#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio3 — Layout Engine (o "chefe sênior")
Sistema sequencial de posicionamento vertical:
- Cada bloco conhece seu próprio topo e fundo
- Nenhum elemento começa acima do fundo do anterior
- Quebras de linha automáticas empurram os blocos seguintes para baixo
- Textos nunca ultrapassam a zona de CTA
"""
from engine.core import (
    XL, XR, CX, CW, FONTS, gf, gr, sw, ew,
    gap_ab, gap_s, first_y, bottom_of,
    fit, wrap, fw, atc, ctr, sac, mix, spv,
    tsc, T, R, L, Lv, Ci, Pg, Arc, CTA, DISC, VBLOCK, svg_wrap
)


class LayoutCursor:
    """
    Gerencia posicionamento vertical garantindo anti-colisão.
    Regra absoluta: next_top >= current_bottom + breathing.
    """
    def __init__(self, y_start, ct, breathing_default=20):
        self.y   = y_start        # topo do próximo bloco
        self.ct  = ct             # limite superior da zona CTA
        self.br  = breathing_default
        self.parts = []           # acumula SVG strings

    def advance(self, y_bottom, extra_breathing=0):
        """Avança o cursor para abaixo do último bloco renderizado."""
        self.y = y_bottom + self.br + extra_breathing

    def available(self):
        """Pixels restantes até a zona CTA."""
        return self.ct - self.y

    def fits(self, needed_px):
        return self.available() >= needed_px

    def add(self, svg_str):
        if svg_str: self.parts.append(svg_str)

    def output(self):
        return '\n'.join(self.parts)


def render_head_block(cursor, text, fk, ff, lang, color, scale=1.0, ml=3,
                      x=None, anc='start', fw_='900', ls=-1):
    """Renderiza headline com wrap automático. Empurra cursor para baixo."""
    x = x if x is not None else XL
    sf = sw(XR - x - 10, fk, lang)
    hi  = max(int(88 * scale), 28)
    lo  = max(int(28 * scale), 20)
    h_fs, lines = fw([text], sf, fk, lang, hi=hi, lo=lo, ml=ml)
    y = first_y(cursor.y, fk, h_fs)
    g = gap_s(fk, h_fs, 14)
    for i, ln in enumerate(lines):
        y_ln = y + i*g
        if y_ln < cursor.ct - 10:
            cursor.add(T(x, y_ln, ln, fw_, h_fs, color, ff, anc, ls=ls))
    last_baseline = y + (len(lines)-1)*g
    y_bot = bottom_of(last_baseline, fk, h_fs)
    cursor.advance(y_bot, 6)
    return h_fs, lines, last_baseline


def render_sub_block(cursor, text, fk, ff, lang, color, scale=1.0,
                     x=None, anc='start', fw_='300', opacity=0.78):
    """Renderiza subhead com wrap. Empurra cursor."""
    x = x if x is not None else XL
    sub_fs = max(int(30 * scale), 18)
    sf = sw(XR - x - 10, fk, lang)
    lines = wrap(text, sub_fs, sf)
    g = gap_s(fk, sub_fs, 12)
    y = first_y(cursor.y, fk, sub_fs)
    for i, ln in enumerate(lines):
        y_ln = y + i*g
        if y_ln < cursor.ct - 10:
            cursor.add(T(x, y_ln, ln, fw_, sub_fs, color, ff, anc, op=opacity))
    last_baseline = y + (len(lines)-1)*g
    y_bot = bottom_of(last_baseline, fk, sub_fs)
    cursor.advance(y_bot, 4)
    return sub_fs, lines, last_baseline


def render_valor_block(cursor, valor_str, fk, ff, lang, bg, pal, scale=1.0,
                       x=None, anc='start'):
    """Renderiza bloco de valor (split). Empurra cursor."""
    x = x if x is not None else XL
    p1, sep, p2 = spv(valor_str)
    sf = sw(XR - x - 10, fk, lang)
    hi  = max(int(96 * scale), 24)
    lo  = max(int(22 * scale), 20)
    vfs = min(fit(p1, sf, hi=hi, lo=lo), fit(p2 if sep else p1, sf, hi=hi, lo=lo))
    vs, y_bot = VBLOCK(x, cursor.y, p1, sep, p2, vfs, fk, ff, bg, pal, anc)
    cursor.add(vs)
    cursor.advance(y_bot, 4)
    return vfs, p1, sep, p2


def render_sep_line(cursor, x1, x2, color, width=2, opacity=0.5, gap_before=8, gap_after=12):
    """Renderiza linha separadora na posição atual do cursor."""
    y = cursor.y + gap_before
    cursor.add(L(x1, y, x2, color, width, opacity))
    cursor.y = y + gap_after
