"""Personagem humanoide minimalista com armature + API de animação por keyframes.

Convenções (personagem em repouso olhando para -Y, lado .L em +X):
  todos os ossos têm o eixo local X = +X do mundo, então rotação X (graus):
    spine/chest/neck/head  : + inclina para frente
    upper_arm / thigh      : - leva o membro para frente, + para trás
    forearm                : - dobra o cotovelo (antebraço para frente)
    shin                   : + dobra o joelho
    foot                   : + aponta os dedos para baixo
  rotação Y em spine/chest/neck/head = girar (+ vira para a esquerda do personagem, +X)
  rotação Z em upper_arm: .L negativo = abrir para fora; .R positivo = abrir para fora.
O objeto armature carrega a posição no chão (location) e a direção (rotation_euler.z).
"""
import bpy, math
from mathutils import Vector, Matrix
import bu

BONES = [
    # nome, head, tail, parent, eixo Z (roll)
    ("hips", (0, 0, 0.92), (0, 0, 1.02), None, (0, -1, 0)),
    ("spine", (0, 0, 1.02), (0, 0, 1.20), "hips", (0, -1, 0)),
    ("chest", (0, 0, 1.20), (0, 0, 1.42), "spine", (0, -1, 0)),
    ("neck", (0, 0, 1.42), (0, 0, 1.50), "chest", (0, -1, 0)),
    ("head", (0, 0, 1.50), (0, 0, 1.80), "neck", (0, -1, 0)),
]
for s, sx in (("L", 1), ("R", -1)):
    BONES += [
        (f"upper_arm.{s}", (0.215 * sx, 0, 1.385), (0.235 * sx, 0, 1.11), "chest", (0, 1, 0)),
        (f"forearm.{s}", (0.235 * sx, 0, 1.11), (0.245 * sx, 0, 0.86), f"upper_arm.{s}", (0, 1, 0)),
        (f"hand.{s}", (0.245 * sx, 0, 0.86), (0.245 * sx, 0, 0.75), f"forearm.{s}", (0, 1, 0)),
        (f"thigh.{s}", (0.10 * sx, 0, 0.92), (0.10 * sx, 0, 0.50), "hips", (0, 1, 0)),
        (f"shin.{s}", (0.10 * sx, 0, 0.50), (0.10 * sx, 0, 0.085), f"thigh.{s}", (0, 1, 0)),
        (f"foot.{s}", (0.10 * sx, 0, 0.085), (0.10 * sx, -0.15, 0.04), f"shin.{s}", (0, 0, -1)),
    ]
BONE_NAMES = [b[0] for b in BONES]


def build(name, body_mat, eye_mat, c=None, loc=(0, 0, 0), yaw=0.0, accent_mat=None):
    ad = bpy.data.armatures.new(name + "_rig")
    arm = bpy.data.objects.new(name, ad)
    bu.link(arm, c)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for (n, h, t, p, z) in BONES:
        b = ad.edit_bones.new(n)
        b.head, b.tail = Vector(h), Vector(t)
        b.align_roll(Vector(z))
        if p:
            b.parent = eb[p]
            b.use_connect = (Vector(h) - eb[p].tail).length < 1e-4
        eb[n] = b
    bpy.ops.object.mode_set(mode="OBJECT")
    ad.display_type = "STICK"
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
    bpy.context.view_layer.update()

    parts = []

    def attach(ob, bone, world_loc, rot=None):
        mw = Matrix.Translation(Vector(world_loc))
        if rot is not None:
            mw = mw @ rot.to_4x4()
        ob.parent = arm
        ob.parent_type = "BONE"
        ob.parent_bone = bone
        bpy.context.view_layer.update()
        pbm = arm.matrix_world @ arm.pose.bones[bone].matrix
        # filho de osso fica relativo à cauda do osso
        tail = Matrix.Translation(Vector((0, arm.pose.bones[bone].length, 0)))
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = (pbm @ tail).inverted() @ mw
        parts.append(ob)
        return ob

    B = body_mat
    attach(bu.capsule(name + "_pelvis", 0.125, 0.05, m=B, c=c, sx=1.2, sy=0.85), "hips", (0, 0, 0.95))
    attach(bu.capsule(name + "_abdomen", 0.13, 0.12, m=B, c=c, sx=1.12, sy=0.8), "spine", (0, 0, 1.12))
    attach(bu.capsule(name + "_chest", 0.155, 0.13, m=B, c=c, sx=1.28, sy=0.78), "chest", (0, 0, 1.30))
    attach(bu.capsule(name + "_neck", 0.05, 0.08, m=B, c=c), "neck", (0, 0, 1.47))
    attach(bu.sphere(name + "_head", 0.165, m=B, c=c, scale=(1.0, 0.96, 1.1)), "head", (0, 0, 1.665))
    for s, sx in (("L", 1), ("R", -1)):
        e = bu.sphere(name + f"_eye.{s}", 0.024, m=eye_mat, c=c, scale=(1.0, 0.45, 1.45), seg=16, rings=8)
        attach(e, "head", (0.062 * sx, -0.152, 1.69))
        attach(bu.sphere(name + f"_shoulder.{s}", 0.068, m=B, c=c), f"upper_arm.{s}", (0.215 * sx, 0, 1.375))
        attach(bu.capsule(name + f"_uarm.{s}", 0.055, 0.2, m=B, c=c), f"upper_arm.{s}", (0.225 * sx, 0, 1.25))
        attach(bu.capsule(name + f"_farm.{s}", 0.048, 0.2, m=B, c=c), f"forearm.{s}", (0.24 * sx, 0, 0.985))
        attach(bu.sphere(name + f"_hand.{s}", 0.052, m=B, c=c, scale=(0.6, 0.95, 1.3)), f"hand.{s}", (0.247 * sx, -0.005, 0.80))
        th = bu.capsule(name + f"_thumb.{s}", 0.018, 0.04, m=B, c=c)
        attach(th, f"hand.{s}", (0.235 * sx, -0.045, 0.825), rot=Matrix.Rotation(math.radians(30), 3, "X"))
        attach(bu.capsule(name + f"_thigh.{s}", 0.075, 0.3, m=B, c=c), f"thigh.{s}", (0.10 * sx, 0, 0.71))
        attach(bu.capsule(name + f"_shin.{s}", 0.06, 0.33, m=B, c=c), f"shin.{s}", (0.10 * sx, 0, 0.30))
        ft = bu.capsule(name + f"_foot.{s}", 0.055, 0.12, m=accent_mat or B, c=c, sx=1.0, sy=1.0)
        ft.scale = (1, 1, 1)
        attach(ft, f"foot.{s}", (0.10 * sx, -0.055, 0.045),
               rot=Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Diagonal((1.0, 0.6, 1.0)))
    arm.location = loc
    arm.rotation_euler = (0, 0, yaw)
    arm["parts"] = [p.name for p in parts]
    return arm


# ------------------------------------------------------------------ poses
NEUTRAL = {
    "hips": (0, 0, 0), "spine": (0, 0, 0), "chest": (0, 0, 0), "neck": (0, 0, 0), "head": (0, 0, 0),
    "upper_arm.L": (0, 0, -6), "upper_arm.R": (0, 0, 6),
    "forearm.L": (-8, 0, 0), "forearm.R": (-8, 0, 0),
    "hand.L": (0, 0, 0), "hand.R": (0, 0, 0),
    "thigh.L": (0, 0, 0), "thigh.R": (0, 0, 0),
    "shin.L": (0, 0, 0), "shin.R": (0, 0, 0),
    "foot.L": (0, 0, 0), "foot.R": (0, 0, 0),
}


def P(**kw):
    """pose a partir do neutro; nomes com '_' em vez de '.': upper_arm_L=(x,y,z)"""
    d = dict(NEUTRAL)
    for k, v in kw.items():
        n = k.replace("_L", ".L").replace("_R", ".R") if k.endswith(("_L", "_R")) else k
        d[n] = v
    return d


class Actor:
    def __init__(self, arm):
        self.arm = arm
        self.hip_h = {}  # frame -> altura extra do quadril

    # pose de ossos ---------------------------------------------------
    def pose(self, t, pose, bones=None, hip=0.0, frame=None):
        fr = frame if frame is not None else bu.F(t)
        for n, (x, y, z) in pose.items():
            if bones and n not in bones:
                continue
            pb = self.arm.pose.bones[n]
            pb.rotation_euler = (math.radians(x), math.radians(y), math.radians(z))
            pb.keyframe_insert("rotation_euler", frame=fr)
        if bones is None or "hips" in bones:
            pb = self.arm.pose.bones["hips"]
            pb.location = (0, hip, 0)
            pb.keyframe_insert("location", frame=fr)

    def hold(self, t0, t1, pose, hip=0.0):
        self.pose(t0, pose, hip=hip)
        self.pose(t1, pose, hip=hip)

    # posição / direção no chão ----------------------------------------
    def place(self, t, xy, yaw_deg, frame=None):
        fr = frame if frame is not None else bu.F(t)
        self.arm.location = (xy[0], xy[1], 0)
        self.arm.rotation_euler = (0, 0, math.radians(yaw_deg))
        self.arm.keyframe_insert("location", frame=fr)
        self.arm.keyframe_insert("rotation_euler", frame=fr)

    def turn(self, t0, t1, xy, yaw0, yaw1):
        self.place(t0, xy, yaw0)
        self.place(t1, xy, yaw1)

    # locomoção ---------------------------------------------------------
    def locomote(self, t0, t1, pts, run=False, step=2, upper=None, end_pose=None, yaw_end=None):
        """anda/corre pela polilinha pts [(x,y),...] entre t0 e t1 (velocidade constante)."""
        segs = []
        tot = 0.0
        for a, b in zip(pts[:-1], pts[1:]):
            L = (Vector(b) - Vector(a)).length
            segs.append((Vector(a), Vector(b), L))
            tot += L
        stride = 0.8 if run else 0.62  # metros por meio ciclo (um passo)
        f0, f1 = bu.F(t0), bu.F(t1)
        bpy.context.scene.frame_set(f0)
        yaw_prev = math.degrees(self.arm.rotation_euler.z)
        for fr in list(range(f0, f1, step)) + [f1]:
            u = (fr - f0) / max(1, f1 - f0)
            # suaviza arranque/parada
            us = u
            d = us * tot
            acc = 0.0
            pos, dirv = Vector(pts[-1]), (segs[-1][1] - segs[-1][0]).normalized()
            for a, b, L in segs:
                if d <= acc + L or (a, b, L) == segs[-1]:
                    k = 0 if L == 0 else min(1, (d - acc) / L)
                    pos = a.lerp(b, k)
                    dirv = (b - a).normalized() if L > 0 else dirv
                    break
                acc += L
            yaw = math.degrees(math.atan2(dirv.x, -dirv.y))
            if yaw_prev is not None:
                while yaw - yaw_prev > 180: yaw -= 360
                while yaw - yaw_prev < -180: yaw += 360
            yaw_prev = yaw
            self.place(None, pos, yaw, frame=fr)
            ph = math.pi * d / stride
            amp = min(1.0, d / 0.25, (tot - d) / 0.25 + 0.15) if tot > 0 else 0
            self.pose(None, gait(ph, run, amp, upper), frame=fr, hip=gait_hip(ph, run, amp))
        if end_pose is not None:
            self.pose(t1 + 0.25, end_pose)
        if yaw_end is not None:
            self.place(t1 + 0.3, pts[-1], yaw_end)


def gait(ph, run=False, amp=1.0, upper=None):
    s, c = math.sin(ph), math.cos(ph)
    A = (42 if run else 24) * amp
    K = (85 if run else 38) * amp
    AR = (55 if run else 18) * amp
    lean = (14 if run else 3) * min(1, amp * 2)
    p = dict(NEUTRAL)
    p["thigh.L"] = (-A * s, 0, 0)
    p["thigh.R"] = (A * s, 0, 0)
    p["shin.L"] = (6 * amp + K * max(0.0, c) ** 1.3, 0, 0)
    p["shin.R"] = (6 * amp + K * max(0.0, -c) ** 1.3, 0, 0)
    p["foot.L"] = (-0.35 * (-A * s) - 0.25 * p["shin.L"][0] + 6, 0, 0)
    p["foot.R"] = (-0.35 * (A * s) - 0.25 * p["shin.R"][0] + 6, 0, 0)
    p["upper_arm.L"] = (AR * s, 0, -8)
    p["upper_arm.R"] = (-AR * s, 0, 8)
    el = -70 if run else -14
    p["forearm.L"] = (el - 10 * amp * max(0, -s), 0, 0)
    p["forearm.R"] = (el - 10 * amp * max(0, s), 0, 0)
    p["spine"] = (lean * 0.5, 4 * amp * s, 0)
    p["chest"] = (lean * 0.5, -7 * amp * s, 0)
    p["head"] = (-lean * 0.6, 3 * amp * s, 0)
    p["hips"] = (0, -5 * amp * s, 0)
    if upper:
        p.update(upper)
    return p


def gait_hip(ph, run, amp):
    return (-(0.05 if run else 0.022) * abs(math.cos(ph)) + (0.0 if run else 0.01)) * amp - (0.04 if run else 0) * amp
