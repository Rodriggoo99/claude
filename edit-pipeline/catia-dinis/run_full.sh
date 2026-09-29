#!/bin/bash
# 4K finished file: his graded cut + graphics + final mix (waits for the 4K overlay render to finish)
set -euo pipefail
cd "$(dirname "$0")"
while pgrep -f "node render.js ../_work/ov4k" >/dev/null; do sleep 15; done
echo "overlay 4K: $(ls _work/ov4k/front | wc -l)"
python3 comp.py full _work/ov4k "../../videos/Catia e Dinis/Catia e Dinis - Final 4K.mp4"
cp final_mix.wav "../../videos/Catia e Dinis/audio_final_mix.wav"
echo "ALL DONE"
ls -l "../../videos/Catia e Dinis"
