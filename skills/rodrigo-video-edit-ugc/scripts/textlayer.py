# Text layer for CapCut: front overlay OVER the depth word with the person already cut out, as an RGBA PNG sequence,
# then ProRes 4444 (alpha) + a lighter PNG-in-MOV.   python3 textlayer.py <ovdir> <outdir>
import sys, os, subprocess, cv2
from comp import text_layer
from edl import N_OUT, FPS, D

ov, out = sys.argv[1], sys.argv[2]
seq = os.path.join(out, "textseq"); os.makedirs(seq, exist_ok=True)
w0, w1 = D["depth_window"]
for k in range(N_OUT):
    dst = f"{seq}/f_{k:05d}.png"
    if os.path.exists(dst): continue
    if os.path.exists(f"{ov}/depth/f_{k:05d}.png"):
        cv2.imwrite(dst, cv2.cvtColor(text_layer(ov, k), cv2.COLOR_RGBA2BGRA))   # merged, person cut out
    else:
        os.symlink(os.path.abspath(f"{ov}/front/f_{k:05d}.png"), dst)
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
src = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{seq}/f_%05d.png"]
subprocess.run(src + ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "-alpha_bits", "16", "-vendor", "apl0"]
               + TAGS + [f"{out}/texto_legendas_CapCut_ProRes4444.mov"], check=True)
subprocess.run(src + ["-c:v", "png", "-pix_fmt", "rgba"] + TAGS + [f"{out}/texto_legendas_alpha.mov"], check=True)
print("text layer done", N_OUT)
