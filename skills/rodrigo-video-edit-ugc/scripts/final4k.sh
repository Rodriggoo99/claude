#!/bin/sh
# Final 4K deliverables (run from this scripts/ folder, after the 1080p preview was approved).
#   sh final4k.sh <src.mp4> <ov1080 dir with mask/ + matte/> <work dir> <audio dir with final_mix/voice/sfx_only.wav>
# Frame ranges come from edl.json (frame = round(t * 60)).
set -e
SRC=$1; OV1=$2; W=$3; AU=$4; P=$(cd "$(dirname "$0")" && pwd)
OV=$W/ov4k; OUT=$W/out; mkdir -p $OV $OUT
LAST=$(cd $P && python3 -c "from edl import N_OUT; print(N_OUT-1)")
DEPTH=$(cd $P && python3 -c "from edl import D, FPS; a,b=D.get('depth_window',[0,0]); print(int(a*FPS)-1, int(b*FPS)+2)")
[ -e $OV/mask ] || ln -s $OV1/mask $OV/mask          # blur masks / mattes are soft: 1080 upscaled is enough
[ -e $OV/matte ] || ln -s $OV1/matte $OV/matte
echo "[1/5] overlay 4K front"; node $P/render/render.js $OV/front front 2 frames 0 $LAST 3
echo "[2/5] overlay 4K depth"; [ "$DEPTH" = "-1 2" ] || node $P/render/render.js $OV/depth depth 2 frames $DEPTH 2
echo "[3/5] plate + finals";   (cd $P && SRC=$SRC python3 comp.py run 2 $OV $OUT/)
echo "[4/5] text layer";       (cd $P && python3 textlayer.py $OV $OUT)
echo "[5/5] mux audio"
cp $AU/final_mix.wav $OUT/audio_final_mix.wav; cp $AU/voice.wav $OUT/audio_voz.wav; cp $AU/sfx_only.wav $OUT/audio_efeitos.wav
ffmpeg -v error -y -i $OUT/final_h264.mp4 -i $OUT/audio_final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart "$OUT/final_H264.mp4"
ffmpeg -v error -y -i $OUT/final_10bit.mp4 -i $OUT/audio_final_mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -shortest -movflags +faststart "$OUT/final_10bit_HEVC.mp4"
echo DONE
