"""
AYAH by INOMA — v3 : reconstruction propre du design « niche en goutte » (d'après result.glb).
Usage :  blender -b -P ayah_v3.py -- [ivory|black|grey] [preview|final]
Proportions mesurées sur le modèle IA, géométrie entièrement reconstruite (surfaces lisses,
arêtes nettes, treillis d'étoiles régulier). Cotes en mm.
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

# ------------------------------------------------------------------ dimensions
H = 215                    # hauteur totale
WF, DF = 0.92, 0.85        # affinage largeur / profondeur par rapport au modèle IA
BASE_TOP = 0.20 * H        # 43 mm
BASE_A, BASE_B = 83, 71    # demi-axes de la base ovale
WALL = 4.0                 # épaisseur de la coque (imprimable)
FRAME_D = 7.0              # saillie du cadre avant
SPHERE_R = 28

COLORS = {
    "ivory": dict(body=(0.80, 0.73, 0.61), metal=(1.0, 0.72, 0.38), mrough=0.25),
    "black": dict(body=(0.016, 0.015, 0.014), metal=(1.0, 0.72, 0.38), mrough=0.25),
    "grey":  dict(body=(0.25, 0.25, 0.26), metal=(0.92, 0.93, 0.95), mrough=0.2),
}[VARIANT]


def X(v): return v * H * WF
def Y(v): return v * H * DF
def Zh(v): return v * H


Y_FRONT = Y(-0.13)         # plan de la face avant de la niche

# silhouette mesurée (z normalisé -> x gauche / x droit / y arrière)
ZS = [.20, .25, .30, .35, .40, .45, .50, .55, .60, .65, .70, .75, .80, .85, .90, .95, .975, 1.0]
XL = [-.370, -.389, -.401, -.406, -.407, -.403, -.393, -.377, -.354, -.324, -.287, -.236, -.167, -.080, -.022, .017, .024, .028]
XR = [.382, .393, .409, .416, .420, .418, .413, .403, .389, .368, .342, .311, .272, .230, .175, .108, .071, .028]
YB = [.300, .307, .312, .316, .315, .313, .305, .293, .279, .260, .234, .203, .164, .121, .076, .023, -.05, -.125]

# courbes de la façade (normalisées) : aile ajourée + ouverture
C1 = [(-.36, .205), (-.37, .30), (-.355, .40), (-.32, .50), (-.265, .58), (-.19, .66), (-.10, .74), (-.02, .81), (.06, .865)]
C2 = [(-.285, .205), (-.29, .30), (-.265, .40), (-.21, .50), (-.135, .58), (-.05, .66), (.02, .74), (.06, .865)]
C3 = [(-.24, .17), (-.245, .30), (-.22, .40), (-.16, .50), (-.08, .58), (.02, .66), (.09, .745), (.15, .81)]
R1 = [(.15, .81), (.215, .77), (.27, .71), (.31, .64), (.345, .55), (.36, .45), (.362, .35), (.35, .25), (.33, .17)]

# ------------------------------------------------------------------ scène
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.length_unit = 'MILLIMETERS'
coll = bpy.context.collection
PRINT_PARTS = []           # objets exportés en STL


# ------------------------------------------------------------------ matériaux
def principled(name, color, metallic=0.0, rough=0.5, coat=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


WARM = (1.0, 0.60, 0.27)
mat_body = principled("Body", COLORS["body"], rough=0.42, coat=0.12)
mat_inner = principled("NicheInside", tuple(c * 0.7 for c in COLORS["body"]), rough=0.6)
mat_metal = principled("Metal", COLORS["metal"], metallic=1.0, rough=COLORS["mrough"])
mat_glow = principled("LEDPanel", (0, 0, 0), emit=(1.0, 0.66, 0.33), strength=7)
mat_glow_soft = principled("LEDLine", (0, 0, 0), emit=WARM, strength=4)
mat_dark = principled("Dark", (0.015, 0.013, 0.012), rough=0.5)


def N(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k == "op":
            n.operation = v
        else:
            n.inputs[k].default_value = v
    return n


def star_distance(nt, vec):
    sep = N(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(vec, sep.inputs[0])
    ab = []
    for i in (0, 1):
        f = N(nt, "ShaderNodeMath", op='FRACT'); nt.links.new(sep.outputs[i], f.inputs[0])
        c = N(nt, "ShaderNodeMath", op='SUBTRACT'); nt.links.new(f.outputs[0], c.inputs[0]); c.inputs[1].default_value = 0.5
        a = N(nt, "ShaderNodeMath", op='ABSOLUTE'); nt.links.new(c.outputs[0], a.inputs[0])
        ab.append(a.outputs[0])
    d1 = N(nt, "ShaderNodeMath", op='MAXIMUM'); nt.links.new(ab[0], d1.inputs[0]); nt.links.new(ab[1], d1.inputs[1])
    s = N(nt, "ShaderNodeMath", op='ADD'); nt.links.new(ab[0], s.inputs[0]); nt.links.new(ab[1], s.inputs[1])
    d2 = N(nt, "ShaderNodeMath", op='MULTIPLY'); nt.links.new(s.outputs[0], d2.inputs[0]); d2.inputs[1].default_value = 0.7071
    d = N(nt, "ShaderNodeMath", op='MINIMUM'); nt.links.new(d1.outputs[0], d.inputs[0]); nt.links.new(d2.outputs[0], d.inputs[1])
    return d.outputs[0]


def mask(nt, value, lo, hi):
    mr = N(nt, "ShaderNodeMapRange")
    nt.links.new(value, mr.inputs["Value"])
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = lo, hi
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 1, 0
    return mr.outputs[0]


def sphere_material():
    m = bpy.data.materials.new("Sphere")
    nt = m.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial")
    uv = N(nt, "ShaderNodeTexCoord")
    mp = N(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (18, 9, 1)
    nt.links.new(uv.outputs["UV"], mp.inputs[0])
    holes = mask(nt, star_distance(nt, mp.outputs[0]), 0.28, 0.30)
    shell = N(nt, "ShaderNodeBsdfPrincipled")
    shell.inputs["Base Color"].default_value = (*COLORS["metal"], 1) if VARIANT != "grey" else (0.9, 0.9, 0.92, 1)
    shell.inputs["Metallic"].default_value = 0.85
    shell.inputs["Roughness"].default_value = 0.3
    hole = N(nt, "ShaderNodeEmission")
    hole.inputs["Color"].default_value = (1.0, 0.76, 0.45, 1)
    hole.inputs["Strength"].default_value = 16
    mix = N(nt, "ShaderNodeMixShader")
    nt.links.new(holes, mix.inputs["Fac"]); nt.links.new(shell.outputs[0], mix.inputs[1]); nt.links.new(hole.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def inlay_material():
    m = bpy.data.materials.new("Inlay")
    nt = m.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial")
    tc = N(nt, "ShaderNodeTexCoord")
    mp = N(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (110, 110, 110)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    d = star_distance(nt, mp.outputs[0])
    off = N(nt, "ShaderNodeMath", op='SUBTRACT'); nt.links.new(d, off.inputs[0]); off.inputs[1].default_value = 0.3
    ab = N(nt, "ShaderNodeMath", op='ABSOLUTE'); nt.links.new(off.outputs[0], ab.inputs[0])
    lines = mask(nt, ab.outputs[0], 0.02, 0.04)
    dark = N(nt, "ShaderNodeBsdfPrincipled"); dark.inputs["Base Color"].default_value = (0.012, 0.011, 0.01, 1); dark.inputs["Roughness"].default_value = 0.35
    gold = N(nt, "ShaderNodeBsdfPrincipled"); gold.inputs["Base Color"].default_value = (*COLORS["metal"], 1)
    gold.inputs["Metallic"].default_value = 1; gold.inputs["Roughness"].default_value = 0.3
    mix = N(nt, "ShaderNodeMixShader")
    nt.links.new(lines, mix.inputs["Fac"]); nt.links.new(dark.outputs[0], mix.inputs[1]); nt.links.new(gold.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def panel_material():
    m = bpy.data.materials.new("FrontPanel")
    nt = m.node_tree; nt.nodes.clear()
    out = N(nt, "ShaderNodeOutputMaterial")
    uv = N(nt, "ShaderNodeTexCoord")
    tex = N(nt, "ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(HERE, "panel_ui.png"))
    tex.extension = 'CLIP'
    nt.links.new(uv.outputs["UV"], tex.inputs[0])
    g = N(nt, "ShaderNodeBsdfPrincipled")
    g.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1)
    g.inputs["Roughness"].default_value = 0.1
    g.inputs["Coat Weight"].default_value = 0.6
    g.inputs["Coat Roughness"].default_value = 0.02
    g.inputs["Emission Strength"].default_value = 1.5
    nt.links.new(tex.outputs["Color"], g.inputs["Emission Color"])
    nt.links.new(g.outputs[0], out.inputs["Surface"])
    return m


def marble_material():
    m = bpy.data.materials.new("Marble")
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.12
    w = N(nt, "ShaderNodeTexWave", Scale=1.5, Distortion=14.0, Detail=8.0)
    r = N(nt, "ShaderNodeValToRGB")
    r.color_ramp.elements[0].color = (0.18, 0.17, 0.16, 1)
    r.color_ramp.elements[1].color = (0.36, 0.34, 0.32, 1)
    r.color_ramp.elements[0].position = 0.4
    nt.links.new(w.outputs["Fac"], r.inputs["Fac"]); nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    return m


# ------------------------------------------------------------------ géométrie 2D
def catmull(pts, n=24):
    P = [np.array(p, float) for p in pts]
    P = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t1 = np.linalg.norm(p1 - p0) ** .5; t2 = t1 + np.linalg.norm(p2 - p1) ** .5; t3 = t2 + np.linalg.norm(p3 - p2) ** .5
        for k in range(n):
            t = t1 + (t2 - t1) * k / n
            a1 = (t1 - t) / t1 * p0 + t / t1 * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / t2 * a1 + t / t2 * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(P[-2])
    return np.array(out)


def resample(poly, step=0.6):
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(poly, axis=0), axis=1))])
    t = np.linspace(0, s[-1], max(2, int(s[-1] / step) + 1))
    return np.stack([np.interp(t, s, poly[:, 0]), np.interp(t, s, poly[:, 1])], 1)


def curve_mm(pts):
    """Courbe normalisée (x, z) -> polyligne lisse en mm, z relatif au sol."""
    c = catmull(pts)
    return resample(np.stack([X(c[:, 0]), Zh(c[:, 1])], 1))


def seg_dist(P, A, B):
    out = np.empty(len(P)); AB = B - A; L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    for i in range(0, len(P), 1500):
        p = P[i:i + 1500, None, :]
        t = np.clip(((p - A) * AB).sum(2) / L2, 0, 1)
        out[i:i + 1500] = np.sqrt(((p - (A + t[..., None] * AB)) ** 2).sum(2)).min(1)
    return out


def inside(P, poly):
    x1, y1 = poly[:, 0], poly[:, 1]; x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
    res = np.empty(len(P), bool)
    for i in range(0, len(P), 1500):
        x, y = P[i:i + 1500, 0:1], P[i:i + 1500, 1:2]
        res[i:i + 1500] = (((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1)).sum(1) % 2 == 1
    return res


def rnd(d, r):
    t = np.clip(d / r, 0, 1)
    return 1 - (1 - t) ** 2.5


def finish(ob, mat, angle=50, part=True):
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data); bm.free()
    smooth(ob, angle)
    ob.data.materials.append(mat)
    if part:
        PRINT_PARTS.append(ob)
    return ob


def slab(name, poly, round_mask, front_fn, back_fn, mat, grid=0.8):
    """Région 2D (x, z) épaissie en Y : front_fn/back_fn(dist_au_bord_arrondi) -> y (mm)."""
    lo, hi = poly.min(0), poly.max(0)
    gx, gz = np.meshgrid(np.arange(lo[0], hi[0], grid), np.arange(lo[1], hi[1], grid * 0.866))
    gx[1::2] += grid / 2
    G = np.stack([gx.ravel(), gz.ravel()], 1)
    G = G[inside(G, poly)]
    nxt = np.roll(poly, -1, 0)
    G = G[seg_dist(G, poly, nxt) > grid * 0.55]
    res = delaunay_2d_cdt([Vector(p) for p in poly] + [Vector(p) for p in G], [], [list(range(len(poly)))], 1, 1e-6)
    V = np.array([(v.x, v.y) for v in res[0]]); F = res[2]
    d = seg_dist(V, poly[round_mask], nxt[round_mask]) if round_mask.any() else np.full(len(V), 1e3)
    yf, yb = front_fn(d), back_fn(d)
    n = len(V)
    co = [(x * MM, y * MM, z * MM) for (x, z), y in zip(V, yf)] + [(x * MM, y * MM, z * MM) for (x, z), y in zip(V, yb)]
    faces = [tuple(f) for f in F] + [tuple(i + n for i in reversed(f)) for f in F]
    ec = Counter(frozenset((f[i], f[(i + 1) % 3])) for f in F for i in range(3))
    faces += [(f[(i + 1) % 3], f[i], f[i] + n, f[(i + 1) % 3] + n) for f in F for i in range(3)
              if ec[frozenset((f[i], f[(i + 1) % 3]))] == 1]
    me = bpy.data.meshes.new(name); me.from_pydata(co, [], faces)
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    return finish(ob, mat)


def smooth(ob, angle=35):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    ob.select_set(False)


def add_bevel(ob, w, seg=4, angle=40):
    m = ob.modifiers.new("bevel", 'BEVEL')
    m.width = w * MM; m.segments = seg; m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angle)


def cyl(name, r, h, loc, mat, rot=(0, 0, 0), verts=128, bevel=0.6, sx=1.0, sy=1.0, part=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * MM, depth=h * MM,
                                        location=Vector(loc) * MM, rotation=rot)
    ob = bpy.context.active_object; ob.name = name
    if sx != 1 or sy != 1:
        ob.scale = (sx, sy, 1); bpy.ops.object.transform_apply(scale=True)
    if bevel:
        add_bevel(ob, bevel)
    smooth(ob)
    ob.data.materials.append(mat)
    if part:
        PRINT_PARTS.append(ob)
    return ob


def boolean(target, cutter):
    m = target.modifiers.new("bool", 'BOOLEAN')
    m.operation = 'DIFFERENCE'; m.object = cutter; m.solver = 'EXACT'
    m.use_self = True; m.use_hole_tolerant = True
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter, do_unlink=True)


def prism_mesh(polys, y0, y1, name="cut"):
    bm = bmesh.new()
    for poly in polys:
        vf = [bm.verts.new((x * MM, y0 * MM, z * MM)) for x, z in poly]
        vb = [bm.verts.new((x * MM, y1 * MM, z * MM)) for x, z in poly]
        bm.faces.new(vf[::-1]); bm.faces.new(vb)
        for k in range(len(poly)):
            bm.faces.new((vf[k], vf[(k + 1) % len(poly)], vb[(k + 1) % len(poly)], vb[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    return ob


# ================================================================== NICHE (coque en goutte)
zc = catmull(list(zip(ZS, ZS)))[:, 0]
xl_f = lambda z: np.interp(z, ZS, XL)
xr_f = lambda z: np.interp(z, ZS, XR)
yb_f = lambda z: np.interp(z, ZS, YB)
# lissage des profils mesurés
zz = np.linspace(.20, 1.0, 400)
xl_s, xr_s, yb_s = (catmull(list(zip(ZS, arr)))[:, 1] for arr in (XL, XR, YB))
zs_s = catmull(list(zip(ZS, XL)))[:, 0]


def section(zn):
    xl, xr, yb = (np.interp(zn, zs_s, a) for a in (xl_s, xr_s, yb_s))
    return X((xl + xr) / 2), X((xr - xl) / 2), Y(yb) - Y_FRONT      # centre x, demi-largeur, profondeur


NZ, NT = 220, 96
def shell_points(offset):
    pts = []
    for i in range(NZ + 1):
        zn = .20 + .80 * i / NZ
        xc, w, d = section(zn)
        w, d = max(w - offset, 0.3), max(d - offset, 0.3)
        row = [(xc + w * math.cos(math.pi * j / NT), Y_FRONT + 1.0 + d * math.sin(math.pi * j / NT), Zh(zn))
               for j in range(NT + 1)]
        pts.append(row)
    return pts


outer, inner = shell_points(0), shell_points(WALL)
bm = bmesh.new()
vo = [[bm.verts.new(Vector(p) * MM) for p in row] for row in outer]
vi = [[bm.verts.new(Vector(p) * MM) for p in row] for row in inner]
for i in range(NZ):
    for j in range(NT):
        bm.faces.new((vo[i][j], vo[i][j + 1], vo[i + 1][j + 1], vo[i + 1][j]))
        bm.faces.new((vi[i][j], vi[i + 1][j], vi[i + 1][j + 1], vi[i][j + 1]))
    for j, (a, b) in ((0, (0, 0)), (NT, (NT, NT))):
        bm.faces.new((vo[i][j], vo[i + 1][j], vi[i + 1][j], vi[i][j]))
for j in range(NT):
    bm.faces.new((vo[0][j], vi[0][j], vi[0][j + 1], vo[0][j + 1]))
    bm.faces.new((vo[NZ][j], vo[NZ][j + 1], vi[NZ][j + 1], vi[NZ][j]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new("Niche_Shell"); bm.to_mesh(me); bm.free()
shell = bpy.data.objects.new("Niche_Shell", me); coll.objects.link(shell)
shell.data.materials.append(mat_body); shell.data.materials.append(mat_inner)
smooth(shell, 40)
for p in shell.data.polygons:                     # faces intérieures -> matériau intérieur
    c = sum((shell.data.vertices[v].co for v in p.vertices), Vector()) / len(p.vertices)
    zn = c.z / MM / H
    xc, w, d = section(min(max(zn, .2), 1))
    if ((c.x / MM - xc) / max(w, 1e-3)) ** 2 + ((c.y / MM - Y_FRONT - 1) / max(d, 1e-3)) ** 2 < 0.97:
        p.material_index = 1
PRINT_PARTS.append(shell)

# ================================================================== CADRE AVANT (aile + liseré)
left = np.stack([X(xl_s), Zh(zs_s)], 1)
right = np.stack([X(xr_s), Zh(zs_s)], 1)
outline = resample(np.concatenate([left, right[::-1]]))
outline = outline[outline[:, 1] >= BASE_TOP - 0.01]
rmask = outline[:, 1] > BASE_TOP + 0.5
rmask &= np.roll(outline[:, 1], -1) > BASE_TOP + 0.5
frame = slab("Front_Frame", outline, rmask,
             lambda d: Y_FRONT - (1.2 + (FRAME_D - 1.2) * rnd(d, 6.5)),
             lambda d: Y_FRONT + 2.0 + 0 * d, mat_body)

c3, r1 = curve_mm(C3), curve_mm(R1)
opening = np.concatenate([c3, r1[1:]])
c1, c2 = curve_mm(C1), curve_mm(C2)
window = np.concatenate([c1, c2[::-1][1:]])
boolean(frame, prism_mesh([opening, window], Y_FRONT - 30, Y_FRONT + 6))
add_bevel(frame, 0.9, seg=3, angle=55)

# ================================================================== PANNEAU AJOURÉ (jali) + LED
win = window[window[:, 1] > BASE_TOP + 0.5]
win_mask = np.ones(len(win), bool)
slab("Filigree_LED", win, ~win_mask, lambda d: Y_FRONT - 0.2 + 0 * d, lambda d: Y_FRONT + 0.6 + 0 * d, mat_glow)
PRINT_PARTS.pop()
jali = slab("Filigree_Panel", win, ~win_mask, lambda d: Y_FRONT - 4.2 + 0 * d, lambda d: Y_FRONT - 2.4 + 0 * d, mat_metal)

S, RS, RD = 6.4, 2.55, 1.15        # pas du treillis, rayon étoile, rayon losange
wn = np.roll(win, -1, 0)


def fits(poly, margin=1.1):
    P = np.array(poly)
    return inside(P, win).all() and seg_dist(P, win, wn).min() > margin


shapes = []
x0, z0 = win[:, 0].min(), win[:, 1].min()
for gx in np.arange(x0 - S, win[:, 0].max() + S, S):
    for gz in np.arange(z0 - S, win[:, 1].max() + S, S):
        st = [(gx + (RS if k % 2 == 0 else RS * 0.62) * math.cos(k * math.pi / 8),
               gz + (RS if k % 2 == 0 else RS * 0.62) * math.sin(k * math.pi / 8)) for k in range(16)]
        if fits(st):
            shapes.append(st)
        cx, cz = gx + S / 2, gz + S / 2
        dm = [(cx + RD * math.cos(k * math.pi / 2), cz + RD * math.sin(k * math.pi / 2)) for k in range(4)]
        if fits(dm):
            shapes.append(dm)
boolean(jali, prism_mesh(shapes, Y_FRONT - 10, Y_FRONT + 0))

# ================================================================== BASE
body = cyl("Base", 1, BASE_TOP - 7, (0, 0, (BASE_TOP + 7) / 2), mat_body, bevel=0, sx=BASE_A, sy=BASE_B)
for v in body.data.vertices:                      # léger fruit : plus étroite en haut
    if v.co.z > 0:
        v.co.x *= 0.965; v.co.y *= 0.965
add_bevel(body, 4.5, seg=6)
cyl("LED_Line", 1, 3, (0, 0, 5.5), mat_glow_soft, bevel=0, sx=BASE_A - 2.5, sy=BASE_B - 2.5, part=False)
cyl("Bottom", 1, 3, (0, 0, 3.5), mat_body, bevel=1, sx=BASE_A - 3, sy=BASE_B - 3)
for fx, fy in ((-52, -38), (52, -38), (-52, 38), (52, 38)):
    cyl("Foot", 5, 2.2, (fx, fy, 1.1), mat_metal, bevel=0.5, verts=48)

# --- vitre noire galbée (écran + icônes en texture)
PANEL = dict(x0=-60, x1=24, z0=13, z1=38, slant=6)


def base_radius_scale(z):
    t = (z - 7) / (BASE_TOP - 7)
    return 1 - 0.035 * t


def on_base(x, z, off):
    k = base_radius_scale(z)
    a, b = BASE_A * k, BASE_B * k
    y = -b * math.sqrt(max(1e-9, 1 - (x / a) ** 2))
    nrm = Vector((x / a ** 2, y / b ** 2, 0)).normalized()
    return Vector((x, y, z)) + nrm * off, nrm


xs_ = np.linspace(-BASE_A + 0.01, BASE_A - 0.01, 4000)
ys_ = -BASE_B * np.sqrt(1 - (xs_ / BASE_A) ** 2)
arc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(xs_), np.diff(ys_)))])
arc -= np.interp((PANEL["x0"] + PANEL["x1"]) / 2, xs_, arc)
nu, nv = 120, 24
co, uvs = [], []
for j in range(nv + 1):
    s = j / nv
    z = PANEL["z0"] + (PANEL["z1"] - PANEL["z0"]) * s
    for i in range(nu + 1):
        x = PANEL["x0"] + (PANEL["x1"] - PANEL["x0"]) * i / nu + PANEL["slant"] * (s - 0.5)
        p, _ = on_base(x, z, 0.5)
        co.append(p * MM)
        uvs.append(((np.interp(x, xs_, arc) - 4 + 64) / 128, (z - PANEL["z0"]) / (PANEL["z1"] - PANEL["z0"])))
faces = [(j * (nu + 1) + i, j * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i + 1, (j + 1) * (nu + 1) + i)
         for j in range(nv) for i in range(nu)]
me = bpy.data.meshes.new("FrontPanel"); me.from_pydata(co, [], faces)
uvl = me.uv_layers.new()
for poly in me.polygons:
    for li in poly.loop_indices:
        uvl.data[li].uv = uvs[me.loops[li].vertex_index]
panel = bpy.data.objects.new("Front_Panel", me); coll.objects.link(panel)
sol = panel.modifiers.new("thick", 'SOLIDIFY'); sol.thickness = 1.2 * MM; sol.offset = -1
add_bevel(panel, 0.4, seg=2)
smooth(panel, 60)
panel.data.materials.append(panel_material())

# --- molette dorée cannelée
kp, kn = on_base(46, 25.5, 0)
bm = bmesh.new()
bmesh.ops.create_cone(bm, cap_ends=True, segments=120, radius1=12 * MM, radius2=12 * MM, depth=14 * MM)
for v in bm.verts:
    if math.hypot(v.co.x, v.co.y) > 1e-6 and round(math.atan2(v.co.y, v.co.x) / (2 * math.pi / 120)) % 2 == 0:
        v.co.x *= 0.955; v.co.y *= 0.955
me = bpy.data.meshes.new("Knob"); bm.to_mesh(me); bm.free()
knob = bpy.data.objects.new("Knob", me); coll.objects.link(knob)
rot = kn.to_track_quat('Z', 'Y').to_euler()
knob.rotation_euler = rot
knob.location = (kp + kn * 8.5) * MM
add_bevel(knob, 0.9, seg=3, angle=60)
smooth(knob, 25)
knob.data.materials.append(mat_metal)
PRINT_PARTS.append(knob)
cyl("Knob_Glow", 13.4, 1.2, tuple(kp + kn * 0.8), mat_glow_soft, rot=rot, bevel=0, part=False)

# ================================================================== SPHÈRE + SOCLE
open_mid = lambda zabs: (np.interp(zabs, c3[:, 1], c3[:, 0]) + np.interp(zabs, r1[::-1][:, 1], r1[::-1][:, 0])) / 2
sz = BASE_TOP + 16 + SPHERE_R + 12
sx = float(open_mid(sz))
sy = Y_FRONT + SPHERE_R * 0.95
cyl("Pedestal_Ring", 36, 3.5, (sx, sy - 6, BASE_TOP + 1.75), mat_metal, bevel=1.0)
cyl("Pedestal_Inlay", 31, 0.5, (sx, sy - 6, BASE_TOP + 3.6), inlay_material(), bevel=0, part=False)

bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=SPHERE_R * MM, location=(sx * MM, sy * MM, sz * MM))
sphere = bpy.context.active_object; sphere.name = "Sphere"
smooth(sphere, 180)
sphere.visible_shadow = False
sphere.data.materials.append(sphere_material())
PRINT_PARTS.append(sphere)
cyl("Sphere_Cap", 11, 5, (sx, sy, sz + SPHERE_R - 1.5), mat_metal, bevel=1.2)
cyl("Sphere_Ring_Bottom", 13, 2.4, (sx, sy, sz - SPHERE_R + 4.5), mat_metal, bevel=0.8)
cyl("Sphere_Finial", 4, 3.5, (sx, sy, sz - SPHERE_R - 0.5), mat_metal, bevel=0.8)

# tige : du chapeau jusqu'au plafond intérieur de la niche
z_ceiling = sz
for zn in np.linspace(sz / H, 1.0, 600):
    xc, w, d = section(zn)
    w, d = w - WALL, d - WALL
    if w <= 0 or d <= 0 or ((sx - xc) / w) ** 2 + ((sy - Y_FRONT - 1) / d) ** 2 > 1:
        break
    z_ceiling = Zh(zn)
top_s = sz + SPHERE_R + 1
cyl("Brass_Rod", 1.0, z_ceiling - top_s + 3, (sx, sy, (z_ceiling + 3 + top_s) / 2), mat_metal, verts=24, bevel=0)

bpy.ops.object.light_add(type='POINT', location=(sx * MM, sy * MM, sz * MM))
li = bpy.context.active_object
li.data.energy, li.data.color, li.data.shadow_soft_size = 0.8, WARM, 0.012

# ================================================================== DÉCOR + RENDU
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
bpy.context.active_object.data.materials.append(marble_material())
bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 1.2, 1), rotation=(math.radians(90), 0, 0))
bpy.context.active_object.data.materials.append(principled("Wall", (0.035, 0.025, 0.018), rough=0.9))
scene.world = bpy.data.worlds.new("World")
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.0075, 0.006, 1)


def look(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def area(loc, target, energy, size, color=(1, 0.85, 0.7)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.active_object
    l.data.energy, l.data.size, l.data.color = energy, size, color
    look(l, target)


area((-0.45, -0.45, 0.55), (0, 0, 0.11), 7, 0.45)
area((0.40, 0.45, 0.45), (0, 0, 0.13), 18, 0.3)
area((0.50, -0.35, 0.15), (0, 0, 0.08), 2.0, 0.4, color=(0.85, 0.88, 1.0))
area((0, -0.35, 0.65), (0, 0, 0.1), 1.2, 0.5)


def camera(name, loc, target, lens, fstop=7.1):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.dof.use_dof = True
    cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    cd.dof.aperture_fstop = fstop
    c = bpy.data.objects.new(name, cd); coll.objects.link(c)
    c.location = loc
    look(c, target)
    return c


cams = [
    (camera("Cam_Hero", (-0.21, -0.56, 0.21), (0.0, 0.0, 0.105), 55), "hero", 1500, 1500),
    (camera("Cam_Front", (0.0, -0.66, 0.12), (0.0, 0.0, 0.107), 55), "face", 1300, 1500),
    (camera("Cam_Back", (0.42, 0.42, 0.22), (0.0, 0.0, 0.10), 55), "arriere", 1500, 1500),
    (camera("Cam_Screen", (0.0, -0.24, 0.05), (-0.018, -0.07, 0.025), 55, 4), "ecran", 1600, 1000),
]
if VARIANT != "ivory":
    cams = cams[:1]

scene.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
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

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"ayah_v3_{VARIANT}.blend"))

if VARIANT == "ivory":                            # STL d'aperçu (maquette décorative, en mm)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in PRINT_PARTS + [panel]:
        ob.select_set(True)
    bpy.ops.wm.stl_export(filepath=os.path.join(HERE, "ayah_v3_maquette.stl"),
                          export_selected_objects=True, apply_modifiers=True, global_scale=1000.0)

for cam, label, w, h in cams:
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.filepath = os.path.join(HERE, "renders", f"v3_{VARIANT}_{label}.png")
    bpy.ops.render.render(write_still=True)
print("AYAH DONE")
