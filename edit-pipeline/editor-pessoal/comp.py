# "Editor pessoal": pre-cut, graded 4K60 H.264 source; graphics on top, the giant "IA" cut behind my silhouette.
#   python3 comp.py masks <ovdir>               person masks (1080) for frames with a back layer
#   python3 comp.py preview <ovdir> <out.mp4>   1080p approval preview
#   python3 comp.py full <ovdir> <out.mp4>      finished 4K file (graded cut + graphics + final mix)
import numpy as np, cv2, subprocess, sys, os

SRC = "/home/user/work/ep/src.mp4"
FPS, FPS_STR = 60.0, "60"
MASKDIR = "_work/masks"
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]

def frames(W, H):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=accurate_rnd+full_chroma_int",
                          "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE, bufsize=W * H * 3)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()

def png(path, W, H):
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if o is None:
        return None
    o = cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA if o.shape[2] == 4 else cv2.COLOR_BGR2RGBA)
    return cv2.resize(o, (W, H), interpolation=cv2.INTER_AREA) if o.shape[1] != W else o

def blend(f, o, cut=None):
    ys, xs = np.nonzero(o[::8, ::8, 3])
    if not len(ys):
        return f
    H, W = f.shape[:2]
    y0, y1, x0, x1 = ys.min() * 8, min(H, ys.max() * 8 + 8), xs.min() * 8, min(W, xs.max() * 8 + 8)
    a = o[y0:y1, x0:x1, 3:4].astype(np.float32) / 255
    if cut is not None:
        a = a * (1 - cut[y0:y1, x0:x1, None])
    f = f.copy()
    f[y0:y1, x0:x1] = (o[y0:y1, x0:x1, :3] * a + f[y0:y1, x0:x1] * (1 - a) + 0.5).astype(np.uint8)
    return f

def compose(f, ov, k, W, H):
    b = png(f"{ov}/back/f_{k:05d}.png", W, H)
    if b is not None:
        m = cv2.imread(f"{MASKDIR}/m_{k:05d}.png", 0)
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255 if m is not None else None
        f = blend(f, b, m)
    o = png(f"{ov}/front/f_{k:05d}.png", W, H)
    return blend(f, o) if o is not None else f

def encoder(out, W, H, crf):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", FPS_STR, "-i", "-",
                             "-i", "final_mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                             "-profile:v", "high", "-pix_fmt", "yuv420p", "-g", "120", "-c:a", "aac", "-b:a", "320k", "-shortest",
                             "-movflags", "+faststart"] + TAGS + [out], stdin=subprocess.PIPE)

if __name__ == "__main__" and sys.argv[1] == "masks":
    from rembg import new_session, remove
    sess = new_session("u2net_human_seg"); os.makedirs(MASKDIR, exist_ok=True)
    need = {int(f[2:7]) for f in os.listdir(f"{sys.argv[2]}/back")}
    for k, f in enumerate(frames(1080, 1920)):
        if k in need and not os.path.exists(f"{MASKDIR}/m_{k:05d}.png"):
            m = np.array(remove(f, session=sess, only_mask=True))
            cv2.imwrite(f"{MASKDIR}/m_{k:05d}.png", cv2.GaussianBlur(m, (0, 0), 0.8))
    print("masks", len(os.listdir(MASKDIR)))

if __name__ == "__main__" and sys.argv[1] in ("preview", "full"):
    W, H = (1080, 1920) if sys.argv[1] == "preview" else (2160, 3840)
    ov, out = sys.argv[2], sys.argv[3]
    enc = encoder(out, W, H, 21 if sys.argv[1] == "preview" else 15)
    for k, f in enumerate(frames(W, H)):
        enc.stdin.write(compose(f, ov, k, W, H).tobytes())
        if k % 600 == 0:
            print("frame", k, flush=True)
    enc.stdin.close(); enc.wait(); print(sys.argv[1], "done", enc.returncode)
