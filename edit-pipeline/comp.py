import numpy as np, cv2, subprocess, sys, os

W, H, FPS = 2160, 3840, 60
AX, AY = 0.528 * W, 0.443 * H  # face centre: zooms stay anchored on the face
# 16-bit pipeline: deband removes the source's 8-bit contour steps on the flat wall
DEBAND = "format=yuv444p16le,deband=1thr=0.012:2thr=0.012:3thr=0.012:range=28:blur=1:coupling=1"
CONTRAST, SAT, WARM = 1.03, 1.06, (1.008, 1.0, 0.99)

def grade(f):
    x = f.astype(np.float32) * (1 / 65535)
    lum = x @ np.float32([0.0722, 0.7152, 0.2126])  # BGR
    x = lum[..., None] + (x - lum[..., None]) * SAT
    x = (x - 0.5) * CONTRAST + 0.5 + 0.004
    x *= np.float32([WARM[2], WARM[1], WARM[0]])
    return x
FF = "ffmpeg"

def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def zoom(t):
    if t < 4.60:   return 1.0 + 0.07 * eio(t / 4.4)                 # hook: slow push-in
    if 27.42 <= t < 30.74: return 1.12                               # "mas o problema..." punch-in
    if 38.52 <= t < 42.58: return 1.0 + 0.06 * eio((t - 38.52) / 3.9)  # "mas é a tal coisa" slow push
    if 51.88 <= t < 53.16: return 1.10                               # "comenta reunião" punch-in
    return 1.0

def warp(img, z):
    if abs(z - 1) < 1e-4:
        return img
    M = np.float32([[z, 0, AX * (1 - z)], [0, z, AY * (1 - z)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

_cache = {}
def overlay(path):
    if path in _cache:
        return _cache[path]
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # BGRA (BGR when fully opaque)
    if o.shape[2] == 3:
        o = np.dstack([o, np.full(o.shape[:2], 255, np.uint8)])
    a = o[:, :, 3]
    ys, xs = np.nonzero(a.max(axis=1))[0], np.nonzero(a.max(axis=0))[0]
    if len(ys) == 0:
        r = None
    else:
        y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
        fg = o[y0:y1, x0:x1, :3].astype(np.float32)
        al = (o[y0:y1, x0:x1, 3:4].astype(np.float32)) / 255.0
        r = (y0, y1, x0, x1, fg * al / 255.0, 1.0 - al)
    _cache.clear()
    _cache[path] = r
    return r

def composite(frame, ov):
    if ov is None:
        return frame
    y0, y1, x0, x1, fga, inv = ov
    frame[y0:y1, x0:x1] = fga + frame[y0:y1, x0:x1] * inv
    return frame

def dec_cmd(src, ss=None, n=None):
    c = [FF, "-v", "error"]
    if ss is not None: c += ["-ss", str(ss)]
    c += ["-i", src]
    if n: c += ["-frames:v", str(n)]
    c += ["-vf", DEBAND + ",scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int",
          "-pix_fmt", "bgr48le", "-f", "rawvideo", "-"]
    return c

def read_frames(src, **kw):
    n = W * H * 3 * 2
    p = subprocess.Popen(dec_cmd(src, **kw), stdout=subprocess.PIPE, bufsize=n * 2)
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield grade(np.frombuffer(b, np.uint16).reshape(H, W, 3))

if __name__ == "__main__" and sys.argv[1] == "still":
    # still <t> <overlay.png> <out.png>
    t = float(sys.argv[2])
    f = next(read_frames("raw.mp4", ss=t, n=1))
    f = composite(warp(f, zoom(t)), overlay(sys.argv[3]))
    cv2.imwrite(sys.argv[4], (np.clip(cv2.resize(f, (720, 1280), interpolation=cv2.INTER_AREA), 0, 1) * 255 + .5).astype(np.uint8))

if __name__ == "__main__" and sys.argv[1] == "full":
    ovdir, out = sys.argv[2], sys.argv[3]
    enc = subprocess.Popen([FF, "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr48le", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-vf", "scale=out_color_matrix=bt709:out_range=tv:in_range=pc:flags=accurate_rnd+full_chroma_int:sws_dither=bayer,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "film", "-x264-params", "aq-mode=3:aq-strength=1.0",
        "-maxrate", "80M", "-bufsize", "160M",
        "-profile:v", "high", "-level", "5.2", "-g", "120",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
        out], stdin=subprocess.PIPE)
    ss = float(os.environ.get("SS", 0)); nfr = int(os.environ.get("NF", 0)) or None
    for i, f in enumerate(read_frames("raw.mp4", ss=ss or None, n=nfr), start=int(round(ss * FPS))):
        t = i / FPS
        ov = overlay(os.path.join(ovdir, f"f_{i:05d}.png"))
        f = composite(warp(f, zoom(t)), ov)
        enc.stdin.write((np.clip(f, 0, 1) * 65535 + .5).astype(np.uint16).tobytes())
        if i % 300 == 0:
            print(f"frame {i} t={t:.1f}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("done", enc.returncode)
