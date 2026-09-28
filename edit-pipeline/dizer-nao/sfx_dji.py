# Sound design for the DJI "dizer não" edit, on the 1.1x output timeline
import numpy as np, subprocess
from sfx_lib import *

EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.62, snd, pan)

# Hook: giant "NÃO" dragged in from the right behind me, lands at 0.46 with a shake
at(0.02, whoosh(0.46, 5200, 700, 0.55, 1.1, lvl=-18), 0.35)            # drag (right -> centre)
at(0.46, impact(-12)); at(0.46, thud(-20))
at(1.44, impact(-15))                                                  # "MAIS DINHEIRO"
# Editorial screen: paper slides up over me, strips slap on, chart drawn by hand
at(4.66, whoosh(0.5, 300, 3200, 0.5, lvl=-21), -0.1); at(4.90, paper(0.45, -21))
at(5.04, paper(0.18, -23), -0.2); at(6.06, paper(0.18, -23), 0.2)       # strips
at(6.48, scribble(0.28, -27), 0.1)                                      # marker on "preço"
at(7.00, scribble(0.38, -30), -0.2)                                     # axes
at(7.30, scribble(0.58, -28), -0.1); at(7.60, paper(0.16, -25), 0.3)    # clients line + label
at(7.92, scribble(0.42, -26), 0.1); at(8.20, paper(0.16, -25), 0.1)     # revenue line (marker) + label
at(8.34, scribble(0.28, -27), 0.3); at(8.44, thud(-25))                 # circle
at(9.30, whoosh(0.45, 3800, 450, 0.35, lvl=-24), 0.15); at(9.36, paper(0.35, -24))
# "chega." slams in behind me
ending_at(13.74, whoosh(0.32, 500, 5000, 0.62, lvl=-21)); at(13.74, impact(-12))
# "mais vezes NÃO": 4 words popping behind me
for k, (t, pan) in enumerate(((15.56, -0.5), (15.68, 0.0), (15.80, 0.55), (15.92, -0.6))):
    at(t, pop(700 * 1.08 ** k, 280 * 1.08 ** k, lvl=-22 - 0.8 * k), pan)
at(16.56, whoosh(0.4, 3000, 500, 0.35, lvl=-28))
# "a melhor decisão" swell
at(17.4, whoosh(1.4, 200, 1300, 0.85, 0.9, lvl=-29))
# Quote screen
at(21.30, whoosh(0.62, 350, 4200, 0.45, lvl=-20), -0.15)
at(21.60, chime(-27))
at(23.94, scribble(0.34, -27), 0.2)                                     # circle "melhor"
at(24.20, whoosh(0.5, 3800, 450, 0.35, lvl=-24), 0.15)
# "Guarda isto" punch-in + save icon
ending_at(24.48, whoosh(0.3, 500, 5000, 0.62, lvl=-23)); at(24.48, thud(-27))
at(24.86, pop(1200, 500, lvl=-21)); at(24.94, chime(-29))
# Visual CTA: hand comes to the lens and covers it (end frame)
ending_at(29.02, whoosh(0.5, 300, 2200, 0.7, 0.9, lvl=-24)); at(29.02, thud(-21))

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
