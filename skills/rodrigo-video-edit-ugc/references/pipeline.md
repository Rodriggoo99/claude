# Pipeline técnico — vídeos UGC (EN)

Os scripts estão em `scripts/` (cópia de `edit-pipeline/ugc-brands/` do repositório). Para um vídeo novo: copiar `scripts/` para `edit-pipeline/<nome-do-video>/`, copiar `render/overlay-template.html` para `render/overlay.html` e editar os tempos/textos; pôr os prints em `render/assets/`.

## Índice
1. Setup do ambiente
2. Ficheiros e o que fazem
3. Ordem de execução (pré-visualização e final)
4. Como escrever o overlay
5. Verificações (margens, centro, QA)
6. Armadilhas conhecidas

## 1. Setup do ambiente

```bash
apt-get install -y ffmpeg git-lfs && git lfs install --local        # ffmpeg com libx265, prores_ks, rubberband
pip install opencv-python-headless numpy faster-whisper onnxruntime "rembg[cpu]" pyloudnorm scipy
cd render && npm init -y && npm i playwright@1.56 @fontsource-variable/archivo @fontsource/jetbrains-mono
```
- `playwright@1.56` corresponde ao Chromium pré-instalado em `/opt/pw-browsers/chromium-1194` (o `render.js` usa esse executável). Não correr `playwright install`.
- O modelo de recorte é o BiRefNet-portrait do rembg: a primeira chamada a `rembg.new_session("birefnet-portrait")` descarrega-o para `~/.rembg/models/birefnet-portrait/` (~1 GB). Depois o `matte.py` usa o ONNX diretamente.

## 2. Ficheiros

| Ficheiro | Função |
|---|---|
| `edl.json` | por vídeo: fps, `speed` (1.0 se ele já mandou a 1.1x), `out_frames`, centro da cara `face` (fração da imagem), `zooms`, `shakes` [[t, px]], `glass_windows` [[t0,t1]], `depth_window` [t0,t1] |
| `edl.py` | zoom(t), shake(t); `python3 edl.py` escreve `shake.json` (o overlay aplica o mesmo abanão que o plate) |
| `render/overlay.html` | todos os gráficos, desenhados em HTML/CSS a 1080×1920; `render(t, mode)` com modos `front` (tudo menos a palavra de profundidade), `depth` (só essa palavra), `mask` (formas dos cartões de vidro, para o blur) |
| `render/render.js` | `node render.js <dir> <mode> <scale 1\|2> frames <de> <até> [workers]` ou `... times t1,t2` → PNG com alpha. Escala 2 = 4K |
| `matte.py` | `dump` (frames do plate já com zoom na janela de profundidade) + `infer` (recorte da pessoa, BiRefNet 1024², ~20 s/frame em 4 CPUs) |
| `comp.py` | plate: 1.1x opcional, zoom na cara, abanão, blur do vidro (máscara) — tudo em RGB 16-bit sem tocar na cor; composição com a camada de texto. `run 1` = pré-visualização H.264 1080p; `run 2` = plate 10-bit + final 10-bit + final H.264 a 4K. `stills` para testes rápidos |
| `textlayer.py` | camada de texto final = front SOBRE (palavra de profundidade × (1 − recorte)) → ProRes 4444 + PNG-MOV |
| `sfx.py` + `sfx_lib.py` | efeitos sintetizados (whoosh, impacto, pop, tick, chime, scribble, shutter) por baixo da voz original com um único ganho plano para −14 LUFS; escreve `final_mix.wav`, `voice.wav`, `sfx_only.wav` à taxa original |
| `final4k.sh` | corre tudo para a final 4K (lê os intervalos de frames do `edl.json`) |

Frame = `round(t × 60)`. Os tempos são sempre na timeline final (a do ficheiro dele, se já vier cortado).

## 3. Ordem de execução

Pré-visualização 1080p:
```bash
python3 edl.py
node render/render.js $OV/front front 1 frames 0 <N-1> 3
node render/render.js $OV/mask  mask  1 frames <janela de vidro em frames> 2      # uma chamada por janela
node render/render.js $OV/depth depth 1 frames <janela de profundidade> 2
SRC=video.mp4 python3 matte.py dump $PLATES && python3 matte.py infer $PLATES $OV/matte
python3 sfx.py video.mp4                                  # na pasta de áudio
SRC=video.mp4 python3 comp.py run 1 $OV $PREV/
ffmpeg -i $PREV/final_h264.mp4 -i final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart preview.mp4
```
Final 4K (depois de aprovado): `sh final4k.sh video.mp4 $OV <work> <pasta de áudio>` (~1–1,5 h em 4 CPUs; correr com `nohup … &` e ir vendo o log).

Para testar um visual sem renderizar tudo: `node render.js <dir>/front front 1 times 0.3,3.9,12.6` + `python3 comp.py stills <dir> <out> 0.3,3.9,12.6` (precisa de `<dir>/matte/t_<t>.png` para a palavra de profundidade).

## 4. Como escrever o overlay

- `CAPS`: lista de blocos `{s, e, items}`; cada item é `{k:'label', text, t, cps}` (etiqueta escrita) ou `{k:'hero', text, t, size, dir, sweep, strike, outline}` (palavra grande arrastada). `t` = início da palavra na transcrição (−0,02 a −0,06 s para entrar no ataque da voz). Bloco acaba no início do seguinte / no corte.
- Cartões: `IG` (print com `zoom`, `ring`, `chip`), `BR` (checklist com `rev`/`tick` por linha), `SV` (save), `DP` (palavra de profundidade). A posição do print depende de para onde ele aponta.
- O `path` do círculo no print está em coordenadas da imagem original (viewBox = tamanho do print) e o `transform-origin` do zoom = posição do número × escala do cartão.
- Janelas de vidro no `edl.json` têm de cobrir a entrada e a saída dos cartões de vidro (+0,25 s).

## 5. Verificações

Margens seguras (todas as frames, letras reais):
```python
import cv2, numpy as np, glob
for f in sorted(glob.glob('front/f_*.png')) + sorted(glob.glob('depth/f_*.png')):
    a = cv2.imread(f, cv2.IMREAD_UNCHANGED)[..., 3]; ys, xs = np.nonzero(a > 128)
    if len(xs) and (xs.min() < 60 or xs.max() > 960 or ys.min() < 250 or ys.max() > 1440): print(f, xs.min(), xs.max(), ys.min(), ys.max())
```
(a 4K multiplicar os limites por 2). Violações típicas: entradas com mola/overshoot, abanão, palavra de profundidade larga → reduzir distâncias/tamanho.

Centro das legendas: bbox do alpha na zona de cima numa frame parada → centro deve dar 540 ± 3.

Áudio: comparar `voice.wav` com o original (`g = a·b/a·a`, resíduo ≈ −138 dBFS) — prova que só houve ganho.

QA visual: folha de contacto a 4–5 fps da pré-visualização antes de enviar; ver entradas, saídas, sobreposições com a cara/relógio/mãos.

## 6. Armadilhas conhecidas

- **rembg → OOM** ao correr o BiRefNet várias vezes na mesma sessão: usar o `matte.py` (onnxruntime com `enable_cpu_mem_arena=False`) e não correr o Chromium em paralelo se houver pouca RAM.
- O Drive muitas vezes tem **dois ficheiros com nomes parecidos**; comparar imagem e áudio (`cmp`, diferença por frame) em vez de assumir.
- `background-clip:text` + `text-shadow` escurece o texto: usar `filter: drop-shadow` (já no template).
- Git: instalar `git-lfs` antes do primeiro commit de vídeo (os `.mp4/.mov/.wav` estão no `.gitattributes`); ficheiros `.gitignore` escrevem-se com a ferramenta Write (o shell pode não criar dotfiles).
- Fontes vêm do `node_modules` (fontsource) — o render espera por `document.fonts.ready`.
