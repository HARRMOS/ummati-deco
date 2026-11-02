import bpy, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath="/Users/mohammadharris/Downloads/result.glb")
ob=[o for o in bpy.data.objects if o.type=='MESH'][0]
me=ob.data; n=len(me.vertices)
co=np.empty(n*3); me.vertices.foreach_get("co",co); co=co.reshape(-1,3)
M=np.array(ob.matrix_world); co=co@M[:3,:3].T+M[:3,3]
co*=1/ (co[:,2].max()-co[:,2].min())  # hauteur = 1
co[:,2]-=co[:,2].min()
x,y,z=co.T
print("x",x.min(),x.max()," y",y.min(),y.max())
for zz in np.arange(0.0,1.001,0.025):
    m=(z>=zz-0.006)&(z<zz+0.006)
    if m.sum()<5: continue
    xs,ys=x[m],y[m]
    # silhouette: x extent; y extent; for the back shell: max y
    print(f"z={zz:.3f} x[{xs.min():+.3f},{xs.max():+.3f}] y[{ys.min():+.3f},{ys.max():+.3f}] n={m.sum()}")
