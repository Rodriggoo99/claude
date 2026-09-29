# Person matte (BiRefNet-portrait ONNX, the rembg model) for the depth word, on the warped 1080 plate.
#   python3 matte.py dump <dir> [t1,t2,...]   -> warped plate frames (all of depth_window, or given times)
#   python3 matte.py infer <dir> <outdir>     -> same-named 8-bit mattes
import sys, os, glob, numpy as np, cv2
from edl import D, FPS

def dump(d, tags=None):
    from comp import out_frames
    os.makedirs(d, exist_ok=True)
    w0, w1 = D["depth_window"]
    want = ({round(float(x) * FPS): f"t_{x}" for x in tags} if tags else
            {k: f"f_{k:05d}" for k in range(int(w0 * FPS) - 1, int(w1 * FPS) + 2)})
    for k, plate in out_frames(1):
        if k in want:
            cv2.imwrite(f"{d}/{want[k]}.png", cv2.cvtColor((plate / 257).astype(np.uint8), cv2.COLOR_RGB2BGR))
        if k >= max(want): break

def infer(d, outdir):
    import onnxruntime as ort
    os.makedirs(outdir, exist_ok=True)
    so = ort.SessionOptions(); so.enable_cpu_mem_arena = False; so.enable_mem_pattern = False
    s = ort.InferenceSession(os.path.expanduser("~/.rembg/models/birefnet-portrait/birefnet-portrait.onnx"), so,
                             providers=["CPUExecutionProvider"])
    name = s.get_inputs()[0].name
    mean, std = np.float32([0.485, 0.456, 0.406]), np.float32([0.229, 0.224, 0.225])
    for f in sorted(glob.glob(f"{d}/*.png")):
        out = os.path.join(outdir, os.path.basename(f))
        if os.path.exists(out): continue
        im = cv2.cvtColor(cv2.imread(f), cv2.COLOR_BGR2RGB)
        x = (cv2.resize(im, (1024, 1024), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 - mean) / std
        y = s.run(None, {name: x.transpose(2, 0, 1)[None]})[0][0, 0]
        y = 1 / (1 + np.exp(-y))
        m = cv2.resize(y, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_LINEAR)
        cv2.imwrite(out, np.clip(m * 255 + .5, 0, 255).astype(np.uint8))
        print("matte", os.path.basename(f), flush=True)

if __name__ == "__main__":
    if sys.argv[1] == "dump": dump(sys.argv[2], sys.argv[3].split(",") if len(sys.argv) > 3 else None)
    else: infer(sys.argv[2], sys.argv[3])
