import bpy, sys, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
src = sys.argv[sys.argv.index("--")+1]
if src.endswith(".glb"):
    bpy.ops.import_scene.gltf(filepath=src)
else:
    bpy.ops.wm.stl_import(filepath=src)
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in meshes:
    print("MESH", o.name, len(o.data.vertices), len(o.data.polygons), [round(d,4) for d in o.dimensions], "mats", [m.name for m in o.data.materials if m])
# bbox global
import itertools
pts=[o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
mn=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
mx=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
print("BBOX", mn, mx)
