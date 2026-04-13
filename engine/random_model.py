#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio4 — Random Document Generator
Gera DocumentState (lista de blocos) 100% aleatórios, compatíveis com BlockRenderer.
Seed determinística: mesma seed = mesmo documento.
"""
import math, random, hashlib
from engine.core import (
    XL, XR, CX, CW, FONTS, FONT_LABELS,
    lum, ctr, atc, sac, mix,
    wrap, fit, ew, sw, gf, gr, tsc,
    gap_ab, gap_s, first_y, bottom_of,
    T, R, L, Lv, Ci, Pg, Arc, DEFS,
    cap, desc, spv, esc
)

W45,H45=1080,1350; W916,H916=1080,1920  # 4:5 e 9:16
TOP45,CT45=84,1110; TOP916,CT916=280,1440

FONT_PAIRS=[
    ('poppins','poppins'),('poppins','lora'),('heros','poppins'),
    ('heros','libsans'),('oswald','libsans'),('oswald','carlito'),
    ('playfair','lora'),('playfair','merriweather'),('raleway','libsans'),
    ('charter','merriweather'),('charter','lora'),('carlito','poppins'),
    ('libsans','libserif'),('merriweather','poppins'),('ubuntu','ubuntu'),
    ('libserif','charter'),
]

PALETTES={
    'vibrante':[
        {'bg':'#0A0A14','ac':'#FF3B8B','ac2':'#FF8A3B','tc':'#FFFFFF'},
        {'bg':'#0D0D1A','ac':'#00D4FF','ac2':'#A855F7','tc':'#FFFFFF'},
        {'bg':'#050F1A','ac':'#00FF88','ac2':'#00D4FF','tc':'#FFFFFF'},
        {'bg':'#1A0A14','ac':'#FF3B5C','ac2':'#FFB800','tc':'#FFFFFF'},
        {'bg':'#0A0A0A','ac':'#FFCC00','ac2':'#FF6B00','tc':'#FFFFFF'},
        {'bg':'#0A1428','ac':'#4DFFB4','ac2':'#4D9FFF','tc':'#FFFFFF'},
        {'bg':'#14000A','ac':'#FF0055','ac2':'#FF6600','tc':'#FFFFFF'},
        {'bg':'#001428','ac':'#00C8FF','ac2':'#0055FF','tc':'#FFFFFF'},
        {'bg':'#1E0A28','ac':'#CC44FF','ac2':'#FF44AA','tc':'#FFFFFF'},
        {'bg':'#0A0514','ac':'#7B4DFF','ac2':'#FF4DB8','tc':'#FFFFFF'},
        {'bg':'#140A00','ac':'#FF9500','ac2':'#FF3B00','tc':'#FFFFFF'},
        {'bg':'#001E14','ac':'#00FF66','ac2':'#FFD700','tc':'#FFFFFF'},
    ],
    'minimalista':[
        {'bg':'#FAFAFA','ac':'#0A0A0A','ac2':'#555555','tc':'#0A0A0A'},
        {'bg':'#F5F5F5','ac':'#1A1A2E','ac2':'#666666','tc':'#1A1A2E'},
        {'bg':'#0A0A0A','ac':'#FFFFFF','ac2':'#AAAAAA','tc':'#FFFFFF'},
        {'bg':'#141414','ac':'#EEEEEE','ac2':'#888888','tc':'#EEEEEE'},
        {'bg':'#F0F8FF','ac':'#001233','ac2':'#334455','tc':'#001233'},
        {'bg':'#1A1A1A','ac':'#F5F5F5','ac2':'#AAAAAA','tc':'#F5F5F5'},
        {'bg':'#F8F4F0','ac':'#2C1A0E','ac2':'#8B6B4A','tc':'#2C1A0E'},
        {'bg':'#080808','ac':'#F0F0F0','ac2':'#707070','tc':'#F0F0F0'},
        {'bg':'#F2F2F2','ac':'#C0392B','ac2':'#333333','tc':'#111111'},
        {'bg':'#111827','ac':'#F9FAFB','ac2':'#9CA3AF','tc':'#F9FAFB'},
    ],
    'neutro':[
        {'bg':'#1C1410','ac':'#D4A96A','ac2':'#A07850','tc':'#F0E8D8'},
        {'bg':'#0E1A14','ac':'#6BC28A','ac2':'#3A8A5A','tc':'#D8F0E0'},
        {'bg':'#141420','ac':'#8888FF','ac2':'#5555CC','tc':'#E8E8FF'},
        {'bg':'#1A1010','ac':'#CC6666','ac2':'#993333','tc':'#FFE8E8'},
        {'bg':'#101818','ac':'#44AAAA','ac2':'#226666','tc':'#E0FFFF'},
        {'bg':'#F5F0E8','ac':'#8B6914','ac2':'#C09428','tc':'#1A1400'},
        {'bg':'#EEF2EC','ac':'#2D5A1B','ac2':'#4A8A30','tc':'#0A1A06'},
        {'bg':'#F0EEF5','ac':'#3D1A7A','ac2':'#6A3ABB','tc':'#0A0028'},
        {'bg':'#1A1620','ac':'#9966CC','ac2':'#CC99FF','tc':'#F0E8FF'},
        {'bg':'#181818','ac':'#D4A017','ac2':'#AA7C00','tc':'#FFF8E0'},
    ],
}

LAYOUTS=[
    'stacked_left','centered_editorial','split_diagonal','oversized_value',
    'frame_national','circle_badge','stripe_tape','terminal_data',
    'editorial_serif','half_bleed','constructivist','brutalist_grid',
    'neon_retro','magazine_full',
]

LAYOUT_ALIGN={
    'stacked_left':'left','centered_editorial':'center','split_diagonal':'left',
    'oversized_value':'left','frame_national':'center','circle_badge':'center',
    'stripe_tape':'left','terminal_data':'left','editorial_serif':'center',
    'half_bleed':'left','constructivist':'left','brutalist_grid':'left',
    'neon_retro':'left','magazine_full':'center',
}

def _seed_rng(seed):
    h=int(hashlib.md5(str(seed).encode()).hexdigest(),16)
    return random.Random(h)

def _uid(rng):
    return f"b{rng.randint(10000,99999)}"

def _safe_ctr(fg,bg,rng,alts,min_r=4.5):
    if ctr(fg,bg)>=min_r: return fg
    for a in alts:
        if ctr(a,bg)>=min_r: return a
    return atc(bg)

def _pick_palette(mode,rng):
    if mode=='auto': mode=rng.choice(['vibrante','minimalista','neutro'])
    pool=PALETTES.get(mode,PALETTES['neutro'])
    return dict(rng.choice(pool))

def _make_decor(layout,pal,is9,rng):
    W=W916 if is9 else W45; H=H916 if is9 else H45
    top=TOP916 if is9 else TOP45; ct=CT916 if is9 else CT45
    bg=pal['bg']; ac=pal['ac']; ac2=pal['ac2']; tc=pal['tc']
    p=[]
    if layout=='stacked_left':
        for i,fc in enumerate([ac,ac2,mix(ac,ac2,0.5)]):
            p.append(R(i*8,0,8,ct,'0',fc,0.55))
        d1=int(H*0.44); d2=int(H*0.48)
        p.append(f'<polygon points="0,{d1} {W},{d2-15} {W},{d2} 0,{d1+15}" fill="{ac}" opacity="0.07"/>')
    elif layout=='centered_editorial':
        for y in range(top,ct,int((ct-top)/5)):
            p.append(L(XL,y,XR,tc,0.5,0.06))
        p.append(Ci(CX,int((top+ct)/2),int(CW*0.38),ac,0.05))
        p.append(Ci(CX,int((top+ct)/2),int(CW*0.38),'none',1.0,ac,0.5))
    elif layout=='split_diagonal':
        ct2=int(ct*0.45); cb=int(ct*0.54)
        lbg=mix(ac,'#FFFFFF',0.88) if lum(ac)<0.5 else mix(ac,'#F8F8F8',0.25)
        if lum(lbg)<0.40: lbg='#F5F5F0'
        p.append(R(0,0,W,H,'0',lbg,1.0))
        p.append(f'<polygon points="0,0 {W},0 {W},{ct2} 0,{cb}" fill="{bg}"/>')
        for i,fc in enumerate([ac,ac2]): p.append(R(0,i*int(cb/2),10,int(cb/2),'0',fc,0.50))
        pal['_lbg']=lbg
    elif layout=='oversized_value':
        for xi in range(XL,XR,56):
            for yi in range(top,ct,56): p.append(Ci(xi,yi,1.5,tc,0.07))
        for i,fc in enumerate([ac,ac2,mix(ac,ac2,0.5)]): p.append(R(0,i*9,W,9,'0',fc,0.55))
    elif layout=='frame_national':
        fr=52
        pid3=f'dia{abs(hash(str(tc)))%9999}'
        p.append(f'<defs><pattern id="{pid3}" x="0" y="0" width="80" height="80" patternUnits="userSpaceOnUse"><polygon points="0,40 40,0 80,40 40,80" fill="{tc}" opacity="0.5"/></pattern></defs>')
        p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#{pid3})" opacity="0.07"/>')
        for i,fc in enumerate([ac,ac2,mix(ac,ac2,0.5)]):
            seg=int(W/3)
            p.append(R(i*seg,0,seg,fr,'0',fc,0.70)); p.append(R(i*seg,H-fr,seg,fr,'0',fc,0.70))
            p.append(R(0,fr+i*int((H-2*fr)/3),fr,int((H-2*fr)/3),'0',fc,0.70))
            p.append(R(W-fr,fr+i*int((H-2*fr)/3),fr,int((H-2*fr)/3),'0',fc,0.70))
        p.append(f'<rect x="{fr}" y="{fr}" width="{W-2*fr}" height="{H-2*fr}" rx="0" fill="none" stroke="{tc}" stroke-width="1.5" opacity="0.16"/>')
        for rx_,ry_ in [(50,50),(W-50,50),(50,H-50),(W-50,H-50)]:
            p.append(f'<line x1="{rx_-16}" y1="{ry_}" x2="{rx_+16}" y2="{ry_}" stroke="{ac}" stroke-width="1" opacity="0.30"/>')
            p.append(f'<line x1="{rx_}" y1="{ry_-16}" x2="{rx_}" y2="{ry_+16}" stroke="{ac}" stroke-width="1" opacity="0.30"/>')
    elif layout=='circle_badge':
        cr=int(min(W,ct-top)*0.42); ccx=CX; ccy=top+cr+20
        cbg=mix(bg,ac,0.12)
        p.append(Ci(ccx,ccy,cr,cbg,1.0,ac,3)); p.append(Ci(ccx,ccy,cr-12,'none',1.0,mix(ac,bg,0.5),1))
        p.append(Arc(ccx,ccy,cr+22,300,60,ac,sw_=6,op=0.30))
        p.append(Arc(ccx,ccy,cr+22,120,240,ac2,sw_=6,op=0.22))
        for i,fc in enumerate([ac,ac2,mix(ac,ac2,0.5)]):
            fh_=int(ct/3); p.append(Lv(W-14,i*fh_,i*fh_+fh_,fc,14,0.45))
    elif layout=='stripe_tape':
        thr=[int(ct*0.20),int(ct*0.45),int(ct*0.68)]; th_h=max(60,int(ct*0.13))
        for ty,fc in zip(thr,[ac,ac2,mix(ac,ac2,0.5)]):
            p.append(R(-20,ty,W+40,th_h,'0',fc,0.18))
            p.append(L(-20,ty,W+40,fc,2,0.50)); p.append(L(-20,ty+th_h,W+40,fc,1,0.28))
    elif layout=='terminal_data':
        pid=f'scan{abs(hash(str(ac)))%9999}'
        p.append(f'<defs><pattern id="{pid}" x="0" y="0" width="1" height="6" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="1" y2="0" stroke="{ac}" stroke-width="0.5" opacity="0.4"/></pattern></defs>')
        p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#{pid})" opacity="0.08"/>')
        ty2=top-50
        p.append(R(0,ty2-8,W,38,'0',ac,0.08)); p.append(L(0,ty2-8,W,ac,0.5,0.40))
        for j,item in enumerate(['STATUS:OK','RISK:LOW','RATE:0.99%']):
            p.append(T(XL+j*240,ty2+14,item,'400',16,ac,gf('carlito','en'),ls=1,op=0.65))
    elif layout=='editorial_serif':
        for off,op_ in [(28,0.18),(38,0.10),(46,0.06)]:
            p.append(L(off,off,W-off,tc,1.5,op_)); p.append(L(off,H-off,W-off,tc,1.5,op_))
            p.append(Lv(off,off,H-off,tc,1.5,op_)); p.append(Lv(W-off,off,H-off,tc,1.5,op_))
        for i,fc in enumerate([ac,ac2,mix(ac,ac2,0.5)]): p.append(R(0,46+i*7,W,7,'0',fc,0.65))
    elif layout=='half_bleed':
        bh=int(ct*0.50)
        p.append(R(0,0,W,bh,'0',ac,1.0))
        for i in range(3):
            fc=mix(ac,'#FFFFFF',(i+1)*0.15) if lum(ac)<0.5 else mix(ac,'#000000',(i+1)*0.12)
            p.append(R(W-80,int(i*bh/3),80,int(bh/3),'0',fc,0.18))
        p.append(L(0,bh,W,atc(ac),3,0.20))
    elif layout=='constructivist':
        cr=int(W*0.47); ccx=int(W*0.70); ccy=int(ct*0.38)
        p.append(Ci(ccx,ccy,cr,ac,0.11)); p.append(Ci(ccx,ccy,cr,'none',1.0,ac,2))
        p.append(Ci(ccx,ccy,int(cr*0.60),'none',1.0,ac,0.40)); p.append(Ci(ccx,ccy,14,ac,0.65))
        ts=220; p.append(Pg(f'{XL},{ct-ts} {XL+ts},{ct-ts} {XL},{ct}',ac,0.18))
        p.append(f'<line x1="{XL}" y1="{int(ct*0.54)}" x2="{W}" y2="{int(ct*0.44)}" stroke="{ac}" stroke-width="3" opacity="0.18"/>')
    elif layout=='brutalist_grid':
        gcols=5; cw_=int(W/gcols); ch_=int(cw_*1.1); grows=int((ct-top)/ch_)+1
        for ci in range(gcols+1): p.append(Lv(ci*cw_,0,H,tc,0.5,0.11))
        for ri in range(grows+1):
            gy=top+ri*ch_
            if gy<H: p.append(L(0,gy,W,tc,0.5,0.11))
        for ci,ri in [(0,0),(2,1),(4,2),(1,3),(3,4)]:
            fc=[ac,ac2,mix(ac,ac2,0.5)][(ci+ri)%3]
            if top+ri*ch_+ch_<ct: p.append(R(ci*cw_,top+ri*ch_,cw_,ch_,'0',fc,0.22))
    elif layout=='neon_retro':
        for r_,op_ in [(420,0.04),(300,0.06),(200,0.08),(110,0.12),(50,0.18)]:
            p.append(Ci(CX,int(H*0.42),r_,ac,op_))
        pid2=f'scan2{abs(hash(str(ac)))%9999}'
        p.append(f'<defs><pattern id="{pid2}" x="0" y="0" width="1" height="8" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="1" y2="0" stroke="{ac}" stroke-width="0.4" opacity="0.5"/></pattern></defs>')
        p.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#{pid2})" opacity="0.08"/>')
        p.append(R(XL-8,top-6,int(W*0.65),int(ct*0.12),'4',ac,0.18))
    elif layout=='magazine_full':
        pad=30
        p.append(f'<rect x="{pad}" y="{pad}" width="{W-2*pad}" height="{H-2*pad}" rx="0" fill="none" stroke="{tc}" stroke-width="1" opacity="0.15"/>')
        p.append(f'<rect x="{pad+8}" y="{pad+8}" width="{W-2*(pad+8)}" height="{H-2*(pad+8)}" rx="0" fill="none" stroke="{ac}" stroke-width="0.5" opacity="0.25"/>')
        p.append(Ci(CX,int(ct*0.68),180,ac,0.07))
        p.append(Ci(CX,int(ct*0.68),180,'none',1.0,ac,1.0))
    return '\n'.join(p)

def _make_blocks(copy,layout,pal,font_h,font_b,country,rng):
    sc=tsc(country)
    bg=pal.get('_lbg',pal['bg']); ac=pal['ac']; ac2=pal['ac2']; tc=pal['tc']
    align=LAYOUT_ALIGN.get(layout,'left')
    t_main=_safe_ctr(tc,pal['bg'],rng,[ac,'#FFFFFF','#0A0204'])
    t_sec=mix(t_main,pal['bg'],0.20)
    if ctr(t_sec,pal['bg'])<3.0: t_sec=t_main
    v_col=_safe_ctr(ac,pal['bg'],rng,[ac2,t_main,'#FFDF00'])
    s_col=_safe_ctr(mix(t_main,pal['bg'],0.15),pal['bg'],rng,[t_sec,t_main])
    # Tamanhos por layout
    hl=((55,70) if layout=='oversized_value' else (70,90) if layout=='circle_badge'
        else (80,105) if layout in('half_bleed','frame_national') else (85,110) if layout in('editorial_serif','magazine_full')
        else (60,80) if layout in('neon_retro','terminal_data') else (80,115))
    hp=int(rng.randrange(hl[0],hl[1]+1,5)*sc['h'])
    vl=((130,155) if layout=='oversized_value' else (100,130) if layout=='neon_retro' else (90,115))
    vp=int(rng.randrange(vl[0],vl[1]+1,5)*sc['v'])
    sp=int(rng.randrange(85,115,5)*sc['s'])
    hw=rng.choice(['900','800','700']); sw2=rng.choice(['300','400'])
    hls=rng.choice([-2,-1,-1,0,1]); sls=rng.choice([-1,0,1,2])
    vflt='glow' if lum(pal['bg'])<0.30 else ''

    def B(bt,text,font,size,color,**kw):
        return {'id':_uid(rng),'type':bt,'text':text,'font':font,'size':size,'color':color,
                'align':kw.get('align',align),'weight':kw.get('weight',''),
                'ls':kw.get('ls',0),'opacity':kw.get('opacity',1.0),
                'visible':kw.get('visible',True),'y_offset':kw.get('y_offset',0),'flt':kw.get('flt','')}

    hcol=atc(ac,'#FFFFFF','#0A0204') if layout=='half_bleed' else t_main
    scol=mix(hcol,pal['bg'],0.20) if ctr(mix(hcol,pal['bg'],0.20),pal['bg'])>=3.0 else t_sec
    blocks=[]
    if layout=='circle_badge':
        blocks+=[B('subhead',copy['sub'],font_b,sp,scol,weight=sw2,ls=sls,opacity=0.68,align='center'),
                 B('headline',copy['head'],font_h,hp,hcol,weight=hw,ls=hls,align='center'),
                 B('value',copy['valor'],font_h,vp,v_col,weight='900',ls=-2,flt=vflt,align='center')]
    elif layout in('editorial_serif','magazine_full'):
        blocks+=[B('subhead','EDIÇÃO ESPECIAL · CRÉDITO',font_b,int(sp*0.5),mix(t_main,pal['bg'],0.30),
                   weight='400',ls=3,opacity=0.60,align='center'),
                 B('divider','',font_b,60,t_main,align='center',opacity=0.25),
                 B('headline',copy['head'],font_h,hp,hcol,weight=hw,ls=hls,align='center'),
                 B('subhead',copy['sub'],font_b,sp,scol,weight=sw2,ls=sls,opacity=0.75,align='center'),
                 B('value',copy['valor'],font_h,vp,v_col,weight='900',ls=-2,flt=vflt,align='center')]
    elif layout=='split_diagonal':
        lbg=pal.get('_lbg','#F5F5F0')
        vc_l=_safe_ctr(ac,lbg,rng,[ac2,'#000000'])
        blocks+=[B('headline',copy['head'],font_h,hp,t_main,weight=hw,ls=hls),
                 B('subhead',copy['sub'],font_b,sp,t_sec,weight=sw2,ls=sls,opacity=0.78),
                 B('value',copy['valor'],font_h,vp,vc_l,weight='900',ls=-2)]
    elif layout=='terminal_data':
        blocks+=[B('headline',copy['head'],'carlito',hp,t_main,weight='700'),
                 B('subhead','// '+copy['sub'],'carlito',sp,mix(ac,pal['bg'],0.45),weight='300',opacity=0.75),
                 B('value',copy['valor'],'carlito',vp,ac,weight='900',ls=-2,flt=vflt or 'glowSm')]
    elif layout=='oversized_value':
        blocks+=[B('headline',copy['head'],font_h,hp,hcol,weight='400',ls=2,opacity=0.85),
                 B('subhead',copy['sub'],font_b,sp,scol,weight=sw2,opacity=0.70),
                 B('value',copy['valor'],font_h,vp,v_col,weight='900',ls=-2,flt=vflt)]
    else:
        blocks+=[B('headline',copy['head'],font_h,hp,hcol,weight=hw,ls=hls),
                 B('subhead',copy['sub'],font_b,sp,scol,weight=sw2,ls=sls,opacity=0.78),
                 B('value',copy['valor'],font_h,vp,v_col,weight='900',ls=-2,flt=vflt)]
    dc=_safe_ctr(mix(t_main,pal['bg'],0.35),pal['bg'],rng,[mix(t_main,pal['bg'],0.20),t_main])
    blocks.append(B('disclaimer',copy['disclaimer'],font_b,100,dc,weight='400',opacity=0.72,align=align))
    return blocks

def generate_random_doc(copy_data,palette_mode='auto',layout_hint=None,
                        seed='',country='BR',fmt='45',variation_index=0):
    """Gera doc com bg_svg para AMBOS os formatos (4:5 e 9:16)."""
    base_seed = seed or f"r_{country}_{variation_index}"
    rng = _seed_rng(base_seed)
    pal = _pick_palette(palette_mode, rng)
    layout = layout_hint if layout_hint in LAYOUTS else rng.choice(LAYOUTS)
    font_h, font_b = rng.choice(FONT_PAIRS)
    # Gerar decoracao para cada formato com rngs independentes mas mesmo estado inicial
    rng_34  = _seed_rng(base_seed + '_45')
    rng_916 = _seed_rng(base_seed + '_916')
    bg_svg_45  = _make_decor(layout, pal, False, rng_34)
    bg_svg_916 = _make_decor(layout, pal, True,  rng_916)
    blocks = _make_blocks(copy_data, layout, pal, font_h, font_b, country, rng)
    bg = pal['bg']
    cta_col = _safe_ctr(pal['tc'], bg, rng, ['#FFFFFF','#0A0204'])
    ac_col  = _safe_ctr(pal['ac'], bg, rng, [pal['ac2'], cta_col])
    return {
        'country':country, 'lang':'pt-BR',
        'bg':bg, 'bg_image':None, 'bg_effect':None, 'bg_opacity':1.0,
        'bg_svg': bg_svg_45,        # default = 34; renderer troca por bg_svg_916 quando fmt=916
        'bg_svg_45':  bg_svg_45,
        'bg_svg_916': bg_svg_916,
        'blocks': blocks,
        'cta_text':  copy_data.get('cta','SIMULAR AGORA'),
        'cta_color': cta_col, 'ac_color': ac_col,
        'disc_text': '', 'disc_color': '#AAAAAA',
        '_layout':layout, '_palette_mode':palette_mode,
        '_palette': {k:v for k,v in pal.items() if not k.startswith('_')},
        '_font_h':font_h, '_font_b':font_b, '_seed':seed,
    }

def generate_batch(copy_data,count,palette_mode='auto',country='BR',fmt='45',seed_prefix='batch'):
    docs=[]; lpool=LAYOUTS[:]; pmodes=['vibrante','minimalista','neutro']*math.ceil(count/3)
    for i in range(count):
        if not lpool: lpool=LAYOUTS[:]
        layout=lpool.pop(i%len(lpool))
        pm=pmodes[i] if palette_mode=='auto' else palette_mode
        docs.append(generate_random_doc(
            copy_data=copy_data,palette_mode=pm,layout_hint=layout,
            seed=f"{seed_prefix}_{i}_{layout}_{pm}",
            country=country,fmt=fmt,variation_index=i))
    return docs
