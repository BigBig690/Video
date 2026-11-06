"""Renderização a partir do projeto.blend.
  python3 -I lib/render.py <projeto.blend> stills <saida_dir> --at 1.2,3.4 [--pct 30] [--samples 8]
  python3 -I lib/render.py <projeto.blend> shots  <saida_dir> [--pct 30]      (1 still no meio de cada plano)
  python3 -I lib/render.py <projeto.blend> anim   <saida_dir> --from 0 --to 10 [--pct 100] [--samples 24] [--step 1]
"""
import sys, os, time, json, argparse
import bpy

ap = argparse.ArgumentParser()
ap.add_argument("blend")
ap.add_argument("mode")
ap.add_argument("out")
ap.add_argument("--at", default="")
ap.add_argument("--pct", type=int, default=100)
ap.add_argument("--samples", type=int, default=0)
ap.add_argument("--from", dest="t0", type=float, default=0)
ap.add_argument("--to", dest="t1", type=float, default=0)
ap.add_argument("--step", type=int, default=1)
ap.add_argument("--fmt", default="JPEG")
ap.add_argument("--engine", default="")
ap.add_argument("--threads", type=int, default=0)
a = ap.parse_args()

bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
sc = bpy.context.scene
FPS = sc.render.fps
sc.render.resolution_percentage = a.pct
if a.engine:
    sc.render.engine = a.engine
if a.samples:
    sc.eevee.taa_render_samples = a.samples
    sc.cycles.samples = a.samples
sc.render.threads_mode = "AUTO"
if a.threads:
    sc.render.threads_mode = "FIXED"
    sc.render.threads = a.threads
os.makedirs(a.out, exist_ok=True)


def F(t):
    return int(round(t * FPS)) + 1


def still(fr, path):
    sc.frame_set(fr)
    sc.render.filepath = path
    sc.render.image_settings.file_format = "PNG"
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"FRAME {fr} {time.time() - t:.1f}s -> {path}", flush=True)


if a.mode == "stills":
    for s in a.at.split(","):
        t = float(s)
        still(F(t), os.path.join(a.out, f"t_{t:06.2f}.png"))
elif a.mode == "shots":
    shots = json.load(open(os.path.join(os.path.dirname(os.path.abspath(a.blend)), "storyboard", "shots.json")))
    for sh in shots:
        ts = [sh["start"] + (sh["end"] - sh["start"]) * f for f in ([0.5] if not a.at else [float(x) for x in a.at.split(",")])]
        for i, t in enumerate(ts):
            still(F(t), os.path.join(a.out, f"{sh['id']}_{i}.png"))
elif a.mode == "anim":
    sc.frame_start = F(a.t0)
    sc.frame_end = F(a.t1) - 1
    sc.frame_step = a.step
    sc.render.image_settings.file_format = a.fmt
    if a.fmt == "JPEG":
        sc.render.image_settings.quality = 94
    sc.render.filepath = os.path.join(a.out, "f_")
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    t = time.time()
    bpy.ops.render.render(animation=True)
    n = (sc.frame_end - sc.frame_start) // a.step + 1
    print(f"ANIM {n} frames {time.time() - t:.1f}s ({(time.time() - t) / max(1, n):.2f}s/frame)", flush=True)
