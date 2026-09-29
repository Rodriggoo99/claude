# Guia de estilo — vídeos UGC em inglês (Rodrigo | UGC Creator)

> **PROPOSTA DE BASE (v2, a aguardar aprovação):** vídeo "UGC Video 1 — Brands don't want followers" (`edit-pipeline/ugc-brands/`).
> Público: **marcas e outros criadores UGC**. Objetivo: mostrar que sei produzir conteúdo — não "autoridade" como na marca pessoal PT.
> Por isso a linguagem visual é **diferente** da base PT (papel editorial, âmbar, Instrument Serif), mas continua cinematográfica e limpa.

Tudo o que o `GUIA-DE-ESTILO-VIDEOS.md` diz sobre **corte, cor (não mexer), 10-bit, entregas para o CapCut, margens seguras, som e fluxo 1080p → 4K** mantém-se. Este guia só muda a parte gráfica.

## Velocidade
- Se o Rodrigo já mandar o corte feito a 1.1x (como neste vídeo), **não acelerar outra vez** — nem imagem nem áudio.

## Conceito: "creator studio"
A estética vem das ferramentas de quem faz conteúdo: interface de apps, briefs de marca, cartões de vidro — com tipografia larga e cores quentes.

| Elemento | PT (marca pessoal) | EN (UGC) |
|---|---|---|
| Tipografia principal | Inter Tight condensada / Instrument Serif itálico | **Archivo Expanded** (larga, 125%, peso 850–900), maiúsculas |
| Etiquetas | Inter Bold espaçada | **JetBrains Mono Bold**, maiúsculas, escrita letra a letra com cursor pêssego |
| Palavra "emocional" | itálico serifado | **contorno (outline)** ou riscada a terracota |
| Cor das legendas | branco | **creme `#FFF4E6`** com sombra quente suave — **nunca preto** |
| Destaque | âmbar do relógio `#F2B24C` | paleta aesthetic tirada do quadro de fogo: **pêssego `#FFB78E`** (palavras/números) e **terracota `#E0784F`** (riscos, círculo, checks, palavra de profundidade); texto dentro dos cartões claros em **café `#4A3A31`** |
| Cartões | papel creme, ecrã escuro | **vidro fosco claro** (blur real do fundo + branco 62%) |

## Recursos gráficos (escolher 2–3 por vídeo, variar)
- **Hook limpo e premium (sem visor/retângulos):** texto grande logo na primeira frame, palavras arrastadas com motion blur, **brilho de luz a passar** nas palavras-chave ("THIS." maior, 150 px) + impacto + punch-in suave na cara.
- **Print real de perfil/resultado:** cartão branco com sombra ao peito, entra com mola, **zoom dentro do cartão** até ao número e círculo terracota desenhado à mão; a legenda em cima diz a frase em inglês (ex.: "1K FOLLOWERS").
- **Checklist "The brief":** cartão de vidro ao peito com linhas 01/02/03 em "skeleton" (a carregar) que se preenchem à medida que falo; checkbox terracota + contador 0/3 → 3/3; o título ("3 THINGS") fica em cima.
- **Palavra de profundidade:** uma única palavra-tese gigante (Archivo Expanded, terracota) **atrás da cabeça**, arrastada com motion blur + impacto + abanão.
- **CTA "save":** pílula de vidro com o ícone de guardar do Instagram a encher a terracota.
- **Callback:** a mesma palavra do hook (ex.: FOLLOWERS riscado) volta no fim.

## Legendas
- **T-shirt branca → legendas em cima, na parede vazia** (bloco alinhado por baixo em y ≈ 525 em 1080×1920, acima do relógio e da cabeça). Cartões/gráficos ficam ao peito.
- **Centradas no ecrã (x = 540)**; como a margem direita é 120 px, a largura máxima do texto é 840 px.
- Estrutura: etiqueta mono (a escrever) + 1–2 palavras grandes em Archivo Expanded que **entram arrastadas** com motion blur direcional.
- Sombra quente suave (castanho, não preto) para lerem sobre a parede clara.

## Som
- Os cortes juntam takes gravados a distâncias diferentes do microfone: igualar **tom (EQ por 1/3 de oitava) e volume (-14 LUFS) take a take** (`audio_match.py`) antes dos efeitos. Neste vídeo o take dos 16,67 s estava 3 dB mais baixo e mais sibilante.

## Técnica
- Pipeline: `edit-pipeline/ugc-brands/` — `overlay.html` (render frame a frame com Playwright, modos `front` / `depth` / `mask`), `comp.py` (zoom na cara, abanão, blur do vidro, composição 16-bit), `matte.py` (recorte BiRefNet-portrait para a palavra atrás da cabeça), `audio_match.py` (igualar takes), `sfx.py` (efeitos sintetizados por baixo da voz).
- O blur do vidro fica **no plate** (não é cor, gradua-se normalmente); o escurecimento/tinta fica na camada de texto.
