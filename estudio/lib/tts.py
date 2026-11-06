"""Narração PT-BR com Kokoro (voz masculina pm_alex / pm_santa).
Uso: python3 -I lib/tts.py <narracao.json> <saida_dir>
narracao.json: {"voice":"pm_alex","speed":0.92,"lines":[{"id":"c1","start":0.3,"parts":["texto", 0.6, "texto"]}]}
Números em 'parts' = pausa em segundos. Grava <id>.wav e voz.wav (linha do tempo completa) + tempos.json.
"""
import json, sys, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
M = os.path.join(ROOT, "_deps", "kokoro")
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
k = Kokoro(os.path.join(M, "kokoro-v1.0.onnx"), os.path.join(M, "voices-v1.0.bin"))
SR = 24000
def trim(x, thr=0.004):
    idx = np.where(np.abs(x) > thr)[0]
    return x if len(idx) == 0 else x[max(0, idx[0]-240): idx[-1]+1200]
res = []; total = cfg.get("total", 60.0)
full = np.zeros(int(total*SR), np.float32)
for ln in cfg["lines"]:
    chunks = []; parts = []; pos = ln["start"]
    for p in ln["parts"]:
        if isinstance(p, (int, float)): c = np.zeros(int(p*SR), np.float32)
        else:
            s, sr = k.create(p, voice=ln.get("voice", cfg["voice"]), speed=ln.get("speed", cfg["speed"]), lang="pt-br")
            c = trim(s.astype(np.float32)); parts.append({"text": p, "start": round(pos, 3), "end": round(pos+len(c)/SR, 3)})
        chunks.append(c); pos += len(c)/SR
    a = np.concatenate(chunks); sf.write(os.path.join(out, ln["id"]+".wav"), a, SR)
    st = ln["start"]; i0 = int(st*SR); full[i0:i0+len(a)] += a[:len(full)-i0]
    res.append({"id": ln["id"], "start": st, "dur": round(len(a)/SR, 3), "end": round(st+len(a)/SR, 3), "parts": parts})
    print(ln["id"], res[-1])
sf.write(os.path.join(out, "voz.wav"), full, SR)
json.dump(res, open(os.path.join(out, "tempos.json"), "w"), indent=1)
