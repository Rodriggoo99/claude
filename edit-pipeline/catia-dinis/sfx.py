# Sound design + mix for "Cátia e Dinis": voice (his graded cut's audio) to -14 LUFS, SFX under it, optional music bed ~19 dB under the voice.
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, "../dizer-nao")
from sfx_lib import *

EV = []
def at(t, snd, pan=0.0): EV.append((t, mono_to_st(snd, pan)))
def ending_at(t, snd, pan=0.0): at(t - len(snd) / SR * 0.62, snd, pan)

at(0.34, pop(900, 350, lvl=-25))                                          # "+1 mês"
ending_at(3.42, whoosh(0.34, 500, 5200, 0.62, lvl=-20)); at(3.42, impact(-12)); at(3.42, thud(-21))   # "0€"
at(3.62, scribble(0.34, -26), 0.2)                                        # circle
# calendar paper
at(13.30, whoosh(0.5, 300, 3200, 0.5, lvl=-21), -0.1); at(13.52, paper(0.45, -21))
at(13.62, paper(0.18, -23), -0.2); at(14.50, paper(0.18, -23), 0.2)
at(13.78, scribble(0.55, -31), -0.1)                                      # grid
for i in range(14):
    at(14.62 + i * 0.13, scribble(0.12, -28 - (i % 3)), -0.5 + i / 13)   # X marks
at(15.28, scribble(0.24, -27), 0.1); at(16.90, paper(0.18, -24), 0.2)
at(18.92, whoosh(0.45, 3800, 450, 0.35, lvl=-24), 0.15); at(18.98, paper(0.35, -24))
# the rule over the blurred shot
at(43.62, whoosh(0.62, 350, 4200, 0.45, lvl=-21), -0.15); at(44.46, chime(-29))
at(45.26, paper(0.18, -23), -0.2); at(46.08, paper(0.18, -23), 0.2); at(47.30, paper(0.18, -23), -0.1)
at(46.70, scribble(0.22, -26), -0.3); at(47.86, scribble(0.30, -25), 0.2); at(48.10, scribble(0.2, -26), -0.3)
at(49.28, whoosh(0.5, 3800, 450, 0.35, lvl=-24), 0.15)
# CTA
at(51.76, pop(1200, 480, lvl=-21))
for i in range(7):
    at(52.30 + i * 0.045, tick(-28), -0.3 + i * 0.1)
at(52.36, impact(-15))

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

src = "/home/user/work/cd/src.mp4"
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
