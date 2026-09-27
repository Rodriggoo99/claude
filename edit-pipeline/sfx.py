# Synthesised sound design, mixed under the normalised voice -> audio_sfx.m4a
import numpy as np, subprocess
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng = np.random.default_rng(7)
db = lambda x: 10 ** (x / 20)
tt = lambda d: np.arange(int(d * SR)) / SR

def svf_bp(x, fc, q):
    """Band-pass with per-sample cutoff (Chamberlin state-variable filter)."""
    y = np.zeros_like(x); lp = bp = 0.0; d = 1.0 / q
    f = 2 * np.sin(np.pi * np.minimum(fc, SR / 6) / SR)
    for i in range(len(x)):
        hp = x[i] - lp - d * bp
        bp += f[i] * hp
        lp += f[i] * bp
        y[i] = bp
    return y

def norm(x, peak_db):
    return x / (np.abs(x).max() + 1e-9) * db(peak_db)

IR = None
def reverb(x, wet=0.18, dec=0.35):
    global IR
    if IR is None:
        t = tt(1.2)
        IR = rng.standard_normal(len(t)) * np.exp(-t / dec)
        IR = sosfilt(butter(2, 5000, "low", fs=SR, output="sos"), IR)
        IR /= np.sqrt((IR ** 2).sum())
    wetsig = fftconvolve(x, IR)[: len(x) + len(IR) - 1]
    out = np.zeros(len(wetsig)); out[: len(x)] += x * (1 - wet)
    return out + wetsig * wet

def whoosh(dur, f0, f1, peak=0.6, q=1.4, lvl=-20):
    t = tt(dur); u = t / dur
    fc = f0 * (f1 / f0) ** u
    env = np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak)) ** 1.6)
    x = svf_bp(rng.standard_normal(len(t)), fc, q) * env
    return norm(reverb(x, 0.2), lvl)

def pop(f0=1100, f1=380, dur=0.12, lvl=-22):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t / 0.018)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.028)
    x[:96] += rng.standard_normal(96) * 0.25 * np.linspace(1, 0, 96)
    return norm(reverb(x, 0.12), lvl)

def tick(lvl=-27):
    t = tt(0.05)
    x = np.sin(2 * np.pi * 2600 * t) * np.exp(-t / 0.008)
    x += sosfilt(butter(2, [2500, 6000], "band", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t / 0.003) * 0.6
    return norm(reverb(x, 0.1), lvl)

def impact(lvl=-11):
    t = tt(1.1)
    f = 42 + 58 * np.exp(-t / 0.09)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.38)
    body = sosfilt(butter(2, 380, "low", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t / 0.05) * 1.6
    click = sosfilt(butter(2, 2500, "high", fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t / 0.004) * 0.35
    x = np.tanh(1.6 * (sub + body + click))
    return norm(reverb(x, 0.22, 0.5), lvl)

def chime(lvl=-22):
    t = tt(1.2); x = np.zeros(len(t))
    for f, off, g in ((1318.5, 0.0, 1.0), (1975.5, 0.075, 0.8)):
        tn = np.clip(t - off, 0, None); on = t >= off
        env = np.minimum(tn / 0.004, 1) * np.exp(-tn / 0.42) * on
        x += g * env * (np.sin(2 * np.pi * f * tn) + 0.22 * np.sin(4 * np.pi * f * tn) + 0.06 * np.sin(6 * np.pi * f * tn))
    return norm(reverb(x, 0.25, 0.5), lvl)

def thud(lvl=-17):
    t = tt(0.35)
    f = 105 + 90 * np.exp(-t / 0.03)
    x = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / 0.075)
    x = sosfilt(butter(2, 900, "low", fs=SR, output="sos"), x)
    return norm(reverb(x, 0.12), lvl)

def scribble(dur=0.75, lvl=-29):
    t = tt(dur); env = np.zeros(len(t)); s = 0.0
    while s < dur - 0.05:
        d = rng.uniform(0.06, 0.13); m = (t >= s) & (t < s + d)
        env[m] = np.sin(np.pi * (t[m] - s) / d) * rng.uniform(0.6, 1.0); s += d * rng.uniform(0.9, 1.15)
    x = sosfilt(butter(2, [1800, 5200], "band", fs=SR, output="sos"), rng.standard_normal(len(t))) * env
    return norm(x, lvl)

def mono_to_st(x, pan=0.0):
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    return np.stack([x * l * 1.41, x * r * 1.41], 1)

# ---- timeline (seconds). "end" anchors put the sound's peak/end on the cut.
EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.62, snd, pan)

at(3.40, impact())                                                    # "0€"
for t_in, t_out in ((14.40, 19.22), (32.50, 38.30), (45.12, 48.62)):  # graphics screens in/out
    at(t_in - 0.22, whoosh(0.62, 350, 4200, 0.45, lvl=-19), -0.15)
    at(t_out - 0.10, whoosh(0.5, 3800, 450, 0.35, lvl=-24), 0.15)
for k, t in enumerate((14.52, 15.28, 15.98, 16.66, 17.30)):          # meeting cards, rising pitch
    at(t, pop(900 * 1.12 ** k, 330 * 1.12 ** k, lvl=-23), -0.1 + 0.05 * k)
at(17.58, tick(-28))                                                   # progress bar
at(33.96, tick()); at(34.52, thud()); at(34.88, tick())                # "mesmo dia" timeline, "não."
at(35.80, pop(1000, 360, lvl=-23)); at(37.00, pop(1500, 600, lvl=-24), 0.2)
at(45.22, pop(800, 300, lvl=-25)); at(45.45, scribble())              # document + signature
at(46.08, chime())                                                     # ✓ diagnóstico
at(47.32, thud(-20))                                                   # ✗ solução
at(48.40, whoosh(0.28, 1800, 7000, 0.5, 1.2, lvl=-27), 0.2)            # strikethrough
for t in (27.42, 51.88):                                               # punch-in zooms
    ending_at(t, whoosh(0.32, 500, 5000, 0.62, lvl=-22))
    at(t, thud(-26))
at(52.30, pop(700, 260, lvl=-21)); at(52.30, chime(-27))               # "REUNIÃO"
at(38.52, whoosh(1.4, 200, 1200, 0.85, 0.9, lvl=-30))                  # soft swell into "mas é a tal coisa"

voice = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", "audio.m4a", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                     capture_output=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)
fx = np.zeros_like(voice)
for t, s in EV:
    i = int(t * SR); n = min(len(s), len(fx) - i)
    if n > 0: fx[i:i + n] += s[:n]
mix = voice + fx
print("voice peak %.1f dB, sfx peak %.1f dB, mix peak %.1f dB" % tuple(20 * np.log10(np.abs(a).max()) for a in (voice, fx, mix)))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "alimiter=limit=0.89:attack=2:release=60:level=false", "-c:a", "aac", "-b:a", "320k", "audio_sfx.m4a"],
               input=mix.astype(np.float64).tobytes(), check=True)
fx_only = fx / max(np.abs(fx).max(), 1e-9) * 0.5
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "sfx_only.wav"], input=fx_only.tobytes(), check=True)
print("events:", len(EV))
