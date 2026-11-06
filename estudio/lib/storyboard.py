"""Gera o storyboard técnico (storyboard.md + 1 imagem por plano + prancha) a partir de shots.json,
tempos da narração e dos quadros renderizados.
  python3 -I lib/storyboard.py <pasta_do_video> <frames_dir>
"""
import json, os, sys, subprocess

V, FR = sys.argv[1], sys.argv[2]
shots = json.load(open(os.path.join(V, "storyboard", "shots.json"), encoding="utf-8"))
tempos = json.load(open(os.path.join(V, "audio", "voz", "tempos.json"), encoding="utf-8"))
parts = [p for l in tempos for p in l["parts"]]
os.makedirs(os.path.join(V, "storyboard", "planos"), exist_ok=True)
md = ["# Storyboard técnico", "",
      "Cada linha é um plano (câmera própria, ligada a um marcador da timeline do `projeto.blend`).",
      "Tempos em segundos; imagens extraídas do render final (quadro do meio do plano).", "",
      "| Plano | Início–fim | Lente | Imagem | Ação / enquadramento | Narração no plano |", "|---|---|---|---|---|---|"]
for s in shots:
    mid = (s["start"] + s["end"]) / 2
    fr = int(round(mid * 30)) + 1
    src = os.path.join(FR, f"f_{fr:04d}.jpg")
    dst = os.path.join(V, "storyboard", "planos", f"{s['id']}.jpg")
    if os.path.isfile(src):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", "scale=270:-1", dst], check=True)
    fala = " ".join(p["text"] for p in parts if p["start"] < s["end"] and p["end"] > s["start"])
    md.append(f"| {s['id']} | {s['start']:.1f}–{s['end']:.1f} | {s['lens']} mm | ![{s['id']}](planos/{s['id']}.jpg) | {s['desc']} | {fala} |")
open(os.path.join(V, "storyboard", "storyboard.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-pattern_type", "glob", "-i", os.path.join(V, "storyboard", "planos", "s*.jpg"),
                "-vf", "tile=9x3:padding=4", os.path.join(V, "storyboard", "prancha_planos.jpg")], check=True)
print("storyboard ok", len(shots))
