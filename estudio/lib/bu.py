"""Utilitários Blender (bpy): materiais, primitivas, keyframes."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

FPS = 30


def F(t):
    """segundos -> frame (1-based)"""
    return int(round(t * FPS)) + 1


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    return sc


def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in p.children]:
        p.children.link(c)
    return c


def link(ob, c=None):
    for u in list(ob.users_collection):
        u.objects.unlink(ob)
    (c or bpy.context.scene.collection).objects.link(ob)
    return ob


# ---------------------------------------------------------------- materiais
def mat(name, color=(0.5, 0.5, 0.5), rough=0.6, metal=0.0, emit=None, emit_str=0.0,
        coat=0.0, sheen=0.0, alpha=1.0, spec=0.5):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.25
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def glass_mat(name, tint=(0.8, 0.9, 1.0), refl=0.12, rough=0.05, alpha_base=0.0):
    """Vidro barato: mistura transparente + brilho (fresnel). Funciona em Eevee e Cycles."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs[0].default_value = (*tint, 1)
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = rough
    fr = nt.nodes.new("ShaderNodeFresnel")
    fr.inputs["IOR"].default_value = 1.5
    mth = nt.nodes.new("ShaderNodeMath")
    mth.operation = "MULTIPLY_ADD"
    mth.inputs[1].default_value = 0.22
    mth.inputs[2].default_value = refl
    mth.use_clamp = True
    nt.links.new(fr.outputs[0], mth.inputs[0])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mth.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = "BLENDED"
    except Exception:
        pass
    return m


def emit_mat(name, color, strength):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*color, 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m


def setmat(ob, m):
    ob.data.materials.clear()
    ob.data.materials.append(m)
    return ob


# ---------------------------------------------------------------- primitivas
def box(name, size, loc=(0, 0, 0), m=None, c=None, bevel=0.0, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    link(ob, c)
    if bevel:
        md = ob.modifiers.new("bev", "BEVEL")
        md.width = bevel
        md.segments = 3
        md.limit_method = "NONE"
    if m:
        setmat(ob, m)
    return ob


def capsule(name, r, length, loc=(0, 0, 0), m=None, c=None, seg=24, rings=12, sx=1.0, sy=1.0):
    """cápsula ao longo de Z, centrada na origem; length = distância entre centros das calotas"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        if v.co.z > 1e-6:
            v.co.z += length / 2
        elif v.co.z < -1e-6:
            v.co.z -= length / 2
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    link(ob, c)
    if m:
        setmat(ob, m)
    return ob


def sphere(name, r, loc=(0, 0, 0), m=None, c=None, scale=(1, 1, 1), seg=32, rings=16):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    link(ob, c)
    if m:
        setmat(ob, m)
    return ob


def cylinder(name, r, h, loc=(0, 0, 0), m=None, c=None, seg=32, r2=None, cap=True, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    for f in bm.faces:
        f.smooth = len(f.verts) == 4
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = rot
    link(ob, c)
    if m:
        setmat(ob, m)
    return ob


def lathe(name, profile, loc=(0, 0, 0), m=None, c=None, seg=32):
    """perfil [(r,z),...] girado em Z (copos, vasos, abajures)"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rows = []
    for (r, z) in profile:
        row = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rows.append(row)
    for j in range(len(rows) - 1):
        for i in range(seg):
            f = bm.faces.new((rows[j][i], rows[j][(i + 1) % seg], rows[j + 1][(i + 1) % seg], rows[j + 1][i]))
            f.smooth = True
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    link(ob, c)
    if m:
        setmat(ob, m)
    return ob


def empty(name, loc=(0, 0, 0), c=None, scale=(1, 1, 1)):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    ob.scale = scale
    link(ob, c)
    return ob


def parent(child, par, keep=True):
    mw = child.matrix_world.copy()
    child.parent = par
    if keep:
        child.matrix_parent_inverse = par.matrix_world.inverted()
    return child


# ---------------------------------------------------------------- luzes / câmeras
def light(name, kind, loc, energy, color=(1, 1, 1), size=0.5, rot=(0, 0, 0), c=None, spot=None, blend=0.3):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = color
    if kind == "AREA":
        ld.size = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "SUN":
        ld.angle = size
    if kind == "SPOT" and spot:
        ld.spot_size = math.radians(spot)
        ld.spot_blend = blend
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    link(ob, c)
    return ob


def look_at(ob, target, roll=0.0):
    d = Vector(target) - ob.location
    q = d.to_track_quat("-Z", "Y")
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate_axis("Z", roll)


def camera(name, loc, target, lens=35, c=None, dof=None, fstop=2.8):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = 36
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    link(ob, c)
    look_at(ob, target)
    if dof is not None:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if isinstance(dof, bpy.types.Object):
            cd.dof.focus_object = dof
        else:
            cd.dof.focus_distance = dof
    return ob


# ---------------------------------------------------------------- keyframes
def key(ob, path, frame, value, index=-1, interp=None):
    if index >= 0:
        getattr(ob, path)[index] = value
    else:
        setattr(ob, path, value)
    ob.keyframe_insert(path, index=index, frame=frame)
    if interp:
        set_interp(ob, path, frame, interp)


def set_interp(idb, path, frame, interp):
    ad = idb.animation_data
    if not ad or not ad.action:
        return
    for fc in fcurves_of(ad.action):
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                if abs(kp.co.x - frame) < 0.5:
                    kp.interpolation = interp


def fcurves_of(action):
    """Blender 5 usa ações em camadas (slots); devolve todas as fcurves."""
    fcs = []
    if hasattr(action, "fcurves") and action.fcurves is not None:
        try:
            fcs.extend(list(action.fcurves))
        except Exception:
            pass
    if hasattr(action, "layers"):
        for L in action.layers:
            for s in L.strips:
                for cb in s.channelbags:
                    fcs.extend(list(cb.fcurves))
    return fcs


def keyval(idb, path, frame, value, index=-1):
    """keyframe em propriedade de datablock (ex.: light.data energy)"""
    if index >= 0:
        getattr(idb, path)[index] = value
    else:
        setattr(idb, path, value)
    idb.keyframe_insert(path, index=index, frame=frame)


def all_linear_const(idb, interp="LINEAR"):
    ad = idb.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def hide_anim(ob, frames_vis):
    """frames_vis: lista [(frame, visível)] -> anima hide_render/hide_viewport"""
    for fr, vis in frames_vis:
        ob.hide_render = not vis
        ob.hide_viewport = not vis
        ob.keyframe_insert("hide_render", frame=fr)
        ob.keyframe_insert("hide_viewport", frame=fr)
    all_const(ob)


def all_const(ob):
    ad = ob.animation_data
    if ad and ad.action:
        for fc in fcurves_of(ad.action):
            if fc.data_path in ("hide_render", "hide_viewport"):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
