"""Montagem final: frames + mix -> MP4 H.264/AAC 1080x1920 30 fps, sem texto/legenda/marca-d'água.
  python3 -I lib/montagem.py <frames_dir> <mix.wav> <saida.mp4> [--fps 30] [--w 1080] [--h 1920]
Faz: upscale Lanczos (quando os frames foram renderizados em resolução menor), nitidez leve, vinheta suave,
grão de filme discreto, normalização de loudness para -14 LUFS (padrão de Shorts/Reels/TikTok).
"""
import subprocess, sys, argparse, os, json

ap = argparse.ArgumentParser()
ap.add_argument("frames")
ap.add_argument("audio")
ap.add_argument("out")
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--w", type=int, default=1080)
ap.add_argument("--h", type=int, default=1920)
ap.add_argument("--crf", type=int, default=19)
a = ap.parse_args()

# 1ª passada do loudnorm (medição)
m = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.audio, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                    "-f", "null", "-"], capture_output=True, text=True).stderr
js = json.loads(m[m.rfind("{"): m.rfind("}") + 1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
vf = (f"scale={a.w}:{a.h}:flags=lanczos,unsharp=5:5:0.6:5:5:0.0,"
      f"vignette=angle=PI/5:mode=forward,noise=alls=2:allf=t,format=yuv420p")
cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(a.fps),
       "-i", os.path.join(a.frames, "f_%04d.jpg"), "-i", a.audio,
       "-vf", vf, "-af", ln + ",aresample=48000,alimiter=limit=0.74:level=false",
       "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-profile:v", "high", "-pix_fmt", "yuv420p",
       "-r", str(a.fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
       "-metadata", "title=", a.out]
print(" ".join(cmd))
subprocess.run(cmd, check=True)
print("OK", a.out)
