#!/bin/bash
# Final 4K delivery for CapCut: overlay at 2x, composite, then mux/copy the deliverables.
set -euo pipefail
cd "$(dirname "$0")"
OUT="../../videos/Dizer Nao a Clientes"
FPS=59.94005994005994

rm -rf _work/ov4k
(cd render && DSF=2 node render.js ../_work/ov4k $FPS "$(python3 -c 'import json;print(json.load(open("../edl.json"))["total_out"])')" 4)
echo "overlay 4K done: $(ls _work/ov4k/front | wc -l) front, $(ls _work/ov4k/back | wc -l) back"

python3 comp_dji.py full _work/ov4k

DUR=$(python3 -c 'import json;D=json.load(open("edl.json"));print(int(D["total_out"]*D["fps"])/D["fps"])')
for pair in "final_mix.wav:audio_final_mix.wav" "voice.wav:audio_voz.wav" "sfx_only.wav:audio_efeitos.wav"; do
  ffmpeg -v error -y -i "${pair%%:*}" -af "atrim=0:$DUR" -c:a pcm_s24le "$OUT/${pair##*:}"
done
cp _work/plate_10bit.mp4 "$OUT/plate_10bit_sem_texto.mp4"
cp _work/texto_legendas_CapCut_ProRes4444.mov "$OUT/texto_legendas_CapCut_ProRes4444.mov"
ffmpeg -v error -y -i _work/final_h264_noaudio.mp4 -i "$OUT/audio_final_mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -movflags +faststart "$OUT/Dizer Nao a Clientes - Final (sem cor) H264.mp4"
ffmpeg -v error -y -i _work/final_10bit_noaudio.mp4 -i "$OUT/audio_final_mix.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -tag:v hvc1 -movflags +faststart "$OUT/Dizer Nao a Clientes - Final (sem cor) 10bit HEVC.mp4"
echo "ALL DONE"
ls -l "$OUT"
