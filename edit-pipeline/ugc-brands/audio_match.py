# Match tone + level across Rodrigo's takes (his cut joins takes recorded at different mic distances).
# Per segment between jump cuts: smoothed EQ towards the median take spectrum, then loudness to -14 LUFS.
#   python3 audio_match.py <src video> <out voice_matched.wav>
import sys, subprocess, numpy as np, pyloudnorm as pyln
from scipy.signal import stft, istft

SR = 48000
CUTS = [0, 4.20, 8.533, 11.433, 13.567, 15.70, 16.667, 18.567, 21.867]   # jump cuts in the source (frame diff)
NFFT, HOP = 2048, 512
LO, HI = -10.0, 5.0

raw = subprocess.run(["ffmpeg", "-v", "error", "-i", sys.argv[1], "-vn", "-af", "aresample=48000:resampler=soxr:precision=28",
                      "-f", "f32le", "-ac", "2", "-"], capture_output=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2).T.astype(np.float64)
dur = x.shape[1] / SR
edges = CUTS + [dur]

def seg_spec(sig):
    """1/3-octave PSD relative to total power, per segment (dB)."""
    from scipy.signal import welch
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        fw, P = welch(sig[:, int(a * SR):int(b * SR)].mean(0), SR, nperseg=4096)
        tot = P.sum()
        out.append([10 * np.log10(P[(fw >= lo) & (fw < hi)].sum() / tot + 1e-15) for lo, hi in zip(bands[:-1], bands[1:])])
    return np.array(out)

bands = 100 * 2 ** (np.arange(0, 22) / 3)                            # 1/3 octave, 100 Hz .. 16 kHz
centers = np.sqrt(bands[:-1] * bands[1:])
y = x.copy()
for it in range(2):                                                  # second pass fixes the residual
    f, tf, Z = stft(y, SR, nperseg=NFFT, noverlap=NFFT - HOP)
    seg_of = np.searchsorted(np.array(edges[1:]), tf, side="right").clip(0, len(CUTS) - 1)
    spec = seg_spec(y)
    target = np.median(spec, 0)
    gains = []
    for s in range(len(CUTS)):
        g = np.clip(target - spec[s], LO, HI)
        g = np.where(centers > 7000, np.minimum(g, 3.0), g)          # never boost hiss much
        g = np.convolve(np.pad(g, 1, mode="edge"), np.ones(3) / 3, mode="valid")
        gains.append(10 ** (np.interp(np.log(np.maximum(f, 20)), np.log(centers), g) / 20))
        if it == 0:
            print(f"seg {edges[s]:5.2f}-{edges[s+1]:5.2f} EQ dB @ 250/1k/4k/10k:",
                  " ".join(f"{np.interp(np.log(v), np.log(centers), g):+5.1f}" for v in (250, 1000, 4000, 10000)))
    G = np.array(gains)[seg_of].T                                    # (bins, frames)
    k = np.ones(3) / 3                                               # ~32 ms crossfade across each cut
    G = np.apply_along_axis(lambda r: np.convolve(np.pad(r, 1, mode="edge"), k, mode="valid"), 1, G)
    _, y = istft(Z * G[None], SR, nperseg=NFFT, noverlap=NFFT - HOP)
    y = y[:, :x.shape[1]]

# loudness per segment -> -14 LUFS, gain ramps of 15 ms at the cuts
meter = pyln.Meter(SR, block_size=0.2)
env = np.ones(y.shape[1])
for s in range(len(CUTS)):
    a, b = int(edges[s] * SR), int(edges[s + 1] * SR)
    L = meter.integrated_loudness(y[:, a:b].T)
    env[a:b] = 10 ** ((-14 - L) / 20)
    print(f"seg {edges[s]:5.2f}-{edges[s+1]:5.2f} {L:6.1f} LUFS -> -14 ({-14 - L:+.1f} dB)")
r = int(0.015 * SR)
env = np.convolve(np.pad(env, r, mode="edge"), np.ones(2 * r + 1) / (2 * r + 1), mode="valid")
y *= env
print("overall", round(meter.integrated_loudness(y.T), 2), "LUFS, peak", round(20 * np.log10(np.abs(y).max()), 2), "dBFS")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_f32le", sys.argv[2]],
               input=y.T.astype(np.float64).tobytes(), check=True)
