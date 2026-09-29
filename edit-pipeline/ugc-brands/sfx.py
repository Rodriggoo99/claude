# Sound design for the UGC (EN) edit, on the 1.0x timeline (Rodrigo's cut already runs at 1.1x).
# Synthesised SFX mixed discreetly under Rodrigo's untouched voice -> final_mix.wav, voice.wav, sfx_only.wav
import numpy as np, subprocess, sys
import pyloudnorm as pyln
from sfx_lib import *

SRC = sys.argv[1] if len(sys.argv) > 1 else "/home/user/work/ugc1/video.mp4"
EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.62, snd, pan)

def shutter(lvl=-24):
    t = tt(0.16)
    n = sosfilt(butter(2, [1200, 7000], "band", fs=SR, output="sos"), rng.standard_normal(len(t)))
    x = n * (np.exp(-t / 0.006) + 0.7 * np.exp(-np.maximum(t - 0.055, 0) / 0.01) * (t > 0.055))
    return norm(reverb(x, 0.1), lvl)

# --- hook (captions in the top wall space)
at(0.00, whoosh(0.35, 400, 3800, 0.3, lvl=-27), 0.1)                     # I'LL SAY THIS lands
ending_at(0.88 + 0.22, whoosh(0.30, 600, 4800, 0.62, lvl=-27), 0.1)        # LAST TIME
ending_at(2.44 + 0.22, whoosh(0.30, 600, 4800, 0.62, lvl=-26), -0.1)       # FOLLOWERS
at(2.75, whoosh(0.22, 1800, 6500, 0.5, 1.2, lvl=-27), 0.2)                 # strike
ending_at(3.52 + 0.22, whoosh(0.32, 500, 5000, 0.62, lvl=-23))             # THIS
at(3.82, impact(-14))
# --- biggest brands
ending_at(5.17 + 0.22, whoosh(0.28, 700, 4500, 0.62, lvl=-29), 0.15)
ending_at(5.43 + 0.22, whoosh(0.28, 700, 4500, 0.62, lvl=-30), -0.15)
# --- IG profile card
at(6.28, whoosh(0.5, 350, 4000, 0.5, lvl=-22), -0.1); at(6.62, thud(-25))
at(6.86, whoosh(0.45, 300, 1800, 0.8, 0.9, lvl=-30))                       # zoom into followers
at(7.39, scribble(0.36, -28), 0.15)                                        # marker ring
at(7.60, pop(1300, 520, lvl=-22), 0.25)                                    # <1K FOLLOWERS chip
at(8.78, whoosh(0.4, 3600, 450, 0.35, lvl=-27))                            # card out
# --- UGC / audience / quality / content
ending_at(8.95 + 0.22, whoosh(0.26, 800, 4800, 0.62, lvl=-30))
ending_at(10.58 + 0.22, whoosh(0.3, 600, 4800, 0.62, lvl=-27))
at(10.98, whoosh(0.22, 1800, 6500, 0.5, 1.2, lvl=-27), -0.2)               # strike AUDIENCE
ending_at(12.10 + 0.30, whoosh(0.42, 300, 5200, 0.7, lvl=-21), 0.2)        # QUALITY dragged in behind the head
at(12.40, impact(-12))
ending_at(14.45 + 0.22, whoosh(0.3, 600, 4800, 0.62, lvl=-26))             # 3 THINGS
# --- brief card
at(15.20, whoosh(0.5, 350, 4000, 0.5, lvl=-23), 0.1); at(15.52, thud(-26))
for k, (rv, tk) in enumerate(((15.69, 16.08), (17.18, 18.17), (19.76, 21.14))):
    at(rv, tick(-30), -0.2 + 0.2 * k)
    at(tk, pop(900 * 1.12 ** k, 380 * 1.12 ** k, lvl=-22), 0.1)
at(20.75, tick(-31), 0.2)
at(21.20, chime(-30))                                                      # 3/3 done
at(22.22, whoosh(0.4, 3600, 450, 0.35, lvl=-27))                           # card out
# --- callback
ending_at(22.66 + 0.22, whoosh(0.3, 500, 5000, 0.62, lvl=-24)); at(22.95, thud(-22))
ending_at(23.58 + 0.22, whoosh(0.28, 700, 4500, 0.62, lvl=-28), 0.1)
at(23.91, whoosh(0.22, 1800, 6500, 0.5, 1.2, lvl=-27), 0.2)
# --- save
at(24.20, whoosh(0.35, 500, 3500, 0.5, lvl=-27)); at(24.49, pop(1200, 500, lvl=-21)); at(24.56, chime(-29))
at(25.56, shutter(-25))                                                    # hand hits the lens

# Voice = Rodrigo's audio as sent: native 44.1 kHz, no speed change, no EQ / compression / limiter —
# only one flat gain so the file sits at -14 LUFS.
# Only the synthesised SFX are resampled (48k -> 44.1k) and summed underneath.
from scipy.signal import resample_poly
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate,channels",
                        "-of", "csv=p=0", SRC], capture_output=True, text=True).stdout.strip().split(",")
VSR, VCH = int(probe[0]), int(probe[1])
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-f", "f32le", "-"], capture_output=True).stdout
voice = np.frombuffer(raw, np.float32).reshape(-1, VCH).astype(np.float64)
if VCH == 1: voice = np.repeat(voice, 2, 1)
L0 = pyln.Meter(VSR).integrated_loudness(voice)
GAIN_DB = -14 - L0                     # one flat gain for the whole file (no EQ / compression / limiting)
voice *= 10 ** (GAIN_DB / 20)
print(f"voice {VSR} Hz, {L0:.2f} LUFS -> flat {GAIN_DB:+.2f} dB -> -14 LUFS")
fx48 = np.zeros((int(len(voice) / VSR * SR) + SR, 2))
for t, snd in EV:
    i = int(t * SR); n = min(len(snd), len(fx48) - i)
    if n > 0: fx48[i:i + n] += snd[:n]
g = np.gcd(VSR, SR)
fx = resample_poly(fx48, VSR // g, SR // g, axis=0)[:len(voice)]
mix = voice + fx
pk = lambda a: 20 * np.log10(np.abs(a).max() + 1e-12)
print("peaks dBFS: voice %.2f, sfx %.2f, mix %.2f" % (pk(voice), pk(fx), pk(mix)))
assert np.abs(mix).max() < 0.999, "mix would clip - lower the SFX, never touch the voice"
for name, sig in (("final_mix.wav", mix), ("voice.wav", voice), ("sfx_only.wav", fx)):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(VSR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", name],
                   input=sig.tobytes(), check=True)
print("events", len(EV), "mix LUFS %.2f" % pyln.Meter(VSR).integrated_loudness(mix))
