"""Rendus de contrôle des pièces imprimables : blender -b -P render_parts.py"""
import bpy, os, math
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "stl")
OUT = os.path.join(HERE, "apercus")
os.makedirs(OUT, exist_ok=True)

IVORY, GOLD, BLACK, WHITE, GREEN = (0.86, 0.80, 0.70), (0.86, 0.64, 0.30), (0.05, 0.05, 0.05), (0.97, 0.97, 0.95), (0.15, 0.45, 0.25)
SPH = Vector((16.93, 2.84, 99.0))
KNOB_P, KNOB_N = Vector((46.0, -57.6, 23.0)), Vector((0.5045, -0.8634, 0))
# nom -> (couleur, position, rotation, décalage vue éclatée)
PARTS = {
    "01_niche_coque": (IVORY, (0, 0, 0), (0, 0, 0), (0, 0, 70)),
    "02_panneau_ajoure_OR": (GOLD, (0, 0, 0), (0, 0, 0), (0, -60, 70)),
    "03_base_coque": (IVORY, (0, 0, 0), (0, 0, 0), (0, 0, 0)),
    "04_fond_electronique": (IVORY, (0, 0, 0), (0, 0, 0), (0, 0, -70)),
    "05_bride_haut_parleur": (IVORY, (-8, -26, 6.0), (0, 0, 0), (0, 0, -45)),
    "06_barrette_esp32": (IVORY, (18, 30 - 32 + 8, 17.0), (0, 0, math.pi / 2), (0, 0, -35)),
    "07_support_ecran": (IVORY, (0, -59.5 + 3.0 + 4.5, 23), (-math.pi / 2, 0, 0), (0, 25, 0)),
    "08_cadre_ecran_NOIR": (BLACK, (0, -62.0 - 0.0, 23), (math.pi / 2, 0, 0), (0, -40, 0)),
    "09_molette_OR": (GOLD, tuple(KNOB_P + KNOB_N * 0.5), tuple(KNOB_N.to_track_quat('Z', 'Y').to_euler()), tuple(KNOB_N * 35)),
    "10_socle_OR": (GOLD, (SPH.x, SPH.y, 43.0), (0, 0, 0), (0, 0, 40)),
    "11_diffuseur_BLANC": (WHITE, (SPH.x, SPH.y, 43.0 + 2.2), (0, 0, 0), (0, 0, 52)),
    "12_sphere_haut_BLANC": (WHITE, tuple(SPH), (0, 0, 0), (0, -50, 95)),
    "13_sphere_bas_BLANC": (WHITE, tuple(SPH), (0, 0, 0), (0, -50, 75)),
}

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light, sh.color_type, sh.show_cavity, sh.show_shadows = 'STUDIO', 'OBJECT', True, True
sh.cavity_type = 'BOTH'
sc.render.film_transparent = False
sc.world = bpy.data.worlds.new("w")
sc.world.color = (0.93, 0.93, 0.94)
sc.view_settings.view_transform = 'Standard'

objs = {}
for name, (col, loc, rot, _) in PARTS.items():
    bpy.ops.wm.stl_import(filepath=os.path.join(STL, name + ".stl"))
    ob = bpy.context.active_object
    ob.color = (*col, 1)
    ob.location, ob.rotation_euler = loc, rot
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(30))
    objs[name] = ob

# repères des composants (volumes approximatifs, pour vérifier l'encombrement)
def box(name, size, loc, col=GREEN, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = size
    o.color = (*col, 1)
    o.name = name
    return o

comps = [
    box("ESP32", (28.5, 64, 1.6), (18, 30, 8.8)),
    box("MAX98357A", (19.5, 18.5, 1.6), (-46, 4, 4.8)),
    box("SD", (24.5, 42, 1.6), (-20, 38, 4.8)),
    box("Ecran", (52, 4.5, 28), (0, -59.5 + 2.25, 23), (0.1, 0.1, 0.12)),
]
bpy.ops.mesh.primitive_cylinder_add(radius=26, depth=28, location=(-8, -26, 3 + 14))
spk = bpy.context.active_object; spk.color = (0.2, 0.2, 0.22, 1); comps.append(spk)
bpy.ops.mesh.primitive_cylinder_add(radius=2, depth=79.6, location=(SPH.x, SPH.y, 157.8))
tube = bpy.context.active_object; tube.color = (*GOLD, 1)


def cam(loc, target, ortho=None, lens=50):
    cd = bpy.data.cameras.new("c")
    if ortho:
        cd.type, cd.ortho_scale = 'ORTHO', ortho
    else:
        cd.lens = lens
    cd.clip_end = 5000
    c = bpy.data.objects.new("c", cd)
    sc.collection.objects.link(c)
    c.location = loc
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = c
    return c


def shot(fname, w=1400, h=1400):
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.filepath = os.path.join(OUT, fname)
    bpy.ops.render.render(write_still=True)


def hide(names, state=True):
    for n in names:
        o = objs.get(n) or bpy.data.objects.get(n)
        o.hide_render = state


# 1. assemblé
cam((-260, -480, 260), (0, 0, 95), lens=50); shot("1_assemble.png")
# 2. éclaté
for name, (_, loc, _, off) in PARTS.items():
    objs[name].location = Vector(loc) + Vector(off)
for o in comps:
    o.location.z -= 70
spk.location.z -= 0
tube.hide_render = True
cam((-420, -620, 300), (0, 0, 70), lens=45); shot("2_eclate.png", 1400, 1600)
# 3. fond électronique vu de dessus avec composants
for name, (_, loc, _, _) in PARTS.items():
    objs[name].location = Vector(loc)
for o in comps:
    o.location.z += 70
hide([n for n in PARTS if n not in ("04_fond_electronique", "05_bride_haut_parleur", "06_barrette_esp32")])
hide(["Ecran"])
cam((0, -0.01, 400), (0, 0, 0), ortho=190); shot("3_fond_dessus.png")
# 4. coque de base vue de dessous (intérieur)
hide(list(PARTS), True); hide([o.name for o in comps], True)
hide(["03_base_coque", "07_support_ecran", "Ecran"], False)
cam((0, 0.01, -400), (0, 0, 20), ortho=190); shot("4_base_dessous.png")
# 5. niche vue de dos / de dessous
hide(["03_base_coque", "07_support_ecran", "Ecran"], True)
hide(["01_niche_coque", "02_panneau_ajoure_OR"], False)
cam((200, 420, 120), (0, 0, 120), lens=45); shot("5_niche_arriere.png")
cam((120, -260, -200), (0, 0, 80), lens=40); shot("6_niche_dessous.png")
# 6. sphère éclatée
hide(["01_niche_coque", "02_panneau_ajoure_OR"], True)
hide(["12_sphere_haut_BLANC", "13_sphere_bas_BLANC"], False)
objs["12_sphere_haut_BLANC"].location.z += 25
cam((SPH.x - 90, SPH.y - 150, SPH.z + 60), tuple(SPH + Vector((0, 0, 10))), lens=60); shot("7_sphere.png", 1000, 1000)
print("RENDUS OK")
