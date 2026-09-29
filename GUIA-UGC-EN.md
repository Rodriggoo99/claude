# Guia de estilo — vídeos UGC em inglês (Rodrigo | UGC Creator)

> **PROPOSTA DE BASE (v1, a aguardar aprovação):** vídeo "UGC Video 1 — Brands don't want followers" (`edit-pipeline/ugc-brands/`).
> Público: **marcas e outros criadores UGC**. Objetivo: mostrar que sei produzir conteúdo — não "autoridade" como na marca pessoal PT.
> Por isso a linguagem visual é **diferente** da base PT (papel editorial, âmbar, Instrument Serif), mas continua cinematográfica e limpa.

Tudo o que o `GUIA-DE-ESTILO-VIDEOS.md` diz sobre **corte, cor (não mexer), 10-bit, entregas para o CapCut, margens seguras, som e fluxo 1080p → 4K** mantém-se. Este guia só muda a parte gráfica.

## Velocidade
- Se o Rodrigo já mandar o corte feito a 1.1x (como neste vídeo), **não acelerar outra vez** — nem imagem nem áudio.

## Conceito: "creator studio"
A estética vem das ferramentas de quem faz conteúdo: visor de câmara, interface de apps, briefs de marca.

| Elemento | PT (marca pessoal) | EN (UGC) |
|---|---|---|
| Tipografia principal | Inter Tight condensada / Instrument Serif itálico | **Archivo Expanded** (larga, 125%, peso 850–900), maiúsculas |
| Etiquetas | Inter Bold espaçada | **JetBrains Mono Bold**, maiúsculas, escrita letra a letra com cursor laranja |
| Palavra "emocional" | itálico serifado | **contorno (outline)** ou riscada a laranja |
| Cor das legendas | branco | **tinta preta `#111113`** sobre a t-shirt branca |
| Destaque | âmbar do relógio `#F2B24C` | **laranja "ember" `#FF5B24`** (do quadro de fogo atrás) — só em números, riscos, checks, REC |
| Cartões | papel creme, ecrã escuro | **vidro fosco claro** (blur real do fundo + branco 62%) |

## Recursos gráficos (escolher 2–3 por vídeo, variar)
- **Hook com visor de câmara:** cantos de enquadramento, ● REC a piscar, timecode, e uma caixa de **foco automático que "tranca" na cara** na palavra-chave ("this") + bip + punch-in. Alternativa ao "palavra gigante atrás da cabeça".
- **Print real de perfil/resultado:** cartão branco com sombra, entra com mola, **zoom dentro do cartão** até ao número, círculo desenhado à mão a laranja + etiqueta em inglês (ex.: `<1K FOLLOWERS`) quando o print está em PT.
- **Checklist "What brands want":** cartão de vidro com linhas 01/02/03 em "skeleton" (a carregar) que se preenchem à medida que falo; checkbox laranja + contador 0/3 → 3/3.
- **Palavra de profundidade:** uma única palavra-tese gigante (Archivo Expanded, preta) **atrás da cabeça**, arrastada com motion blur + impacto + abanão.
- **CTA "save":** pílula de vidro com o ícone de guardar do Instagram a encher a laranja.
- **Callback:** a mesma palavra do hook (ex.: FOLLOWERS riscado) volta no fim.

## Legendas
- Ao peito (topo do bloco ~y 1185 em 1080×1920), centradas em x = 510 (centro da zona segura).
- Estrutura: etiqueta mono (a escrever) + 1–2 palavras grandes em Archivo Expanded que **entram arrastadas** com motion blur direcional.
- Halo branco suave atrás das etiquetas para lerem sobre o microfone/mãos.

## Técnica
- Pipeline: `edit-pipeline/ugc-brands/` — `overlay.html` (render frame a frame com Playwright, modos `front` / `depth` / `mask`), `comp.py` (zoom na cara, abanão, blur do vidro, composição 16-bit), `matte.py` (recorte BiRefNet-portrait para a palavra atrás da cabeça), `sfx.py` (voz -14 LUFS + efeitos sintetizados).
- O blur do vidro fica **no plate** (não é cor, gradua-se normalmente); o escurecimento/tinta fica na camada de texto.
