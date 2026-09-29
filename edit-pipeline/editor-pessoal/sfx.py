# Sound design + mix for "Cátia e Dinis": voice (his graded cut's audio) to -14 LUFS, SFX under it, optional music bed ~19 dB under the voice.
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, "../dizer-nao")
from sfx_lib import *

EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.62, snd, pan)

# hook
ending_at(2.20, whoosh(0.36, 300, 4200, 0.62, lvl=-20)); at(2.20, impact(-13)); at(2.20, thud(-22))   # IA rises behind me
at(3.96, pop(1000, 420, lvl=-24))                                         # "uma frase"
# paper: 2 horas + the task list
at(4.66, whoosh(0.5, 300, 3200, 0.5, lvl=-21), -0.1); at(4.90, paper(0.45, -21)); at(5.02, paper(0.18, -23), -0.2)
at(6.34, scribble(0.42, -27), 0.1); at(6.60, scribble(0.4, -30), 0.4)
for i, t0 in enumerate((7.54, 8.54, 9.56, 10.62)):
    at(t0 - 0.08, paper(0.16, -24), -0.3 + 0.2 * i); at(t0 - 0.1, scribble(0.18, -31), -0.4); at(t0 + 0.3, scribble(0.16, -26), -0.4)
at(12.30, scribble(0.34, -26), 0.1)
at(13.00, whoosh(0.45, 3800, 450, 0.35, lvl=-24), 0.15); at(13.08, paper(0.35, -24))
# raw takes → folder → the prompt typed as I read it
at(14.10, whoosh(0.4, 400, 3000, 0.55, lvl=-25), -0.4)
for t0, pan in ((14.50, -0.5), (14.62, -0.35), (14.74, -0.2)):
    at(t0 + 0.2, pop(760, 300, lvl=-25), pan)
at(15.56, whoosh(0.4, 2400, 600, 0.4, lvl=-26), -0.3)
PT = [("Corta", 16.60), ("as", 16.90), ("pausas", 16.98), ("e", 17.50), ("os", 17.58), ("erros.", 17.70), ("Põe", 18.08), ("legendas", 18.26),
      ("no", 18.76), ("meu", 18.84), ("estilo,", 18.98), ("formato", 19.42), ("vertical,", 19.98), ("4K.", 20.58)]
for w, t0 in PT:
    for c in range(len(w)):
        at(t0 + c * 0.03, tick(-34 - (c % 3)), -0.35)                     # soft key clicks
at(20.94, pop(1300, 520, lvl=-22), -0.3); at(21.00, whoosh(0.4, 900, 5000, 0.5, lvl=-25), -0.2)
# 2 horas → 10 minutos
at(22.06, scribble(0.2, -27)); at(22.04, thud(-24))
# CTA
at(25.90, pop(1200, 480, lvl=-21)); at(26.00, whoosh(0.3, 600, 3200, 0.5, lvl=-27))
for c in range(8):
    at(26.30 + c * 0.04, tick(-31), 0.1)

def load(path):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                        capture_output=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)

def lufs(path):
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(m[m.rindex("{"):m.rindex("}") + 1])["input_i"])

def write(name, sig, limit=True):
    af = ["-af", "alimiter=limit=0.89:attack=2:release=60:level=false"] if limit else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-"] + af + ["-c:a", "pcm_s24le", name],
                   input=sig.tobytes(), check=True)

src = "/home/user/work/ep/src.mp4"
voice = load(src) * db(-14 - lufs(src))
N = len(voice)
fx = np.zeros_like(voice)
for t, s in EV:
    i = int(t * SR); n = min(len(s), N - i)
    if n > 0: fx[i:i + n] += s[:n]
mix = voice + fx

music_path = sys.argv[1] if len(sys.argv) > 1 else None
offset = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
if music_path:
    mu = load(music_path)[int(offset * SR):]
    mu = np.tile(mu, (int(np.ceil(N / len(mu))), 1))[:N] if len(mu) < N else mu[:N]
    # level: ~19 dB under the voice (measured on the approved "Dizer não" mix), gentle ducking under speech
    W = json.load(open("words.json"))
    env = np.zeros(N)
    for w in W: env[int(w["s"] * SR):int(w["e"] * SR)] = 1
    k = int(0.25 * SR); env = np.convolve(env, np.ones(k) / k, "same").clip(0, 1)
    rms = lambda a: np.sqrt(np.mean(a ** 2)) + 1e-12
    speech = env > 0.5
    g = rms(voice[speech]) / rms(mu) * db(-19)
    duck = db(-3) + (1 - db(-3)) * (1 - env)                              # -3 dB more while I speak
    # leveler: the track builds up later on, never let it get closer than 16 dB to the voice
    hop = int(0.5 * SR); ceil = rms(voice[speech]) * db(-16)
    lv = np.array([min(1.0, ceil / (g * rms(mu[i:i + hop]) + 1e-12)) for i in range(0, N, hop)])
    lv = np.convolve(np.repeat(lv, hop)[:N], np.ones(SR) / SR, "same")
    duck = duck * lv
    fade = np.minimum(1, np.minimum(np.arange(N) / (0.4 * SR), (N - np.arange(N)) / (1.2 * SR)))
    music = mu * g * (duck * fade)[:, None]
    # match the approved "Dizer não" mix: music bed at -32.7 LUFS integrated under a -14 LUFS voice
    write("_work/music_tmp.wav", music, limit=False)
    music *= db(-32.7 - lufs("_work/music_tmp.wav"))
    mix = mix + music
    write("audio_musica.wav", music, limit=False)
write("final_mix.wav", mix); write("sfx_only.wav", fx, limit=False); write("voice.wav", voice)
print("events", len(EV), "music", bool(music_path))
