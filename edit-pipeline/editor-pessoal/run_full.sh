#!/bin/bash
# 4K finished file (graded cut + graphics + voice/SFX mix, no music — the trending sound is added in-app)
set -euo pipefail
cd "$(dirname "$0")"
OUT="../../videos/Editor Pessoal"
rm -rf _work/ov4k
(cd render && DSF=2 node render.js ../_work/ov4k 60 29.13 4)
echo "overlay 4K: $(ls _work/ov4k/front | wc -l)"
python3 comp.py full _work/ov4k "$OUT/Editor Pessoal - Final 4K (sem musica).mp4"
cp final_mix.wav "$OUT/audio_voz_efeitos_sem_musica.wav"
echo "ALL DONE"
ls -l "$OUT"
