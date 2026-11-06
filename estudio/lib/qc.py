"""Verificação de qualidade do vídeo final. Escreve relatorio_qualidade.md e uma prancha de quadros.
  python3 -I lib/qc.py <video.mp4> <relatorio.md> <prancha.png> [--expect-black 61.0] [--frames_dir DIR --nframes 1875]
"""
import subprocess, sys, json, os, re, argparse, datetime

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("report")
ap.add_argument("sheet")
ap.add_argument("--expect-black", type=float, default=None, help="início do preto intencional (corte final)")
ap.add_argument("--allow-black", default="", help="trechos pretos intencionais 'ini-fim,ini-fim' (ex.: apagão)")
ap.add_argument("--frames_dir", default=None)
ap.add_argument("--nframes", type=int, default=0)
ap.add_argument("--extra", default="", help="arquivo .md com notas adicionais anexadas ao relatório")
a = ap.parse_args()
R = []
ok_all = True


def check(name, ok, detail):
    global ok_all
    ok_all &= bool(ok)
    R.append(f"| {name} | {'OK' if ok else 'FALHA'} | {detail} |")


exists = os.path.isfile(a.video) and os.path.getsize(a.video) > 1000
check("Arquivo MP4 existe", exists, f"{a.video} ({os.path.getsize(a.video) / 1e6:.1f} MB)" if exists else "não encontrado")
if not exists:
    sys.exit(1)
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", a.video],
                               capture_output=True, text=True).stdout)
v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
au = [s for s in pr["streams"] if s["codec_type"] == "audio"]
dur = float(pr["format"]["duration"])
fr = v["r_frame_rate"].split("/")
fps = float(fr[0]) / float(fr[1])
nb = int(v.get("nb_frames", 0))
check("Resolução 1080×1920 (9:16)", (v["width"], v["height"]) == (1080, 1920), f"{v['width']}×{v['height']}")
check("FPS = 30", abs(fps - 30) < 0.01, f"{fps:.3f} fps, {nb} quadros")
check("Codec de vídeo H.264", v["codec_name"] == "h264", f"{v['codec_name']} / {v.get('profile')} / {v.get('pix_fmt')}")
check("Áudio AAC presente", bool(au) and au[0]["codec_name"] == "aac",
      f"{au[0]['codec_name']} {au[0].get('sample_rate')} Hz {au[0].get('channels')} canais" if au else "sem áudio")
check("Duração entre 55 e 65 s", 55 <= dur <= 65, f"{dur:.2f} s")
if au:
    ad = float(au[0].get("duration", dur))
    check("Áudio e vídeo com mesma duração", abs(ad - float(v.get("duration", dur))) < 0.1,
          f"vídeo {float(v.get('duration', dur)):.2f} s / áudio {ad:.2f} s")

# quadros pretos
bd = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-vf", "blackdetect=d=0.1:pix_th=0.06", "-an", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
blacks = [(float(x), float(y)) for x, y in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bd)]
allowed = [tuple(map(float, r.split("-"))) for r in a.allow_black.split(",") if r]
unexpected = [b for b in blacks if (a.expect_black is None or b[0] < a.expect_black - 0.15)
              and not any(lo - 0.05 <= b[0] and b[1] <= hi + 0.05 for lo, hi in allowed)]
check("Sem quadros pretos indesejados", not unexpected,
      ("pretos encontrados: " + ", ".join(f"{s:.2f}–{e:.2f}s" for s, e in blacks)) + (" — todos intencionais (apagão / corte seco final)" if blacks and not unexpected else "")
      if blacks else "nenhum trecho preto")
# congelamentos (quadros repetidos por muito tempo)
fz = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-vf", "freezedetect=n=0.0008:d=1.2", "-an", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
freezes = [(float(x), float(y)) for x, y in re.findall(r"freeze_start: ([\d.]+).*?freeze_end: ([\d.]+)", fz, re.S)]
fr_bad = [f for f in freezes if a.expect_black is None or f[0] < a.expect_black - 0.15]
check("Sem imagem congelada > 1,2 s (fora do final)", not fr_bad,
      ", ".join(f"{s:.2f}–{e:.2f}s" for s, e in freezes) if freezes else "nenhum congelamento")
# áudio
if au:
    eb = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-af", "ebur128=framelog=quiet:peak=true", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)
    tpv = float(tp[-1]) if tp else 0
    check("Loudness ≈ −14 LUFS", abs(I + 14) < 1.5, f"{I:.1f} LUFS integrado")
    check("Sem clipping (pico < −0,5 dBFS)", tpv < -0.5, f"pico real {tpv:.1f} dBFS")
    sd = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.video, "-af", "silencedetect=n=-55dB:d=1.5", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    sil = [(float(x), float(y)) for x, y in re.findall(r"silence_start: ([\d.]+).*?silence_end: ([\d.]+)", sd, re.S)]
    check("Sem buracos de áudio (> 1,5 s abaixo de −55 dB)", not sil,
          ", ".join(f"{s:.2f}–{e:.2f}s" for s, e in sil) if sil else "nenhum silêncio total")
# frames de origem
if a.frames_dir and a.nframes:
    fs = sorted(f for f in os.listdir(a.frames_dir) if f.startswith("f_"))
    empty = [f for f in fs if os.path.getsize(os.path.join(a.frames_dir, f)) == 0]
    check("Todos os quadros renderizados", len(fs) == a.nframes and not empty, f"{len(fs)}/{a.nframes} arquivos, {len(empty)} vazios")
# texto na tela: o pipeline não cria objetos de texto; verificação documental
# prancha de amostragem: 1 quadro a cada 2 s
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.video, "-vf",
                "fps=1/2,scale=180:-1,tile=8x4:padding=4", "-frames:v", "1", a.sheet], check=True)
check("Prancha de amostragem gerada", os.path.isfile(a.sheet), os.path.basename(a.sheet) + " (1 quadro a cada 2 s)")

md = [f"# Relatório de qualidade — {os.path.basename(a.video)}", "",
      f"Gerado em {datetime.datetime.now():%Y-%m-%d %H:%M} por `lib/qc.py` (medições reais com ffprobe/ffmpeg).", "",
      f"**Resultado geral: {'APROVADO' if ok_all else 'COM PENDÊNCIAS'}**", "",
      "| Verificação | Resultado | Detalhe |", "|---|---|---|"] + R
if a.extra and os.path.isfile(a.extra):
    md += ["", open(a.extra, encoding="utf-8").read()]
open(a.report, "w", encoding="utf-8").write("\n".join(md) + "\n")
print("\n".join(R))
print("GERAL", "OK" if ok_all else "PENDENCIAS")
