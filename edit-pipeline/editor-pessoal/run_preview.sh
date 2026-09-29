#!/bin/bash
# 1080p approval preview: overlay → person masks for the "IA" frames → composite with the final mix
set -euo pipefail
cd "$(dirname "$0")"
rm -rf _work/ov1080
(cd render && DSF=1 node render.js ../_work/ov1080 60 29.13 4)
echo "overlay: $(ls _work/ov1080/front | wc -l) front, $(ls _work/ov1080/back | wc -l) back"
python3 comp.py masks _work/ov1080
mkdir -p "../../videos/Editor Pessoal"
python3 comp.py preview _work/ov1080 "../../videos/Editor Pessoal/Editor Pessoal - PREVIEW 1080p.mp4"
echo PREVIEW DONE
