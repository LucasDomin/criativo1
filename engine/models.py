#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio3 — 14 Modelos SVG
Todos usam LayoutCursor: nenhum texto ultrapassa outro.
Inspirados nas tendências 2025: bold minimalism, oversized type,
geometric shapes, anti-design, retro-futurism, diagonal, data dashboard.
"""
import math
from engine.core import (
    XL, XR, CX, CW, FONTS, gf, gr, sw, ew,
    gap_ab, gap_s, first_y, bottom_of,
    fit, wrap, fw, atc, ctr, sac, mix, spv, tsc,
    T, R, L, Lv, Ci, Pg, Arc, CTA, DISC, VBLOCK, svg_wrap,
    cap, desc
)
from engine.layout import (
    LayoutCursor, render_head_block, render_sub_block,
    render_valor_block, render_sep_line
)


def _setup(c, is9, pal, country, fk_default):
    """Setup padrão para todos os modelos."""
    lang = c['lang']
    ff   = gf(fk_default, lang)
    bg   = pal['bg']; ac = pal['a1']; tc = atc(bg)
    W, H = 1080, 1920 if is9 else 1440
    top  = 280 if is9 else 90
    ct   = 1440 if is9 else 1185
    sc   = tsc(country)
    return lang, ff, bg, ac, tc, W, H, top, ct, sc


# ══════════════════════════════════════════════════════════════════
# A — BOLD MANIFESTO  |  Poppins
# Tendência: Bold Minimalism — tipografia 900 dominante, barras nacionais
# Layout: cursor sequencial, sub compacta, valor com glow
# ══════════════════════════════════════════════════════════════════
def model_A(c, is9, pal, country='US', opts=None):
    opts = opts or {}
    fk   = opts.get('font_head','poppins')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c, is9, pal, country, fk)
    flags = pal['flags']
    cur   = LayoutCursor(top, ct, breathing_default=22)
    parts = []

    # ── Decoração ──
    parts.append(R(0,0,14,ct,'0',flags[0],1.0))
    if len(flags)>1: parts.append(R(14,0,7,ct,'0',flags[1],0.70))
    if len(flags)>2: parts.append(R(21,0,6,ct,'0',flags[2],0.50))
    d1=int(H*0.44); d2=int(H*0.48)
    parts.append(f'<polygon points="0,{d1} {W},{d2-20} {W},{d2} 0,{d1+20}" fill="{ac}" opacity="0.08"/>')

    # ── Head ──
    hc = opts.get('color_head', ac)
    head_scale = sc['h'] * opts.get('head_scale', 1.0)
    sub_scale  = sc['s'] * opts.get('sub_scale',  1.0)
    val_scale  = sc['v'] * opts.get('val_scale',  1.0)
    cur.y = top
    h_fs, _, h_base = render_head_block(
        cur, c['head'], fk, ff, lang, hc,
        scale=head_scale, ml=sc['ml'], fw_='900', ls=-2)
    parts.append(cur.output()); cur.parts=[]

    # ── Separador ──
    render_sep_line(cur, XL+28, XL+180, ac, width=3, opacity=0.85, gap_before=4, gap_after=18)
    parts.append(cur.output()); cur.parts=[]

    # ── Sub ──
    sc_ = opts.get('color_sub', tc)
    render_sub_block(cur, c['sub'], fk, ff, lang, sc_,
                     scale=sub_scale, fw_='300', opacity=float(opts.get('opacity_sub',0.78)))
    parts.append(cur.output()); cur.parts=[]

    # ── Valor ──
    cur.y += 12
    vc_ = opts.get('color_val', None)
    if vc_:
        from engine.core import atc as _atc, sac as _sac
        pal_v = {**pal, 'a1': vc_}
    else:
        pal_v = pal
    render_valor_block(cur, c['valor'], fk, ff, lang, bg, pal_v, scale=val_scale)
    parts.append(cur.output()); cur.parts=[]

    return svg_wrap(W, H, bg,
        '\n'.join(parts)
        + '\n' + CTA(c,pal,is9,ff,fk,lang,bg)
        + '\n' + DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# B — ARC GAUGE  |  Liberation Sans
# Tendência: Data Dashboard, Fintech UI — velocímetro financeiro
# ══════════════════════════════════════════════════════════════════
def model_B(c, is9, pal, country='US', opts=None):
    opts = opts or {}
    fk   = opts.get('font_head','libsans')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c, is9, pal, country, fk)
    flags = pal['flags']
    cur   = LayoutCursor(top, ct, breathing_default=20)
    parts = []

    # ── Head ──
    hc = opts.get('color_head', tc)
    h_fs,_,_ = render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='700',ls=0)
    parts.append(cur.output()); cur.parts=[]

    # ── Sub ──
    sc_ = opts.get('color_sub', tc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='300',opacity=0.75)
    parts.append(cur.output()); cur.parts=[]

    # ── Arco gauge ──
    arc_avail = ct - cur.y - 80
    arc_r     = min(int(arc_avail*0.46), 320)
    arc_cx    = CX
    arc_cy    = min(cur.y + arc_r + 20, ct - 60)

    parts.append(Arc(arc_cx,arc_cy,arc_r,0,220,mix(tc,bg,0.85),sw_=26,op=0.18))
    parts.append(Arc(arc_cx,arc_cy,arc_r,0,165,ac,sw_=26,op=0.22))
    parts.append(Arc(arc_cx,arc_cy,arc_r,0,165,ac,sw_=9,op=0.90))
    parts.append(Arc(arc_cx,arc_cy,arc_r-40,0,220,mix(tc,bg,0.70),sw_=1,op=0.28))
    er=math.radians(165-90); tip_x=arc_cx+arc_r*math.cos(er); tip_y=arc_cy+arc_r*math.sin(er)
    parts.append(Ci(int(tip_x),int(tip_y),17,ac,1.0))
    parts.append(Ci(int(tip_x),int(tip_y),7,bg,1.0))
    for deg in range(0,221,22):
        a=math.radians(deg-90)
        x1=arc_cx+(arc_r-32)*math.cos(a); y1=arc_cy+(arc_r-32)*math.sin(a)
        x2=arc_cx+(arc_r+32)*math.cos(a); y2=arc_cy+(arc_r+32)*math.sin(a)
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{tc}" stroke-width="2" opacity="0.16"/>')
    for i,fc in enumerate(flags[:3]):
        fa=math.radians(-90+i*30)
        parts.append(Ci(int(arc_cx+(arc_r+52)*math.cos(fa)),int(arc_cy+(arc_r+52)*math.sin(fa)),7,fc,0.80))

    # ── Valor no centro do arco ──
    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(int(arc_r*1.5),fk,lang),hi=max(int(68*sc['v']),20),lo=18),
            fit(p2 if sv else p1,sw(int(arc_r*1.5),fk,lang),hi=max(int(68*sc['v']),20),lo=18))
    vc_ = opts.get('color_val', ac)
    ly=arc_cy+int(cap(fk)*vfs*0.4)
    if sv:
        sf2=max(20,int(vfs*0.48)//2*2)
        parts.append(T(arc_cx,ly,p1,'900',vfs,tc,ff,'middle',ls=-1,op=0.68))
        ly+=gap_ab(fk,vfs,fk,sf2,12)
        parts.append(T(arc_cx,ly,sv,'300',sf2,tc,ff,'middle',op=0.50))
        ly+=gap_ab(fk,sf2,fk,vfs,14)
        parts.append(T(arc_cx,ly,p2,'900',vfs,vc_,ff,'middle',ls=-2,flt='glow'))
    else:
        parts.append(T(arc_cx,ly,p1,'900',vfs,vc_,ff,'middle',ls=-2,flt='glow'))

    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# C — DIAGONAL CLASH  |  Lora
# Tendência: Split-screen, dois mundos em contraste
# ══════════════════════════════════════════════════════════════════
def model_C(c, is9, pal, country='US', opts=None):
    opts = opts or {}
    fk   = opts.get('font_head','lora')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c, is9, pal, country, fk)
    flags = pal['flags']
    cut_top=int(ct*0.45); cut_bot=int(ct*0.54)
    lbg=mix(ac,'#FFFFFF',0.88) if atc(ac)=='#0A0204' else mix(ac,'#F8F8F8',0.25)
    if atc(lbg)!='#0A0204': lbg='#F5F5F0'
    dtc=atc(bg); ltc=atc(lbg)
    parts=[]
    parts.append(R(0,0,W,H,'0',lbg,1.0))
    parts.append(f'<polygon points="0,0 {W},0 {W},{cut_top} 0,{cut_bot}" fill="{bg}"/>')
    for i,fc in enumerate(flags[:3]):
        fh=int(cut_bot/max(len(flags[:3]),1)); parts.append(R(0,i*fh,10,fh,'0',fc,0.50))

    # ── Head na zona escura ──
    cur=LayoutCursor(top,cut_top-10,22)
    hc=opts.get('color_head',dtc)
    render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='700',ls=0)
    parts.append(cur.output()); cur.parts=[]
    sc_=opts.get('color_sub',dtc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='400',opacity=0.78)
    parts.append(cur.output())

    # ── Valor na zona clara ──
    cur2=LayoutCursor(cut_bot+36,ct,20)
    vc_=opts.get('color_val',sac(ac,lbg))
    pal_cl={**pal,'a1':vc_}
    render_valor_block(cur2,c['valor'],fk,ff,lang,lbg,pal_cl,scale=sc['v'])
    parts.append(cur2.output())

    return svg_wrap(W,H,lbg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,lbg)+'\n'+DISC(c,pal,is9,ff,fk,lang,lbg))


# ══════════════════════════════════════════════════════════════════
# D — TERMINAL STREAM  |  Carlito
# Tendência: Data/Tech aesthetic — CRT, scanlines, terminal prompt
# ══════════════════════════════════════════════════════════════════
def model_D(c, is9, pal, country='US', opts=None):
    opts = opts or {}
    fk   = opts.get('font_head','carlito')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c, is9, pal, country, fk)
    tbg='#020A06' if atc(bg)=='#FFFFFF' else mix(bg,'#020A06',0.40)
    tc =atc(tbg)
    tg =ac if ctr(ac,tbg)>=4.5 else '#00FF88'; td=mix(tg,tbg,0.55)
    parts=[]
    for sy in range(0,H,6):
        parts.append(f'<line x1="0" y1="{sy}" x2="{W}" y2="{sy}" stroke="{tg}" stroke-width="0.5" opacity="0.03"/>')
    ty=top-50
    parts.append(R(0,ty-8,W,38,'0',tg,0.08)); parts.append(L(0,ty-8,W,tg,0.5,0.40))
    for j,item in enumerate(['SCORE:●●●●○','STATUS:APPROVED','RATE:0.99%','RISK:LOW']):
        tx_=XL+j*220
        if tx_<W-80: parts.append(T(tx_,ty+14,item,'400',16,tg,ff,ls=1,op=0.65))
    py=first_y(top,fk,22); parts.append(T(XL,py,'> CREDIT_ANALYSIS.exe','400',22,td,ff,ls=1))
    yr=py+int(desc(fk)*22)+14; parts.append(L(XL,yr,XR,tg,0.5,0.35))

    cur=LayoutCursor(yr+16,ct,18)
    hc=opts.get('color_head',tc)
    # Render head com prefixo >
    h_fs,h_lines,h_base=render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='700')
    for i,ln in enumerate(h_lines):
        px='> ' if i==0 else '  '
        parts.append(T(XL,cur.y - (len(h_lines)-1)*gap_s(fk,h_fs,14) + i*gap_s(fk,h_fs,14),px,'400',h_fs,td,ff,op=0.60))
    parts.append(cur.output()); cur.parts=[]
    sc_=opts.get('color_sub',td)
    # Sub com prefixo //
    sub_fs=max(int(24*sc['s']),18)
    sub_lines=wrap(c['sub'],sub_fs,sw(CW-40,fk,lang))
    y=first_y(cur.y,fk,sub_fs); gs_=gap_s(fk,sub_fs,10)
    for i,ln in enumerate(sub_lines):
        y_ln=y+i*gs_
        if y_ln<ct-20: parts.append(T(XL,y_ln,'// '+ln,'300',sub_fs,sc_,ff,op=0.75))
    cur.y=bottom_of(y+(len(sub_lines)-1)*gs_,fk,sub_fs)+18

    # Caixa terminal para valor
    p1,sv,p2=spv(c['valor'])
    vc_=opts.get('color_val',tg)
    vfs=min(fit(p1,sw(CW-20,fk,lang),hi=max(int(82*sc['v']),22),lo=20),
            fit(p2 if sv else p1,sw(CW-20,fk,lang),hi=max(int(82*sc['v']),22),lo=20))
    yvt=min(cur.y,ct-240)
    bh=int(cap(fk)*vfs)+int(desc(fk)*vfs)+36
    if sv: sf2=max(20,int(vfs*0.48)//2*2); bh+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,14)
    parts.append(R(XL-12,yvt-8,CW+24,bh+16,'4',tg,0.06))
    parts.append(f'<rect x="{XL-12}" y="{yvt-8}" width="{CW+24}" height="{bh+16}" rx="4" fill="none" stroke="{tg}" stroke-width="0.8" opacity="0.55"/>')
    parts.append(T(XL,yvt,'DISPONÍVEL:','400',15,tg,ff,ls=2,op=0.65))
    yc=yvt+int(cap(fk)*vfs)+18
    if sv:
        sf2=max(20,int(vfs*0.48)//2*2)
        parts.append(T(XL,yc,p1,'700',vfs,tc,ff,ls=-1,op=0.68)); yc+=gap_ab(fk,vfs,fk,sf2,12)
        parts.append(T(XL,yc,'→ '+sv,'300',sf2,td,ff,op=0.55)); yc+=gap_ab(fk,sf2,fk,vfs,14)
        parts.append(T(XL,yc,p2,'900',vfs,vc_,ff,ls=-2,flt='glow'))
    else: parts.append(T(XL,yc,p1,'900',vfs,vc_,ff,ls=-2,flt='glow'))

    return svg_wrap(W,H,tbg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,tbg)+'\n'+DISC(c,pal,is9,ff,fk,lang,tbg))


# ══════════════════════════════════════════════════════════════════
# E — FLOAT CARD  |  Lora / Playfair
# Tendência: Premium Card UI — sombra offset, textura diagonal
# ══════════════════════════════════════════════════════════════════
def model_E(c, is9, pal, country='US', opts=None):
    opts = opts or {}
    fk   = opts.get('font_head','lora')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c, is9, pal, country, fk)
    flags=pal['flags']
    cbg=mix(bg,'#FFFFFF',0.13) if atc(bg)=='#FFFFFF' else mix(bg,'#000000',0.09)
    ctc=atc(cbg); cac=sac(ac,cbg)
    parts=[]
    for xi in range(-H,W+H,60):
        parts.append(f'<line x1="{xi}" y1="0" x2="{xi+H}" y2="{H}" stroke="{tc}" stroke-width="0.8" opacity="0.05"/>')
    for i,fc in enumerate(flags[:3]):
        fh=int(ct/max(len(flags[:3]),1)); parts.append(Lv(W-18,i*fh,i*fh+fh,fc,18,0.45))

    # Sub fora do card
    cur0=LayoutCursor(top,ct,16)
    sc_=opts.get('color_sub',tc)
    render_sub_block(cur0,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='400',opacity=0.68)
    parts.append(cur0.output())

    # Card flutuante
    cm=40; cx=cm; cw=W-2*cm; ctop=cur0.y+24
    h_hi=max(int(72*sc['h']),24); h_lo=max(int(28*sc['h']),22)
    h_fs,h_lines=fw([c['head']],sw(cw-80,fk,lang),fk,lang,hi=h_hi,lo=h_lo,ml=sc['ml'])
    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(cw-80,fk,lang),hi=max(int(88*sc['v']),22),lo=22),
            fit(p2 if sv else p1,sw(cw-80,fk,lang),hi=max(int(88*sc['v']),22),lo=22))
    # Altura do card baseada no conteúdo real
    ch_cnt=(int(cap(fk)*h_fs)+(len(h_lines)-1)*gap_s(fk,h_fs,14)
            +gap_ab(fk,h_fs,fk,vfs,30)+int(cap(fk)*vfs))
    if sv:
        sf2=max(20,int(vfs*0.48)//2*2)
        ch_cnt+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,16)+int(desc(fk)*vfs)
    else: ch_cnt+=int(desc(fk)*vfs)
    cpad=44; card_h=min(ch_cnt+2*cpad, ct-ctop-60)
    parts.append(R(cx+10,ctop+10,cw,card_h,'16',ac,0.15))
    parts.append(R(cx,ctop,cw,card_h,'16',cbg,1.0))
    parts.append(f'<rect x="{cx}" y="{ctop}" width="{cw}" height="6" rx="0" fill="{ac}"/>')
    parts.append(f'<rect x="{cx}" y="{ctop}" width="{cw}" height="16" rx="0" fill="{ac}" fill-opacity="0.18"/>')
    cxi=cx+cpad; yin=ctop+cpad+int(cap(fk)*h_fs); g2=gap_s(fk,h_fs,14)
    hc=opts.get('color_head',ctc)
    for i,ln in enumerate(h_lines):
        if yin+i*g2<ctop+card_h-10: parts.append(T(cxi,yin+i*g2,ln,'700',h_fs,hc,ff))
    yin+=(len(h_lines)-1)*g2
    yr=yin+int(desc(fk)*h_fs)+18
    if yr<ctop+card_h-10: parts.append(L(cxi,yr,cx+cw-cpad,cac,1.5,0.38))
    yv=min(yr+int(cap(fk)*vfs)+14,ctop+card_h-int(desc(fk)*vfs)-10)
    vc_=opts.get('color_val',cac)
    pal_card={**pal,'a1':vc_}
    vs,_=VBLOCK(cxi,yv-int(cap(fk)*vfs),p1,sv,p2,vfs,fk,ff,cbg,pal_card)
    parts.append(vs)
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# F — NATIONAL FRAME  |  Charter / Merriweather
# Tendência: Heritage Serif revival, marca nacional
# ══════════════════════════════════════════════════════════════════
def model_F(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','charter')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']; fr=52; icw=W-2*fr-48
    parts=[]
    for xi in range(-80,W+80,80):
        for yi in range(-80,H+80,80):
            pts=f'{xi},{yi+40} {xi+40},{yi} {xi+80},{yi+40} {xi+40},{yi+80}'
            parts.append(Pg(pts,tc,0.04))
    n=len(flags[:3])
    for i,fc in enumerate(flags[:n]):
        seg=int(W/n)
        for ys,hs in [(0,fr),(H-fr,fr)]: parts.append(R(i*seg,ys,seg,hs,'0',fc,0.75))
        for xs,ws in [(0,fr),(W-fr,fr)]: parts.append(R(xs,fr+i*int((H-2*fr)/n),ws,int((H-2*fr)/n),'0',fc,0.75))
    parts.append(f'<rect x="{fr}" y="{fr}" width="{W-2*fr}" height="{H-2*fr}" rx="0" fill="none" stroke="{tc}" stroke-width="1.5" opacity="0.18"/>')
    for rx_,ry_ in [(50,50),(W-50,50),(50,H-50),(W-50,H-50)]:
        parts.append(f'<line x1="{rx_-16}" y1="{ry_}" x2="{rx_+16}" y2="{ry_}" stroke="{ac}" stroke-width="1" opacity="0.28"/>')
        parts.append(f'<line x1="{rx_}" y1="{ry_-16}" x2="{rx_}" y2="{ry_+16}" stroke="{ac}" stroke-width="1" opacity="0.28"/>')
        parts.append(f'<circle cx="{rx_}" cy="{ry_}" r="6" fill="none" stroke="{ac}" stroke-width="1" opacity="0.28"/>')

    sf=sw(icw,fk,lang)
    cur=LayoutCursor(top,ct,18)
    # Sub centralizada acima da headline (editorial invertido)
    sc_=opts.get('color_sub',tc)
    sub_fs=max(int(22*sc['s']),18)
    sub_lines=wrap(c['sub'],sub_fs,sf)
    y=first_y(cur.y,fk,sub_fs)
    for i,ln in enumerate(sub_lines):
        parts.append(T(CX,y+i*gap_s(fk,sub_fs,10),ln,'400',sub_fs,sc_,ff,'middle',op=0.58,ls=1))
    cur.y=bottom_of(y+(len(sub_lines)-1)*gap_s(fk,sub_fs,10),fk,sub_fs)+18
    parts.append(L(CX-180,cur.y,CX+180,tc,0.8,0.22)); cur.y+=18

    hc=opts.get('color_head',tc)
    h_hi=max(int(76*sc['h']),24)
    h_fs,h_lines=fw([c['head']],sf,fk,lang,hi=h_hi,lo=22,ml=sc['ml'])
    y=first_y(cur.y,fk,h_fs); g2=gap_s(fk,h_fs,14)
    for i,ln in enumerate(h_lines): parts.append(T(CX,y+i*g2,ln,'700',h_fs,hc,ff,'middle',ls=1))
    cur.y=bottom_of(y+(len(h_lines)-1)*g2,fk,h_fs)+18
    parts.append(L(fr+24,cur.y,W-fr-24,tc,2,0.18)); cur.y+=6
    parts.append(L(fr+24,cur.y,W-fr-24,ac,0.8,0.40)); cur.y+=18

    # Bloco valor em caixa
    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(icw-40,fk,lang),hi=max(int(86*sc['v']),22),lo=20),
            fit(p2 if sv else p1,sw(icw-40,fk,lang),hi=max(int(86*sc['v']),22),lo=20))
    vpad=28; vbh=int(cap(fk)*vfs)+int(desc(fk)*vfs)+2*vpad
    if sv: sf2=max(20,int(vfs*0.48)//2*2); vbh+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,16)
    yvb=min(cur.y,ct-vbh-100); ixl=fr+24; icw2=W-2*fr-48
    parts.append(R(ixl,yvb,icw2,vbh,'0',ac,0.18))
    parts.append(f'<rect x="{ixl}" y="{yvb}" width="{icw2}" height="{vbh}" rx="0" fill="none" stroke="{ac}" stroke-width="2" opacity="0.58"/>')
    parts.append(f'<rect x="{ixl}" y="{yvb}" width="{icw2}" height="4" fill="{ac}"/>')
    vc_=opts.get('color_val',sac(ac,mix(bg,ac,0.18)))
    yc=yvb+vpad+int(cap(fk)*vfs)
    if sv:
        sf2=max(20,int(vfs*0.48)//2*2)
        parts.append(T(CX,yc,p1,'700',vfs,atc(mix(bg,ac,0.18)),ff,'middle',ls=-1,op=0.68)); yc+=gap_ab(fk,vfs,fk,sf2,12)
        parts.append(T(CX,yc,sv,'300',sf2,atc(mix(bg,ac,0.18)),ff,'middle',op=0.52)); yc+=gap_ab(fk,sf2,fk,vfs,16)
        parts.append(T(CX,yc,p2,'700',vfs,vc_,ff,'middle',ls=-2,flt='glow'))
    else: parts.append(T(CX,yc,p1,'700',vfs,vc_,ff,'middle',ls=-2,flt='glow'))
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# G — OVERSIZED TYPE  |  Heros Cn / Oswald
# Tendência: Type-as-image, oversized experimental fonts 2025
# ══════════════════════════════════════════════════════════════════
def model_G(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','heros')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    cur=LayoutCursor(top,ct,18)
    parts=[]
    for xi in range(XL,XR,54): # grid pontilhado
        for yi in range(top,ct,54): parts.append(Ci(xi,yi,1.5,tc,0.08))
    for i,fc in enumerate(flags[:3]): parts.append(R(0,i*9,W,9,'0',fc,0.55))

    # Head pequena (contexto)
    hc=opts.get('color_head',ac)
    h_fs,_,_ = render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h']*0.6,ml=sc['ml'],fw_='400',ls=3)
    parts.append(cur.output()); cur.parts=[]

    # Sub
    sc_=opts.get('color_sub',tc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s']*0.9,fw_='300',opacity=0.70)
    parts.append(cur.output()); cur.parts=[]
    cur.y += 16

    # Valor GIGANTE (o herói)
    p1,sv,p2=spv(c['valor'])
    avail=ct-cur.y-80
    vfs_hi=max(int(130*sc['v']),30); vfs_lo=max(int(28*sc['v']),26)
    vfs=min(fit(p1,sw(CW,fk,lang),hi=vfs_hi,lo=vfs_lo),fit(p2 if sv else p1,sw(CW,fk,lang),hi=vfs_hi,lo=vfs_lo))
    vc_=opts.get('color_val',ac)
    if sv:
        sf2=max(22,int(vfs*0.48)//2*2)
        yc=first_y(cur.y,fk,vfs)
        # p1 outline brutalista
        parts.append(f'<text x="{XL}" y="{yc}" font-family="{ff}" font-weight="900" font-size="{vfs}" fill="none" stroke="{tc}" stroke-width="1.5" opacity="0.45" letter-spacing="-2">{c["valor"].split(list(filter(lambda s: s in c["valor"],[" a "," to "," – "]))[0] if any(s in c["valor"] for s in [" a "," to "," – "]) else c["valor"])[0] if any(s in c["valor"] for s in [" a "," to "," – "]) else ""}</text>')
        parts.append(f'<text x="{XL}" y="{yc}" font-family="{ff}" font-weight="900" font-size="{vfs}" fill="none" stroke="{tc}" stroke-width="1.5" opacity="0.45" letter-spacing="-2">{p1}</text>')
        yc2=yc+gap_ab(fk,vfs,fk,sf2,12)
        parts.append(T(XL,yc2,sv,'100',sf2,tc,ff,op=0.55))
        yc3=yc2+gap_ab(fk,sf2,fk,vfs,16)
        parts.append(T(XL,yc3,p2,'900',vfs,vc_,ff,ls=-2,flt='glow'))
    else:
        yc=first_y(cur.y,fk,vfs)
        parts.append(T(XL,yc,p1,'900',vfs,vc_,ff,ls=-2,flt='glow'))
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# H — STRIPE TAPE  |  Poppins / Raleway
# Tendência: Maximalism com fitas coloridas atravessando o layout
# ══════════════════════════════════════════════════════════════════
def model_H(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','poppins')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    cur=LayoutCursor(top,ct,22)
    parts=[]
    thr=[int(ct*0.20),int(ct*0.45),int(ct*0.68)]
    th_h=max(60,int(ct*0.13))
    for ty,fc in zip(thr,flags[:3]):
        parts.append(R(-20,ty,W+40,th_h,'0',fc,0.18))
        parts.append(L(-20,ty,W+40,fc,2,0.50)); parts.append(L(-20,ty+th_h,W+40,fc,1,0.30))

    hc=opts.get('color_head',tc)
    render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='900')
    parts.append(cur.output()); cur.parts=[]
    sc_=opts.get('color_sub',tc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='300',opacity=0.78)
    parts.append(cur.output()); cur.parts=[]
    cur.y+=14

    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(CW,fk,lang),hi=max(int(88*sc['v']),22),lo=22),
            fit(p2 if sv else p1,sw(CW,fk,lang),hi=max(int(88*sc['v']),22),lo=22))
    val_th=int(cap(fk)*vfs)+int(desc(fk)*vfs)+28
    if sv: sf2=max(20,int(vfs*0.48)//2*2); val_th+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,16)
    parts.append(R(0,cur.y-8,W,val_th+16,'0',ac,0.14)); parts.append(L(0,cur.y-8,W,ac,3,0.60))
    vc_=opts.get('color_val',sac(ac,bg))
    pal_v={**pal,'a1':vc_}
    render_valor_block(cur,c['valor'],fk,ff,lang,bg,pal_v,scale=sc['v'])
    parts.append(cur.output())
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# I — HALF BLEED  |  Charter / Merriweather
# Tendência: Color blocking, premium editorial 2025
# ══════════════════════════════════════════════════════════════════
def model_I(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','charter')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    bh=int(ct*0.50); btc=atc(ac,'#FFFFFF','#0A0204')
    parts=[]
    parts.append(R(0,0,W,bh,'0',ac,1.0))
    n=len(flags[:3])
    for i,fc in enumerate(flags[:n]):
        parts.append(R(W-80,int(i*bh/n),80,int(bh/n),'0',fc,0.18))
    parts.append(L(0,bh,W,atc(ac),3,0.20)); parts.append(L(0,bh+3,W,ac,1,0.30))

    cur=LayoutCursor(top,bh-10,18)
    hc=opts.get('color_head',btc)
    render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='700')
    parts.append(cur.output()); cur.parts=[]
    sc_=opts.get('color_sub',btc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='400',opacity=0.80)
    parts.append(cur.output())

    low=bh+28; parts.append(L(XL,low-12,XL+120,ac,3,0.55))
    cur2=LayoutCursor(low,ct,20)
    vc_=opts.get('color_val',sac(ac,bg))
    pal_v={**pal,'a1':vc_}
    render_valor_block(cur2,c['valor'],fk,ff,lang,bg,pal_v,scale=sc['v'])
    parts.append(cur2.output()); cur2.parts=[]
    ltc=atc(bg,'#0A0204','#FFFFFF'); sc2_=opts.get('color_sub',ltc)
    render_sub_block(cur2,c['sub'],fk,ff,lang,sc2_,scale=sc['s']*0.85,fw_='400',opacity=0.78)
    parts.append(cur2.output())
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# J — CIRCULAR BADGE  |  Carlito / Ubuntu
# Tendência: Geometric branding, circle-dominant layout
# ══════════════════════════════════════════════════════════════════
def model_J(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','carlito')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    cr=int(min(W,ct-top)*0.42); ccx=CX; ccy=top+cr+20
    cbg=mix(bg,ac,0.12) if atc(bg)=='#FFFFFF' else mix(bg,ac,0.08)
    ctc=atc(cbg); cac=sac(ac,cbg); sf_c=sw(int(cr*1.6),fk,lang)
    parts=[]
    for i,fc in enumerate(flags[:3]):
        fh=int(ct/max(len(flags[:3]),1)); parts.append(Lv(W-14,i*fh,i*fh+fh,fc,14,0.45))
    parts.append(Ci(ccx,ccy,cr,cbg,1.0,ac,3))
    parts.append(Ci(ccx,ccy,cr-12,'none',1.0,mix(ac,bg,0.5),1))
    parts.append(Arc(ccx,ccy,cr+22,300,60,ac,sw_=6,op=0.30))
    parts.append(Arc(ccx,ccy,cr+22,120,240,flags[-1] if flags else ac,sw_=6,op=0.20))

    # Conteúdo dentro do círculo com cursor
    cur=LayoutCursor(ccy-cr+28,ccy+cr-20,10)
    sc_=opts.get('color_sub',ctc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s']*0.85,fw_='300',
                     opacity=0.68, x=ccx, anc='middle')
    parts.append(cur.output()); cur.parts=[]
    hc=opts.get('color_head',ctc)
    render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h']*0.85,ml=sc['ml'],
                     fw_='700', x=ccx, anc='middle')
    parts.append(cur.output()); cur.parts=[]
    vc_=opts.get('color_val',cac)
    pal_v={**pal,'a1':vc_}
    render_valor_block(cur,c['valor'],fk,ff,lang,cbg,pal_v,scale=sc['v']*0.85, x=ccx, anc='middle')
    parts.append(cur.output())

    # Sub externa
    ext_y=ccy+cr+36; ext_fs=max(int(22*sc['s']),16)
    if ext_y<ct-40:
        for i,ln in enumerate(wrap(c['sub'],ext_fs,sw(CW,fk,lang))):
            ey=first_y(ext_y+i*gap_s(fk,ext_fs,12),fk,ext_fs)
            if ey<ct-20: parts.append(T(CX,ey,ln,'300',ext_fs,tc,ff,'middle',op=0.62))
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# K — CONSTRUCTIVIST  |  Heros Cn
# Tendência: Geometric shapes as brand storytellers — Rodchenko 2025
# ══════════════════════════════════════════════════════════════════
def model_K(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','heros')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    zona_x=570; sf_l=sw(zona_x-XL-20,fk,lang)
    parts=[]
    cr=int(W*0.47); ccx=int(W*0.70); ccy=int(ct*0.38)
    parts.append(Ci(ccx,ccy,cr,ac,0.11)); parts.append(Ci(ccx,ccy,cr,'none',1.0,ac,2))
    parts.append(Ci(ccx,ccy,int(cr*0.60),'none',1.0,ac,0.40)); parts.append(Ci(ccx,ccy,14,ac,0.65))
    ts_=220; parts.append(Pg(f'{XL},{ct-ts_} {XL+ts_},{ct-ts_} {XL},{ct}',ac,0.18))
    for i,fc in enumerate(flags[:3]): parts.append(R(0,i*8,W,8,'0',fc,0.60))
    parts.append(f'<line x1="{XL}" y1="{int(ct*0.54)}" x2="{W}" y2="{int(ct*0.44)}" stroke="{ac}" stroke-width="3" opacity="0.18"/>')

    cur=LayoutCursor(top,ct,18)
    hc=opts.get('color_head',tc)
    render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='900')
    parts.append(cur.output()); cur.parts=[]

    # Faixa de valor
    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(CW-60,fk,lang),hi=max(int(78*sc['v']),20),lo=20),
            fit(p2 if sv else p1,sw(CW-60,fk,lang),hi=max(int(78*sc['v']),20),lo=20))
    fh=int(cap(fk)*vfs)+int(desc(fk)*vfs)+34
    if sv: sf2=max(20,int(vfs*0.48)//2*2); fh+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,14)
    y_f=min(cur.y+22,ct-fh-110)
    parts.append(R(0,y_f,W,fh,'0',ac,0.14)); parts.append(L(0,y_f,W,ac,3,0.65)); parts.append(L(0,y_f+fh,W,ac,1,0.30))
    tc_f=atc(mix(bg,ac,0.14)); ac_f=sac(ac,mix(bg,ac,0.14))
    vc_=opts.get('color_val',ac_f); pal_v={**pal,'a1':vc_}
    cur2=LayoutCursor(y_f,y_f+fh,6)
    render_valor_block(cur2,c['valor'],fk,ff,lang,mix(bg,ac,0.14),pal_v,scale=sc['v'])
    parts.append(cur2.output())
    # Sub abaixo
    cur3=LayoutCursor(y_f+fh+16,ct,14)
    sc_=opts.get('color_sub',tc)
    render_sub_block(cur3,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='300',opacity=0.72)
    parts.append(cur3.output())
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# L — BRUTALIST GRID  |  Liberation Sans
# Tendência: Anti-design grid, geometric cells 2025
# ══════════════════════════════════════════════════════════════════
def model_L(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','libsans')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    gcols=5; cw_=int(W/gcols); ch_=int(cw_*1.1)
    grows=int((ct-top)/ch_)+1
    parts=[]
    for ci in range(gcols+1): parts.append(Lv(ci*cw_,0,H,tc,0.5,0.12))
    for ri in range(grows+1):
        gy=top+ri*ch_
        if gy<H: parts.append(L(0,gy,W,tc,0.5,0.12))
    for ci,ri in [(0,0),(2,1),(4,2),(1,3),(3,4)]:
        fc=flags[(ci+ri)%len(flags)]
        if top+ri*ch_+ch_<ct: parts.append(R(ci*cw_,top+ri*ch_,cw_,ch_,'0',fc,0.22))

    cur=LayoutCursor(top+8,ct,16)
    hc=opts.get('color_head',tc)
    render_head_block(cur,c['head'],fk,ff,lang,hc,scale=sc['h'],ml=sc['ml'],fw_='900')
    parts.append(cur.output()); cur.parts=[]
    sc_=opts.get('color_sub',tc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s']*0.88,fw_='300',opacity=0.72)
    parts.append(cur.output()); cur.parts=[]

    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(CW,fk,lang),hi=max(int(82*sc['v']),22),lo=20),
            fit(p2 if sv else p1,sw(CW,fk,lang),hi=max(int(82*sc['v']),22),lo=20))
    vcel_h=int(cap(fk)*vfs)+int(desc(fk)*vfs)+40
    if sv: sf2=max(20,int(vfs*0.48)//2*2); vcel_h+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,14)
    y_vcel=min(cur.y+18,ct-vcel_h-110)
    parts.append(R(0,y_vcel,W,vcel_h,'0',ac,0.14)); parts.append(L(0,y_vcel,W,ac,3,0.60))
    vc_=opts.get('color_val',sac(ac,bg)); pal_v={**pal,'a1':vc_}
    cur2=LayoutCursor(y_vcel,y_vcel+vcel_h+4,4)
    render_valor_block(cur2,c['valor'],fk,ff,lang,bg,pal_v,scale=sc['v'])
    parts.append(cur2.output())
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# M — RETRO FUTURISM  |  Oswald / Poppins
# Tendência: Y2K revival, neon, scan lines, retro-futurism 2025
# ══════════════════════════════════════════════════════════════════
def model_M(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','oswald')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    neon=ac; neon2=mix(ac,'#FFFFFF',0.35) if atc(ac)=='#0A0204' else mix(ac,'#FFFFFF',0.20)
    parts=[]
    # Círculos neon de fundo (Y2K halo)
    for r_,op_ in [(400,0.04),(280,0.06),(180,0.09),(90,0.14)]:
        parts.append(Ci(CX,int(H*0.42),r_,neon,op_))
    # Scan lines
    for sy in range(0,H,8):
        parts.append(f'<line x1="0" y1="{sy}" x2="{W}" y2="{sy}" stroke="{neon}" stroke-width="0.4" opacity="0.04"/>')

    cur=LayoutCursor(top,ct,22)
    hc=opts.get('color_head',tc)
    # H1 com bloco de destaque
    h1_fs=max(int(42*sc['h']),22)
    h1_lines=wrap(c['head'],h1_fs,sw(CW,fk,lang))
    y=first_y(top,fk,h1_fs)
    h1_w=min(int(ew(h1_lines[0],h1_fs)*1.1)+40,CW)
    parts.append(R(XL-8,y-int(cap(fk)*h1_fs)-6,h1_w,int(cap(fk)*h1_fs)+int(desc(fk)*h1_fs)+14,'4',neon,0.20))
    for i,ln in enumerate(h1_lines[:2]):
        y_ln=y+i*gap_s(fk,h1_fs,14)
        if y_ln<ct-10: parts.append(T(XL,y_ln,ln,'700',h1_fs,neon,ff,ls=1))
    cur.y=bottom_of(y+(min(len(h1_lines),2)-1)*gap_s(fk,h1_fs,14),fk,h1_fs)+20
    parts.append(cur.output()); cur.parts=[]

    sc_=opts.get('color_sub',tc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='300',opacity=0.78)
    parts.append(cur.output()); cur.parts=[]

    # Valor com duplo neon
    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(CW,fk,lang),hi=max(int(90*sc['v']),22),lo=22),
            fit(p2 if sv else p1,sw(CW,fk,lang),hi=max(int(90*sc['v']),22),lo=22))
    vc_=opts.get('color_val',neon2)
    yc=first_y(cur.y,fk,vfs)
    if sv:
        sf2=max(22,int(vfs*0.50)//2*2)
        parts.append(T(XL,yc,p1,'900',vfs,tc,ff,ls=-1,op=0.65))
        yc+=gap_ab(fk,vfs,fk,sf2,12)
        parts.append(T(XL,yc,sv,'300',sf2,tc,ff,op=0.55))
        yc+=gap_ab(fk,sf2,fk,vfs,16)
        parts.append(T(XL,yc,p2,'900',vfs,neon,ff,ls=-2,flt='glowLg',op=0.40))
        parts.append(T(XL,yc,p2,'900',vfs,vc_,ff,ls=-2,flt='glow'))
    else:
        parts.append(T(XL,yc,p1,'900',vfs,neon,ff,ls=-2,flt='glowLg',op=0.40))
        parts.append(T(XL,yc,p1,'900',vfs,vc_,ff,ls=-2,flt='glow'))
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ══════════════════════════════════════════════════════════════════
# N — EDITORIAL MAGAZINE  |  Playfair / Merriweather
# Tendência: Serif revival, magazine editorial premium 2025
# Layout: drop cap, regra tripla, tipografia como composição
# ══════════════════════════════════════════════════════════════════
def model_N(c, is9, pal, country='US', opts=None):
    opts=opts or {}; fk=opts.get('font_head','playfair')
    lang, ff, bg, ac, tc, W, H, top, ct, sc = _setup(c,is9,pal,country,fk)
    flags=pal['flags']
    parts=[]
    # Linhas triplas editoriais no topo
    for off,op_ in [(28,0.22),(38,0.14),(46,0.08)]:
        parts.append(L(off,off,W-off,tc,1.5,op_))
        parts.append(L(off,H-off,W-off,tc,1.5,op_))
        parts.append(Lv(off,off,H-off,tc,1.5,op_))
        parts.append(Lv(W-off,off,H-off,tc,1.5,op_))
    # Faixas bandeira no topo como régua
    for i,fc in enumerate(flags[:3]): parts.append(R(0,46+i*7,W,7,'0',fc,0.65))

    cur=LayoutCursor(top,ct,20)
    # Número de edição estilizado
    issue_fs=13
    parts.append(T(XL,cur.y+issue_fs,'EDIÇÃO ESPECIAL  ·  CRÉDITO DISPONÍVEL','400',issue_fs,ac,ff,ls=3,op=0.60))
    cur.y+=issue_fs+14
    parts.append(L(XL,cur.y,XR,tc,0.5,0.20)); cur.y+=16

    hc=opts.get('color_head',tc)
    # Headline com drop-cap (primeira letra maior)
    h_hi=max(int(80*sc['h']),26)
    h_fs,h_lines=fw([c['head']],sw(CW,fk,lang),fk,lang,hi=h_hi,lo=22,ml=sc['ml'])
    y=first_y(cur.y,fk,h_fs); g2=gap_s(fk,h_fs,16)
    for i,ln in enumerate(h_lines):
        parts.append(T(CX,y+i*g2,ln,'700',h_fs,hc,ff,'middle',ls=1))
    cur.y=bottom_of(y+(len(h_lines)-1)*g2,fk,h_fs)+16

    # Separador ornamentado
    parts.append(L(CX-200,cur.y,CX-20,ac,1,0.40))
    parts.append(Ci(CX,cur.y,10,ac,0.25)); parts.append(Ci(CX,cur.y,5,ac,0.55))
    parts.append(L(CX+20,cur.y,CX+200,ac,1,0.40)); cur.y+=28

    sc_=opts.get('color_sub',tc)
    render_sub_block(cur,c['sub'],fk,ff,lang,sc_,scale=sc['s'],fw_='400',opacity=0.75, anc='middle', x=CX)
    parts.append(cur.output()); cur.parts=[]

    # Valor em caixa editorial
    p1,sv,p2=spv(c['valor'])
    vfs=min(fit(p1,sw(CW-80,fk,lang),hi=max(int(88*sc['v']),22),lo=22),
            fit(p2 if sv else p1,sw(CW-80,fk,lang),hi=max(int(88*sc['v']),22),lo=22))
    vpad=24; vbh=int(cap(fk)*vfs)+int(desc(fk)*vfs)+2*vpad
    if sv: sf2=max(20,int(vfs*0.48)//2*2); vbh+=gap_ab(fk,vfs,fk,sf2,12)+gap_ab(fk,sf2,fk,vfs,16)
    yvb=min(cur.y+12,ct-vbh-100)
    parts.append(R(XL,yvb,CW,vbh,'0',ac,0.10)); parts.append(f'<rect x="{XL}" y="{yvb}" width="{CW}" height="{vbh}" rx="0" fill="none" stroke="{ac}" stroke-width="1" opacity="0.45"/>')
    parts.append(f'<rect x="{XL}" y="{yvb}" width="{CW}" height="3" fill="{ac}" fill-opacity="0.90"/>')
    vc_=opts.get('color_val',sac(ac,mix(bg,ac,0.10)))
    yc=yvb+vpad+int(cap(fk)*vfs)
    if sv:
        sf2=max(20,int(vfs*0.48)//2*2)
        parts.append(T(CX,yc,p1,'700',vfs,atc(mix(bg,ac,0.10)),ff,'middle',ls=-1,op=0.68)); yc+=gap_ab(fk,vfs,fk,sf2,12)
        parts.append(T(CX,yc,sv,'300',sf2,atc(mix(bg,ac,0.10)),ff,'middle',op=0.52)); yc+=gap_ab(fk,sf2,fk,vfs,16)
        parts.append(T(CX,yc,p2,'700',vfs,vc_,ff,'middle',ls=-2,flt='glow'))
    else: parts.append(T(CX,yc,p1,'700',vfs,vc_,ff,'middle',ls=-2,flt='glow'))
    return svg_wrap(W,H,bg,'\n'.join(parts)+'\n'+CTA(c,pal,is9,ff,fk,lang,bg)+'\n'+DISC(c,pal,is9,ff,fk,lang,bg))


# ── Mapa de modelos ──────────────────────────────────────────────
MODEL_MAP = {
    'A':'Stacked Manifesto', 'B':'Arc Gauge', 'C':'Diagonal Clash',
    'D':'Terminal Stream',   'E':'Float Card', 'F':'National Frame',
    'G':'Oversized Type',    'H':'Stripe Tape','I':'Half Bleed',
    'J':'Circular Badge',    'K':'Constructivist','L':'Brutalist Grid',
    'M':'Retro Futurism',    'N':'Editorial Magazine',
}

MODEL_FONTS = {  # fonte padrão de cada modelo
    'A':'poppins','B':'libsans','C':'lora','D':'carlito',
    'E':'lora',   'F':'charter','G':'heros','H':'poppins',
    'I':'charter','J':'carlito','K':'heros','L':'libsans',
    'M':'oswald', 'N':'playfair',
}

_MODEL_FNS = {
    'A':model_A,'B':model_B,'C':model_C,'D':model_D,
    'E':model_E,'F':model_F,'G':model_G,'H':model_H,
    'I':model_I,'J':model_J,'K':model_K,'L':model_L,
    'M':model_M,'N':model_N,
}


def generate_svg(country_code, copy_data, model_key, format_key, opts=None):
    from engine.countries import get_palette
    pal = get_palette(country_code)
    if copy_data.get('cta'): pal['cta'] = copy_data['cta']
    c = {
        'head':       copy_data['head'],
        'sub':        copy_data['sub'],
        'valor':      copy_data['valor'],
        'disclaimer': copy_data['disclaimer'],
        'lang':       copy_data.get('lang', pal['lang']),
        'cta':        pal['cta'],
    }
    # Aplicar fonte padrão do modelo se não vier nos opts
    if opts and not opts.get('font_head'):
        opts['font_head'] = MODEL_FONTS.get(model_key.upper(), 'poppins')
    is9 = (format_key == '916')
    fn  = _MODEL_FNS.get(model_key.upper(), model_A)
    return fn(c, is9, pal, country=country_code, opts=opts or {})
