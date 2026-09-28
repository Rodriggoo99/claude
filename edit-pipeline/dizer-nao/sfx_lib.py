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


def paper(dur=0.35, lvl=-24):
    """Paper sheet sliding / slapping: crackly band-passed noise with a soft attack."""
    t = tt(dur); u = t / dur
    env = np.minimum(u / 0.12, 1) * (1 - u) ** 1.4
    crackle = 1 + 0.9 * (rng.random(len(t)) < 0.004) * rng.uniform(1, 3, len(t))
    x = sosfilt(butter(2, [700, 6500], "band", fs=SR, output="sos"), rng.standard_normal(len(t))) * env * crackle
    return norm(reverb(x, 0.1), lvl)
