#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio3 Engine — Core
Sistema de layout com anti-colisão: nenhum texto ultrapassa outro.
Física precisa: gap_ab, first_y, render ratio, fit, wrap.
"""
import math

XL, XR, CX = 130, 950, 540
CW = XR - XL  # 820

# ── Fontes disponíveis ────────────────────────────────────────────
FONTS = {
    'poppins':    {'cap':0.980,'desc':0.255,'r':1.264,'f':'Poppins,sans-serif'},
    'lora':       {'cap':0.960,'desc':0.256,'r':1.331,'f':'Lora,serif'},
    'heros':      {'cap':0.919,'desc':0.205,'r':1.097,'f':"'TeX Gyre Heros Cn','Arial Narrow',sans-serif"},
    'carlito':    {'cap':0.845,'desc':0.154,'r':1.083,'f':"Carlito,'Trebuchet MS',sans-serif"},
    'charter':    {'cap':0.932,'desc':0.205,'r':1.268,'f':"'Bitstream Charter',Georgia,serif"},
    'libsans':    {'cap':0.890,'desc':0.190,'r':1.296,'f':"'Liberation Sans',Arial,sans-serif"},
    'libserif':   {'cap':0.920,'desc':0.210,'r':1.280,'f':"'Liberation Serif','Times New Roman',serif"},
    'ubuntu':     {'cap':0.910,'desc':0.200,'r':1.230,'f':"Ubuntu,'Trebuchet MS',sans-serif"},
    'oswald':     {'cap':0.950,'desc':0.220,'r':1.180,'f':"Oswald,'Arial Narrow',sans-serif"},
    'playfair':   {'cap':0.940,'desc':0.240,'r':1.350,'f':"'Playfair Display',Georgia,serif"},
    'raleway':    {'cap':0.900,'desc':0.200,'r':1.250,'f':"Raleway,'Trebuchet MS',sans-serif"},
    'merriweather':{'cap':0.930,'desc':0.230,'r':1.320,'f':"Merriweather,Georgia,serif"},
}

FONT_LABELS = {
    'poppins':    'Poppins',
    'lora':       'Lora',
    'heros':      'Heros Cn',
    'carlito':    'Carlito',
    'charter':    'Charter',
    'libsans':    'Lib. Sans',
    'libserif':   'Lib. Serif',
    'ubuntu':     'Ubuntu',
    'oswald':     'Oswald',
    'playfair':   'Playfair',
    'raleway':    'Raleway',
    'merriweather': 'Merriweather',
}

EW = {'d':0.52,'n':0.30,'w':0.68,'g':0.52,'sp':0.25,
      'th':0.58,'cj':0.95,'sy':0.60,'gr':0.52}

# ── Escala tipográfica por país ──────────────────────────────────
TYPE_SCALE = {
    'JP': {'h':0.72,'s':0.78,'v':0.88,'ml':4},
    'KR': {'h':0.74,'s':0.80,'v':0.88,'ml':4},
    'DE': {'h':0.82,'s':0.85,'v':0.92,'ml':4},
    'NL': {'h':0.84,'s':0.86,'v':0.94,'ml':3},
    'BE': {'h':0.84,'s':0.86,'v':0.94,'ml':3},
    'CZ': {'h':0.84,'s':0.86,'v':0.94,'ml':4},
    'TR': {'h':0.85,'s':0.88,'v':0.94,'ml':4},
    'CO': {'h':0.88,'s':0.92,'v':0.82,'ml':3},
    'PH': {'h':0.92,'s':0.94,'v':0.88,'ml':3},
    'GR': {'h':0.86,'s':0.88,'v':0.94,'ml':3},
    '_':  {'h':1.00,'s':1.00,'v':1.00,'ml':3},
}

def tsc(country):
    return TYPE_SCALE.get(country.upper(), TYPE_SCALE['_'])

# ── Helpers de fonte ──────────────────────────────────────────────
def gf(fk, lang):
    ff = FONTS.get(fk, FONTS['poppins'])['f']
    if 'th' in lang: ff += ",'Noto Sans Thai'"
    if 'ja' in lang: ff += ",'Noto Sans CJK JP'"
    if 'ko' in lang: ff += ",'Noto Sans CJK KR'"
    return ff

def gr(fk, lang):
    if any(x in lang for x in ['th','ja','ko']): return 0.70
    return FONTS.get(fk, FONTS['poppins'])['r']

def cap(fk):  return FONTS.get(fk, FONTS['poppins'])['cap']
def desc(fk): return FONTS.get(fk, FONTS['poppins'])['desc']

def sw(canvas, fk, lang):
    return int(canvas / gr(fk, lang))

# ── Estimativa de largura ─────────────────────────────────────────
def ew(text, fs):
    v = 0.0
    for ch in text:
        o = ord(ch)
        if   0x0E00<=o<=0x0E7F: v+=EW['th']
        elif 0x3000<=o<=0x9FFF or 0xAC00<=o<=0xD7A3: v+=EW['cj']
        elif 0x0370<=o<=0x03FF: v+=EW['gr']
        elif ch in 'IiJjLl1|:.,;!': v+=EW['n']
        elif ch in 'MmWw': v+=EW['w']
        elif ch.isdigit(): v+=EW['g']
        elif ch==' ': v+=EW['sp']
        elif ch in '₱₺¥€£$฿₩': v+=EW['sy']
        else: v+=EW['d']
    return v * fs

# ── Gap físico — NÚCLEO do anti-colisão ──────────────────────────
def gap_ab(fa, sa, fb, sb, br=20):
    """Delta Y baseline_a → baseline_b garantindo topo_b ≥ bottom_a + br"""
    return int(desc(fa)*sa + cap(fb)*sb + br)

def gap_s(fk, fs, br=20):
    return gap_ab(fk, fs, fk, fs, br)

def first_y(top_margin, fk, fs):
    """Baseline da 1ª linha tal que topo visual = top_margin"""
    return top_margin + int(cap(fk) * fs)

def bottom_of(y_baseline, fk, fs):
    """Retorna coordenada Y do fundo real do glyph (para anti-colisão)"""
    return y_baseline + int(desc(fk) * fs)

# ── fit / wrap ────────────────────────────────────────────────────
def fit(text, sw_, hi=120, lo=20):
    for fs in range(hi, lo-1, -2):
        if ew(text, fs) <= sw_: return fs
    return lo

def wrap(text, fs, sw_):
    is_cjk = any(0x0E00<=ord(c)<=0x9FFF or 0xAC00<=ord(c)<=0xD7A3 for c in text)
    if is_cjk and ' ' not in text:
        lines, cur, cw = [], '', 0.0
        for ch in text:
            o=ord(ch)
            w=(EW['th'] if 0x0E00<=o<=0x0E7F
               else EW['cj'] if 0x3000<=o<=0x9FFF or 0xAC00<=o<=0xD7A3
               else EW['d'])
            if cw+w*fs<=sw_: cur+=ch; cw+=w*fs
            else:
                if cur: lines.append(cur)
                cur=ch; cw=w*fs
        if cur: lines.append(cur)
        return lines or [text]
    words=text.split(); lines,cur=[],''
    for w in words:
        t=(cur+' '+w).strip()
        if ew(t,fs)<=sw_: cur=t
        else:
            if cur: lines.append(cur)
            cur=w
    if cur: lines.append(cur)
    return lines or [text]

def fw(lines_in, sw_, fk, lang, hi=96, lo=32, ml=3):
    for fs in range(hi, lo-1, -2):
        if sum(len(wrap(l,fs,sw_)) for l in lines_in) <= ml:
            return fs, [l for ln in lines_in for l in wrap(ln,fs,sw_)]
    return lo, [l for ln in lines_in for l in wrap(ln,lo,sw_)]

# ── WCAG ──────────────────────────────────────────────────────────
def lum(hx):
    h=hx.lstrip('#')
    if len(h)==3: h=''.join(c*2 for c in h)
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    rgb=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in rgb]
    return 0.2126*rgb[0]+0.7152*rgb[1]+0.0722*rgb[2]

def atc(bg, light='#FFFFFF', dark='#0A0204'):
    return light if lum(bg)<0.30 else dark

def ctr(fg, bg):
    l1,l2=lum(fg),lum(bg)
    return (max(l1,l2)+0.05)/(min(l1,l2)+0.05)

def sac(ac, bg):
    return ac if ctr(ac,bg)>=4.5 else atc(bg)

def mix(c1,c2,t=0.5):
    h1=[int(c1.lstrip('#')[i:i+2],16) for i in (0,2,4)]
    h2=[int(c2.lstrip('#')[i:i+2],16) for i in (0,2,4)]
    return '#{:02X}{:02X}{:02X}'.format(*[int(a*(1-t)+b*t) for a,b in zip(h1,h2)])

def spv(v):
    for s in [' a ',' to ',' – ',' - ',' tot ',' bis ',' até ',' à ',
              ' ila ',' έως ','～','〜','—','~']:
        if s in v: p1,p2=v.split(s,1); return p1.strip(),s.strip(),p2.strip()
    return v,'',''

def esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

# ── Primitivos SVG ────────────────────────────────────────────────
def T(x,y,s,fw_,fs,fill,ff,anc='start',ls=0,op=1.0,flt=''):
    ta  = f' text-anchor="{anc}"'    if anc!='start' else ''
    lsp = f' letter-spacing="{ls}"' if ls else ''
    opc = f' opacity="{op}"'        if op<1 else ''
    fid = f' filter="url(#{flt})"'  if flt else ''
    return (f'<text x="{x}" y="{y}" font-family="{ff}" font-weight="{fw_}" '
            f'font-size="{fs}" fill="{fill}"{ta}{lsp}{opc}{fid}>{esc(s)}</text>')

def R(x,y,w,h,rx,fill,op=1.0,stroke='none',sw_=0):
    sk=f' stroke="{stroke}" stroke-width="{sw_}"' if stroke!='none' else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" fill-opacity="{op}"{sk}/>'

def L(x1,y,x2,col,sw_=2,op=1.0):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{col}" stroke-width="{sw_}" opacity="{op}"/>'

def Lv(x,y1,y2,col,sw_=1,op=1.0):
    return f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{col}" stroke-width="{sw_}" opacity="{op}"/>'

def Ci(cx,cy,r,fill,op=1.0,stroke='none',sw_=0):
    sk=f' stroke="{stroke}" stroke-width="{sw_}"' if stroke!='none' else ''
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" opacity="{op}"{sk}/>'

def Pg(pts,fill,op=1.0,stroke='none',sw_=0):
    sk=f' stroke="{stroke}" stroke-width="{sw_}"' if stroke!='none' else ''
    return f'<polygon points="{pts}" fill="{fill}" opacity="{op}"{sk}/>'

def Arc(cx,cy,r,s_d,e_d,col,sw_=4,op=1.0):
    s=math.radians(s_d-90); e=math.radians(e_d-90)
    x1=cx+r*math.cos(s); y1=cy+r*math.sin(s)
    x2=cx+r*math.cos(e); y2=cy+r*math.sin(e)
    lg=1 if (e_d-s_d)>180 else 0
    return (f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 {lg},1 {x2:.1f},{y2:.1f}" '
            f'fill="none" stroke="{col}" stroke-width="{sw_}" opacity="{op}" stroke-linecap="round"/>')

def DEFS():
    return '''<defs>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="18" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glowM" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="10" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glowSm" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur stdDeviation="6" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glowLg" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="28" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="3" stdDeviation="6" flood-color="#000" flood-opacity="0.55"/>
  </filter>
  <filter id="shadowHard" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="2" dy="4" stdDeviation="2" flood-color="#000" flood-opacity="0.80"/>
  </filter>
</defs>'''

# ── CTA posição fixa ──────────────────────────────────────────────
def CTA(c, pal, is9, ff, fk, lang, bg_cta):
    tc=atc(bg_cta)
    ac=pal['a1'] if ctr(pal['a1'],bg_cta)>=3.0 else tc
    lbl=c['cta']; afs=54; arrow='↓'
    ratio=gr(fk,lang)
    aw=int(ew(arrow,afs)*ratio)+8
    cfs=fit(lbl, sw(CW-aw-28,fk,lang), hi=28, lo=14)
    tw=int(ew(lbl,cfs)*ratio)
    sy=1110 if not is9 else 1440
    cy=1185 if not is9 else 1540
    total=tw+24+aw
    tx=max(XL,XR-total) if not is9 else max(XL,CX-total//2)
    arx=min(XR-aw,tx+tw+24)
    return '\n'.join([
        R(0,sy,1080,1080,'0',bg_cta,0.96),
        L(XL,sy,XR,ac,1.5,0.35),
        T(tx,cy,lbl,'900',cfs,tc,ff,ls=1),
        T(arx,cy,arrow,'900',afs,ac,ff,flt='glowSm'),
        L(tx,cy+12,arx+aw,ac,2,0.55),
    ])

# ── DISC sempre completo ──────────────────────────────────────────
def DISC(c, pal, is9, ff, fk, lang, bg):
    dy=1228 if not is9 else 1830
    tc=atc(bg,light='#CCCCCC',dark='#444444')
    sf=sw(CW,fk,lang)
    out=[L(XL,dy-16,XR,tc,0.5,0.20)]
    for wl in wrap(c['disclaimer'],13,sf):
        out.append(T(CX,dy,wl,'400',13,tc,ff,'middle',op=0.72))
        dy+=18
    return '\n'.join(out)

# ── BLOCO DE VALOR com anti-colisão ──────────────────────────────
def VBLOCK(xi, y_top, p1, sep, p2, vfs, fk, ff, bg, pal, anc='start'):
    """Renderiza valor. y_top = topo visual desejado. Retorna (svg, y_bottom)."""
    tc=atc(bg); ac=sac(pal['a1'],bg)
    y=y_top+int(cap(fk)*vfs)   # primeiro baseline
    out=[]
    if sep:
        sf2=max(20,int(vfs*0.50)//2*2)
        out.append(T(xi,y,p1,'900',vfs,tc,ff,anc,ls=-1,op=0.70))
        y+=gap_ab(fk,vfs,fk,sf2,12)
        out.append(T(xi,y,sep,'300',sf2,tc,ff,anc,op=0.55))
        y+=gap_ab(fk,sf2,fk,vfs,16)
        out.append(T(xi,y,p2,'900',vfs,ac,ff,anc,ls=-2,flt='glow'))
        y_bot=bottom_of(y,fk,vfs)
    else:
        out.append(T(xi,y,p1,'900',vfs,ac,ff,anc,ls=-2,flt='glow'))
        y_bot=bottom_of(y,fk,vfs)
    return '\n'.join(out), y_bot

def svg_wrap(W,H,bg,content):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">\n{DEFS()}\n'
            f'{R(0,0,W,H,"0",bg)}\n{content}\n</svg>')
