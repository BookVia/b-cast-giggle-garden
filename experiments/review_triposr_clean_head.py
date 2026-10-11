import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;O=R/'tool_experiments/triposr_clean_head'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(O/'head_UNAPPROVED.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
bounds=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
center=sum(bounds,Vector())/len(bounds)
for o in meshes:o.location-=center
size=max(max(v[i] for v in bounds)-min(v[i] for v in bounds) for i in range(3))
for o in meshes:
 if not o.data.materials:
  m=bpy.data.materials.new('Reconstruction vertex colour');m.use_nodes=True
  if o.data.color_attributes:
   n=m.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name=o.data.color_attributes[0].name;m.node_tree.links.new(n.outputs['Color'],m.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
  o.data.materials.append(m)
bpy.ops.object.camera_add(location=(0,-size*3,0));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=size*1.2
sc=bpy.context.scene;sc.camera=cam;sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True
sc.render.resolution_x=512;sc.render.resolution_y=512;sc.render.resolution_percentage=100
sc.world=bpy.data.worlds.new('Review world');sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1)
for loc,power in [((size,-size*2,size*2),450),((-size,-size,size),250)]:
 bpy.ops.object.light_add(type='AREA',location=loc);bpy.context.object.data.energy=power;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=size*2
 bpy.context.object.rotation_euler=(-bpy.context.object.location).to_track_quat('-Z','Y').to_euler()
sc.cycles.device='CPU'
sc['production_ready']=False;sc['visual_reference_passed']=False
bpy.ops.wm.save_as_mainfile(filepath=str(O/'head_review_UNAPPROVED.blend'))
for name,loc in [('front',(0,-3*size,0)),('profile',(3*size,0,0)),('back',(0,3*size,0)),('three_quarter',(2*size,-3*size,size*.35))]:
 cam.location=loc;cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(O/('review_'+name+'.png'));bpy.ops.render.render(write_still=True);print('REVIEW_DONE',name,flush=True)
import sys
sys.path.insert(0,str(R))
from png_validation import valid_png
for name in ['front','profile','back','three_quarter']: assert valid_png(O/('review_'+name+'.png'),512,512)
(O/'render_review.json').write_text(json.dumps({'views':4,'production_ready':False,'visual_reference_passed':False,'note':'Reconstructed head only. Unseen surfaces inferred, not approved artwork.'},indent=2))
print('HEAD_REVIEW_COMPLETE',flush=True)
