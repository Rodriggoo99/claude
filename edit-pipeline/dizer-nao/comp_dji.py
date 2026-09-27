# Cut + 1.1x speed + face-centred zooms + overlay, no colour changes (16-bit RGB round trip).
import numpy as np, cv2, subprocess, sys, os, json

D = json.load(open("edl.json"))
FPS, SPEED, SUBS = D["fps"], D["speed"], D["subs"]
W, H = 2160, 3840
AX, AY = 0.555 * W, 0.445 * H  # face centre
FF = "ffmpeg"
FPS_STR = "60000/1001"

def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def zoom(t):  # output-timeline seconds
    if t < 2.16:              return 1.0 + 0.06 * eio(t / 2.1)            # hook push-in
    if 13.72 <= t < 14.30:    return 1.12                                 # "chega." punch-in
    if 16.68 <= t < 19.56:    return 1.0 + 0.06 * eio((t - 16.68) / 2.8)  # "melhor decisão" push-in
    if 24.48 <= t < 25.70:    return 1.10                                 # "guarda isto" punch-in
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
    o = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if o.shape[2] == 3:
        o = np.dstack([o, np.full(o.shape[:2], 255, np.uint8)])
    o = cv2.cvtColor(o, cv2.COLOR_BGRA2RGBA)
    a = o[:, :, 3]
    ys, xs = np.nonzero(a.max(axis=1))[0], np.nonzero(a.max(axis=0))[0]
    r = None
    if len(ys):
        y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
        al = o[y0:y1, x0:x1, 3:4].astype(np.float32) / 255.0
        r = (y0, y1, x0, x1, o[y0:y1, x0:x1, :3].astype(np.float32) * 257.0 * al, 1.0 - al)
    _cache.clear(); _cache[path] = r
    return r

def composite(frame, ov):
    if ov is None:
        return frame
    y0, y1, x0, x1, fga, inv = ov
    out = frame.copy()
    out[y0:y1, x0:x1] = np.clip(fga + frame[y0:y1, x0:x1].astype(np.float32) * inv + 0.5, 0, 65535).astype(np.uint16)
    return out

def seg_frames(s):
    n = s["f_out"] - s["f_in"]
    cmd = [FF, "-v", "error", "-ss", f'{(s["f_in"] - 0.5) / FPS:.6f}', "-i", "dji.MP4", "-frames:v", str(n),
           "-vf", "scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int",
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

def cut_frames():
    for s in SUBS:
        yield from seg_frames(s)

def src_time_for(t_out):
    j = round(t_out * FPS * SPEED); acc = 0
    for s in SUBS:
        n = s["f_out"] - s["f_in"]
        if j < acc + n:
            return (s["f_in"] + j - acc) / FPS
        acc += n
    return SUBS[-1]["f_out"] / FPS

YUV10 = "scale=out_color_matrix=bt709:out_range=tv:in_range=pc:flags=accurate_rnd+full_chroma_int"
TAGS = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]

def encoder(out, kind):
    base = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", FPS_STR, "-i", "-"]
    if kind == "x265":
        v = ["-vf", YUV10 + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", "14",
             "-x265-params", "log-level=error:aq-mode=3:no-sao=1", "-tag:v", "hvc1"]
    else:
        v = ["-vf", YUV10 + ":sws_dither=bayer,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
             "-tune", "film", "-x264-params", "aq-mode=3", "-profile:v", "high", "-level", "5.2", "-g", "120"]
    return subprocess.Popen(base + v + TAGS + [out], stdin=subprocess.PIPE)

if __name__ == "__main__" and sys.argv[1] == "still":
    t = float(sys.argv[2]); ts = src_time_for(t)
    b = subprocess.run([FF, "-v", "error", "-ss", f"{ts:.4f}", "-i", "dji.MP4", "-frames:v", "1", "-vf",
                        "scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int",
                        "-pix_fmt", "rgb48le", "-f", "rawvideo", "-"], capture_output=True).stdout
    f = np.frombuffer(b, np.uint16).reshape(H, W, 3)
    f = composite(warp(f, zoom(t)), overlay(sys.argv[3]))
    small = cv2.resize(f, (720, 1280), interpolation=cv2.INTER_AREA)
    cv2.imwrite(sys.argv[4], cv2.cvtColor((small / 257).astype(np.uint8), cv2.COLOR_RGB2BGR))

if __name__ == "__main__" and sys.argv[1] == "plate":
    n_out = int(D["total_out"] * FPS)
    base = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb48le", "-s", f"{W}x{H}", "-r", FPS_STR, "-i", "-"]
    enc = subprocess.Popen(base + ["-vf", YUV10 + ",format=yuv420p10le", "-c:v", "libx265", "-preset", "medium", "-crf", "4",
          "-x265-params", "log-level=error:aq-mode=3:no-sao=1:psy-rd=1.0", "-tag:v", "hvc1"] + TAGS + [sys.argv[2]], stdin=subprocess.PIPE)
    k = 0
    for j, f in enumerate(cut_frames()):
        if k >= n_out: break
        if j != round(k * SPEED): continue
        enc.stdin.write(warp(f, zoom(k / FPS)).tobytes()); k += 1
    enc.stdin.close(); enc.wait(); print("plate done", k, enc.returncode)

if __name__ == "__main__" and sys.argv[1] == "full":
    ovdir = sys.argv[2]
    n_out = int(D["total_out"] * FPS)
    encs = [encoder("plate_10bit.mp4", "x265"), encoder("final_10bit_noaudio.mp4", "x265"), encoder("final_h264_noaudio.mp4", "x264")]
    k = 0
    for j, f in enumerate(cut_frames()):
        if k >= n_out:
            break
        if j != round(k * SPEED):
            continue
        t = k / FPS
        plate = warp(f, zoom(t))
        final = composite(plate, overlay(os.path.join(ovdir, f"f_{k:05d}.png")))
        encs[0].stdin.write(plate.tobytes())
        fb = final.tobytes()
        encs[1].stdin.write(fb); encs[2].stdin.write(fb)
        if k % 300 == 0:
            print(f"out frame {k}/{n_out} t={t:.1f}", flush=True)
        k += 1
    for e in encs:
        e.stdin.close()
    for e in encs:
        e.wait()
    print("done frames", k, [e.returncode for e in encs])
