# Sound design for "Dia 1 de Outubro" on the 1.1x output timeline, mixed under the -14 LUFS voice.
import sys, os, numpy as np, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dizer-nao"))
from sfx_lib import *
from scipy.signal import butter, sosfilt

def key(lvl=-27):                      # keyboard tap
    t = tt(0.06)
    x = sosfilt(butter(2, [1400, 4200], "band", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t / 0.006)
    x += 0.5 * np.sin(2 * np.pi * 180 * t) * np.exp(-t / 0.012)
    return norm(reverb(x, 0.08), lvl + rng.uniform(-1.5, 1.5))

def paper(dur=0.45, lvl=-24):          # sheet sliding
    t = tt(dur); u = t / dur
    env = np.sin(np.pi * np.clip(u, 0, 1)) ** 1.5 * (0.7 + 0.3 * rng.random(len(t)))
    x = sosfilt(butter(2, [700, 6500], "band", fs=SR, output="sos"), rng.standard_normal(len(t))) * env
    return norm(reverb(x, 0.1), lvl)

EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.85, snd, pan)

# ---- hook: 92 dragged in, digits rolling, impact on landing
ending_at(1.95, whoosh(0.55, 350, 4800, 0.85, lvl=-19), 0.25)
tk = 1.42
while tk < 1.92:
    at(tk, tick(-31 - 4 * (tk - 1.42)), 0.2); tk += 0.028 + 0.09 * ((tk - 1.42) / 0.5) ** 2
at(1.95, impact(-12))
at(4.72, scribble(0.22, -27), -0.1)                        # strike "desculpa"
at(5.08, whoosh(0.4, 3000, 500, 0.3, lvl=-30), 0.1)          # 92 leaves
# ---- list at the chest
for k, t in enumerate((5.32, 7.12, 8.89, 10.52)):
    at(t, pop(820 * 1.08 ** k, 320 * 1.08 ** k, lvl=-24), -0.15 + 0.1 * k); at(t + 0.05, tick(-31), 0.15)
at(11.36, whoosh(0.35, 1800, 500, 0.3, lvl=-31))
at(12.47, scribble(0.24, -26), 0.1)                          # strike "vídeos pessoais"
at(14.14, thud(-24))                                         # "isto"
at(14.50, whoosh(0.35, 3000, 600, 0.3, lvl=-31))
# ---- tempo -> prazo
at(17.16, scribble(0.18, -26), 0.1)
ending_at(18.42, whoosh(0.28, 600, 4200, 0.7, lvl=-27)); at(18.42, pop(1300, 520, lvl=-25), 0.15)
at(18.50, scribble(0.28, -28), 0.2)
at(22.24, tick(-30))
# ---- "o primeiro a cair"
at(26.96, whoosh(0.34, 2600, 280, 0.25, 0.9, lvl=-26), 0.1); at(27.22, thud(-27))
at(27.258, whoosh(0.22, 700, 3000, 0.6, lvl=-30))            # punch-in "então"
# ---- calendar screen
at(28.90, paper(0.42, -22), -0.1); at(28.92, whoosh(0.45, 300, 3200, 0.4, lvl=-23))
at(29.62, whoosh(0.4, 500, 2600, 0.6, lvl=-30))
for c in range(14):
    at(29.88 + c * 0.03, tick(-34 - (c % 3)), -0.3 + c * 0.045)
at(30.22, pop(900, 380, lvl=-23), -0.3); at(30.30, scribble(0.26, -27), -0.3)
at(30.36, whoosh(0.62, 250, 2200, 0.8, 0.9, lvl=-27), 0.1)  # the 92 days fill
at(30.98, scribble(0.26, -27), 0.3)
at(31.60, tick(-29), 0.3)
at(31.90, paper(0.32, -24), -0.2); at(32.24, scribble(0.24, -30), 0.1)
at(33.38, paper(0.36, -25), 0.1); at(33.40, whoosh(0.42, 3600, 450, 0.35, lvl=-24), 0.1)
# ---- CTA: comment "já foste"
at(40.47, pop(1250, 520, lvl=-21)); at(40.56, whoosh(0.3, 500, 2400, 0.6, lvl=-30), 0.1)
for i in range(8):
    at(40.78 + i * 0.065, key(-27), 0.1)
at(41.36, pop(1500, 700, lvl=-24), 0.1); at(41.40, chime(-31))
at(42.08, whoosh(0.35, 2800, 600, 0.3, lvl=-32))

voice = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                     capture_output=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
fx = np.zeros_like(voice)
for t, s in EV:
    i = int(t * SR); n = min(len(s), len(fx) - i)
    if n > 0: fx[i:i + n] += s[:n]
mix = voice + fx
print("voice peak %.1f dB, sfx peak %.1f dB, mix peak %.1f dB" % tuple(20 * np.log10(np.abs(a).max()) for a in (voice, fx, mix)))
od = sys.argv[2]
for name, sig in (("final_mix.wav", mix), ("audio_efeitos.wav", fx)):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "alimiter=limit=0.89:attack=2:release=60:level=false", "-c:a", "pcm_s24le", os.path.join(od, name)],
                   input=sig.tobytes(), check=True)
print("events", len(EV))
