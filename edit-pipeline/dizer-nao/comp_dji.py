# Cut + 1.1x speed + face-centred zooms + camera shake + depth-masked overlay, no colour changes (16-bit RGB round trip).
# PREVIEW=1 works at 1080x1920 (approval preview); default is 4K 2160x3840.
#   python3 comp_dji.py masks <ovdir>          person masks for frames that have a back (behind-me) layer
#   python3 comp_dji.py preview <ovdir> <out>  1080p preview (needs PREVIEW=1)
#   python3 comp_dji.py full <ovdir>           4K: plate 10-bit, final 10-bit + H264, text layer ProRes 4444 alpha
import numpy as np, cv2, subprocess, sys, os, json, math

D = json.load(open("edl.json"))
FPS, SPEED, SUBS = D["fps"], D["speed"], D["subs"]
PREVIEW = os.environ.get("PREVIEW") == "1"
W, H = (1080, 1920) if PREVIEW else (2160, 3840)
PX = W / 1080  # overlay CSS px -> output px
AX, AY = 0.555 * W, 0.445 * H  # face centre
N_OUT = int(D["total_out"] * FPS)
FF = "ffmpeg"
FPS_STR = "60000/1001"
MASKDIR = "_work/masks"

def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def zoom(t):  # output-timeline seconds
    if t < 2.16:              return 1.0 + 0.06 * eio(t / 2.1)            # hook push-in
    if 13.72 <= t < 14.30:    return 1.12                                 # "chega." punch-in
    if 16.68 <= t < 19.56:    return 1.0 + 0.06 * eio((t - 16.68) / 2.8)  # "melhor decisão" push-in
    if 24.48 <= t < 25.70:    return 1.10                                 # "guarda isto" punch-in
    return 1.0

# Landing shakes — the same formula lives in overlay.html (shake()), in 1080-space px.
SHAKES = ((0.46, 16.0), (13.74, 12.0))
def shake(t):
    for t0, amp in SHAKES:
        u = t - t0
        if 0 <= u < 0.4:
            e = math.exp(-u / 0.085)
            return amp * e * math.sin(2 * math.pi * 21 * u), 0.7 * amp * e * math.sin(2 * math.pi * 16 * u + 1.3), amp * e
    return 0.0, 0.0, 0.0

def warp(img, t):
    z = zoom(t)
    dx, dy, a = shake(t)
    z *= 1 + 2.2 * a / 1080  # tiny extra zoom so the shake never shows an edge
    if abs(z - 1) < 1e-5 and a == 0:
        return img
    M = np.float32([[z, 0, AX * (1 - z) + dx * PX], [0, z, AY * (1 - z) + dy * PX]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def read_png(path):
    if not os.path.exists(path):
        return None
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # Chromium writes fully opaque frames (full-screen graphics) as RGB
    o = cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA if o.shape[2] == 4 else cv2.COLOR_BGR2RGBA)
    if o.shape[1] != W:
        o = cv2.resize(o, (W, H), interpolation=cv2.INTER_AREA if o.shape[1] > W else cv2.INTER_CUBIC)
    return o

def person_mask(k):
    m = cv2.imread(f"{MASKDIR}/m_{k:05d}.png", 0)
    if m is None:
        return None
    if m.shape[1] != W:
        m = cv2.resize(m, (W, H), interpolation=cv2.INTER_CUBIC)
    return m.astype(np.float32) / 255.0

def text_layer(ovdir, k):
    """Front layer over the back layer with the person cut out -> RGBA float (premultiplied rgb 0..1, alpha 0..1)."""
    fr, bk = read_png(f"{ovdir}/front/f_{k:05d}.png"), read_png(f"{ovdir}/back/f_{k:05d}.png")
    rgb = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W, 1), np.float32)
    if bk is not None and bk[:, :, 3].any():
        m = person_mask(k)
        a = bk[:, :, 3:4].astype(np.float32) / 255 * (1 - (m[:, :, None] if m is not None else 0))
        rgb = bk[:, :, :3].astype(np.float32) / 255 * a; al = a
    if fr is not None and fr[:, :, 3].any():
        a = fr[:, :, 3:4].astype(np.float32) / 255
        rgb = fr[:, :, :3].astype(np.float32) / 255 * a + rgb * (1 - a); al = a + al * (1 - a)
    return rgb, al

def composite(frame16, rgb, al):
    if not al.any():
        return frame16
    out = rgb * 65535 + frame16.astype(np.float32) * (1 - al)
    return np.clip(out + 0.5, 0, 65535).astype(np.uint16)

def seg_frames(s):
    n = s["f_out"] - s["f_in"]
    sc = f"scale={W}:{H}:" if PREVIEW else "scale="
    cmd = [FF, "-v", "error", "-ss", f'{(s["f_in"] - 0.5) / FPS:.6f}', "-i", "dji.MP4", "-frames:v", str(n),
           "-vf", sc + "in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int",
           "-pix_fmt", "rgb48le", "-f", "rawvideo", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * 6)
    got = 0
    while got < n:
        b = p.stdout.read(W * H * 6)
        if len(b) < W * H * 6:
            break
        got += 1
        yield np.frombuffer(b, np.uint16).reshape(H, W, 3)
    p.stdout.close(); p.wait()
    if got < n:
        print("WARN short segment", s["id"], got, n, flush=True)

def out_frames():
    """Yields (k, t, plate16) on the 1.1x output timeline."""
    k = 0
    for j, f in enumerate(f for s in SUBS for f in seg_frames(s)):
        if k >= N_OUT:
            break
        if j != round(k * SPEED):
            continue
        t = k / FPS
        yield k, t, warp(f, t)
        k += 1

YUV10 = "scale=out_color_matrix=bt709:out_range=tv:in_range=pc:flags=accurate_rnd+full_chroma_int"
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]

def encoder(out, kind):
    base = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", FPS_STR, "-i", "-"]
    if kind == "plate":
        v = ["-vf", YUV10 + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", "4",
             "-x265-params", "log-level=error:aq-mode=3:no-sao=1:psy-rd=1.0", "-tag:v", "hvc1"]
    elif kind == "x265":
        v = ["-vf", YUV10 + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", "14",
             "-x265-params", "log-level=error:aq-mode=3:no-sao=1", "-tag:v", "hvc1"]
    elif kind == "preview":
        v = ["-vf", YUV10 + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
             "-profile:v", "high", "-g", "120"]
    else:
        v = ["-vf", YUV10 + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
             "-tune", "film", "-x264-params", "aq-mode=3", "-profile:v", "high", "-level", "5.2", "-g", "120"]
    return subprocess.Popen(base + v + TAGS + [out], stdin=subprocess.PIPE)

def prores_alpha(out):
    return subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba64le", "-s", f"{W}x{H}", "-r", FPS_STR,
                             "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                             "-alpha_bits", "16", "-vendor", "apl0"] + TAGS + [out], stdin=subprocess.PIPE)

if __name__ == "__main__" and sys.argv[1] == "masks":
    # Person masks at 1080x1920 on the transformed plate, only where a back layer exists.
    from rembg import new_session, remove
    assert PREVIEW, "masks are computed at 1080 (run with PREVIEW=1) and upscaled for 4K"
    sess = new_session("u2net_human_seg")
    os.makedirs(MASKDIR, exist_ok=True)
    need = {int(f[2:7]) for f in os.listdir(f"{sys.argv[2]}/back")}
    for k, t, plate in out_frames():
        if k not in need or os.path.exists(f"{MASKDIR}/m_{k:05d}.png"):
            continue
        rgb8 = (plate / 257).astype(np.uint8)
        m = np.array(remove(rgb8, session=sess, only_mask=True))
        m = cv2.GaussianBlur(m, (0, 0), 0.8)
        cv2.imwrite(f"{MASKDIR}/m_{k:05d}.png", m)
    print("masks", len(os.listdir(MASKDIR)))

if __name__ == "__main__" and sys.argv[1] == "still":  # still <t> <ovdir> <out.jpg>
    ovdir, want = sys.argv[3], [float(x) for x in sys.argv[2].split(",")]
    ks = {round(x * FPS): x for x in want}
    for k, t, plate in out_frames():
        if k in ks:
            f = composite(plate, *text_layer(ovdir, k))
            cv2.imwrite(sys.argv[4].replace("#", f"{ks[k]:05.2f}"), cv2.cvtColor((f / 257).astype(np.uint8), cv2.COLOR_RGB2BGR))
        if k > max(ks):
            break

if __name__ == "__main__" and sys.argv[1] == "preview":
    ovdir, out = sys.argv[2], sys.argv[3]
    enc = encoder(out, "preview")
    for k, t, plate in out_frames():
        enc.stdin.write(composite(plate, *text_layer(ovdir, k)).tobytes())
        if k % 300 == 0:
            print(f"frame {k}/{N_OUT}", flush=True)
    enc.stdin.close(); enc.wait(); print("preview done", enc.returncode)

if __name__ == "__main__" and sys.argv[1] == "full":
    ovdir = sys.argv[2]
    encs = [encoder("_work/plate_10bit.mp4", "plate"), encoder("_work/final_10bit_noaudio.mp4", "x265"),
            encoder("_work/final_h264_noaudio.mp4", "x264")]
    pr = prores_alpha("_work/texto_legendas_CapCut_ProRes4444.mov")
    for k, t, plate in out_frames():
        rgb, al = text_layer(ovdir, k)
        final = composite(plate, rgb, al)
        encs[0].stdin.write(plate.tobytes())
        fb = final.tobytes(); encs[1].stdin.write(fb); encs[2].stdin.write(fb)
        straight = np.where(al > 1e-4, rgb / np.maximum(al, 1e-4), 0)  # un-premultiply for ProRes
        pr.stdin.write(np.clip(np.dstack([straight, al]) * 65535 + 0.5, 0, 65535).astype(np.uint16).tobytes())
        if k % 300 == 0:
            print(f"out frame {k}/{N_OUT} t={t:.1f}", flush=True)
    for e in encs + [pr]:
        e.stdin.close()
    for e in encs + [pr]:
        e.wait()
    print("done", [e.returncode for e in encs + [pr]])
