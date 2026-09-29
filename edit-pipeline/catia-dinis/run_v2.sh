#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
python3 sfx.py /home/user/work/cd/music/cinematic.mp3 3.0
./run_preview.sh
