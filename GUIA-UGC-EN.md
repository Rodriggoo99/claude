# Guia de estilo — vídeos UGC em inglês (Rodrigo | UGC Creator)

> **BASE (v4 — design aprovado pelo Rodrigo):** vídeo "UGC Video 1 — Brands don't want followers" (`edit-pipeline/ugc-brands/`).
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
- **Print real de perfil/resultado:** cartão branco com sombra, **colocado onde eu aponto** (aqui em cima, porque aponto para cima), entra com mola, **zoom dentro do cartão** até ao número, círculo terracota desenhado à mão + etiqueta em inglês (`<1K FOLLOWERS`) quando o print está em PT.
- **Checklist "The brief":** cartão de vidro ao peito com linhas 01/02/03 em "skeleton" (a carregar) que se preenchem à medida que falo; checkbox terracota + contador 0/3 → 3/3; o título ("3 THINGS") fica em cima.
- **Palavra de profundidade:** uma única palavra-tese gigante (Archivo Expanded, **gradiente creme → pêssego, sem sombra**) **atrás da cabeça**, arrastada com motion blur + impacto + abanão. A cabeça só deve tapar **~1/3 de baixo** das letras do meio (medir com o recorte) — se tapar mais, a palavra deixa de se ler. Enquanto ela está no ecrã, em cima só uma etiqueta pequena.
- **CTA "save":** pílula de vidro com o ícone de guardar do Instagram a encher a terracota.
- **Callback:** a mesma palavra do hook (ex.: FOLLOWERS riscado) volta no fim.

## Legendas
- **T-shirt branca → legendas em cima, na parede vazia** (bloco alinhado por baixo em y ≈ 525 em 1080×1920, acima do relógio e da cabeça). Cartões/gráficos ficam ao peito.
- **Centradas no ecrã (x = 540)**; como a margem direita é 120 px, a largura máxima do texto é 840 px.
- Estrutura: etiqueta mono (a escrever) + 1–2 palavras grandes em Archivo Expanded que **entram arrastadas** com motion blur direcional.
- Sombra quente suave (castanho, não preto) para lerem sobre a parede clara.

## Som
- **Usar o áudio tal como o Rodrigo o manda:** mesma velocidade, mesma taxa de amostragem, **sem EQ, sem compressão, sem limitador** na voz. Só é permitido **um ganho plano** para o ficheiro ficar a -14 LUFS (ex.: o áudio corrigido deste vídeo vinha a -20 LUFS → +6 dB). O stem `audio_voz.wav` = original × ganho, amostra a amostra.
- Os efeitos sintetizados vão por baixo; se o mix fosse clipar, baixa-se os efeitos — nunca a voz.
- (Testado e rejeitado: igualar tom/volume take a take com EQ — soou "debaixo de água".)

## Técnica
- Pipeline: `edit-pipeline/ugc-brands/` — `overlay.html` (render frame a frame com Playwright, modos `front` / `depth` / `mask`), `comp.py` (zoom na cara, abanão, blur do vidro, composição 16-bit), `matte.py` (recorte BiRefNet-portrait para a palavra atrás da cabeça), `sfx.py` (efeitos sintetizados por baixo da voz original).
- O blur do vidro fica **no plate** (não é cor, gradua-se normalmente); o escurecimento/tinta fica na camada de texto.
