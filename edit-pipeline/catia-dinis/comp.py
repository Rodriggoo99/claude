# "Cátia e Dinis": the cut arrives already graded, so the video itself is never re-encoded for delivery.
#   python3 comp.py preview <ovdir> <out.mp4>   1080p approval preview (his graded cut + blur segment + overlay)
#   python3 comp.py final <ovdir>               4K deliverables: ProRes 4444 text layer + blurred segment clip for the rule
import numpy as np, cv2, subprocess, sys, os

SRC = "/home/user/work/cd/src.mp4"
FPS, FPS_STR = 60.0, "60"
N = int(round(58.4 * FPS))
BLUR = (43.80, 44.10, 49.34, 49.62)          # rule: my own shot blurred behind the strips
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]

def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def blur_k(t):
    a, b, c, d = BLUR
    return eio((t - a) / (b - a)) * (1 - eio((t - c) / (d - c)))

def soft(img, k, W, H, sigma=18):
    if k <= 0:
        return img
    s = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), sigma * W / 1080 / 4)
    s = cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(img.astype(np.float32) * (1 - k) + s.astype(np.float32) * k + 0.5, 0, 65535).astype(img.dtype)

def frames(W, H, ss=0.0, n=N, fmt="rgb48le"):
    bpp = 6 if fmt == "rgb48le" else 3
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{ss:.4f}", "-i", SRC, "-frames:v", str(n), "-vf",
                          f"scale={W}:{H}:flags=accurate_rnd+full_chroma_int", "-pix_fmt", fmt, "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, bufsize=W * H * bpp)
    dt = np.uint16 if bpp == 6 else np.uint8
    while True:
        b = p.stdout.read(W * H * bpp)
        if len(b) < W * H * bpp:
            break
        yield np.frombuffer(b, dt).reshape(H, W, 3)
    p.wait()

def overlay(path, W, H):
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if o is None:
        return None
    o = cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA if o.shape[2] == 4 else cv2.COLOR_BGR2RGBA)
    if o.shape[1] != W:
        o = cv2.resize(o, (W, H), interpolation=cv2.INTER_AREA)
    return o

if __name__ == "__main__" and sys.argv[1] == "preview":
    W, H = 1080, 1920
    ov, out = sys.argv[2], sys.argv[3]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", FPS_STR, "-i", "-",
                            "-i", "final_mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart"] + TAGS + [out],
                           stdin=subprocess.PIPE)
    for k, f in enumerate(frames(W, H, fmt="rgb24")):
        t = k / FPS
        f = soft(f, blur_k(t), W, H)
        o = overlay(f"{ov}/front/f_{k:05d}.png", W, H)
        if o is not None and o[:, :, 3].any():
            a = o[:, :, 3:4].astype(np.float32) / 255
            f = (o[:, :, :3] * a + f * (1 - a) + 0.5).astype(np.uint8)
        enc.stdin.write(f.tobytes())
        if k % 600 == 0:
            print("frame", k, flush=True)
    enc.stdin.close(); enc.wait(); print("preview done", enc.returncode)

if __name__ == "__main__" and sys.argv[1] == "final":
    W, H = 2160, 3840
    ov = sys.argv[2]
    os.makedirs("_work", exist_ok=True)
    # 1) text layer ProRes 4444 + alpha, straight from the PNGs (no video underneath)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", FPS_STR, "-i", f"{ov}/front/f_%05d.png", "-c:v", "prores_ks",
                    "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "8", "-qscale:v", "9", "-vendor", "apl0"] + TAGS +
                   ["_work/texto_legendas_CapCut_ProRes4444.mov"], check=True)
    # 2) blurred segment of his graded shot for the rule (drop it on a track above the video at BLUR[0])
    a, b, c, d = BLUR
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba64le", "-s", f"{W}x{H}", "-r", FPS_STR, "-i", "-",
                            "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-alpha_bits", "8", "-qscale:v", "5",
                            "-vendor", "apl0"] + TAGS + ["_work/segmento_desfocado_regra.mov"], stdin=subprocess.PIPE)
    k0, n = int(round(a * FPS)), int(round((d - a) * FPS))
    for i, f in enumerate(frames(W, H, ss=k0 / FPS, n=n)):
        t = (k0 + i) / FPS; k = blur_k(t)
        s = soft(f, 1.0, W, H)
        alpha = np.full((H, W, 1), int(k * 65535), np.uint16)             # fades in/out on its own alpha
        enc.stdin.write(np.dstack([s, alpha]).tobytes())
    enc.stdin.close(); enc.wait(); print("final done", enc.returncode)
