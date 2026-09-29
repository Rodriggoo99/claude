#!/bin/sh
# Final 4K deliverables.  sh final4k.sh <src.mp4> <ov1080 dir (mask + matte)> <work dir> <audio dir>
set -e
SRC=$1; OV1=$2; W=$3; AU=$4; P=$(cd "$(dirname "$0")" && pwd)
OV=$W/ov4k; OUT=$W/out; mkdir -p $OV $OUT
[ -e $OV/mask ] || ln -s $OV1/mask $OV/mask          # blur masks / mattes are soft: 1080 upscaled is enough
[ -e $OV/matte ] || ln -s $OV1/matte $OV/matte
echo "[1/5] overlay 4K front"; node $P/render/render.js $OV/front front 2 frames 0 1541 3
echo "[2/5] overlay 4K depth"; node $P/render/render.js $OV/depth depth 2 frames 725 818 2
echo "[3/5] plate + finals";   (cd $P && SRC=$SRC python3 comp.py run 2 $OV $OUT/)
echo "[4/5] text layer";       (cd $P && python3 textlayer.py $OV $OUT)
echo "[5/5] mux audio"
cp $AU/final_mix.wav $OUT/audio_final_mix.wav; cp $AU/voice.wav $OUT/audio_voz.wav; cp $AU/sfx_only.wav $OUT/audio_efeitos.wav
ffmpeg -v error -y -i $OUT/final_h264.mp4 -i $OUT/audio_final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart "$OUT/final_H264.mp4"
ffmpeg -v error -y -i $OUT/final_10bit.mp4 -i $OUT/audio_final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart "$OUT/final_10bit_HEVC.mp4"
echo DONE
