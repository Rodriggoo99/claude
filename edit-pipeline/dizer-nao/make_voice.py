# Voice track from the DJI original on the EDL cuts: frame-accurate trims, 4 ms fades, 1.1x (pitch kept), -14 LUFS.
import json, subprocess

D = json.load(open("edl.json"))
FPS, SPEED = D["fps"], D["speed"]
parts, labels = [], []
for i, s in enumerate(D["subs"]):
    a, b = s["f_in"] / FPS, s["f_out"] / FPS
    parts.append(f"[0:a]atrim={a:.6f}:{b:.6f},asetpts=PTS-STARTPTS,afade=t=in:d=0.004,"
                 f"afade=t=out:st={b - a - 0.004:.6f}:d=0.004[a{i}]")
    labels.append(f"[a{i}]")
fc = ";".join(parts) + f";{''.join(labels)}concat=n={len(labels)}:v=0:a=1,atempo={SPEED}[cut]"

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "dji.MP4", "-filter_complex", fc, "-map", "[cut]",
                "-ac", "2", "-ar", "48000", "-c:a", "pcm_f32le", "_work/voice_raw.wav"], check=True)
# two-pass linear loudnorm to -14 LUFS
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", "_work/voice_raw.wav", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "_work/voice_raw.wav", "-af", ln + ",aresample=48000",
                "-c:a", "pcm_s24le", "voice.wav"], check=True)
print("voice.wav done, input", j["input_i"], "LUFS")
