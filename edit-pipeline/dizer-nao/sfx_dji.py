# Sound design for the DJI "dizer não" edit, on the 1.1x output timeline
import numpy as np, subprocess
from sfx_lib import *

EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.62, snd, pan)

at(1.40, impact(-13))                                                  # "MAIS DINHEIRO"
# Screen A: requests accepted at any price, then work vs revenue
at(4.70, whoosh(0.62, 350, 4200, 0.45, lvl=-19), -0.15)
for k, t in enumerate((5.10, 5.40, 5.70, 6.00, 6.30)):
    at(t, pop(900 * 1.1 ** k, 330 * 1.1 ** k, lvl=-24), -0.1 + 0.05 * k)
    at(t + 0.14, tick(-29), 0.2)                                        # "ACEITE" tag
for k in range(6):
    at(6.20 + k * 0.1, tick(-31 - k), 0.1)                              # prices ticking down
at(7.12, whoosh(0.4, 600, 3000, 0.5, lvl=-25))                          # bars in
at(7.50, whoosh(0.7, 300, 2600, 0.8, 0.9, lvl=-26), -0.2)               # work bar rising
at(8.42, whoosh(0.5, 2600, 250, 0.2, 0.9, lvl=-25), 0.2); at(8.46, thud(-23))  # revenue drops
at(8.70, whoosh(0.5, 3800, 450, 0.35, lvl=-25), 0.15)                   # screen out
# "CHEGA."
ending_at(13.72, whoosh(0.32, 500, 5000, 0.62, lvl=-21)); at(13.72, impact(-12))
# Floating card: more NO than YES
at(14.22, whoosh(0.45, 500, 3500, 0.5, lvl=-24))
for k, t in enumerate((15.56, 15.68, 15.80, 15.92)):
    at(t, pop(650, 260, lvl=-23 - k))
at(16.32, pop(1500, 650, lvl=-25), 0.2)
at(16.55, whoosh(0.4, 3000, 500, 0.35, lvl=-27))
# "a melhor decisão" swell
at(17.4, whoosh(1.4, 200, 1300, 0.85, 0.9, lvl=-29))
# Quote screen
at(21.30, whoosh(0.62, 350, 4200, 0.45, lvl=-20), -0.15)
at(21.60, chime(-27))
at(23.98, whoosh(0.3, 1800, 6000, 0.5, 1.2, lvl=-28), 0.2)              # underline "melhor"
at(24.20, whoosh(0.5, 3800, 450, 0.35, lvl=-24), 0.15)
# "Guarda isto" punch-in + save icon
ending_at(24.48, whoosh(0.3, 500, 5000, 0.62, lvl=-23)); at(24.48, thud(-27))
at(24.86, pop(1200, 500, lvl=-21)); at(24.94, chime(-29))

voice = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "voice.wav", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                     capture_output=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
fx = np.zeros_like(voice)
for t, s in EV:
    i = int(t * SR); n = min(len(s), len(fx) - i)
    if n > 0: fx[i:i + n] += s[:n]
mix = voice + fx
print("voice peak %.1f dB, sfx peak %.1f dB, mix peak %.1f dB" % tuple(20 * np.log10(np.abs(a).max()) for a in (voice, fx, mix)))
for name, sig in (("final_mix.wav", mix), ("sfx_only.wav", fx)):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "alimiter=limit=0.89:attack=2:release=60:level=false", "-c:a", "pcm_s24le", name],
                   input=sig.tobytes(), check=True)
print("events", len(EV))
