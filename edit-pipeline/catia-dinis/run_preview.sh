#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
rm -rf _work/ov1080
(cd render && DSF=1 node render.js ../_work/ov1080 60 58.4 4)
echo "overlay: $(ls _work/ov1080/front | wc -l)"
mkdir -p "../../videos/Catia e Dinis"
python3 comp.py preview _work/ov1080 "../../videos/Catia e Dinis/Catia e Dinis - PREVIEW 1080p.mp4"
echo PREVIEW DONE
