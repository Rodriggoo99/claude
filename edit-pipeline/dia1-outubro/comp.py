# Cut + 1.1x + face-centred zooms + impact shake + depth cut-out of the "92" + overlay. No colour changes (16-bit RGB round trip).
#   python3 comp.py still  <t_out> <front.png> [back.png] <out.jpg>
#   python3 comp.py preview <ovdir> <out.mp4>                     1080p H.264 + mix, for approval
#   python3 comp.py final   <ovdir> <outdir>                      4K: plate 10-bit, text layer (ProRes 4444 alpha), finals
#   python3 comp.py full    <ovdir> <out.mp4>                     4K complete version only (H.264 + mix)
import numpy as np, cv2, subprocess, sys, os, json, math

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "edl.json")))
FPS, SPEED, SUBS, N_OUT = D["fps"], D["speed"], D["subs"], D["n_out"]
DS = D.get("design_speed", SPEED)   # timeline the zoom/shake times below were authored on
SRC = os.environ.get("SRC", "/home/user/work/dia1/src.mp4")
FF = "ffmpeg"
FACE = (590 / 1080, 840 / 1920)  # face centre (fraction of frame)

def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def zoom(t):  # design-timeline seconds; zoom changes sit on the existing jump cuts
    if t < 5.212:              return 1.0 + 0.05 * eio(t / 1.95)                 # hook push-in, lands on "92"
    if 12.879 <= t < 14.606:   return 1.06                                       # "o que fica de fora é sempre isto"
    if 17.424 <= t < 18.818:   return 1.08                                       # "falta de prazo"
    if 27.258 <= t < 28.53:    return 1.07                                       # "então, a partir de hoje"
    if t >= 40.485:            return 1.0 + 0.06 * eio((t - 40.485) / 3.2)       # CTA slow push-in
    return 1.0

def shake(t):  # impact when the 92 lands (1080-scale px)
    u = t - 1.95
    if u < 0 or u > 0.4: return 0.0, 0.0
    a = 9.0 * math.exp(-u / 0.085)
    return a * math.sin(2 * math.pi * 21 * u), 0.7 * a * math.sin(2 * math.pi * 17 * u + 1.3)

def xform(t, W, H):
    td = t * SPEED / DS
    z = zoom(td); sx, sy = shake(td); k = W / 1080
    ax, ay = FACE[0] * W, FACE[1] * H
    return np.float32([[z, 0, ax * (1 - z) + sx * k], [0, z, ay * (1 - z) + sy * k]])

def warp(img, M, W, H):
    if abs(M[0, 0] - 1) < 1e-5 and abs(M[0, 2]) < 1e-3 and abs(M[1, 2]) < 1e-3:
        return img
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def read_rgba(path, W, H):
    if not path or not os.path.exists(path):
        return None
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    o = cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA)
    if o.shape[1] != W:
        o = cv2.resize(o, (W, H), interpolation=cv2.INTER_AREA)
    a = o[:, :, 3:4].astype(np.float32) / 255.0
    return o[:, :, :3].astype(np.float32) * 257.0 * a, a        # premultiplied 16-bit colour, alpha

# ---- person mask for the depth layer
_seg = None
def person_mask(plate16):
    global _seg
    from rembg import new_session, remove
    from PIL import Image
    if _seg is None:
        _seg = new_session("u2net_human_seg")
    H, W = plate16.shape[:2]
    small = cv2.resize(plate16, (1080, 1920), interpolation=cv2.INTER_AREA) if W != 1080 else plate16
    small8 = (small / 257).astype(np.uint8)
    m = np.asarray(remove(Image.fromarray(small8), session=_seg, only_mask=True), np.float32) / 255.0
    if W != 1080:
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    g = cv2.cvtColor((plate16 / 65535.0).astype(np.float32), cv2.COLOR_RGB2GRAY)
    return np.clip(guided(g, m, int(8 * W / 1080), 1e-3), 0, 1)

def guided(I, p, r, eps):
    bf = lambda x: cv2.boxFilter(x, -1, (2 * r + 1, 2 * r + 1))
    mI, mp = bf(I), bf(p)
    a = (bf(I * p) - mI * mp) / (bf(I * I) - mI * mI + eps)
    b = mp - a * mI
    return bf(a) * I + bf(b)

def text_layer(k, ovdir, plate, M, W, H):
    """Returns (premult colour, alpha) of the text layer for output frame k, depth already cut out."""
    f = read_rgba(os.path.join(ovdir, f"f_{k:05d}.png"), W, H)
    b = read_rgba(os.path.join(ovdir, f"b_{k:05d}.png"), W, H)
    if b is not None:
        sx, sy = M[0, 2] - FACE[0] * W * (1 - M[0, 0]), M[1, 2] - FACE[1] * H * (1 - M[1, 1])
        if abs(sx) > 1e-3 or abs(sy) > 1e-3:   # the 92 lives in the scene: it shakes with the plate
            T = np.float32([[1, 0, sx], [0, 1, sy]])
            b = (cv2.warpAffine(b[0], T, (W, H), flags=cv2.INTER_LINEAR),
                 cv2.warpAffine(b[1], T, (W, H), flags=cv2.INTER_LINEAR)[:, :, None])
        keep = (1.0 - person_mask(plate))[:, :, None]
        b = (b[0] * keep, b[1] * keep)
        if f is None:
            return b
        return f[0] + b[0] * (1 - f[1]), f[1] + b[1] * (1 - f[1])
    return f

def over(plate, lay):
    if lay is None:
        return plate
    c, a = lay
    return np.clip(c + plate.astype(np.float32) * (1 - a) + 0.5, 0, 65535).astype(np.uint16)

def decoder(s, W, H):
    n = s["f_out"] - s["f_in"]
    vf = f"scale={W}:{H}:in_color_matrix=bt709:in_range=tv:out_range=pc:flags=lanczos+accurate_rnd+full_chroma_int,format=rgb48le"
    cmd = [FF, "-v", "error", "-ss", f'{(s["f_in"] - 0.5) / FPS:.6f}', "-i", SRC, "-frames:v", str(n), "-vf", vf, "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 6)
    got = 0
    while got < n:
        buf = p.stdout.read(W * H * 6)
        if len(buf) < W * H * 6:
            break
        got += 1
        yield np.frombuffer(buf, np.uint16).reshape(H, W, 3)
    p.stdout.close(); p.wait()
    if got < n:
        print("WARN short segment", s, got, n, flush=True)

def out_frames(W, H):
    k = 0
    def cut():
        for s in SUBS:
            yield from decoder(s, W, H)
    for j, f in enumerate(cut()):
        if k >= N_OUT:
            break
        if j != round(k * SPEED):
            continue
        yield k, f
        k += 1

def src_frame_for(k):
    j = round(k * SPEED)
    for s in SUBS:
        n = s["f_out"] - s["f_in"]
        if j < s["cut_start"] + n:
            return s["f_in"] + j - s["cut_start"]
    return SUBS[-1]["f_out"] - 1

YUV10 = "scale=out_color_matrix=bt709:out_range=tv:in_range=pc:flags=accurate_rnd+full_chroma_int"
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
def raw_in(W, H, pix="rgb48le"):
    return [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", pix, "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]

if __name__ == "__main__" and sys.argv[1] == "still":
    t = float(sys.argv[2]); k = int(round(t * FPS)); W, H = 1080, 1920
    fi = src_frame_for(k)
    vf = f"scale={W}:{H}:in_color_matrix=bt709:in_range=tv:out_range=pc:flags=lanczos+accurate_rnd+full_chroma_int,format=rgb48le"
    buf = subprocess.run([FF, "-v", "error", "-ss", f"{(fi - 0.5) / FPS:.6f}", "-i", SRC, "-frames:v", "1", "-vf", vf, "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    f = np.frombuffer(buf, np.uint16).reshape(H, W, 3)
    M = xform(t, W, H); plate = warp(f, M, W, H)
    fr = read_rgba(sys.argv[3], W, H)
    bk = read_rgba(sys.argv[4], W, H) if len(sys.argv) > 5 else None
    if bk is not None:
        keep = (1.0 - person_mask(plate))[:, :, None]
        bk = (bk[0] * keep, bk[1] * keep)
        fr = bk if fr is None else (fr[0] + bk[0] * (1 - fr[1]), fr[1] + bk[1] * (1 - fr[1]))
    out = over(plate, fr)
    cv2.imwrite(sys.argv[-1], cv2.cvtColor((out / 257).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])

if __name__ == "__main__" and sys.argv[1] == "preview":
    ovdir, out = sys.argv[2], sys.argv[3]; W, H = 1080, 1920
    enc = subprocess.Popen(raw_in(W, H) + ["-i", os.environ.get("MIX", "/home/user/work/dia1/final_mix.wav"),
          "-vf", YUV10 + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-maxrate", "4.6M", "-bufsize", "9M",
          "-profile:v", "high", "-g", "120", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart"] + TAGS + [out], stdin=subprocess.PIPE)
    for k, f in out_frames(W, H):
        M = xform(k / FPS, W, H); plate = warp(f, M, W, H)
        enc.stdin.write(over(plate, text_layer(k, ovdir, plate, M, W, H)).tobytes())
        if k % 300 == 0: print("preview", k, "/", N_OUT, flush=True)
    enc.stdin.close(); enc.wait(); print("preview done", enc.returncode)

if __name__ == "__main__" and sys.argv[1] == "final":
    ovdir, od = sys.argv[2], sys.argv[3]; W, H = 2160, 3840
    os.makedirs(od, exist_ok=True)
    x265 = lambda crf: ["-vf", YUV10 + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", str(crf),
                        "-x265-params", "log-level=error:aq-mode=3:no-sao=1", "-tag:v", "hvc1"] + TAGS
    e_plate = subprocess.Popen(raw_in(W, H) + x265(6) + [os.path.join(od, "plate_10bit.mp4")], stdin=subprocess.PIPE)
    e_f10 = subprocess.Popen(raw_in(W, H) + x265(14) + [os.path.join(od, "final_10bit_noaudio.mp4")], stdin=subprocess.PIPE)
    e_264 = subprocess.Popen(raw_in(W, H) + ["-vf", YUV10 + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
          "-tune", "film", "-profile:v", "high", "-level", "5.2", "-g", "120"] + TAGS + [os.path.join(od, "final_h264_noaudio.mp4")], stdin=subprocess.PIPE)
    e_txt = subprocess.Popen(raw_in(W, H, "rgba64le") + ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
          "-alpha_bits", "16", "-vendor", "apl0"] + TAGS + [os.path.join(od, "texto_ProRes4444.mov")], stdin=subprocess.PIPE)
    for k, f in out_frames(W, H):
        M = xform(k / FPS, W, H); plate = warp(f, M, W, H)
        lay = text_layer(k, ovdir, plate, M, W, H)
        e_plate.stdin.write(plate.tobytes())
        fin = over(plate, lay).tobytes(); e_f10.stdin.write(fin); e_264.stdin.write(fin)
        if lay is None:
            rgba = np.zeros((H, W, 4), np.uint16)
        else:   # un-premultiply for the straight-alpha ProRes layer
            c, a = lay
            rgb = np.where(a > 1e-4, c / np.maximum(a, 1e-4), 0)
            rgba = np.dstack([np.clip(rgb + 0.5, 0, 65535), np.clip(a[:, :, 0] * 65535 + 0.5, 0, 65535)]).astype(np.uint16)
        e_txt.stdin.write(rgba.tobytes())
        if k % 120 == 0: print("final", k, "/", N_OUT, flush=True)
    for e in (e_plate, e_f10, e_264, e_txt):
        e.stdin.close()
    for e in (e_plate, e_f10, e_264, e_txt):
        e.wait()
    print("final done", [e.returncode for e in (e_plate, e_f10, e_264, e_txt)])

if __name__ == "__main__" and sys.argv[1] == "full":
    ovdir, out = sys.argv[2], sys.argv[3]; W, H = 2160, 3840
    enc = subprocess.Popen(raw_in(W, H) + ["-i", os.environ.get("MIX", "/home/user/work/dia1/final_mix.wav"),
          "-vf", YUV10 + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "film",
          "-profile:v", "high", "-level", "5.2", "-g", "120", "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart"] + TAGS + [out],
          stdin=subprocess.PIPE)
    for k, f in out_frames(W, H):
        M = xform(k / FPS, W, H); plate = warp(f, M, W, H)
        enc.stdin.write(over(plate, text_layer(k, ovdir, plate, M, W, H)).tobytes())
        if k % 150 == 0: print("full", k, "/", N_OUT, flush=True)
    enc.stdin.close(); enc.wait(); print("full done", enc.returncode)
