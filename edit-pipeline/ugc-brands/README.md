# UGC Video 1 — "Brands don't want followers" (EN) — pipeline

Base proposta para os vídeos UGC em inglês: ver `GUIA-UGC-EN.md` na raiz.
Fonte: `UGC Video 1 Pré Claude.mp4` (Drive › Videos Claude Edits › Videos UGC) — já cortado e a 1.1x pelo Rodrigo, por isso **sem mudança de velocidade**.

```
python3 edl.py                                   # shake.json (partilhado com o overlay)
node render/render.js <ov>/front front 1 frames 0 1541 3     # 1080 (scale 2 = 4K)
node render/render.js <ov>/mask  mask  1 frames 913 1352 2   # vidro fosco (checklist)
node render/render.js <ov>/mask  mask  1 frames 1452 1532 2  # vidro fosco (save)
node render/render.js <ov>/depth depth 1 frames 725 818 2    # QUALITY atrás da cabeça
python3 matte.py dump <plates> && python3 matte.py infer <plates> <ov>/matte
python3 sfx.py                                   # final_mix.wav, voice.wav, sfx_only.wav (-14 LUFS)
python3 comp.py run 1 <ov> <out>/                # pré-visualização 1080p
python3 comp.py run 2 <ov4k> <out>/              # final 4K: plate 10-bit + final 10-bit + H.264
```
Setup: `cd render && npm i playwright@1.56 @fontsource-variable/archivo @fontsource/jetbrains-mono`; `pip install opencv-python-headless onnxruntime rembg pyloudnorm scipy soundfile` (o modelo BiRefNet-portrait vem do rembg).
