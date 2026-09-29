#!/bin/bash
# 4K complete version (Rodrigo asked for the full video only, no separate plate/text/stems): overlay at 2x, composite, mux mix.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
W=/home/user/work/dia1
OUT="/home/user/claude/videos/Dia 1 de Outubro"
N=$(python3 -c "import json;print(json.load(open('$HERE/edl.json'))['n_out'])")
mkdir -p "$W/ov4k"
node "$HERE/render/render.js" "$W/ov4k" frames 60 "$N" 4 2
echo "overlay4k done $(ls "$W/ov4k" | wc -l)"
python3 "$HERE/comp.py" full "$W/ov4k" "$OUT/Dia 1 de Outubro - Completo 4K.mp4" 2>&1 | grep -v -i warn
echo "FINALIZE DONE"
ls -la "$OUT"
