"""Rendus AYAH Radio : blender -b -P render_radio.py -- [vert|noir|blanc]"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
STL, OUT = os.path.join(HERE, "stl"), os.path.join(HERE, "apercus")
os.makedirs(OUT, exist_ok=True)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VAR = argv[0] if argv else "vert"
BODY = {"vert": (0.022, 0.065, 0.045), "noir": (0.012, 0.012, 0.012), "blanc": (0.80, 0.76, 0.68)}[VAR]

R90 = math.radians(90)
PARTS = {   # nom: (matériau, position, rotation, décalage éclaté)
    "01_corps": ("body", (0, 0, 0), (0, 0, 0), (0, 0, 0)),
    "02_grille_OR": ("gold", (0, 0, 0), (0, 0, 0), (0, -90, 0)),
    "03_plaque_calligraphie_NOIR+OR": ("plaque", (0, 0, 0), (0, 0, 0), (0, -130, 0)),
    "04_baffle": ("white", (0, 0, 0), (0, 0, 0), (0, -45, 0)),
    "06_dos_electronique": ("body", (0, 0, 0), (0, 0, 0), (0, 70, 0)),
    "08_socle_OR": ("gold", (0, 0, 0), (0, 0, 0), (0, 0, -45)),
    "09_molette_OR": ("gold", (56, 0, 28), (R90, 0, 0), (0, -60, 0)),
    "10_touche_precedent_OR": ("gold", (-48, 0, 28), (R90, 0, 0), (0, -60, 0)),
    "11_touche_lecture_OR": ("gold", (-18, 0, 28), (R90, 0, 0), (0, -60, 0)),
    "12_touche_suivant_OR": ("gold", (12, 0, 28), (R90, 0, 0), (0, -60, 0)),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def mat(name, color, metallic=0.0, rough=0.5, emit=None, strength=0.0, coat=0.0):
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


M = {
    "body": mat("Body", BODY, rough=0.55, coat=0.1),
    "gold": mat("Gold", (1.0, 0.70, 0.36), metallic=1.0, rough=0.28),
    "dark": mat("Dark", (0.015, 0.03, 0.022), rough=0.6),
    "white": mat("White", (0.9, 0.88, 0.84), rough=0.7),
    "glow": mat("Glow", (0, 0, 0), emit=(1.0, 0.62, 0.30), strength=5),
    "spk": mat("Spk", (0.03, 0.03, 0.03), rough=0.8),
}
objs = {}
for name, (m, loc, rot, _) in PARTS.items():
    bpy.ops.wm.stl_import(filepath=os.path.join(STL, name + ".stl"))
    ob = bpy.context.active_object
    ob.location, ob.rotation_euler = loc, rot
    if m == "plaque":
        ob.data.materials.append(M["dark"]); ob.data.materials.append(M["gold"])
        for p in ob.data.polygons:                       # relief (y < 1,15) -> or
            if p.center.y < 1.15:
                p.material_index = 1
    else:
        ob.data.materials.append(M[m])
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
    objs[name] = ob

# haut-parleurs (repères) + lumière LED derrière la grille
for x in (-46, 46):
    bpy.ops.mesh.primitive_cylinder_add(radius=20, depth=25, location=(x, 14.5 + 12.5, 92), rotation=(R90, 0, 0))
    bpy.context.active_object.data.materials.append(M["spk"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 11.8, 95), rotation=(R90, 0, 0))
g = bpy.context.active_object; g.scale = (110, 55, 1); g.data.materials.append(M["glow"])

# scène
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, 0))
marble = mat("Marble", (0.62, 0.58, 0.54), rough=0.15)
bpy.context.active_object.data.materials.append(marble)
sc.world = bpy.data.worlds.new("w")
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.04, 0.035, 1)


def look(o, t):
    o.rotation_euler = (Vector(t) - o.location).to_track_quat('-Z', 'Y').to_euler()


def area(loc, t, e, s, c=(1, 0.86, 0.72)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.active_object
    l.data.energy, l.data.size, l.data.color = e, s, c
    look(l, t)


area((-300, -350, 400), (0, 0, 60), 2.2e5, 300)
area((350, 200, 300), (0, 0, 80), 1.2e5, 200)
area((250, -300, 80), (0, 0, 50), 4e4, 250, (0.85, 0.9, 1))


def cam(loc, t, lens=50):
    cd = bpy.data.cameras.new("c"); cd.lens = lens; cd.clip_end = 10000
    c = bpy.data.objects.new("c", cd); sc.collection.objects.link(c)
    c.location = loc; look(c, t); sc.camera = c


sc.render.engine = 'CYCLES'
prefs = bpy.context.preferences.addons["cycles"].preferences
try:
    prefs.compute_device_type = 'METAL'; prefs.get_devices()
    for d in prefs.devices:
        d.use = True
    sc.cycles.device = 'GPU'
except Exception:
    pass
sc.cycles.samples = 64
sc.cycles.use_denoising = True
try:
    sc.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    pass


def shot(f, w=1500, h=1100):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = os.path.join(OUT, f)
    bpy.ops.render.render(write_still=True)


cam((-230, -420, 190), (0, 0, 72), 50); shot(f"rendu_{VAR}.png")
cam((0, -480, 80), (0, 0, 75), 50); shot(f"face_{VAR}.png", 1300, 1100)
if VAR == "vert":
    for name, (_, loc, _, off) in PARTS.items():
        objs[name].location = Vector(loc) + Vector(off)
    cam((-520, -560, 330), (0, -40, 60), 45); shot("eclate.png", 1600, 1200)
print("RENDUS OK")
