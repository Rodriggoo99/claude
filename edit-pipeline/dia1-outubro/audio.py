# Voice track: cut per EDL (3 ms crossfades at splices), 1.1x with pitch preserved, loudness -14 LUFS.
import json, numpy as np, subprocess
D = json.load(open("edl.json")); FPS = D["fps"]; SR = 48000
SRC = "/home/user/work/dia1/src.mp4"
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                                 capture_output=True).stdout, np.float32).reshape(-1, 2)
xf = int(0.003 * SR); parts = []
for s in D["subs"]:
    a = x[int(round(s["f_in"] / FPS * SR)): int(round(s["f_out"] / FPS * SR))].copy()
    r = np.linspace(0, 1, xf)[:, None]
    a[:xf] *= r; a[-xf:] *= r[::-1]
    parts.append(a)
cut = np.concatenate(parts)
fo = int(0.03 * SR); cut[-fo:] *= np.linspace(1, 0, fo)[:, None]   # source ends abruptly on "dezembro"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", f"atempo={D['speed']},loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:print_format=summary",
                "-ar", str(SR), "-c:a", "pcm_s24le", "voice_raw.wav"], input=cut.tobytes(), check=True)
# second pass with measured values for an accurate linear gain
m = subprocess.run(["ffmpeg", "-v", "info", "-i", "voice_raw.wav", "-af", "ebur128=peak=true", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
print([l for l in m.splitlines() if "I:" in l or "Peak:" in l][-3:])
