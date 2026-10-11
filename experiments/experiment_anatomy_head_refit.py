import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).parent;O=R/'tool_experiments/mpfb_head_refit';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'tool_experiments/mpfb_cpu/anatomy_experiment_UNAPPROVED.blend'))
src=next(o for o in bpy.context.scene.objects if o.type=='MESH')
for modifier in src.modifiers:modifier.show_viewport=False;modifier.show_render=False
bpy.context.view_layer.update()
me=src.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
def group_center(name):
 idx=src.vertex_groups[name].index;pts=[me.vertices[v.index].co for v in src.data.vertices if any(g.group==idx and g.weight>.1 for g in v.groups)]
 assert pts,name
 return sum(pts,Vector())/len(pts)
markers={n:list(group_center(n)) for n in ['joint-l-eye','joint-r-eye','joint-mouth','joint-neck','joint-head','joint-head-2']}
me=src.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
body=src.vertex_groups['body'].index
keep={v.index for v in src.data.vertices if any(g.group==body and g.weight>.1 for g in v.groups) and me.vertices[v.index].co.z>markers['joint-neck'][2]+.015}
eye=(Vector(markers['joint-l-eye'])+Vector(markers['joint-r-eye']))*.5
half=abs(markers['joint-l-eye'][0]-markers['joint-r-eye'][0])*.5
sx=6.4;sz=5.8;sy=3.8
verts=[];mapping={}
for i in sorted(keep):
 p=me.vertices[i].co.copy();mapping[i]=len(verts);verts.append((0.40*math.tanh((p.x-eye.x)*22.0),(p.y-eye.y)*sy-.23,(p.z-eye.z)*sz+2.175))
faces=[tuple(mapping[i] for i in p.vertices) for p in me.polygons if all(i in mapping for i in p.vertices)]
src.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mesh=bpy.data.meshes.new('MPFB head topology experiment');mesh.from_pydata(verts,[],faces);mesh.update()
ob=bpy.data.objects.new('Amina new anatomy head experiment UNAPPROVED',mesh);bpy.context.scene.collection.objects.link(ob)
m=bpy.data.materials.new('Warm brown anatomy refit test');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.31,.084,.028,1);m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.55;mesh.materials.append(m)
for p in mesh.polygons:p.use_smooth=True
mod=ob.modifiers.new('Preview subdivision','SUBSURF');mod.levels=1;mod.render_levels=1
# Bring only studio camera/lights and approved-reference-labelled accessories from the existing candidate.
with bpy.data.libraries.load(str(R/'amina_reconstruction_v22/Amina_likeness_candidate_UNAPPROVED.blend'),link=False) as (a,b):
 b.objects=[n for n in a.objects if n.startswith(('Amina seated eyeball','Amina brown iris','Amina pupil','Amina main eye reflection','Amina secondary reflection','Amina irregular puff','V20 detailed puff','Amina fitted scalp','Amina swept scalp','Amina fabric headband','Amina folded bow','Amina bow knot','Purple drop earring')) or n.startswith(('Camera','Area'))]
for item in b.objects:
 if item:bpy.context.scene.collection.objects.link(item)
sc=bpy.context.scene
camera_data=bpy.data.cameras.new('Branch camera');camera=bpy.data.objects.new('Branch camera',camera_data);sc.collection.objects.link(camera);sc.camera=camera;camera_data.type='ORTHO'
for name,loc,power,size in [('Key',(-3,-4,5),450,4),('Fill',(3,-3,3),250,3)]:
 light_data=bpy.data.lights.new(name,'AREA');light_data.energy=power;light_data.shape='DISK';light_data.size=size
 light=bpy.data.objects.new(name,light_data);sc.collection.objects.link(light);light.location=loc;light.rotation_euler=(Vector((0,0,2.2))-light.location).to_track_quat('-Z','Y').to_euler()
sc.world=bpy.data.worlds.new('Branch neutral world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.28,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
cam=sc.camera;cam.location=(0,-7,2.2);cam.rotation_euler=(Vector((0,0,2.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.6
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=640;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
sc['production_ready']=False;sc['visual_reference_passed']=False
im=bpy.data.images.load(str(R/'approved_reference_assets/Giggle Garden Adventure.png'));im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Amina_anatomy_refit_UNAPPROVED.blend'))
sc.render.filepath=str(O/'head_front.png');bpy.ops.render.render(write_still=True)
sys.path.insert(0,str(R));from png_validation import valid_png
assert valid_png(O/'head_front.png',640,640)
(O/'experiment.json').write_text(json.dumps({'production_ready':False,'visual_reference_passed':False,'markers':markers,'scale':[sx,sy,sz],'vertices':len(verts),'faces':len(faces),'quads':sum(len(f)==4 for f in faces),'limitations':['Neutral anatomy test; mouth expression and custom likeness not established','Accessories transferred for comparison, fit unverified','No rig']},indent=2))
print('MPFB_HEAD_BRANCH_RENDER_DONE',flush=True)
