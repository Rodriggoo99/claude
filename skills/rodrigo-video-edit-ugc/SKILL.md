---
name: rodrigo-video-edit-ugc
description: Base aprovada para editar os vídeos UGC do Rodrigo ("Rodrigo | UGC Creator") — marca pessoal UGC, normalmente em inglês, feita para chegar a marcas e a outros criadores UGC. Estilo "creator studio" — Archivo Expanded + etiquetas mono escritas letra a letra, legendas creme centradas em cima quando a t-shirt é branca, paleta pêssego/terracota (nunca preto), cartões de vidro fosco, print real onde ele aponta, palavra-tese atrás da cabeça, áudio original intocado, pré-visualização 1080p e final 4K separada para o CapCut. Usar SEMPRE que o Rodrigo pedir para editar, cortar, legendar ou pôr motion graphics num vídeo UGC ou da marca pessoal UGC — mesmo que diga só "vídeo UGC", "vídeo em inglês", "vídeo para marcas", "mais um vídeo UGC" ou deixe um ficheiro "UGC … Pre Claude" no Drive. Para vídeos de marca pessoal/autoridade em português usar a skill rodrigo-video-edit-pt.
---

# Vídeos UGC do Rodrigo — base "creator studio" (EN)

Referência aprovada: **"UGC Video 1 — Brands don't want followers"** (v4). No repositório `Rodriggoo99/claude`: `GUIA-UGC-EN.md`, pipeline em `edit-pipeline/ugc-brands/`, entregas em `videos/UGC Video 1 - Brands Dont Want Followers/`. Os scripts desta skill (`scripts/`) são esse pipeline, prontos a copiar para um vídeo novo.

**Para quem é:** marcas e outros criadores UGC. O vídeo tem de provar que o Rodrigo sabe produzir conteúdo que vende — limpo, premium, cinematográfico — e **não** pode parecer a marca pessoal PT (papel creme editorial, âmbar do relógio, Instrument Serif). Cada vídeo UGC segue esta base mas varia os gráficos: nunca repetir exatamente a mesma sequência de recursos.

## Fluxo de trabalho

1. **Buscar o vídeo** ao Drive (pasta "Videos Claude Edits › Videos UGC"). O conector do Drive só descarrega ≤10 MB; para o vídeo usar `curl -L "https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t"`. Se houver ficheiros com nomes parecidos, confirmar qual é (no vídeo 1 havia "UGC Video 1 Pré Claude" e o certo era "UGC 1 Pre Claude" — mesma imagem, áudio corrigido). Prints/imagens na mesma pasta são para usar no vídeo.
2. **Analisar antes de mexer:** `ffprobe`; transcrição Whisper large-v3 (`en`) com tempos por palavra; detetar os jump cuts (diferença entre frames); comparar a duração/ritmo. O Rodrigo costuma mandar o corte **já feito e já a 1.1x** — nesse caso **não voltar a cortar nem acelerar** (nem imagem nem áudio). Se vier em bruto, aplicar as regras de corte do `GUIA-DE-ESTILO-VIDEOS.md` (melhor take por entoação + cara, corte apertado, 1.1x, cortar quando a mão chega à câmara).
3. **Plano de gráficos** (2–3 recursos + CTA, ver abaixo), com tempos tirados das palavras da transcrição. Escrever o `edl.json` (zooms, abanões, janelas de vidro e de profundidade) e o `render/overlay.html` a partir do `overlay-template.html`.
4. **Pré-visualização 1080p** → enviar no chat (≤30 MB) e esperar feedback. Iterar só no que ele pedir; dizer sempre o que mudou e porquê.
5. **Final 4K** só depois de aprovado: `scripts/final4k.sh` → entregas (abaixo) → `LEIA-ME.md` → Git LFS + commit + push no branch indicado.

Detalhes técnicos, comandos e armadilhas: **`references/pipeline.md`** (ler antes de correr os scripts).

## Regras herdadas da base (não negociáveis)

- **Não mexer na cor** — ele grada depois. Pipeline em RGB 16-bit, plate entregue em 10-bit (mesmo que a fonte seja 8-bit).
- **Margens seguras Reels/TikTok** (1080×1920): 250 px em cima, 480 em baixo, 120 à direita, 60 à esquerda. Verificar **todas** as frames medindo os pixels reais das letras (alpha > 128), incluindo entradas animadas e abanões — não caixas.
- Zooms poucos, suaves, **centrados na cara**; punch-in só em palavras-chave.
- Cada gráfico fica **completo e parado ~0,8–1 s** antes de sair.

## Sistema visual

| Elemento | Valor |
|---|---|
| Palavras grandes | **Archivo Expanded** (variável, `font-stretch:125%`, peso 850–900), maiúsculas, tracking −0.018em, ~84–100 px (150 px para a palavra do hook) |
| Etiquetas | **JetBrains Mono ExtraBold** 33 px, maiúsculas, escritas letra a letra com cursor bloco pêssego |
| Texto das legendas | **creme `#FFF4E6`** + sombra quente suave (castanho `rgba(58,34,22,…)`) — **nunca preto** |
| Destaques | **pêssego `#FFB78E`** (números, palavras-chave), **terracota `#E0784F`** (riscos, círculos, checks, ícones cheios) — cores quentes tiradas do quadro de fogo do escritório |
| Texto dentro de cartões claros | café `#4A3A31` |
| Cartões | **vidro fosco claro**: blur real do plate por baixo + branco 62% + borda branca fina + sombra suave |

Porquê estas cores: ele pediu explicitamente "cores aesthetic, mas preto não". Se o cenário mudar (outra divisão/roupa), tirar a cor de destaque da cena com a mesma lógica (tons quentes, suaves) e manter o creme para texto.

### Legendas
- **T-shirt branca → legendas em cima, na parede vazia** acima da cabeça (bloco alinhado por baixo em y ≈ 525, acima do relógio e do cabelo). Cartões e gráficos ficam ao peito — exceto quando ele aponta para cima (ver print). Com roupa escura, confirmar com ele antes de mudar a posição.
- **Centradas no ecrã (x = 540)**, não no centro da zona segura; por causa da margem direita a largura máxima é 840 px. Medir o centro real depois de renderizar.
- Estrutura: etiqueta mono (a escrever) + 1–2 palavras grandes que **entram arrastadas** com motion blur direcional. Texto grande logo na **primeira frame** (é a capa do Reel).
- Riscado terracota para negar ("~~FOLLOWERS~~"); contorno (outline) para a palavra "errada"; brilho de luz a passar (sweep) só nas palavras-chave do hook/remate.

## Recursos gráficos (menu — escolher 2–3 por vídeo + CTA, variar entre vídeos)

- **Hook limpo e premium:** palavra grande desde a frame 0, arrastada, brilho a passar, impacto + punch-in suave. **Nada de visor de câmara, REC, cantos ou caixas de foco** — foi rejeitado ("não gosto, há espaço para algo mais premium").
- **Print real (perfil, resultados, mensagens):** cartão branco com sombra, entra com mola, **zoom dentro do cartão** até ao número que interessa e círculo terracota desenhado à mão. **Pôr o print onde ele aponta** (no vídeo 1 apontava para cima → cartão em cima). Se o print estiver em português, juntar uma etiqueta em inglês (`<1K FOLLOWERS`). Nunca inventar números nem logótipos de marcas.
- **Checklist / lista ("The brief"):** cartão de vidro com linhas 01/02/03 em "skeleton" que se preenchem à medida que ele fala, checkbox terracota e contador 0/3 → 3/3; o título ("3 THINGS") fica nas legendas de cima.
- **Palavra de profundidade:** uma palavra-tese gigante atrás da cabeça (recorte BiRefNet), **gradiente creme → pêssego, sem sombra**. A cabeça só pode tapar **~1/3 de baixo** das letras do meio — medir o topo da cabeça no recorte e subir a palavra se tapar mais (no vídeo 1 tapava 60% e "não se via bem"). Enquanto está no ecrã, em cima só uma etiqueta pequena.
- **CTA save/comenta:** pílula de vidro com o ícone nativo do Instagram a encher a terracota; sai antes de a mão chegar à câmara.
- **Callback:** a palavra do hook volta no fim (ex.: FOLLOWERS riscado outra vez).

## Som

- **Usar o áudio tal como ele o manda:** mesma velocidade, mesma taxa de amostragem, **sem EQ, sem compressão, sem limitador, sem igualar takes**. Só é permitido **um ganho plano** para o ficheiro ficar a −14 LUFS; o stem `audio_voz.wav` tem de ser o original × ganho, amostra a amostra (verificar).
- Porquê: tentar igualar o tom dos takes com EQ deixou o áudio "debaixo de água" e ele pediu para não mexer. Se notares diferenças entre takes, **avisa** em vez de processar — ele corrige na origem.
- Efeitos sintetizados (`sfx_lib.py`) discretos por baixo: whoosh nas entradas, impacto na palavra de profundidade/hook, pop nos checks e na etiqueta, chime no 3/3 e no save. Se o mix clipar, baixar os efeitos, nunca a voz. Música só com licença e só se ele pedir.

## Entregas (pasta `videos/<Nome do vídeo>/`, via Git LFS)

| Ficheiro | Para quê |
|---|---|
| `<Nome> - Final (sem cor) H264.mp4` | versão completa para ver/publicar |
| `<Nome> - Final (sem cor) 10bit HEVC.mp4` | o mesmo em 10-bit |
| `plate_10bit_sem_texto.mp4` | para graduar: corte + zooms + blur do vidro, sem texto |
| `texto_legendas_CapCut_ProRes4444.mov` | legendas + gráficos com transparência (profundidade já recortada), por cima do plate graduado |
| `texto_legendas_alpha.mov` | o mesmo em PNG/alpha, mais leve |
| `audio_final_mix.wav` / `audio_voz.wav` / `audio_efeitos.wav` | mix e stems |
| `LEIA-ME.md` | ficheiros, fluxo no CapCut (timeline 2160×3840, plate na faixa 1, texto por cima a 100%, tudo começa em 00:00), decisões tomadas |

Antes de entregar: contar frames (= fonte), confirmar sincronização, 10-bit no plate, margens seguras a 4K e uma frame da final comparada com a pré-visualização aprovada.

## Erros já cometidos (não repetir)

- Legendas pretas; legendas ao peito sobre t-shirt branca; texto centrado em x = 510 em vez de 540.
- Visor de câmara / caixa de foco no hook.
- Palavra de profundidade demasiado tapada pela cabeça, em terracota sólida (pouco contraste) ou com sombra.
- Acelerar um corte que já vinha a 1.1x; processar/igualar o áudio.
- Print ao peito quando ele aponta para cima.
