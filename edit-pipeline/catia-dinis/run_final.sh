#!/bin/bash
# 4K delivery for CapCut (the graded cut itself is not re-encoded)
set -euo pipefail
cd "$(dirname "$0")"
OUT="../../videos/Catia e Dinis"
rm -rf _work/ov4k
(cd render && DSF=2 node render.js ../_work/ov4k 60 58.4 4)
echo "overlay 4K: $(ls _work/ov4k/front | wc -l)"
python3 comp.py final _work/ov4k
cp _work/texto_legendas_CapCut_ProRes4444.mov "$OUT/texto_legendas_CapCut_ProRes4444.mov"
cp _work/segmento_desfocado_regra.mov "$OUT/segmento_desfocado_regra_43.80s.mov"
cp final_mix.wav "$OUT/audio_final_mix.wav"; cp voice.wav "$OUT/audio_voz.wav"
cp audio_musica.wav "$OUT/audio_musica.wav"; cp sfx_only.wav "$OUT/audio_efeitos.wav"
echo "ALL DONE"; ls -l "$OUT"
