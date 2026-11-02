"""
AYAH by INOMA — modèle conceptuel paramétrique (Blender 5.x)
Usage :  blender -b -P ayah_model.py -- [variant] [quality]
         variant : ivory | black | grey     quality : preview | final
Toutes les cotes sont en mm (converties en m).
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VARIANT = argv[0] if len(argv) > 0 else "ivory"
QUALITY = argv[1] if len(argv) > 1 else "preview"

MM = 0.001

# ---------------------------------------------------------------- paramètres
P = dict(
    base_w=170, base_d=105, base_h=40, base_z0=5, base_corner=35, base_edge=3,
    arch_w=72, arch_h=185, arch_inner_w=54, arch_inner_h=152, arch_depth=34,
    arch_tilt=12,                      # décalage de la pointe vers la droite (flamme)
    band_out=(69, 179), band_in=(57, 160), band_recess=4,
    sphere_r=26, sphere_z=90,           # au-dessus du dessus de la base
    screen_w=43, screen_h=23,           # écran IPS 1.9" 170x320 (zone active ~42.7x22.7)
    panel_w=88, panel_h=29, panel_x=-6,
    knob_r=11, knob_len=13, knob_angle=32,
)

COLORS = {
    "ivory": dict(body=(0.83, 0.77, 0.66), metal=(1.0, 0.74, 0.40), metal_rough=0.27),
    "black": dict(body=(0.018, 0.017, 0.016), metal=(1.0, 0.74, 0.40), metal_rough=0.27),
    "grey":  dict(body=(0.36, 0.36, 0.37), metal=(0.90, 0.91, 0.93), metal_rough=0.22),
}[VARIANT]

# ---------------------------------------------------------------- scène vide
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'


# ---------------------------------------------------------------- matériaux
def principled(name, color, metallic=0.0, rough=0.5, coat=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    return m


WARM = (1.0, 0.58, 0.25)
mat_body = principled("Body", COLORS["body"], rough=0.55)
mat_metal = principled("Metal", COLORS["metal"], metallic=1.0, rough=COLORS["metal_rough"])
mat_glass = principled("BlackGlass", (0.004, 0.004, 0.004), rough=0.04, coat=1.0)
mat_glow = principled("LEDGlow", (0, 0, 0), emit=WARM, emit_strength=6)
mat_glow_soft = principled("LEDGlowSoft", (0, 0, 0), emit=WARM, emit_strength=3)
mat_dark = principled("Dark", (0.02, 0.018, 0.016), rough=0.6)


def screen_material():
    m = bpy.data.materials.new("Screen")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(HERE, "screen_ui.png"))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.4
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = 0.03
    gl.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1)
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], add.inputs[0])
    nt.links.new(gl.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    return m


def sphere_material():
    """Sphère translucide : motif cellulaire lumineux (effet ajouré/lithophane)."""
    m = bpy.data.materials.new("Sphere")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = 'DISTANCE_TO_EDGE'
    vor.inputs["Scale"].default_value = 160.0
    nt.links.new(coord.outputs["Object"], vor.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.05
    ramp.color_ramp.elements[1].position = 0.09
    nt.links.new(vor.outputs["Distance"], ramp.inputs["Fac"])
    shell = nt.nodes.new("ShaderNodeBsdfPrincipled")
    shell.inputs["Base Color"].default_value = (0.92, 0.86, 0.74, 1)
    shell.inputs["Roughness"].default_value = 0.5
    shell.inputs["Emission Color"].default_value = (*WARM, 1)
    shell.inputs["Emission Strength"].default_value = 0.6
    hole = nt.nodes.new("ShaderNodeEmission")
    hole.inputs["Color"].default_value = (1.0, 0.70, 0.38, 1)
    hole.inputs["Strength"].default_value = 9
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs["Color"], mix.inputs["Fac"])
    nt.links.new(shell.outputs[0], mix.inputs[1])
    nt.links.new(hole.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def marble_material():
    m = bpy.data.materials.new("Marble")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.18
    noise = nt.nodes.new("ShaderNodeTexWave")
    noise.inputs["Scale"].default_value = 1.2
    noise.inputs["Distortion"].default_value = 12
    noise.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.22, 0.21, 0.20, 1)
    ramp.color_ramp.elements[1].color = (0.42, 0.40, 0.38, 1)
    ramp.color_ramp.elements[0].position = 0.35
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    return m


# ---------------------------------------------------------------- utilitaires
def link(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


def smooth(ob, angle=35):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    try:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    except Exception:
        bpy.ops.object.shade_smooth()
    ob.select_set(False)


def rounded_box(name, sx, sy, sz, loc, r_corner, r_edge, axis=2, segments=16):
    """Boîte avec arêtes parallèles à `axis` arrondies (r_corner) + chanfrein doux global."""
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (sx * MM, sy * MM, sz * MM)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    edges = [e for e in bm.edges if abs(e.verts[0].co[axis] - e.verts[1].co[axis]) > 1e-7]
    bmesh.ops.bevel(bm, geom=edges, offset=r_corner * MM, segments=segments,
                    profile=0.5, affect='EDGES')
    bm.to_mesh(ob.data)
    bm.free()
    if r_edge:
        mod = ob.modifiers.new("edge", 'BEVEL')
        mod.width = r_edge * MM
        mod.segments = 4
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(40)
    ob.location = Vector(loc) * MM
    smooth(ob)
    return ob


def cylinder(name, r, h, loc, rot=(0, 0, 0), verts=96, bevel=0.6):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r * MM, depth=h * MM,
                                        location=Vector(loc) * MM, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    if bevel:
        mod = ob.modifiers.new("edge", 'BEVEL')
        mod.width = bevel * MM
        mod.segments = 3
        mod.limit_method = 'ANGLE'
    smooth(ob)
    return ob


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


# ---------------------------------------------------------------- profil de l'arche
def half_width(W, u):
    """Demi-largeur d'une ogive en flamme ; u=0 en bas, u=1 à la pointe."""
    return W * (1 - u) ** 0.8 * (1 + 1.2 * u)        # ventre vers 1/3, pointe en flamme


def tilt(u):
    return P["arch_tilt"] * u ** 5


def side(W, H, sign, z_start=0.0, n=120):
    """Points (x, z) d'un côté de l'ogive, du bas vers la pointe."""
    pts = []
    u0 = z_start / H
    for i in range(n + 1):
        u = u0 + (1 - u0) * i / n
        u = min(u, 0.9995)
        pts.append((sign * half_width(W, u) + tilt(u), u * H))
    return pts


def u_outline(outer, inner, z_start=0.0):
    """Contour fermé en U inversé : extérieur gauche→pointe→droite, puis intérieur retour."""
    Wo, Ho = outer
    Wi, Hi = inner
    ol = side(Wo, Ho, -1, z_start)
    orr = side(Wo, Ho, +1, z_start)
    il = side(Wi, Hi, -1, z_start)
    ir = side(Wi, Hi, +1, z_start)
    return ol + orr[::-1][1:] + ir + il[::-1][1:]


def prism_from_outline(name, pts, y0, y1, z_base, bevel=0.0):
    """Extrude un contour (x, z) entre y0 et y1 (mm), via une courbe 2D remplie."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '2D'
    cu.fill_mode = 'BOTH'
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for p, (x, z) in zip(sp.points, pts):
        p.co = (x * MM, z * MM, 0, 1)
    sp.use_cyclic_u = True
    depth = abs(y1 - y0)
    cu.extrude = (depth / 2 - bevel) * MM
    if bevel:
        cu.bevel_depth = bevel * MM
        cu.bevel_resolution = 3
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.location = (0, (y0 + y1) / 2 * MM, z_base * MM)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.convert(target='MESH')
    ob = bpy.context.active_object
    ob.select_set(False)
    bm = bmesh.new()                       # soude capuchons + biseau -> maillage fermé
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def boolean(target, cutter, op='DIFFERENCE'):
    mod = target.modifiers.new("bool", 'BOOLEAN')
    mod.operation = op
    mod.object = cutter
    mod.solver = 'EXACT'
    apply_mods(target)
    bpy.data.objects.remove(cutter, do_unlink=True)


def star_points(cx, cz, r_out, r_in, rot=0.0):
    pts = []
    for k in range(16):
        r = r_out if k % 2 == 0 else r_in
        a = rot + k * math.pi / 8
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


# ================================================================= MODÈLE
top = P["base_z0"] + P["base_h"]          # dessus de la base (z)
fy = -P["base_d"] / 2                      # face avant (y)

# --- Base électronique
base = link(rounded_box("Base", P["base_w"], P["base_d"], P["base_h"],
                        (0, 0, P["base_z0"] + P["base_h"] / 2), P["base_corner"], P["base_edge"]), mat_body)
ring = link(rounded_box("LED_Ring", P["base_w"] - 5, P["base_d"] - 5, 2.4,
                        (0, 0, P["base_z0"] - 1.2), P["base_corner"] - 2.5, 0), mat_glow_soft)
plate = link(rounded_box("Bottom_Plate", P["base_w"] - 8, P["base_d"] - 8, 3.4,
                         (0, 0, 1.7 + 0.2), P["base_corner"] - 4, 0.8), mat_dark)
for sx in (-1, 1):
    for sy in (-1, 1):
        link(cylinder("Foot", 5, 1.2, (sx * 55, sy * 30, 0.6), bevel=0.3), mat_metal)

# --- Façade : verre noir + écran + icônes tactiles
panel = link(rounded_box("Front_Glass", P["panel_w"], 2.0, P["panel_h"],
                         (P["panel_x"], fy - 0.4, P["base_z0"] + P["base_h"] / 2),
                         6, 0.6, axis=1, segments=10), mat_glass)

bpy.ops.mesh.primitive_plane_add(size=1, location=(P["panel_x"] * MM, (fy - 1.45) * MM,
                                                   (P["base_z0"] + P["base_h"] / 2) * MM),
                                 rotation=(math.radians(90), 0, 0))
screen = bpy.context.active_object
screen.name = "Screen_1.9in"
screen.scale = (P["screen_w"] * MM, P["screen_h"] * MM, 1)
link(screen, screen_material())


def icon(name, shapes, cx, cz):
    """shapes : liste de polygones (x, z) relatifs ; plaqués sur le verre."""
    me = bpy.data.meshes.new(name)
    verts, faces = [], []
    for poly in shapes:
        i0 = len(verts)
        verts += [((cx + x) * MM, (fy - 1.46) * MM, (cz + z) * MM) for x, z in poly]
        faces.append(list(range(i0, i0 + len(poly))))
    me.from_pydata(verts, [], faces)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return link(ob, mat_glow)


cz = P["base_z0"] + P["base_h"] / 2
tri = 2.6
icon("Icon_Prev", [[(-3.2, -tri), (-2.6, -tri), (-2.6, tri), (-3.2, tri)],
                   [(2.6, tri), (2.6, -tri), (-2.2, 0)]], P["panel_x"] - 35, cz)
icon("Icon_Next", [[(3.2, tri), (2.6, tri), (2.6, -tri), (3.2, -tri)],
                   [(-2.6, -tri), (-2.6, tri), (2.2, 0)]], P["panel_x"] + 35, cz)

# --- Molette (volume / validation) sur l'angle avant droit
cxk, cyk = P["base_w"] / 2 - P["base_corner"], fy + P["base_corner"]
a = math.radians(P["knob_angle"])
d = Vector((math.sin(a), -math.cos(a), 0))
surf = Vector((cxk, cyk, cz)) + d * P["base_corner"]
rot_q = d.to_track_quat('Z', 'Y').to_euler()
knob = link(cylinder("Knob", P["knob_r"], P["knob_len"], surf + d * (P["knob_len"] / 2 + 1.0),
                     rot=rot_q, verts=128, bevel=1.0), mat_metal)
bpy.context.view_layer.objects.active = knob
grooves = knob.modifiers.new("knurl", 'DISPLACE')     # moletage léger
tex = bpy.data.textures.new("knurl", 'STUCCI')
tex.noise_scale = 0.08
grooves.texture = tex
grooves.strength = 0.0002
link(cylinder("Knob_Ring", P["knob_r"] + 1.2, 0.8, surf + d * 0.6, rot=rot_q, bevel=0), mat_glow)

# --- Socle doré sous la sphère
link(cylinder("Pedestal", 40, 3, (0, 0, top + 1.5), bevel=0.8), mat_metal)
link(cylinder("Pedestal_Inlay", 33, 0.6, (0, 0, top + 3.1), bevel=0), mat_dark)
link(cylinder("Pedestal_Glow", 30, 0.4, (0, 0, top + 3.45), bevel=0), mat_glow_soft)

# --- Arche (coque)
D = P["arch_depth"]
arch = prism_from_outline("Arch_Shell", u_outline((P["arch_w"], P["arch_h"]),
                                                  (P["arch_inner_w"], P["arch_inner_h"])),
                          -D / 2, D / 2, top, bevel=2.0)
link(arch, mat_body)

# panneaux ajourés dorés + LED derrière, sur les faces avant ET arrière
band = u_outline(P["band_out"], P["band_in"], z_start=8)
rec = P["band_recess"]

centre = []
for sgn in (-1, 1):
    so = side(*P["band_out"], sgn, z_start=8, n=400)
    si = side(*P["band_in"], sgn, z_start=8, n=400)
    centre.append([((po[0] + pi[0]) / 2, (po[1] + pi[1]) / 2, math.dist(po, pi))
                   for po, pi in zip(so, si)])


def star_cutter(y_a, y_b):
    me = bpy.data.meshes.new("stars")
    bm = bmesh.new()
    for path in centre:
        acc, last = 10.5, None
        for x, z, w in path:
            if last is not None:
                acc += math.dist((x, z), last)
            last = (x, z)
            if acc < 10.5:
                continue
            acc = 0.0
            r_out = min(4.4, 0.37 * w)
            if r_out < 1.6 or z > P["band_in"][1] - 3:
                continue
            poly = star_points(x, z, r_out, r_out * 0.62)
            vf = [bm.verts.new((px * MM, y_a * MM, (pz + top) * MM)) for px, pz in poly]
            vb = [bm.verts.new((px * MM, y_b * MM, (pz + top) * MM)) for px, pz in poly]
            bm.faces.new(vf[::-1])
            bm.faces.new(vb)
            for k in range(16):
                bm.faces.new((vf[k], vf[(k + 1) % 16], vb[(k + 1) % 16], vb[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("stars", me)
    bpy.context.collection.objects.link(ob)
    return ob


for s in (-1, 1):                       # s = -1 : face avant, +1 : face arrière
    face = s * D / 2
    inward = -s
    boolean(arch, prism_from_outline("cut", band, face + s * 5, face + inward * rec, top))
    link(prism_from_outline("Arch_LED_Diffuser", band, face + inward * (rec - 0.6),
                            face + inward * (rec - 0.1), top), mat_glow)
    fil = prism_from_outline("Arch_Filigree", band, face + inward * 0.5,
                             face + inward * 2.5, top)
    link(fil, mat_metal)
    boolean(fil, star_cutter(face + s * 2, face + inward * 4))
smooth(arch, 30)

# --- Sphère + suspension en tube laiton
sz = top + P["sphere_z"]
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=P["sphere_r"] * MM,
                                     location=(0, 0, sz * MM))
sphere = bpy.context.active_object
sphere.name = "Sphere"
smooth(sphere, 180)
link(sphere, sphere_material())
link(cylinder("Sphere_Cap_Top", 7, 3, (0, 0, sz + P["sphere_r"] - 0.5), bevel=0.8), mat_metal)
link(cylinder("Sphere_Cap_Bottom", 4.5, 2.4, (0, 0, sz - P["sphere_r"] + 0.3), bevel=0.6), mat_metal)

# point haut de l'ouverture intérieure à x = 0 (la pointe est décalée)
inner_left = side(P["arch_inner_w"], P["arch_inner_h"], -1, n=2000)
z_hit = max(z for x, z in inner_left if abs(x) < 0.6) + top
rod_bot = sz + P["sphere_r"] + 1
link(cylinder("Brass_Rod", 2.0, z_hit - rod_bot + 6, (0, 0, (z_hit + 6 + rod_bot) / 2),
              verts=32, bevel=0), mat_metal)

bpy.ops.object.light_add(type='POINT', location=(0, 0, sz * MM))
inner = bpy.context.active_object
inner.data.energy = 1.2
inner.data.color = WARM
inner.data.shadow_soft_size = 0.008

# ================================================================= DÉCOR + RENDU
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0, 0))
link(bpy.context.active_object, marble_material()).name = "Table"
bpy.ops.mesh.primitive_plane_add(size=3, location=(0, 0.9, 0.6), rotation=(math.radians(90), 0, 0))
link(bpy.context.active_object, principled("Wall", (0.05, 0.035, 0.025), rough=0.9)).name = "Wall"

world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.009, 0.007, 1)


def area(name, loc, target, energy, size, color=(1, 0.86, 0.72)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    L = bpy.context.active_object
    L.name = name
    L.data.energy = energy
    L.data.size = size
    L.data.color = color
    L.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


area("Key", (-0.45, -0.45, 0.55), (0, 0, 0.1), 9, 0.35)
area("Rim", (0.35, 0.45, 0.45), (0, 0, 0.12), 14, 0.25)
area("Fill", (0.5, -0.3, 0.15), (0, 0, 0.1), 1.5, 0.4, color=(0.85, 0.88, 1.0))


def camera(name, loc, target, lens):
    cam_d = bpy.data.cameras.new(name)
    cam_d.lens = lens
    cam_d.dof.use_dof = True
    cam_d.dof.focus_distance = (Vector(target) - Vector(loc)).length
    cam_d.dof.aperture_fstop = 5.6
    cam = bpy.data.objects.new(name, cam_d)
    bpy.context.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return cam


cam_hero = camera("Cam_Hero", (-0.24, -0.52, 0.19), (0.0, 0.0, 0.115), 55)
cam_screen = camera("Cam_Screen", (0.03, -0.20, 0.07), (0.005, -0.05, 0.025), 50)
cam_front = camera("Cam_Front", (0.0, -0.62, 0.13), (0.0, 0.0, 0.115), 50)

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
scene.cycles.samples = 64 if QUALITY == "preview" else 256
scene.cycles.use_denoising = True
scene.view_settings.look = 'AgX - Medium High Contrast' if 'AgX' in scene.view_settings.view_transform else 'None'

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"ayah_{VARIANT}.blend"))

shots = [(cam_hero, "hero", 1600, 1200), (cam_screen, "screen", 1600, 1000), (cam_front, "front", 1200, 1400)]
if VARIANT != "ivory":
    shots = shots[:1]
for cam, label, w, h in shots:
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = w, h
    scene.render.filepath = os.path.join(HERE, "renders", f"ayah_{VARIANT}_{label}.png")
    bpy.ops.render.render(write_still=True)
print("AYAH DONE")
