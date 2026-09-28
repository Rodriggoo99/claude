# Frame-by-frame safe-margin check on the real letter pixels (alpha >= 160) of the overlay, screen paper hidden.
# Reels/TikTok safe area on 1080x1920: top 250, bottom 480, right 120, left 60. Measure frames are rendered at 0.5x.
import cv2, numpy as np, glob, sys, os
d = sys.argv[1]; S = 0.5
L, T, R, B = 60 * S, 250 * S, (1080 - 120) * S, (1920 - 480) * S
TRANSIT = [(1.40, 1.97), (28.94, 29.30), (33.40, 33.72)]  # elements sliding in/out of frame
bad = []
for p in sorted(glob.glob(os.path.join(d, "m_*.png"))):
    k = int(p[-9:-4]); t = k / 60
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)[:, :, 3]
    ys, xs = np.nonzero(a >= 160)
    if not len(ys): continue
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if x0 < L or x1 > R or y0 < T or y1 > B:
        if not any(a0 <= t <= a1 for a0, a1 in TRANSIT):
            bad.append((k, t, x0 / S, x1 / S, y0 / S, y1 / S))
print("frames outside safe area:", len(bad))
for b in bad[:0]: print("  f%05d t=%.2f  x %.0f-%.0f  y %.0f-%.0f" % b)
runs = []
for b in bad:
    if runs and b[0] == runs[-1][1] + 1: runs[-1][1] = b[0]; runs[-1][2].append(b)
    else: runs.append([b[0], b[0], [b]])
for a, z, bs in runs:
    print("  t %.2f-%.2f  x %.0f-%.0f  y %.0f-%.0f" % (a / 60, z / 60, min(x[2] for x in bs), max(x[3] for x in bs), min(x[4] for x in bs), max(x[5] for x in bs)))
