# Studio4 — Creative Generator

Sistema local para gerar criativos SVG + PNG com **edição por bloco clicável**, **background com efeitos** e **clones por país com tradução automática**.

---

## Instalação rápida

```bash
git clone https://github.com/SEU_USUARIO/studio4.git && cd studio4
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py   # → http://localhost:5000
```

### Dependências opcionais (para PNG)
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf imagemagick
# macOS
brew install --cask wkhtmltopdf && brew install imagemagick
```

---

## O que é novo no Studio4

### 1. Edição por bloco clicável
Cada criativo é composto por **blocos independentes**:

| Tipo | Base | Controles |
|------|------|-----------|
| `headline` | 88px | Fonte, Tamanho %, Cor, Alinhamento, Spacing, Opacity |
| `subhead` | 30px | Fonte, Tamanho %, Cor, Alinhamento, Spacing, Opacity |
| `value` | 96px | Fonte, Tamanho %, Cor, Alinhamento (suporta split "a"/"to") |
| `cta` | 28px | Texto, Cor, Alinhamento |
| `disclaimer` | 13px | Cor, Tamanho %, Opacity |
| `divider` | — | Largura %, Cor, Opacity |
| `spacer` | — | Altura em px |

- Adicione quantos blocos quiser de cada tipo
- Reordene com ↑↓
- Oculte/mostre individualmente com o toggle de visibilidade
- **Anti-colisão total**: quando um texto quebra linha, todos os blocos seguintes descem automaticamente

### 2. Background
- Upload de imagem (JPG, PNG, WebP)
- **Efeito P&B** (grayscale SVG filter)
- **Efeito Degradê** (overlay gradiente da imagem para cor de fundo)
- Opacidade ajustável (0–100%)
- Cor de fundo sólida com picker
- "Da bandeira" — aplica paleta do país primário automaticamente

### 3. Tradução e clones por país
- Cole o texto em PT-BR no país primário
- Adicione países clones — tradução automática via Claude API
- Alterações de **fonte, tamanho e cor** no primário propagam para todos os clones
- Cada clone tem menu próprio com:
  - Textos traduzidos editáveis
  - Visibilidade independente por bloco (●/○)
  - Preview individual
- Novos blocos adicionados são traduzidos para todos os clones automaticamente
- Sem API key: retorna texto original com CTA localizado

### 4. Exportação
- País primário + todos os clones
- Formatos 3:4 e/ou 9:16 por clique
- SVG sempre; PNG opcional (requer wkhtmltoimage)
- ZIP automático para download

---

## Anti-colisão (LayoutCursor)

```
top_margin
  ↓ first_y(fk, fs)           ← topo visual = top_margin
[BLOCO 1 baseline]
  ↓ bottom_of(baseline) + br  ← fundo real + breathing
[BLOCO 2 baseline]             ← nunca começa acima do fundo anterior
  ↓ bottom_of(baseline) + br
[BLOCO 3 baseline]
  ...até y_ct (zona CTA)
[CTA fixo y=1265 (3:4) | 1540 (9:16)]
[DISC fixo y=1310 (3:4) | 1830 (9:16)]
```

Quebra de linha automática → empurra todos os blocos seguintes → zero sobreposição.

---

## API

```bash
# Preview rápido
POST /api/preview
{ "document": {...}, "fmt": "34" }

# Traduzir blocos para múltiplos países
POST /api/translate
{ "blocks": [...], "countries": ["US","JP","DE"], "source_lang": "pt-BR" }

# Gerar (exportar com job async)
POST /api/generate
{ "mode": "document", "document": {...}, "clones": [...], "formats": ["34","916"], "generate_png": true }

# Status do job
GET /api/status/{job_id}

# Download ZIP
GET /api/download/{job_id}

# Upload imagem para background
POST /api/upload-image  (multipart/form-data, campo "file")

# Paleta do país
GET /api/country-palette/BR
```

---

## Estrutura

```
studio4/
├── app.py                    # Flask backend + rotas
├── engine/
│   ├── core.py               # Física tipográfica + primitivos SVG
│   ├── layout.py             # LayoutCursor anti-colisão
│   ├── renderer.py           # BlockRenderer — documento → SVG
│   ├── translator.py         # Tradução via Claude API
│   ├── models.py             # 14 modelos A–N (modo clássico)
│   └── countries.py          # 25 países com paletas
├── templates/
│   └── index.html            # UI completa (single file)
├── uploads/                  # Imagens de background temporárias
└── outputs/
    ├── svg/                  # SVGs exportados
    ├── png/                  # PNGs exportados
    └── zip/                  # ZIPs para download
```

---

## Configurar tradução automática

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

Ou cole a chave na aba **Config** da interface.

---

## Licença

MIT
