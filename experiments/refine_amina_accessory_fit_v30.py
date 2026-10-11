import bpy,math,json,array,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).parent;O=R/'amina_reconstruction_v30';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'amina_reconstruction_v29/Amina_anatomy_refinement_UNAPPROVED.blend'))
head=bpy.data.objects['Amina anatomy refinement V29 UNAPPROVED'];head.name='Amina anatomy refinement V30 UNAPPROVED'
# Shorten lower face while keeping all newly fitted facial pieces together.
def facial_warp(q):
 if q.z<2.175:q.z=2.175+(q.z-2.175)*.88
 if abs(q.x)<.14 and 2.01<q.z<2.14 and q.y<-.25:
  w=math.exp(-((q.z-2.08)/.055)**2)*math.exp(-((q.x/.12)**4));q.x*=1-.16*w
 return q
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and (ob==head or ob.name.startswith(('V29 mouth','V29 curved upper teeth'))):
  inv=ob.matrix_world.inverted()
  for v in ob.data.vertices:v.co=inv@facial_warp(ob.matrix_world@v.co)
  ob.data.update()
bpy.context.view_layer.update();ev=head.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bvh=BVHTree.FromPolygons([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.polygons])
# Restore the missing approved purple bead and stud components.
with bpy.data.libraries.load(str(R/'amina_reconstruction_v22/Amina_likeness_candidate_UNAPPROVED.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith(('Earring stud','Purple earring bead'))]
for ob in b.objects:
 if ob:bpy.context.scene.collection.objects.link(ob)
attachments={}
for side in [-1,1]:
 hit=bvh.find_nearest(Vector((side*.35,-.045,2.025)));target=hit[0]+Vector((side*.006,-.008,-.002));attachments[str(side)]=list(target)
 old=Vector((side*.448,-.062,1.935));shift=target-old
 for ob in bpy.context.scene.objects:
  if ob.name.startswith(('Earring stud','Purple earring bead','Purple drop earring')):
   bounds=[ob.matrix_world@Vector(v) for v in ob.bound_box];cx=sum(p.x for p in bounds)/len(bounds)
   if (cx<0)==(side<0):ob.location+=shift
purple=bpy.data.materials.new('V30 reference purple earrings');purple.use_nodes=True;purple.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.16,.017,.23,1);purple.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.30
for ob in bpy.context.scene.objects:
 if ob.name.startswith('Purple earring bead'):ob.data.materials.clear();ob.data.materials.append(purple)
 if ob.name.startswith('Earring stud'):ob.data.materials.clear();ob.data.materials.append(bpy.data.materials['Brass buttons'])
# Replace the inherited band with a ribbon sampled on this head surface.
oldband=bpy.data.objects.get('Amina fabric headband');bandmat=oldband.data.materials[0];bpy.data.objects.remove(oldband,do_unlink=True)
vs=[];fs=[]
for i in range(81):
 x=-.333+.666*i/80;z=2.59-.175*(abs(x)/.333)**1.6
 for dz in [-.012,.012]:
  hit=bvh.ray_cast(Vector((x,-1,z+dz)),Vector((0,1,0)))
  if hit[0] is None:hit=bvh.find_nearest(Vector((x,-.16,z+dz)))
  vs.append(tuple(hit[0]+hit[1]*.011))
 if i:fs.append((2*i-2,2*i,2*i+1,2*i-1))
mesh=bpy.data.meshes.new('V30 surface fitted fabric band');mesh.from_pydata(vs,[],fs);mesh.update();mesh.materials.append(bandmat)
band=bpy.data.objects.new('V30 surface fitted fabric headband',mesh);bpy.context.scene.collection.objects.link(band)
sol=band.modifiers.new('Fabric thickness','SOLIDIFY');sol.thickness=.003
for p in mesh.polygons:p.use_smooth=True
# Seat the whole bow from its shared knot, preserving the cloth folds.
knot=bpy.data.objects['Amina bow knot'];bb=[knot.matrix_world@Vector(v) for v in knot.bound_box];old=sum(bb,Vector())/8
hit=bvh.ray_cast(Vector((.095,-1,2.59)),Vector((0,1,0)));target=hit[0]+hit[1]*.025
for ob in bpy.context.scene.objects:
 if ob.name.startswith(('Amina folded bow','Amina bow knot')):ob.location+=target-old
# Refit both support meshes and actual strand positions together, with reference-like asymmetry.
pufffits={}
for ob in bpy.context.scene.objects:
 if not (ob.name.startswith('Amina irregular puff volume') or ob.type=='CURVES' and 'detailed puff' in ob.name):continue
 side=-1 if (ob.name.endswith('-1') if ob.type=='CURVES' else sum((ob.matrix_world@Vector(v)).x for v in ob.bound_box)<0) else 1
 old=np.array([side*.403,.06,2.56],dtype=np.float32);new=np.array([side*.387,.05,2.555 if side<0 else 2.535],dtype=np.float32);factor=1.03 if side<0 else .94
 if ob.type=='MESH':
  count=len(ob.data.vertices);data=np.empty(count*3,dtype=np.float32);ob.data.vertices.foreach_get('co',data)
 else:
  attr=ob.data.attributes['position'];count=len(attr.data);data=np.empty(count*3,dtype=np.float32);attr.data.foreach_get('vector',data)
 local=data.reshape(-1,3);matrix=np.array(ob.matrix_world,dtype=np.float32);world=local@matrix[:3,:3].T+matrix[:3,3];world=(world-old)*factor+new
 inv=np.array(ob.matrix_world.inverted(),dtype=np.float32);local=world@inv[:3,:3].T+inv[:3,3];data=local.astype(np.float32).reshape(-1)
 if ob.type=='MESH':ob.data.vertices.foreach_set('co',data);ob.data.update()
 else:attr.data.foreach_set('vector',data)
 pufffits[ob.name]={'scale':factor,'new_center':new.tolist()}
ev.to_mesh_clear()
sc=bpy.context.scene;sc['production_ready']=False;sc['visual_reference_passed']=False;sc['rigged']=False
sc.cycles.samples=16;sc.cycles.device='CPU';sc.render.resolution_x=640;sc.render.resolution_y=640
bpy.ops.wm.save_as_mainfile(filepath=str(O/'Amina_anatomy_refinement_UNAPPROVED.blend'))
for name,loc in [('face',(0,-7,2.2)),('three_quarter',(3,-6,2.2)),('profile',(6,-1,2.2))]:
 cam=sc.camera;cam.location=loc;cam.rotation_euler=(Vector((0,0,2.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.5;sc.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True);print('V30_REVIEW_DONE',name,flush=True)
sys.path.insert(0,str(R));from png_validation import valid_png
for name in ['face','three_quarter','profile']:assert valid_png(O/(name+'.png'),640,640)
(O/'fit_changes.json').write_text(json.dumps({'production_ready':False,'visual_reference_passed':False,'earring_attachments':attachments,'puffs':pufffits,'changes':['Missing studs and purple beads restored','Band rebuilt on anatomy surface','Bow fitted by knot attachment','Puff supports and native fibres refitted together','Lower face compressed and nose width refined'],'requires':['Visual likeness review','Topology and clearance audit','Body integration and deformation tests']},indent=2));print('V30_COMPLETE')
