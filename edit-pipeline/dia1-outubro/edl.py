# Builds the EDL for "Dia 1 de Outubro": the source already comes pre-cut (single take, jump cuts),
# so we only tighten the few pauses > 0.19 s at the existing cuts, then map words to the output timeline.
# Speed: 1.0 (Rodrigo: the 1.1x speed-up was noticeable on this one). The graphics/SFX/zoom timings were authored on the
# 1.1x timeline ("design_speed"); comp.py, render.js and sfx.py rescale them, so everything stays locked to the voice.
import json, numpy as np, subprocess

FPS, SPEED, DESIGN_SPEED, N = 60, 1.0, 1.1, 2970
SRC = "/home/user/work/dia1/src.mp4"
CUTS = [344, 654, 756, 856, 970, 1156, 1252, 1342, 1534, 1710, 1816, 1900, 2212, 2386, 2474, 2694]  # frame-diff jump cuts

sr = 48000
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                                 capture_output=True).stdout, np.float32)
hop = int(sr * 0.005)
db = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(hop * 4) / (hop * 4), "same")[::hop]) + 1e-9)

subs, start = [], 0
for c in CUTS:
    i = int(c / FPS / 0.005); a = b = i
    while a > 0 and db[a] < -30: a -= 1
    while b < len(db) - 1 and db[b] < -30: b += 1
    end_t, start_t = a * 0.005, b * 0.005
    out_f, in_f = c, c
    if start_t - end_t > 0.19:                      # tighten: keep 0.09 s tail + 0.05 s head
        out_f = min(c, int(np.ceil((end_t + 0.09) * FPS)))
        in_f = max(c, int(np.floor((start_t - 0.05) * FPS)))
    subs.append({"f_in": start, "f_out": out_f})
    start = in_f
subs.append({"f_in": start, "f_out": N})

acc = 0
for s in subs:
    s["cut_start"] = acc; acc += s["f_out"] - s["f_in"]
total_cut = acc
n_out = int(total_cut / SPEED)

def src2out(t):
    f = t * FPS
    for s in subs:
        if f < s["f_in"]:
            return (s["cut_start"]) / FPS / SPEED          # inside a removed gap -> snap to next clip
        if f <= s["f_out"]:
            return (s["cut_start"] + f - s["f_in"]) / FPS / SPEED
    return total_cut / FPS / SPEED

T = json.load(open("transcript.json"))
words = [{"w": w["w"].strip(), "s": round(src2out(w["s"]), 3), "e": round(src2out(w["e"]), 3)} for seg in T for w in seg["words"]]
json.dump({"fps": FPS, "speed": SPEED, "design_speed": DESIGN_SPEED, "subs": subs, "total_cut_frames": total_cut, "n_out": n_out,
           "total_out": n_out / FPS}, open("edl.json", "w"), indent=1)
json.dump(words, open("words_out.json", "w"), ensure_ascii=False, indent=0)
removed = N - total_cut
print(f"clips {len(subs)}  removed {removed} frames ({removed/FPS:.2f}s)  out {n_out} frames = {n_out/FPS:.2f}s")
print(" ".join(f'{w["w"]}@{w["s"]:.2f}' for w in words))
