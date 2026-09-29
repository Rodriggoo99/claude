# Shared timeline maths (zoom, shake) for comp.py; writes shake.json for the overlay renderer.
import json, math, os
D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "edl.json")))
FPS, SPEED, N_OUT = D["fps"], D["speed"], D["out_frames"]

def eio(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def zoom(t):
    for z in D.get("zooms", []):
        if z["t0"] <= t < z["t1"]:
            if "ramp" in z:  # quick punch-in
                return 1 + (z["z0"] - 1) * eio((t - z["t0"]) / z["ramp"])
            return z["z0"] + (z["z1"] - z["z0"]) * eio((t - z["t0"]) / (z["t1"] - z["t0"]))
    return 1.0

def shake(t):
    """Decaying camera shake in 1080-space px after each hero landing."""
    dx = dy = 0.0
    for t0, a in D.get("shakes", []):
        u = t - t0
        if 0 <= u < 0.3:
            env = a * (1 - u / 0.3) ** 2
            dx += env * math.sin(u * 2 * math.pi * 17)
            dy += env * 0.7 * math.cos(u * 2 * math.pi * 13)
    return round(dx, 2), round(dy, 2)

def in_win(t, w):
    return w[0] <= t < w[1]

if __name__ == "__main__":
    json.dump([shake(k / FPS) for k in range(N_OUT)], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "shake.json"), "w"))
    print("shake.json", N_OUT)
