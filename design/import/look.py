import bpy, sys, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
src = sys.argv[sys.argv.index("--")+1]; tag=sys.argv[sys.argv.index("--")+2]
bpy.ops.import_scene.gltf(filepath=src)
ob=[o for o in bpy.data.objects if o.type=='MESH'][0]
sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH' if tag=="geo" else 'CYCLES'
if tag=="geo":
    sc.display.shading.light='STUDIO'; sc.display.shading.color_type='SINGLE'; sc.display.shading.single_color=(0.8,0.78,0.74)
    sc.display.shading.show_cavity=True
else:
    sc.cycles.samples=32; sc.world=bpy.data.worlds.new("w"); sc.world.color=(1,1,1)
    sc.world.use_nodes=True; sc.world.node_tree.nodes["Background"].inputs[1].default_value=1.0
sc.render.resolution_x=sc.render.resolution_y=900
cd=bpy.data.cameras.new("c"); cd.type='ORTHO'; cd.ortho_scale=1.15
cam=bpy.data.objects.new("c",cd); sc.collection.objects.link(cam); sc.camera=cam
views={"front":(0,-3,0),"side":(3,0,0),"34":(2,-2.2,1.0),"top":(0,-0.01,3),"back":(0,3,0)}
for name,loc in views.items():
    cam.location=loc
    cam.rotation_euler=(Vector((0,0,0))-Vector(loc)).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=f"/Users/mohammadharris/tiktok claude/ayah-design/import/view_{tag}_{name}.png"
    bpy.ops.render.render(write_still=True)
