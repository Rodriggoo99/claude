# 1.1x + face-centred zooms + camera shake + frosted-glass blur + overlay. No colour changes (16-bit RGB round trip).
#   python3 comp.py still <t> <out.png>            (1080 preview still, overlay rendered on the fly)
#   python3 comp.py run <scale 1|2> <ovdir> <outprefix>
# ovdir holds front/, depth/ (+ matte/), mask/ PNG sequences named f_00000.png at the matching scale.
import numpy as np, cv2, subprocess, sys, os, json
from edl import D, FPS, SPEED, N_OUT, zoom, shake, in_win

SRC = os.environ.get("SRC", "video.mp4")   # the source clip (set SRC=...)
FF = "ffmpeg"
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
IN_RGB = "scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int"
OUT_YUV = "scale=out_color_matrix=bt709:out_range=tv:in_range=pc:flags=accurate_rnd+full_chroma_int"

def dims(scale):
    return 1080 * scale, 1920 * scale

def warp(img, z, sh, scale):
    W, H = img.shape[1], img.shape[0]
    ax, ay = D["face"][0] * W, D["face"][1] * H
    if abs(z - 1) < 1e-4 and sh == (0, 0):
        return img
    M = np.float32([[z, 0, ax * (1 - z) + sh[0] * scale], [0, z, ay * (1 - z) + sh[1] * scale]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def frost(img, mask):
    """Blur the plate under the glass cards (mask 0..1 float, same size)."""
    if mask is None:
        return img
    H, W = img.shape[:2]
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
    sig = 22 * (W / 1080) / 4
    small = cv2.GaussianBlur(small, (0, 0), sig)
    big = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    m = mask[..., None]
    return np.clip(img.astype(np.float32) * (1 - m) + big * m + 0.5, 0, 65535).astype(np.uint16)

def read_rgba(path):
    if not os.path.exists(path):
        return None
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if o is None:
        return None
    if o.shape[2] == 3:
        o = np.dstack([o, np.full(o.shape[:2], 255, np.uint8)])
    return cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA)

def over(top, bot):
    """Premultiplied 'over' of two straight-alpha RGBA uint8 images -> straight RGBA uint8."""
    if top is None: return bot
    if bot is None: return top
    ta, ba = top[..., 3:4] / 255.0, bot[..., 3:4] / 255.0
    a = ta + ba * (1 - ta)
    c = (top[..., :3] * ta + bot[..., :3] * ba * (1 - ta)) / np.maximum(a, 1e-6)
    return np.dstack([np.clip(c + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8)

def text_layer(ovdir, k):
    """front OVER (depth word with the person cut out) -> the RGBA text layer delivered for CapCut."""
    f = read_rgba(f"{ovdir}/front/f_{k:05d}.png")
    d = read_rgba(f"{ovdir}/depth/f_{k:05d}.png")
    if d is not None:
        m = cv2.imread(f"{ovdir}/matte/f_{k:05d}.png", cv2.IMREAD_GRAYSCALE)
        if m is not None:
            m = cv2.resize(m, (d.shape[1], d.shape[0]), interpolation=cv2.INTER_LINEAR)
            d = d.copy(); d[..., 3] = (d[..., 3].astype(np.float32) * (1 - m / 255.0) + .5).astype(np.uint8)
    return over(f, d)

def composite(frame, ov):
    if ov is None:
        return frame
    a = ov[..., 3:4].astype(np.float32) / 255.0
    ys, xs = np.nonzero(a[..., 0].max(axis=1))[0], np.nonzero(a[..., 0].max(axis=0))[0]
    if not len(ys):
        return frame
    y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
    out = frame.copy()
    fg = ov[y0:y1, x0:x1, :3].astype(np.float32) * 257.0
    al = a[y0:y1, x0:x1]
    out[y0:y1, x0:x1] = np.clip(fg * al + frame[y0:y1, x0:x1].astype(np.float32) * (1 - al) + .5, 0, 65535).astype(np.uint16)
    return out

def src_frames(scale):
    W, H = dims(scale)
    vf = (f"scale={W}:{H}:flags=lanczos," if scale == 1 else "") + IN_RGB
    p = subprocess.Popen([FF, "-v", "error", "-i", SRC, "-vf", vf, "-pix_fmt", "rgb48le", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, bufsize=W * H * 6)
    n = W * H * 6
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint16).reshape(H, W, 3)
    p.stdout.close(); p.wait()

def out_frames(scale):
    """Yields (k, plate-before-frost) on the 1.1x output timeline."""
    k = 0
    for j, f in enumerate(src_frames(scale)):
        if k >= N_OUT: break
        while k < N_OUT and round(k * SPEED) == j:
            t = k / FPS
            yield k, warp(f, zoom(t), shake(t), scale)
            k += 1

def mask_for(ovdir, k, shape):
    t = k / FPS
    if not any(in_win(t, w) for w in D.get("glass_windows", [])):
        return None
    m = cv2.imread(f"{ovdir}/mask/f_{k:05d}.png", cv2.IMREAD_UNCHANGED)
    if m is None: return None
    m = (m[..., 3] if m.ndim == 3 and m.shape[2] == 4 else m).astype(np.float32) / 255.0
    if m.max() <= 0: return None
    if m.shape[:2] != shape[:2]:
        m = cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_LINEAR)
    return m

def enc(out, scale, kind):
    W, H = dims(scale)
    base = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if kind == "x265":
        v = ["-vf", OUT_YUV + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", "14",
             "-x265-params", "log-level=error:aq-mode=3:no-sao=1", "-tag:v", "hvc1"]
    elif kind == "plate":
        v = ["-vf", OUT_YUV + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", "6",
             "-x265-params", "log-level=error:aq-mode=3:no-sao=1:psy-rd=1.0", "-tag:v", "hvc1"]
    else:
        v = ["-vf", OUT_YUV + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
             "-crf", "17" if scale == 1 else "16", "-tune", "film", "-x264-params", "aq-mode=3", "-profile:v", "high", "-g", "120"]
    return subprocess.Popen(base + v + TAGS + [out], stdin=subprocess.PIPE)

if __name__ == "__main__" and sys.argv[1] == "run":
    scale, ovdir, pre = int(sys.argv[2]), sys.argv[3], sys.argv[4]
    kinds = [("final_h264.mp4", "x264")] if scale == 1 else [("plate_10bit.mp4", "plate"), ("final_10bit.mp4", "x265"), ("final_h264.mp4", "x264")]
    encs = [enc(pre + n, scale, kd) for n, kd in kinds]
    for k, plate in out_frames(scale):
        plate = frost(plate, mask_for(ovdir, k, plate.shape))
        ov = text_layer(ovdir, k)
        if ov is not None and ov.shape[:2] != plate.shape[:2]:
            ov = cv2.resize(ov, (plate.shape[1], plate.shape[0]), interpolation=cv2.INTER_LINEAR)
        final = composite(plate, ov).tobytes()
        if scale == 1:
            encs[0].stdin.write(final)
        else:
            encs[0].stdin.write(plate.tobytes()); encs[1].stdin.write(final); encs[2].stdin.write(final)
        if k % 120 == 0: print("frame", k, flush=True)
    for e in encs: e.stdin.close()
    for e in encs: e.wait()
    print("done", [e.returncode for e in encs])

if __name__ == "__main__" and sys.argv[1] == "stills":
    # python3 comp.py stills <ovdir-with-t_ files> <outdir> t1,t2,...  (1080, uses front/depth/mask t_<t>.png)
    ovdir, outdir, ts = sys.argv[2], sys.argv[3], [float(x) for x in sys.argv[4].split(",")]
    os.makedirs(outdir, exist_ok=True)
    want = {round(t * FPS): t for t in ts}
    for k, plate in out_frames(1):
        if k not in want: continue
        t = want[k]; tag = sys.argv[4].split(",")[ts.index(t)]
        mp = f"{ovdir}/mask/t_{tag}.png"
        m = cv2.imread(mp, cv2.IMREAD_UNCHANGED) if os.path.exists(mp) else None
        if m is not None:
            m = m[..., 3].astype(np.float32) / 255.0
            plate = frost(plate, m if m.max() > 0 else None)
        f = read_rgba(f"{ovdir}/front/t_{tag}.png"); d = read_rgba(f"{ovdir}/depth/t_{tag}.png")
        mt = f"{ovdir}/matte/t_{tag}.png"
        if d is not None and os.path.exists(mt):
            mm = cv2.imread(mt, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
            d = d.copy(); d[..., 3] = (d[..., 3] * (1 - mm)).astype(np.uint8)
        img = composite(plate, over(f, d))
        cv2.imwrite(f"{outdir}/s_{tag}.jpg", cv2.cvtColor((img / 257).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
        if len(want) == 1 or k == max(want): break
