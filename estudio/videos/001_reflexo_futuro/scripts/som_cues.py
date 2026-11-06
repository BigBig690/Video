"""Gera audio/cues.json (trilha, ambiências e efeitos) sincronizado com a animação de cena.py."""
import json, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "audio", "cues.json")

S = []


def fx(at, name, gain=-10, **kw):
    S.append(dict(at=round(at, 3), name=name, gain=gain, **kw))


def steps(t0, t1, pts, stride, run=False, gain=-14, mirror=False, seed=100):
    L = sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]))
    k = 1
    while k * stride < L:
        fx(t0 + (t1 - t0) * (k * stride) / L, "step", gain, run=run, mirror=mirror, seed=seed + k)
        k += 1
    fx(t1, "step", gain - 3, run=run, mirror=mirror, seed=seed + 50)


# --- cena 1: o espelho "acorda"
fx(0.0, "swell", -14, dur=3.0)
fx(1.7, "riser", -16, dur=1.5)
fx(3.0, "whoosh", -12)
fx(3.62, "clink", -10, mirror=True)
fx(3.95, "glass_floor", -6, mirror=True)
fx(4.07, "roll", -12, mirror=True)
fx(5.8, "hit", -14)
fx(5.85, "stinger", -16)
# --- cena 2: o copo real cai igualzinho
fx(8.25, "clink", -8)
fx(8.6, "glass_floor", -3)
fx(8.72, "roll", -9)
fx(8.8, "step", -12, seed=3)
fx(8.98, "step", -14, seed=4)
fx(10.4, "swell", -16, dur=2.5)
fx(12.55, "clink", -12, pitch=0.6)
fx(12.6, "shimmer", -10)
# --- cena 3: usando o poder
fx(15.2, "swell", -18, dur=1.5)
fx(15.4, "clink", -12, pitch=0.8, mirror=True)
fx(15.8, "shatter", -5, mirror=True)
fx(16.55, "whoosh", -12)
steps(16.6, 17.5, [(-0.75, 0.25), (-1.3, -0.4), (-1.72, -1.02)], 0.8, run=True, gain=-10)
fx(17.45, "box", -10)
fx(17.9, "breath", -20, dur=1.0, rate=1.0)
fx(18.6, "creak", -10, mirror=True)
fx(18.62, "latch", -12, mirror=True)
steps(18.85, 19.75, [(-0.35, -3.2), (-0.4, -1.75)], 0.62, gain=-16, mirror=True, seed=200)
fx(20.12, "latch", -10)
fx(20.15, "creak", -8)
steps(20.4, 21.3, [(-0.35, -3.2), (-0.4, -1.75)], 0.62, gain=-13, seed=300)
fx(20.95, "box", -10)
fx(21.95, "jingle", -12, mirror=True)
fx(22.2, "ding", -20, mirror=True)
fx(23.25, "jingle", -9)
fx(23.6, "ding", -17)
# --- cena 4: noite
fx(24.2, "tick", -26)
steps(24.6, 26.6, [(0.95, -0.2), (0.3, 0.6), (-0.35, 1.3)], 0.62, gain=-15, seed=400)
fx(27.25, "freeze", -10)
fx(28.95, "swish", -18)
for i, t in enumerate([31.35, 32.05, 32.75]):
    fx(t, "step", -16, seed=500 + i)
for i in range(13):          # coração acelerando
    fx(30.0 + i * (0.95 - i * 0.03), "heartbeat", -15 + i * 0.4, seed=600 + i)
# --- cena 5: olha a porta, encara, bate no vidro
fx(33.55, "slowmo", -16)
fx(36.75, "impact", -12)
fx(36.8, "swell", -14, dur=2.0)
fx(37.9, "step", -14, mirror=True, seed=700)
for i, tk in enumerate([38.45, 38.95, 39.45, 39.95, 40.4, 40.9, 41.5, 42.2]):
    fx(tk, "knock_glass", -6 + min(i, 4) * 1.0, seed=710 + i)
# piscar das luzes: mesma sequência determinística de cena.py
rnd = random.Random(7)
t = 38.3
prev_on = True
while t < 43.0:
    on = rnd.random() > 0.45
    if not on:
        rnd.uniform(0.0, 0.25)
    if on != prev_on:
        fx(t, "crackle", -12 if not on else -16, seed=int(t * 100))
    prev_on = on
    t += rnd.uniform(0.06, 0.22)
fx(38.3, "hum", -18, dur=4.7)
# --- cena 6: fuga
fx(43.2, "whoosh", -10, seed=9)
steps(43.2, 45.5, [(-0.3, 0.38), (-0.4, -1.4), (-0.45, -2.1), (-0.45, -3.15), (0.05, -3.3)], 0.8, run=True, gain=-9, seed=800)
fx(43.9, "hit", -10)
steps(45.5, 47.7, [(0.05, -3.3), (3.0, -3.3)], 0.8, run=True, gain=-9, seed=850)
steps(47.7, 49.3, [(3.0, -3.3), (3.55, -3.3)], 0.62, gain=-13, seed=880)
fx(46.3, "clunk", -9, seed=1)
fx(47.0, "clunk", -8, seed=2)
fx(47.85, "clunk", -7, seed=3)
fx(48.75, "clunk", -3, big=True, seed=4)
fx(49.5, "breath", -12, dur=4.5, rate=1.4)
fx(54.0, "breath", -18, dur=2.5, rate=0.9)
# --- cena 7: a janela
fx(52.2, "drone", -12, dur=8.8, f=41.2)
fx(54.4, "swell", -12, dur=3.5)
fx(55.2, "riser", -14, dur=3.0)
fx(58.3, "slowmo", -14)
fx(59.8, "stinger", -10)
fx(61.6, "soft_knock", -4, after_cut=True)

amb = [
    dict(name="roomtone", start=0, end=24.2, gain=-20),
    dict(name="city", start=0, end=24.2, gain=-30, lp=1200),
    dict(name="roomtone", start=24.2, end=43.2, gain=-19),
    dict(name="wind", start=24.2, end=43.2, gain=-30, lp=900),
    dict(name="roomtone", start=43.2, end=61.0, gain=-20),
    dict(name="wind", start=49.0, end=61.0, gain=-27, lp=700),
]
music = [
    dict(start=0, end=7.2, mood="mystery", intensity=0.35),
    dict(start=7.2, end=15.0, mood="mystery", intensity=0.5),
    dict(start=15.0, end=24.2, mood="wonder", intensity=0.45),
    dict(start=24.2, end=33.3, mood="dark", intensity=0.45),
    dict(start=33.3, end=43.2, mood="tension", intensity=0.8),
    dict(start=43.2, end=49.3, mood="tension", intensity=1.0),
    dict(start=49.3, end=62.5, mood="dark", intensity=0.3),
]
music_gain = [[0, 0], [48.6, 0], [49.2, -40], [52.2, -40], [55.0, -6], [60.9, -2], [61.0, -60]]
cues = dict(total=62.5, music=music, music_gain=music_gain, amb=amb, sfx=S, cut=61.0, seed=5,
            music_db=-15, amb_db=7, sfx_db=-3, duck_music=10, duck_amb=6)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(cues, open(OUT, "w"), indent=1)
print("cues", len(S))
