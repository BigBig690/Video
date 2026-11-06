"""Motor de som do estúdio: efeitos originais sintetizados, trilha por humor, ambiências, mixagem com ducking.
Tudo é gerado localmente (numpy/scipy) — sem arquivos licenciados de terceiros.

  python3 -I lib/som.py <cues.json> <voz.wav> <saida_dir>

cues.json:
 {"total": 62.5,
  "music": [{"start":0,"end":7,"mood":"mystery","intensity":0.4}, ...],
  "music_gain": [[t, dB], ...]            # automação extra da música (silêncios, corte seco)
  "amb":   [{"name":"roomtone","start":0,"end":24,"gain":-22,"lp":null}, ...],
  "sfx":   [{"at": 3.6, "name": "clink", "gain": -8, "mirror": false, "seed": 1, "dur": null, "pan": 0}, ...],
  "cut":   61.0}                           # tudo silencia neste instante (corte seco), exceto sfx com "after_cut": true
Saídas: musica.wav, efeitos.wav, ambiencia.wav, voz_tratada.wav, mix.wav (48 kHz estéreo)
"""
import sys, os, json
import numpy as np
from scipy import signal
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "audio_kit"))
from dsp import (SR, secs, t_axis, noise, lp, hp, bp, sine, osc, expdec, env_adsr, stereo, as_stereo, reverb,
                 normalize, rms_db, place, write_wav, db, rng)
import sfx as K
import music as MUS


# ------------------------------------------------------------------ efeitos novos
def _ring(n, freqs, taus, amps, seed=0):
    x = np.zeros(n, np.float32)
    r = rng(seed)
    for f, tau, a in zip(freqs, taus, amps):
        x += sine(f * (1 + r.uniform(-0.01, 0.01)), n, r.uniform(0, 6)) * expdec(n, tau) * a
    return x


def clink(dur=0.6, seed=1, pitch=1.0, **_):
    """vidro tocando madeira/vidro"""
    n = secs(dur)
    x = _ring(n, np.array([2150, 3420, 5230, 7810]) * pitch, [0.18, 0.12, 0.08, 0.05], [1, 0.7, 0.5, 0.3], seed)
    x[: secs(0.003)] += noise(secs(0.003), seed) * 0.8
    return normalize(stereo(x, 0, 0.3), -6)


def glass_floor(dur=1.2, seed=2, **_):
    n = secs(dur)
    x = K._thump(n, 220, 90, 0.08, 0.6, seed) * 0.7
    x += _ring(n, [1850, 2960, 4400, 6900], [0.3, 0.2, 0.12, 0.07], [1, 0.8, 0.5, 0.3], seed)
    return normalize(stereo(x, 0, 0.4), -4)


def roll(dur=0.8, seed=3, **_):
    n = secs(dur)
    t = t_axis(n)
    x = bp(noise(n, seed), 900, 4000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 7 * t))) * np.exp(-t / (dur * 0.6))
    for i, at in enumerate([0.05, 0.22, 0.41, 0.58]):
        if at < dur:
            c = _ring(secs(0.2), [2600 + 300 * i, 4100], [0.05, 0.03], [0.5, 0.3], seed + i)
            place(x, c, secs(at), 0.5 * (1 - at / dur))
    return normalize(stereo(x, 0.1, 0.4), -10)


def shatter(dur=1.6, seed=4, **_):
    n = secs(dur)
    r = rng(seed)
    x = K._thump(n, 180, 60, 0.12, 0.8, seed) * 0.8
    x += hp(noise(n, seed), 2500) * expdec(n, 0.07) * 0.7
    for i in range(26):
        at = abs(r.normal(0.0, 0.18))
        c = _ring(secs(0.4), [r.uniform(1800, 7500), r.uniform(3000, 9000)], [r.uniform(0.04, 0.15), 0.05], [1, 0.5], seed + i)
        place(x, c, secs(at), r.uniform(0.1, 0.5) * np.exp(-at * 2))
    return normalize(stereo(x, 0, 0.8), -3)


def creak(dur=0.9, seed=5, **_):
    n = secs(dur)
    t = t_axis(n)
    r = rng(seed)
    f = 210 + 120 * np.sin(2 * np.pi * 0.7 * t) + np.cumsum(r.normal(0, 3, n)) * 0.02
    pulses = (np.sin(2 * np.pi * np.cumsum(28 + 10 * np.sin(2 * np.pi * 1.3 * t)) / SR) > 0.7).astype(np.float32)
    x = bp(osc("saw", f, n), 300, 2400) * (0.35 + 0.65 * pulses) * np.sin(np.pi * t / dur) ** 0.6
    return normalize(stereo(x, -0.2, 0.3), -8)


def latch(dur=0.25, seed=6, **_):
    n = secs(dur)
    x = hp(noise(n, seed), 1800) * expdec(n, 0.012)
    x2 = hp(noise(n, seed + 1), 1200) * expdec(n, 0.015)
    out = x.copy()
    place(out, x2, secs(0.07), 0.7)
    out += K._thump(n, 300, 120, 0.04, 0.0, seed) * 0.4
    return normalize(stereo(out, 0, 0.2), -8)


def knock_glass(dur=1.4, seed=7, **_):
    """palmas batendo num espelho grande: baque grave + ressonância do vidro + tremor"""
    n = secs(dur)
    x = K._thump(n, 160, 55, 0.16, 0.9, seed) * 1.0
    x += lp(noise(n, seed), 900) * expdec(n, 0.03) * 0.8
    x += _ring(n, [420, 690, 1130, 1870, 2950], [0.5, 0.35, 0.25, 0.15, 0.08], [0.35, 0.3, 0.25, 0.15, 0.08], seed)
    trem = 1 + 0.25 * np.sin(2 * np.pi * 13 * t_axis(n)) * expdec(n, 0.3)
    x *= trem
    return normalize(reverb(stereo(x, 0, 0.5), 1.6, 0.25, seed), -2)


def soft_knock(dur=3.5, seed=8, **_):
    n = secs(dur)
    x = K._thump(n, 140, 60, 0.12, 0.5, seed) * 0.8
    x += _ring(n, [520, 860, 1400], [0.6, 0.4, 0.2], [0.25, 0.2, 0.1], seed)
    return normalize(reverb(stereo(x, 0, 0.4), 3.2, 0.45, seed), -6)


def crackle(dur=0.35, seed=9, **_):
    n = secs(dur)
    r = rng(seed)
    x = np.zeros(n, np.float32)
    for i in range(r.integers(4, 9)):
        at = r.uniform(0, dur * 0.8)
        c = hp(noise(secs(0.01), seed + i), 2500) * expdec(secs(0.01), 0.002)
        place(x, c, secs(at), r.uniform(0.4, 1.0))
    hm = (sine(120, n) * 0.5 + sine(240, n) * 0.3 + osc("square", 60, n) * 0.15) * np.exp(-t_axis(n) / 0.2)
    x += hm * 0.35
    return normalize(stereo(x, r.uniform(-0.3, 0.3), 0.3), -8)


def clunk(dur=1.4, seed=10, big=False, **_):
    """interruptor geral / luz apagando"""
    n = secs(dur)
    x = hp(noise(n, seed), 1500) * expdec(n, 0.008) * 0.7
    x += K._thump(n, 110 if big else 160, 35 if big else 60, 0.35 if big else 0.18, 0.6, seed)
    t = t_axis(n)
    x += sine(110 * np.exp(-t / 0.3) + 25, n) * expdec(n, 0.5) * (0.5 if big else 0.2)
    return normalize(reverb(stereo(x, 0, 0.4), 2.2, 0.3, seed), -3 if big else -6)


def breath(dur=4.0, seed=11, rate=1.25, **_):
    n = secs(dur)
    t = t_axis(n)
    ph = (t * rate) % 1.0
    env = np.where(ph < 0.45, np.abs(np.sin(np.pi * ph / 0.45)) ** 1.5, 0.75 * np.sin(np.pi * (ph - 0.45) / 0.55) ** 2)
    x = bp(noise(n, seed, "pink"), 500, 2200) * env * (0.7 + 0.3 * np.sin(2 * np.pi * 0.2 * t))
    return normalize(stereo(x, 0, 0.3), -10)


def jingle(dur=0.6, seed=12, **_):
    n = secs(dur)
    r = rng(seed)
    x = np.zeros(n, np.float32)
    for i in range(12):
        at = r.uniform(0, dur * 0.6)
        c = _ring(secs(0.2), [r.uniform(3500, 8000), r.uniform(5000, 10000)], [0.06, 0.04], [1, 0.6], seed + i)
        place(x, c, secs(at), r.uniform(0.3, 1))
    return normalize(stereo(x, 0.1, 0.5), -8)


def box(dur=0.5, seed=13, **_):
    n = secs(dur)
    x = lp(noise(n, seed), 500) * expdec(n, 0.05) + K._thump(n, 140, 70, 0.08, 0.2, seed) * 0.6
    return normalize(stereo(x, 0, 0.2), -8)


def step(dur=0.3, seed=14, run=False, **_):
    n = secs(dur)
    x = K._thump(n, 120, 55, 0.05 if not run else 0.07, 0.4, seed) * 0.8
    x += bp(noise(n, seed), 300, 3000) * expdec(n, 0.02 if not run else 0.03) * 0.5
    return normalize(stereo(x, rng(seed).uniform(-0.2, 0.2), 0.2), -6)


def drone(dur=8.0, seed=15, f=55, **_):
    n = secs(dur)
    t = t_axis(n)
    x = osc("saw", f * (1 + 0.003 * np.sin(2 * np.pi * 0.1 * t)), n) + osc("saw", f * 1.498, n) * 0.4 + sine(f / 2, n) * 0.8
    x = lp(x, 420) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.07 * t))
    return normalize(reverb(stereo(x, 0, 1.0), 3.0, 0.4, seed), -10)


def swell(dur=3.0, seed=16, **_):
    """shimmer frio do espelho"""
    n = secs(dur)
    t = t_axis(n)
    env = np.sin(np.pi * t / dur) ** 2
    x = sum(sine(f * (1 + 0.002 * np.sin(2 * np.pi * 5 * t + i)), n, i) for i, f in enumerate([880, 1318.5, 1760, 2637]))
    x = x * env * 0.25 + bp(noise(n, seed, "pink"), 3000, 9000) * env * 0.15
    return normalize(reverb(stereo(x, 0, 1.0), 3.0, 0.5, seed), -10)


NEW = dict(clink=clink, glass_floor=glass_floor, roll=roll, shatter=shatter, creak=creak, latch=latch,
           knock_glass=knock_glass, soft_knock=soft_knock, crackle=crackle, clunk=clunk, breath=breath,
           jingle=jingle, box=box, step=step, drone=drone, swell=swell)


def make(name, **kw):
    kw = {k: v for k, v in kw.items() if v is not None}
    if name in NEW:
        return as_stereo(NEW[name](**kw)).astype(np.float32)
    return K.make(name, **{k: v for k, v in kw.items() if k in ("dur", "seed", "pitch")})


def mirrorize(x):
    """o que acontece 'dentro do espelho' soa abafado e distante"""
    return reverb(lp(x, 2600), 2.4, 0.45, 99) * 0.8


def pan(x, p):
    if not p:
        return x
    l = np.cos((p + 1) * np.pi / 4) * np.sqrt(2)
    r = np.sin((p + 1) * np.pi / 4) * np.sqrt(2)
    m = x.mean(axis=1)
    return np.stack([m * l, m * r], 1).astype(np.float32)


def auto(x, points):
    """automação de ganho [[t, dB], ...] (linear em dB)"""
    if not points:
        return x
    ts = np.array([p[0] for p in points])
    gs = np.array([p[1] for p in points])
    t = np.arange(len(x)) / SR
    g = db(np.interp(t, ts, gs))
    return (x * g[:, None]).astype(np.float32)


def envelope(mono, att=0.03, rel=0.5):
    hop = secs(0.01)
    fr = np.sqrt(np.add.reduceat(mono ** 2, np.arange(0, len(mono), hop)) / hop)
    lv = np.clip((20 * np.log10(fr + 1e-9) + 50) / 30, 0, 1)
    out = np.zeros_like(lv)
    a, r = np.exp(-0.01 / att), np.exp(-0.01 / rel)
    v = 0.0
    for i, s in enumerate(lv):
        v = a * v + (1 - a) * s if s > v else r * v + (1 - r) * s
        out[i] = v
    return np.repeat(out, hop)[: len(mono)]


def load_voice(path):
    from scipy.io import wavfile
    sr, v = wavfile.read(path)
    v = v.astype(np.float32)
    if v.ndim == 2:
        v = v.mean(1)
    if np.abs(v).max() > 2:
        v /= 32768.0
    from math import gcd
    g = gcd(sr, SR)
    v = signal.resample_poly(v, SR // g, sr // g).astype(np.float32)
    return v


def treat_voice(v):
    """voz: passa-altas, leve presença, compressão suave e ambiência curta de sala"""
    v = hp(v, 75)
    pres = bp(v, 2500, 5000) * 0.18
    warm = lp(v, 220) * 0.12
    v = v + pres + warm
    env = envelope(np.abs(v), 0.005, 0.12) + 1e-3
    gain = np.clip(0.55 / np.maximum(env, 0.55), 0.6, 1.0)
    v = v * gain
    v = reverb(stereo(v, 0, 0.0), 0.7, 0.08, 3)
    return normalize(v, -3)


def main():
    cues = json.load(open(sys.argv[1]))
    out = sys.argv[3]
    os.makedirs(out, exist_ok=True)
    total = cues["total"]
    N = secs(total)
    # voz
    v = treat_voice(load_voice(sys.argv[2]))
    voice = np.zeros((N, 2), np.float32)
    place(voice, v[:N], 0)
    venv = envelope(np.abs(voice).mean(1))
    # música
    mus = MUS.render_score(cues["music"], total, seed=cues.get("seed", 3))[:N]
    if len(mus) < N:
        mus = np.concatenate([mus, np.zeros((N - len(mus), 2), np.float32)])
    mus = auto(mus, cues.get("music_gain"))
    # ambiência
    amb = np.zeros((N, 2), np.float32)
    for a in cues.get("amb", []):
        d = a["end"] - a["start"]
        bed = make(a["name"], dur=max(d, 1.0), seed=a.get("seed"))
        if a.get("lp"):
            bed = lp(bed, a["lp"])
        f = min(secs(0.6), len(bed) // 3)
        bed[:f] *= np.linspace(0, 1, f)[:, None]
        bed[-f:] *= np.linspace(1, 0, f)[:, None]
        place(amb, bed, secs(a["start"]), db(a.get("gain", -20)))
    # efeitos
    fx = np.zeros((N + secs(4), 2), np.float32)
    for c in cues.get("sfx", []):
        kw = {k: c[k] for k in ("dur", "seed", "pitch", "run", "big", "rate", "f") if k in c}
        x = make(c["name"], **kw)
        if c.get("mirror"):
            x = mirrorize(x)
        x = pan(x, c.get("pan", 0))
        place(fx, x, secs(c["at"]), db(c.get("gain", -10)))
    fx = fx[:N]
    # corte seco
    cut = cues.get("cut")
    if cut:
        k = secs(cut)
        k2 = k + secs(0.02)
        for arr in (mus, amb, fx, voice):
            arr[k2:] = 0
            arr[k:k2] *= np.linspace(1, 0, k2 - k)[:, None]
        for c in cues.get("sfx", []):
            if c.get("after_cut"):
                x = pan(make(c["name"], **{k_: c[k_] for k_ in ("dur", "seed") if k_ in c}), c.get("pan", 0))
                place(fx, x, secs(c["at"]), db(c.get("gain", -10)))
    # ducking
    duck_m = db(-cues.get("duck_music", 10) * venv)[:, None]
    duck_a = db(-cues.get("duck_amb", 5) * venv)[:, None]
    mg, ag, fg = db(cues.get("music_db", -15)), db(cues.get("amb_db", 0)), db(cues.get("sfx_db", -4))
    mix = voice + mus * duck_m * mg + amb * duck_a * ag + fx * fg
    # limitador simples
    pk = np.abs(mix).max()
    if pk > 0.98:
        env = np.maximum(np.abs(mix).max(1), 0.9)
        env = signal.lfilter([1], [1, -0.995], env * 0.005)
        mix = mix / np.maximum(1, np.abs(mix).max() / 0.98)
    for nm, arr in (("voz_tratada", voice), ("musica", mus * mg), ("ambiencia", amb * ag), ("efeitos", fx * fg), ("mix", mix)):
        write_wav(os.path.join(out, nm + ".wav"), arr)
    print("mix ok", round(len(mix) / SR, 2), "s  pico", round(float(np.abs(mix).max()), 3), "rms dB", round(rms_db(mix), 1))


if __name__ == "__main__":
    main()
