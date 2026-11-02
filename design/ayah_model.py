"""
AYAH by INOMA — modèle conceptuel v2 (Blender 5.x), fidèle à l'image de référence.
Usage :  blender -b -P ayah_model.py -- [ivory|black|grey] [preview|final]

Principe : chaque partie de l'arche est une région 2D (vue de face) "gonflée" en volume
avec un profil arrondi -> formes sculptées, arêtes fines, épaisseur qui s'affine vers le haut.
Cotes en mm.
"""
import bpy, bmesh, math, sys, os
import numpy as np
from collections import Counter
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VARIANT = argv[0] if len(argv) > 0 else "ivory"
QUALITY = argv[1] if len(argv) > 1 else "preview"
MM = 0.001

# ------------------------------------------------------------------ paramètres
BASE_A, BASE_B = 84, 54          # demi-axes de l'ovale de la base
BASE_Z0, BASE_TOP = 9, 47        # corps de la base (au-dessus du liseré LED et des pieds)
ARCH_SX, ARCH_SZ = 0.95, 0.90    # échelle globale de l'arche (largeur, hauteur)
SPHERE_R = 24
PANEL = dict(x0=-55, x1=45, z0=15, z1=42, slant=7)   # vitre noire galbée (parallélogramme)
KNOB = dict(x=66, z=28.5, r=13, L=15)

COLORS = {
    "ivory": dict(body=(0.80, 0.73, 0.61), metal=(1.0, 0.72, 0.38), mrough=0.25),
    "black": dict(body=(0.016, 0.015, 0.014), metal=(1.0, 0.72, 0.38), mrough=0.25),
    "grey":  dict(body=(0.25, 0.25, 0.26), metal=(0.92, 0.93, 0.95), mrough=0.2),
}[VARIANT]

# Contours de l'arche (vue de face, x vers la droite, z vers le haut, z=0 = dessus de la base).
# Chaque contour = côté gauche (pied -> pointe) puis côté droit (pointe -> pied).
OUTER = ([(-70, -6), (-74, 20), (-78, 50), (-74, 85), (-62, 118), (-42, 148), (-18, 170), (5, 184), (20, 191)],
         [(20, 191), (28, 175), (40, 152), (55, 120), (66, 85), (71, 45), (72, -6)])
BAND_OUT = ([(-52, -6), (-55, 20), (-58, 50), (-55, 82), (-46, 112), (-30, 138), (-12, 156), (6, 168), (14, 172)],
            [(14, 172), (22, 160), (33, 140), (46, 112), (55, 80), (60, 45), (60, -6)])
BAND_IN = ([(-36, -6), (-38, 20), (-40, 50), (-37, 80), (-29, 106), (-16, 128), (-2, 143), (8, 150)],
           [(8, 150), (17, 141), (27, 124), (38, 100), (47, 72), (51, 40), (52, -6)])
INNER = ([(-29, -6), (-31, 20), (-33, 50), (-30, 78), (-23, 102), (-11, 122), (1, 135), (6, 140)],
         [(6, 140), (13, 133), (22, 117), (32, 95), (40, 70), (44, 40), (45, -6)])

# ------------------------------------------------------------------ scène
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.length_unit = 'MILLIMETERS'
coll = bpy.context.collection


# ------------------------------------------------------------------ matériaux
def principled(name, color, metallic=0.0, rough=0.5, coat=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.03
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


WARM = (1.0, 0.60, 0.27)
mat_body = principled("Body", COLORS["body"], rough=0.42)
mat_body.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 0.15
mat_metal = principled("Metal", COLORS["metal"], metallic=1.0, rough=COLORS["mrough"])
mat_glow = principled("LEDCore", (0, 0, 0), emit=(1.0, 0.66, 0.33), strength=9)
mat_glow_soft = principled("LEDLine", (0, 0, 0), emit=WARM, strength=4)
mat_dark = principled("Dark", (0.015, 0.013, 0.012), rough=0.5)


def N(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k == "op":
            n.operation = v
        else:
            n.inputs[k].default_value = v
    return n


def star_distance(nt, vec):
    """Distance « étoile à 8 branches » dans une cellule unitaire (pavage islamique simple)."""
    sep = N(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(vec, sep.inputs[0])
    absd = []
    for i in (0, 1):
        f = N(nt, "ShaderNodeMath", op='FRACT')
        nt.links.new(sep.outputs[i], f.inputs[0])
        c = N(nt, "ShaderNodeMath", op='SUBTRACT')
        nt.links.new(f.outputs[0], c.inputs[0])
        c.inputs[1].default_value = 0.5
        a = N(nt, "ShaderNodeMath", op='ABSOLUTE')
        nt.links.new(c.outputs[0], a.inputs[0])
        absd.append(a.outputs[0])
    d1 = N(nt, "ShaderNodeMath", op='MAXIMUM')
    nt.links.new(absd[0], d1.inputs[0]); nt.links.new(absd[1], d1.inputs[1])
    s = N(nt, "ShaderNodeMath", op='ADD')
    nt.links.new(absd[0], s.inputs[0]); nt.links.new(absd[1], s.inputs[1])
    d2 = N(nt, "ShaderNodeMath", op='MULTIPLY')
    nt.links.new(s.outputs[0], d2.inputs[0]); d2.inputs[1].default_value = 0.7071
    d = N(nt, "ShaderNodeMath", op='MINIMUM')
    nt.links.new(d1.outputs[0], d.inputs[0]); nt.links.new(d2.outputs[0], d.inputs[1])
    return d.outputs[0]


def band_mask(nt, value, lo, hi):
    mr = N(nt, "ShaderNodeMapRange")
    nt.links.new(value, mr.inputs["Value"])
    mr.inputs["From Min"].default_value = lo
    mr.inputs["From Max"].default_value = hi
    mr.inputs["To Min"].default_value = 1
    mr.inputs["To Max"].default_value = 0
    return mr.outputs[0]


def sphere_material():
    m = bpy.data.materials.new("Sphere")
    nt = m.node_tree
    nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial")
    uv = N(nt, "ShaderNodeTexCoord")
    mp = N(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (16, 8, 1)
    nt.links.new(uv.outputs["UV"], mp.inputs[0])
    d = star_distance(nt, mp.outputs[0])
    holes = band_mask(nt, d, 0.27, 0.29)
    shell = N(nt, "ShaderNodeBsdfPrincipled")
    shell.inputs["Base Color"].default_value = (0.93, 0.87, 0.76, 1)
    shell.inputs["Roughness"].default_value = 0.45
    shell.inputs["Emission Color"].default_value = (*WARM, 1)
    shell.inputs["Emission Strength"].default_value = 1.2
    hole = N(nt, "ShaderNodeEmission")
    hole.inputs["Color"].default_value = (1.0, 0.74, 0.42, 1)
    hole.inputs["Strength"].default_value = 14
    mix = N(nt, "ShaderNodeMixShader")
    nt.links.new(holes, mix.inputs["Fac"])
    nt.links.new(shell.outputs[0], mix.inputs[1])
    nt.links.new(hole.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def inlay_material():
    """Disque noir avec réseau d'étoiles doré (socle sous la sphère)."""
    m = bpy.data.materials.new("Inlay")
    nt = m.node_tree
    nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial")
    tc = N(nt, "ShaderNodeTexCoord")
    mp = N(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (110, 110, 110)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    d = star_distance(nt, mp.outputs[0])
    off = N(nt, "ShaderNodeMath", op='SUBTRACT')
    nt.links.new(d, off.inputs[0]); off.inputs[1].default_value = 0.3
    ab = N(nt, "ShaderNodeMath", op='ABSOLUTE')
    nt.links.new(off.outputs[0], ab.inputs[0])
    lines = band_mask(nt, ab.outputs[0], 0.02, 0.04)
    dark = N(nt, "ShaderNodeBsdfPrincipled")
    dark.inputs["Base Color"].default_value = (0.012, 0.011, 0.01, 1)
    dark.inputs["Roughness"].default_value = 0.35
    gold = N(nt, "ShaderNodeBsdfPrincipled")
    gold.inputs["Base Color"].default_value = (*COLORS["metal"], 1)
    gold.inputs["Metallic"].default_value = 1
    gold.inputs["Roughness"].default_value = 0.3
    mix = N(nt, "ShaderNodeMixShader")
    nt.links.new(lines, mix.inputs["Fac"])
    nt.links.new(dark.outputs[0], mix.inputs[1])
    nt.links.new(gold.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def panel_material():
    m = bpy.data.materials.new("FrontPanel")
    nt = m.node_tree
    nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial")
    uv = N(nt, "ShaderNodeTexCoord")
    tex = N(nt, "ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(HERE, "panel_ui.png"))
    tex.extension = 'CLIP'
    nt.links.new(uv.outputs["UV"], tex.inputs[0])
    glass = N(nt, "ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1)
    glass.inputs["Roughness"].default_value = 0.08
    glass.inputs["Coat Weight"].default_value = 0.6
    glass.inputs["Coat Roughness"].default_value = 0.02
    glass.inputs["Emission Strength"].default_value = 1.5
    nt.links.new(tex.outputs["Color"], glass.inputs["Emission Color"])
    nt.links.new(glass.outputs[0], out.inputs["Surface"])
    return m


def marble_material():
    m = bpy.data.materials.new("Marble")
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.12
    w = N(nt, "ShaderNodeTexWave", Scale=1.5, Distortion=14.0, Detail=8.0)
    r = N(nt, "ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (0.30, 0.29, 0.28, 1)
    r.color_ramp.elements[1].color = (0.62, 0.60, 0.57, 1)
    r.color_ramp.elements[0].position = 0.4
    nt.links.new(w.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


# ------------------------------------------------------------------ géométrie 2D
def catmull(pts, n=20):
    P = [np.array(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + np.linalg.norm(p1 - p0) ** 0.5
        t2 = t1 + np.linalg.norm(p2 - p1) ** 0.5
        t3 = t2 + np.linalg.norm(p3 - p2) ** 0.5
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(P[-2])
    return np.array(out)


def resample(poly, step):
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.stack([np.interp(t, s, poly[:, 0]), np.interp(t, s, poly[:, 1])], axis=1)


def contour(c, step=0.5):
    left, right = (resample(catmull(side) * [ARCH_SX, ARCH_SZ], step) for side in c)
    return np.concatenate([left, right[1:]])


def seg_dist(P, A, B):
    out = np.empty(len(P))
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    for i in range(0, len(P), 1500):
        p = P[i:i + 1500, None, :]
        t = np.clip(((p - A) * AB).sum(2) / L2, 0, 1)
        out[i:i + 1500] = np.sqrt(((p - (A + t[..., None] * AB)) ** 2).sum(2)).min(1)
    return out


def inside(P, poly):
    x1, y1 = poly[:, 0], poly[:, 1]
    x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
    res = np.empty(len(P), bool)
    for i in range(0, len(P), 1500):
        x, y = P[i:i + 1500, 0:1], P[i:i + 1500, 1:2]
        c = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)
        res[i:i + 1500] = c.sum(1) % 2 == 1
    return res


def region(A, B):
    """Polygone fermé entre deux contours (A puis B inversé) et le type de chaque segment."""
    pts = np.concatenate([A, B[::-1]])
    kinds = np.array(['A'] * (len(A) - 1) + ['-'] + ['B'] * (len(B) - 1) + ['-'])
    return pts, kinds


def rnd(d, r):
    t = np.clip(d / r, 0, 1)
    return 1 - (1 - t) ** 2.5


def half_depth(z):
    """Demi-épaisseur de l'arche : 19 mm en bas -> 10 mm en haut (profil en lame)."""
    return (38 - 18 * np.clip(z / 170, 0, 1)) / 2


def solid_from_region(name, pts, kinds, front_fn, back_fn, mat, grid=0.75, z0=BASE_TOP):
    lo, hi = pts.min(0), pts.max(0)
    gx, gz = np.meshgrid(np.arange(lo[0], hi[0], grid), np.arange(lo[1], hi[1], grid * 0.866))
    gx[1::2] += grid / 2                       # grille hexagonale -> triangles réguliers
    G = np.stack([gx.ravel(), gz.ravel()], 1)
    G = G[inside(G, pts)]
    G = G[seg_dist(G, pts, np.roll(pts, -1, 0)) > grid * 0.55]
    verts = [Vector(p) for p in pts] + [Vector(p) for p in G]
    res = delaunay_2d_cdt(verts, [], [list(range(len(pts)))], 1, 1e-6)
    V = np.array([(v.x, v.y) for v in res[0]])
    F = res[2]
    nxt = np.roll(pts, -1, 0)
    dist = {k: seg_dist(V, pts[kinds == k], nxt[kinds == k]) for k in ('A', 'B')}
    h = half_depth(V[:, 1])
    yf, yb = front_fn(V, dist, h), back_fn(V, dist, h)
    n = len(V)
    co = [(x * MM, y * MM, (z + z0) * MM) for (x, z), y in zip(V, yf)] + \
         [(x * MM, y * MM, (z + z0) * MM) for (x, z), y in zip(V, yb)]
    faces = [tuple(f) for f in F] + [tuple(i + n for i in reversed(f)) for f in F]
    ec = Counter()
    for f in F:
        for i in range(len(f)):
            ec[frozenset((f[i], f[(i + 1) % len(f)]))] += 1
    for f in F:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            if ec[frozenset((a, b))] == 1:
                faces.append((b, a, a + n, b + n))
    me = bpy.data.meshes.new(name)
    me.from_pydata(co, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    smooth(ob, 50)
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ utilitaires 3D
def smooth(ob, angle=35):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    ob.select_set(False)


def add_bevel(ob, w, seg=4, angle=40):
    m = ob.modifiers.new("bevel", 'BEVEL')
    m.width = w * MM
    m.segments = seg
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)


def cyl(name, r, h, loc, mat, rot=(0, 0, 0), verts=128, bevel=0.6, sx=1.0, sy=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * MM, depth=h * MM,
                                        location=Vector(loc) * MM, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    if sx != 1 or sy != 1:
        ob.scale = (sx, sy, 1)
        bpy.ops.object.transform_apply(scale=True)
    if bevel:
        add_bevel(ob, bevel)
    smooth(ob)
    ob.data.materials.append(mat)
    return ob


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def boolean(target, cutter):
    m = target.modifiers.new("bool", 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    m.object = cutter
    m.solver = 'EXACT'
    m.use_self = True
    m.use_hole_tolerant = True
    apply_mods(target)
    bpy.data.objects.remove(cutter, do_unlink=True)


# ================================================================== BASE
cyl("Base", 1, BASE_TOP - BASE_Z0, (0, 0, (BASE_TOP + BASE_Z0) / 2), mat_body,
    bevel=0, sx=BASE_A, sy=BASE_B)
add_bevel(bpy.data.objects["Base"], 4.5, seg=6)
cyl("LED_Line", 1, 3, (0, 0, BASE_Z0 - 1.5), mat_glow_soft, bevel=0, sx=BASE_A - 2.5, sy=BASE_B - 2.5)
cyl("Bottom", 1, 3, (0, 0, 4.5), mat_body, bevel=1, sx=BASE_A - 3, sy=BASE_B - 3)
for fx, fy in ((-55, -28), (55, -28), (-55, 28), (55, 28)):
    cyl("Foot", 5, 3.2, (fx, fy, 1.6), mat_metal, bevel=0.5, verts=48)

# --- vitre noire galbée (suit l'ovale, extrémités inclinées) + écran/icônes en texture
xs = np.linspace(-BASE_A + 0.01, BASE_A - 0.01, 4000)
ys = -BASE_B * np.sqrt(1 - (xs / BASE_A) ** 2)
arc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))])
arc -= np.interp(0, xs, arc)


def on_base(x, z, off):
    y = -BASE_B * math.sqrt(max(1e-9, 1 - (x / BASE_A) ** 2))
    nrm = Vector((x / BASE_A ** 2, y / BASE_B ** 2, 0)).normalized()
    return Vector((x, y, z)) + nrm * off, nrm


nu, nv = 120, 24
co, uvs = [], []
for j in range(nv + 1):
    s = j / nv
    z = PANEL["z0"] + (PANEL["z1"] - PANEL["z0"]) * s
    for i in range(nu + 1):
        x = PANEL["x0"] + (PANEL["x1"] - PANEL["x0"]) * i / nu + PANEL["slant"] * (s - 0.5)
        p, _ = on_base(x, z, 0.5)
        co.append(p * MM)
        uvs.append(((np.interp(x, xs, arc) + 64) / 128, (z - PANEL["z0"]) / (PANEL["z1"] - PANEL["z0"])))
faces = [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i)
         for j in range(nv) for i in range(nu)]
me = bpy.data.meshes.new("FrontPanel")
me.from_pydata(co, [], faces)
uvl = me.uv_layers.new()
for poly in me.polygons:
    for li in poly.loop_indices:
        uvl.data[li].uv = uvs[me.loops[li].vertex_index]
panel = bpy.data.objects.new("Front_Panel", me)
coll.objects.link(panel)
sol = panel.modifiers.new("thick", 'SOLIDIFY')
sol.thickness = 1.2 * MM
sol.offset = -1
add_bevel(panel, 0.4, seg=2)
smooth(panel, 60)
panel.data.materials.append(panel_material())

# --- molette dorée cannelée sur l'avant droit
kp, kn = on_base(KNOB["x"], KNOB["z"], 0)
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=120, radius1=KNOB["r"] * MM,
                      radius2=KNOB["r"] * MM, depth=KNOB["L"] * MM)
for v in bm.verts:
    r = math.hypot(v.co.x, v.co.y)
    if r > 1e-6:
        k = round(math.atan2(v.co.y, v.co.x) / (2 * math.pi / 120))
        if k % 2 == 0:
            v.co.x *= 0.955
            v.co.y *= 0.955
me = bpy.data.meshes.new("Knob")
bm.to_mesh(me)
bm.free()
knob = bpy.data.objects.new("Knob", me)
coll.objects.link(knob)
knob.rotation_euler = kn.to_track_quat('Z', 'Y').to_euler()
knob.location = (kp + kn * (KNOB["L"] / 2 + 1.5)) * MM
add_bevel(knob, 0.9, seg=3, angle=60)
smooth(knob, 25)
knob.data.materials.append(mat_metal)
ring = cyl("Knob_Glow", KNOB["r"] + 1.4, 1.2, tuple(kp + kn * 0.8), mat_glow_soft,
           rot=kn.to_track_quat('Z', 'Y').to_euler(), bevel=0)
cyl("Knob_Gap", KNOB["r"] + 0.6, 1.0, tuple(kp + kn * 1.6), mat_dark,
    rot=kn.to_track_quat('Z', 'Y').to_euler(), bevel=0)

# ================================================================== ARCHE
outer, band_o, band_i, inner = contour(OUTER), contour(BAND_OUT), contour(BAND_IN), contour(INNER)

# 1) coque extérieure : arête fine côté extérieur, marche nette vers la bande dorée
pts, kinds = region(outer, band_o)
shell_f = lambda V, d, h: -np.minimum(1.6 + (h - 1.6) * rnd(d['A'], 17), (h - 4) + 4 * rnd(d['B'], 3))
solid_from_region("Arch_Shell", pts, kinds, shell_f, lambda V, d, h: -shell_f(V, d, h), mat_body)

# 2) liseré intérieur autour de l'ouverture
pts, kinds = region(band_i, inner)
rim_f = lambda V, d, h: -np.minimum((h - 4) + 2 * rnd(d['A'], 2.5), (h - 7) + 5 * rnd(d['B'], 5))
solid_from_region("Arch_InnerRim", pts, kinds, rim_f, lambda V, d, h: -rim_f(V, d, h), mat_body)

# 3) bande dorée ajourée (avant + arrière) et diffuseur LED au cœur
pts, kinds = region(band_o, band_i)
front = solid_from_region("Filigree_Front", pts, kinds, lambda V, d, h: -(h - 5.0),
                          lambda V, d, h: -(h - 6.4), mat_metal)
back = solid_from_region("Filigree_Back", pts, kinds, lambda V, d, h: h - 6.4,
                         lambda V, d, h: h - 5.0, mat_metal)
solid_from_region("LED_Core", pts, kinds, lambda V, d, h: -0.4 + 0 * h,
                  lambda V, d, h: 0.4 + 0 * h, mat_glow)

# étoiles à 8 branches + petits losanges, taille adaptée à la largeur locale de la bande
L = 900
bo = resample(band_o, 1.0)
bi = resample(band_i, 1.0)
bo = np.stack([np.interp(np.linspace(0, 1, L), np.linspace(0, 1, len(bo)), bo[:, k]) for k in (0, 1)], 1)
bi = np.stack([np.interp(np.linspace(0, 1, L), np.linspace(0, 1, len(bi)), bi[:, k]) for k in (0, 1)], 1)
mid, wid = (bo + bi) / 2, np.linalg.norm(bo - bi, axis=1)
bm = bmesh.new()


def prism(poly):
    vf = [bm.verts.new((x * MM, -40 * MM, (z + BASE_TOP) * MM)) for x, z in poly]
    vb = [bm.verts.new((x * MM, 40 * MM, (z + BASE_TOP) * MM)) for x, z in poly]
    bm.faces.new(vf[::-1])
    bm.faces.new(vb)
    for k in range(len(poly)):
        bm.faces.new((vf[k], vf[(k + 1) % len(poly)], vb[(k + 1) % len(poly)], vb[k]))


def star(cx, cz, r, rot):
    return [(cx + (r if k % 2 == 0 else r * 0.6) * math.cos(rot + k * math.pi / 8),
             cz + (r if k % 2 == 0 else r * 0.6) * math.sin(rot + k * math.pi / 8)) for k in range(16)]


acc, prev_c, last_star = 1e9, None, None
for (x, z), w, i in zip(mid, wid, range(L)):
    if prev_c is not None:
        acc += math.dist((x, z), prev_c)
    prev_c = (x, z)
    r = min(0.36 * w, 7.0)
    if z < 4 or r < 1.8 or acc < max(2.35 * r + 1.4, 5):
        continue
    t = bo[i] - bi[i]
    rot = math.atan2(t[1], t[0])
    prism(star(x, z, r, rot))
    if last_star is not None:
        mx, mz = (x + last_star[0]) / 2, (z + last_star[1]) / 2
        rd = 0.11 * w
        if rd > 0.9:
            prism([(mx + rd * math.cos(rot + k * math.pi / 2), mz + rd * math.sin(rot + k * math.pi / 2))
                   for k in range(4)])
    last_star, acc = (x, z), 0.0
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("stars")
bm.to_mesh(me)
bm.free()
cut = bpy.data.objects.new("stars", me)
coll.objects.link(cut)
bpy.ops.object.select_all(action='DESELECT')
front.select_set(True)
back.select_set(True)
bpy.context.view_layer.objects.active = front
bpy.ops.object.join()
front.name = "Arch_Filigree"
boolean(front, cut)

# ================================================================== SOCLE + SPHÈRE
tip_x = 4.0
cyl("Pedestal_Ring", 38, 3.5, (tip_x, 0, BASE_TOP + 1.75), mat_metal, bevel=1.0)
cyl("Pedestal_Inlay", 33, 0.5, (tip_x, 0, BASE_TOP + 3.6), inlay_material(), bevel=0)

sz = BASE_TOP + 50 + SPHERE_R
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=SPHERE_R * MM,
                                     location=(tip_x * MM, 0, sz * MM))
sphere = bpy.context.active_object
sphere.name = "Sphere"
smooth(sphere, 180)
sphere.visible_shadow = False
sphere.data.materials.append(sphere_material())
top_s = sz + SPHERE_R
cyl("Sphere_Collar", 10, 4.5, (tip_x, 0, top_s - 1.0), mat_metal, bevel=1.2)
bpy.ops.mesh.primitive_torus_add(major_radius=10.2 * MM, minor_radius=1.0 * MM,
                                 location=(tip_x * MM, 0, (top_s - 3.2) * MM))
t = bpy.context.active_object
smooth(t, 180)
t.data.materials.append(mat_metal)
cyl("Sphere_Finial", 4, 3, (tip_x, 0, sz - SPHERE_R + 0.5), mat_metal, bevel=0.8)
z_hit = max(z for x, z in inner if abs(x - tip_x) < 0.8) + BASE_TOP
cyl("Brass_Rod", 0.9, z_hit - top_s + 4, (tip_x, 0, (z_hit + 4 + top_s) / 2), mat_metal, verts=24, bevel=0)

bpy.ops.object.light_add(type='POINT', location=(tip_x * MM, 0, sz * MM))
L_in = bpy.context.active_object
L_in.data.energy = 1.6
L_in.data.color = WARM
L_in.data.shadow_soft_size = 0.01

# ================================================================== DÉCOR + RENDU
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(marble_material())
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 1.0, 1), rotation=(math.radians(90), 0, 0))
bpy.context.active_object.data.materials.append(principled("Wall", (0.04, 0.028, 0.02), rough=0.9))

world = bpy.data.worlds.new("World")
scene.world = world
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.0075, 0.006, 1)


def look(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def area(loc, target, energy, size, color=(1, 0.85, 0.7)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.active_object
    l.data.energy, l.data.size, l.data.color = energy, size, color
    look(l, target)


area((-0.42, -0.42, 0.50), (0, 0, 0.11), 8, 0.4)
area((0.38, 0.42, 0.42), (0, 0, 0.13), 16, 0.25)
area((0.45, -0.35, 0.12), (0, 0, 0.08), 1.6, 0.4, color=(0.85, 0.88, 1.0))
area((0, -0.3, 0.6), (0, 0, 0.1), 2.5, 0.5)


def camera(name, loc, target, lens, fstop=6.3):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    cd.dof.aperture_fstop = fstop
    c = bpy.data.objects.new(name, cd)
    coll.objects.link(c)
    c.location = loc
    look(c, target)
    return c


cams = [
    (camera("Cam_Hero", (-0.13, -0.52, 0.17), (0.0, 0.0, 0.118), 55), "hero", 1600, 1600),
    (camera("Cam_Screen", (0.035, -0.20, 0.06), (0.0, -0.05, 0.029), 55, 4), "screen", 1600, 1000),
    (camera("Cam_ThreeQuarter", (0.33, -0.40, 0.20), (0.0, 0.0, 0.115), 55), "trois-quarts", 1600, 1600),
]
if VARIANT != "ivory":
    cams = cams[:1]

scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use = True
    scene.cycles.device = 'GPU'
except Exception:
    scene.cycles.device = 'CPU'
scene.cycles.samples = 96 if QUALITY == "preview" else 384
scene.cycles.use_denoising = True
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    pass

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"ayah_{VARIANT}.blend"))
for cam, label, w, h in cams:
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.filepath = os.path.join(HERE, "renders", f"ayah_{VARIANT}_{label}.png")
    bpy.ops.render.render(write_still=True)
print("AYAH DONE")
