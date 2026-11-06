"""Vídeo 001 — "E se seu reflexo mostrasse o futuro 10 segundos antes?"
Constrói o projeto Blender completo (modelagem, rigs, animação, luzes, câmeras) e salva projeto.blend.
Uso: python3 -I scripts/cena.py <saida.blend>
"""
import sys, os, math, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "lib"))
import bpy
from mathutils import Vector, Matrix, Euler
import bu, personagem as pg
from bu import F, key, keyval

OUT = sys.argv[-1] if sys.argv[-1].endswith(".blend") else os.path.join(HERE, "..", "projeto.blend")
TOTAL = 62.5
sc = bu.reset()
sc.frame_start, sc.frame_end = 1, F(TOTAL) - 1

MY = 2.5          # plano do espelho (parede do fundo)
MX0, MX1 = -0.9, 0.7   # abertura do espelho em X
MZ0, MZ1 = 0.06, 2.06
RW, RF, RH = 2.4, -2.4, 2.7   # meia-largura, parede da frente, altura
HY0 = -4.2        # parede sul do corredor
HX1 = 4.2         # fim do corredor (janela)
A = (-0.35, 1.3)  # marca do protagonista diante do espelho
TABLE = (0.45, 1.42)
DOOR_X0, DOOR_X1 = -0.9, 0.0

# ------------------------------------------------------------------ coleções
C_base = bu.coll("Q_base")      # quarto (instanciado no mundo do espelho e no quarto-fantasma)
C_frente = bu.coll("Q_frente")  # parede da frente (porta)
C_fundo = bu.coll("Q_fundo")    # parede do espelho
C_luz = bu.coll("Q_luzes")
C_dyn = bu.coll("Dinamicos")
C_char = bu.coll("Personagens")
C_hall = bu.coll("Corredor")
C_cam = bu.coll("Cameras")
C_ghost = bu.coll("Fantasma")

# ------------------------------------------------------------------ materiais
M = {}
M["wall"] = bu.mat("parede", (0.34, 0.30, 0.33), rough=0.9)
M["wall2"] = bu.mat("parede_corredor", (0.26, 0.27, 0.31), rough=0.9)
M["floor"] = bu.mat("piso_madeira", (0.18, 0.11, 0.07), rough=0.55, coat=0.15)
M["rug"] = bu.mat("tapete", (0.32, 0.12, 0.10), rough=1.0, sheen=0.6)
M["ceil"] = bu.mat("teto", (0.40, 0.38, 0.40), rough=0.95)
M["trim"] = bu.mat("rodape", (0.10, 0.09, 0.10), rough=0.6)
M["wood"] = bu.mat("madeira", (0.30, 0.17, 0.09), rough=0.5, coat=0.2)
M["wood_d"] = bu.mat("madeira_escura", (0.09, 0.06, 0.05), rough=0.45, coat=0.3)
M["frame"] = bu.mat("moldura", (0.035, 0.03, 0.03), rough=0.3, metal=0.4)
M["fabric"] = bu.mat("tecido_poltrona", (0.55, 0.36, 0.08), rough=0.95, sheen=0.7)
M["bed"] = bu.mat("lencol", (0.62, 0.62, 0.66), rough=0.95, sheen=0.5)
M["blanket"] = bu.mat("cobertor", (0.13, 0.20, 0.32), rough=0.95, sheen=0.6)
M["vase"] = bu.mat("vaso_ceramica", (0.02, 0.45, 0.42), rough=0.25, coat=0.6)
M["book1"] = bu.mat("livro1", (0.45, 0.08, 0.06), rough=0.7)
M["book2"] = bu.mat("livro2", (0.08, 0.20, 0.35), rough=0.7)
M["book3"] = bu.mat("livro3", (0.55, 0.45, 0.25), rough=0.7)
M["gift"] = bu.mat("presente", (0.65, 0.05, 0.08), rough=0.5, coat=0.3)
M["ribbon"] = bu.mat("fita", (0.95, 0.75, 0.2), rough=0.3, metal=0.6)
M["gold"] = bu.mat("chaves", (1.0, 0.72, 0.3), rough=0.2, metal=1.0, emit=(1.0, 0.7, 0.3), emit_str=0.0)
M["lampshade"] = bu.emit_mat("cupula_abajur", (1.0, 0.62, 0.32), 0.0)
M["copo"] = bu.mat("copo_vidro", (0.95, 0.5, 0.12), rough=0.08, coat=1.0, alpha=0.75, emit=(1.0, 0.55, 0.15), emit_str=0.25)
M["janela"] = bu.glass_mat("vidro_janela", tint=(0.55, 0.65, 0.8), refl=0.18, rough=0.03)
M["espelho"] = bu.glass_mat("vidro_espelho", tint=(0.93, 0.96, 1.0), refl=0.03, rough=0.02)
M["glow"] = bu.emit_mat("brilho_espelho", (0.35, 0.85, 1.0), 0.0)
M["body"] = bu.mat("grafite", (0.010, 0.010, 0.012), rough=0.45, coat=0.3, spec=0.5)
M["body_v"] = bu.mat("visitante", (0.42, 0.36, 0.30), rough=0.5, coat=0.2)
M["eye"] = bu.emit_mat("olhos", (1.0, 0.95, 0.86), 1.6)
M["eye_r"] = bu.emit_mat("olhos_reflexo", (0.75, 0.92, 1.0), 1.6)
M["sky_day"] = bu.emit_mat("ceu_dia", (1.0, 0.82, 0.6), 1.2)
M["night_out"] = bu.emit_mat("ceu_noite", (0.05, 0.08, 0.16), 0.5)
M["bulb"] = bu.emit_mat("lampada_corredor", (1.0, 0.8, 0.55), 0.0)
M["plant"] = bu.mat("planta", (0.10, 0.28, 0.12), rough=0.7)
M["pot"] = bu.mat("vaso_planta", (0.55, 0.30, 0.20), rough=0.8)
M["shard"] = M["vase"]


# ------------------------------------------------------------------ quarto
def room_shell():
    T = 0.1
    bu.box("piso", (2 * RW + 0.4, MY - RF + 0.4, 0.1), (0, (MY + RF) / 2, -0.05), M["floor"], C_base)
    bu.box("teto", (2 * RW + 0.4, MY - RF + 0.4, 0.1), (0, (MY + RF) / 2, RH + 0.05), M["ceil"], C_base)
    # parede direita (cheia)
    bu.box("parede_dir", (T, MY - RF, RH), (RW + T / 2, (MY + RF) / 2, RH / 2), M["wall"], C_base)
    # parede esquerda com janela (y 0.5..1.7, z 0.9..2.1)
    wy0, wy1, wz0, wz1 = 0.5, 1.7, 0.9, 2.1
    x = -RW - T / 2
    bu.box("parede_esq_a", (T, wy0 - RF, RH), (x, (wy0 + RF) / 2, RH / 2), M["wall"], C_base)
    bu.box("parede_esq_b", (T, MY - wy1, RH), (x, (MY + wy1) / 2, RH / 2), M["wall"], C_base)
    bu.box("parede_esq_c", (T, wy1 - wy0, wz0), (x, (wy0 + wy1) / 2, wz0 / 2), M["wall"], C_base)
    bu.box("parede_esq_d", (T, wy1 - wy0, RH - wz1), (x, (wy0 + wy1) / 2, (RH + wz1) / 2), M["wall"], C_base)
    # caixilho da janela + vidro + "céu"
    for i, (sy, sz, ly, lz) in enumerate([(1.3, 0.06, 1.1, wz0), (1.3, 0.06, 1.1, wz1), (0.06, 1.26, wy0, 1.5),
                                         (0.06, 1.26, wy1, 1.5), (0.04, 1.2, 1.1, 1.5), (1.2, 0.04, 1.1, 1.5)]):
        bu.box(f"caixilho_{i}", (0.14, sy, sz), (-RW - 0.02, ly, lz), M["wood_d"], C_base)
    bu.box("vidro_janela_q", (0.01, 1.2, 1.2), (-RW - 0.04, 1.1, 1.5), M["janela"], C_base)
    sky = bu.box("ceu_janela", (0.02, 3.0, 2.4), (-RW - 1.2, 1.1, 1.5), M["sky_day"], C_base)
    bu.box("ceu_janela_noite", (0.02, 3.0, 2.4), (-RW - 1.21, 1.1, 1.5), M["night_out"], C_base)
    bu.box("cortina_a", (0.06, 0.35, 2.3), (-RW + 0.08, 0.32, 1.35), bu.mat("cortina", (0.42, 0.33, 0.24), rough=1, sheen=0.8), C_base, bevel=0.02)
    bu.box("cortina_b", (0.06, 0.35, 2.3), (-RW + 0.08, 1.88, 1.35), bpy.data.materials["cortina"], C_base, bevel=0.02)
    # rodapés
    bu.box("rodape_dir", (0.03, MY - RF, 0.1), (RW - 0.015, (MY + RF) / 2, 0.05), M["trim"], C_base)
    bu.box("rodape_esq", (0.03, MY - RF, 0.1), (-RW + 0.015, (MY + RF) / 2, 0.05), M["trim"], C_base)
    # parede do fundo com abertura do espelho
    y = MY + T / 2
    bu.box("fundo_esq", (MX0 + RW, T, RH), ((MX0 - RW) / 2, y, RH / 2), M["wall"], C_fundo)
    bu.box("fundo_dir", (RW - MX1, T, RH), ((MX1 + RW) / 2, y, RH / 2), M["wall"], C_fundo)
    bu.box("fundo_cima", (MX1 - MX0, T, RH - MZ1), ((MX0 + MX1) / 2, y, (RH + MZ1) / 2), M["wall"], C_fundo)
    bu.box("fundo_baixo", (MX1 - MX0, T, MZ0), ((MX0 + MX1) / 2, y, MZ0 / 2), M["wall"], C_fundo)
    # moldura do espelho (fica no plano, entra no mundo do espelho também)
    fw = 0.07
    cx = (MX0 + MX1) / 2
    for nm, s, l in [("mold_e", (fw, 0.06, MZ1 - MZ0 + 2 * fw), (MX0 - fw / 2, MY - 0.01, (MZ0 + MZ1) / 2)),
                     ("mold_d", (fw, 0.06, MZ1 - MZ0 + 2 * fw), (MX1 + fw / 2, MY - 0.01, (MZ0 + MZ1) / 2)),
                     ("mold_c", (MX1 - MX0 + 2 * fw, 0.06, fw), (cx, MY - 0.01, MZ1 + fw / 2)),
                     ("mold_b", (MX1 - MX0 + 2 * fw, 0.06, fw), (cx, MY - 0.01, MZ0 - fw / 2 + 0.03))]:
        bu.box(nm, s, l, M["frame"], C_fundo, bevel=0.01)
    # filete luminoso interno (assinatura visual: o espelho "acorda")
    gl = 0.012
    for nm, s, l in [("glow_e", (gl, 0.02, MZ1 - MZ0), (MX0 + gl / 2, MY - 0.035, (MZ0 + MZ1) / 2)),
                     ("glow_d", (gl, 0.02, MZ1 - MZ0), (MX1 - gl / 2, MY - 0.035, (MZ0 + MZ1) / 2)),
                     ("glow_c", (MX1 - MX0, 0.02, gl), (cx, MY - 0.035, MZ1 - gl / 2)),
                     ("glow_b", (MX1 - MX0, 0.02, gl), (cx, MY - 0.035, MZ0 + gl / 2 + 0.03))]:
        bu.box(nm, s, l, M["glow"], C_fundo)
    bu.box("vidro_espelho", (MX1 - MX0, 0.004, MZ1 - MZ0), (cx, MY - 0.03, (MZ0 + MZ1) / 2), M["espelho"], C_fundo)
    # parede da frente com porta
    y = RF - T / 2
    bu.box("frente_esq", (DOOR_X0 + RW, T, RH), ((DOOR_X0 - RW) / 2, y, RH / 2), M["wall"], C_frente)
    bu.box("frente_dir", (RW - DOOR_X1, T, RH), ((DOOR_X1 + RW) / 2, y, RH / 2), M["wall"], C_frente)
    bu.box("frente_cima", (DOOR_X1 - DOOR_X0, T, RH - 2.1), ((DOOR_X0 + DOOR_X1) / 2, y, (RH + 2.1) / 2), M["wall"], C_frente)
    for nm, s, l in [("bat_e", (0.06, 0.16, 2.14), (DOOR_X0 - 0.03, y, 1.07)),
                     ("bat_d", (0.06, 0.16, 2.14), (DOOR_X1 + 0.03, y, 1.07)),
                     ("bat_c", (DOOR_X1 - DOOR_X0 + 0.12, 0.16, 0.06), ((DOOR_X0 + DOOR_X1) / 2, y, 2.13))]:
        bu.box(nm, s, l, M["wood_d"], C_frente)
    bu.box("rodape_frente", (2 * RW, 0.03, 0.1), (0, RF + 0.015, 0.05), M["trim"], C_frente)


def furniture():
    c = C_base
    # mesinha redonda (pedestal) ao lado do espelho
    tx, ty = TABLE
    bu.cylinder("mesinha_tampo", 0.26, 0.04, (tx, ty, 0.70), M["wood"], c, seg=40)
    bu.cylinder("mesinha_pe", 0.035, 0.68, (tx, ty, 0.35), M["wood_d"], c)
    bu.cylinder("mesinha_base", 0.18, 0.03, (tx, ty, 0.015), M["wood_d"], c)
    # cama (parede direita)
    bx0, bx1, by0, by1 = 1.3, 2.38, 0.35, 2.45
    bu.box("cama_base", (bx1 - bx0, by1 - by0, 0.32), ((bx0 + bx1) / 2, (by0 + by1) / 2, 0.2), M["wood_d"], c, bevel=0.02)
    bu.box("colchao", (bx1 - bx0 - 0.04, by1 - by0 - 0.06, 0.2), ((bx0 + bx1) / 2, (by0 + by1) / 2 - 0.02, 0.46), M["bed"], c, bevel=0.06)
    bu.box("cobertor", (bx1 - bx0 + 0.02, (by1 - by0) * 0.62, 0.06), ((bx0 + bx1) / 2, by0 + (by1 - by0) * 0.31, 0.56), M["blanket"], c, bevel=0.04)
    bu.box("travesseiro", (0.75, 0.38, 0.13), ((bx0 + bx1) / 2, by1 - 0.3, 0.6), M["bed"], c, bevel=0.06)
    bu.box("cabeceira", (bx1 - bx0 + 0.04, 0.06, 1.0), ((bx0 + bx1) / 2, MY - 0.04, 0.5), M["wood_d"], c, bevel=0.02)
    # criado-mudo com abajur (prático de luz)
    bu.box("criado", (0.42, 0.4, 0.55), (1.0, 2.25, 0.275), M["wood"], c, bevel=0.015)
    bu.cylinder("abajur_base", 0.07, 0.04, (1.0, 2.25, 0.57), M["frame"], c)
    bu.cylinder("abajur_haste", 0.012, 0.3, (1.0, 2.25, 0.72), M["frame"], c)
    bu.lathe("abajur_cupula", [(0.15, 0.82), (0.09, 1.02)], (1.0, 2.25, 0.0), M["lampshade"], c)
    # estante (canto frente-esquerda) com livros
    ex, ey = -2.18, -1.35
    bu.box("estante_lat1", (0.4, 0.03, 1.9), (ex, ey - 0.6, 0.95), M["wood"], c)
    bu.box("estante_lat2", (0.4, 0.03, 1.9), (ex, ey + 0.6, 0.95), M["wood"], c)
    bu.box("estante_fundo", (0.02, 1.2, 1.9), (ex - 0.19, ey, 0.95), M["wood_d"], c)
    for i, z in enumerate([0.05, 0.5, 0.95, 1.4, 1.88]):
        bu.box(f"estante_prat{i}", (0.4, 1.2, 0.03), (ex, ey, z), M["wood"], c)
    import random
    rnd = random.Random(4)
    for z in (0.065, 0.515, 0.965):
        yy = ey - 0.55
        while yy < ey + 0.5:
            w = rnd.uniform(0.03, 0.07)
            h = rnd.uniform(0.24, 0.36)
            bu.box(f"livro_{z}_{yy:.2f}", (0.26, w, h), (ex - 0.03, yy + w / 2, z + 0.015 + h / 2),
                   M[rnd.choice(["book1", "book2", "book3"])], c)
            yy += w + 0.006
    # planta
    bu.lathe("vaso_planta", [(0.0, 0.0), (0.14, 0.0), (0.17, 0.32), (0.0, 0.32)], (-1.9, 2.15, 0), M["pot"], c)
    for i in range(7):
        a = i * 0.9
        b = bu.sphere(f"folha_{i}", 0.12, (-1.9 + 0.12 * math.cos(a), 2.15 + 0.12 * math.sin(a), 0.55 + 0.06 * (i % 3)),
                      M["plant"], c, scale=(0.6, 1.4, 0.25))
        b.rotation_euler = (0.5, 0.3, a)
    # tapete
    bu.box("tapete", (2.2, 1.6, 0.012), (-0.2, 0.4, 0.006), M["rug"], c, bevel=0.005)
    # poltrona (frente-direita)
    px, py = 0.95, -1.55
    g = bu.empty("poltrona", (px, py, 0), c)
    parts = [bu.box("pol_assento", (0.8, 0.7, 0.22), (0, 0, 0.32), M["fabric"], c, bevel=0.05),
             bu.box("pol_encosto", (0.8, 0.18, 0.62), (0, -0.30, 0.68), M["fabric"], c, bevel=0.06),
             bu.box("pol_braco_e", (0.14, 0.72, 0.36), (-0.4, 0, 0.5), M["fabric"], c, bevel=0.05),
             bu.box("pol_braco_d", (0.14, 0.72, 0.36), (0.4, 0, 0.5), M["fabric"], c, bevel=0.05),
             bu.box("pol_base", (0.84, 0.74, 0.1), (0, 0, 0.13), M["wood_d"], c, bevel=0.02)]
    for p in parts:
        p.parent = g
    g.rotation_euler = (0, 0, math.radians(200))
    bu.box("almofada", (0.62, 0.52, 0.1), (px, py + 0.02, 0.47), M["fabric"], C_dyn, bevel=0.04)
    am = bu.box("almofada_M", (0.62, 0.52, 0.1), (px, py + 0.02 - MY, 0.47), M["fabric"], C_dyn, bevel=0.04)
    am["mirror"] = True
    # quadro na parede direita
    bu.box("quadro", (0.03, 0.7, 0.5), (RW - 0.02, -1.0, 1.55), M["frame"], c, bevel=0.01)
    bu.box("quadro_tela", (0.01, 0.6, 0.4), (RW - 0.04, -1.0, 1.55), bu.mat("tela_quadro", (0.6, 0.35, 0.18), rough=0.8), c)


room_shell()
furniture()

# ------------------------------------------------------------------ luzes do quarto (animadas dia/noite)
L = {}
L["janela"] = bu.light("luz_janela", "AREA", (-RW - 0.5, 1.1, 1.6), 0, (1.0, 0.8, 0.6), size=1.3, rot=(0, -math.radians(90), 0), c=C_luz)
L["janela"].data.shape = "RECTANGLE"
L["janela"].data.size, L["janela"].data.size_y = 1.4, 1.4
L["sol"] = bu.light("luz_sol_chao", "SPOT", (-RW - 1.4, 1.1, 2.9), 0, (1.0, 0.78, 0.55), size=0.15,
                    rot=(0, 0, 0), c=C_luz, spot=40, blend=0.25)
bu.look_at(L["sol"], (0.0, 0.9, 0.0))
L["teto"] = bu.light("luz_teto", "AREA", (0, 0.2, RH - 0.05), 0, (1.0, 0.92, 0.82), size=2.2, c=C_luz)
L["abajur"] = bu.light("luz_abajur", "POINT", (1.0, 2.25, 0.92), 0, (1.0, 0.62, 0.3), size=0.08, c=C_luz)
L["rim"] = bu.light("luz_recorte", "AREA", (0.9, -1.6, 2.3), 0, (0.75, 0.85, 1.0), size=1.0, c=C_luz)
bu.look_at(L["rim"], (-0.3, 1.6, 1.2))
L["espelho"] = bu.light("luz_espelho", "AREA", ((MX0 + MX1) / 2, MY - 0.2, 1.1), 0, (0.4, 0.8, 1.0), size=1.4, c=C_luz)
bu.look_at(L["espelho"], ((MX0 + MX1) / 2, 0.5, 1.1))
L["espelho"].data.shape = "RECTANGLE"
L["espelho"].data.size, L["espelho"].data.size_y = 1.5, 2.0

# mundo
w = bpy.data.worlds.new("mundo")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.012, 0.012, 0.018, 1)
bg.inputs[1].default_value = 1.0


def lights_key(t, janela, sol, teto, abajur, rim, espelho=None, jcol=None, frame=None):
    fr = frame if frame is not None else F(t)
    for nm, v in (("janela", janela), ("sol", sol), ("teto", teto), ("abajur", abajur), ("rim", rim)):
        keyval(L[nm].data, "energy", fr, v)
    if jcol:
        keyval(L["janela"].data, "color", fr, jcol)
        keyval(L["sol"].data, "color", fr, jcol)


def emit_key(m, fr, v):
    ns = [n for n in m.node_tree.nodes if n.type == "EMISSION"]
    inp = ns[0].inputs[1] if ns else m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    inp.default_value = v
    inp.keyframe_insert("default_value", frame=fr)


DAY = dict(janela=900, sol=2600, teto=120, abajur=0, rim=260, espelho=0)
NIGHT = dict(janela=160, sol=0, teto=0, abajur=55, rim=140, espelho=0)
DAYC, NIGHTC = (1.0, 0.8, 0.6), (0.45, 0.6, 1.0)
lights_key(0, **DAY, jcol=DAYC)
lights_key(24.0, **DAY, jcol=DAYC, frame=F(24.2) - 1)
lights_key(24.2, **NIGHT, jcol=NIGHTC)
emit_key(M["sky_day"], 1, 1.2)
emit_key(M["sky_day"], F(24.2) - 1, 1.2)
emit_key(M["sky_day"], F(24.2), 0.0)
emit_key(M["lampshade"], 1, 0.0)
emit_key(M["lampshade"], F(24.2) - 1, 0.0)
emit_key(M["lampshade"], F(24.2), 2.5)

# brilho do espelho: pulsa quando mostra o futuro
GLOW_ON = [(0.0, 1.0), (2.8, 6.0), (4.2, 2.0), (10.3, 2.5), (12.6, 8.0), (13.6, 2.0), (15.0, 3.0), (15.8, 5.0),
           (16.6, 1.0), (18.4, 4.0), (19.9, 1.0), (21.4, 4.0), (22.6, 1.0), (24.2, 0.6), (27.4, 0.0),
           (35.9, 0.0), (36.8, 3.0), (38.2, 6.0), (43.2, 2.0), (46.3, 0.0), (54.0, 0.0), (56.0, 3.0), (61.0, 4.0)]
for t, v in GLOW_ON:
    emit_key(M["glow"], F(t), v)
    keyval(L["espelho"].data, "energy", F(t), v * 12)

# piscar das luzes (cena 5) — determinístico
import random
rnd = random.Random(7)
t = 38.3
while t < 43.0:
    on = rnd.random() > 0.45
    k = 1.0 if on else rnd.uniform(0.0, 0.25)
    lights_key(t, janela=160, sol=0, teto=0, abajur=55 * k, rim=140 * (0.4 + 0.6 * k), espelho=0)
    emit_key(M["lampshade"], F(t), 2.5 * k)
    t += rnd.uniform(0.06, 0.22)
lights_key(43.0, **NIGHT)
emit_key(M["lampshade"], F(43.0), 2.5)
# corrida: luz do quarto apaga em 46.3
lights_key(46.2, **NIGHT, frame=F(46.3) - 1)
emit_key(M["lampshade"], F(46.3) - 1, 2.5)
lights_key(46.3, janela=60, sol=0, teto=0, abajur=0, rim=0, espelho=0)
emit_key(M["lampshade"], F(46.3), 0.0)
for nm in L:
    if nm != "espelho":
        bu.all_linear_const(L[nm].data, "CONSTANT")
sky_o = bpy.data.objects["ceu_janela"]
bu.hide_anim(sky_o, [(1, True), (F(24.2), False)])
for gname in ("vidro_espelho", "vidro_janela_q"):
    bpy.data.objects[gname].visible_shadow = False

# ------------------------------------------------------------------ objetos dinâmicos (reais e gêmeos do espelho)
MIR = bu.empty("MUNDO_ESPELHO", (0, MY, 0), C_dyn, scale=(1, -1, 1))
bpy.data.objects["almofada_M"].parent = MIR


def to_mirror(ob):
    ob.parent = MIR
    return ob


def setpos(ob, xyz):
    if ob.parent == MIR:
        return (xyz[0], xyz[1] - MY, xyz[2])
    return tuple(xyz)


def kloc(ob, t, xyz, rot=None, frame=None):
    fr = frame if frame is not None else F(t)
    ob.location = setpos(ob, xyz)
    ob.keyframe_insert("location", frame=fr)
    if rot is not None:
        ob.rotation_euler = [math.radians(r) for r in rot]
        ob.keyframe_insert("rotation_euler", frame=fr)


def make_copo(name, mirror=False):
    o = bu.lathe(name, [(0.0, 0.004), (0.034, 0.0), (0.036, 0.004), (0.043, 0.13), (0.039, 0.13), (0.031, 0.008), (0.0, 0.012)],
                 (0, 0, 0), M["copo"], C_dyn)
    agua = bu.lathe(name + "_agua", [(0.0, 0.012), (0.033, 0.012), (0.038, 0.085), (0.0, 0.085)], (0, 0, 0),
                    bu.glass_mat("agua", tint=(0.75, 0.9, 1.0), refl=0.3), C_dyn)
    agua.parent = o
    if mirror:
        to_mirror(o)
    return o


def copo_fall(ob, t0):
    """copo tomba na mesinha, rola para a borda e cai no chão (≈0.75 s)."""
    tx, ty = TABLE
    top = 0.72
    x0, y0 = tx - 0.1, ty - 0.05
    kloc(ob, t0 - 0.05, (x0, y0, top), (0, 0, 0))
    kloc(ob, t0 + 0.12, (x0 + 0.02, y0, top + 0.01), (0, 25, 0))
    kloc(ob, t0 + 0.24, (x0 + 0.08, y0, top + 0.035), (0, 88, 0))
    kloc(ob, t0 + 0.36, (tx + 0.22, y0 - 0.03, top + 0.03), (0, 110, 30))
    kloc(ob, t0 + 0.5, (tx + 0.38, y0 - 0.06, 0.38), (0, 200, 60))
    kloc(ob, t0 + 0.62, (tx + 0.46, y0 - 0.1, 0.04), (0, 270, 80))
    kloc(ob, t0 + 0.72, (tx + 0.52, y0 - 0.12, 0.09), (0, 285, 95))
    kloc(ob, t0 + 0.82, (tx + 0.58, y0 - 0.15, 0.043), (0, 270, 110))
    kloc(ob, t0 + 1.4, (tx + 0.72, y0 - 0.2, 0.043), (0, 270, 160))


copo = make_copo("copo")
copo_m = make_copo("copo_M", mirror=True)
tx, ty = TABLE
# reflexo: cai em 3.35 ; real: cai em 8.0 ; volta à mesa na cena 3 (outro dia)
copo_fall(copo_m, 3.35)
kloc(copo, 0, (tx - 0.1, ty - 0.05, 0.72), (0, 0, 0))
copo_fall(copo, 8.0)
for ob in (copo, copo_m):
    kloc(ob, 14.9, (tx + 0.72, ty - 0.25, 0.043), (0, 270, 160))
    kloc(ob, 15.0, (tx - 0.1, ty - 0.05, 0.72), (0, 0, 0))
# no espelho, depois da queda prevista, o reflexo do copo acompanha o copo real
kloc(copo_m, 4.9, (tx + 0.72, ty - 0.2, 0.043), (0, 270, 160))
kloc(copo_m, 5.0, (tx - 0.1, ty - 0.05, 0.72), (0, 0, 0))
kloc(copo_m, 7.95, (tx - 0.1, ty - 0.05, 0.72), (0, 0, 0))
copo_fall(copo_m, 7.6)   # durante a cena 2 o espelho continua um pouco adiantado
bu.all_linear_const(copo, "BEZIER")

# vaso na estante
VASE0 = (-2.08, -1.15, 0.965)


def make_vase(name, mirror=False):
    o = bu.lathe(name, [(0.0, 0.0), (0.06, 0.0), (0.085, 0.08), (0.07, 0.2), (0.035, 0.26), (0.045, 0.3), (0.0, 0.3)],
                 (0, 0, 0), M["vase"], C_dyn)
    if mirror:
        to_mirror(o)
    return o


vase = make_vase("vaso")
vase_m = make_vase("vaso_M", True)
kloc(vase, 0, VASE0, (0, 0, 0))
kloc(vase_m, 0, VASE0, (0, 0, 0))
# no espelho: tomba, cai e se espatifa (15.25–15.85)
kloc(vase_m, 15.2, VASE0, (0, 0, 0))
kloc(vase_m, 15.4, (VASE0[0] + 0.12, VASE0[1], VASE0[2] + 0.02), (0, 35, 0))
kloc(vase_m, 15.55, (VASE0[0] + 0.3, VASE0[1] + 0.05, VASE0[2] - 0.2), (0, 80, 10))
kloc(vase_m, 15.78, (VASE0[0] + 0.45, VASE0[1] + 0.1, 0.05), (0, 120, 30))
bu.hide_anim(vase_m, [(1, True), (F(15.8), False), (F(16.7), True)])
kloc(vase_m, 16.6, VASE0, (0, 0, 0))
shards = []
for i in range(9):
    s = bu.box(f"caco_M_{i}", (0.05 + 0.02 * (i % 3), 0.04, 0.012), (0, 0, 0), M["vase"], C_dyn, rot=(0, 0, i))
    to_mirror(s)
    a = i * 2.39
    r = 0.15 + 0.07 * (i % 4)
    kloc(s, 15.8, (VASE0[0] + 0.45, VASE0[1] + 0.1, 0.05), (0, 0, i * 40))
    kloc(s, 16.1, (VASE0[0] + 0.45 + r * math.cos(a), VASE0[1] + 0.1 + r * math.sin(a), 0.012), (90 * (i % 2), 0, i * 40 + 120))
    bu.hide_anim(s, [(1, False), (F(15.8), True), (F(16.7), False)])
    shards.append(s)
# real: tomba em 17.0, ele pega em ~17.5
kloc(vase, 16.95, VASE0, (0, 0, 0))
kloc(vase, 17.15, (VASE0[0] + 0.12, VASE0[1], VASE0[2] + 0.02), (0, 35, 0))
kloc(vase, 17.32, (VASE0[0] + 0.3, VASE0[1] + 0.05, VASE0[2] - 0.15), (0, 80, 10))
# daqui o vaso segue a mão do protagonista (constraint Child Of animada)

# porta (dobradiça em DOOR_X0)
def make_door(name, mirror=False):
    piv = bu.empty(name, (DOOR_X0, RF, 0), C_dyn)
    d = bu.box(name + "_folha", (DOOR_X1 - DOOR_X0 - 0.02, 0.05, 2.08), ((DOOR_X1 - DOOR_X0) / 2, 0, 1.04), M["wood"], C_dyn, bevel=0.01)
    d.parent = piv
    h = bu.sphere(name + "_macaneta", 0.03, (DOOR_X1 - DOOR_X0 - 0.1, 0.06, 1.0), M["ribbon"], C_dyn)
    h.parent = piv
    h2 = bu.sphere(name + "_macaneta2", 0.03, (DOOR_X1 - DOOR_X0 - 0.1, -0.06, 1.0), M["ribbon"], C_dyn)
    h2.parent = piv
    if mirror:
        to_mirror(piv)
        piv.location = setpos(piv, (DOOR_X0, RF, 0))
    return piv


door = make_door("porta")
door_m = make_door("porta_M", True)


def door_key(ob, t, ang):
    ob.rotation_euler = (0, 0, math.radians(ang))
    ob.keyframe_insert("rotation_euler", frame=F(t))


for d in (door, door_m):
    door_key(d, 0, 0)
# no espelho abre em 18.6 ; real em 20.15 ; fecham depois
door_key(door_m, 18.55, 0)
door_key(door_m, 19.1, -80)
door_key(door_m, 19.85, -80)
door_key(door_m, 19.9, 0)
door_key(door_m, 20.15, 0)
door_key(door_m, 20.7, -80)
door_key(door, 20.15, 0)
door_key(door, 20.7, -80)
for d in (door, door_m):
    door_key(d, 21.35, -80)
    door_key(d, 21.4, 0)
    # fuga: a porta é aberta com força em 43.9
    door_key(d, 43.85, 0)
    door_key(d, 44.15, -105)

# presente
def make_gift(name, mirror=False):
    g = bu.box(name, (0.3, 0.3, 0.24), (0, 0, 0), M["gift"], C_dyn, bevel=0.01)
    r1 = bu.box(name + "_fita1", (0.31, 0.05, 0.25), (0, 0, 0), M["ribbon"], C_dyn)
    r2 = bu.box(name + "_fita2", (0.05, 0.31, 0.25), (0, 0, 0), M["ribbon"], C_dyn)
    lw = bu.sphere(name + "_laco", 0.06, (0, 0, 0.13), M["ribbon"], C_dyn, scale=(1.4, 0.6, 0.6))
    for o in (r1, r2, lw):
        o.parent = g
    if mirror:
        to_mirror(g)
    return g


gift = make_gift("presente")
gift_m = make_gift("presente_M", True)


# chaves
def make_keys(name, mirror=False):
    ring = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    for i in range(48):
        pass
    bm.free()
    k = bu.cylinder(name, 0.025, 0.006, (0, 0, 0), M["gold"], C_dyn, seg=24, rot=(math.radians(90), 0, 0))
    k1 = bu.box(name + "_k1", (0.012, 0.004, 0.07), (0.01, 0, -0.055), M["gold"], C_dyn)
    k2 = bu.box(name + "_k2", (0.012, 0.004, 0.065), (-0.012, 0, -0.05), M["gold"], C_dyn, rot=(0, 0.4, 0))
    for o in (k1, k2):
        o.parent = k
    if mirror:
        to_mirror(k)
    return k


keys = make_keys("chaves")
keys_m = make_keys("chaves_M", True)
KEY0 = (0.92, -1.42, 0.38)   # escondidas sob a almofada da poltrona
for o in (keys, keys_m):
    kloc(o, 0, KEY0, (90, 0, 30))

# ------------------------------------------------------------------ personagens
P_arm = pg.build("protagonista", M["body"], M["eye"], C_char)
R_arm = pg.build("reflexo", M["body"], M["eye_r"], C_char)
R_arm.parent = MIR
V_arm = pg.build("visitante", M["body_v"], M["eye"], C_char)
VM_arm = pg.build("visitante_M", M["body_v"], M["eye"], C_char)
VM_arm.parent = MIR
P, R, V, VM = pg.Actor(P_arm), pg.Actor(R_arm), pg.Actor(V_arm), pg.Actor(VM_arm)


def place(actor, t, xy, yaw, frame=None):
    fr = frame if frame is not None else F(t)
    a = actor.arm
    if a.parent == MIR:
        a.location = (xy[0], xy[1] - MY, 0)
    else:
        a.location = (xy[0], xy[1], 0)
    a.rotation_euler = (0, 0, math.radians(yaw))
    a.keyframe_insert("location", frame=fr)
    a.keyframe_insert("rotation_euler", frame=fr)


def cut_place(actor, t, xy, yaw):
    """teleporte num corte: chave no frame anterior repetindo o estado atual + nova chave"""
    fr = F(t)
    bpy.context.scene.frame_set(fr - 1)
    actor.arm.keyframe_insert("location", frame=fr - 1)
    actor.arm.keyframe_insert("rotation_euler", frame=fr - 1)
    place(actor, t, xy, yaw)


def cut_pose(actor, t, pose, hip=0.0):
    fr = F(t)
    bpy.context.scene.frame_set(fr - 1)
    for pb in actor.arm.pose.bones:
        pb.keyframe_insert("rotation_euler", frame=fr - 1)
    actor.arm.pose.bones["hips"].keyframe_insert("location", frame=fr - 1)
    actor.pose(t, pose, hip=hip)


def walk(actor, t0, t1, pts, run=False, upper=None):
    """locomoção respeitando o mundo do espelho"""
    a = actor.arm
    if a.parent == MIR:
        pts2 = [(x, y - MY) for (x, y) in pts]
    else:
        pts2 = pts
    actor.locomote(t0, t1, pts2, run=run, upper=upper)


def breathe(actor, t0, t1, base, amp=2.0, rate=0.32, heavy=False):
    t = t0
    i = 0
    while t <= t1:
        p = dict(base)
        s = math.sin(i * math.pi)
        cx, cy, cz = p["chest"]
        hx, hy, hz = p["head"]
        p["chest"] = (cx - amp * s, cy, cz)
        p["head"] = (hx + amp * 0.5 * s, hy, hz)
        if heavy:
            sx, sy, sz = p["spine"]
            p["spine"] = (sx + 3 * (1 + s), sy, sz)
        actor.pose(t, p)
        t += rate * (0.6 if heavy else 1.0) * 2.4
        i += 1


# poses-chave
def flipY(p):
    """inverte o giro (eixo Y) de tronco/pescoço/cabeça"""
    return dict(p)  # (verificado numericamente: os sinais originais já estavam corretos)


STAND = pg.P()
LOOK_R = flipY(pg.P(head=(8, -55, 0), neck=(0, -15, 0), chest=(-4, -8, 0)))
SCARED = flipY(pg.P(head=(-6, -45, 4), neck=(-4, -12, 0), chest=(-10, -8, 0), spine=(-4, 0, 0),
              upper_arm_L=(-25, 0, -18), forearm_L=(-60, 0, 0), upper_arm_R=(-30, 0, 20), forearm_R=(-65, 0, 0),
              thigh_L=(-6, 0, 0), shin_L=(10, 0, 0)))
JUMPBACK = flipY(pg.P(head=(-12, -30, 0), chest=(-14, -6, 0), spine=(-6, 0, 0), upper_arm_L=(-55, 0, -25),
                forearm_L=(-70, 0, 0), upper_arm_R=(-60, 0, 25), forearm_R=(-75, 0, 0),
                thigh_L=(-14, 0, 0), shin_L=(22, 0, 0), thigh_R=(10, 0, 0), shin_R=(12, 0, 0)))
LOOK_FLOOR = flipY(pg.P(head=(35, -35, 0), neck=(10, -10, 0), chest=(6, -6, 0), upper_arm_R=(-12, 0, 10), forearm_R=(-30, 0, 0)))
REACH_R = pg.P(upper_arm_R=(-82, 0, -6), forearm_R=(-6, 0, 0), hand_R=(-70, -80, 0), head=(4, 0, -6), chest=(3, 0, 0))
REACH_R_HALF = pg.P(upper_arm_R=(-40, 0, 4), forearm_R=(-50, 0, 0), hand_R=(-20, -30, 0), head=(2, 0, -4))
TOUCH_TILT = pg.P(upper_arm_R=(-84, 0, -6), forearm_R=(-4, 0, 0), hand_R=(-72, -80, 0), head=(6, 0, -14), chest=(4, 0, 0))
CROUCH = pg.P(hips=(0, 0, 0), spine=(30, 0, 0), chest=(15, 0, 0), head=(10, 0, 0), thigh_L=(-95, 0, 0), shin_L=(120, 0, 0),
              foot_L=(-25, 0, 0), thigh_R=(-70, 0, 0), shin_R=(130, 0, 0), foot_R=(-55, 0, 0),
              upper_arm_R=(-65, 0, 6), forearm_R=(-30, 0, 0), upper_arm_L=(-20, 0, -10), forearm_L=(-40, 0, 0))
CROUCH_HIP = -0.36
CROUCH_UP = dict(CROUCH, **{"upper_arm.R": (-120, 0, -10), "forearm.R": (-25, 0, 0), "head": (-15, 0, 0), "chest": (5, 0, 0)})
OPEN_ARMS = pg.P(upper_arm_L=(-45, 0, -35), forearm_L=(-55, 0, 0), upper_arm_R=(-45, 0, 35), forearm_R=(-55, 0, 0),
                 head=(-6, 0, 0), chest=(-4, 0, 0))
HOLD_BOX = pg.P(upper_arm_L=(-40, 0, -10), forearm_L=(-60, 0, 0), hand_L=(0, 0, 0), upper_arm_R=(-40, 0, 10),
                forearm_R=(-60, 0, 0), head=(10, 0, 0))
CATCH = pg.P(spine=(25, 0, 0), chest=(10, 0, 0), head=(-10, 0, 0), upper_arm_L=(-85, 0, -10), forearm_L=(-20, 0, 0),
             upper_arm_R=(-85, 0, 10), forearm_R=(-20, 0, 0), thigh_L=(-55, 0, 0), shin_L=(70, 0, 0),
             thigh_R=(30, 0, 0), shin_R=(35, 0, 0), foot_R=(30, 0, 0))
RELIEF = pg.P(spine=(8, 0, 0), head=(18, 0, 0), upper_arm_L=(-50, 0, -5), forearm_L=(-70, 0, 0), upper_arm_R=(-50, 0, 5),
              forearm_R=(-70, 0, 0))
RAISE_R = pg.P(upper_arm_R=(-165, 0, -15), forearm_R=(-15, 0, 0), head=(-4, 0, 0))
WAVE_A = pg.P(upper_arm_R=(-160, 0, 0), forearm_R=(-30, 0, 0), head=(-2, 0, 0))
WAVE_B = pg.P(upper_arm_R=(-160, 0, 25), forearm_R=(-5, 0, 0), head=(-2, 0, 0))
UNEASY = pg.P(upper_arm_R=(-30, 0, 10), forearm_R=(-60, 0, 0), upper_arm_L=(-10, 0, -10), forearm_L=(-40, 0, 0),
              chest=(-6, 0, 0), head=(-4, 0, 0))
STEPBACK = pg.P(upper_arm_R=(-20, 0, 12), forearm_R=(-45, 0, 0), upper_arm_L=(-15, 0, -12), forearm_L=(-45, 0, 0),
                chest=(-10, 0, 0), spine=(-4, 0, 0), head=(-6, 0, 0), thigh_R=(12, 0, 0), shin_R=(8, 0, 0))
DEFEND = pg.P(upper_arm_L=(-70, 0, -10), forearm_L=(-90, 0, 0), upper_arm_R=(-70, 0, 10), forearm_R=(-90, 0, 0),
              chest=(-14, 0, 0), spine=(-6, 0, 0), head=(-8, 0, 0))
FLINCH = pg.P(upper_arm_L=(-85, 0, -10), forearm_L=(-100, 0, 0), upper_arm_R=(-85, 0, 10), forearm_R=(-100, 0, 0),
              chest=(-20, 0, 0), spine=(-8, 0, 0), head=(12, 0, 0), thigh_R=(14, 0, 0))
LOOK_DOOR = pg.P(chest=(0, 40, 0), neck=(0, 30, 0), head=(4, 52, 0), spine=(0, 10, 0), upper_arm_L=(0, 0, -4))
STARE = pg.P(head=(10, 0, 0), chest=(4, 0, 0))
KNOCK_PRE = pg.P(upper_arm_L=(-95, 0, -14), forearm_L=(-55, 0, 0), hand_L=(-60, 70, 0), upper_arm_R=(-95, 0, 14),
                 forearm_R=(-55, 0, 0), hand_R=(-60, -70, 0), chest=(-6, 0, 0), head=(6, 0, 0))
KNOCK_HIT = pg.P(upper_arm_L=(-100, 0, -24), forearm_L=(-8, 0, 0), hand_L=(-80, 80, 0), upper_arm_R=(-100, 0, 24),
                 forearm_R=(-8, 0, 0), hand_R=(-80, -80, 0), chest=(8, 0, 0), head=(4, 0, 0))
PANT = pg.P(spine=(14, 0, 0), chest=(8, 0, 0), head=(-12, 0, 0), upper_arm_L=(-10, 0, -12), forearm_L=(-30, 0, 0),
            upper_arm_R=(-10, 0, 12), forearm_R=(-30, 0, 0))
OVER_SHOULDER = pg.P(chest=(0, -45, 0), neck=(0, -35, 0), head=(-4, -58, 0), spine=(0, -14, 0))

# ======================= PROTAGONISTA ==============================
# CENA 1 (0–7.2): imóvel diante do espelho; vira a cabeça assustado no fim
place(P, 0, A, 180)
breathe(P, 0, 5.4, STAND, amp=1.2)
P.pose(5.55, STAND)
P.pose(5.85, SCARED)
P.pose(7.1, SCARED)
# CENA 2 (7.2–15): copo real cai em 8.0; pulo para trás; olha o chão; olha o espelho
P.pose(7.25, LOOK_R)
P.pose(8.55, LOOK_R)
P.pose(8.8, JUMPBACK, hip=0.03)
place(P, 8.6, A, 180)
place(P, 8.95, (A[0] - 0.12, A[1] - 0.35), 195)
P.pose(9.3, JUMPBACK)
P.pose(9.7, LOOK_FLOOR)
P.pose(10.25, LOOK_FLOOR)
# mão no espelho: perto do vidro
M2 = (A[0] + 0.05, 1.85)
cut_place(P, 10.3, M2, 180)
cut_pose(P, 10.3, UNEASY)
P.pose(11.3, UNEASY)
P.pose(11.9, REACH_R_HALF)
P.pose(12.55, REACH_R)
P.pose(13.1, TOUCH_TILT)
P.pose(14.95, TOUCH_TILT)
# CENA 3a (15–18.4): vaso
B3 = (-0.75, 0.25)
cut_place(P, 15.0, B3, 180)
cut_pose(P, 15.0, STAND)
P.pose(16.2, STAND)
P.pose(16.55, OVER_SHOULDER)
place(P, 16.5, B3, 180)
walk(P, 16.6, 17.5, [B3, (-1.3, -0.4), (-1.72, -1.02)], run=True)
P.pose(17.5, CATCH, hip=-0.12)
place(P, 17.75, (-1.76, -1.06), -60)
P.pose(17.85, CATCH, hip=-0.14)
P.pose(18.35, RELIEF)
# CENA 3b (18.4–21.4): presente
B4 = (-0.3, 0.55)
cut_place(P, 18.4, B4, 180)
cut_pose(P, 18.4, STAND)
P.pose(19.3, STAND)
P.pose(19.75, pg.P(head=(0, 50, 0), neck=(0, 20, 0), chest=(0, 20, 0)))
cut_place(P, 19.9, (-0.45, -0.6), 0)
cut_pose(P, 19.9, OPEN_ARMS)
P.pose(20.6, OPEN_ARMS)
P.pose(20.95, HOLD_BOX)
P.pose(21.35, HOLD_BOX)
# CENA 3c (21.4–24.2): chaves
B5 = (0.15, 0.35)
cut_place(P, 21.4, B5, 180)
cut_pose(P, 21.4, STAND)
P.pose(22.0, STAND)
P.pose(22.45, pg.P(head=(0, 40, 0), chest=(0, 15, 0)))
cut_place(P, 22.6, (0.92, -0.98), 0)
cut_pose(P, 22.6, CROUCH, hip=CROUCH_HIP)
P.pose(23.05, dict(CROUCH, **{"upper_arm.R": (-75, 0, 4), "forearm.R": (-10, 0, 0)}), hip=CROUCH_HIP)
P.pose(23.35, CROUCH, hip=CROUCH_HIP)
P.pose(23.8, CROUCH_UP, hip=CROUCH_HIP + 0.04)
P.pose(24.15, CROUCH_UP, hip=CROUCH_HIP + 0.04)
# CENA 4 (24.2–33.3): noite
N0 = (0.95, -0.2)
cut_place(P, 24.2, N0, 140)
cut_pose(P, 24.2, STAND)
place(P, 24.55, N0, 140)
walk(P, 24.6, 26.6, [N0, (0.3, 0.6), A])
place(P, 26.95, A, 180)
P.pose(26.95, STAND)
breathe(P, 27.0, 28.3, STAND, amp=1.0)
P.pose(28.45, STAND)
P.pose(28.95, RAISE_R)
P.pose(29.3, WAVE_A)
P.pose(29.55, WAVE_B)
P.pose(29.8, WAVE_A)
P.pose(30.05, WAVE_B)
P.pose(30.4, RAISE_R)
P.pose(30.9, UNEASY)
# recua lentamente
place(P, 31.0, A, 180)
P.pose(31.0, UNEASY)
for i, (tt, dy) in enumerate([(31.6, -0.18), (32.3, -0.36), (33.0, -0.52)]):
    place(P, tt, (A[0], A[1] + dy), 180)
    P.pose(tt - 0.3, STEPBACK if i % 2 == 0 else UNEASY)
    P.pose(tt, UNEASY)
# CENA 5 (33.3–43.2)
A2 = (A[0], A[1] - 0.52)
breathe(P, 33.3, 37.9, UNEASY, amp=1.6, rate=0.25)
P.pose(38.1, DEFEND)
for i, tk in enumerate([38.45, 38.95, 39.45, 39.95, 40.4, 40.9, 41.5, 42.2]):
    P.pose(tk + 0.03, FLINCH)
    P.pose(tk + 0.25, DEFEND)
place(P, 38.4, A2, 180)
place(P, 41.0, (A2[0], A2[1] - 0.25), 180)
place(P, 42.5, (A2[0] + 0.05, A2[1] - 0.35), 180)
P.pose(42.75, DEFEND)
place(P, 42.75, (A2[0] + 0.05, A2[1] - 0.35), 180)
place(P, 43.15, (A2[0] + 0.05, A2[1] - 0.4), 360)
# CENA 6 (43.2–52.2): fuga
R0 = (A2[0] + 0.05, A2[1] - 0.4)
DOORC = ((DOOR_X0 + DOOR_X1) / 2, RF)
HALL_Y = -3.3
walk(P, 43.2, 45.5, [R0, (-0.4, -1.4), (DOORC[0], RF + 0.3), (DOORC[0], HALL_Y + 0.15), (DOORC[0] + 0.5, HALL_Y)], run=True)
walk(P, 45.5, 47.7, [(DOORC[0] + 0.5, HALL_Y), (3.0, HALL_Y)], run=True)
walk(P, 47.7, 49.3, [(3.0, HALL_Y), (3.55, HALL_Y)], run=False)
place(P, 49.5, (3.55, HALL_Y), 90)
P.pose(49.5, PANT)
breathe(P, 49.6, 54.0, PANT, amp=3.0, rate=0.3, heavy=True)
P.pose(54.4, pg.P(head=(-6, 0, 0), chest=(-2, 0, 0)))
P.pose(61.0, pg.P(head=(-6, 0, 0), chest=(-2, 0, 0)))

# ======================= REFLEXO (mundo do espelho) ==================
# Coordenadas = as do "protagonista do futuro" que ele representa.
place(R, 0, A, 180)
R.pose(0, flipY(pg.P(head=(4, -20, 0))))           # já está se mexendo no 1º frame
R.pose(0.8, flipY(pg.P(head=(18, -50, 0), neck=(4, -10, 0), chest=(2, -6, 0), upper_arm_R=(-20, 0, 12), forearm_R=(-30, 0, 0))))
R.pose(2.6, flipY(pg.P(head=(22, -54, 0), neck=(6, -12, 0), chest=(3, -8, 0), upper_arm_R=(-25, 0, 12), forearm_R=(-40, 0, 0))))
R.pose(3.3, flipY(pg.P(head=(26, -50, 0), neck=(8, -10, 0), chest=(4, -6, 0), upper_arm_R=(-30, 0, 15), forearm_R=(-50, 0, 0))))
R.pose(4.1, flipY(pg.P(head=(40, -40, 0), neck=(10, -10, 0), chest=(6, -6, 0), upper_arm_R=(-20, 0, 10), forearm_R=(-30, 0, 0))))
R.pose(5.0, LOOK_R)
R.pose(7.2, LOOK_R)
# cena 2: igual ao protagonista, ~0.4 s adiantado
R.pose(8.15, LOOK_R)
R.pose(8.4, JUMPBACK, hip=0.03)
place(R, 8.2, A, 180)
place(R, 8.55, (A[0] - 0.12, A[1] - 0.35), 195)
R.pose(8.9, JUMPBACK)
R.pose(9.3, LOOK_FLOOR)
R.pose(10.25, LOOK_FLOOR)
cut_place(R, 10.3, M2, 180)
cut_pose(R, 10.3, UNEASY)
R.pose(10.45, UNEASY)
R.pose(10.95, REACH_R_HALF)
R.pose(11.45, REACH_R)
R.pose(12.0, TOUCH_TILT)
R.pose(14.95, TOUCH_TILT)
# cena 3a
cut_place(R, 15.0, B3, 180)
cut_pose(R, 15.0, STAND)
R.pose(15.2, STAND)
R.pose(15.55, OVER_SHOULDER)
R.pose(16.5, OVER_SHOULDER)
# cena 3b: o reflexo já está virado para a porta com braços abertos
cut_place(R, 18.4, B4, 180)
cut_pose(R, 18.4, STAND)
R.pose(18.6, STAND)
R.pose(18.95, pg.P(head=(0, 50, 0), neck=(0, 20, 0), chest=(0, 20, 0)))
place(R, 19.0, B4, 180)
walk(R, 19.05, 19.6, [B4, (-0.45, -0.6)])
place(R, 19.75, (-0.45, -0.6), 0)
R.pose(19.75, OPEN_ARMS)
R.pose(19.88, OPEN_ARMS)
cut_place(R, 19.9, (-0.45, -0.6), 0)
# cena 3c: reflexo agachado na poltrona pegando as chaves
cut_place(R, 21.4, (0.92, -0.98), 0)
cut_pose(R, 21.4, CROUCH, hip=CROUCH_HIP)
R.pose(21.75, dict(CROUCH, **{"upper_arm.R": (-75, 0, 4), "forearm.R": (-10, 0, 0)}), hip=CROUCH_HIP)
R.pose(22.05, CROUCH, hip=CROUCH_HIP)
R.pose(22.4, CROUCH_UP, hip=CROUCH_HIP + 0.04)
R.pose(22.55, CROUCH_UP, hip=CROUCH_HIP + 0.04)
cut_place(R, 22.6, (0.92, -0.98), 0)
cut_pose(R, 22.6, CROUCH, hip=CROUCH_HIP)
R.pose(23.05, dict(CROUCH, **{"upper_arm.R": (-75, 0, 4), "forearm.R": (-10, 0, 0)}), hip=CROUCH_HIP)
R.pose(23.35, CROUCH, hip=CROUCH_HIP)
R.pose(23.8, CROUCH_UP, hip=CROUCH_HIP + 0.04)
# cena 4: anda junto (0.5 s adiantado) e PARA em 27.4
cut_place(R, 24.2, N0, 140)
cut_pose(R, 24.2, STAND)
walk(R, 24.2, 26.2, [N0, (0.3, 0.6), A])
place(R, 26.5, A, 180)
R.pose(26.5, STAND)
R.pose(27.4, pg.P(head=(2, 0, 0)))
R.pose(33.5, pg.P(head=(2, 0, 0)))
# cena 5: olha para a porta, depois para você, e bate no vidro
R.pose(34.7, LOOK_DOOR)
R.pose(35.85, LOOK_DOOR)
R.pose(36.8, STARE)
R.pose(37.9, STARE)
RK = (A[0], 1.92)
place(R, 37.9, A, 180)
walk(R, 37.95, 38.3, [A, RK])
place(R, 38.32, RK, 180)
R.pose(38.25, KNOCK_PRE)
for tk in [38.45, 38.95, 39.45, 39.95, 40.4, 40.9, 41.5, 42.2]:
    R.pose(tk - 0.16, KNOCK_PRE)
    R.pose(tk, KNOCK_HIT)
    R.pose(tk + 0.1, KNOCK_HIT)
R.pose(42.5, KNOCK_HIT)
R.pose(46.0, pg.P(upper_arm_L=(-80, 0, -10), forearm_L=(-15, 0, 0), hand_L=(-80, 80, 0), upper_arm_R=(-80, 0, 10),
                  forearm_R=(-15, 0, 0), hand_R=(-80, -80, 0), head=(14, 0, 0)))

# ======================= VISITANTES =================================
for act, mirror, t_in in ((V, False, 20.15), (VM, True, 18.6)):
    a = act.arm
    place(act, 0, (DOORC[0], -3.6), 0)
    act.pose(0, HOLD_BOX)
    place(act, t_in - 0.05, (DOORC[0] + 0.1, -3.2), 0)
    walk(act, t_in + 0.25, t_in + 1.15, [(DOORC[0] + 0.1, -3.2), (DOORC[0] + 0.05, -1.75)],
         upper={k: v for k, v in HOLD_BOX.items() if k.startswith(("upper_arm", "forearm", "hand"))})
    act.pose(t_in + 1.4, pg.P(upper_arm_L=(-55, 0, -10), forearm_L=(-40, 0, 0), upper_arm_R=(-55, 0, 10),
                              forearm_R=(-40, 0, 0), head=(-10, 0, 0), chest=(-8, 0, 0)), hip=0.02)
    act.pose(t_in + 1.6, pg.P(upper_arm_L=(-55, 0, -10), forearm_L=(-40, 0, 0), upper_arm_R=(-55, 0, 10),
                              forearm_R=(-40, 0, 0), head=(-10, 0, 0), chest=(-8, 0, 0)))
    for fr_, vis in [(1, False), (F(t_in - 0.3), True), (F(21.4), False)]:
        for pn in [a.name] + list(a["parts"]):
            o = bpy.data.objects[pn]
            o.hide_render = not vis
            o.keyframe_insert("hide_render", frame=fr_)
        if mirror and vis and fr_ > 1:
            pass
    for pn in [a.name] + list(a["parts"]):
        bu.all_const(bpy.data.objects[pn])

# visitante do espelho some quando o real entra (o espelho volta a refletir o presente)
for pn in [VM_arm.name] + list(VM_arm["parts"]):
    o = bpy.data.objects[pn]
    o.hide_render = True
    o.keyframe_insert("hide_render", frame=F(19.9))
    o.hide_render = False
    o.keyframe_insert("hide_render", frame=F(20.0))
    bu.all_const(o)
cut_place(VM, 20.0, (DOORC[0] + 0.1, -3.2), 0)
VM.pose(20.0, HOLD_BOX)
place(VM, 20.1, (DOORC[0] + 0.1, -3.2), 0)
walk(VM, 20.4, 21.3, [(DOORC[0] + 0.1, -3.2), (DOORC[0] + 0.05, -1.75)],
     upper={k: v for k, v in HOLD_BOX.items() if k.startswith(("upper_arm", "forearm", "hand"))})


# ======================= OBJETOS PRESOS ÀS MÃOS ======================
def attach_to_hand(ob, arm, bone, t_on, t_off=None, offset=(0, 0, 0), rot=(0, 0, 0)):
    """Child Of animado: o objeto passa a seguir a mão entre t_on e t_off."""
    con = ob.constraints.new("CHILD_OF")
    con.target = arm
    con.subtarget = bone
    con.use_scale_x = con.use_scale_y = con.use_scale_z = False
    con.set_inverse_pending = False
    con.inverse_matrix = Matrix.Identity(4)
    con.influence = 0.0
    con.keyframe_insert("influence", frame=F(t_on) - 1)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=F(t_on))
    if t_off:
        con.keyframe_insert("influence", frame=F(t_off) - 1)
        con.influence = 0.0
        con.keyframe_insert("influence", frame=F(t_off))
    return con


def hand_hold(ob, arm, bone, t_on, t_off, local_loc, local_rot=(0, 0, 0)):
    """Child Of animado. Enquanto preso, location/rotation do objeto são relativas à cabeça do osso."""
    bpy.context.view_layer.update()
    mirror = ob.parent == MIR
    con = ob.constraints.new("CHILD_OF")
    con.name = f"segura_{bone}_{t_on}"
    con.target = arm
    con.subtarget = bone
    con.use_scale_x = con.use_scale_y = con.use_scale_z = False
    con.inverse_matrix = MIR.matrix_world.inverted() if mirror else Matrix.Identity(4)
    f_on = F(t_on)
    bpy.context.scene.frame_set(f_on - 1)
    ob.keyframe_insert("location", frame=f_on - 1)
    ob.keyframe_insert("rotation_euler", frame=f_on - 1)
    con.influence = 0.0
    con.keyframe_insert("influence", frame=f_on - 1)
    con.influence = 1.0
    con.keyframe_insert("influence", frame=f_on)
    ob.location = local_loc
    ob.rotation_euler = [math.radians(r) for r in local_rot]
    ob.keyframe_insert("location", frame=f_on)
    ob.keyframe_insert("rotation_euler", frame=f_on)
    if t_off:
        f_off = F(t_off)
        con.keyframe_insert("influence", frame=f_off - 1)
        con.influence = 0.0
        con.keyframe_insert("influence", frame=f_off)
        ob.keyframe_insert("location", frame=f_off - 1)
        ob.keyframe_insert("rotation_euler", frame=f_off - 1)
    for fc in bu.fcurves_of(ob.animation_data.action):
        for kp in fc.keyframe_points:
            if "influence" in fc.data_path or int(round(kp.co.x)) in (f_on - 1, (F(t_off) - 1) if t_off else -9):
                kp.interpolation = "CONSTANT"


# vaso pego pela mão esquerda em 17.45 e segurado
hand_hold(vase, P_arm, "chest", 17.45, 18.4, (0.0, 0.0, 0.34), (0, 0, 0))
kloc(vase, 18.4, VASE0, (0, 0, 0))
# presente: visitante carrega; protagonista recebe
GL = (0.0, 0.1, 0.03)
GIFT_OFF = (0.0, -0.08, 0.3)
for gob, act, t_in in ((gift, V_arm, 20.15), (gift_m, VM_arm, 18.6)):
    kloc(gob, 0, (0, -6, -5))
    t_off = 21.4 if gob is gift else 19.9
    hand_hold(gob, act, "chest", t_in - 0.3, t_off, GIFT_OFF, (0, 0, 0))
    kloc(gob, t_off, (0, -6, -5))
hand_hold(gift_m, VM_arm, "chest", 20.0, 21.4, GIFT_OFF, (0, 0, 0))
kloc(gift_m, 21.4, (0, -6, -5))
# chaves: tiradas da poltrona
kloc(keys_m, 21.4, KEY0, (90, 0, 30))
hand_hold(keys_m, R_arm, "hand.R", 21.95, 22.6, (0.0, 0.08, 0.0), (0, 0, 90))
kloc(keys_m, 22.6, KEY0, (90, 0, 30))
hand_hold(keys_m, R_arm, "hand.R", 23.25, 24.2, (0.0, 0.08, 0.0), (0, 0, 90))
hand_hold(keys, P_arm, "hand.R", 23.25, 24.2, (0.0, 0.08, 0.0), (0, 0, 90))
kloc(keys, 24.2, KEY0, (90, 0, 30))
kloc(keys_m, 24.2, KEY0, (90, 0, 30))
emit_key(M["gold"], 1, 0.0)
emit_key(M["gold"], F(21.9), 0.0)
emit_key(M["gold"], F(22.2), 6.0)
emit_key(M["gold"], F(22.6), 0.5)
emit_key(M["gold"], F(23.2), 0.5)
emit_key(M["gold"], F(23.6), 6.0)
emit_key(M["gold"], F(24.2), 0.0)

# olhos do reflexo acendem (cena 5 e final)
def eye_key(m, t, v):
    emit_key(m, F(t), v)


eye_key(M["eye_r"], 0, 1.6)
eye_key(M["eye_r"], 36.2, 1.6)
eye_key(M["eye_r"], 36.9, 5.0)
eye_key(M["eye_r"], 46.0, 5.0)

# ======================= CORREDOR ===================================
def hallway():
    c = C_hall
    T = 0.1
    hx0 = -RW
    L_ = HX1 - hx0
    cy = (RF + HY0) / 2
    bu.box("c_piso", (L_ + 0.2, RF - HY0 + 0.2, 0.1), ((hx0 + HX1) / 2, cy, -0.05), M["floor"], c)
    bu.box("c_teto", (L_ + 0.2, RF - HY0 + 0.2, 0.1), ((hx0 + HX1) / 2, cy, RH + 0.05), M["ceil"], c)
    bu.box("c_parede_sul", (L_, T, RH), ((hx0 + HX1) / 2, HY0 - T / 2, RH / 2), M["wall2"], c)
    bu.box("c_parede_oeste", (T, RF - HY0, RH), (hx0 - T / 2, cy, RH / 2), M["wall2"], c)
    # parede norte além do quarto
    bu.box("c_parede_norte", (HX1 - RW, T, RH), ((RW + HX1) / 2, RF - T / 2, RH / 2), M["wall2"], c)
    # parede leste com janela (y -3.85..-2.85, z 0.85..2.15)
    wy0, wy1, wz0, wz1 = cy - 0.55, cy + 0.55, 0.8, 2.2
    x = HX1 + T / 2
    bu.box("c_leste_a", (T, wy0 - HY0, RH), (x, (wy0 + HY0) / 2, RH / 2), M["wall2"], c)
    bu.box("c_leste_b", (T, RF - wy1, RH), (x, (RF + wy1) / 2, RH / 2), M["wall2"], c)
    bu.box("c_leste_c", (T, wy1 - wy0, wz0), (x, cy, wz0 / 2), M["wall2"], c)
    bu.box("c_leste_d", (T, wy1 - wy0, RH - wz1), (x, cy, (RH + wz1) / 2), M["wall2"], c)
    for i, (sy, sz, ly, lz) in enumerate([(1.16, 0.06, cy, wz0), (1.16, 0.06, cy, wz1), (0.06, 1.46, wy0, 1.5),
                                         (0.06, 1.46, wy1, 1.5)]):
        bu.box(f"c_caixilho_{i}", (0.16, sy, sz), (HX1 + 0.02, ly, lz), M["frame"], c)
    bu.box("c_vidro", (0.01, wy1 - wy0, wz1 - wz0), (HX1 + 0.05, cy, (wz0 + wz1) / 2), bu.glass_mat("vidro_janela_noite", tint=(0.62, 0.68, 0.8), refl=0.12, rough=0.02), c)
    bu.box("c_rodape", (L_, 0.03, 0.1), ((hx0 + HX1) / 2, HY0 + 0.015, 0.05), M["trim"], c)
    # quadros e aparador
    bu.box("c_aparador", (1.0, 0.35, 0.8), (1.6, HY0 + 0.2, 0.4), M["wood_d"], c, bevel=0.02)
    bu.box("c_quadro1", (0.6, 0.03, 0.45), (1.6, HY0 + 0.02, 1.6), M["frame"], c)
    bu.box("c_quadro1t", (0.5, 0.01, 0.35), (1.6, HY0 + 0.04, 1.6), bu.mat("tela2", (0.2, 0.3, 0.45), rough=0.8), c)
    bu.box("c_quadro2", (0.45, 0.03, 0.6), (-1.4, HY0 + 0.02, 1.55), M["frame"], c)
    bu.box("c_quadro2t", (0.37, 0.01, 0.5), (-1.4, HY0 + 0.04, 1.55), bu.mat("tela3", (0.45, 0.2, 0.15), rough=0.8), c)
    lamps = []
    for i, lx in enumerate([-1.2, 0.9, 2.9]):
        bu.cylinder(f"c_luminaria_{i}", 0.16, 0.05, (lx, cy, RH - 0.03), M["bulb"], c)
        lt = bu.light(f"luz_corredor_{i}", "AREA", (lx, cy, RH - 0.08), 0, (1.0, 0.8, 0.55), size=0.35, c=c)
        lt.data.shape = "DISK"
        lamps.append(lt)
    return lamps


HL = hallway()
# lâmpadas do corredor: acesas (noite) e apagam uma a uma
for i, lt in enumerate(HL):
    keyval(lt.data, "energy", 1, 0)
    keyval(lt.data, "energy", F(24.2), 140)
for i, (lt, toff) in enumerate(zip(HL, [47.0, 47.85, 48.75])):
    keyval(lt.data, "energy", F(toff) - 1, 140)
    keyval(lt.data, "energy", F(toff), 0)
    bu.all_linear_const(lt.data, "CONSTANT")
emit_key(M["bulb"], 1, 0.0)
emit_key(M["bulb"], F(24.2), 3.0)
bulb_off = []
for i, toff in enumerate([47.0, 47.85, 48.75]):
    mm = bu.emit_mat(f"lampada_corredor_{i}", (1.0, 0.8, 0.55), 0.0)
    bpy.data.objects[f"c_luminaria_{i}"].data.materials[0] = mm
    emit_key(mm, 1, 0)
    emit_key(mm, F(24.2), 3.0)
    emit_key(mm, F(toff) - 1, 3.0)
    emit_key(mm, F(toff), 0.0)
    bu.all_linear_const(mm.node_tree, "CONSTANT")
moon_h = bu.light("luz_lua_corredor", "AREA", (HX1 + 0.6, -3.3, 1.6), 0, (0.4, 0.5, 0.9), size=1.0, c=C_hall)
bu.look_at(moon_h, (2.0, -3.3, 0.8))
keyval(moon_h.data, "energy", 1, 0)
keyval(moon_h.data, "energy", F(24.2), 25)
keyval(moon_h.data, "energy", F(48.75), 25)
keyval(moon_h.data, "energy", F(48.85), 45)
keyval(moon_h.data, "energy", F(50.0), 30)
rim_h = bu.light("luz_recorte_corredor", "AREA", (3.9, -3.9, 2.4), 0, (0.55, 0.7, 1.0), size=0.6, c=C_hall)
bu.look_at(rim_h, (3.4, -3.3, 1.3))
keyval(rim_h.data, "energy", 1, 0)
keyval(rim_h.data, "energy", F(48.75), 0)
keyval(rim_h.data, "energy", F(50.0), 30)

# ======================= MUNDO DO ESPELHO (instâncias) ===============
def instance(name, collection, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = collection
    e.location = loc
    e.rotation_euler = rot
    bu.link(e, C_dyn)
    if parent:
        e.parent = parent
    return e


for cc in (C_base, C_frente, C_luz):
    instance("espelho_" + cc.name, cc, MIR, loc=(0, -MY, 0))
# fora do quarto (vista pela porta no reflexo): o corredor espelhado
instance("espelho_corredor", C_hall, MIR, loc=(0, -MY, 0))

# ======================= QUARTO-FANTASMA (visto na janela) ===========
GH = bu.empty("QUARTO_FANTASMA", (7.0, -3.4, 0), C_ghost)
GH.rotation_euler = (0, 0, math.radians(-90))
instance("fantasma_base", C_base, GH)
instance("fantasma_fundo", C_fundo, GH)
G_arm = pg.build("reflexo_fantasma", M["body"], M["eye_r"], C_ghost)
G_arm.parent = GH
G = pg.Actor(G_arm)
G_arm.location = (A[0], A[1], 0)
G_arm.rotation_euler = (0, 0, math.radians(180))
G.pose(0, pg.P(head=(2, 0, 0)))
for pn in [G_arm.name] + list(G_arm["parts"]):
    bu.hide_anim(bpy.data.objects[pn], [(1, False), (F(54.0), True)])
G.pose(58.3, pg.P(head=(2, 0, 0)))
G.pose(59.9, OVER_SHOULDER)
G.pose(61.0, dict(OVER_SHOULDER, head=(-6, -62, 0)))
ghost_light = bu.light("luz_fantasma", "AREA", (0, 0, 0), 0, (0.35, 0.75, 1.0), size=1.6, c=C_ghost)
ghost_light.parent = GH
ghost_light.location = ((MX0 + MX1) / 2, MY - 0.25, 1.1)
ghost_light.rotation_euler = (math.radians(-90), 0, 0)
ghost_light.data.shape = "RECTANGLE"
ghost_light.data.size, ghost_light.data.size_y = 1.5, 2.0
for t, v in [(0, 0), (52.8, 0), (55.0, 420), (58.0, 480), (61.0, 560)]:
    keyval(ghost_light.data, "energy", F(t), v)
gpanel = bu.box("painel_fantasma", (MX1 - MX0 + 0.1, 0.02, MZ1 - MZ0 + 0.1), (0, 0, 0), bu.emit_mat("brilho_painel_fantasma", (0.35, 0.8, 1.0), 0.0), C_ghost)
gpanel.parent = GH
gpanel.location = ((MX0 + MX1) / 2, MY + 0.08, (MZ0 + MZ1) / 2)
for t, v in [(1, 0.0), (54.0, 0.0), (55.5, 1.6), (61.0, 2.2)]:
    emit_key(bpy.data.materials["brilho_painel_fantasma"], F(t) if t > 1 else 1, v)
ghost_rim = bu.light("luz_fantasma_recorte", "SPOT", (0, 0, 0), 0, (0.5, 0.75, 1.0), size=0.2, c=C_ghost, spot=30)
ghost_rim.parent = GH
ghost_rim.location = (A[0] + 1.2, A[1] - 2.0, 2.5)
for t, v in [(0, 0), (54.0, 0), (56.0, 260), (61.0, 320)]:
    keyval(ghost_rim.data, "energy", F(t), v)
# luzes do quarto fantasma acompanham o tempo (o espelho do fantasma brilha)
gm = bu.emit_mat("brilho_fantasma", (0.35, 0.85, 1.0), 0.0)
for nm in ("glow_e", "glow_d", "glow_c", "glow_b"):
    pass
emit_key(M["eye_r"], F(52.0), 5.0)

# ======================= CÂMERAS ====================================
SHOTS = []


def smooth(u):
    return u * u * (3 - 2 * u)


def shot(sid, t0, t1, p0, p1, g0, g1, lens=35, lens1=None, fstop=4.0, shake=0.004, ease=True, desc=""):
    cam = bu.camera("cam_" + sid, p0, g0, lens=lens, c=C_cam)
    tgt = bu.empty("alvo_" + sid, g0, C_cam)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = tgt
    cam.data.dof.aperture_fstop = fstop
    cam.data.clip_start = 0.02
    f0, f1 = F(t0), F(t1)
    for fr in list(range(f0 - 1, f1 + 2, 2)):
        u = min(1, max(0, (fr - f0) / max(1, f1 - f0)))
        us = smooth(u) if ease else u
        p = Vector(p0).lerp(Vector(p1), us)
        g = Vector(g0).lerp(Vector(g1), us)
        tt = fr / 30.0
        p += Vector((math.sin(tt * 1.7 + len(sid)) * shake, math.sin(tt * 1.3) * shake * 0.6, math.sin(tt * 2.1 + 1) * shake * 0.8))
        cam.location = p
        bu.look_at(cam, g)
        cam.keyframe_insert("location", frame=fr)
        cam.keyframe_insert("rotation_euler", frame=fr)
        tgt.location = g
        tgt.keyframe_insert("location", frame=fr)
        if lens1:
            cam.data.lens = lens + (lens1 - lens) * us
            cam.data.keyframe_insert("lens", frame=fr)
    m = sc.timeline_markers.new(sid, frame=f0)
    m.camera = cam
    SHOTS.append({"id": sid, "start": t0, "end": t1, "lens": lens, "desc": desc})
    return cam


mx = (MX0 + MX1) / 2
# --- CENA 1
shot("s01", 0.0, 3.0, (0.95, -0.75, 1.55), (0.75, -0.3, 1.5), (-0.1, 2.6, 1.25), (-0.15, 2.6, 1.2), lens=30, fstop=5.6,
     desc="Plano por cima do ombro: protagonista imóvel; o reflexo já se mexe e olha para o copo.")
shot("s02", 3.0, 4.4, (0.62, 0.15, 1.35), (0.25, 1.2, 1.12), (0.1, 3.4, 0.95), (0.25, 3.6, 0.8), lens=32, lens1=40, fstop=4,
     shake=0.006, desc="Aproximação rápida ao espelho: no reflexo, o copo cai.")
shot("s03", 4.4, 5.6, (0.05, 0.55, 0.95), (0.08, 0.62, 0.93), (tx - 0.1, ty - 0.05, 0.78), (tx - 0.1, ty - 0.05, 0.78), lens=55, fstop=2.0,
     desc="Inserto: o copo real continua parado na mesinha.")
shot("s04", 5.6, 7.2, (0.55, 1.78, 1.62), (0.48, 1.72, 1.63), (-0.36, 1.25, 1.64), (-0.37, 1.18, 1.64), lens=40, fstop=2.0,
     desc="Close do rosto: ele vira a cabeça, assustado.")
# --- CENA 2
shot("s05", 7.2, 10.3, (1.9, 0.0, 1.25), (1.75, 0.15, 1.2), (-0.1, 1.6, 0.75), (-0.15, 1.5, 0.8), lens=28, fstop=5.6,
     desc="Plano lateral: o copo real cai exatamente como no espelho; ele pula para trás.")
shot("s06", 10.3, 12.0, (-0.95, 0.75, 1.5), (-0.85, 0.95, 1.45), (0.05, 3.2, 1.25), (0.05, 3.1, 1.25), lens=40, fstop=4.0,
     desc="Por cima do ombro esquerdo: o reflexo levanta a mão antes dele.")
shot("s07", 12.0, 15.0, (0.75, 1.55, 1.45), (0.62, 1.7, 1.42), (-0.25, 2.5, 1.35), (-0.25, 2.5, 1.35), lens=35, fstop=2.8,
     desc="Perfil no vidro: as mãos se encontram; a dele chega atrasada.")
# --- CENA 3
shot("s08", 15.0, 16.6, (0.75, -0.45, 1.5), (0.6, -0.2, 1.45), (-0.6, 2.6, 1.0), (-0.65, 2.6, 0.95), lens=30, fstop=5.6,
     desc="No espelho, o vaso da estante (atrás dele) cai e se espatifa.")
shot("s09", 16.6, 18.4, (0.2, -0.3, 1.0), (-0.2, -0.45, 1.0), (-1.4, -0.6, 1.0), (-1.8, -1.0, 0.85), lens=24, fstop=5.6, shake=0.008,
     desc="Ele se vira, corre e pega o vaso no ar.")
shot("s10", 18.4, 19.9, (0.65, -0.25, 1.55), (0.55, -0.05, 1.5), (-0.4, 2.6, 1.1), (-0.4, 2.6, 1.1), lens=32, fstop=5.6,
     desc="No espelho: a porta se abre e alguém entra com um presente.")
shot("s11", 19.9, 21.4, (-0.1, 1.6, 1.45), (-0.2, 1.35, 1.4), (-0.45, -1.4, 1.1), (-0.45, -1.6, 1.05), lens=30, fstop=4.0,
     desc="Real: ele já espera de braços abertos quando a porta abre.")
shot("s12", 21.4, 22.6, (-0.55, 0.6, 1.4), (-0.5, 0.8, 1.35), (0.9, 3.8, 0.6), (0.9, 3.8, 0.6), lens=35, fstop=4.0,
     desc="No espelho: o reflexo tira as chaves de baixo da almofada.")
shot("s13", 22.6, 24.2, (-0.25, 0.05, 1.0), (-0.15, -0.05, 1.05), (0.9, -1.25, 0.55), (0.9, -1.15, 0.75), lens=32, fstop=2.4,
     desc="Real: ele encontra as chaves no mesmo lugar.")
# --- CENA 4 (noite)
shot("s14", 24.2, 27.6, (-2.0, -2.0, 2.3), (-1.85, -1.75, 2.2), (0.2, 1.3, 0.9), (-0.2, 1.4, 1.0), lens=24, fstop=8.0,
     desc="Noite. Plano geral alto: ele caminha até o espelho.")
shot("s15", 27.6, 30.8, (0.85, -0.5, 1.6), (0.6, 0.1, 1.55), (-0.25, 2.6, 1.3), (-0.3, 2.6, 1.35), lens=32, fstop=5.6,
     desc="Ele levanta o braço e acena; o reflexo não responde.")
shot("s16", 30.8, 33.3, (0.6, 2.2, 1.45), (0.55, 2.05, 1.45), (-0.4, 0.8, 1.35), (-0.4, 0.9, 1.4), lens=30, fstop=4.0,
     desc="Ângulo do espelho: ele recua devagar; o reflexo continua parado, mais perto do vidro.")
# --- CENA 5
shot("s17", 33.3, 35.7, (0.35, 0.6, 1.6), (0.25, 1.0, 1.58), (-0.35, 3.8, 1.45), (-0.35, 3.8, 1.5), lens=40, fstop=4.0,
     desc="O reflexo vira lentamente a cabeça para a porta.")
shot("s18", 35.7, 38.1, (-0.15, 1.35, 1.66), (-0.2, 1.65, 1.66), (-0.35, 3.8, 1.66), (-0.35, 3.8, 1.66), lens=60, fstop=2.8,
     desc="Close: o reflexo volta a cabeça e encara você.")
shot("s19", 38.1, 40.6, (1.15, 1.3, 1.45), (1.05, 1.45, 1.42), (-0.3, 2.5, 1.3), (-0.3, 2.45, 1.3), lens=26, fstop=5.6, shake=0.007,
     desc="Plano lateral: o reflexo bate as duas mãos no vidro; a luz oscila.")
shot("s20", 40.6, 43.2, (-0.35, 1.2, 1.45), (-0.3, 1.45, 1.42), (-0.35, 3.0, 1.35), (-0.35, 3.0, 1.35), lens=38, fstop=4.0, shake=0.01,
     desc="Ponto de vista: as palmas batendo no vidro, luz piscando.")
# --- CENA 6
shot("s21", 43.2, 45.6, (0.9, 1.6, 1.6), (0.3, -1.4, 1.5), (-0.3, -0.6, 1.0), (-0.45, -3.3, 1.0), lens=24, fstop=8.0, shake=0.012, ease=False,
     desc="Ele foge do quarto; câmera o persegue até a porta.")
shot("s22", 45.6, 49.4, (-0.2, -2.75, 1.35), (2.4, -2.75, 1.35), (0.6, -3.5, 1.0), (3.6, -3.4, 1.1), lens=22, fstop=8.0, shake=0.01, ease=False,
     desc="Corredor: ele corre; as luzes apagam uma a uma.")
shot("s23", 49.4, 52.2, (1.6, -2.85, 1.6), (2.0, -2.95, 1.6), (3.6, -3.3, 1.3), (3.7, -3.3, 1.35), lens=30, fstop=5.6,
     desc="Ele para diante da janela escura. Silêncio.")
# --- CENA 7
shot("s24", 52.2, 55.0, (2.4, -3.0, 1.62), (3.0, -3.12, 1.6), (4.2, -3.35, 1.45), (4.2, -3.35, 1.45), lens=32, lens1=36, fstop=4.0,
     desc="Câmera avança por cima do ombro em direção ao vidro.")
shot("s25", 55.0, 58.0, (3.75, -3.3, 1.5), (3.95, -3.3, 1.5), (8.0, -3.3, 1.25), (8.0, -3.3, 1.3), lens=40, lens1=48, fstop=4.0,
     desc="No vidro: o quarto, e o reflexo parado diante do espelho antigo.")
shot("s26", 58.0, 62.5, (3.95, -3.3, 1.5), (4.12, -3.3, 1.52), (8.2, -3.25, 1.55), (8.2, -3.25, 1.6), lens=55, lens1=75, fstop=2.8,
     desc="O reflexo vira a cabeça e encara a câmera. Corte seco para preto.")

# corte seco para preto em 61.0: câmera s26 olha para o vazio com tudo apagado
black = bu.box("tela_preta", (0.3, 0.3, 0.01), (0, 0, 0), bu.emit_mat("preto", (0, 0, 0), 0.0), C_cam)
black.parent = bpy.data.objects["cam_s26"]
black.location = (0, 0, -0.03)
bu.hide_anim(black, [(1, False), (F(61.0), True)])
black.visible_shadow = False

for ob in bpy.data.objects:
    if ob.type == "LIGHT":
        ob.visible_camera = False
        ob.visible_glossy = False
        ob.visible_transmission = False

# ======================= RENDER (padrão final; render.py ajusta) =====
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 12
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.03
sc.cycles.use_denoising = True
sc.cycles.denoiser = "OPENIMAGEDENOISE"
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 2
sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 8
sc.cycles.caustics_reflective = False
sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
sc.render.use_persistent_data = True
sc.render.film_transparent = False
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = 24
sc.eevee.use_shadows = True
sc.eevee.shadow_ray_count = 2
sc.eevee.shadow_step_count = 6
sc.eevee.use_fast_gi = True
sc.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
sc.view_settings.exposure = -0.35

json.dump(SHOTS, open(os.path.join(os.path.dirname(OUT), "storyboard", "shots.json"), "w"), indent=1, ensure_ascii=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
print("SALVO", OUT, "frames", sc.frame_start, sc.frame_end, "shots", len(SHOTS))
